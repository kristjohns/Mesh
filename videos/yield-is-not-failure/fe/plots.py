"""Field plots for the video: elastic part shaded by sigma_vm/sigma_Y, plastic part by equivalent plastic strain."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.tri as mtri  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, to_rgb  # noqa: E402

BG = "#0B0F19"
EL = LinearSegmentedColormap.from_list("el", ["#16233A", "#1F4E7A", "#2F86B8", "#6FC3DF", "#CFEFF5"])
PL = LinearSegmentedColormap.from_list("pl", ["#FF5A1F", "#FF8A1F", "#FFB627", "#FFE66D", "#FFFFFF"])


def field_colors(model, vm_nodal, eb_nodal, sy, eb_lo=1e-5, eb_hi=5e-2):
    """Per-subtriangle RGB: elastic -> blue ramp by vm/sy; plastic -> orange->white by log(ebar)."""
    tri = model.subtriangles()
    vm = vm_nodal[tri].mean(axis=1)
    eb = eb_nodal[tri].mean(axis=1)
    rgb = EL(np.clip(vm / sy, 0, 1))[:, :3]
    pl = eb > eb_lo
    if pl.any():
        x = (np.log10(np.clip(eb[pl], eb_lo, eb_hi)) - np.log10(eb_lo)) / (np.log10(eb_hi) - np.log10(eb_lo))
        rgb[pl] = PL(x)[:, :3]
    return tri, rgb


def draw_field(model, u, vm_nodal, eb_nodal, sy, fname, win, size=(8, 6), dpi=200, mirror=(), scale=0.0,
               outline=True, swap=False, shift=(0.0, 0.0)):
    """Render the coloured field; mirror: tuple of 'x'/'y' to reflect a symmetric model for display."""
    X = model.X + scale * u.reshape(-1, 2) + np.asarray(shift)[None, :]
    tri, rgb = field_colors(model, vm_nodal, eb_nodal, sy)
    fig = plt.figure(figsize=size, dpi=dpi, facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_facecolor(BG)
    variants = [(1, 1)]
    if "x" in mirror:
        variants += [(-1, 1) for _ in range(1)]
    if "y" in mirror:
        variants += [(s, -1) for s, _ in list(variants)]
    for sx, sy_ in variants:
        xx, yy = X[:, 0] * sx, X[:, 1] * sy_
        if swap:
            xx, yy = yy, xx
        T = mtri.Triangulation(xx, yy, tri)
        ax.tripcolor(T, facecolors=np.arange(len(tri)), cmap=matplotlib.colors.ListedColormap(rgb),
                     edgecolors="none", vmin=0, vmax=len(tri) - 1, rasterized=True)
        if outline:
            # yield boundary: contour of plastic indicator
            ind = (eb_nodal > 1e-5).astype(float)
            Tn = mtri.Triangulation(xx, yy, tri)
            if ind.max() > 0 and ind.min() < 1:
                ax.tricontour(Tn, ind, levels=[0.5], colors=["#FFE66D"], linewidths=1.2)
    ax.set_xlim(win[0], win[1]); ax.set_ylim(win[2], win[3]); ax.set_aspect("equal"); ax.axis("off")
    fig.savefig(fname, facecolor=BG)
    plt.close(fig)


def draw_contour(model, values, fname, win, vmax, cmap="turbo", levels=14, size=(8, 6), dpi=200, mirror=(),
                 swap=False, mark=None):
    X = model.X
    tri = model.subtriangles()
    fig = plt.figure(figsize=size, dpi=dpi, facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_facecolor(BG)
    variants = [(1, 1)]
    if "x" in mirror:
        variants.append((-1, 1))
    if "y" in mirror:
        variants += [(s, -1) for s, _ in list(variants)]
    lv = np.linspace(0, vmax, levels + 1)
    for sx, sy_ in variants:
        xx, yy = X[:, 0] * sx, X[:, 1] * sy_
        if swap:
            xx, yy = yy, xx
        T = mtri.Triangulation(xx, yy, tri)
        ax.tricontourf(T, np.clip(values, 0, vmax * 0.99999), levels=lv, cmap=cmap)
    ax.set_xlim(win[0], win[1]); ax.set_ylim(win[2], win[3]); ax.set_aspect("equal"); ax.axis("off")
    fig.savefig(fname, facecolor=BG)
    plt.close(fig)
