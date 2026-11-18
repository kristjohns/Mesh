"""Helpers shared by the "Yield is not failure" scenes (on top of common.py)."""
import os
import sys

import numpy as np
from manim import *  # noqa: F401,F403
from PIL import Image

from common import (BG, BUILD, C_BAD, C_GOOD, C_HYD, C_SHEAR, C_STEEL, C_TRESCA, C_VM, C_X, C_Y, C_YIELD, C_Z,  # noqa: F401
                    DIM, DUR, FAINT, INK, PANEL, ROOT, M, NScene, T, load_json)

sys.path.insert(0, os.path.join(ROOT, "fe"))
FR = os.path.join(BUILD, "frames")

EL_COLS = ["#16233A", "#1F4E7A", "#2F86B8", "#6FC3DF", "#CFEFF5"]      # same ramps as fe/plots.py
PL_COLS = ["#FF5A1F", "#FF8A1F", "#FFB627", "#FFE66D", "#FFFFFF"]
C_FRONT = "#FFE66D"                                                    # yield boundary
C_EPP = "#4D96FF"
C_TRUE = "#F15BB5"
C_THEORY = "#E8EDF5"
C_ASME = "#00F5D4"


def ramp(colors, n):
    from matplotlib.colors import LinearSegmentedColormap, to_hex
    cm = LinearSegmentedColormap.from_list("r", colors)
    return [to_hex(cm(i / max(1, n - 1))) for i in range(n)]


def ramp_at(colors, x):
    from matplotlib.colors import LinearSegmentedColormap, to_hex
    return to_hex(LinearSegmentedColormap.from_list("r", colors)(float(np.clip(x, 0, 1))))


def ramp_bar(colors, width=2.4, height=0.2, n=40):
    cells = VGroup(*[Rectangle(width=width / n, height=height, fill_color=c, fill_opacity=1, stroke_width=0)
                     for c in ramp(colors, n)]).arrange(RIGHT, buff=0)
    return VGroup(cells, SurroundingRectangle(cells, buff=0, stroke_color=DIM, stroke_width=1))


def field_legend(width=2.2, size=19):
    """Legend for the FE field frames: elastic blue ramp, plastic orange ramp, yield boundary."""
    el = ramp_bar(EL_COLS, width)
    el_t = VGroup(T("elastic", size, INK), M(r"\sigma_{vm}/\sigma_Y", size=size + 5)).arrange(RIGHT, buff=0.12)
    el_l = VGroup(T("0", size - 2, DIM), T("1", size - 2, DIM))
    pl = ramp_bar(PL_COLS, width)
    pl_t = VGroup(T("plastic", size, INK), M(r"\bar\varepsilon_p", size=size + 6)).arrange(RIGHT, buff=0.12)
    pl_l = VGroup(T("0.001 %", size - 3, DIM), T("5 %", size - 3, DIM))
    yb = VGroup(Line(ORIGIN, RIGHT * 0.45, color=C_FRONT, stroke_width=3), T("yield boundary", size, INK)).arrange(RIGHT, buff=0.12)
    g1 = VGroup(el_t, el); el.next_to(el_t, DOWN, buff=0.08, aligned_edge=LEFT)
    el_l[0].next_to(el, DOWN, buff=0.06, aligned_edge=LEFT); el_l[1].next_to(el, DOWN, buff=0.06, aligned_edge=RIGHT)
    g1.add(el_l)
    g2 = VGroup(pl_t, pl); pl.next_to(pl_t, DOWN, buff=0.08, aligned_edge=LEFT)
    pl_l[0].next_to(pl, DOWN, buff=0.06, aligned_edge=LEFT); pl_l[1].next_to(pl, DOWN, buff=0.06, aligned_edge=RIGHT)
    g2.add(pl_l)
    return VGroup(g1, g2, yb).arrange(RIGHT, buff=0.45, aligned_edge=UP)


