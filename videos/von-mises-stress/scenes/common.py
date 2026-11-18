"""Shared style, narration timing and building blocks for every scene."""
import json
import os
from contextlib import contextmanager

import numpy as np
from manim import *  # noqa: F401,F403

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BUILD = os.path.join(ROOT, "build")

# ------------------------------------------------------------------ palette (consistent meaning)
BG = "#0B0F19"
INK = "#E8EDF5"        # text
DIM = "#8A96A8"        # secondary text
FAINT = "#2A3446"      # grid / guides
PANEL = "#121A2A"
C_X = "#FF6B6B"        # x / 1 / sigma_1
C_Y = "#6BCB77"        # y / 2 / sigma_2
C_Z = "#4D96FF"        # z / 3 / sigma_3
C_SHEAR = "#FFD93D"    # shear stress / deviatoric (shape)
C_DEV = C_SHEAR
C_HYD = "#B983FF"      # hydrostatic (volume)
C_VM = "#F15BB5"       # von Mises equivalent stress
C_YIELD = "#FF9F1C"    # yield strength sigma_Y
C_TRESCA = "#00F5D4"   # Tresca
C_STEEL = "#8D99AE"
C_GOOD = "#6BCB77"
C_BAD = "#FF5A5F"
FONT = "Inter"
COMP = [C_X, C_Y, C_Z]

config.background_color = BG

_DUR_PATH = os.path.join(BUILD, "audio", "durations.json")
DUR = json.load(open(_DUR_PATH)) if os.path.exists(_DUR_PATH) else {}

import sys  # noqa: E402
sys.path.insert(0, ROOT)
from narration import SCENES as _SCENES  # noqa: E402
TEXT = {k: v for _, segs in _SCENES for k, v in segs}


def cue(key, phrase):
    """Estimated time (s) from the start of beat `key` at which `phrase` is spoken."""
    txt = TEXT[key]
    i = txt.find(phrase)
    if i < 0:
        raise KeyError(f"{phrase!r} not in {key}")
    # speech time ~ proportional to letters; punctuation adds pauses
    w = lambda s: sum(1.0 for ch in s if ch.isalnum()) + 6.0 * sum(1 for ch in s if ch in ".:;") + \
        3.0 * sum(1 for ch in s if ch == ",")
    return DUR.get(key, 3.0) * w(txt[:i]) / max(1.0, w(txt))


def load_json(*parts):
    return json.load(open(os.path.join(BUILD, *parts)))


def T(s, size=30, color=INK, weight=NORMAL, **kw):
    """Body text in the house font."""
    return Text(s, font=FONT, font_size=size, color=color, weight=weight, **kw)


def M(*s, size=40, color=INK, **kw):
    return MathTex(*s, font_size=size, color=color, **kw)


# ------------------------------------------------------------------ narration sync
class Narrated:
    """Mixin: `with self.say("id") as d:` starts beat `id` (d = its duration in s).

    Animations inside the block should fit in d; on exit the scene waits until the beat
    (plus a short gap) has finished.  The start time of every beat is logged to
    build/timeline/<Scene>.json, from which the audio track and subtitles are built.
    """

    GAP = 0.25

    def setup(self):
        super().setup()
        self.timeline = []
        self._seg = (0.0, 0.0)

    def now(self):
        return self.renderer.time

    @contextmanager
    def say(self, key, gap=None):
        gap = self.GAP if gap is None else gap
        t0 = self.now()
        d = DUR.get(key, 3.0)
        self.timeline.append([key, round(t0, 4)])
        self._seg = (t0, d)
        yield d
        el = self.now() - t0
        if el < d + gap:
            self.wait(d + gap - el)

    def left(self, margin=0.0):
        t0, d = self._seg
        return max(0.1, t0 + d - self.now() - margin)

    def until(self, key, phrase, lead=0.15):
        """Wait (inside a `say` block) until shortly before `phrase` is spoken; returns nothing."""
        t0, _ = self._seg
        target = t0 + cue(key, phrase) - lead
        if target - self.now() > 1 / 30:
            self.wait(target - self.now())

    def till(self, key, phrase, lead=0.15, minimum=0.3):
        """Duration from now until `phrase` (useful as run_time)."""
        t0, _ = self._seg
        return max(minimum, t0 + cue(key, phrase) - lead - self.now())

    def tear_down(self):
        super().tear_down()
        os.makedirs(os.path.join(BUILD, "timeline"), exist_ok=True)
        json.dump({"scene": type(self).__name__, "duration": round(self.now(), 4), "beats": self.timeline},
                  open(os.path.join(BUILD, "timeline", f"{type(self).__name__}.json"), "w"), indent=1)


