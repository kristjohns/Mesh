import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "fatigue_fea"))
from common import *

E = 210000.0
SF, B = 952.0, -0.089
SU, SY = 510.0, 355.0


def rainflow_idx(x):
    """ASTM E1049 rainflow on turning points; returns list of (i, j, range, count)."""
    x = np.asarray(x, float)
    dx = np.diff(x)
    tp = [0] + [k + 1 for k in range(len(dx) - 1) if dx[k] * dx[k + 1] < 0] + [len(x) - 1]
    stack, out = [], []
    for p in tp:
        stack.append(p)
        while len(stack) >= 3:
            X = abs(x[stack[-1]] - x[stack[-2]])
            Y = abs(x[stack[-2]] - x[stack[-3]])
            if X < Y:
                break
            if len(stack) == 3:
                out.append((stack[0], stack[1], Y, 0.5))
                stack.pop(0)
            else:
                out.append((stack[-3], stack[-2], Y, 1.0))
                last = stack.pop()
                stack.pop(); stack.pop()
                stack.append(last)
    for k in range(len(stack) - 1):
        out.append((stack[k], stack[k + 1], abs(x[stack[k + 1]] - x[stack[k]]), 0.5))
    return out


class S04HCF(SyncScene):
    scene_id = "s04_hcf"

    def construct(self):
        self.tag = chapter_tag(3, "High-cycle fatigue")
        self.add(self.tag)
        self.part_title()
        self.part_sn()
        self.part_haigh()
        self.part_notch()
        self.part_weld()
        self.part_rainflow()
        self.part_multiaxial()
        self.finish()

    def clear(self, rt=0.6):
        objs = [m for m in self.mobjects if m is not self.tag]
        if objs:
            self.play(*[FadeOut(m) for m in objs], run_time=rt)

    # ------------------------------------------------------------------ a
    def part_title(self):
        t = T("HIGH-CYCLE FATIGUE", 72, CYAN, weight=BOLD)
        s = T("the stress–life world", 32, MUTED).next_to(t, DOWN, buff=0.3)
        self.play(FadeIn(t, scale=1.1), FadeIn(s), run_time=1.0)
        self.wait_until(self.end("a") - 0.2)
        self.play(FadeOut(VGroup(t, s)), run_time=0.4)

    # ------------------------------------------------------------------ b, c
    def part_sn(self):
        self.cue("b")
        # Woehler axle icon
        wheel1 = Circle(0.55, color=TXT, stroke_width=3).move_to(LEFT * 5.3 + UP * 2.2)
        wheel2 = wheel1.copy().move_to(LEFT * 3.1 + UP * 2.2)
        axle = Line(wheel1.get_center(), wheel2.get_center(), color=AMBER, stroke_width=8)
        spokes = VGroup(*[Line(wheel1.get_center(), wheel1.get_center() + 0.5 * np.array([np.cos(a), np.sin(a), 0]),
                               color=MUTED, stroke_width=2) for a in np.linspace(0, 2 * PI, 6, endpoint=False)])
        spokes2 = spokes.copy().move_to(wheel2.get_center())
        cap = T("Wöhler · railway axles · 1860s", 22, MUTED).next_to(VGroup(wheel1, wheel2), DOWN, buff=0.2)
        icon = VGroup(axle, wheel1, wheel2, spokes, spokes2, cap)
        self.play(FadeIn(icon), run_time=0.8)
        self.play(Rotate(spokes, 2 * PI, about_point=wheel1.get_center()),
                  Rotate(spokes2, 2 * PI, about_point=wheel2.get_center()), run_time=2.0)
        ax = LogAxes((3, 9), (np.log10(80), np.log10(700)), x_length=8.0, y_length=5.0).move_to(RIGHT * 2.4 + DOWN * 0.8)
        xt = ax.xlabels(range(3, 10), 24)
        ys = [100, 200, 300, 500]
        yt = VGroup(*[T(str(v), 22, MUTED).next_to(ax.c2p(3, np.log10(v)), LEFT, buff=0.15) for v in ys])
        xl = T("cycles to failure N", 24, MUTED).next_to(xt, DOWN, buff=0.15)
        yl = M(r"\sigma_a\;[\mathrm{MPa}]", 30, MUTED).next_to(ax.c2p(3, np.log10(700)), UP, buff=0.15)
        self.play(FadeOut(icon), Create(ax), FadeIn(xt), FadeIn(yt), FadeIn(xl), FadeIn(yl), run_time=1.2)
        sn = lambda lN: np.log10(SF) + B * (np.log10(2) + lN)
        rng = np.random.default_rng(5)
        dots = VGroup()
        for lev in [480, 430, 380, 340, 300, 275]:
            lN0 = (np.log10(lev) - np.log10(SF)) / B - np.log10(2)
            for k in range(4):
                lN = lN0 + rng.normal(0, 0.22)
                if lN < 6.4:
                    dots.add(Dot(ax.c2p(lN, np.log10(lev)), radius=0.06, color=TXT))
        runouts = VGroup(*[Arrow(ax.c2p(7.0, np.log10(v)), ax.c2p(7.45, np.log10(v)), buff=0, color=MUTED,
                                 stroke_width=2.5, max_tip_length_to_length_ratio=0.4) for v in [255, 262, 248]])
        self.play(LaggedStart(*[FadeIn(d, scale=0.5) for d in dots], lag_ratio=0.05), run_time=2.0)
        line = ax.plot(sn, x_range=[3, np.log10(2e6)], color=CYAN, stroke_width=5)
        eq = M(r"\sigma_a=\sigma_f'\,(2N)^{\,b}", 44, CYAN).move_to(LEFT * 4.6 + UP * 0.6)
        eqn = T("Basquin (1910)", 22, MUTED).next_to(eq, DOWN, buff=0.15)
        self.wait_until(self.start("b") + self.dur("b") * 0.62)
        self.play(Create(line), Write(eq), FadeIn(eqn), run_time=1.6)
        bn = VGroup(M(r"\sigma_f'=952\,\mathrm{MPa}", 28, TXT), M(r"b=-0.089", 28, TXT)).arrange(DOWN, buff=0.12).next_to(eqn, DOWN, buff=0.3)
        self.play(FadeIn(bn), run_time=0.8)
        # c: knee + limit + aluminium + Marin
        self.cue("c")
        lim = sn(np.log10(2e6))
        flat = ax.plot(lambda x: lim, x_range=[np.log10(2e6), 9], color=CYAN, stroke_width=5)
        knee = Dot(ax.c2p(np.log10(2e6), lim), radius=0.09, color=PINK)
        self.play(Create(flat), FadeIn(knee, scale=2), FadeIn(runouts), run_time=1.2)
        tl = T("fatigue limit ≈ 0.5 Su\n(smooth, polished)", 20, CYAN, weight=BOLD).next_to(ax.c2p(7.9, lim), UP, buff=0.3)
        self.play(FadeIn(tl), run_time=0.6)
        al = ax.plot(lambda x: np.log10(330) - 0.11 * (x - 3), x_range=[3, 9], color=VIOLET, stroke_width=3)
        al.set_stroke(opacity=0.9)
        alt = T("aluminium: no clear limit", 22, VIOLET, weight=BOLD).next_to(ax.c2p(7.6, np.log10(330) - 0.11 * 4.6), DOWN, buff=0.1)
        self.wait_until(self.start("c") + self.dur("c") * 0.33)
        self.play(Create(al), FadeIn(alt), run_time=1.2)
        self.wait_until(self.start("c") + self.dur("c") * 0.5)
        marin = M(r"S_e=", r"k_a", r"k_b", r"k_c", r"k_d", r"k_e", r"\,S_e'", size=44).move_to(LEFT * 4.6 + UP * 0.9)
        cols = [TXT, AMBER, GREEN, PINK, RED, VIOLET, CYAN]
        for part, c in zip(marin, cols):
            part.set_color(c)
        labs = ["surface finish", "size", "load type", "temperature", "reliability"]
        lg = VGroup(*[VGroup(M(f"k_{ch}", 28, c), T(l, 22, c)).arrange(RIGHT, buff=0.2)
                      for ch, l, c in zip("abcde", labs, cols[1:6])]).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        lg.next_to(marin, DOWN, buff=0.35)
        self.play(FadeOut(VGroup(eq, eqn, bn)), Write(marin), FadeIn(lg), run_time=1.4)
        lim2 = np.log10(10 ** lim * 0.62)
        flat2 = ax.plot(lambda x: lim2, x_range=[np.log10(2e6), 9], color=AMBER, stroke_width=4)
        down = Arrow(ax.c2p(8.2, lim), ax.c2p(8.2, lim2), buff=0.05, color=AMBER, stroke_width=3)
        t2 = T("corrected limit", 20, AMBER).next_to(ax.c2p(8.2, lim2), DOWN, buff=0.12)
        self.play(TransformFromCopy(flat, flat2), GrowArrow(down), FadeIn(t2), run_time=1.4)
        self.wait_until(self.end("c") - 0.3)

    # ------------------------------------------------------------------ d
    def part_haigh(self):
        self.cue("d")
        self.clear()
        Se = 262.0
        ax = Axes(x_range=[-150, 560, 100], y_range=[0, 320, 100], x_length=8.4, y_length=5.0,
                  axis_config={"color": GRID, "stroke_width": 2, "include_ticks": False}, tips=False).move_to(LEFT * 1.6 + DOWN * 0.5)
        xl = M(r"\text{mean stress }\sigma_m", 28, MUTED).next_to(ax.c2p(220, 0), DOWN, buff=0.6)
        yl = M(r"\text{amplitude }\sigma_a", 28, MUTED).next_to(ax.c2p(0, 320), UP, buff=0.12)
        ticks = VGroup(
            M(r"S_e", 28, CYAN).next_to(ax.c2p(0, Se), LEFT, buff=0.12),
            M(r"S_y", 28, MUTED).next_to(ax.c2p(SY, 0), DOWN, buff=0.15),
            M(r"S_u", 28, MUTED).next_to(ax.c2p(SU, 0), DOWN, buff=0.15))
        title = T("Haigh diagram", 30, TXT, weight=BOLD).to_edge(UP, buff=0.9).shift(LEFT * 1.6)
        self.play(Create(ax), FadeIn(xl), FadeIn(yl), FadeIn(ticks), FadeIn(title), run_time=1.0)
        good = ax.plot(lambda m: Se * (1 - m / SU), x_range=[0, SU], color=CYAN, stroke_width=4)
        gerb = ax.plot(lambda m: Se * (1 - (m / SU) ** 2), x_range=[0, SU], color=GREEN, stroke_width=4)
        sod = ax.plot(lambda m: Se * (1 - m / SY), x_range=[0, SY], color=RED, stroke_width=4)
        swt = ax.plot(lambda m: 0.5 * (-m + np.sqrt(m * m + 4 * Se * Se)), x_range=[0, 540], color=AMBER, stroke_width=4)
        comp = DashedLine(ax.c2p(-150, Se), ax.c2p(0, Se), color=CYAN, stroke_width=3)
        yld = DashedLine(ax.c2p(0, SY), ax.c2p(SY, 0), color=MUTED, stroke_width=2)
        legend = VGroup()
        for name, col in [("Goodman: σa/Se + σm/Su = 1", CYAN), ("Gerber: parabola to Su", GREEN),
                          ("Soderberg: line to Sy (conservative)", RED), ("Smith–Watson–Topper: √(σmax σa) = Se", AMBER)]:
            legend.add(VGroup(Line(ORIGIN, RIGHT * 0.5, color=col, stroke_width=5), T(name, 22, TXT)).arrange(RIGHT, buff=0.2))
        legend.arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to(RIGHT * 4.3 + UP * 0.8)
        # tension / compression hints
        tens = T("tension opens cracks", 20, RED).next_to(ax.c2p(250, 300), UP, buff=0.0)
        compt = T("compression\nhelps", 20, CYAN).next_to(ax.c2p(-75, Se), DOWN, buff=0.15)
        self.play(FadeIn(tens), FadeIn(compt), Create(comp), run_time=1.0)
        seq = [(good, 0), (gerb, 1), (sod, 2)]
        t0 = self.start("d") + 6.0
        for k, (curve, li) in enumerate(seq):
            self.wait_until(t0 + k * 4.2)
            self.play(Create(curve), FadeIn(legend[li], shift=LEFT * 0.2), run_time=1.2)
        self.play(Create(yld), run_time=0.6)
        self.wait_until(self.start("d") + self.dur("d") * 0.78)
        self.play(Create(swt), FadeIn(legend[3], shift=LEFT * 0.2), run_time=1.2)
        # an operating point
        pt = Dot(ax.c2p(150, 160), radius=0.09, color=WHITE_)
        self.play(FadeIn(pt, scale=2), run_time=0.5)
        self.play(pt.animate.move_to(ax.c2p(150, Se * (1 - 150 / SU))), run_time=0.8)
        self.wait_until(self.end("d") - 0.2)

    # ------------------------------------------------------------------ e, f
    def part_notch(self):
        self.cue("e")
        self.clear()
        d = load_npz("plate_hcf.npz")
        im = img(frames("kt_map")[0], height=5.3).move_to(LEFT * 4.3 + DOWN * 0.65)
        cb = img(os.path.join(FRAMES, "cb_kt.png"), height=4.4).next_to(im, RIGHT, buff=0.05)
        cbt = M(r"\sigma_{yy}/S", 26, MUTED).next_to(cb, UP, buff=0.1)
        arrows = VGroup(*[Arrow(im.get_top() + [x, 0.05, 0], im.get_top() + [x, 0.45, 0], buff=0, color=AMBER,
                                stroke_width=3, max_tip_length_to_length_ratio=0.35) for x in np.linspace(-1.5, 1.5, 4)])
        arrows2 = arrows.copy().rotate(PI, about_point=im.get_center())
        self.play(FadeIn(im), FadeIn(cb), FadeIn(cbt), FadeIn(arrows), FadeIn(arrows2), run_time=1.2)
        St = M("S", 30, AMBER).next_to(arrows, UP, buff=0.05)
        self.play(FadeIn(St), run_time=0.3)
        # stress along ligament
        nodes = d["nodes"]
        lig = np.nonzero(np.abs(nodes[:, 1]) < 1e-9)[0]
        lig = lig[np.argsort(nodes[lig, 0])]
        xs = nodes[lig, 0]
        sy = d["F_syy"][9][lig] / 70.0
        ax = Axes(x_range=[10, 40, 10], y_range=[0, 3.5, 1], x_length=6.2, y_length=4.2,
                  axis_config={"color": GRID, "stroke_width": 2, "include_ticks": True, "tick_size": 0.05}, tips=False
                  ).move_to(RIGHT * 3.6 + DOWN * 0.2)
        xt = VGroup(*[T(str(v), 20, MUTED).next_to(ax.c2p(v, 0), DOWN, buff=0.12) for v in [10, 20, 30, 40]])
        yt = VGroup(*[T(str(v), 20, MUTED).next_to(ax.c2p(10, v), LEFT, buff=0.12) for v in [1, 2, 3]])
        xl = T("x along the ligament [mm]", 22, MUTED).next_to(xt, DOWN, buff=0.12)
        yl = M(r"\sigma_{yy}/S", 28, MUTED).next_to(ax.c2p(10, 3.5), UP, buff=0.12)
        fe = VMobject().set_points_smoothly([ax.c2p(x, y) for x, y in zip(xs, sy)]).set_stroke(AMBER, 4)
        a = 10.0
        kir = ax.plot(lambda x: 1 + 0.5 * (a / x) ** 2 + 1.5 * (a / x) ** 4, x_range=[10, 40], color=MUTED, stroke_width=2.5)
        kir = DashedVMobject(kir, num_dashes=40)
        self.play(Create(ax), FadeIn(xt), FadeIn(yt), FadeIn(xl), FadeIn(yl), run_time=0.8)
        self.play(Create(fe), run_time=1.6)
        kt = VGroup(M(r"K_t=\frac{\sigma_{\max}}{S}=3.25", 34, AMBER),
                    M(r"K_{t,\mathrm{net}}=2.44\;\;(\text{Peterson: }2.43)", 26, TXT)).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        kt.next_to(ax.c2p(17, 3.3), RIGHT, buff=0.1)
        self.wait_until(self.start("e") + self.dur("e") * 0.45)
        self.play(Write(kt[0]), Flash(ax.c2p(10, sy[0]), color=AMBER), run_time=1.2)
        self.wait_until(self.start("e") + self.dur("e") * 0.7)
        self.play(FadeIn(kt[1]), Create(kir), run_time=1.0)
        kl = T("infinite plate (Kirsch): 3.0", 18, MUTED).next_to(ax.c2p(30, 1.1), UP, buff=0.1)
        self.play(FadeIn(kl), run_time=0.5)
        # f: Kf and notch sensitivity
        self.cue("f")
        self.play(FadeOut(VGroup(ax, xt, yt, xl, yl, fe, kir, kl, kt)), run_time=0.6)
        ax2 = Axes(x_range=[0, 10, 2], y_range=[0, 1.0, 0.2], x_length=6.0, y_length=3.6,
                   axis_config={"color": GRID, "stroke_width": 2, "include_ticks": True, "tick_size": 0.05}, tips=False
                   ).move_to(RIGHT * 3.5 + DOWN * 1.0)
        xt2 = VGroup(*[T(str(v), 20, MUTED).next_to(ax2.c2p(v, 0), DOWN, buff=0.12) for v in [0, 2, 4, 6, 8, 10]])
        yt2 = VGroup(*[T(f"{v:.1f}", 20, MUTED).next_to(ax2.c2p(0, v), LEFT, buff=0.12) for v in [0.5, 1.0]])
        xl2 = T("notch radius r [mm]", 22, MUTED).next_to(xt2, DOWN, buff=0.1)
        yl2 = T("notch sensitivity q", 22, MUTED).next_to(ax2.c2p(0, 1.0), UP, buff=0.12)
        def q_of(su):
            aP = 0.0254 * (2070.0 / su) ** 1.8
            return lambda r: 1.0 / (1.0 + aP / max(r, 1e-6))
        c1 = ax2.plot(q_of(510), x_range=[0.02, 10], color=CYAN, stroke_width=4)
        c2 = ax2.plot(q_of(1400), x_range=[0.005, 10], color=GREEN, stroke_width=3)
        l1 = T("S355, Su ≈ 510 MPa", 18, CYAN).next_to(ax2.c2p(4.5, 0.9), DOWN, buff=0.15)
        l2 = T("high-strength, Su ≈ 1400", 18, GREEN).next_to(ax2.c2p(7.5, 0.99), UP, buff=0.06)
        eqs = VGroup(M(r"K_f = 1 + q\,(K_t-1)", 36, TXT),
                     M(r"q = \frac{1}{1+a/r}\quad\text{(Peterson)}", 30, MUTED)).arrange(DOWN, buff=0.2).move_to(RIGHT * 3.5 + UP * 2.0)
        self.play(Write(eqs[0]), run_time=1.0)
        self.play(FadeIn(eqs[1]), Create(ax2), FadeIn(xt2), FadeIn(yt2), FadeIn(xl2), FadeIn(yl2), run_time=1.0)
        self.play(Create(c1), Create(c2), FadeIn(l1), FadeIn(l2), run_time=1.6)
        self.wait_until(self.start("f") + self.dur("f") * 0.66)
        q10 = q_of(510)(10.0)
        pt = Dot(ax2.c2p(10, q10), radius=0.09, color=AMBER)
        res = M(r"r=10\,\mathrm{mm}:\; q\approx 0.97 \;\Rightarrow\; K_f\approx K_t", 28, AMBER).next_to(ax2, UP, buff=0.1).shift(DOWN * 0.05)
        self.play(FadeIn(pt, scale=2), Write(res), run_time=1.2)
        self.wait_until(self.end("f") - 0.2)

    # ------------------------------------------------------------------ g - k
    def part_weld(self):
        self.cue("g")
        self.clear()
        w = load_npz("weld_tjoint.npz")
        meta = json.loads(str(w["meta"]))
        bm = meta["bending"]
        full = img(os.path.join(FRAMES, "weld_bending", "full.png"), width=12.4).move_to(DOWN * 0.3)
        XL, YL = (-95, 95), (-12, 68)
        P = lambda x, y: mm2pt(full, x, y, XL, YL)
        self.play(FadeIn(full), run_time=1.0)
        up = Arrow(P(0, 61), P(0, 75), buff=0, color=AMBER, stroke_width=5)
        upt = M("P", 30, AMBER).next_to(up, RIGHT, buff=0.1)
        toes = VGroup(Circle(0.28, color=WHITE_, stroke_width=3).move_to(P(13.2, 20.3)),
                      Circle(0.28, color=WHITE_, stroke_width=3).move_to(P(-13.2, 20.3)))
        tt = T("weld toe: sharp notch", 24, TXT, weight=BOLD).next_to(P(30, 34), UP, buff=0.0)
        ar = Arrow(tt.get_bottom(), toes[0].get_top(), buff=0.08, color=TXT, stroke_width=3)
        rs = T("+ residual stresses ≈ yield  →  weld S–N curves ignore applied mean stress", 22, AMBER).to_edge(DOWN, buff=0.45)
        self.play(GrowArrow(up), FadeIn(upt), run_time=0.6)
        self.play(Create(toes), FadeIn(tt), GrowArrow(ar), run_time=1.0)
        self.wait_until(self.start("g") + self.dur("g") * 0.45)
        self.play(FadeIn(rs, shift=UP * 0.1), run_time=0.8)
        self.wait_until(self.end("g") - 0.2)
        # ---- h: nominal stress method
        self.cue("h")
        self.play(FadeOut(VGroup(tt, ar, rs, up, upt, toes)), FadeOut(full), run_time=0.6)
        head = T("1 · NOMINAL STRESS METHOD", 30, CYAN, weight=BOLD).to_edge(UP, buff=0.9)
        ax = LogAxes((4, 8), (np.log10(20), np.log10(400)), x_length=6.4, y_length=4.2).move_to(LEFT * 2.6 + DOWN * 0.5)
        xt = ax.xlabels(range(4, 9), 22)
        yt = VGroup(*[T(str(v), 20, MUTED).next_to(ax.c2p(4, np.log10(v)), LEFT, buff=0.12) for v in [50, 100, 200]])
        fams = VGroup()
        for fat in [160, 125, 100, 80, 63, 50, 36]:
            f = lambda lN, fat=fat: np.log10(fat) - (lN - np.log10(2e6)) / 3.0
            c = ax.plot(f, x_range=[4, 7], color=AMBER if fat == 80 else MUTED, stroke_width=4 if fat == 80 else 1.8)
            fams.add(c)
        lab80 = T("FAT 80", 22, AMBER, weight=BOLD).next_to(ax.c2p(7, np.log10(80) - (7 - 6.301) / 3), RIGHT, buff=0.1)
        cat = VGroup(T("detail category catalogue", 24, TXT, weight=BOLD),
                     T("FAT = stress range at 2·10⁶ cycles", 20, MUTED),
                     M(r"\Delta\sigma_{\mathrm{nom}} = \frac{M}{W}\;\;(\text{beam theory})", 30, TXT),
                     T("only if joint + load match a catalogued detail", 20, RED)).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        cat.move_to(RIGHT * 3.8 + DOWN * 0.2)
        self.play(FadeIn(head), Create(ax), FadeIn(xt), FadeIn(yt), run_time=0.8)
        self.play(LaggedStart(*[Create(c) for c in fams], lag_ratio=0.1), FadeIn(lab80), run_time=1.6)
        self.play(LaggedStart(*[FadeIn(c, shift=LEFT * 0.2) for c in cat], lag_ratio=0.3), run_time=self.until("h", 0.95))
        # ---- i: hot spot
        self.cue("i")
        self.play(FadeOut(VGroup(head, ax, xt, yt, fams, lab80, cat)), run_time=0.6)
        head = T("2 · STRUCTURAL HOT-SPOT STRESS", 30, GREEN, weight=BOLD).to_edge(UP, buff=0.9)
        mid = img(os.path.join(FRAMES, "weld_bending", "mid.png"), width=6.6).move_to(LEFT * 3.4 + UP * 0.45)
        XLm, YLm = (-2, 60), (-4, 34)
        Pm = lambda x, y: mm2pt(mid, x, y, XLm, YLm)
        self.play(FadeIn(head), FadeIn(mid), run_time=0.8)
        t_ = meta["t"]
        x_toe = meta["x_toe"]
        sd = w["bending_surf_d"]
        ss = w["bending_surf_sxx"]
        keep = sd <= 52
        ax = Axes(x_range=[0, 52, 10], y_range=[0, 300, 100], x_length=6.4, y_length=3.8,
                  axis_config={"color": GRID, "stroke_width": 2, "include_ticks": True, "tick_size": 0.05}, tips=False
                  ).move_to(RIGHT * 3.6 + DOWN * 0.35)
        xt = VGroup(*[T(str(v), 18, MUTED).next_to(ax.c2p(v, 0), DOWN, buff=0.1) for v in [0, 10, 20, 30, 40, 50]])
        yt = VGroup(*[T(str(v), 18, MUTED).next_to(ax.c2p(0, v), LEFT, buff=0.1) for v in [100, 200, 300]])
        xl = T("distance from weld toe [mm]", 20, MUTED).next_to(xt, DOWN, buff=0.1)
        yl = M(r"\sigma_{xx}\text{ at surface [MPa]}", 24, MUTED).next_to(ax.c2p(0, 300), UP, buff=0.1)
        curve = VMobject().set_points_as_corners([ax.c2p(x, min(y, 300)) for x, y in zip(sd[keep], ss[keep])]).set_stroke(TXT, 4)
        surf_line = Line(Pm(x_toe, 20.0), Pm(60, 20.0), color=WHITE_, stroke_width=3)
        self.play(Create(ax), FadeIn(xt), FadeIn(yt), FadeIn(xl), FadeIn(yl), Create(surf_line), run_time=1.0)
        self.play(Create(curve), run_time=2.0)
        # decomposition: linear structural part + notch peak
        lin = ax.plot(lambda x: bm["hs_dnv"] + (bm["s15"] - bm["s05"]) / t_ * x, x_range=[0, 52], color=GREEN, stroke_width=3)
        lin = DashedVMobject(lin, num_dashes=45)
        peak_t = T("nonlinear notch peak", 18, RED).next_to(ax.c2p(2, 240), RIGHT, buff=0.1)
        lin_t = T("linear structural part", 18, GREEN).next_to(ax.c2p(30, 85), DOWN, buff=0.1)
        self.wait_until(self.start("i") + 9.5)
        self.play(Create(lin), FadeIn(peak_t), FadeIn(lin_t), run_time=1.4)
        # read-out points
        self.wait_until(self.start("i") + 15.0)
        p05 = Dot(ax.c2p(0.5 * t_, bm["s05"]), radius=0.09, color=AMBER)
        p15 = Dot(ax.c2p(1.5 * t_, bm["s15"]), radius=0.09, color=AMBER)
        m05 = VGroup(Dot(Pm(x_toe + 0.5 * t_, 20), radius=0.07, color=AMBER), Dot(Pm(x_toe + 1.5 * t_, 20), radius=0.07, color=AMBER))
        l05 = T("0.5t", 18, AMBER).next_to(p05, UP, buff=0.12)
        l15 = T("1.5t", 18, AMBER).next_to(p15, UP, buff=0.12)
        self.play(FadeIn(p05, scale=2), FadeIn(p15, scale=2), FadeIn(m05), FadeIn(l05), FadeIn(l15), run_time=0.8)
        ext = DashedLine(ax.c2p(1.5 * t_, bm["s15"]), ax.c2p(0, bm["hs_dnv"]), color=AMBER, stroke_width=3)
        hs = Star(5, outer_radius=0.16, color=AMBER, fill_opacity=1).move_to(ax.c2p(0, bm["hs_dnv"]))
        eqh = M(r"\sigma_{hs}=1.5\,\sigma_{0.5t}-0.5\,\sigma_{1.5t}", 30, AMBER).move_to(LEFT * 3.4 + DOWN * 2.45)
        self.wait_until(self.start("i") + 19.0)
        self.play(Create(ext), FadeIn(hs, scale=2), Write(eqh), run_time=1.4)
        hst = M(rf"\sigma_{{hs}}={bm['hs_dnv']:.0f}\,\mathrm{{MPa}}", 30, AMBER).next_to(ax.c2p(0, bm["hs_dnv"]), RIGHT, buff=0.3).shift(DOWN * 0.45)
        self.wait_until(self.start("i") + 24.5)
        self.play(FadeIn(hst), run_time=0.6)
        dnv = T("→ hot-spot S–N curve, e.g. DNV curve D  (log a = 12.164, m = 3)", 22, TXT).move_to(LEFT * 3.4 + DOWN * 3.15)
        self.wait_until(self.start("i") + 28.0)
        self.play(FadeIn(dnv, shift=UP * 0.1), run_time=0.8)
        self.wait_until(self.end("i") - 0.2)
        # ---- j: effective notch
        self.cue("j")
        self.play(FadeOut(VGroup(head, ax, xt, yt, xl, yl, curve, lin, peak_t, lin_t, p05, p15, l05, l15, ext, hs, hst, eqh, dnv, m05, surf_line)),
                  FadeOut(mid), run_time=0.6)
        head = T("3 · EFFECTIVE NOTCH STRESS", 30, RED, weight=BOLD).to_edge(UP, buff=0.9)
        toe = img(os.path.join(FRAMES, "weld_bending", "toe.png"), width=7.8).move_to(LEFT * 2.4 + DOWN * 0.4)
        XLt, YLt = (9.0, 19.0), (16.5, 24.0)
        Pt = lambda x, y: mm2pt(toe, x, y, XLt, YLt)
        self.play(FadeIn(head), FadeIn(toe), run_time=1.0)
        cx, cy = meta["cx"], meta["cy"]
        rr = Circle(radius=toe.width / 10.0 * 1.0, color=WHITE_, stroke_width=2.5).move_to(Pt(cx, cy))
        rr = DashedVMobject(rr, num_dashes=30)
        rline = Line(Pt(cx, cy), Pt(cx + 0.7071, cy + 0.7071), color=WHITE_, stroke_width=2.5)
        rt = M(r"r_{\mathrm{ref}}=1\,\mathrm{mm}", 30, TXT).next_to(Pt(cx + 0.9, cy + 0.9), RIGHT, buff=0.1)
        self.play(Create(rr), Create(rline), FadeIn(rt), run_time=1.2)
        nk = int(w["bending_k_notch"])
        npt = Pt(*w["nodes"][nk])
        star = Star(5, outer_radius=0.17, color=WHITE_, fill_opacity=1).move_to(npt)
        val = VGroup(M(rf"\sigma_{{\mathrm{{notch}}}}={bm['s_notch']:.0f}\,\mathrm{{MPa}}", 34, RED),
                     T("compare with the FAT 225 curve (IIW)", 22, TXT)).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        val.move_to(RIGHT * 4.6 + DOWN * 0.4)
        self.wait_until(self.start("j") + self.dur("j") * 0.45)
        self.play(FadeIn(star, scale=2), Write(val[0]), run_time=1.2)
        self.play(FadeIn(val[1]), run_time=0.6)
        self.wait_until(self.end("j") - 0.2)
        # ---- k: comparison of lives
        self.cue("k")
        self.play(FadeOut(VGroup(head, rr, rline, rt, star, val)), FadeOut(toe), run_time=0.6)
        lives = [("nominal stress, FAT 80", 2e6 * (80 / 100) ** 3, CYAN),
                 ("hot spot, DNV curve D", bm["lives"]["hotspot_DNV_D"], GREEN),
                 ("effective notch, FAT 225", bm["lives"]["notch_FAT225"], RED)]
        head = T("same joint, Δσ_nom = 100 MPa", 30, TXT, weight=BOLD).to_edge(UP, buff=0.9)
        ax = LogAxes((5, 7), (0, 3), x_length=8.0, y_length=3.6).move_to(RIGHT * 1.4 + DOWN * 0.4)
        xt = ax.xlabels([5, 6, 7], 24)
        xl = T("predicted life [cycles]", 22, MUTED).next_to(xt, DOWN, buff=0.12)
        self.play(FadeIn(head), Create(ax), FadeIn(xt), FadeIn(xl), run_time=0.8)
        bars = VGroup()
        for k, (name, N, col) in enumerate(lives):
            y = 2.5 - k
            x1 = ax.c2p(np.log10(N), y)[0]
            x0 = ax.c2p(5, y)[0]
            bar = Rectangle(width=x1 - x0, height=0.55, fill_color=col, fill_opacity=0.85, stroke_width=0)
            bar.move_to([(x0 + x1) / 2, ax.c2p(5, y)[1], 0])
            lab = T(name, 22, TXT).next_to([x0, ax.c2p(5, y)[1], 0], LEFT, buff=0.2)
            v = T(f"{N/1e6:.2f} M", 22, col, weight=BOLD).next_to(bar, RIGHT, buff=0.15)
            bars.add(VGroup(bar, lab, v))
        for b in bars:
            self.play(GrowFromEdge(b[0], LEFT), FadeIn(b[1]), FadeIn(b[2]), run_time=0.8)
        note = T("consistent — if each method's mesh & read-out rules are followed exactly", 22, AMBER).to_edge(DOWN, buff=0.6)
        self.wait_until(self.start("k") + self.dur("k") * 0.55)
        self.play(FadeIn(note, shift=UP * 0.1), run_time=0.8)
        self.wait_until(self.end("k") - 0.2)

    # ------------------------------------------------------------------ l
    def part_rainflow(self):
        self.cue("l")
        self.clear()
        U = load_npz("uniaxial_studies.npz")
        x = U["va_x"]
        s = x / np.max(np.abs(x)) * 120.0           # stress history [MPa]
        n = len(s)
        ax = Axes(x_range=[0, n, 100], y_range=[-140, 140, 70], x_length=8.6, y_length=3.0,
                  axis_config={"color": GRID, "stroke_width": 2, "include_ticks": False}, tips=False).move_to(LEFT * 2.2 + UP * 1.3)
        yl = M(r"\sigma(t)", 28, MUTED).next_to(ax.c2p(0, 140), UP, buff=0.05)
        sig = VMobject().set_points_as_corners([ax.c2p(i, v) for i, v in enumerate(s)]).set_stroke(MUTED, 2)
        head = T("Rainflow counting + Palmgren–Miner", 30, TXT, weight=BOLD).to_edge(UP, buff=0.9).shift(RIGHT * 2.5)
        self.play(FadeIn(head), Create(ax), FadeIn(yl), run_time=0.8)
        self.play(Create(sig), run_time=2.0, rate_func=linear)
        cyc = rainflow_idx(s)
        full = [c for c in cyc if c[3] == 1.0]
        # histogram axes
        hx = Axes(x_range=[0, 240, 40], y_range=[0, 12, 4], x_length=5.2, y_length=2.6,
                  axis_config={"color": GRID, "stroke_width": 2, "include_ticks": False}, tips=False).move_to(LEFT * 3.4 + DOWN * 2.1)
        hxl = M(r"\text{range }\Delta\sigma\;[\mathrm{MPa}]", 24, MUTED).next_to(hx, DOWN, buff=0.12)
        hyl = T("count", 20, MUTED).next_to(hx.c2p(0, 12), UP, buff=0.08)
        self.play(Create(hx), FadeIn(hxl), FadeIn(hyl), run_time=0.6)
        bins = np.arange(0, 241, 20)
        counts = np.zeros(len(bins) - 1)
        blocks = VGroup()
        cols = [CYAN, GREEN, AMBER, PINK, RED, VIOLET]
        order = sorted(full, key=lambda c: -c[2])
        shown = 0
        def add_block(r, cnt, col):
            k = min(int(r // 20), len(counts) - 1)
            h0 = counts[k]
            counts[k] += cnt
            x0, x1 = hx.c2p(bins[k], 0)[0], hx.c2p(bins[k + 1], 0)[0]
            y0, y1 = hx.c2p(0, h0)[1], hx.c2p(0, counts[k])[1]
            return Rectangle(width=(x1 - x0) * 0.9, height=max(y1 - y0, 0.01), fill_color=col, fill_opacity=0.85,
                             stroke_width=0).move_to([(x0 + x1) / 2, (y0 + y1) / 2, 0])
        for k, (i, j, r, c) in enumerate(order[:6]):
            col = cols[k % len(cols)]
            seg = VGroup(Dot(ax.c2p(i, s[i]), radius=0.07, color=col), Dot(ax.c2p(j, s[j]), radius=0.07, color=col),
                         DashedLine(ax.c2p(i, s[i]), ax.c2p(j, s[i]), color=col, stroke_width=2),
                         DoubleArrow(ax.c2p(j, s[i]), ax.c2p(j, s[j]), buff=0, color=col, stroke_width=4, tip_length=0.12))
            blk = add_block(r, 1.0, col)
            self.play(Create(seg), run_time=0.45)
            self.play(TransformFromCopy(seg, blk), run_time=0.55)
            blocks.add(seg, blk)
        rest = VGroup()
        for (i, j, r, c) in order[6:] + [cc for cc in cyc if cc[3] == 0.5]:
            rest.add(add_block(r, c, MUTED))
        self.play(LaggedStart(*[FadeIn(b) for b in rest], lag_ratio=0.03), run_time=1.6)
        # Miner
        miner = VGroup(M(r"D=\sum_i \frac{n_i}{N_i}", 44, TXT),
                       T("failure predicted at D = 1", 22, MUTED),
                       T("design: D ≤ 1 / DFF", 22, AMBER, weight=BOLD)).arrange(DOWN, buff=0.22).move_to(RIGHT * 3.9 + DOWN * 1.9)
        self.wait_until(self.start("l") + self.dur("l") * 0.55)
        self.play(Write(miner[0]), run_time=1.2)
        self.wait_until(self.start("l") + self.dur("l") * 0.75)
        self.play(FadeIn(miner[1]), run_time=0.6)
        self.wait_until(self.start("l") + self.dur("l") * 0.88)
        self.play(FadeIn(miner[2]), run_time=0.6)
        self.wait_until(self.end("l") - 0.2)

    # ------------------------------------------------------------------ m
    def part_multiaxial(self):
        self.cue("m")
        self.clear()
        seqt = T("Miner ignores sequence: high→low ≠ low→high", 26, AMBER, weight=BOLD).to_edge(UP, buff=0.95)
        self.play(FadeIn(seqt), run_time=0.6)
        # stress element with rotating critical plane
        sq = Square(2.2, color=TXT, stroke_width=3).move_to(LEFT * 4.0 + DOWN * 0.5)
        arrs = VGroup(Arrow(sq.get_right(), sq.get_right() + RIGHT * 0.9, buff=0, color=AMBER, stroke_width=5),
                      Arrow(sq.get_left(), sq.get_left() + LEFT * 0.9, buff=0, color=AMBER, stroke_width=5),
                      Arrow(sq.get_top() + LEFT * 0.7, sq.get_top() + RIGHT * 0.7, buff=0, color=CYAN, stroke_width=5),
                      Arrow(sq.get_bottom() + RIGHT * 0.7, sq.get_bottom() + LEFT * 0.7, buff=0, color=CYAN, stroke_width=5))
        plane = Line(sq.get_center() + LEFT * 1.4, sq.get_center() + RIGHT * 1.4, color=RED, stroke_width=4)
        self.play(Create(sq), LaggedStart(*[GrowArrow(a) for a in arrs], lag_ratio=0.2), run_time=1.2)
        self.play(Create(plane), run_time=0.4)
        self.play(Rotate(plane, PI, about_point=sq.get_center()), run_time=3.0, rate_func=linear)
        crit = VGroup(
            VGroup(T("stress invariants", 24, CYAN, weight=BOLD), T("Sines · Crossland", 22, TXT)).arrange(DOWN, aligned_edge=LEFT, buff=0.08),
            VGroup(T("mesoscopic", 24, GREEN, weight=BOLD), T("Dang Van", 22, TXT)).arrange(DOWN, aligned_edge=LEFT, buff=0.08),
            VGroup(T("critical plane", 24, RED, weight=BOLD), T("Findley", 22, TXT),
                   M(r"\tau_a + k\,\sigma_{n,\max} \le f", 30, TXT)).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.45).move_to(RIGHT * 2.6 + DOWN * 0.5)
        for c in crit:
            self.play(FadeIn(c, shift=LEFT * 0.2), run_time=0.7)
            self.wait(0.9)
        self.play(Rotate(plane, PI, about_point=sq.get_center()), run_time=self.until("m", 0.92), rate_func=linear)
