"""How the elastic-plastic analysis works, how the solver was validated, and the code load factors."""
import numpy as np
from manim import *  # noqa: F401,F403

from ycommon import (C_ASME, C_BAD, C_EPP, C_FRONT, C_GOOD, C_THEORY, C_TRUE, C_VM, C_X, C_Y, C_YIELD, C_Z, DIM,
                     FAINT, INK, PANEL, M, NScene, T, ax_labels, axes, cross_mark, data_curve, hline, load_json, panel,
                     tick_mark, ticks, vline)

E = 210000.0


class Y02_Method(NScene):
    def construct(self):
        head = T("How the analysis handles yield", 30, INK, weight=SEMIBOLD).to_corner(UL, buff=0.4)
        # ------------------------------------------------------------ k1: radial return in the pi-plane
        C = np.array([-3.7, -0.45, 0.0])
        R = 2.0
        circ = Circle(radius=R, color=C_YIELD, stroke_width=4).move_to(C)
        circ_t = T("von Mises yield surface", 21, C_YIELD).next_to(circ, DOWN, buff=0.2)
        axs = VGroup()
        for i, ang in enumerate([90, 210, 330]):
            u = np.array([np.cos(np.radians(ang)), np.sin(np.radians(ang)), 0])
            axs.add(DashedLine(C, C + u * 2.9, color=FAINT, stroke_width=2))
            axs.add(M(rf"\sigma'_{i + 1}", size=28, color=DIM).move_to(C + u * 3.2))
        sub = T("deviatoric plane, one Gauss point", 19, DIM).next_to(circ, UP, buff=0.75)
        a_n, a_t = np.radians(75), np.radians(35)
        p_n = C + 1.3 * np.array([np.cos(a_n), np.sin(a_n), 0])
        p_t = C + 2.95 * np.array([np.cos(a_t), np.sin(a_t), 0])
        p_r = C + R * np.array([np.cos(a_t), np.sin(a_t), 0])
        d_n = Dot(p_n, color=INK, radius=0.08)
        l_n = M(r"\boldsymbol\sigma_n", size=34).next_to(d_n, LEFT, buff=0.12)
        ar_t = DashedLine(p_n, p_t, color=INK, stroke_width=3).add_tip(tip_length=0.18)
        d_t = Dot(p_t, color=C_BAD, radius=0.08)
        l_t = M(r"\boldsymbol\sigma^{tr}", size=34, color=C_BAD).next_to(d_t, UR, buff=0.08)
        ar_r = Arrow(p_t, p_r, color=C_VM, buff=0.05, stroke_width=5, max_tip_length_to_length_ratio=0.3)
        d_r = Dot(p_r, color=C_VM, radius=0.09)
        l_r = M(r"\boldsymbol\sigma_{n+1}", size=34, color=C_VM).next_to(d_r, DR, buff=0.06)
        nrm = Arrow(p_r, p_r + 0.85 * (p_r - C) / R, color=C_GOOD, buff=0, stroke_width=5,
                    max_tip_length_to_length_ratio=0.3).shift(0.55 * np.array([-np.sin(a_t), np.cos(a_t), 0]))
        l_nrm = M(r"\Delta\boldsymbol\varepsilon_p\parallel\mathbf n", size=30, color=C_GOOD).next_to(nrm.get_end(), UP, buff=0.08)
        eqs = VGroup(
            VGroup(T("elastic predictor", 20, DIM), M(r"\boldsymbol\sigma^{tr}=\boldsymbol\sigma_n+\mathbb{C}:\Delta\boldsymbol\varepsilon", size=34)),
            VGroup(T("yield check", 20, DIM), M(r"q^{tr}=\sqrt{\tfrac32\,\mathbf s^{tr}\!:\!\mathbf s^{tr}}\;>\;\sigma_Y(\bar\varepsilon_p)\,?", size=34)),
            VGroup(T("radial return", 20, DIM), M(r"\Delta\gamma=\frac{q^{tr}-\sigma_Y}{3G+H},\quad \mathbf s_{n+1}=\Big(1-\frac{3G\,\Delta\gamma}{q^{tr}}\Big)\mathbf s^{tr}", size=32)),
            VGroup(T("plastic flow", 20, DIM), M(r"\Delta\boldsymbol\varepsilon_p=\Delta\gamma\,\mathbf n,\qquad \mathbf n=\tfrac32\,\mathbf s/q", size=34)),
        )
        for e in eqs:
            e.arrange(DOWN, buff=0.1, aligned_edge=LEFT)
        eqs.arrange(DOWN, buff=0.38, aligned_edge=LEFT).move_to(RIGHT * 3.35 + DOWN * 0.35)
        with self.say("k1") as d:
            self.play(FadeIn(head), run_time=0.6)
            self.play(Create(circ), FadeIn(axs), FadeIn(sub), FadeIn(circ_t), run_time=1.2)
            self.play(FadeIn(d_n), FadeIn(l_n), run_time=0.4)
            self.until("k1", "predicts an elastic")
            self.play(Create(ar_t), FadeIn(d_t), FadeIn(l_t), FadeIn(eqs[0]), run_time=1.2)
            self.until("k1", "If it lies outside")
            self.play(Indicate(circ, color=C_YIELD, scale_factor=1.04), FadeIn(eqs[1]), run_time=1.0)
            self.until("k1", "returned radially")
            self.play(GrowArrow(ar_r), FadeIn(d_r), FadeIn(l_r), FadeIn(eqs[2]), run_time=1.2)
            self.until("k1", "plastic strain grows")
            self.play(GrowArrow(nrm), FadeIn(l_nrm), FadeIn(eqs[3]), run_time=1.0)
        k1 = VGroup(circ, circ_t, axs, sub, d_n, l_n, ar_t, d_t, l_t, ar_r, d_r, l_r, nrm, l_nrm, eqs)
        # ------------------------------------------------------------ k2: increments + Newton on the FE plate curve
        c1 = load_json("fe", "case1.json")
        P = np.r_[0.0, c1["curves"]["epp"]["P"]]
        dd = np.r_[0.0, c1["curves"]["epp"]["d"]]
        ax = axes((0, 1.2), (0, 1200), 6.6, 4.6, 0.2, 200).move_to(LEFT * 2.8 + DOWN * 0.45)
        tk = ticks(ax, [0, 0.4, 0.8, 1.2], [0, 400, 800, 1200], size=18)
        lb = ax_labels(ax, "displacement [mm]", "load [kN]")
        cur = data_curve(ax, dd, P, C_EPP, width=4.5)
        cur_t = T("FE load–displacement curve (case 1)", 19, C_EPP).next_to(ax.c2p(0.75, 990), DOWN, buff=0.2)
        Pi = lambda x: float(np.interp(x, dd, P))
        dPi = lambda x: float((Pi(x + 1e-3) - Pi(max(0.0, x - 1e-3))) / (x + 1e-3 - max(0.0, x - 1e-3)))
        xinv = lambda p: float(np.interp(p, P, dd))
        levels = [300.0, 600.0, 850.0]
        neq = VGroup(T("each increment: Newton–Raphson", 20, DIM),
                     M(r"\mathbf K_T\,\Delta\mathbf u=\mathbf f_{ext}-\mathbf f_{int}(\mathbf u)", size=36),
                     M(r"\mathbf K_T=\int \mathbf B^T\,\mathbb{C}^{ep}_{alg}\,\mathbf B\,dV", size=34),
                     T("consistent tangent: quadratic convergence", 19, DIM)).arrange(DOWN, buff=0.18, aligned_edge=LEFT)
        neq.move_to(RIGHT * 3.75 + UP * 0.9)
        with self.say("k2") as d:
            self.play(FadeOut(k1), run_time=0.6)
            self.play(Create(ax), FadeIn(tk), FadeIn(lb), run_time=0.8)
            self.play(Create(cur), FadeIn(cur_t), run_time=1.0)
            dots = VGroup()
            for lv in levels:
                hl = hline(ax, lv, FAINT, width=1.8)
                dt = Dot(ax.c2p(xinv(lv), lv), color=C_GOOD, radius=0.07)
                self.play(Create(hl), FadeIn(dt, scale=1.4), run_time=0.45)
                dots.add(hl, dt)
            self.until("k2", "Newton-Raphson")
            self.play(FadeIn(neq), run_time=0.8)
            # Newton zig-zag for the increment 850 -> 985 kN, where the tangent stiffness drops
            x = xinv(850.0)
            path = [ax.c2p(x, Pi(x))]
            for _ in range(5):
                x = x + (985.0 - Pi(x)) / max(dPi(x), 1e-3)
                path += [ax.c2p(x, 985.0), ax.c2p(x, Pi(x))]
            zz = VMobject(stroke_color=C_YIELD, stroke_width=3).set_points_as_corners(path)
            self.play(Create(zz), run_time=1.2)
            self.until("k2", "When the structure")
            lv = 1050.0
            hl4 = hline(ax, lv, C_BAD, width=2.2)
            x = xinv(960.0)
            path = [ax.c2p(x, Pi(x))]
            for _ in range(3):
                slope = max(dPi(x), 40.0)
                xn = min(x + (lv - Pi(x)) / slope, 1.25)
                path += [ax.c2p(xn, lv), ax.c2p(xn, Pi(min(xn, 1.2)))]
                x = xn
                if x >= 1.2:
                    break
            zz2 = VMobject(stroke_color=C_BAD, stroke_width=3).set_points_as_corners(path)
            xm = cross_mark(C_BAD, 0.32).move_to(ax.c2p(1.17, lv) + UP * 0.32)
            msg = VGroup(T("load above the limit load:", 21, C_BAD, weight=BOLD),
                         T("no equilibrium state exists,", 21, INK), T("Newton iterations diverge", 21, INK),
                         T("→ plastic collapse", 21, C_BAD, weight=BOLD)).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
            msg.move_to(RIGHT * 3.75 + DOWN * 1.65)
            self.play(Create(hl4), run_time=0.5)
            self.play(Create(zz2), run_time=1.2)
            self.play(FadeIn(xm, scale=1.3), FadeIn(msg), run_time=0.8)
        k2 = VGroup(ax, tk, lb, cur, cur_t, dots, neq, zz, hl4, zz2, xm, msg)
        # ------------------------------------------------------------ k3: two material models
        from epfem import dnv_type_curve
        h = dnv_type_curve()
        ep = np.r_[0.0, np.linspace(1e-5, 0.10, 300)]
        sp = h(ep)[0]
        with self.say("k3") as d:
            self.play(FadeOut(k2), run_time=0.6)
            axA = axes((0, 0.10), (0, 600), 5.2, 3.6, 0.02, 100).move_to(LEFT * 3.4 + DOWN * 0.55)
            axB = axes((0, 0.10), (0, 600), 5.2, 3.6, 0.02, 100).move_to(RIGHT * 3.4 + DOWN * 0.55)
            g = VGroup()
            for axx in (axA, axB):
                g.add(axx, ticks(axx, [0, 0.05, 0.10], [0, 200, 400, 600], xfmt="{:.0%}", size=17),
                      ax_labels(axx, "strain", "stress [MPa]", size=19))
            epp = data_curve(axA, [0, 355 / E, 0.10], [0, 355, 355], C_EPP, width=5)
            tru = data_curve(axB, np.r_[0.0, sp / E + ep], np.r_[0.0, sp], C_TRUE, width=5)
            tA = VGroup(T("elastic–perfectly plastic", 25, C_EPP, weight=BOLD), T("→ limit-load analysis", 21, INK)
                        ).arrange(DOWN, buff=0.1).next_to(axA, UP, buff=0.75)
            tB = VGroup(T("true stress–strain curve", 25, C_TRUE, weight=BOLD), T("→ elastic–plastic and local-strain checks", 21, INK)
                        ).arrange(DOWN, buff=0.1).next_to(axB, UP, buff=0.75)
            self.play(FadeIn(g), run_time=0.7)
            self.play(Create(epp), FadeIn(tA), run_time=1.2)
            self.until("k3", "and the true")
            self.play(Create(tru), FadeIn(tB), run_time=1.4)
            self.until("k3", "yield plateau")
            pl = T("yield plateau", 19, C_YIELD).next_to(axB.c2p(0.022, 300), RIGHT, buff=0.1)
            hd = T("strain hardening", 19, C_YIELD).next_to(axB.c2p(0.07, float(h(np.array([0.068]))[0][0])), UP, buff=0.25)
            self.play(FadeIn(pl), FadeIn(hd), run_time=0.8)
        k3 = VGroup(g, epp, tru, tA, tB, pl, hd)
        # ------------------------------------------------------------ k4: validation against Hill
        c3 = load_json("fe", "case3.json")
        a, b, sy = c3["a"], c3["b"], c3["sy"]
        k_ = sy / np.sqrt(3)
        cs = np.linspace(a, b, 300)
        ph = k_ * (2 * np.log(cs / a) + 1 - cs ** 2 / b ** 2)
        cc = np.array(c3["curve"]["c"]); pp = np.array(c3["curve"]["p"])
        sel = cc > a + 0.2
        with self.say("k4") as d:
            self.play(FadeOut(k3), run_time=0.6)
            ax4 = axes((50, 100), (0, 450), 6.4, 4.4, 10, 50).move_to(LEFT * 2.6 + DOWN * 0.55)
            tk4 = ticks(ax4, [50, 60, 70, 80, 90, 100], [0, 100, 200, 300, 400], size=18)
            lb4 = ax_labels(ax4, "plastic front radius c [mm]", "bore pressure p [MPa]")
            hill = data_curve(ax4, cs, ph, C_THEORY, width=3)
            fe = VGroup(*[Dot(ax4.c2p(c_, p_), radius=0.045, color=C_VM) for c_, p_ in zip(cc[sel], pp[sel])])
            leg = VGroup(VGroup(Line(ORIGIN, RIGHT * 0.5, color=C_THEORY, stroke_width=3), T("Hill (1950), exact", 20, INK)).arrange(RIGHT, buff=0.12),
                         VGroup(Dot(radius=0.05, color=C_VM), T("this solver, FE", 20, INK)).arrange(RIGHT, buff=0.2)
                         ).arrange(DOWN, buff=0.12, aligned_edge=LEFT).move_to(ax4.c2p(84, 120))
            hd4 = T("Validation: thick cylinder under internal pressure", 28, INK, weight=SEMIBOLD).to_corner(UL, buff=0.4)
            info = VGroup(T("own solver, written for this film", 21, DIM),
                          T("6-node triangles · J2 radial return", 21, DIM),
                          T("consistent tangent · Newton–Raphson", 21, DIM)).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
            info.move_to(RIGHT * 4.0 + UP * 1.6)
            self.play(FadeTransform(head, hd4), Create(ax4), FadeIn(tk4), FadeIn(lb4), FadeIn(info), run_time=1.0)
            self.play(Create(hill), FadeIn(leg[0]), run_time=1.0)
            self.play(LaggedStart(*[FadeIn(x_) for x_ in fe], lag_ratio=0.02), FadeIn(leg[1]), run_time=1.6)
            self.until("k4", "First yield")
            r1 = panel("FIRST YIELD", [row_ for row_ in [VGroup(T("FE", 22, C_VM, weight=BOLD), T("224.0 MPa", 22, INK)).arrange(RIGHT, buff=0.2),
                                                         VGroup(T("Hill", 22, C_THEORY, weight=BOLD), T("223.9 MPa", 22, INK)).arrange(RIGHT, buff=0.2)]],
                       color=C_YIELD, width=3.4)
            r1.move_to(RIGHT * 4.0 + DOWN * 0.2)
            m1 = Circle(radius=0.14, color=C_YIELD, stroke_width=3).move_to(ax4.c2p(50, 224))
            self.play(FadeIn(r1), Create(m1), run_time=0.8)
            self.until("k4", "Collapse")
            r2 = panel("COLLAPSE (c = b)", [VGroup(T("FE", 22, C_VM, weight=BOLD), T("413.1 MPa", 22, INK)).arrange(RIGHT, buff=0.2),
                                            VGroup(T("Hill", 22, C_THEORY, weight=BOLD), T("413.8 MPa", 22, INK)).arrange(RIGHT, buff=0.2)],
                       color=C_BAD, width=3.4)
            r2.next_to(r1, DOWN, buff=0.3)
            m2 = Circle(radius=0.14, color=C_BAD, stroke_width=3).move_to(ax4.c2p(100, 413.8))
            self.play(FadeIn(r2), Create(m2), run_time=0.8)
        k4 = VGroup(hd4, ax4, tk4, lb4, hill, fe, leg, info, r1, r2, m1, m2)
        # ------------------------------------------------------------ k5: load factors
        with self.say("k5") as d:
            self.play(FadeOut(k4), run_time=0.6)
            hd5 = T("The margin moves from the stress to the load", 30, INK, weight=SEMIBOLD).to_corner(UL, buff=0.4)
            old = VGroup(T("elastic route", 22, DIM, weight=BOLD), M(r"\sigma\;\le\;\text{allowable}", size=38, color=DIM)).arrange(DOWN, buff=0.15)
            new = VGroup(T("elastic–plastic route", 22, C_ASME, weight=BOLD),
                         M(r"\gamma\times(\text{design loads})\;\Rightarrow\;\text{converged, stable solution}", size=38, color=INK)).arrange(DOWN, buff=0.15)
            top = VGroup(old, Arrow(ORIGIN, RIGHT * 1.2, color=DIM, buff=0), new).arrange(RIGHT, buff=0.5).next_to(hd5, DOWN, buff=0.55)
            top.set_x(0)
            top_final = top.copy()
            if top.width > 13.4:
                top.scale_to_fit_width(13.4)
                top_final.scale_to_fit_width(13.4).set_x(0)
            top.move_to(UP * 0.2)
            self.play(FadeIn(hd5), FadeIn(old), run_time=0.8)
            self.until("k5", "they multiply")
            self.play(GrowArrow(top[1]), FadeIn(new), run_time=1.0)
            self.until("k5", "1.5 for", lead=1.0)
            self.play(Transform(top, top_final), run_time=0.7)
            rows = [("Limit-load analysis", "elastic–perfectly plastic, σy = 1.5 S, small displacements", "1.5", C_EPP),
                    ("Elastic–plastic analysis", "true stress–strain curve, large displacements", "2.4", C_TRUE),
                    ("Local failure check", "true stress–strain curve, triaxial strain limit", "1.7", C_X)]
            tbl = VGroup()
            for nm, desc, f, col in rows:
                a_ = T(nm, 25, col, weight=BOLD)
                b_ = T(desc, 20, INK)
                c_ = VGroup(M(r"\gamma=", size=38), T(f, 34, col, weight=BOLD)).arrange(RIGHT, buff=0.12)
                box = RoundedRectangle(width=12.4, height=1.0, corner_radius=0.12, stroke_color=FAINT, stroke_width=1.5,
                                       fill_color=PANEL, fill_opacity=1)
                txt = VGroup(a_, b_).arrange(DOWN, buff=0.08, aligned_edge=LEFT).move_to(box).align_to(box, LEFT).shift(RIGHT * 0.35)
                c_.move_to(box).align_to(box, RIGHT).shift(LEFT * 0.4)
                tbl.add(VGroup(box, txt, c_))
            tbl.arrange(DOWN, buff=0.2).next_to(top, DOWN, buff=0.6)
            foot = T("ASME VIII-2 Part 5, factors on (P + Ps + D); other load combinations apply. Check the edition in force.",
                     17, DIM).next_to(tbl, DOWN, buff=0.3)
            for rr, ph in zip(tbl, ["1.5 for", "2.4 for", "1.7 for"]):
                self.until("k5", ph)
                self.play(FadeIn(rr, shift=0.15 * UP), run_time=0.6)
            self.play(FadeIn(foot), run_time=0.5)
        self.wait(0.5)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.8)
