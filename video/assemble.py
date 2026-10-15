"""Concatenate scene chunks with cross-fades, mux the soundtrack and subtitles.

Usage: python3 assemble.py [--video fatigue] [--crf 19] [--scale 1080|720] [--out path]
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from projects import project  # noqa: E402

P = project()
BUILD = P["build_dir"]
args = sys.argv[1:]
opt = lambda k, d: args[args.index(k) + 1] if k in args else d
crf = opt("--crf", "19")
scale = opt("--scale", "1080")
maxrate = opt("--maxrate", P.get("maxrate", "8M"))  # caps the few shots with shimmering fine detail
kf = opt("--keyframes", P["cuts_path"])  # keyframes where the web player splits the file
out = opt("--out", P["out_path"])
os.makedirs(os.path.dirname(out), exist_ok=True)
edl = json.load(open(os.path.join(BUILD, "edl.json")))
X = edl["xfade"]
ids, offsets = edl["ids"], edl["offsets"]
inputs = []
for i in ids:
    inputs += ["-i", os.path.join(BUILD, "chunks", f"{i}.mp4")]
filt = []
prev = "0:v"
for k in range(1, len(ids)):
    lab = f"v{k}"
    filt.append(f"[{prev}][{k}:v]xfade=transition=fade:duration={X}:offset={offsets[k]:.4f}[{lab}]")
    prev = lab
vf = f"[{prev}]" + ("scale=1280:720:flags=lanczos," if scale == "720" else "") + "format=yuv420p[vout]"
filt.append(vf)
n = len(ids)
# a hair early, so float rounding can never push a keyframe to the next frame
kf_args = ["-force_key_frames", ",".join(f"{x - 0.001:.4f}" for x in json.load(open(kf)))] if kf and os.path.exists(kf) else []
# explicit length: -shortest would stop at the last subtitle cue and cut the end card
total = offsets[-1] + edl["durations"][-1]
cmd = ["ffmpeg", "-y", "-loglevel", "error", "-stats", *inputs,
       "-i", os.path.join(BUILD, "audio", "mix.wav"),
       "-i", os.path.join(BUILD, "subtitles.srt"),
       "-filter_complex", ";".join(filt), "-map", "[vout]", "-map", f"{n}:a", "-map", f"{n + 1}:s",
       "-c:v", "libx264", "-preset", "slow", "-crf", crf, "-tune", "animation", "-r", "30",
       "-maxrate", maxrate, "-bufsize", maxrate, *kf_args,
       "-c:a", "aac", "-b:a", "192k", "-c:s", "mov_text", "-metadata:s:s:0", "language=eng",
       "-metadata", f"title={P['title']}",
       "-movflags", "+faststart", "-t", f"{total:.3f}", out]
print(" ".join(cmd[:8]), "...")
subprocess.run(cmd, check=True)
print("wrote", out)
