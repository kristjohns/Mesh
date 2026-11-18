"""Case 1 (plate with a hole: limit load) and case 2 (plastic hinge: shape factor, twice-elastic-slope)."""
import numpy as np
from manim import *  # noqa: F401,F403

from ycommon import (BG, C_ASME, C_BAD, C_EPP, C_FRONT, C_GOOD, C_THEORY, C_TRUE, C_VM, C_X, C_YIELD, C_Z, DIM, FAINT,
                     INK, PANEL, ImageSeq, M, NScene, T, ax_labels, axes, case_card, case_header, data_curve,
                     field_legend, follow, frame_index, grow_with, hline, load_json, panel, strike, tick_mark, ticks,
                     vline)


class Y03_Plate(NScene):
    def construct(self):
        c1 = load_json("fe", "case1.json")
        P = np.array(c1["curves"]["epp"]["P"]); D = np.array(c1["curves"]["epp"]["d"])
        n = len(P)
        fidx = frame_index(c1["frame_keys"])
        Py_el, Plim = c1["P_first_yield_elastic"], c1["P_limit_fe"]
        case_card(self, 1, "Plate with a hole", "limit-load analysis")
        hdr = case_header(1, "Plate with a hole in tension", "plane stress  ·  S355  ·  elastic–perfectly plastic")
        # geometry in image coordinates (window -105..105 x -78.75..78.75 mm)
        IH = 5.0
        IW = IH * 4 / 3
        IC = np.array([-3.45, -0.4, 0.0])
        s = IW / 210.0
        mm = lambda x, y: IC + np.array([x * s, y * s, 0.0])
        plate = Rectangle(width=200 * s, height=157.5 * s, stroke_width=0, fill_color="#1A2436", fill_opacity=1).move_to(IC)
        edges = VGroup(Line(mm(-100, -78.75), mm(-100, 78.75)), Line(mm(100, -78.75), mm(100, 78.75))).set_stroke(INK, 2.5)
        hole = Circle(radius=30 * s, stroke_color=INK, stroke_width=2.5, fill_color=BG, fill_opacity=1).move_to(IC)
        arrows = VGroup(*[Arrow(mm(x, 66), mm(x, 92), buff=0, color=C_X, stroke_width=4, max_tip_length_to_length_ratio=0.35)
                          for x in (-80, -40, 0, 40, 80)],
                        *[Arrow(mm(x, -66), mm(x, -92), buff=0, color=C_X, stroke_width=4, max_tip_length_to_length_ratio=0.35)
                          for x in (-80, -40, 0, 40, 80)])
        dimW = VGroup(DoubleArrow(mm(-100, -52), mm(100, -52), buff=0, color=DIM, stroke_width=2, tip_length=0.15),
                      T("W = 200 mm", 20, INK).move_to(mm(52, -60)))
        dimd = VGroup(DoubleArrow(mm(-30, 0), mm(30, 0), buff=0, color=DIM, stroke_width=2, tip_length=0.15),
                      T("d = 60 mm", 20, INK).next_to(mm(0, 0), UP, buff=0.12))
        info = VGroup(T("t = 20 mm", 20, INK), T("S355:  σY = 355 MPa", 20, INK)).arrange(DOWN, buff=0.08, aligned_edge=LEFT)
        info.move_to(mm(-48, 56))
        schem = VGroup(plate, edges, hole, arrows, dimW, dimd, info)
        # right-hand formulas
        f1 = VGroup(M(r"K_{t,net}=\frac{\sigma_{\max}}{\sigma_{net}}=2.36", size=38),
                    T("linear elastic FE", 19, DIM)).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
        f2 = VGroup(M(r"P_Y=\frac{\sigma_Y\,(W-d)\,t}{K_{t,net}}=421\ \mathrm{kN}", size=38),
                    T("load at first yield", 19, DIM)).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
        fg = VGroup(f1, f2).arrange(DOWN, buff=0.45, aligned_edge=LEFT).move_to(RIGHT * 3.7 + UP * 0.3)
        # plot
        ax = axes((0, 1.2), (0, 1200), 5.2, 3.8, 0.2, 200).move_to(RIGHT * 3.95 + DOWN * 0.75)
        tk = ticks(ax, [0, 0.4, 0.8, 1.2], [0, 400, 800, 1200], size=17)
        lb = ax_labels(ax, "end displacement [mm]", "load P [kN]", size=20)
        k = ValueTracker(0.0)
        full = data_curve(ax, D, P, C_EPP, width=4.5)
        img = ImageSeq("case1", IH, index_fn=lambda: fidx(k.get_value()))
        img.move_to(IC)
        frame = SurroundingRectangle(img, buff=0, stroke_color=FAINT, stroke_width=1.5)
        leg = field_legend(width=1.8, size=17).next_to(img, DOWN, buff=0.22)

        with self.say("p1") as d:
            self.play(FadeIn(hdr), run_time=0.6)
            self.play(FadeIn(plate), Create(edges), DrawBorderThenFill(hole), run_time=1.0)
            self.play(LaggedStart(*[GrowArrow(a_) for a_ in arrows], lag_ratio=0.05), run_time=0.8)
            self.play(FadeIn(dimW), FadeIn(dimd), FadeIn(info), run_time=0.8)
            self.until("p1", "The stress concentration")
            self.play(FadeIn(f1, shift=0.1 * UP), run_time=0.8)
            self.until("p1", "so the edge")
            self.play(FadeIn(f2, shift=0.1 * UP), run_time=0.8)
            self.wait(max(0.1, self.left() - 2.2))
            self.play(FadeOut(schem), FadeIn(img), FadeIn(frame), FadeIn(leg),
                      fg.animate.scale(0.62).move_to(RIGHT * 3.9 + UP * 2.62), run_time=1.0)
            curve = grow_with(full, k, n)
            dot = follow(ax, D, P, k, color=INK)
            self.play(Create(ax), FadeIn(tk), FadeIn(lb), run_time=0.8)
            self.add(curve, dot)
        ky = float(np.interp(Py_el, P, np.arange(n)))
        with self.say("p2") as d:
            self.play(k.animate.set_value(ky), run_time=1.4, rate_func=linear)
            fy = Dot(ax.c2p(float(np.interp(ky, np.arange(n), D)), Py_el), color=C_YIELD, radius=0.08)
            fyl = T("first yield, 421 kN", 19, C_YIELD).next_to(fy, RIGHT, buff=0.15).shift(DOWN * 0.1)
            self.play(FadeIn(fy, scale=1.4), FadeIn(fyl), run_time=0.5)
            k_pl = float(np.argmax(P > 0.985 * Plim))
            self.play(k.animate.set_value(k_pl), run_time=max(1.0, self.till("p2", "Only when")), rate_func=linear)
            self.play(k.animate.set_value(n - 1), run_time=max(1.0, self.till("p2", "the limit load") - 0.2), rate_func=linear)
            lim = hline(ax, 994.0, C_YIELD, width=2.2)
            liml = VGroup(T("limit load: FE 996 kN", 20, INK, weight=BOLD),
                          M(r"\sigma_Y\,(W-d)\,t=994\ \mathrm{kN}", size=30, color=C_YIELD)).arrange(DOWN, buff=0.08, aligned_edge=RIGHT)
            liml.next_to(ax.c2p(1.2, 994), DOWN, buff=0.15).align_to(ax.c2p(1.2, 0), RIGHT)
            self.play(Create(lim), FadeIn(liml), run_time=0.9)
        with self.say("p3") as d:
            br = BraceBetweenPoints(ax.c2p(0, 0), ax.c2p(0, Py_el), direction=LEFT, color=C_YIELD).shift(LEFT * 0.55)
            brt = VGroup(T("42 %", 22, C_YIELD, weight=BOLD), T("of the", 17, C_YIELD), T("limit load", 17, C_YIELD)
                         ).arrange(DOWN, buff=0.04).next_to(br, LEFT, buff=0.1)
            self.play(GrowFromCenter(br), FadeIn(brt), run_time=0.8)
            self.until("p3", "The criterion")
            crit = panel("LIMIT-LOAD ANALYSIS  ·  ASME VIII-2 §5.2.3",
                         ["elastic–perfectly plastic, yield stress σy = 1.5 S", "small-displacement theory",
                          "loads factored by 1.5 (P + Ps + D)", "pass: the solution converges"],
                         color=C_ASME, size=21, width=6.7, buff=0.12)
            crit.move_to(np.array([-3.55, 1.5, 0]))
            self.play(FadeOut(img), FadeOut(frame), FadeOut(leg), FadeOut(fg), FadeIn(crit.box), FadeIn(crit.title), run_time=0.9)
            phr = ["elastic, perfectly plastic", "yield stress of 1.5", "1.5 times the design", "requires a converged"]
            for rr, ph in zip(crit.body, phr):
                self.until("p3", ph)
                self.play(FadeIn(rr, shift=0.1 * RIGHT), run_time=0.45)
        img.clear_updaters()
        with self.say("p4") as d:
            calc = VGroup(
                M(r"S=\min\!\Big(\tfrac{470}{2.4},\tfrac{355}{1.5}\Big)=195.8\ \mathrm{MPa},\quad 1.5S=293.8\ \mathrm{MPa}", size=28),
                M(r"P_{lim}(1.5S)=996\times\tfrac{293.8}{355}=824\ \mathrm{kN}", size=30),
                M(r"P_{design}\le 824/1.5=549\ \mathrm{kN}", size=32, color=C_GOOD),
                M(r"\sigma_{\max,el}=2.36\times\tfrac{549\,000}{2800}=463\ \mathrm{MPa}\;>\;\sigma_Y", size=30),
            ).arrange(DOWN, buff=0.17, aligned_edge=LEFT)
            calc.next_to(crit, DOWN, buff=0.3).align_to(crit, LEFT).shift(RIGHT * 0.1)
            note = T("S355 values, for illustration", 16, DIM).next_to(calc, DOWN, buff=0.12).align_to(calc, LEFT)
            if calc.width > 6.7:
                VGroup(calc, note).scale_to_fit_width(6.7).align_to(crit, LEFT).shift(RIGHT * 0.1)
            self.play(FadeIn(calc[0]), FadeIn(note), run_time=0.7)
            self.play(FadeIn(calc[1]), run_time=0.6)
            scaled = data_curve(ax, D, P * 293.8 / 355.0, C_ASME, width=3, dashed=True)
            l824 = hline(ax, 824.0, C_ASME, width=1.8)
            l549 = hline(ax, 549.0, C_GOOD, width=2.2)
            t549 = T("design load 549 kN", 19, C_GOOD).next_to(ax.c2p(1.2, 549), DOWN, buff=0.1).align_to(ax.c2p(1.2, 0), RIGHT)
            t824 = T("EPP with σy = 1.5 S: 824 kN", 18, C_ASME).next_to(ax.c2p(1.2, 824), DOWN, buff=0.1).align_to(ax.c2p(1.2, 0), RIGHT)
            self.play(FadeOut(br), FadeOut(brt), FadeOut(liml[1]), Create(scaled), FadeIn(t824), run_time=0.9)
            self.until("p4", "permits a design load")
            self.play(FadeIn(calc[2]), Create(l549), FadeIn(t549), run_time=0.8)
            self.until("p4", "where the elastic peak")
            self.play(FadeIn(calc[3]), run_time=0.8)
            self.until("p4", "acceptable against")
            ok = VGroup(tick_mark(C_GOOD, 0.3), T("accepted: no plastic collapse", 21, C_GOOD, weight=BOLD)).arrange(RIGHT, buff=0.15)
            ok.next_to(note, DOWN, buff=0.3).align_to(calc, LEFT)
            self.play(FadeIn(ok), run_time=0.6)
            self.until("p4", "It is the same answer")
            same = M(r"\frac{P}{(W-d)\,t}=\frac{549\,000}{2800}=196\ \mathrm{MPa}=S", size=34, color=C_ASME)
            same_t = T("= the classical rule  Pm ≤ S", 20, C_ASME)
            sg = VGroup(same, same_t).arrange(DOWN, buff=0.1)
            sg.move_to(np.array([3.95, 2.35, 0]))
            self.play(FadeIn(sg, shift=0.1 * UP), run_time=0.9)
            self.until("p4", "The peak at the hole")
            self.play(Indicate(calc[3], color=C_YIELD, scale_factor=1.04), run_time=1.0)
        self.wait(0.6)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.8)