class ImageSeq(ImageMobject):
    """PNG sequence shown at a fixed size; the displayed frame follows `index_fn()` (e.g. a ValueTracker)."""

    def __init__(self, folder, height, index_fn=None, start=0, **kw):
        self.folder = os.path.join(FR, folder)
        self.files = sorted(f for f in os.listdir(self.folder) if f.endswith(".png"))
        super().__init__(os.path.join(self.folder, self.files[start]), **kw)
        self.height = height
        self.index_fn = index_fn
        self._idx = start
        if index_fn is not None:
            self.add_updater(ImageSeq._upd)

    def set_frame(self, i):
        i = int(np.clip(i, 0, len(self.files) - 1))
        if i != self._idx:
            self._idx = i
            self.pixel_array = np.array(Image.open(os.path.join(self.folder, self.files[i])).convert("RGBA"))
        return self

    def _upd(self):
        self.set_frame(self.index_fn())

    def to_xy(self, fx, fy):
        """Scene point of a normalized image position (fx from left, fy from top)."""
        c = self.get_center()
        return c + np.array([(fx - 0.5) * self.width, (0.5 - fy) * self.height, 0.0])


def frame_index(frame_keys):
    """Map a curve index k (curve[j] <-> solver step j+1) to the last frame with key-1 <= k."""
    ci = np.asarray(frame_keys) - 1

    def f(k):
        return int(max(0, np.searchsorted(ci, k + 1e-6, side="right") - 1))
    return f


# ------------------------------------------------------------------ plots
def axes(xr, yr, w, h, step_x=None, step_y=None):
    xr = list(xr) + ([step_x] if step_x else [])
    yr = list(yr) + ([step_y] if step_y else [])
    ax = Axes(x_range=xr, y_range=yr, x_length=w, y_length=h, tips=False,
              axis_config=dict(color=DIM, stroke_width=2, include_ticks=True, tick_size=0.05))
    return ax


def ticks(ax, xs=(), ys=(), xfmt="{:g}", yfmt="{:g}", size=18):
    g = VGroup()
    x0, y0 = ax.x_range[0], ax.y_range[0]
    for x in xs:
        g.add(T(xfmt.format(x), size, DIM).next_to(ax.c2p(x, y0), DOWN, buff=0.12))
    for y in ys:
        g.add(T(yfmt.format(y), size, DIM).next_to(ax.c2p(x0, y), LEFT, buff=0.12))
    return g


def ax_labels(ax, xl, yl, size=22, math=False):
    mk = (lambda s: M(s, size=size + 6, color=INK)) if math else (lambda s: T(s, size, INK))
    xlab = mk(xl).next_to(ax.x_axis.get_end(), DOWN, buff=0.45).align_to(ax.x_axis.get_end(), RIGHT)
    ylab = mk(yl).next_to(ax.y_axis.get_end(), UP, buff=0.18).align_to(ax.y_axis, LEFT)
    return VGroup(xlab, ylab)


