"""Shared theme, helpers and the narration-synchronised base scene."""
import os, json
import numpy as np
from manim import *

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO = os.path.join(HERE, "audio")
FRAMES = os.path.join(HERE, "build", "frames")
RESULTS = os.path.join(HERE, "..", "fatigue_fea", "results")

# ------------------------------------------------------------------ palette
BG = "#0B1020"
PANEL = "#131A2C"
PANEL2 = "#1A2338"
GRID = "#26314B"
TXT = "#E8ECF4"
MUTED = "#8A96AD"
CYAN = "#4CC9F0"
AMBER = "#F7B32B"
PINK = "#F15BB5"
GREEN = "#7AE582"
RED = "#FF5964"
VIOLET = "#9B5DE5"
BLUE = "#4361EE"
WHITE_ = "#FFFFFF"
# regime colours
C_EL, C_SD, C_AP, C_RT = "#4CC9F0", "#7AE582", "#F7B32B", "#FF5964"

config.background_color = BG
config.frame_rate = 30

TEX = TexTemplate()
TEX.add_to_preamble(r"\usepackage{cmbright}\usepackage{amsmath}\usepackage{amssymb}")
FONT = "Lato"


def T(s, size=30, color=TXT, weight=NORMAL, **kw):
    return Text(s, font=FONT, font_size=size, color=color, weight=weight, **kw)


def M(*args, size=None, color=None, **kw):
    """MathTex helper. Positional args: tex strings, then optionally size (number)
    and colour (hex string starting with '#')."""
    strs = []
    for a in args:
        if isinstance(a, (int, float)):
            size = a
        elif isinstance(a, str) and a.startswith("#"):
            color = a
        else:
            strs.append(a)
    return MathTex(*strs, tex_template=TEX, font_size=size or 40, color=color or TXT, **kw)


def chapter_tag(num, title):
    a = T(f"{num:02d}", 22, CYAN, weight=BOLD)
    b = T(title.upper(), 20, MUTED, weight=BOLD)
    g = VGroup(a, b).arrange(RIGHT, buff=0.25)
    g.to_corner(UL, buff=0.45)
    line = Line(g.get_left() + DOWN * 0.28, g.get_right() + DOWN * 0.28, stroke_width=1.5, color=GRID)
    return VGroup(g, line)


def card(width, height, color=PANEL, stroke=GRID, radius=0.18, opacity=0.92):
    return RoundedRectangle(width=width, height=height, corner_radius=radius,
                            fill_color=color, fill_opacity=opacity, stroke_color=stroke, stroke_width=1.5)


def pill(text, color, size=22, fill_opacity=0.18):
    t = T(text, size, color, weight=BOLD)
    r = RoundedRectangle(width=t.width + 0.45, height=t.height + 0.28, corner_radius=0.2,
                         fill_color=color, fill_opacity=fill_opacity, stroke_color=color, stroke_width=1.6)
    t.move_to(r)
    return VGroup(r, t)


def log_tick_labels(axes, exps, axis="x", size=24, color=MUTED):
    g = VGroup()
    for e in exps:
        lab = M(rf"10^{{{e}}}", size, color)
        if axis == "x":
            lab.next_to(axes.c2p(e, axes.y_range[0]), DOWN, buff=0.18)
        else:
            lab.next_to(axes.c2p(axes.x_range[0], e), LEFT, buff=0.18)
        g.add(lab)
    return g


def timing():
    with open(os.path.join(AUDIO, "timing.json")) as fh:
        return json.load(fh)


class SyncScene(MovingCameraScene):
    """Scene synchronised to a narration track. Use self.cue('seg') to wait until a
    segment starts, self.dur('seg') for its duration, self.finish() at the end."""
    scene_id = None

    def setup(self):
        super().setup()
        self.camera.background_color = BG
        self.tm = timing()[self.scene_id]

    def start(self, seg):
        return self.tm["segments"][seg]["start"]

    def dur(self, seg):
        return self.tm["segments"][seg]["dur"]

    def end(self, seg):
        return self.start(seg) + self.dur(seg)

    @property
    def now(self):
        return self.renderer.time

    def wait_until(self, t):
        dt = t - self.now
        if dt > 1.0 / 30:
            self.wait(dt)

    def cue(self, seg, offset=0.0):
        self.wait_until(self.start(seg) + offset)

    def until(self, seg, frac=1.0, offset=0.0):
        """time left until a fraction of a segment (for run_time sizing)."""
        return max(0.2, self.start(seg) + frac * self.dur(seg) + offset - self.now)

    def finish(self, fade=True):
        tot = self.tm["total"]
        if fade:
            rem = tot - self.now
            if rem > 0.8:
                self.wait(rem - 0.7)
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        self.wait_until(tot)


def load_npz(name):
    return np.load(os.path.join(RESULTS, name), allow_pickle=False)


