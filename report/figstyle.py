"""Shared style and helpers for the report figures (light theme, print-ready)."""
import os, sys, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.tri import Triangulation
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "fatigue_fea", "results")
FIG = os.path.join(HERE, "figs")
os.makedirs(FIG, exist_ok=True)
sys.path.insert(0, os.path.join(HERE, "..", "fatigue_fea"))

# palette (print)
BLUE = "#1C86C8"
GREEN = "#2A9D4B"
ORANGE = "#E8890C"
RED = "#D7263D"
VIOLET = "#7B4FD0"
PINK = "#D6336C"
GRAY = "#6B7280"
LGRAY = "#D1D5DB"
TXT = "#1F2933"
C_EL, C_SD, C_AP, C_RT = BLUE, GREEN, ORANGE, RED

TEXTWIDTH = 6.85    # inches (A4, 1.8 cm margins)

matplotlib.rcParams.update({
    "font.family": "Lato",
    "font.size": 8.5,
    "axes.titlesize": 9.5,
    "axes.titleweight": "bold",
    "axes.labelsize": 8.5,
    "axes.edgecolor": "#9CA3AF",
    "axes.linewidth": 0.8,
    "axes.labelcolor": TXT,
    "xtick.color": "#4B5563",
    "ytick.color": "#4B5563",
    "xtick.labelsize": 7.5,
    "ytick.labelsize": 7.5,
    "legend.fontsize": 7.5,
    "legend.frameon": False,
    "mathtext.fontset": "stixsans",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "savefig.dpi": 300,
    "figure.dpi": 150,
    "text.color": TXT,
})

STRESS_CMAP = matplotlib.colormaps["turbo"]
PLAST_CMAP = LinearSegmentedColormap.from_list("plast", ["#FFF7EC", "#FDD49E", "#FC8D59", "#D7301F", "#7F0000"])
CORE_CMAP = LinearSegmentedColormap.from_list("core", [(0.0, "#5BC0EB"), (0.03, "#5BC0EB"), (0.05, "#FDD9B5"),
                                                       (0.5, "#F4845F"), (1.0, "#9D0208")])

Q9_TRIS = np.array([[0, 4, 8], [4, 1, 8], [1, 5, 8], [5, 2, 8], [2, 6, 8], [6, 3, 8], [3, 7, 8], [7, 0, 8]])
Q9_OUTLINE = [0, 4, 1, 5, 2, 6, 3, 7, 0]

# material constants used throughout
E = 210000.0
SF, B, EF, C = 952.0, -0.089, 0.737, -0.668
KP, NP = 596.0, 0.076
SU, SY = 510.0, 355.0
KT = 3.249


def load(name):
    return np.load(os.path.join(RES, name))


def mirrored(nodes, elems, ux=None, uy=None, quadrants=4):
    sx = np.array([1, -1, 1, -1][:quadrants])
    sy = np.array([1, 1, -1, -1][:quadrants])
    nn = nodes.shape[0]
    P, Es, UX, UY = [], [], [], []
    for q in range(quadrants):
        P.append(nodes * np.array([sx[q], sy[q]]))
        e = elems + q * nn
        if sx[q] * sy[q] < 0:
            e = e[:, [0, 3, 2, 1, 7, 6, 5, 4, 8]]
        Es.append(e)
        if ux is not None:
            UX.append(ux * sx[q]); UY.append(uy * sy[q])
    out = (np.concatenate(P), np.concatenate(Es))
    if ux is not None:
        out = out + (np.concatenate(UX), np.concatenate(UY))
    return out


def field(ax, nodes, elems, values, vmin, vmax, cmap, mesh=False, lw=0.15, alpha=0.25):
    tris = elems[:, Q9_TRIS].reshape(-1, 3)
    tri = Triangulation(nodes[:, 0], nodes[:, 1], tris)
    m = ax.tripcolor(tri, np.clip(values, vmin, vmax), shading="gouraud", cmap=cmap, vmin=vmin, vmax=vmax,
                     rasterized=True)
    if mesh:
        segs = [nodes[e[Q9_OUTLINE]] for e in elems]
        ax.add_collection(LineCollection(segs, colors=(0.1, 0.1, 0.1, alpha), linewidths=lw, rasterized=True))
    ax.set_aspect("equal")
    return m


def clean(ax):
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


def panel_label(ax, s, x=-0.02, y=1.02, **kw):
    ax.text(x, y, s, transform=ax.transAxes, fontsize=9.5, fontweight="bold", va="bottom", ha="left", **kw)


def save(fig, name):
    fig.savefig(os.path.join(FIG, name + ".pdf"), bbox_inches="tight", pad_inches=0.02)
    fig.savefig(os.path.join(FIG, name + ".png"), bbox_inches="tight", pad_inches=0.02, dpi=160)
    plt.close(fig)


def strain_life(N, sf=SF, b=B, ef=EF, c=C, e=E):
    tN = 2 * np.asarray(N, float)
    return sf / e * tN ** b + ef * tN ** c


def ro_eps(s):
    return s / E + (np.abs(s) / KP) ** (1 / NP) * np.sign(s)
