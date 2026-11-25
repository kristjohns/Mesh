import subprocess, sys
from PIL import Image
def sheet(video, times, out, cols=4):
    ims = []
    for t in times:
        fn = f"/home/user/Mesh/video/build/check/f_{t}.png"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(t), "-i", video, "-frames:v", "1", fn], check=True)
        ims.append(Image.open(fn))
    w, h = ims[0].size
    rows = (len(ims) + cols - 1) // cols
    S = Image.new("RGB", (w * cols, h * rows))
    for i, im in enumerate(ims):
        S.paste(im, ((i % cols) * w, (i // cols) * h))
    S.save(out)
if __name__ == "__main__":
    video, out = sys.argv[1], sys.argv[2]
    times = [float(t) for t in sys.argv[3].split(",")]
    cols = int(sys.argv[4]) if len(sys.argv) > 4 else 4
    sheet(video, times, out, cols)
