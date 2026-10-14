"""Concatenate scene chunks with cross-fades, mux the soundtrack and subtitles.

Usage: python3 assemble.py [--crf 19] [--scale 1080|720] [--out path]
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[1:]
opt = lambda k, d: args[args.index(k) + 1] if k in args else d
crf = opt("--crf", "19")
scale = opt("--scale", "1080")
maxrate = opt("--maxrate", "8M")  # caps the few shots with shimmering fine detail
out = opt("--out", os.path.join(os.path.dirname(ROOT), "output", "fea_best_practice_subsea_wellhead.mp4"))
os.makedirs(os.path.dirname(out), exist_ok=True)
edl = json.load(open(os.path.join(ROOT, "build", "edl.json")))
X = edl["xfade"]
ids, offsets = edl["ids"], edl["offsets"]
inputs = []
for i in ids:
    inputs += ["-i", os.path.join(ROOT, "build", "chunks", f"{i}.mp4")]
filt = []
prev = "0:v"
for k in range(1, len(ids)):
    lab = f"v{k}"
    filt.append(f"[{prev}][{k}:v]xfade=transition=fade:duration={X}:offset={offsets[k]:.4f}[{lab}]")
    prev = lab
vf = f"[{prev}]" + ("scale=1280:720:flags=lanczos," if scale == "720" else "") + "format=yuv420p[vout]"
filt.append(vf)
n = len(ids)
# explicit length: -shortest would stop at the last subtitle cue and cut the end card
total = offsets[-1] + edl["durations"][-1]
cmd = ["ffmpeg", "-y", "-loglevel", "error", "-stats", *inputs,
       "-i", os.path.join(ROOT, "build", "audio", "mix.wav"),
       "-i", os.path.join(ROOT, "build", "subtitles.srt"),
       "-filter_complex", ";".join(filt), "-map", "[vout]", "-map", f"{n}:a", "-map", f"{n + 1}:s",
       "-c:v", "libx264", "-preset", "slow", "-crf", crf, "-tune", "animation", "-r", "30",
       "-maxrate", maxrate, "-bufsize", maxrate,
       "-c:a", "aac", "-b:a", "192k", "-c:s", "mov_text", "-metadata:s:s:0", "language=eng",
       "-metadata", "title=Meshing with Purpose - FEA best practice, subsea wellhead & template case study",
       "-movflags", "+faststart", "-t", f"{total:.3f}", out]
print(" ".join(cmd[:8]), "...")
subprocess.run(cmd, check=True)
print("wrote", out)
