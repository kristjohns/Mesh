"""Split the final video into <15 MB parts for the web player (web/index.html).

Cuts (web/cuts.json) sit in narration pauses, where assemble.py forces keyframes, so a
part boundary never falls inside a spoken sentence. Video is stream-copied;
each part gets its own AAC track cut sample-exactly from the master mix, so the
audio of a part covers exactly its video span.

Usage: python3 tools_webparts.py [master.mp4] [outdir]
"""
import json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
master = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(ROOT), "output", "fea_best_practice_subsea_wellhead.mp4")
outdir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "build", "web")
FPS = 30
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


def main():
    os.makedirs(os.path.join(outdir, "v"), exist_ok=True)
    tmp = os.path.join(ROOT, "build", "webtmp")
    os.makedirs(tmp, exist_ok=True)
    edl = json.load(open(os.path.join(ROOT, "build", "edl.json")))
    total = round((edl["offsets"][-1] + edl["durations"][-1]) * FPS) / FPS
    cuts = json.load(open(os.path.join(ROOT, "web", "cuts.json")))
    bounds = [0.0] + cuts + [total]
    # video: stream copy at the forced keyframes (nudged early so rounding can't skip one)
    run("ffmpeg", "-loglevel", "error", "-y", "-i", master, "-map", "0:v", "-c", "copy", "-f", "segment",
        "-segment_times", ",".join(f"{c - 0.02:.4f}" for c in cuts), "-reset_timestamps", "1",
        os.path.join(tmp, "v%02d.mp4"))
    mix = os.path.join(ROOT, "build", "audio", "mix.wav")
    parts, t0 = [], 0
    for i in range(len(bounds) - 1):
        vpath = os.path.join(tmp, f"v{i:02d}.mp4")
        n = frames(vpath)
        start, dur = t0 / FPS, n / FPS
        expect = round((bounds[i + 1] - bounds[i]) * FPS)
        if n != expect:
            raise SystemExit(f"part {i}: {n} frames, expected {expect} (a cut missed its keyframe)")
        apath = os.path.join(tmp, f"a{i:02d}.m4a")
        run("ffmpeg", "-loglevel", "error", "-y", "-ss", f"{start:.6f}", "-t", f"{dur:.6f}", "-i", mix,
            "-c:a", "aac", "-b:a", "160k", apath)
        name = f"v/part{i:02d}.mp4"
        dst = os.path.join(outdir, name)
        run("ffmpeg", "-loglevel", "error", "-y", "-i", vpath, "-i", apath, "-map", "0:v", "-map", "1:a",
            "-c", "copy", "-movflags", "+faststart", dst)
        size = os.path.getsize(dst)
        if size > 14.8e6:
            raise SystemExit(f"{name} is {size / 1e6:.2f} MB, over the artifact file limit")
        parts.append({"src": name, "start": round(start, 4), "dur": round(dur, 4), "mb": round(size / 1e6, 2)})
        print(name, f"{start:8.3f} +{dur:7.3f}s  {size / 1e6:5.2f} MB")
        t0 += n
    chapters = [{"t": round(0 if k == 0 else o + edl["xfade"] / 2, 2), "n": num, "title": title}
                for k, (o, (num, title)) in enumerate(zip(edl["offsets"], CHAPTERS))]
    manifest = {"total": round(t0 / FPS, 4), "parts": parts, "chapters": chapters,
                "cues": srt_cues(os.path.join(ROOT, "build", "subtitles.srt"))}
    # poster: the title card from the intro
    run("ffmpeg", "-loglevel", "error", "-y", "-ss", "35.5", "-i", master, "-frames:v", "1",
        "-vf", "scale=1280:720:flags=lanczos", "-q:v", "4", os.path.join(outdir, "poster.jpg"))
    page = open(os.path.join(ROOT, "web", "player.html"), encoding="utf-8").read()
    page = page.replace("/*MANIFEST*/null", json.dumps(manifest, ensure_ascii=False, separators=(",", ":")))
    open(os.path.join(outdir, "index.html"), "w", encoding="utf-8").write(page)
    print("wrote", outdir, f"{len(parts)} parts, {sum(p['mb'] for p in parts):.1f} MB")


if __name__ == "__main__":
    main()