class NScene(Narrated, Scene):
    pass


class N3DScene(Narrated, ThreeDScene):
    pass


# ------------------------------------------------------------------ titles
def section_card(scene, num, title, dur=2.3):
    n = T(f"{num:02d}", size=34, color=C_YIELD, weight=BOLD)
    t = T(title, size=50, weight=SEMIBOLD)
    grp = VGroup(n, t).arrange(DOWN, buff=0.3)
    line = Line(LEFT * 3.2, RIGHT * 3.2, stroke_width=2, color=C_YIELD).next_to(t, DOWN, buff=0.35)
    line.set_opacity(0.8)
    scene.play(FadeIn(n, shift=0.2 * DOWN), FadeIn(t, shift=0.2 * UP), Create(line), run_time=0.9)
    scene.wait(max(0.1, dur - 1.6))
    scene.play(FadeOut(VGroup(grp, line)), run_time=0.7)


def caption_box(mob, color=C_VM, buff=0.18, corner=0.12, width=2.5):
    return SurroundingRectangle(mob, color=color, buff=buff, corner_radius=corner, stroke_width=width)


def tag(text, color=DIM, size=22):
    return T(text, size=size, color=color)


# ------------------------------------------------------------------ stress cube (3D)
def stress_cube(sig, size=2.0, scale=0.9, max_len=1.4, shear=True, cube_opacity=0.16, thickness=0.034,
                labels=False, label_size=34, min_len=0.0):
    """Cube with traction arrows for a 3x3 stress tensor `sig` (dimensionless units).

    Normal components: arrows along the face normal (outward = tension).
    Shear components: tangential arrows on the faces, colored C_SHEAR.
    Returns VGroup(cube, normals, shears, labels) with attributes for later access.
    """
    sig = np.asarray(sig, dtype=float)
    h = size / 2
    cube = Cube(side_length=size, fill_color=C_STEEL, fill_opacity=cube_opacity, stroke_color=INK,
                stroke_width=1.6, stroke_opacity=0.9)
    normals, shears, labs = VGroup(), VGroup(), VGroup()
    e = np.eye(3)
    names = ["x", "y", "z"]
    for i in range(3):
        s = sig[i, i]
        if abs(s) < 1e-9:
            continue
        ln = float(np.clip(abs(s) * scale, min_len, max_len))
        for sgn in (1, -1):
            c = sgn * h * e[i]
            outer = c + sgn * e[i] * ln
            start, end = (c, outer) if s > 0 else (outer, c)     # tension points away from the face
            a = Arrow3D(start, end, color=COMP[i], thickness=thickness, height=0.22, base_radius=0.07,
                        resolution=8)
            normals.add(a)
        if labels:
            lab = MathTex(rf"\sigma_{names[i]}", color=COMP[i], font_size=label_size)
            lab.move_to(h * e[i] + e[i] * (ln + 0.35))
            labs.add(lab)
    if shear:
        for i in range(3):
            for j in range(3):
                if i == j or abs(sig[i, j]) < 1e-9:
                    continue
                t = sig[i, j]
                ln = float(np.clip(abs(t) * scale, min_len, max_len * 0.8))
                k3 = 3 - i - j
                for sgn in (1, -1):
                    c = sgn * h * e[i] + sgn * 0.01 * e[i] + 0.42 * h * e[k3] * (1 if j > k3 else -1)
                    d = sgn * np.sign(t) * e[j]
                    start, end = c - d * ln / 2, c + d * ln / 2
                    a = Arrow3D(start, end, color=C_SHEAR, thickness=thickness * 0.9, height=0.2,
                                base_radius=0.06, resolution=8)
                    shears.add(a)
    g = VGroup(cube, normals, shears, labs)
    g.cube, g.normals, g.shears, g.labs = cube, normals, shears, labs
    return g


def gauge(value, limit, width=5.0, label=r"\sigma_{vm}", color=C_VM, ymax=1.3, height=0.32):
    """Horizontal bar: value vs. yield limit (fraction shown up to ymax * limit)."""
    frame = RoundedRectangle(width=width, height=height, corner_radius=height / 2, stroke_color=DIM,
                             stroke_width=1.5, fill_opacity=0)
    frac = np.clip(value / (limit * ymax), 0, 1)
    bar = RoundedRectangle(width=max(frac * width, 0.02), height=height * 0.8, corner_radius=height * 0.4,
                           fill_color=color, fill_opacity=0.9, stroke_width=0)
    bar.align_to(frame, LEFT).shift(RIGHT * 0.02)
    yx = frame.get_left()[0] + width / ymax
    yl = DashedLine([yx, -height * 0.9, 0], [yx, height * 0.9, 0], color=C_YIELD, stroke_width=2.5)
    ylab = MathTex(r"\sigma_Y", color=C_YIELD, font_size=28).next_to(yl, UP, buff=0.05)
    vlab = MathTex(label, color=color, font_size=30).next_to(frame, LEFT, buff=0.2)
    return VGroup(frame, bar, yl, ylab, vlab)


