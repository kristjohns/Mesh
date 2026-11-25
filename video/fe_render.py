"""Render finite element result frames (transparent PNG) with matplotlib.

The quarter model is mirrored to show the full plate. Q9 elements are split
into 8 triangles for smooth Gouraud shading."""
import os, sys, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.tri import Triangulation
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "fatigue_fea", "results")
OUT = os.path.join(HERE, "build", "frames")
Q9_TRIS = np.array([[0, 4, 8], [4, 1, 8], [1, 5, 8], [5, 2, 8], [2, 6, 8], [6, 3, 8], [3, 7, 8], [7, 0, 8]])
Q9_OUTLINE = [0, 4, 1, 5, 2, 6, 3, 7, 0]

# FE-style rainbow for stress, fire for plastic strain
STRESS_CMAP = matplotlib.colormaps["turbo"]
PLAST_CMAP = LinearSegmentedColormap.from_list(
    "plast", ["#1a2240", "#3b2a6b", "#7a2f8f", "#c13a7a", "#f0605d", "#fca636", "#fcfdbf"])
DIVERGE = LinearSegmentedColormap.from_list(
    "div", ["#3a7bd5", "#4cc9f0", "#1b2440", "#f7b32b", "#ff5964"])


def mirrored(nodes, elems, ux=None, uy=None, quadrants=4):
    """Return full-model arrays from the quarter model: nodes (4n,2), elems, sign maps."""
    sx = np.array([1, -1, 1, -1][:quadrants])
    sy = np.array([1, 1, -1, -1][:quadrants])
    nn = nodes.shape[0]
    P, E, UX, UY = [], [], [], []
    for q in range(quadrants):
        P.append(nodes * np.array([sx[q], sy[q]]))
        e = elems + q * nn
        if sx[q] * sy[q] < 0:
            e = e[:, [0, 3, 2, 1, 7, 6, 5, 4, 8]]
        E.append(e)
        if ux is not None:
            UX.append(ux * sx[q])
            UY.append(uy * sy[q])
    out = (np.concatenate(P), np.concatenate(E))
    if ux is not None:
        out = out + (np.concatenate(UX), np.concatenate(UY))
    return out


def render_field(nodes, elems, values, fn, vmin, vmax, cmap, xlim, ylim, px_w=900,
                 mesh_lines=True, line_alpha=0.18, outline=True, dpi=100, hole=None):
    tris = elems[:, Q9_TRIS].reshape(-1, 3)
    tri = Triangulation(nodes[:, 0], nodes[:, 1], tris)
    w_in = px_w / dpi
    aspect = (ylim[1] - ylim[0]) / (xlim[1] - xlim[0])
    fig = plt.figure(figsize=(w_in, w_in * aspect), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_alpha(0.0)
    ax.patch.set_alpha(0.0)
    ax.tripcolor(tri, np.clip(values, vmin, vmax), shading="gouraud", cmap=cmap, vmin=vmin, vmax=vmax,
                 rasterized=True)
    if mesh_lines:
        segs = [nodes[e[Q9_OUTLINE]] for e in elems]
        ax.add_collection(LineCollection(segs, colors=(1, 1, 1, line_alpha), linewidths=0.35))
    fig.savefig(fn, transparent=True, dpi=dpi)
    plt.close(fig)


def _job(args):
    render_field(*args[0], **args[1])
    return args[0][4]


def plate_frames(case, field, steps_sel=None, vmin=0, vmax=400, cmap=STRESS_CMAP, scale=0.0,
                 tag=None, px_w=700, xlim=(-42, 42), ylim=(-62, 62), mesh_lines=True, source="F",
                 transform=None):
    """Render frames for a plate case. source 'F' (field steps) or 'EOC' (end-of-cycle)."""
    d = np.load(os.path.join(RES, f"plate_{case}.npz"))
    nodes, elems = d["nodes"], d["elems"]
    vals = d[f"{source}_{field}"] if field != "custom" else None
    ux, uy = d[f"{source}_ux"], d[f"{source}_uy"]
    n = ux.shape[0]
    idx = range(n) if steps_sel is None else steps_sel
    tag = tag or f"{case}_{field}_{source}"
    od = os.path.join(OUT, tag)
    os.makedirs(od, exist_ok=True)
    jobs = []
    files = []
    for j, i in enumerate(idx):
        v = vals[i] if transform is None else transform(d, i)
        P, E, UX, UY = mirrored(nodes, elems, ux[i], uy[i])
        V = np.tile(v, 4)
        Pd = P + scale * np.stack([UX, UY], axis=1)
        fn = os.path.join(od, f"{j:04d}.png")
        files.append(fn)
        if not os.path.exists(fn):
            jobs.append(((Pd, E, V, None, fn, vmin, vmax, cmap, xlim, ylim),
                         dict(px_w=px_w, mesh_lines=mesh_lines)))
    # fix arg order: render_field(nodes, elems, values, fn, ...)
    jobs = [((a[0], a[1], a[2], a[4], a[5], a[6], a[7], a[8], a[9]), k) for a, k in jobs]
    if jobs:
        with Pool(4) as p:
            p.map(_job2, jobs)
    return files


def _job2(args):
    a, k = args
    render_field(*a, **k)


def colorbar_png(fn, cmap, vmin, vmax, label, ticks, px_w=110, px_h=520, dpi=100, txt="#E8ECF4"):
    fig = plt.figure(figsize=(px_w / dpi, px_h / dpi), dpi=dpi)
    ax = fig.add_axes([0.08, 0.04, 0.32, 0.9])
    grad = np.linspace(vmin, vmax, 256)[:, None]
    ax.imshow(grad, aspect="auto", cmap=cmap, origin="lower", extent=[0, 1, vmin, vmax])
    ax.set_xticks([])
    ax.yaxis.tick_right()
    ax.set_yticks(ticks)
    ax.tick_params(colors=txt, labelsize=11, length=3)
    for s in ax.spines.values():
        s.set_visible(False)
    fig.patch.set_alpha(0)
    fig.savefig(fn, transparent=True, dpi=dpi)
    plt.close(fig)


if __name__ == "__main__":
    # quick test
    f = plate_frames("lcf", "vm", steps_sel=[10, 30], vmin=0, vmax=400, scale=20, tag="test_lcf_vm")
    print(f)