def data_curve(ax, xs, ys, color, width=4.0, dashed=False):
    pts = [ax.c2p(float(x), float(y)) for x, y in zip(xs, ys)]
    c = VMobject(stroke_color=color, stroke_width=width)
    c.set_points_as_corners(pts)
    if dashed:
        return DashedVMobject(c, num_dashes=max(10, len(pts) // 2), dashed_ratio=0.55)
    return c


def grow_with(full, k, n):
    """Partial copy of `full` (built from n data points) that follows tracker k in data-index units."""
    part = full.copy()

    def upd(m):
        a = float(np.clip(k.get_value() / max(1, n - 1), 0, 1))
        m.pointwise_become_partial(full, 0, max(a, 1e-4))
    part.add_updater(upd)
    upd(part)
    return part


def follow(ax, xs, ys, k, color=INK, radius=0.07):
    xs, ys = np.asarray(xs, float), np.asarray(ys, float)
    idx = np.arange(len(xs))
    d = Dot(radius=radius, color=color)
    d.set_stroke(BG, width=2, background=True)

    def upd(m):
        kk = float(np.clip(k.get_value(), 0, len(xs) - 1))
        m.move_to(ax.c2p(np.interp(kk, idx, xs), np.interp(kk, idx, ys)))
    d.add_updater(upd)
    upd(d)
    return d


def hline(ax, y, color, x0=None, x1=None, dashed=True, width=2.5):
    x0 = ax.x_range[0] if x0 is None else x0
    x1 = ax.x_range[1] if x1 is None else x1
    L = (DashedLine if dashed else Line)(ax.c2p(x0, y), ax.c2p(x1, y), color=color, stroke_width=width)
    return L


def vline(ax, x, color, y0=None, y1=None, dashed=True, width=2.5):
    y0 = ax.y_range[0] if y0 is None else y0
    y1 = ax.y_range[1] if y1 is None else y1
    return (DashedLine if dashed else Line)(ax.c2p(x, y0), ax.c2p(x, y1), color=color, stroke_width=width)


# ------------------------------------------------------------------ text blocks
def case_header(num, title, sub=None):
    a = T(f"CASE {num}", 22, C_YIELD, weight=BOLD)
    b = T(title, 30, INK, weight=SEMIBOLD)
    g = VGroup(a, b).arrange(RIGHT, buff=0.3, aligned_edge=DOWN)
    if sub:
        s = T(sub, 20, DIM).next_to(g, DOWN, buff=0.1, aligned_edge=LEFT)
        g = VGroup(g, s)
    return g.to_corner(UL, buff=0.35)


def case_card(scene, num, title, crit, dur=2.2):
    n = T(f"CASE {num}", 30, C_YIELD, weight=BOLD)
    t = T(title, 50, INK, weight=SEMIBOLD)
    c = T(crit, 26, DIM)
    g = VGroup(n, t, c).arrange(DOWN, buff=0.3)
    line = Line(LEFT * 3.0, RIGHT * 3.0, stroke_width=2, color=C_YIELD).next_to(t, DOWN, buff=0.18).set_opacity(0.8)
    c.next_to(line, DOWN, buff=0.25)
    scene.play(FadeIn(n, shift=0.2 * DOWN), FadeIn(t, shift=0.2 * UP), Create(line), run_time=0.8)
    scene.play(FadeIn(c), run_time=0.4)
    scene.wait(max(0.1, dur - 1.9))
    scene.play(FadeOut(VGroup(n, t, c, line)), run_time=0.7)


def panel(title, rows, color=C_ASME, width=None, size=22, title_size=21, buff=0.16, pad=0.28):
    """Rounded panel: title line in `color`, then rows (strings -> Text, or mobjects)."""
    ttl = T(title, title_size, color, weight=BOLD)
    body = VGroup(*[T(r, size, INK) if isinstance(r, str) else r for r in rows]).arrange(DOWN, buff=buff, aligned_edge=LEFT)
    content = VGroup(ttl, body).arrange(DOWN, buff=0.22, aligned_edge=LEFT)
    w = max(width or 0.0, content.width + 2 * pad)
    box = RoundedRectangle(width=w, height=content.height + 2 * pad, corner_radius=0.14, stroke_color=color,
                           stroke_width=2, fill_color=PANEL, fill_opacity=0.92)
    content.move_to(box).align_to(box, LEFT).shift(RIGHT * pad)
    g = VGroup(box, content)
    g.box, g.title, g.body = box, ttl, body
    return g


def tick_mark(color=C_GOOD, s=0.32, width=6):
    return VMobject(stroke_color=color, stroke_width=width).set_points_as_corners(
        [[-0.5 * s, 0.02 * s, 0], [-0.15 * s, -0.36 * s, 0], [0.55 * s, 0.46 * s, 0]])


def cross_mark(color=C_BAD, s=0.3, width=6):
    return VGroup(Line([-s / 2, -s / 2, 0], [s / 2, s / 2, 0], color=color, stroke_width=width),
                  Line([-s / 2, s / 2, 0], [s / 2, -s / 2, 0], color=color, stroke_width=width))


def strike(mob, color=C_BAD, width=4):
    return Line(mob.get_left() + LEFT * 0.08, mob.get_right() + RIGHT * 0.08, color=color, stroke_width=width)


def row(*items, buff=0.14):
    return VGroup(*[T(i, 22, INK) if isinstance(i, str) else i for i in items]).arrange(RIGHT, buff=buff)


def callout(text_mob, target, direction=UR, color=INK, dist=1.0, buff=0.08):
    """Label placed at target + direction*dist with a thin leader line to target."""
    text_mob.move_to(np.asarray(target) + np.asarray(direction) * dist)
    start = text_mob.get_critical_point(-np.sign(np.asarray(direction)))
    ln = Line(start, target, color=color, stroke_width=2, buff=buff)
    return VGroup(text_mob, ln)
