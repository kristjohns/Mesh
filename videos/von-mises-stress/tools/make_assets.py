"""Static image assets: polycrystal micrograph-style illustration (Voronoi grains with lattices)."""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.path import Path  # noqa: E402
from scipy.spatial import Voronoi  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "build", "assets")
os.makedirs(OUT, exist_ok=True)
BG = "#0B0F19"


def polycrystal(fname="polycrystal.png", w=16.0, h=9.0, n=46, seed=7, spacing=0.085):
    rng = np.random.default_rng(seed)
    # Lloyd-relaxed seeds for even grain sizes
    pts = rng.uniform([0, 0], [w, h], size=(n, 2))
    for _ in range(4):
        mir = np.vstack([pts, pts * [-1, 1], pts * [1, -1], [2 * w, 0] + pts * [-1, 1], [0, 2 * h] + pts * [1, -1]])
        vor = Voronoi(mir)
        new = []
        for i in range(n):
            reg = vor.regions[vor.point_region[i]]
            poly = vor.vertices[reg]
            new.append(poly.mean(axis=0))
        pts = np.clip(np.array(new), 0.01, [w - 0.01, h - 0.01])
    mir = np.vstack([pts, pts * [-1, 1], pts * [1, -1], [2 * w, 0] + pts * [-1, 1], [0, 2 * h] + pts * [1, -1]])
    vor = Voronoi(mir)
    fig = plt.figure(figsize=(w, h), dpi=240, facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, w); ax.set_ylim(0, h); ax.axis("off"); ax.set_facecolor(BG)
    cmap = matplotlib.colormaps["twilight"]
    centers = []
    for i in range(n):
        reg = vor.regions[vor.point_region[i]]
        poly = vor.vertices[reg]
        th = rng.uniform(0, np.pi / 2)
        tint = cmap(0.15 + 0.7 * th / (np.pi / 2))
        ax.fill(poly[:, 0], poly[:, 1], color=tint, alpha=0.16, lw=0)
        # lattice clipped to the grain
        c = pts[i]
        R = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])
        k = np.arange(-40, 41)
        g = np.array(np.meshgrid(k, k)).reshape(2, -1).T * spacing
        lat = c + g @ R.T
        inside = Path(poly).contains_points(lat, radius=-spacing * 0.6)
        lat = lat[inside]
        ax.scatter(lat[:, 0], lat[:, 1], s=1.4, color="#C8D2E0", alpha=0.85, lw=0)
        ax.plot(*np.vstack([poly, poly[:1]]).T, color="#E8EDF5", lw=1.6, alpha=0.9)
        centers.append(c)
    fig.savefig(os.path.join(OUT, fname), facecolor=BG)
    plt.close(fig)
    np.save(os.path.join(OUT, "polycrystal_centers.npy"), np.array(centers) / [w, h])
    print("polycrystal written")


if __name__ == "__main__":
    polycrystal()
