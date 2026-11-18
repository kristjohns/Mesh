"""Case 5 (Bree cylinder: shakedown, alternating plasticity, ratcheting) and the criteria summary."""
import numpy as np
from manim import *  # noqa: F401,F403

from ycommon import (BG, C_ASME, C_BAD, C_EPP, C_FRONT, C_GOOD, C_SHEAR, C_TRESCA, C_TRUE, C_VM, C_X, C_Y, C_YIELD,
                     C_Z, DIM, FAINT, INK, PANEL, M, NScene, T, ax_labels, axes, case_card, case_header, cross_mark,
                     data_curve, hline, load_json, panel, strike, tick_mark, ticks, vline)

C_SD, C_AP, C_RT = C_Z, C_SHEAR, C_BAD          # shakedown, alternating plasticity, ratcheting


class Y07_Bree(NScene):
    def construct(self):
        c5 = load_json("fe", "case5.json")
        runs = c5["runs"]
        case_card(self, 5, "Thermal cycling", "shakedown or ratcheting: cyclic elastic–plastic analysis")
        hdr = case_header(5, "Thin cylinder: constant pressure + cyclic through-wall ΔT",
                          "axisymmetric, open ends  ·  R = 200 mm, t = 10 mm  ·  σY = 355 MPa, elastic–perfectly plastic")
        # ------------------------------------------------------------ r1: wall schematic
        W, H = 1.6, 3.6
        wc = np.array([-4.1, -0.2, 0])
        wall = Rectangle(width=W, height=H, stroke_color=INK, stroke_width=2.5, fill_color="#1A2436", fill_opacity=1).move_to(wc)
        pin = VGroup(*[Arrow(wc + LEFT * (W / 2 + 0.75) + UP * y, wc + LEFT * W / 2 + UP * y, buff=0.03, color=C_X,
                             stroke_width=4, max_tip_length_to_length_ratio=0.35) for y in np.linspace(-1.4, 1.4, 5)])
        pl = VGroup(M(r"p", size=34, color=C_X), T("constant", 17, DIM)).arrange(DOWN, buff=0.04).next_to(pin, LEFT, buff=0.12)
        lab_in = T("inner, hot", 18, C_X).next_to(wall.get_corner(DL), DOWN, buff=0.15).shift(LEFT * 0.2)
        lab_out = T("outer, cold", 18, C_Z).next_to(wall.get_corner(DR), DOWN, buff=0.45).shift(RIGHT * 0.2)
        th = ValueTracker(0.0)
        tprof = always_redraw(lambda: Line(wc + LEFT * W / 2 + UP * (0.9 * th.get_value() * 1.4),
                                           wc + RIGHT * W / 2 + DOWN * (0.9 * th.get_value() * 1.4), color=C_YIELD, stroke_width=4))
        tl = T("temperature", 18, C_YIELD).next_to(wall, UP, buff=0.15)
        wt = T("wall thickness →", 16, DIM).next_to(wall, DOWN, buff=0.85)
        # hoop stress across the wall (Bree idealisation, X = 0.3, Y = 1.4): position horizontal, stress vertical
        o = np.array([0.9, -0.2, 0])
        Wp, Sy_ = 3.0, 1.0                  # plot width; units per sigma_Y
        xs = np.linspace(-1, 1, 81)
        Xs, Ys = 0.3, 1.4
        el_p = lambda x: Xs + Ys * x        # x = -1 inner (hot: thermal compression) ... +1 outer
        P2 = lambda x, sv: o + np.array([x * Wp / 2, sv * Sy_, 0])
        ax_s = VGroup(Line(P2(-1, 0), P2(1, 0), color=DIM, stroke_width=2),
                      Line(P2(-1, -1.35), P2(-1, 1.9), color=DIM, stroke_width=2))
        ysl = VGroup(DashedLine(P2(-1, 1), P2(1, 1), color=C_YIELD, stroke_width=2),
                     DashedLine(P2(-1, -1), P2(1, -1), color=C_YIELD, stroke_width=2))
        yst = VGroup(M(r"+\sigma_Y", size=26, color=C_YIELD).next_to(ysl[0], RIGHT, buff=0.1),
                     M(r"-\sigma_Y", size=26, color=C_YIELD).next_to(ysl[1], RIGHT, buff=0.1))
        wl = T("hoop stress across the wall", 18, DIM).next_to(P2(0, 1.9), UP, buff=0.1)
        pos = VGroup(T("inner", 16, C_X).next_to(P2(-1, -1.35), DOWN, buff=0.1),
                     T("outer", 16, C_Z).next_to(P2(1, -1.35), DOWN, buff=0.1))
        el = VMobject(stroke_color=INK, stroke_width=2.5).set_points_as_corners([P2(x, el_p(x)) for x in xs])
        el = DashedVMobject(el, num_dashes=40)
        elt = T("elastic", 17, INK).next_to(P2(1, el_p(1)), RIGHT, buff=0.1)
        cl = VMobject(stroke_color=C_VM, stroke_width=4).set_points_as_corners([P2(x, np.clip(el_p(x), -1, 1)) for x in xs])
        clt = T("first heat-up: both surfaces yield", 19, C_VM, weight=BOLD).next_to(pos, DOWN, buff=0.2)
        with self.say("r1") as d:
            self.play(FadeIn(hdr), run_time=0.6)
            self.play(FadeIn(wall), LaggedStart(*[GrowArrow(a_) for a_ in pin], lag_ratio=0.1), FadeIn(pl), run_time=1.0)
            self.add(tprof)
            self.play(FadeIn(tl), FadeIn(lab_in), FadeIn(lab_out), FadeIn(wt), run_time=0.5)
            self.until("r1", "that cycles")
            for _ in range(2):
                self.play(th.animate.set_value(1.0), run_time=0.7)
                self.play(th.animate.set_value(0.0), run_time=0.7)
            self.until("r1", "The first heat-up")
            self.play(Create(ax_s), FadeIn(ysl), FadeIn(yst), FadeIn(wl), FadeIn(pos), th.animate.set_value(1.0), run_time=0.8)
            self.play(Create(el), FadeIn(elt), run_time=0.8)
            self.play(Create(cl), FadeIn(clt), run_time=0.9)
        tprof.clear_updaters()
        sch = VGroup(wall, pin, pl, lab_in, lab_out, tprof, tl, wt, ax_s, ysl, yst, wl, pos, el, elt, cl, clt)
        # ------------------------------------------------------------ r1b: Bree diagram
        bx = axes((0, 1.0), (0, 4.0), 4.3, 4.9, 0.25, 1.0).move_to(np.array([-4.15, -0.45, 0]))
        btk = ticks(bx, [0, 0.25, 0.5, 0.75, 1.0], [0, 1, 2, 3, 4], size=17)
        blb = VGroup(VGroup(M(r"X=\frac{pR}{t\,\sigma_Y}", size=30), T("pressure (primary)", 17, DIM)).arrange(DOWN, buff=0.04)
                     .move_to(np.array([0.0, -2.35, 0])),
                     VGroup(M(r"Y=\frac{E\alpha\Delta T}{2(1-\nu)\sigma_Y}", size=30), T("thermal (secondary)", 17, DIM)).arrange(DOWN, buff=0.04)
                     .move_to(np.array([0.0, 1.55, 0])))
        ax_tags = VGroup(M(r"X", size=30).next_to(bx.x_axis.get_end(), RIGHT, buff=0.12),
                         M(r"Y", size=30).next_to(bx.y_axis.get_end(), UP, buff=0.1))
        P_ = lambda pts: [bx.c2p(x, y) for x, y in pts]
        xr = np.linspace(0.25, 0.5, 20)
        reg_E = Polygon(*P_([(0, 0), (1, 0), (0, 1)]), stroke_width=0, fill_color=C_GOOD, fill_opacity=0.22)
        reg_S = Polygon(*P_([(0, 1), (1, 0), (0.5, 2), (0, 2)]), stroke_width=0, fill_color=C_SD, fill_opacity=0.22)
        reg_P = Polygon(*P_([(0, 2), (0.5, 2)] + [(x, 1 / x) for x in xr[::-1]] + [(0, 4)]), stroke_width=0,
                        fill_color=C_AP, fill_opacity=0.18)
        reg_R = Polygon(*P_([(1, 0), (1, 4), (0.25, 4)] + [(x, 1 / x) for x in xr] + [(0.5, 2)]), stroke_width=0,
                        fill_color=C_RT, fill_opacity=0.20)
        bnd = VGroup(Line(*P_([(0, 1), (1, 0)]), color=C_GOOD, stroke_width=3),
                     Line(*P_([(0, 2), (0.5, 2)]), color=INK, stroke_width=2),
                     Line(*P_([(0.5, 2), (1, 0)]), color=C_RT, stroke_width=3),
                     VMobject(stroke_color=C_RT, stroke_width=3).set_points_smoothly(P_([(x, 1 / x) for x in xr])))
        rl = VGroup(T("elastic", 19, C_GOOD, weight=BOLD).move_to(bx.c2p(0.22, 0.3)),
                    T("shakedown", 19, C_SD, weight=BOLD).move_to(bx.c2p(0.25, 1.55)),
                    VGroup(T("alternating", 18, C_AP, weight=BOLD), T("plasticity", 18, C_AP, weight=BOLD)).arrange(DOWN, buff=0.02).move_to(bx.c2p(0.14, 3.2)),
                    T("ratcheting", 19, C_RT, weight=BOLD).move_to(bx.c2p(0.72, 2.9)))
        bnd_t = VGroup(M(r"X+Y=1", size=24, color=C_GOOD).move_to(bx.c2p(0.62, 0.62)),
                       M(r"XY=1", size=24, color=C_RT).move_to(bx.c2p(0.47, 2.62)),
                       M(r"Y=4(1-X)", size=24, color=C_RT).move_to(bx.c2p(0.92, 0.95)))
        cols = dict(shakedown=C_SD, alternating=C_AP, ratchet=C_RT)
        pts = {k_: Dot(bx.c2p(runs[k_]["X"], runs[k_]["Y"]), radius=0.1, color=cols[k_]).set_stroke(INK, 2) for k_ in cols}
        ptl = {k_: M(rf"({runs[k_]['X']:.1f},\,{runs[k_]['Y']:.1f})", size=24, color=INK).next_to(pts[k_], RIGHT, buff=0.1)
               for k_ in cols}
        with self.say("r1b") as d:
            self.play(FadeOut(sch), run_time=0.6)
            self.play(Create(bx), FadeIn(btk), FadeIn(ax_tags), run_time=0.8)
            self.until("r1b", "the pressure stress")
            self.play(FadeIn(blb[0]), run_time=0.6)
            self.until("r1b", "the thermal stress")
            self.play(FadeIn(blb[1]), run_time=0.6)
            self.until("r1b", "Below the line")
            self.play(FadeIn(reg_E), Create(bnd[0]), FadeIn(rl[0]), FadeIn(bnd_t[0]), run_time=0.9)
            self.play(FadeIn(reg_S), FadeIn(reg_P), FadeIn(reg_R), Create(bnd[1:]), FadeIn(rl[1:]), FadeIn(bnd_t[1:]), run_time=1.2)
            self.until("r1b", "Our three analyses")
            self.play(*[FadeIn(pts[k_], scale=1.4) for k_ in cols], *[FadeIn(ptl[k_]) for k_ in cols], run_time=0.9)
        # ------------------------------------------------------------ r2-r4: strain histories
        spec = [("shakedown", "r2", 0.08, [0, 0.04, 0.08], "{:.2f} %"),
                ("alternating", "r3", 0.04, [0, 0.02, 0.04], "{:.2f} %"),
                ("ratchet", "r4", 0.6, [0, 0.3, 0.6], "{:.1f} %")]
        titles = dict(shakedown="shakedown (0.3, 1.4)", alternating="alternating plasticity (0.1, 2.6)",
                      ratchet="ratcheting (0.6, 2.4)")
        ycen = dict(shakedown=1.85, alternating=-0.3, ratchet=-2.45)
        plots = {}
        for name, beat, ymax, yt, fmt in spec:
            rr = runs[name]
            t = np.array(rr["t"]); hoop = np.array(rr["hoop"]) * 100
            x = (t - 1.0) / 2.0
            axp = axes((-1, 10), (0, ymax), 4.9, 1.2, 1, ymax / 2).move_to(np.array([4.45, ycen[name], 0]))
            tkp = ticks(axp, [0, 2, 4, 6, 8, 10], yt, yfmt=fmt, size=15)
            ttl = T(titles[name], 19, cols[name], weight=BOLD).next_to(axp, UP, buff=0.12).align_to(axp, LEFT)
            yl = T("hoop strain", 15, DIM).next_to(axp, UP, buff=0.14).align_to(axp, RIGHT)
            cur = data_curve(axp, np.r_[-0.5, x], np.r_[0.0, hoop], cols[name], width=3.5)
            plots[name] = (axp, tkp, ttl, yl, cur)
        xl = T("load cycles", 17, INK).next_to(plots["ratchet"][0].x_axis.get_end(), DOWN, buff=0.38).align_to(plots["ratchet"][0].x_axis.get_end(), RIGHT)
        notes = dict(
            shakedown=VGroup(T("plastic strain stops at 0.14 %", 16, INK), T("every later cycle elastic", 16, C_GOOD)),
            alternating=VGroup(T("diameter stable; surfaces reverse-yield", 16, INK),
                               T("accumulated plastic strain 0.5 → 3.0 %", 16, C_AP)),
            ratchet=VGroup(T("+0.03 % hoop strain per cycle,", 16, INK), T("no stabilisation", 16, C_RT, weight=BOLD)))
        for k_, g in notes.items():
            g.arrange(DOWN, buff=0.03, aligned_edge=LEFT)
        phr = dict(shakedown="The plastic strain stops", alternating="That is alternating", ratchet="That is")
        for name, beat, *_ in spec:
            axp, tkp, ttl, yl, cur = plots[name]
            with self.say(beat) as d:
                self.play(Indicate(pts[name], scale_factor=1.6, color=cols[name]), FadeIn(axp), FadeIn(tkp), FadeIn(ttl), FadeIn(yl),
                          *([FadeIn(xl)] if name == "ratchet" else []), run_time=0.9)
                self.play(Create(cur), run_time=min(4.0, max(1.5, self.left() * 0.35)), rate_func=linear)
                self.until(beat, phr[name])
                g = notes[name].move_to(axp.c2p(5.2, 0.33 * axp.y_range[1])) if name != "ratchet" else notes[name].move_to(axp.c2p(6.9, 0.25 * axp.y_range[1]))
                self.play(FadeIn(g), run_time=0.6)
                if name == "ratchet":
                    self.until("r4", "The criterion")
                    crit = panel("RATCHETING CHECK  ·  ASME VIII-2 §5.5.7",
                                 ["cyclic elastic–plastic analysis, at least three cycles", "pass if any one holds:",
                                  "  (a) no plastic action (shakedown)", "  (b) an elastic core in the load-bearing section",
                                  "  (c) no permanent change in overall dimensions"], color=C_ASME, size=19, width=6.6, buff=0.12)
                    crit.move_to(np.array([-3.45, -0.2, 0]))
                    bree = VGroup(bx, btk, blb, ax_tags, reg_E, reg_S, reg_P, reg_R, bnd, rl, bnd_t, *pts.values(), *ptl.values())
                    self.play(FadeOut(bree), FadeIn(crit), run_time=0.9)
                    vr = VGroup(T("shakedown: (a) ✓", 18, C_SD), T("alternating plasticity: (b), (c) ✓, then a fatigue check", 18, C_AP),
                                T("ratcheting: fails", 18, C_RT, weight=BOLD)).arrange(DOWN, buff=0.08, aligned_edge=LEFT)
                    vr.next_to(crit, DOWN, buff=0.3).align_to(crit, LEFT)
                    self.play(FadeIn(vr), run_time=0.7)
        self.wait(0.6)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.8)


