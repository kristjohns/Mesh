import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from common import *

E = 210000.0


class S07APS(SyncScene):
    scene_id = "s07_aps"

    def construct(self):
        self.tag = chapter_tag(6, "Accumulated plastic strain")
        self.add(self.tag)
        self.part_definition()
        self.part_responses()
        self.part_melan()
        self.part_bree()
        self.part_plate()
        self.part_material()
        self.part_practice()
        self.part_answer()
        self.finish()

    def clear(self, rt=0.6, keep=()):
        objs = [m for m in self.mobjects if m is not self.tag and m not in keep]
        if objs:
            self.play(*[FadeOut(m) for m in objs], run_time=rt)

    # ------------------------------------------------------------------ a, b, c
    def part_definition(self):
        eq = M(r"\bar{\varepsilon}_p=\int_0^t\sqrt{\tfrac{2}{3}\,\dot{\boldsymbol{\varepsilon}}_p:\dot{\boldsymbol{\varepsilon}}_p}\;dt", 60, TXT).move_to(UP * 1.2)
        names = T("equivalent plastic strain  ·  PEEQ (Abaqus)  ·  accumulated plastic strain", 24, MUTED).next_to(eq, DOWN, buff=0.5)
        self.play(Write(eq), run_time=2.4)
        self.play(FadeIn(names), run_time=0.8)
        box = SurroundingRectangle(eq[0][8:], color=AMBER, buff=0.1, corner_radius=0.1)
        note = T("a magnitude: always ≥ 0", 26, AMBER, weight=BOLD).next_to(names, DOWN, buff=0.5)
        self.wait_until(self.start("a") + self.dur("a") * 0.62)
        self.play(Create(box), FadeIn(note), run_time=1.0)
        self.wait_until(self.end("a") - 0.2)
        # ---- b
        self.cue("b")
        self.play(FadeOut(VGroup(names, note, box)), eq.animate.scale(0.55).to_corner(UR, buff=0.5).shift(DOWN * 0.3), run_time=0.8)
        d = load_npz("plate_lcf.npz")
        m = d["T_cycle"] <= 4
        tc = np.concatenate([[0], d["T_tc"][m]])
        epl = np.concatenate([[0], d["T_root_epyy"][m] * 100])
        eto = np.concatenate([[0], d["T_root_eyy"][m] * 100])
        pe = np.concatenate([[0], d["T_root_peeq"][m] * 100])
        ax = Axes(x_range=[0, 4, 1], y_range=[-0.6, 3.6, 0.5], x_length=9.0, y_length=5.0,
                  axis_config={"color": GRID, "stroke_width": 2, "include_ticks": True, "tick_size": 0.05}, tips=False).move_to(LEFT * 1.0 + DOWN * 0.5)
        xt = VGroup(*[T(str(v), 20, MUTED).next_to(ax.c2p(v, -0.6), DOWN, buff=0.1) for v in range(5)])
        yt = VGroup(*[T(f"{v:g}", 20, MUTED).next_to(ax.c2p(0, v), LEFT, buff=0.1) for v in [0, 1, 2, 3]])
        xl = T("cycles (case 3, notch root)", 22, MUTED).next_to(xt, DOWN, buff=0.1)
        yl = T("strain [%]", 22, MUTED).next_to(ax.c2p(0, 3.6), UP, buff=0.1).align_to(ax, LEFT)
        zero = DashedLine(ax.c2p(0, 0), ax.c2p(4, 0), color=GRID, stroke_width=1.5)
        self.play(Create(ax), FadeIn(xt), FadeIn(yt), FadeIn(xl), FadeIn(yl), Create(zero), run_time=0.8)
        c_e = VMobject().set_points_as_corners([ax.c2p(a, b) for a, b in zip(tc, eto)]).set_stroke(CYAN, 3)
        c_p = VMobject().set_points_as_corners([ax.c2p(a, b) for a, b in zip(tc, epl)]).set_stroke(AMBER, 3)
        c_q = VMobject().set_points_as_corners([ax.c2p(a, b) for a, b in zip(tc, pe)]).set_stroke(PINK, 5)
        leg = VGroup(VGroup(Line(ORIGIN, RIGHT * 0.45, color=CYAN, stroke_width=4), T("total strain ε_yy", 22, CYAN)).arrange(RIGHT, buff=0.15),
                     VGroup(Line(ORIGIN, RIGHT * 0.45, color=AMBER, stroke_width=4), T("plastic strain ε_p,yy", 22, AMBER)).arrange(RIGHT, buff=0.15),
                     VGroup(Line(ORIGIN, RIGHT * 0.45, color=PINK, stroke_width=6), T("PEEQ", 22, PINK, weight=BOLD)).arrange(RIGHT, buff=0.15)
                     ).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to(RIGHT * 4.9 + UP * 0.9)
        self.play(Create(c_e), Create(c_p), Create(c_q), FadeIn(leg), run_time=6.0, rate_func=linear)
        sl = T("+0.82 % every cycle", 26, PINK, weight=BOLD).next_to(ax.c2p(3.0, pe[np.searchsorted(tc, 3.0)]), UP + LEFT, buff=0.1)
        bnd = VGroup(DashedLine(ax.c2p(0, 0.383), ax.c2p(4, 0.383), color=CYAN, stroke_width=2),
                     DashedLine(ax.c2p(0, -0.383), ax.c2p(4, -0.383), color=CYAN, stroke_width=2))
        bt = T("strain only oscillates: ±0.38 %", 22, CYAN).next_to(ax.c2p(4, -0.383), DOWN, buff=0.12).align_to(ax.c2p(2.0, 0), LEFT)
        self.wait_until(self.start("b") + self.dur("b") * 0.6)
        self.play(FadeIn(sl), run_time=0.8)
        self.wait_until(self.start("b") + self.dur("b") * 0.8)
        self.play(Create(bnd), FadeIn(bt), run_time=1.0)
        self.wait_until(self.end("b") - 0.2)
        # ---- c
        self.cue("c")
        self.clear()
        q = T("large PEEQ = fatigue?  ratcheting?  neither?", 34, TXT, weight=BOLD).move_to(UP * 1.6)
        self.play(FadeIn(q), run_time=0.8)
        f1 = VGroup(T("look at the plastic strain tensor over one complete cycle:", 24, MUTED),
                    M(r"\Delta\boldsymbol{\varepsilon}_p^{\,\mathrm{cycle}}=\boldsymbol{\varepsilon}_p(t_N)-\boldsymbol{\varepsilon}_p(t_{N-1})", 40, AMBER),
                    T("≈ 0  →  shakedown or closed plastic cycle          ≠ 0  →  ratcheting", 24, TXT),
                    T("plus the plastic strain range inside the cycle  →  low-cycle fatigue", 24, TXT)).arrange(DOWN, buff=0.3).move_to(DOWN * 0.6)
        for k, f in enumerate(f1):
            self.play(FadeIn(f, shift=UP * 0.1), run_time=0.7)
            self.wait(0.8)
        self.wait_until(self.end("c") - 0.2)

    # ------------------------------------------------------------------ d
    def part_responses(self):
        self.cue("d")
        self.clear()
        cards = []
        spec = [("hcf", "ELASTIC", C_EL, "no yielding"),
                ("shake", "ELASTIC SHAKEDOWN", C_SD, "yield only in the first cycles"),
                ("lcf", "ALTERNATING PLASTICITY", C_AP, "closed plastic cycle repeats"),
                ("ratchet_m", "RATCHETING", C_RT, "net plastic strain every cycle")]
        xs = [-5.2, -1.75, 1.75, 5.2]
        self.resp = []
        for (case, title, col, sub), x in zip(spec, xs):
            d = load_npz(f"plate_{case}.npz")
            e, s = d["T_root_eyy"] * 100, d["T_root_syy"]
            lo, hi = min(e.min(), 0), max(e.max(), 0.05)
            ax = Axes(x_range=[lo, hi, (hi - lo) / 2], y_range=[-420, 420, 210], x_length=2.9, y_length=2.5,
                      axis_config={"color": GRID, "stroke_width": 1.5, "include_ticks": False}, tips=False)
            lp = VMobject().set_points_as_corners([ax.c2p(a, b) for a, b in zip(e, s)]).set_stroke(col, 2.5)
            root = int(d["probes"][0])
            pe = np.concatenate([[0], d["T_root_peeq"] * 100])
            tcy = np.concatenate([[0], d["T_tc"]])
            ax2 = Axes(x_range=[0, 12, 4], y_range=[0, 10, 5], x_length=2.9, y_length=1.3,
                       axis_config={"color": GRID, "stroke_width": 1.5, "include_ticks": False}, tips=False)
            sp = VMobject().set_points_as_corners([ax2.c2p(a, min(b, 10)) for a, b in zip(tcy, pe)]).set_stroke(col, 3)
            pl = T("PEEQ vs cycles", 16, MUTED).next_to(ax2, DOWN, buff=0.05)
            ttl = T(title, 20, col, weight=BOLD)
            st = T(sub, 17, TXT)
            grp = VGroup(ttl, VGroup(ax, lp), VGroup(ax2, sp, pl), st).arrange(DOWN, buff=0.22)
            bx = card(3.3, 6.4).move_to(grp)
            bx.set_stroke(col, 1.5)
            G = VGroup(bx, grp).move_to([x, -0.35, 0])
            cards.append((G, lp, sp))
            self.resp.append((title, col, VGroup(ax2.copy(), sp.copy())))
        for G, lp, sp in cards:
            self.play(FadeIn(G[0]), FadeIn(G[1][0]), FadeIn(G[1][1][0]), FadeIn(G[1][2][0]), FadeIn(G[1][2][2]), FadeIn(G[1][3]), run_time=0.6)
            self.play(Create(lp), Create(sp), run_time=2.6, rate_func=linear)
        self.wait_until(self.end("d") - 0.2)

    # ------------------------------------------------------------------ e
    def part_melan(self):
        self.cue("e")
        self.clear()
        ax = Axes(x_range=[-1.6, 1.6, 0.5], y_range=[-1.6, 1.6, 0.5], x_length=5.6, y_length=5.6,
                  axis_config={"color": GRID, "stroke_width": 2, "include_ticks": False}, tips=False).move_to(LEFT * 3.6 + DOWN * 0.4)
        xl = M(r"\sigma_1/\sigma_y", 26, MUTED).next_to(ax.x_axis.get_right(), DOWN, buff=0.1)
        yl = M(r"\sigma_2/\sigma_y", 26, MUTED).next_to(ax.y_axis.get_top(), RIGHT, buff=0.1)
        t = np.linspace(0, 2 * np.pi, 300)
        # von Mises ellipse s1^2 - s1 s2 + s2^2 = 1 -> principal axes at 45 deg
        a, b = np.sqrt(2.0), np.sqrt(2.0 / 3.0)
        pts = [ax.c2p((a * np.cos(u) - b * np.sin(u)) / np.sqrt(2), (a * np.cos(u) + b * np.sin(u)) / np.sqrt(2)) for u in t]
        ell = VMobject().set_points_smoothly(pts).set_stroke(TXT, 3).set_fill(CYAN, 0.06)
        el_t = T("yield surface", 20, MUTED).next_to(ax.c2p(1.05, 1.15), RIGHT, buff=0.05)
        self.play(Create(ax), FadeIn(xl), FadeIn(yl), Create(ell), FadeIn(el_t), run_time=1.2)
        A = np.array([1.45, 0.25])
        seg = Line(ax.c2p(0, 0), ax.c2p(*A), color=AMBER, stroke_width=6)
        segt = T("elastic stress path, cycled", 20, AMBER).next_to(ax.c2p(1.0, -0.9), DOWN, buff=0.0)
        self.play(Create(seg), FadeIn(segt), run_time=1.0)
        rho = np.array([-0.62, -0.05])
        seg2 = Line(ax.c2p(*rho), ax.c2p(*(A + rho)), color=GREEN, stroke_width=6)
        rarr = Arrow(ax.c2p(*A), ax.c2p(*(A + rho)), buff=0.05, color=PINK, stroke_width=4)
        rt = M(r"+\boldsymbol{\rho}", 32, PINK).next_to(rarr, UP, buff=0.05)
        self.wait_until(self.start("e") + 5.5)
        self.play(GrowArrow(rarr), FadeIn(rt), run_time=0.8)
        self.play(TransformFromCopy(seg, seg2), run_time=1.2)
        ok = T("fits inside → elastic shakedown", 20, GREEN, weight=BOLD).next_to(ax, DOWN, buff=0.25)
        self.play(FadeIn(ok), run_time=0.6)
        thm = VGroup(T("Melan's theorem", 30, TXT, weight=BOLD),
                     T("if a constant, self-equilibrating residual\nstress field ρ exists such that", 22, MUTED),
                     M(r"f\big(\boldsymbol{\sigma}^{el}(t)+\boldsymbol{\rho}\big)\le 0\quad\forall t", 36, TXT),
                     T("then the structure shakes down", 22, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to(RIGHT * 3.4 + UP * 1.4)
        self.play(FadeIn(thm, shift=LEFT * 0.2), run_time=1.2)
        self.wait_until(self.start("e") + self.dur("e") * 0.55)
        # too long a range
        A2 = np.array([2.3, 0.4])
        segL = Line(ax.c2p(-0.75, -0.13), ax.c2p(*(A2 + np.array([-0.75, -0.13]))), color=RED, stroke_width=6)
        self.play(FadeOut(VGroup(seg2, rarr, rt, ok, segt)), Transform(seg, segL), run_time=1.0)
        no = T("range > 2σy: cannot fit → no shakedown", 20, RED, weight=BOLD).next_to(ax, DOWN, buff=0.25)
        self.play(FadeIn(no), run_time=0.6)
        rule = VGroup(M(r"\Delta\sigma^{el}_{eq}\le 2\,\sigma_y", 40, AMBER),
                      T("ASME VIII-2: range of P_L + P_b + Q\n≤ S_PS = max(3S, 2S_y)", 22, TXT)).arrange(DOWN, buff=0.25).move_to(RIGHT * 3.4 + DOWN * 1.6)
        self.wait_until(self.start("e") + self.dur("e") * 0.72)
        self.play(Write(rule[0]), run_time=1.0)
        self.play(FadeIn(rule[1]), run_time=0.8)
        self.wait_until(self.end("e") - 0.2)

    # ------------------------------------------------------------------ f, g
    def part_bree(self):
        self.cue("f")
        self.clear()
        c = LEFT * 3.6 + DOWN * 0.3
        outer = Circle(radius=2.3, color=TXT, stroke_width=3).move_to(c)
        inner = Circle(radius=1.85, color=TXT, stroke_width=3).move_to(c)
        wall = Annulus(inner_radius=1.85, outer_radius=2.3, fill_color="#2b3550", fill_opacity=1, stroke_width=0).move_to(c)
        press = VGroup(*[Arrow(c + 1.05 * np.array([np.cos(a), np.sin(a), 0]), c + 1.8 * np.array([np.cos(a), np.sin(a), 0]),
                               buff=0, color=AMBER, stroke_width=4, max_tip_length_to_length_ratio=0.3) for a in np.linspace(0, 2 * PI, 12, endpoint=False)])
        pt = T("pressure p\n(primary, sustained)", 22, AMBER).move_to(c)
        self.play(FadeIn(wall), Create(outer), Create(inner), run_time=1.0)
        self.play(LaggedStart(*[GrowArrow(p) for p in press], lag_ratio=0.05), FadeIn(pt), run_time=1.2)
        heat = Annulus(inner_radius=1.85, outer_radius=2.07, fill_color=RED, fill_opacity=0.0, stroke_width=0).move_to(c)
        self.add(heat)
        tt = T("cyclic through-wall ΔT\n(secondary)", 22, RED).next_to(outer, DOWN, buff=0.2)
        self.play(heat.animate.set_fill(opacity=0.75), FadeIn(tt), run_time=1.0)
        self.play(heat.animate.set_fill(opacity=0.0), run_time=1.0)
        self.play(heat.animate.set_fill(opacity=0.75), run_time=1.0)
        # stresses through the wall
        ax = Axes(x_range=[-0.5, 0.5, 0.5], y_range=[-1.5, 2.0, 0.5], x_length=4.2, y_length=4.2,
                  axis_config={"color": GRID, "stroke_width": 2, "include_ticks": False}, tips=False).move_to(RIGHT * 2.8 + DOWN * 0.4)
        xl = T("through the wall", 20, MUTED).next_to(ax, DOWN, buff=0.15)
        yl = M(r"\sigma_\theta/\sigma_y", 26, MUTED).next_to(ax.y_axis.get_top(), RIGHT, buff=0.1)
        X = 0.5
        prim = ax.plot(lambda y: X, x_range=[-0.5, 0.5], color=AMBER, stroke_width=4)
        sec = ax.plot(lambda y: X - 2.0 * y * 1.2, x_range=[-0.5, 0.5], color=RED, stroke_width=4)
        lp = M(r"X=\sigma_p/\sigma_y", 28, AMBER).next_to(ax.c2p(0.5, X), RIGHT, buff=0.1)
        ls = M(r"Y=\sigma_t/\sigma_y", 28, RED).next_to(ax.c2p(0.5, X - 1.2), RIGHT, buff=0.1)
        self.play(Create(ax), FadeIn(xl), FadeIn(yl), Create(prim), FadeIn(lp), run_time=1.2)
        self.play(TransformFromCopy(prim, sec), FadeIn(ls), run_time=1.2)
        self.wait_until(self.end("f") - 0.2)
        # ---- g: map
        self.cue("g")
        self.clear()
        tr = ValueTracker(0)
        mp = FrameSeq(frames("bree_fill"), tr, height=5.5)
        mp.stretch_to_fit_width(5.5 * 1.25)
        mp.move_to(LEFT * 1.9 + DOWN * 0.25)
        X0, X1 = mp.get_left()[0], mp.get_right()[0]
        Y0, Y1 = mp.get_bottom()[1], mp.get_top()[1]
        P = lambda x, y: np.array([X0 + (X1 - X0) * x / 1.0, Y0 + (Y1 - Y0) * y / 4.0, 0])
        frame_ = Rectangle(width=X1 - X0, height=Y1 - Y0, color=GRID, stroke_width=2).move_to(mp)
        xt = VGroup(*[T(f"{v:g}", 20, MUTED).next_to(P(v, 0), DOWN, buff=0.1) for v in [0, 0.5, 1]])
        yt = VGroup(*[T(f"{v}", 20, MUTED).next_to(P(0, v), LEFT, buff=0.1) for v in [0, 1, 2, 3, 4]])
        xl = M(r"X=\sigma_{\mathrm{primary}}/\sigma_y", 28, AMBER).next_to(xt, DOWN, buff=0.1)
        yl = M(r"Y=\sigma_{\mathrm{thermal}}/\sigma_y", 28, RED).rotate(PI / 2).next_to(yt, LEFT, buff=0.15)
        self.add(mp)
        self.play(Create(frame_), FadeIn(xt), FadeIn(yt), FadeIn(xl), FadeIn(yl), run_time=1.0)
        info = VGroup(T("6 561 load combinations", 22, TXT), T("× 24 cycles each", 22, TXT),
                      T("through-wall fibre model", 22, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.1).to_edge(RIGHT, buff=0.5).shift(UP * 2.0)
        self.play(FadeIn(info), run_time=0.6)
        self.play(tr.animate.set_value(60), run_time=9.0, rate_func=linear)
        # analytical boundaries
        def pl(xs, ys, col=WHITE_):
            return VMobject().set_points_as_corners([P(x, y) for x, y in zip(xs, ys)]).set_stroke(col, 3.5)
        xx = np.linspace(0, 1, 50)
        b_el = pl(xx, 1 - xx)
        xa = np.linspace(0.5, 1.0, 40)
        b_r1 = pl(xa, 4 * (1 - xa))
        yb = np.linspace(2.0, 4.0, 40)
        b_r2 = pl(1 / yb, yb)
        b_p = pl([0, 0.5], [2, 2])
        self.play(Create(b_el), Create(b_r1), Create(b_r2), Create(b_p), run_time=2.0)
        labs = VGroup(T("E", 30, BG, weight=BOLD).move_to(P(0.22, 0.35)),
                      T("S", 30, BG, weight=BOLD).move_to(P(0.35, 1.3)),
                      T("P", 30, BG, weight=BOLD).move_to(P(0.12, 3.2)),
                      T("R₁", 30, BG, weight=BOLD).move_to(P(0.83, 1.6)),
                      T("R₂", 30, BG, weight=BOLD).move_to(P(0.6, 3.2)))
        self.play(LaggedStart(*[FadeIn(l, scale=1.3) for l in labs], lag_ratio=0.15), run_time=1.2)
        leg = VGroup(*[VGroup(Square(0.28, fill_color=c, fill_opacity=0.95, stroke_width=0), T(n, 22, TXT)).arrange(RIGHT, buff=0.15)
                       for c, n in [(C_EL, "elastic"), (C_SD, "shakedown"), (C_AP, "alternating plasticity"), (C_RT, "ratcheting")]]
                     ).arrange(DOWN, aligned_edge=LEFT, buff=0.16).next_to(info, DOWN, buff=0.5, aligned_edge=LEFT)
        self.play(FadeIn(leg), run_time=0.6)
        agree = VGroup(T("lines: Bree (1967), analytical", 20, TXT), T("agreement:\n6 560 / 6 561 points", 22, GREEN, weight=BOLD)
                       ).arrange(DOWN, aligned_edge=LEFT, buff=0.1).next_to(leg, DOWN, buff=0.5, aligned_edge=LEFT)
        self.wait_until(self.start("g") + self.dur("g") * 0.8)
        self.play(FadeIn(agree), run_time=0.8)
        self.wait_until(self.end("g") - 0.2)

    # ------------------------------------------------------------------ h, i
    def part_plate(self):
        self.cue("h")
        self.clear()
        temp = img(frames("tm_ratchet_temp")[0], height=2.6).move_to(LEFT * 5.6 + UP * 1.6)
        tt = T("T: hot centre,\ncool edges (cycled)", 18, MUTED).next_to(temp, DOWN, buff=0.1)
        self.play(FadeIn(temp), FadeIn(tt), run_time=0.8)
        tr1, tr2 = ValueTracker(0), ValueTracker(0)
        a1 = FrameSeq(frames("tm_altpl_vm"), tr1, height=4.3).move_to(LEFT * 2.35 + UP * 0.6)
        a2 = FrameSeq(frames("tm_ratchet_vm"), tr2, height=4.3).move_to(RIGHT * 0.75 + UP * 0.6)
        h1 = T("low tension  X = 0.25", 20, C_AP, weight=BOLD).next_to(a1, UP, buff=0.1)
        h2 = T("double tension  X = 0.5", 20, C_RT, weight=BOLD).next_to(a2, UP, buff=0.1)
        self.play(FadeIn(a1), FadeIn(a2), FadeIn(h1), FadeIn(h2), run_time=0.8)
        self.add(tr1, tr2)
        # displacement vs cycle plot
        ax = Axes(x_range=[0, 12, 2], y_range=[0, 400, 100], x_length=4.0, y_length=3.4,
                  axis_config={"color": GRID, "stroke_width": 2, "include_ticks": True, "tick_size": 0.05}, tips=False).move_to(RIGHT * 4.55 + UP * 0.3)
        xt = VGroup(*[T(str(v), 16, MUTED).next_to(ax.c2p(v, 0), DOWN, buff=0.08) for v in [0, 4, 8, 12]])
        yt = VGroup(*[T(str(v), 16, MUTED).next_to(ax.c2p(0, v), LEFT, buff=0.08) for v in [100, 200, 300, 400]])
        xl = T("cycle", 18, MUTED).next_to(xt, DOWN, buff=0.05)
        yl = T("plate end displacement [µm]", 18, MUTED).next_to(ax.c2p(0, 400), UP, buff=0.1).align_to(ax, LEFT)
        self.play(Create(ax), FadeIn(xt), FadeIn(yt), FadeIn(xl), FadeIn(yl), run_time=0.8)
        curves = []
        for case, col in [("tm_altpl", C_AP), ("tm_ratchet", C_RT)]:
            d = load_npz(f"plate_{case}.npz")
            eoc = d["T_uy_top"][d["T_end_of_cycle"]] * 1000
            cyc = np.arange(1, len(eoc) + 1)
            pre = d["T_uy_top"][9] * 1000
            pts = [ax.c2p(0, pre)] + [ax.c2p(c_, v) for c_, v in zip(cyc, eoc)]
            curves.append(VMobject().set_points_as_corners(pts).set_stroke(col, 4))
        self.play(tr1.animate.set_value(119), tr2.animate.set_value(119), Create(curves[0]), Create(curves[1]),
                  run_time=self.until("h", 0.75), rate_func=linear)
        r1 = T("+22 µm every cycle", 22, C_RT, weight=BOLD).next_to(ax.c2p(7, 300), UP, buff=0.1)
        r0 = T("stops changing", 20, C_AP, weight=BOLD).next_to(ax.c2p(8, 62), UP, buff=0.1)
        self.play(FadeIn(r1), FadeIn(r0), run_time=0.8)
        self.wait_until(self.end("h") - 0.2)
        # ---- i: elastic core
        self.cue("i")
        c1 = img(frames("tm_altpl_core")[0], height=4.3).move_to(a1)
        c2 = img(frames("tm_ratchet_core")[0], height=4.3).move_to(a2)
        a1.clear_updaters(); a2.clear_updaters()
        self.play(FadeOut(a1), FadeOut(a2), FadeIn(c1), FadeIn(c2), run_time=1.0)
        leg = VGroup(VGroup(Square(0.25, fill_color=CYAN, fill_opacity=1, stroke_width=0), T("no plastic flow during the cycle", 18, TXT)).arrange(RIGHT, buff=0.12),
                     VGroup(Square(0.25, fill_color="#f0605d", fill_opacity=1, stroke_width=0), T("plastic flow during the cycle", 18, TXT)).arrange(RIGHT, buff=0.12)
                     ).arrange(DOWN, aligned_edge=LEFT, buff=0.1).move_to(LEFT * 0.8 + DOWN * 2.45)
        y1 = T("elastic core ✓", 26, CYAN, weight=BOLD).next_to(c1, DOWN, buff=0.1)
        y2 = T("no elastic core ✗", 26, RED, weight=BOLD).next_to(c2, DOWN, buff=0.1)
        self.play(FadeIn(leg), run_time=0.6)
        self.play(FadeIn(y1, scale=1.2), run_time=0.6)
        self.wait(1.5)
        self.play(FadeIn(y2, scale=1.2), run_time=0.6)
        self.wait_until(self.end("i") - 0.2)

    # ------------------------------------------------------------------ j
    def part_material(self):
        self.cue("j")
        self.clear()
        U = load_npz("uniaxial_studies.npz")
        spec = [("prager", "linear kinematic", CYAN), ("af", "Armstrong–Frederick", RED), ("chaboche", "Chaboche (3 terms)", AMBER)]
        head = T("material ratcheting: stress control, σm = 60 MPa, σa = 300 MPa", 26, TXT, weight=BOLD).to_edge(UP, buff=0.85)
        self.play(FadeIn(head), run_time=0.6)
        groups, curves, finals = [], [], []
        for k, (key, name, col) in enumerate(spec):
            e, s = U[f"rat_{key}_eps"] * 100, U[f"rat_{key}_sig"]
            ax = Axes(x_range=[-0.4, 2.2, 0.5], y_range=[-420, 420, 210], x_length=3.9, y_length=3.6,
                      axis_config={"color": GRID, "stroke_width": 2, "include_ticks": False}, tips=False).move_to([-4.6 + 4.6 * k, -0.2, 0])
            t = T(name, 24, col, weight=BOLD).next_to(ax, UP, buff=0.2)
            xl = T("strain −0.4 … 2.2 %", 16, MUTED).next_to(ax, DOWN, buff=0.08)
            lp = VMobject().set_points_as_corners([ax.c2p(a, b) for a, b in zip(e, s)]).set_stroke(col, 2.2)
            fin = T(f"after 15 cycles: {e[-1]:.2f} %", 22, col, weight=BOLD).next_to(xl, DOWN, buff=0.2)
            groups.append(VGroup(ax, t, xl)); curves.append(lp); finals.append(fin)
        self.play(*[FadeIn(g) for g in groups], run_time=0.8)
        self.play(*[Create(c) for c in curves], run_time=self.until("j", 0.62), rate_func=linear)
        self.play(*[FadeIn(f) for f in finals], run_time=0.8)
        msg = T("if ratcheting matters: calibrate against ratcheting tests, not just a stress–strain curve", 22, GREEN, weight=BOLD).to_edge(DOWN, buff=0.45)
        self.wait_until(self.start("j") + self.dur("j") * 0.82)
        self.play(FadeIn(msg, shift=UP * 0.1), run_time=0.8)
        self.wait_until(self.end("j") - 0.2)

    # ------------------------------------------------------------------ k, l, m
    def part_practice(self):
        self.cue("k")
        self.clear()
        head = T("assessing accumulated plastic strain in practice", 32, TXT, weight=BOLD).to_edge(UP, buff=0.85)
        self.play(FadeIn(head), run_time=0.6)
        def step(n, title, lines, col):
            num = Circle(radius=0.3, color=col, stroke_width=3).set_fill(col, 0.15)
            nt = T(str(n), 24, col, weight=BOLD).move_to(num)
            body = VGroup(T(title, 26, col, weight=BOLD), *[T(l, 21, TXT) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
            return VGroup(VGroup(num, nt), body).arrange(RIGHT, buff=0.3, aligned_edge=UP)
        s1 = step(1, "run enough cycles", ["ASME VIII-2: at least 3 complete cycles", "Eurocode 3-1-6: use the increment after the 3rd cycle"], CYAN)
        s2 = step(2, "separate the response", ["net plastic strain per cycle  →  ratcheting", "plastic strain range in the cycle  →  low-cycle fatigue",
                                               "change of key dimensions per cycle"], GREEN)
        VGroup(s1, s2).arrange(DOWN, aligned_edge=LEFT, buff=0.6).move_to(DOWN * 0.3 + LEFT * 0.5)
        self.play(FadeIn(s1, shift=RIGHT * 0.2), run_time=0.8)
        self.wait_until(self.start("k") + self.dur("k") * 0.5)
        self.play(FadeIn(s2, shift=RIGHT * 0.2), run_time=0.8)
        self.wait_until(self.end("k") - 0.2)
        # ---- l: acceptance criteria
        self.cue("l")
        self.clear(keep=(head,))
        nh = T("3 · acceptance criteria", 30, AMBER, weight=BOLD).to_edge(UP, buff=0.85)
        self.play(Transform(head, nh), run_time=0.6)
        def crit(title, col, items, w=6.5):
            t = T(title, 20, col, weight=BOLD)
            body = VGroup(*items).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
            g = VGroup(t, body).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
            if g.width > w - 0.4:
                g.scale((w - 0.4) / g.width)
            b = card(w, g.height + 0.4).move_to(g)
            b.set_stroke(col, 1.5)
            return VGroup(b, g)
        c1 = crit("ASME VIII-2 · elastic-plastic ratcheting", CYAN,
                  [T("EPP model, ≥ 3 cycles — pass if ONE holds:", 18, MUTED), T("a) no plastic action", 19, TXT),
                   T("b) elastic core in the primary-load-bearing boundary", 19, TXT),
                   T("c) no permanent change in overall dimensions", 19, TXT)])
        c2 = crit("EN 13445-3 Annex B · progressive deformation", GREEN,
                  [T("shakedown must be shown, e.g. with Melan's theorem", 19, TXT)])
        c3 = crit("Eurocode 3 Part 1-6 · LS2 cyclic plasticity", AMBER,
                  [M(r"\varepsilon_{p,eq,Ed}\le 25\,\frac{f_y}{E}\approx 4.2\,\%\;(\mathrm{S355})", 28, TXT),
                   M(r"\varepsilon_{p,eq,Ed}\approx n_{cyc}\,\Delta\varepsilon_{p,eq}\;(\text{after 3rd cycle})", 24, MUTED)])
        c4 = crit("ASME VIII-2 · local failure (strain limit)", RED,
                  [M(r"\varepsilon_{peq}+\varepsilon_{cf}\le\varepsilon_L=\varepsilon_{Lu}\,e^{-\frac{\alpha_{sl}}{1+m_2}\left(\frac{\sigma_1+\sigma_2+\sigma_3}{3\sigma_e}-\frac{1}{3}\right)}", 26, TXT),
                   M(r"\text{load sequences: }D_\varepsilon=\sum_k \Delta\varepsilon_{peq,k}/\varepsilon_{L,k}\le 1", 24, MUTED)])
        left = VGroup(c1, c2).arrange(DOWN, buff=0.3)
        right = VGroup(c3, c4).arrange(DOWN, buff=0.3)
        VGroup(left, right).arrange(RIGHT, buff=0.3, aligned_edge=UP).move_to(DOWN * 0.45)
        sched = [c1, c2, c3, c4]
        fr = [0.02, 0.36, 0.5, 0.74]
        for c, f in zip(sched, fr):
            self.wait_until(self.start("l") + self.dur("l") * f)
            self.play(FadeIn(c, shift=UP * 0.15), run_time=0.8)
        self.wait_until(self.end("l") - 0.2)
        # ---- m: damage
        self.cue("m")
        self.clear(keep=(head,))
        nh = T("4 · damage", 30, AMBER, weight=BOLD).to_edge(UP, buff=0.85)
        self.play(Transform(head, nh), run_time=0.6)
        a = VGroup(T("alternating plasticity", 26, C_AP, weight=BOLD),
                   M(r"D=D_{LCF}\big(\Delta\varepsilon\ \text{of stabilised loop}\big)+D_{HCF}\le 1", 34, TXT)).arrange(DOWN, buff=0.2)
        b = VGroup(T("ratcheting", 26, C_RT, weight=BOLD),
                   M(r"D=D_{fatigue}+\frac{\varepsilon_{ratchet}}{\varepsilon_{f}}\quad(\text{ductility exhaustion})", 34, TXT),
                   T("in design codes: continued ratcheting is generally not acceptable", 22, RED)).arrange(DOWN, buff=0.2)
        VGroup(a, b).arrange(DOWN, buff=0.8).move_to(DOWN * 0.4)
        self.play(FadeIn(a, shift=UP * 0.15), run_time=1.0)
        self.wait_until(self.start("m") + self.dur("m") * 0.4)
        self.play(FadeIn(b[:2], shift=UP * 0.15), run_time=1.0)
        self.wait_until(self.start("m") + self.dur("m") * 0.78)
        self.play(FadeIn(b[2]), run_time=0.6)
        self.wait_until(self.end("m") - 0.2)

    # ------------------------------------------------------------------ n
    def part_answer(self):
        self.cue("n")
        self.clear()
        head = T("Is accumulated plastic strain a problem?", 36, TXT, weight=BOLD).to_edge(UP, buff=0.85)
        self.play(FadeIn(head), run_time=0.8)
        rows = [("PEEQ stops growing", "shakedown", "back to HCF — with the right local mean stress", C_SD, 1),
                ("PEEQ grows, closed cycle", "alternating plasticity", "LCF — governed by the plastic strain RANGE", C_AP, 2),
                ("PEEQ grows, strain drifts", "ratcheting", "design it out", C_RT, 3)]
        grp = VGroup()
        for cond, regime, verdict, col, k in rows:
            ttl, colr, spark = self.resp[k]
            sp = spark.copy().scale(0.75)
            c1 = VGroup(sp, T(cond, 24, TXT)).arrange(RIGHT, buff=0.3)
            arr = Arrow(LEFT * 0.4, RIGHT * 0.4, color=col, stroke_width=4, buff=0)
            c2 = VGroup(T(regime.upper(), 24, col, weight=BOLD), T(verdict, 22, TXT)).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
            grp.add(VGroup(c1, arr, c2).arrange(RIGHT, buff=0.35))
        grp.arrange(DOWN, aligned_edge=LEFT, buff=0.6).move_to(DOWN * 0.3)
        fr = [0.05, 0.35, 0.68]
        for g, f in zip(grp, fr):
            self.wait_until(self.start("n") + self.dur("n") * f)
            self.play(FadeIn(g, shift=RIGHT * 0.2), run_time=0.9)
        self.wait_until(self.end("n") - 0.3)