class FrameSeq(ImageMobject):
    """An image whose pixels are swapped from a list of PNG files, driven by a ValueTracker."""
    def __init__(self, files, tracker, height=None, loop=False, **kw):
        from PIL import Image
        self.files = files
        self.loop = loop
        self._cache = {}
        arr = np.array(Image.open(files[0]).convert("RGBA"))
        super().__init__(arr, **kw)
        if height is not None:
            self.height = height
        self.tracker = tracker
        self._cur = 0
        self.add_updater(lambda m: m._update())

    def _load(self, i):
        from PIL import Image
        if i not in self._cache:
            if len(self._cache) > 60:
                self._cache.pop(next(iter(self._cache)))
            self._cache[i] = np.array(Image.open(self.files[i]).convert("RGBA"))
        return self._cache[i]

    def _update(self):
        v = int(round(self.tracker.get_value()))
        i = v % len(self.files) if self.loop else int(np.clip(v, 0, len(self.files) - 1))
        if i != self._cur:
            self.pixel_array = self._load(i)
            self._cur = i


def frames(tag):
    d = os.path.join(FRAMES, tag)
    return sorted(os.path.join(d, f) for f in os.listdir(d) if f.endswith(".png"))


def img(path, height=None, width=None):
    m = ImageMobject(path)
    if height is not None:
        m.height = height
    if width is not None:
        m.width = width
    return m


def mm2pt(mob, x, y, xlim=(-42, 42), ylim=(-62, 62)):
    """map model coordinates (mm) to scene point for an image rendered with xlim/ylim."""
    sx = mob.width / (xlim[1] - xlim[0])
    sy = mob.height / (ylim[1] - ylim[0])
    c = mob.get_center()
    return c + np.array([(x - 0.5 * (xlim[0] + xlim[1])) * sx, (y - 0.5 * (ylim[0] + ylim[1])) * sy, 0.0])


def glow_line(points, color=RED, width=5):
    core = VMobject().set_points_as_corners(points).set_stroke(color, width)
    halo = core.copy().set_stroke(color, width * 4, opacity=0.25)
    return VGroup(halo, core)


def loop_curve(axes, xs, ys, color=AMBER, width=3):
    pts = [axes.c2p(x, y) for x, y in zip(xs, ys)]
    return VMobject().set_points_as_corners(pts).set_stroke(color, width)


class LogAxes(VGroup):
    """Axes in log10 coordinates with the axis lines at the lower-left corner.
    xr, yr: (min, max) in log10 units (y may also be linear if ylog=False)."""
    def __init__(self, xr, yr, x_length=9, y_length=5, xstep=1, ystep=1, color=GRID):
        self.xmin, self.xmax = xr
        self.ymin, self.ymax = yr
        self.ax = Axes(x_range=[0, xr[1] - xr[0], xstep], y_range=[0, yr[1] - yr[0], ystep],
                       x_length=x_length, y_length=y_length,
                       axis_config={"color": color, "stroke_width": 2, "include_ticks": True, "tick_size": 0.05},
                       tips=False)
        super().__init__(self.ax)

    def c2p(self, x, y):
        return self.ax.c2p(x - self.xmin, y - self.ymin)

    def plot(self, f, x_range, **kw):
        return self.ax.plot(lambda u: f(u + self.xmin) - self.ymin,
                            x_range=[x_range[0] - self.xmin, x_range[1] - self.xmin], **kw)

    def polyline(self, xs, ys, color=TXT, width=3):
        return VMobject().set_points_as_corners([self.c2p(x, y) for x, y in zip(xs, ys)]).set_stroke(color, width)

    def xlabels(self, exps, size=24, color=MUTED, fmt=None):
        g = VGroup()
        for e in exps:
            lab = M(fmt(e) if fmt else rf"10^{{{e}}}", size, color)
            lab.next_to(self.c2p(e, self.ymin), DOWN, buff=0.15)
            g.add(lab)
        return g

    def ylabels(self, exps, size=24, color=MUTED, fmt=None):
        g = VGroup()
        for e in exps:
            lab = M(fmt(e) if fmt else rf"10^{{{e}}}", size, color)
            lab.next_to(self.c2p(self.xmin, e), LEFT, buff=0.15)
            g.add(lab)
        return g

    def vband(self, x0, x1, color, opacity=0.1):
        r = Rectangle(width=self.c2p(x1, self.ymin)[0] - self.c2p(x0, self.ymin)[0],
                      height=self.c2p(self.xmin, self.ymax)[1] - self.c2p(self.xmin, self.ymin)[1],
                      fill_color=color, fill_opacity=opacity, stroke_width=0)
        r.move_to([(self.c2p(x0, 0)[0] + self.c2p(x1, 0)[0]) / 2,
                   (self.c2p(0, self.ymin)[1] + self.c2p(0, self.ymax)[1]) / 2, 0])
        return r