class Y08_Criteria(NScene):
    def construct(self):
        head = T("The acceptance criteria once yield is allowed", 32, INK, weight=SEMIBOLD).to_corner(UL, buff=0.4)
        cw = [3.05, 4.35, 4.45, 0.75]
        hdrs = ["FAILURE MODE", "ANALYSIS", "ACCEPTANCE", "CASE"]
        data = [("Plastic collapse", "limit load: EPP, σy = 1.5 S", "converges at 1.5 × loads", "1", C_VM),
                ("Plastic collapse", "elastic–plastic: true curve, large displ.", "converges at 2.4 × loads", "3", C_VM),
                ("Plastic collapse", "load–deformation curve (TES)", "load ≤ ⅔ of the TES collapse load", "2", C_VM),
                ("Gross plastic deformation", "EN 13445-3 Annex B, direct route", "principal structural strain ≤ 5 %", "–", C_VM),
                ("Local failure", "elastic–plastic at 1.7 × loads", "εp + εcf ≤ εL, triaxiality-adjusted", "4", C_X),
                ("Ratcheting", "cyclic elastic–plastic", "shakedown, elastic core, or no growth", "5", C_SHEAR)]
        x0 = -6.55

        def mkrow(cells, colors, size=19, weight=NORMAL, h=0.55, fill=PANEL):
            g = VGroup()
            x = x0
            for txt, w, col in zip(cells, cw, colors):
                t = T(txt, size, col, weight=weight)
                if t.width > w - 0.2:
                    t.scale_to_fit_width(w - 0.2)
                t.move_to(np.array([x + 0.12, 0, 0]), aligned_edge=LEFT)
                g.add(t)
                x += w + 0.08
            bg = RoundedRectangle(width=sum(cw) + 0.08 * 3 + 0.2, height=h, corner_radius=0.08, stroke_width=0,
                                  fill_color=fill, fill_opacity=1).move_to(np.array([x0 - 0.1 + (sum(cw) + 0.24 + 0.2) / 2, 0, 0]))
            return VGroup(bg, g)
        hr = mkrow(hdrs, [DIM] * 4, size=17, weight=BOLD, fill=BG)
        rows = VGroup(*[mkrow(r[:4], [r[4], INK, C_ASME, C_YIELD]) for r in data])
        tbl = VGroup(hr, rows)
        hr.move_to(np.array([0, 2.35, 0]), coor_mask=np.array([0, 1, 0]))
        for i, r in enumerate(rows):
            r.move_to(np.array([0, 1.75 - 0.61 * i, 0]), coor_mask=np.array([0, 1, 0]))
        foot = VGroup(T("Fatigue, buckling and fracture: their own procedures.", 19, DIM),
                      T("Serviceability (leak-tightness, distortion) may limit deformation further.", 19, DIM)
                      ).arrange(DOWN, buff=0.06, aligned_edge=LEFT).next_to(rows, DOWN, buff=0.28).align_to(rows, LEFT).shift(RIGHT * 0.1)
        with self.say("s1") as d:
            self.play(FadeIn(head), FadeIn(hr), run_time=0.8)
            for r, ph in zip(rows[:4], ["a converged limit-load", "an elastic-plastic analysis at 2.4", "twice-elastic-slope", "EN 13445"]):
                self.until("s1", ph)
                self.play(FadeIn(r, shift=0.1 * UP), run_time=0.55)
        with self.say("s2") as d:
            for r, ph in zip(rows[4:], ["Against local failure", "Against ratcheting"]):
                self.until("s2", ph)
                self.play(FadeIn(r, shift=0.1 * UP), run_time=0.55)
            self.until("s2", "Fatigue, buckling")
            self.play(FadeIn(foot[0]), run_time=0.6)
            self.until("s2", "and serviceability")
            self.play(FadeIn(foot[1]), run_time=0.6)
        with self.say("s3") as d:
            bad = mkrow(["Yield", "linear elastic", "peak σvm ≤ σY", ""], [C_BAD, DIM, DIM, DIM], size=19, fill="#2A1620")
            bad.next_to(foot, DOWN, buff=0.3).align_to(rows, LEFT)
            st = Line(bad[1][0].get_left() + LEFT * 0.05, bad[1][2].get_right() + RIGHT * 0.1, color=C_BAD, stroke_width=4)
            nl = cross_mark(C_BAD, 0.26, 5).move_to(np.array([x0 + sum(cw[:3]) + 3 * 0.08 + 0.35, bad.get_center()[1], 0]))
            self.play(FadeIn(bad, shift=0.1 * UP), run_time=0.6)
            self.play(Create(st), FadeIn(nl), run_time=0.7)
            self.until("s3", "Yielding is allowed")
            msg = T("Yielding is allowed.  Collapse, rupture, ratcheting and fatigue are not.", 24, C_YIELD, weight=BOLD).to_edge(DOWN, buff=0.25)
            self.play(FadeIn(msg, shift=0.1 * UP), run_time=0.7)
        with self.say("s4") as d:
            self.play(FadeOut(Group(*self.mobjects)), run_time=0.8)
            l1 = T("When the elastic contour turns red,", 40, INK, weight=SEMIBOLD)
            l2 = T("the analysis is not over.", 40, INK, weight=SEMIBOLD)
            l3 = T("Ask which failure mode you are protecting against,", 30, DIM)
            l4 = T("and run the analysis that can see it.", 30, C_YIELD, weight=BOLD)
            g = VGroup(l1, l2, l3, l4).arrange(DOWN, buff=0.28)
            l3.shift(DOWN * 0.25); l4.shift(DOWN * 0.25)
            self.play(FadeIn(l1), FadeIn(l2), run_time=0.9)
            self.until("s4", "Ask which")
            self.play(FadeIn(l3), run_time=0.6)
            self.until("s4", "and run the analysis")
            self.play(FadeIn(l4), run_time=0.6)
        self.wait(1.6)
        self.play(FadeOut(g), run_time=0.8)
        # ------------------------------------------------------------ references
        rt = T("References", 30, INK, weight=SEMIBOLD).to_corner(UL, buff=0.45)
        refs = ["ASME BPVC Section VIII, Division 2, Part 5: Design by Analysis Requirements",
                "EN 13445-3, Annex B: Design by Analysis, Direct Route",
                "DNV-RP-C208: Determination of structural capacity by non-linear FE analysis methods",
                "API TR 17TR8: High-pressure high-temperature design guidelines",
                "J. Bree, J. Strain Analysis 2 (1967) 226–238: thin tubes under pressure and cyclic heat flux",
                "R. Hill, The Mathematical Theory of Plasticity, Oxford (1950)",
                "H. Neuber, J. Appl. Mech. 28 (1961) 544–550",
                "E. A. de Souza Neto, D. Perić, D. R. J. Owen, Computational Methods for Plasticity, Wiley (2008)"]
        rg = VGroup(*[T(r_, 20, INK) for r_ in refs]).arrange(DOWN, buff=0.2, aligned_edge=LEFT).next_to(rt, DOWN, buff=0.4).align_to(rt, LEFT)
        nb = VGroup(T("All results: elastic–plastic FE solver written for this film (6-node triangles, J2 radial return,", 18, DIM),
                    T("consistent tangent), validated against Hill's solution. Material data representative of S355 and a 75 ksi forging.", 18, DIM),
                    T("Code clauses are summarised: check the edition in force before use.", 18, C_YIELD)
                    ).arrange(DOWN, buff=0.06, aligned_edge=LEFT).next_to(rg, DOWN, buff=0.45).align_to(rg, LEFT)
        self.play(FadeIn(rt), LaggedStart(*[FadeIn(r_) for r_ in rg], lag_ratio=0.08), run_time=1.6)
        self.play(FadeIn(nb), run_time=0.8)
        self.wait(7.0)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.2)
