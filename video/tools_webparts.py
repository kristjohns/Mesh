"""Split the final video into <15 MB parts for the web player (web/index.html).

Cuts (web/cuts.json) sit in narration pauses, where assemble.py forces keyframes, so a
part boundary never falls inside a spoken sentence. Video is stream-copied;
each part gets its own AAC track cut sample-exactly from the master mix, so the
audio of a part covers exactly its video span.

Usage: python3 tools_webparts.py [--video fatigue] [master.mp4] [outdir]
"""
import json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from projects import project  # noqa: E402

P = project()
BUILD = P["build_dir"]
FLAGS = ("--video", "--prefix")
PAGE_ONLY = "--page-only" in sys.argv   # rewrite captions and page from <outdir>/parts.json, keep the video parts
pos = [a for i, a in enumerate(sys.argv[1:], 1) if a not in FLAGS and sys.argv[i - 1] not in FLAGS and not a.startswith("--")]
# folder of the parts inside the page; a new folder lets a new version upload next to the live one
PREFIX = sys.argv[sys.argv.index("--prefix") + 1] if "--prefix" in sys.argv else "v"
master = pos[0] if len(pos) > 0 else P["out_path"]
outdir = pos[1] if len(pos) > 1 else os.path.join(BUILD, "web")
PLAYER = os.path.join(ROOT, "web", "player.html" if P["id"] == "fea" else f"{P['id']}_player.html")
FPS = 30
CHAPTERS = P["chapters"]


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


def vtt(cues, start, dur):
    """WebVTT of the cues inside one part, on the part's own clock (for the iPhone's native full screen)"""
    def ts(x):
        x = max(0.0, x)
        return f"{int(x // 3600):02d}:{int(x % 3600 // 60):02d}:{x % 60:06.3f}"
    out = ["WEBVTT", ""]
    for a, b, text in cues:
        if b <= start or a >= start + dur:
            continue
        out += [f"{ts(a - start)} --> {ts(min(b, start + dur) - start)}", text, ""]
    return "\n".join(out)


def main():
    os.makedirs(os.path.join(outdir, PREFIX), exist_ok=True)
    edl = json.load(open(os.path.join(BUILD, "edl.json")))
    cues = srt_cues(os.path.join(BUILD, "subtitles.srt"))
    if PAGE_ONLY:
        parts = json.load(open(os.path.join(outdir, "parts.json")))
        return write_page(parts, edl, cues)
    tmp = os.path.join(BUILD, "webtmp")
    os.makedirs(tmp, exist_ok=True)
    total = round((edl["offsets"][-1] + edl["durations"][-1]) * FPS) / FPS
    cuts = json.load(open(P["cuts_path"]))
    bounds = [0.0] + cuts + [total]
    # video: stream copy at the forced keyframes (nudged early so rounding can't skip one)
    run("ffmpeg", "-loglevel", "error", "-y", "-i", master, "-map", "0:v", "-c", "copy", "-f", "segment",
        "-segment_times", ",".join(f"{c - 0.02:.4f}" for c in cuts), "-reset_timestamps", "1",
        os.path.join(tmp, "v%02d.mp4"))
    mix = os.path.join(BUILD, "audio", "mix.wav")
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
        name = f"{PREFIX}/part{i:02d}.mp4"
        dst = os.path.join(outdir, name)
        run("ffmpeg", "-loglevel", "error", "-y", "-i", vpath, "-i", apath, "-map", "0:v", "-map", "1:a",
            "-c", "copy", "-movflags", "+faststart", dst)
        size = os.path.getsize(dst)
        if size > 14.8e6:
            raise SystemExit(f"{name} is {size / 1e6:.2f} MB, over the artifact file limit")
        parts.append({"src": name, "start": round(start, 4), "dur": round(dur, 4), "mb": round(size / 1e6, 2)})
        print(name, f"{start:8.3f} +{dur:7.3f}s  {size / 1e6:5.2f} MB")
        t0 += n
    json.dump(parts, open(os.path.join(outdir, "parts.json"), "w"))
    write_page(parts, edl, cues)


def write_page(parts, edl, cues):
    for p in parts:
        p["vtt"] = p["src"][:-4] + ".vtt.txt"   # WebVTT; artifacts serve .txt, not .vtt
        open(os.path.join(outdir, p["vtt"]), "w", encoding="utf-8").write(vtt(cues, p["start"], p["dur"]))
    t0 = round((parts[-1]["start"] + parts[-1]["dur"]) * FPS)
    chapters = [{"t": round(0 if k == 0 else o + edl["xfade"] / 2, 2), "n": num, "title": title}
                for k, (o, (num, title)) in enumerate(zip(edl["offsets"], CHAPTERS))]
    manifest = {"total": round(t0 / FPS, 4), "parts": parts, "chapters": chapters,
                "cues": cues}
    # poster: the title card from the intro
    run("ffmpeg", "-loglevel", "error", "-y", "-ss", str(P["poster"]), "-i", master, "-frames:v", "1",
        "-vf", "scale=1280:720:flags=lanczos", "-q:v", "4", os.path.join(outdir, "poster.jpg"))
    page = open(PLAYER, encoding="utf-8").read()
    page = page.replace("/*MANIFEST*/null", json.dumps(manifest, ensure_ascii=False, separators=(",", ":")))
    open(os.path.join(outdir, "index.html"), "w", encoding="utf-8").write(page)
    print("wrote", outdir, f"{len(parts)} parts, {sum(p['mb'] for p in parts):.1f} MB")


if __name__ == "__main__":
    main()