def matrix_tex(entries, colors=None, size=40, h_buff=1.0, v_buff=0.6):
    m = Matrix(entries, element_to_mobject=lambda s: MathTex(s, font_size=size), h_buff=h_buff,
               v_buff=v_buff, bracket_h_buff=0.15)
    m.set_color(INK)
    if colors is not None:
        for (i, j), c in colors.items():
            m.get_rows()[i][j].set_color(c)
    return m


def vm_principal(s1, s2, s3):
    return float(np.sqrt(0.5 * ((s1 - s2) ** 2 + (s2 - s3) ** 2 + (s3 - s1) ** 2)))


def turbo_colors(n=12):
    import matplotlib
    cm = matplotlib.colormaps["turbo"]
    return [matplotlib.colors.to_hex(cm((i + 0.5) / n)) for i in range(n)]


def colorbar(vmin, vmax, n=12, height=4.0, width=0.32, title=r"\sigma_{vm}\ \mathrm{[MPa]}", ticks=None,
             size=22):
    cols = turbo_colors(n)
    cells = VGroup(*[Rectangle(width=width, height=height / n, fill_color=c, fill_opacity=1, stroke_width=0)
                     for c in cols]).arrange(UP, buff=0)
    frame = SurroundingRectangle(cells, buff=0, stroke_color=DIM, stroke_width=1)
    ticks = ticks or np.linspace(vmin, vmax, 5)
    labs = VGroup()
    for v in ticks:
        y = cells.get_bottom()[1] + (v - vmin) / (vmax - vmin) * height
        lab = T(f"{v:.0f}", size=size, color=INK).move_to([cells.get_right()[0] + 0.45, y, 0])
        labs.add(lab)
    ttl = MathTex(title, font_size=size + 6, color=INK).next_to(cells, UP, buff=0.25)
    return VGroup(cells, frame, labs, ttl)


class ZoomImage(ImageMobject):
    """Full-frame image that zooms about a focus point by re-cropping the source (fast in Cairo)."""

    def __init__(self, path, focus=(0.5, 0.5), **kw):
        from PIL import Image
        self.src = Image.open(path).convert("RGBA")
        self.out = (config.pixel_width, config.pixel_height)
        super().__init__(np.array(self.src.resize(self.out, Image.LANCZOS)), **kw)
        self.height = config.frame_height
        self.focus = focus                      # (x from left, y from top), normalized
        self.zoom = ValueTracker(1.0)
        self._last = 1.0
        self.add_updater(lambda m: m._upd())

    def _upd(self):
        z = self.zoom.get_value()
        if abs(z - self._last) < 1e-6:
            return
        self._last = z
        W_, H_ = self.src.size
        fx, fy = self.focus[0] * W_, self.focus[1] * H_
        cx = fx + (W_ / 2 - fx) / z
        cy = fy + (H_ / 2 - fy) / z
        w, h = W_ / z, H_ / z
        box = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
        from PIL import Image
        self.pixel_array = np.array(self.src.crop(box).resize(self.out, Image.BILINEAR))


def track(mob, seq, pts, offset=ORIGIN):
    """Keep `mob` on a projected 3D anchor of a FrameSequence (pts = per-frame [x, y])."""
    def upd(m):
        i = min(seq._idx, len(pts) - 1)
        m.move_to(np.array([pts[i][0], pts[i][1], 0.0]) + offset)
    mob.add_updater(upd)
    upd(mob)
    return mob


class FrameSequence(ImageMobject):
    """Full-frame image that plays a PNG sequence (30 fps) starting when `play()` is called."""

    def __init__(self, folder, fps=30, **kw):
        self.files = sorted(f for f in os.listdir(folder) if f.endswith(".png"))
        self.folder = folder
        self.fps = fps
        super().__init__(os.path.join(folder, self.files[0]), **kw)
        self.height = config.frame_height
        self._t = 0.0
        self._idx = 0

    def start(self):
        self._t = 0.0

        def upd(m, dt):
            m._t += dt
            i = min(int(m._t * m.fps), len(m.files) - 1)
            if i != m._idx:
                m._idx = i
                from PIL import Image
                m.pixel_array = np.array(Image.open(os.path.join(m.folder, m.files[i])).convert("RGBA"))
        self.add_updater(upd)
        return self

    def n_seconds(self):
        return len(self.files) / self.fps
