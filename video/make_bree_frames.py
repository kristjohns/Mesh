"""Progressive-reveal frames of the numerically computed Bree diagram."""
import os
import numpy as np
from PIL import Image
RES = os.path.join(os.path.dirname(__file__), "..", "fatigue_fea", "results")
OUT = os.path.join(os.path.dirname(__file__), "build", "frames", "bree_fill")
os.makedirs(OUT, exist_ok=True)
d = np.load(os.path.join(RES, "bree_map.npz"))
cls, xs, ys, rat = d["cls"], d["xs"], d["ys"], d["ratchet"]
ny, nx = cls.shape
cols = {0: (76, 201, 240), 1: (122, 229, 130), 2: (247, 179, 43), 3: (255, 89, 100)}
rgb = np.zeros((ny, nx, 3))
for k, c in cols.items():
    rgb[cls == k] = c
# shade ratcheting by rate
r = np.clip(np.log10(np.maximum(np.abs(rat), 1e-4)) / 2.0 + 1.0, 0.35, 1.0)
rgb[cls == 3] = rgb[cls == 3] * r[cls == 3][:, None]
X, Y = np.meshgrid(xs, ys)
prog = 0.5 * (X / 1.0 + Y / 4.0)
N = 60
S = 10
for f in range(N + 1):
    p = f / N
    a = np.clip((p * 1.02 - prog) / 0.04, 0, 1) if f < N else np.ones_like(prog)
    img = np.zeros((ny, nx, 4), np.uint8)
    img[..., :3] = rgb.astype(np.uint8)
    img[..., 3] = (a * 235).astype(np.uint8)
    im = Image.fromarray(img[::-1], "RGBA").resize((nx * S, ny * S), Image.NEAREST)
    im.save(os.path.join(OUT, f"{f:04d}.png"))
print("ok", N + 1)
