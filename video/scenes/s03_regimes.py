import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from common import *

E = 210000.0
SF, B, EF, C = 952.0, -0.089, 0.737, -0.668


class S03Regimes(SyncScene):
    scene_id = "s03_regimes"

    def construct(self):
        tag = chapter_tag(2, "LCF vs HCF")
        self.add(tag)
        U = load_npz("uniaxial_studies.npz")

        # ---------------------------------------------------------------- a
        q = T("What separates low-cycle from high-cycle fatigue?", 40, TXT, weight=BOLD).move_to(UP * 1.4)
        n = M(r"N = 10^4\,?", 70, MUTED).move_to(DOWN * 0.1)
        cross = Cross(n, stroke_color=RED, stroke_width=6)
        pl = T("PLASTICITY", 84, AMBER, weight=BOLD).move_to(DOWN * 0.3)
        self.play(FadeIn(q, shift=UP * 0.2), run_time=0.9)
        self.play(FadeIn(n), run_time=0.6)
        self.play(Create(cross), run_time=0.6)
        self.wait_until(self.start("a") + 4.6)
        self.play(FadeOut(VGroup(n, cross)), FadeIn(pl, scale=1.2), run_time=0.8)
        self.wait_until(self.end("a") - 0.1)

        # ---------------------------------------------------------------- b
        self.cue("b")
        self.play(FadeOut(VGroup(q, pl)), run_time=0.5)
        ax = Axes(x_range=[-0.9, 0.9, 0.3], y_range=[-480, 480, 160], x_length=7.2, y_length=5.6,
                  axis_config={"color": GRID, "stroke_width": 2, "include_ticks": False}).move_to(LEFT * 2.6 + DOWN * 0.35)
        xl = M(r"\varepsilon\;[\%]", 32, MUTED).next_to(ax.x_axis.get_right(), DOWN, buff=0.15)
        yl = M(r"\sigma\;[\mathrm{MPa}]", 32, MUTED).next_to(ax.y_axis.get_top(), RIGHT, buff=0.15)
        self.play(Create(ax), FadeIn(xl), FadeIn(yl), run_time=1.0)
        # elastic line
        e_el = np.concatenate([np.linspace(0, 0.1, 30), np.linspace(0.1, -0.1, 60), np.linspace(-0.1, 0.1, 60)])
        line = loop_curve(ax, e_el, E * e_el / 100, CYAN, 4)
        dot = Dot(color=WHITE_, radius=0.07)
        lab_el = T("small amplitude: elastic line", 24, CYAN, weight=BOLD).move_to(RIGHT * 3.7 + UP * 2.2)
        self.play(Create(line), MoveAlongPath(dot, line), FadeIn(lab_el), run_time=3.0, rate_func=linear)
        # loop at 0.4 %
        n1 = 320
        e4, s4 = U["loop_40_eps"] * 100, U["loop_40_sig"]
        loop = loop_curve(ax, e4[-n1 - 1:], s4[-n1 - 1:], AMBER, 4)
        first = loop_curve(ax, e4[:n1 // 4 + 1], s4[:n1 // 4 + 1], AMBER, 2.5).set_stroke(opacity=0.5)
        lab_pl = T("past cyclic yield: hysteresis loop", 24, AMBER, weight=BOLD).next_to(lab_el, DOWN, buff=0.35, aligned_edge=LEFT)
        self.wait(0.8)
        self.play(Create(first), run_time=1.4, rate_func=linear)
        self.play(Create(loop), MoveAlongPath(dot, loop), FadeIn(lab_pl), run_time=4.5, rate_func=linear)
        area = Polygon(*[ax.c2p(x, y) for x, y in zip(e4[-n1:][::4], s4[-n1:][::4])],
                       fill_color=AMBER, fill_opacity=0.25, stroke_width=0)
        # plastic strain range at sigma = 0
        lc = slice(-n1, None)
        ee, ss = e4[lc], s4[lc]
        zc = np.nonzero(np.diff(np.sign(ss)) != 0)[0]
        xz = [ee[k] - ss[k] * (ee[k + 1] - ee[k]) / (ss[k + 1] - ss[k]) for k in zc[:2]]
        xz.sort()
        dep_line = DoubleArrow(ax.c2p(xz[0], -60), ax.c2p(xz[1], -60), buff=0, color=PINK, stroke_width=4, tip_length=0.18)
        dep_t = M(r"\Delta\varepsilon_p", 34, PINK).next_to(dep_line, DOWN, buff=0.1)
        self.wait_until(self.start("b") + self.dur("b") * 0.6)
        self.play(GrowFromCenter(dep_line), FadeIn(dep_t), run_time=1.0)
        area_t = T("area = plastic work\ndissipated per cycle", 24, AMBER).move_to(RIGHT * 3.7 + DOWN * 0.2)
        arr = Arrow(area_t.get_left(), ax.c2p(0.12, 150), color=AMBER, stroke_width=3, buff=0.15)
        self.play(FadeIn(area), FadeIn(area_t), GrowArrow(arr), run_time=1.2)
        self.wait_until(self.end("b") - 0.2)

        # ---------------------------------------------------------------- c
        self.cue("c")
        e8, s8 = U["loop_80_eps"] * 100, U["loop_80_sig"]
        fat = loop_curve(ax, e8[-n1 - 1:], s8[-n1 - 1:], AMBER, 4)
        self.play(FadeOut(VGroup(lab_el, lab_pl, area_t, arr, dep_line, dep_t, area, first, dot)),
                  Transform(loop, fat), run_time=1.0)
        lcf = VGroup(T("LOW-CYCLE FATIGUE", 28, AMBER, weight=BOLD),
                     M(r"\Delta\varepsilon_p \gg \Delta\varepsilon_e", 34, TXT),
                     T("N ≲ 10⁴ – 10⁵ cycles", 24, TXT),
                     T("strain controls the damage", 24, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        hcf = VGroup(T("HIGH-CYCLE FATIGUE", 28, CYAN, weight=BOLD),
                     M(r"\Delta\varepsilon_p \approx 0", 34, TXT),
                     T("N ≳ 10⁵ cycles", 24, TXT),
                     T("stress controls the damage", 24, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        lcf.move_to(RIGHT * 4.0 + UP * 1.5)
        hcf.move_to(RIGHT * 4.0 + DOWN * 1.6).align_to(lcf, LEFT)
        bl = SurroundingRectangle(lcf, color=AMBER, buff=0.25, corner_radius=0.15, stroke_width=1.5)
        bh = SurroundingRectangle(hcf, color=CYAN, buff=0.25, corner_radius=0.15, stroke_width=1.5)
        self.play(FadeIn(lcf, shift=LEFT * 0.2), Create(bl), run_time=1.0)
        self.wait_until(self.start("c") + self.dur("c") * 0.62)
        self.play(FadeIn(hcf, shift=LEFT * 0.2), Create(bh), Indicate(line, color=CYAN), run_time=1.0)
        self.wait_until(self.end("c") - 0.3)

        # ---------------------------------------------------------------- d
        self.cue("d")
        self.play(FadeOut(VGroup(ax, xl, yl, line, loop, lcf, hcf, bl, bh)), run_time=0.7)
        ax2 = LogAxes((0, 10), (-4.2, 0.2), x_length=10.4, y_length=5.3).move_to(LEFT * 0.9 + DOWN * 0.55)
        xt = ax2.xlabels(range(0, 11, 2), 24)
        yt = ax2.ylabels(range(-4, 1, 1), 24)
        xlab = M(r"\text{reversals to failure } 2N_f", 30, MUTED).next_to(xt, DOWN, buff=0.2)
        ylab = M(r"\varepsilon_a", 34, MUTED).next_to(ax2.c2p(0, 0.2), RIGHT, buff=0.2)
        el = lambda x: np.log10(SF / E) + B * x
        pl_ = lambda x: np.log10(EF) + C * x
        tot = lambda x: np.log10(10 ** el(x) + 10 ** pl_(x))
        c_el = ax2.plot(el, x_range=[0, 10], color=CYAN, stroke_width=4)
        c_pl = ax2.plot(pl_, x_range=[0, 6.15], color=AMBER, stroke_width=4)
        c_tot = ax2.plot(tot, x_range=[0, 10], color=WHITE_, stroke_width=5)
        eq = M(r"\varepsilon_a=", r"\frac{\sigma_f'}{E}(2N_f)^{b}", r"+", r"\varepsilon_f'(2N_f)^{c}", size=40).to_corner(UR, buff=0.5).shift(DOWN * 0.45)
        eq[1].set_color(CYAN)
        eq[3].set_color(AMBER)
        mask = ax2.vband(7.02, 10.2, BG, 0.85)
        self.play(Create(ax2), FadeIn(xt), FadeIn(yt), FadeIn(xlab), FadeIn(ylab), run_time=1.2)
        self.add(mask)
        self.play(Create(c_el), run_time=1.6)
        lbl_el = T("elastic: Basquin", 24, CYAN, weight=BOLD).next_to(ax2.c2p(5.2, el(5.2)), UP, buff=0.15)
        self.play(FadeIn(lbl_el), Write(eq[0]), Write(eq[1]), run_time=1.0)
        self.play(Create(c_pl), run_time=1.6)
        lbl_pl = T("plastic: Coffin–Manson", 24, AMBER, weight=BOLD).next_to(ax2.c2p(1.2, pl_(1.2)), RIGHT, buff=0.2)
        self.play(FadeIn(lbl_pl), Write(eq[2]), Write(eq[3]), run_time=1.0)
        self.play(Create(c_tot), run_time=1.8)
        lbl_t = T("total", 24, WHITE_, weight=BOLD).next_to(ax2.c2p(0.4, tot(0.4)), UP, buff=0.12)
        self.play(FadeIn(lbl_t), run_time=0.5)

        # ---------------------------------------------------------------- e
        self.cue("e")
        xt_ = np.log10((EF * E / SF) ** (1 / (B - C)))
        pt = Dot(ax2.c2p(xt_, el(xt_)), radius=0.1, color=PINK)
        vl = DashedLine(ax2.c2p(xt_, -4.2), ax2.c2p(xt_, 0.2), color=PINK, stroke_width=2.5)
        tl = VGroup(M(r"2N_t \approx 6\,600", 30, PINK), T("(N ≈ 3 300 cycles)", 22, PINK)).arrange(DOWN, buff=0.08)
        tl.next_to(ax2.c2p(xt_, -0.3), RIGHT, buff=0.15)
        self.play(FadeIn(pt, scale=2), Create(vl), FadeIn(tl), run_time=1.2)
        rl = ax2.vband(0, xt_, AMBER, 0.10)
        rh = ax2.vband(xt_, 7, CYAN, 0.08)
        tL = T("LCF · ductility", 26, AMBER, weight=BOLD).move_to(ax2.c2p(1.9, -3.7))
        tH = T("HCF · strength", 26, CYAN, weight=BOLD).move_to(ax2.c2p(5.4, -3.7))
        self.play(FadeIn(rl), FadeIn(rh), FadeIn(tL), FadeIn(tH), run_time=1.2)
        # illustrative high-strength steel
        self.wait_until(self.start("e") + self.dur("e") * 0.72)
        sf2, b2, ef2, c2 = 1800.0, -0.08, 0.3, -0.70
        x2 = np.log10((ef2 * E / sf2) ** (1 / (b2 - c2)))
        g_el = ax2.plot(lambda x: np.log10(sf2 / E) + b2 * x, x_range=[0, 6.9], color=VIOLET, stroke_width=2.5)
        g_pl = ax2.plot(lambda x: np.log10(ef2) + c2 * x, x_range=[0, 5.2], color=VIOLET, stroke_width=2.5)
        g_el.set_stroke(opacity=0.8); g_pl.set_stroke(opacity=0.8)
        gpt = Dot(ax2.c2p(x2, np.log10(sf2 / E) + b2 * x2), radius=0.08, color=VIOLET)
        gl = T("high-strength steel (illustrative): 2Nₜ ≈ 300", 20, VIOLET).next_to(ax2.c2p(0.2, -3.2), RIGHT, buff=0.0)
        self.play(Create(g_el), Create(g_pl), FadeIn(gpt), FadeIn(gl), run_time=1.6)
        self.wait_until(self.end("e") - 0.2)

        # ---------------------------------------------------------------- f
        self.cue("f")
        self.play(FadeOut(VGroup(g_el, g_pl, gpt, gl)), FadeOut(mask), run_time=0.8)
        rv = ax2.vband(7, 10, VIOLET, 0.12)
        tV = T("VHCF", 26, VIOLET, weight=BOLD).move_to(ax2.c2p(8.5, -3.7))
        self.play(FadeIn(rv), FadeIn(tV), run_time=0.8)
        # fish-eye inset
        fe_c = ax2.c2p(8.5, -0.9)
        disc = Circle(radius=0.85, color=TXT, stroke_width=2).set_fill("#2b3550", 1).move_to(fe_c)
        eye = Circle(radius=0.36, color=AMBER, stroke_width=2).set_fill(AMBER, 0.22).move_to(fe_c + LEFT * 0.12 + UP * 0.1)
        inc = Dot(eye.get_center(), radius=0.06, color=RED)
        fl = T("fish-eye from an\ninternal inclusion", 20, AMBER).next_to(disc, DOWN, buff=0.12)
        self.play(FadeIn(disc), GrowFromCenter(eye), FadeIn(inc), FadeIn(fl), run_time=1.2)
        lim = DashedLine(ax2.c2p(6.3, tot(6.3)), ax2.c2p(10, tot(6.3)), color=MUTED, stroke_width=2.5)
        limt = T("classical 'fatigue limit'?", 20, MUTED).next_to(ax2.c2p(8.5, tot(6.3)), UP, buff=0.12)
        self.wait_until(self.start("f") + self.dur("f") * 0.6)
        self.play(Create(lim), FadeIn(limt), run_time=1.0)
        self.play(Indicate(c_tot, color=VIOLET), run_time=1.4)
        self.wait_until(self.end("f") - 0.2)

        # ---------------------------------------------------------------- g
        self.cue("g")
        plot_all = Group(*[m for m in self.mobjects if m is not tag])
        self.play(FadeOut(plot_all), run_time=0.7)
        big = img(frames("shake_vm_peak")[0], height=5.9).move_to(LEFT * 3.9 + DOWN * 0.05)
        box = Square(side_length=big.height * 34 / 124, color=WHITE_, stroke_width=2).move_to(big.get_center())
        box.stretch_to_fit_height(big.height * 25.5 / 124)
        zoom = img(frames("shake_zone_zoom")[0], width=5.4).move_to(RIGHT * 2.7 + UP * 0.35)
        zframe = SurroundingRectangle(zoom, color=WHITE_, stroke_width=2, buff=0.0)
        l1 = Line(box.get_corner(UR), zframe.get_corner(UL), color=WHITE_, stroke_width=1.5, stroke_opacity=0.6)
        l2 = Line(box.get_corner(DR), zframe.get_corner(DL), color=WHITE_, stroke_width=1.5, stroke_opacity=0.6)
        self.play(FadeIn(big), run_time=1.0)
        t_bulk = T("bulk: elastic", 26, CYAN, weight=BOLD).next_to(big, DOWN, buff=0.15)
        self.play(FadeIn(t_bulk), Create(box), run_time=0.8)
        self.play(Create(l1), Create(l2), FadeIn(zoom), Create(zframe), run_time=1.2)
        t_root = T("notch root: plastic zone", 26, AMBER, weight=BOLD).next_to(zframe, UP, buff=0.12)
        self.play(FadeIn(t_root), run_time=0.6)
        msg = VGroup(T("elastic surroundings impose a strain cycle on the notch", 22, TXT),
                     T("→ local strain approach", 24, GREEN, weight=BOLD),
                     T("→ finite element analysis in both regimes", 24, GREEN, weight=BOLD)
                     ).arrange(DOWN, buff=0.14).next_to(zframe, DOWN, buff=0.3)
        self.wait_until(self.start("g") + self.dur("g") * 0.45)
        self.play(FadeIn(msg[0], shift=UP * 0.1), run_time=0.8)
        self.wait_until(self.start("g") + self.dur("g") * 0.75)
        self.play(FadeIn(msg[1:], shift=UP * 0.1), run_time=0.8)
        self.finish()
