"""Build the web player (build/web): the final video as one continuous stream, plus a fallback.

Artifact files are capped at 15 MB, so the 1080p master is remuxed (no re-encode) into an
HLS playlist of ~10 s fMP4 segments, played as one 17-minute stream through hls.js or, where
media streaming isn't available, the system player. Where neither can run, the page falls
back to the 540p copy split into three files at keyframes inside narration pauses.

Usage: python3 tools_webparts.py [master.mp4] [outdir]
"""
import csv, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(os.path.dirname(ROOT), "output")
master = sys.argv[1] if len(sys.argv) > 1 else os.path.join(OUT_DIR, "fea_best_practice_subsea_wellhead.mp4")
outdir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "build", "web")
small = os.path.join(OUT_DIR, "fea_best_practice_subsea_wellhead_small.mp4")
FPS = 30
LIMIT = 14.8e6  # artifact file limit, with margin
CHAPTERS = [  # one per scene, in order
    ("", "Introduction"),
    ("", "The system we are modelling"),
    ("", "Questions first: global and local models"),
    ("1", "Choosing the element type"),
    ("", "Inside the solid family: locking and hourglassing"),
    ("", "Axisymmetric or 3D?"),
    ("2", "Choosing the mesh size"),
    ("", "Welds and hot-spot stress"),
    ("3", "Modelling the soil: p-y springs"),
    ("4", "Interfaces: conductor housing and template"),
    ("", "Interfaces: conductor housing and HP housing"),
    ("", "Interfaces: conductor and soil"),
    ("5", "Verification"),
    ("", "Takeaways"),
]


def run(*a):
    subprocess.run(a, check=True)


def frames(path):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v",
                                   "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", path])
    return int(out.decode().strip().strip(","))


def srt_cues(path):
    def ts(s):
        h, m, sec, ms = (int(x) for x in re.split("[:,]", s))
        return h * 3600 + m * 60 + sec + ms / 1000
    cues = []
    for block in open(path, encoding="utf-8").read().strip().split("\n\n"):
        lines = block.splitlines()
        if len(lines) < 3:
            continue
        a, b = [x.strip() for x in lines[1].split("-->")]
        cues.append([round(ts(a), 3), round(ts(b), 3), "\n".join(lines[2:])])
    return cues


def narration_pauses(edl):
    t = json.load(open(os.path.join(ROOT, "data", "timing.json")))
    off = dict(zip(edl["ids"], edl["offsets"]))
    iv = sorted((off[s["id"]] + l["start"], off[s["id"]] + l["start"] + l["dur"]) for s in t["scenes"] for l in s["lines"])
    return [(b0 + 0.12, a1 - 0.12) for (_, b0), (a1, _) in zip(iv, iv[1:]) if a1 - b0 >= 0.45]


def make_small():
    """540p two-pass copy, under the 30 MiB chat attachment limit."""
    vf = ["-vf", "scale=960:540:flags=lanczos", "-c:v", "libx264", "-preset", "slow", "-tune", "animation", "-b:v", "165k"]
    log = os.path.join(ROOT, "build", "small2pass")
    run("ffmpeg", "-loglevel", "error", "-y", "-i", master, "-map", "0:v", *vf, "-pass", "1", "-passlogfile", log, "-an", "-f", "mp4", os.devnull)
    run("ffmpeg", "-loglevel", "error", "-y", "-i", master, "-map", "0", *vf, "-maxrate", "600k", "-bufsize", "1200k",
        "-pass", "2", "-passlogfile", log, "-c:a", "aac", "-b:a", "64k", "-c:s", "copy", "-movflags", "+faststart", small)