class Y04_Beam(NScene):
    def construct(self):
        c2 = load_json("fe", "case2.json")
        Me = np.array(c2["curves"]["epp"]["M"]); th = np.array(c2["curves"]["epp"]["th"]) * 1e3
        Mt = np.array(c2["curves"]["true"]["M"]); tht = np.array(c2["curves"]["true"]["th"]) * 1e3
        Man = np.array(c2["M_analytic"])
        n = len(Me)
        fidx = frame_index(c2["frame_keys"])
        My, Mp = c2["M_y"], c2["M_p"]
        kel = c2["tes_true"][2] / 1e3               # kN m per mrad
        Mtes, thtes = c2["tes_true"][0], c2["tes_true"][1] * 1e3
        case_card(self, 2, "Plastic hinge", "shape factor · twice-elastic-slope collapse load")
        hdr = case_header(2, "Plastic hinge in a rectangular beam", "constant moment  ·  S355  ·  100 × 50 mm section")
        IH = 3.6
        IW = IH * 1920 / 1008
        IC = np.array([-3.35, 0.65, 0.0])
        s = IW / 312.0
        mm = lambda x, y: IC + np.array([(x - 150) * s, y * s, 0.0])
        beam = Rectangle(width=300 * s, height=100 * s, stroke_color=INK, stroke_width=2.5, fill_color="#1A2436", fill_opacity=1).move_to(mm(150, 0))
        wall = VGroup(*[Line(mm(-2, y), mm(-12, y - 10), color=DIM, stroke_width=2) for y in np.linspace(-45, 55, 6)])
        rot = Line(mm(300 + 8, -58), mm(300 - 8, 58), color=C_YIELD, stroke_width=4)
        arc = CurvedArrow(mm(312, 40), mm(300, 62), color=C_YIELD, angle=-PI / 2.5, stroke_width=3)
        thl = M(r"\theta", size=34, color=C_YIELD).next_to(arc, RIGHT, buff=0.08)
        Ml = VGroup(M(r"M", size=34), T("constant along the span", 19, DIM)).arrange(RIGHT, buff=0.15).next_to(beam, DOWN, buff=0.25)
        secg = VGroup(Rectangle(width=0.5, height=1.0, stroke_color=INK, stroke_width=2, fill_color="#1A2436", fill_opacity=1),
                      T("b = 50", 17, INK), T("h = 100 mm", 17, INK))
        secg[1].next_to(secg[0], DOWN, buff=0.08); secg[2].next_to(secg[0], RIGHT, buff=0.1)
        secg.next_to(beam, DOWN, buff=0.25).align_to(beam, RIGHT).shift(LEFT * 0.6)
        schem = VGroup(beam, wall, rot, arc, thl, Ml, secg)
        k = ValueTracker(0.0)
        img = ImageSeq("case2", IH, index_fn=lambda: fidx(k.get_value()))
        img.move_to(IC)
        leg = field_legend(width=1.8, size=17).next_to(img, DOWN, buff=0.3)
        ax = axes((0, 120), (0, 50), 5.3, 4.4, 30, 10).move_to(RIGHT * 3.95 + DOWN * 0.35)
        tk = ticks(ax, [0, 30, 60, 90, 120], [0, 10, 20, 30, 40, 50], size=17)
        lb = ax_labels(ax, "end rotation θ [mrad]", "moment M [kN·m]", size=20)
        full = data_curve(ax, th, Me, C_EPP, width=4.5)
        with self.say("b1") as d:
            self.play(FadeIn(hdr), run_time=0.6)
            self.play(FadeIn(beam), FadeIn(wall), run_time=0.8)
            self.play(Create(rot), Create(arc), FadeIn(thl), FadeIn(Ml), FadeIn(secg), run_time=1.0)
            self.until("b1", "The outer fibres")
            self.play(FadeOut(schem), FadeIn(img), FadeIn(leg), Create(ax), FadeIn(tk), FadeIn(lb), run_time=1.0)
            curve = grow_with(full, k, n)
            dot = follow(ax, th, Me, k, color=INK)
            self.add(curve, dot)
            ky = float(np.interp(My, Me, np.arange(n)))
            self.play(k.animate.set_value(ky), run_time=self.till("b1", "29.6") + 0.5, rate_func=linear)
            lmy = hline(ax, My, C_YIELD, width=2)
            tmy = M(r"M_Y=\sigma_Y\,\tfrac{bh^2}{6}=29.6", size=28, color=C_YIELD).next_to(ax.c2p(120, My), DOWN, buff=0.12).align_to(ax.c2p(120, 0), RIGHT)
            self.play(Create(lmy), FadeIn(tmy), run_time=0.7)
            self.until("b1", "Plasticity then spreads")
            self.play(k.animate.set_value(45), run_time=max(0.8, self.left() - 0.2), rate_func=linear)
        with self.say("b2") as d:
            self.play(k.animate.set_value(n - 1), run_time=self.till("b2", "one and a half"), rate_func=linear)
            lmp = hline(ax, Mp, C_VM, width=2)
            tmp = M(r"M_p=\sigma_Y\,\tfrac{bh^2}{4}=44.4", size=28, color=C_VM).next_to(ax.c2p(120, Mp), UP, buff=0.12).align_to(ax.c2p(120, 0), RIGHT)
            self.play(Create(lmp), FadeIn(tmp), run_time=0.7)
            sf = VGroup(T("shape factor", 20, DIM), M(r"\frac{M_p}{M_Y}=1.5", size=38)).arrange(RIGHT, buff=0.2)
            sf.move_to(ax.c2p(75, 15))
            self.play(FadeIn(sf), run_time=0.7)
            self.until("b2", "The finite element curve")
            an = data_curve(ax, th, Man, C_THEORY, width=2.5, dashed=True)
            anl = VGroup(VGroup(Line(ORIGIN, RIGHT * 0.45, color=C_EPP, stroke_width=4), T("FE, elastic–perfectly plastic", 18, INK)).arrange(RIGHT, buff=0.12),
                         VGroup(DashedLine(ORIGIN, RIGHT * 0.45, color=C_THEORY, stroke_width=2.5), T("closed form (max. diff. 0.02 % of Mp)", 18, INK)).arrange(RIGHT, buff=0.12)
                         ).arrange(DOWN, buff=0.1, aligned_edge=LEFT).move_to(ax.c2p(82, 21))
            anl.align_to(ax.c2p(118, 0), RIGHT)
            self.play(Create(an), FadeOut(sf), FadeIn(anl), run_time=1.2)

        with self.say("b3") as d:
            tcur = data_curve(ax, tht, Mt, C_TRUE, width=4)
            tl = VGroup(Line(ORIGIN, RIGHT * 0.45, color=C_TRUE, stroke_width=4), T("FE, true stress–strain curve", 18, INK)).arrange(RIGHT, buff=0.12)
            tl.next_to(anl, DOWN, buff=0.1, aligned_edge=LEFT)
            self.play(Create(tcur), FadeIn(tl), run_time=1.4)
            self.until("b3", "The twice-elastic-slope")
            el = Line(ax.c2p(0, 0), ax.c2p(48 / kel, 48), color=INK, stroke_width=2.5)
            elt = VGroup(Line(ORIGIN, RIGHT * 0.45, color=INK, stroke_width=2.5), T("elastic slope k", 18, INK)).arrange(RIGHT, buff=0.12)
            elt.next_to(tl, DOWN, buff=0.1, aligned_edge=LEFT)
            self.play(Create(el), FadeIn(elt), run_time=0.8)
            self.until("b3", "draw a line")
            tes = Line(ax.c2p(0, 0), ax.c2p(2 * 48 / kel, 48), color=C_ASME, stroke_width=3.5)
            tesl = VGroup(Line(ORIGIN, RIGHT * 0.45, color=C_ASME, stroke_width=3.5), T("TES line, slope k/2", 18, C_ASME)).arrange(RIGHT, buff=0.12)
            tesl.next_to(elt, DOWN, buff=0.1, aligned_edge=LEFT)
            self.play(Create(tes), FadeIn(tesl), run_time=1.0)
            self.until("b3", "It cuts the curve")
            pt = Dot(ax.c2p(thtes, Mtes), color=C_ASME, radius=0.09)
            ptl = VGroup(M(r"M_{TES}=", size=30, color=C_ASME), T("43.0 kN·m", 24, C_ASME, weight=BOLD)).arrange(RIGHT, buff=0.1)
            ptl.next_to(pt, RIGHT, buff=0.25).shift(DOWN * 0.45)
            self.play(FadeIn(pt, scale=1.5), FadeIn(ptl), run_time=0.8)
            self.until("b3", "and the allowable")
            la = hline(ax, Mtes * 2 / 3, C_GOOD, width=2.4)
            lat = VGroup(T("allowable", 19, C_GOOD, weight=BOLD), M(r"\tfrac23\,M_{TES}=28.6", size=28, color=C_GOOD)).arrange(RIGHT, buff=0.12)
            lat.next_to(ax.c2p(120, Mtes * 2 / 3), UP, buff=0.1).align_to(ax.c2p(120, 0), RIGHT)
            self.play(Create(la), FadeIn(lat), FadeOut(tmy), FadeOut(lmy), run_time=0.9)
        img.clear_updaters()
        with self.say("b4") as d:
            body = VGroup(
                M(r"\tfrac23\,M_p=\tfrac23\times1.5\,M_Y=M_Y", size=40),
                T("two-thirds of the plastic moment is first yield", 21, DIM),
                M(r"P_L+P_b\;\le\;1.5\,S", size=44, color=C_ASME),
                T("the elastic-route limit on membrane + bending stress:", 21, DIM),
                T("the 1.5 is the shape factor of a rectangle", 21, DIM),
            ).arrange(DOWN, buff=0.22, aligned_edge=LEFT)
            if body.width > 6.3:
                body.scale_to_fit_width(6.3)
            box = RoundedRectangle(width=6.9, height=body.height + 1.2, corner_radius=0.14, stroke_color=C_ASME, stroke_width=2,
                                   fill_color=PANEL, fill_opacity=0.95)
            ttl = T("WHY TWO-THIRDS", 21, C_ASME, weight=BOLD)
            VGroup(ttl, body).arrange(DOWN, buff=0.3, aligned_edge=LEFT).move_to(box).align_to(box, LEFT).shift(RIGHT * 0.35)
            pg = VGroup(box, ttl, body).move_to(np.array([-3.4, -0.2, 0]))
            self.play(FadeOut(img), FadeOut(leg), FadeIn(box), FadeIn(ttl), run_time=0.8)
            self.play(FadeIn(body[0]), run_time=0.8)
            self.until("b4", "For a rectangle")
            self.play(FadeIn(body[1]), run_time=0.6)
            self.until("b4", "It is also why")
            self.play(FadeIn(body[2], shift=0.1 * UP), run_time=0.8)
            self.play(FadeIn(body[3]), run_time=0.5)
            self.until("b4", "the shape factor")
            self.play(FadeIn(body[4]), run_time=0.6)
            self.until("b4", "Redistribution is already")
            bot = T("Redistribution is already built into the elastic rules.", 24, C_YIELD, weight=BOLD).to_edge(DOWN, buff=0.35)
            self.play(FadeIn(bot, shift=0.1 * UP), run_time=0.8)
        self.wait(0.6)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.8)
