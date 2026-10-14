"""Contact sheets of a rendered chunk: python3 tools_review.py <scene> [step_seconds] [start] [end]"""
import os
import subprocess
import sys
import tempfile
from PIL import Image, ImageDraw, ImageFont

scene = sys.argv[1]
step = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0
src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build", "chunks", scene + ".mp4")
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src]).decode())
start = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
end = float(sys.argv[4]) if len(sys.argv) > 4 else dur
tmp = tempfile.mkdtemp()
ts = []
t = start
while t < end:
    ts.append(t)
    t += step
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22) if os.path.exists("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf") else None
ims = []
for i, t in enumerate(ts):
    f = os.path.join(tmp, f"{i:04d}.png")
    subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", src, "-frames:v", "1", "-vf", "scale=640:360", f], check=True)
    im = Image.open(f).convert("RGB")
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 92, 30], fill=(0, 0, 0))
    d.text((6, 3), f"{t:6.1f}s", fill=(255, 220, 80), font=font)
    ims.append(im)
cols = 3
out_dir = os.path.join("/tmp/claude-0/-home-user-Mesh/c131553b-1455-59eb-a52d-b9f2446358da/scratchpad", "review")
os.makedirs(out_dir, exist_ok=True)
per = 12
for p in range(0, len(ims), per):
    grp = ims[p:p + per]
    rows = (len(grp) + cols - 1) // cols
    W = Image.new("RGB", (640 * cols, 360 * rows))
    for i, im in enumerate(grp):
        W.paste(im, ((i % cols) * 640, (i // cols) * 360))
    path = os.path.join(out_dir, f"{scene}_{p // per:02d}.png")
    W.save(path)
    print(path)