def main():
    edl = json.load(open(os.path.join(ROOT, "build", "edl.json")))
    total = round((edl["offsets"][-1] + edl["durations"][-1]) * FPS) / FPS
    tmp = os.path.join(ROOT, "build", "webtmp")
    for d in (outdir, os.path.join(outdir, "h"), os.path.join(outdir, "lo"), tmp):
        os.makedirs(d, exist_ok=True)

    # 1) the continuous stream: HLS, fMP4 segments, stream-copied from the master
    hdir = os.path.join(outdir, "h")
    for f in os.listdir(hdir):
        os.remove(os.path.join(hdir, f))
    run("ffmpeg", "-loglevel", "error", "-y", "-i", master, "-map", "0:v", "-map", "0:a", "-c", "copy",
        "-f", "hls", "-hls_time", "10", "-hls_playlist_type", "vod", "-hls_segment_type", "fmp4",
        "-hls_fmp4_init_filename", "init.mp4", "-hls_segment_filename", os.path.join(hdir, "seg%03d.mp4"),
        os.path.join(hdir, "playlist.m3u8"))
    # artifacts serve no .m3u8 type: hls.js reads the playlist as text, the system player gets a data URL
    playlist = os.path.join(hdir, "playlist.m3u8")
    lines = open(playlist).read().splitlines()
    td = next(int(l.split(":")[1]) for l in lines if l.startswith("#EXT-X-TARGETDURATION"))
    segs = [[float(l.split(":")[1].rstrip(",")), "h/" + lines[k + 1]] for k, l in enumerate(lines) if l.startswith("#EXTINF")]
    os.replace(playlist, os.path.join(hdir, "playlist.txt"))
    big = max(os.path.getsize(os.path.join(hdir, f)) for f in os.listdir(hdir))
    if big > LIMIT:
        raise SystemExit(f"an HLS segment is {big / 1e6:.1f} MB, over the artifact file limit")

    # 2) fallback: the 540p copy in three files, cut at keyframes inside narration pauses
    if not os.path.exists(small):
        make_small()
    pk = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries",
                                  "packet=pts_time,flags", "-of", "csv=p=0", small]).decode().splitlines()
    kf = [float(r[0]) for r in csv.reader(pk) if len(r) >= 2 and "K" in r[1]]
    pauses = narration_pauses(edl)
    inpause = [k for k in kf if any(a <= k <= b for a, b in pauses)]
    cuts = [min(inpause, key=lambda k: abs(k - x)) for x in (total / 3, 2 * total / 3)]
    run("ffmpeg", "-loglevel", "error", "-y", "-i", small, "-map", "0:v", "-c", "copy", "-f", "segment",
        "-segment_times", ",".join(f"{c - 0.02:.4f}" for c in cuts), "-reset_timestamps", "1", os.path.join(tmp, "lo%d.mp4"))
    mix = os.path.join(ROOT, "build", "audio", "mix.wav")
    lo, t0 = [], 0
    for i in range(3):
        v = os.path.join(tmp, f"lo{i}.mp4")
        n = frames(v)
        start, dur = t0 / FPS, n / FPS
        a = os.path.join(tmp, f"lo{i}.m4a")
        run("ffmpeg", "-loglevel", "error", "-y", "-ss", f"{start:.6f}", "-t", f"{dur:.6f}", "-i", mix, "-c:a", "aac", "-b:a", "64k", a)
        name = f"lo/part{i}.mp4"
        dst = os.path.join(outdir, name)
        run("ffmpeg", "-loglevel", "error", "-y", "-i", v, "-i", a, "-map", "0:v", "-map", "1:a", "-c", "copy", "-movflags", "+faststart", dst)
        if os.path.getsize(dst) > LIMIT:
            raise SystemExit(f"{name} is over the artifact file limit")
        lo.append({"src": name, "start": round(start, 4), "dur": round(dur, 4)})
        t0 += n
    if t0 != round(total * FPS):
        raise SystemExit(f"fallback parts have {t0} frames, expected {round(total * FPS)}")

    # 3) poster, page
    run("ffmpeg", "-loglevel", "error", "-y", "-ss", "35.5", "-i", master, "-frames:v", "1",
        "-vf", "scale=1280:720:flags=lanczos", "-q:v", "4", os.path.join(outdir, "poster.jpg"))
    chapters = [{"t": round(0 if k == 0 else o + edl["xfade"] / 2, 2), "n": num, "title": title}
                for k, (o, (num, title)) in enumerate(zip(edl["offsets"], CHAPTERS))]
    manifest = {"total": total, "hls": "h/playlist.txt", "init": "h/init.mp4", "td": td, "segs": segs, "lo": lo, "chapters": chapters,
                "cues": srt_cues(os.path.join(ROOT, "build", "subtitles.srt"))}
    page = open(os.path.join(ROOT, "web", "player.html"), encoding="utf-8").read()
    page = page.replace("/*MANIFEST*/null", json.dumps(manifest, ensure_ascii=False, separators=(",", ":")))
    open(os.path.join(outdir, "index.html"), "w", encoding="utf-8").write(page)
    print(f"wrote {outdir}: {len(os.listdir(hdir))} stream files, fallback cuts at {cuts[0]:.2f} s and {cuts[1]:.2f} s")


if __name__ == "__main__":
    main()
