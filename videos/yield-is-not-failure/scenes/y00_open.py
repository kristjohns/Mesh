"""Cold open (elastic 558 MPa vs elastic-plastic 0.18 %) and why yield is not failure."""
import os

import numpy as np
from manim import *  # noqa: F401,F403

from common import colorbar
from ycommon import (C_ASME, BG, C_BAD, C_FRONT, C_GOOD, C_SHEAR, C_TRESCA, C_VM, C_X, C_YIELD, C_Z, DIM, FAINT, FR, INK,
                     PANEL, ImageSeq, M, NScene, T, ax_labels, axes, data_curve, field_legend, follow, hline, load_json,
                     strike, ticks, vline)

E = 210000.0
# fillet-root location in the 48 x 27 mm window (z horizontal, r vertical)
ZS, Ro1 = 600.0, 136.55
WIN = (ZS - 34, ZS + 14, Ro1 - 13.5, Ro1 + 13.5)


def img_frac(z, r):
    return (z - WIN[0]) / (WIN[1] - WIN[0]), 1 - (r - WIN[2]) / (WIN[3] - WIN[2])


def img_point(img, z, r):
    fx, fy = img_frac(z, r)
    c = img.get_center()
    return c + np.array([(fx - 0.5) * img.width, (0.5 - fy) * img.height, 0.0])


class Y00_Open(NScene):
    def construct(self):
        c4 = load_json("fe", "case4.json")
        peak_z, peak_r = c4["where"]["z"], c4["where"]["r"]
        el = ImageMobject(os.path.join(FR, "open_elastic.png"))
        el.height = 5.0
        el.move_to(LEFT * 0.9 + DOWN * 0.15)
        frame = SurroundingRectangle(el, buff=0, stroke_color=FAINT, stroke_width=1.5)
        ttl = T("Transition-piece fillet  ·  linear elastic", 28, INK, weight=SEMIBOLD).next_to(el, UP, buff=0.25)
        ttl.align_to(el, LEFT)
        cb = colorbar(0, 560, n=14, height=4.0, ticks=[0, 140, 280, 420, 560], size=20)
        cb.next_to(el, RIGHT, buff=0.45).shift(DOWN * 0.15)
        dash = DashedLine(ORIGIN, RIGHT * 0.55, color=WHITE, stroke_width=3)
        dl = VGroup(dash, T("355 MPa = yield", 20, INK)).arrange(RIGHT, buff=0.12).next_to(cb, DOWN, buff=0.3)
        dl.align_to(cb, LEFT)
        pk = img_point(el, peak_z, peak_r)

        with self.say("n1") as d:
            self.play(FadeIn(el), FadeIn(frame), FadeIn(ttl, shift=0.1 * UP), run_time=1.4)
            self.play(FadeIn(cb), run_time=0.6)
            self.until("n1", "Now increase")
            lf = T("× 1.7 design load", 30, C_YIELD, weight=BOLD).move_to(img_point(el, 575, 147.5))
            self.play(FadeIn(lf, scale=1.2), run_time=0.7)
            self.until("n1", "The linear elastic answer")
            lab = VGroup(M(r"\sigma_{vm,\max} =", size=40), T("558 MPa", 36, INK, weight=BOLD)).arrange(RIGHT, buff=0.15)
            lab.move_to(img_point(el, 578.5, 141.0))
            lead = Line(lab.get_bottom() + DOWN * 0.05 + RIGHT * 0.8, pk, color=INK, stroke_width=2.5, buff=0.06)
            ring = Circle(radius=0.13, color=INK, stroke_width=3).move_to(pk)
            self.play(FadeIn(lab, shift=0.1 * DOWN), Create(lead), Create(ring), run_time=1.0)
            self.until("n1", "far above")
            self.play(FadeIn(dl), Indicate(dash, color=WHITE), run_time=1.0)
        with self.say("n2") as d:
            st = strike(lab[1], color=C_BAD, width=5)
            fic = T("not physical", 24, C_BAD, weight=BOLD).next_to(lab, DOWN, buff=0.12).align_to(lab, RIGHT)
            self.play(Create(st), FadeIn(fic), run_time=0.8)
            self.until("n2", "Steel cannot")
            self.play(FadeOut(VGroup(cb, dl, lf, ttl)),
                      Group(el, frame, lab, st, fic, lead, ring).animate.scale(0.66).move_to(LEFT * 3.55 + UP * 0.45),
                      run_time=1.2)
            t_el = T("linear elastic", 26, INK, weight=SEMIBOLD).next_to(el, UP, buff=0.18).align_to(el, LEFT)
            # inset: what linear elasticity assumes vs what steel does
            axi = axes((0, 0.006), (0, 600), 4.6, 3.0, 0.001, 100).move_to(RIGHT * 3.7 + UP * 0.35)
            tki = ticks(axi, [0, 0.002, 0.004, 0.006], [0, 200, 400, 600], xfmt="{:.1%}", size=17)
            lbi = ax_labels(axi, "strain", "stress [MPa]", size=19)
            lin = DashedLine(axi.c2p(0, 0), axi.c2p(558 / E, 558), color=INK, stroke_width=3)
            lin_t = T("linear elastic: 558", 19, INK).next_to(axi.c2p(558 / E, 558), RIGHT, buff=0.12)
            from epfem import dnv_type_curve
            ee = np.linspace(0, 0.006, 200)
            hh = dnv_type_curve()
            ss = np.array([min(E * e, 357.0) for e in ee])
            for i, e in enumerate(ee):                      # plateau beyond yield (true curve)
                if E * e > 357.0:
                    epl = e - 357.0 / E
                    ss[i] = float(hh(np.array([epl]))[0][0])
            stl = data_curve(axi, ee, ss, C_YIELD, width=5)
            stl_t = T("steel: yields at 355", 19, C_YIELD).next_to(axi.c2p(0.0045, 360), DOWN, buff=0.15)
            self.play(FadeIn(t_el), Create(axi), FadeIn(tki), FadeIn(lbi), run_time=0.7)
            self.play(Create(lin), FadeIn(lin_t), run_time=0.8)
            self.play(Create(stl), FadeIn(stl_t), run_time=1.0)
            self.until("n2", "The elastic-plastic analysis")
            self.play(FadeOut(VGroup(axi, tki, lbi, lin, lin_t, stl, stl_t)), run_time=0.5)
            ep = ImageSeq("case4", el.height)
            ep.set_frame(66)                                   # load factor 1.7 (step 68)
            ep.move_to(RIGHT * 3.55 + UP * 0.45)
            fr2 = SurroundingRectangle(ep, buff=0, stroke_color=FAINT, stroke_width=1.5)
            t_ep = T("elastic–plastic  ·  same load", 26, INK, weight=SEMIBOLD).next_to(ep, UP, buff=0.18).align_to(ep, LEFT)
            leg = field_legend(width=1.9, size=19).next_to(ep, DOWN, buff=0.35)
            if leg.width > 6.9:
                leg.scale_to_fit_width(6.9)
            self.play(FadeIn(ep), FadeIn(fr2), FadeIn(t_ep), run_time=1.0)
            self.play(FadeIn(leg), run_time=0.6)
            # 5 mm scale bar on the EP image
            p0 = img_point(ep, 568.0, 125.0)
            bar = VGroup(Line(p0, p0 + RIGHT * ep.width * 5 / 48, color=INK, stroke_width=4),
                         T("5 mm", 18, INK).next_to(p0 + RIGHT * ep.width * 2.5 / 48, UP, buff=0.06))
            self.play(FadeIn(bar), run_time=0.4)
            self.until("n2", "a peak plastic strain")
            pk2 = img_point(ep, peak_z, peak_r)
            lab2 = VGroup(M(r"\bar\varepsilon_{p,\max} =", size=38), T("0.18 %", 34, C_YIELD, weight=BOLD)).arrange(RIGHT, buff=0.15)
            lab2.move_to(img_point(ep, 579.0, 142.0))
            lead2 = Line(lab2.get_bottom() + DOWN * 0.05 + RIGHT * 0.5, pk2, color=INK, stroke_width=2.5, buff=0.06)
            self.play(FadeIn(lab2, shift=0.1 * DOWN), Create(lead2), run_time=0.9)
        with self.say("n3") as d:
            hl = Circle(radius=0.42, color=C_FRONT, stroke_width=4).move_to(pk2 + DOWN * 0.08)
            self.play(Create(hl), run_time=0.7)
            self.until("n3", "Has anything failed")
            q = T("Has anything failed?", 46, INK, weight=BOLD).to_edge(DOWN, buff=0.45)
            self.play(FadeOut(leg), FadeIn(q, shift=0.2 * UP), run_time=0.8)
            self.until("n3", "Answering that")
            everything = Group(*self.mobjects)
            self.play(FadeOut(everything), run_time=0.8)
            title = T("YIELD IS NOT FAILURE", 66, INK, weight=BOLD).shift(UP * 1.0)
            line = Line(LEFT * 4.6, RIGHT * 4.6, color=C_YIELD, stroke_width=3).next_to(title, DOWN, buff=0.3)
            sub = T("Five elastic–plastic finite element analyses, and the criteria that decide", 26, DIM)
            sub.next_to(line, DOWN, buff=0.3)
            self.play(FadeIn(title, shift=0.15 * UP), Create(line), run_time=1.0)
            self.play(FadeIn(sub), run_time=0.6)
            self.until("n3", "Here are five")
            names = ["Plate with a hole", "Plastic hinge", "Thick-walled cylinder", "Notch strain", "Thermal cycling"]
            chips = VGroup()
            for i, nm in enumerate(names):
                t = VGroup(T(f"{i + 1}", 22, C_YIELD, weight=BOLD), T(nm, 21, INK)).arrange(RIGHT, buff=0.14)
                box = RoundedRectangle(width=t.width + 0.4, height=0.55, corner_radius=0.12, stroke_color=FAINT,
                                       stroke_width=1.5, fill_color=PANEL, fill_opacity=1)
                t.move_to(box)
                chips.add(VGroup(box, t))
            chips.arrange(RIGHT, buff=0.2).next_to(sub, DOWN, buff=0.7)
            if chips.width > 13.4:
                chips.scale_to_fit_width(13.4)
            self.play(LaggedStart(*[FadeIn(c, shift=0.15 * UP) for c in chips], lag_ratio=0.18), run_time=1.6)
        self.wait(1.0)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.8)


class Y01_Why(NScene):
    def construct(self):
        from epfem import dnv_type_curve
        h = dnv_type_curve()
        ep = np.r_[0.0, np.linspace(1e-5, 0.19, 400)]
        sp = h(ep)[0]
        eps = np.r_[0.0, sp / E + ep]
        sig = np.r_[0.0, sp]
        # ------------------------------------------------------------ w1: the material
        ax = axes((0, 0.20), (0, 600), 9.6, 4.7, 0.05, 100).move_to(DOWN * 0.35 + RIGHT * 0.2)
        tk = ticks(ax, [0, 0.05, 0.10, 0.15, 0.20], [0, 200, 400, 600], xfmt="{:.0%}", size=19)
        lab = ax_labels(ax, "true strain", "true stress [MPa]")
        head = T("S355 structural steel  ·  true stress–strain curve", 28, INK, weight=SEMIBOLD).to_corner(UL, buff=0.4)
        curve = data_curve(ax, eps, sig, C_VM, width=5)
        with self.say("w1") as d:
            self.play(FadeIn(head), Create(ax), FadeIn(tk), FadeIn(lab), run_time=1.2)
            self.play(Create(curve), run_time=2.2, rate_func=linear)
            self.until("w1", "yields at a strain")
            py = ax.c2p(357 / E, 357)
            dy = Dot(py, color=C_YIELD, radius=0.08)
            ly = VGroup(T("yield", 22, C_YIELD, weight=BOLD), M(r"\varepsilon_Y=\sigma_Y/E\approx0.17\,\%", size=32, color=C_YIELD)
                        ).arrange(RIGHT, buff=0.15).move_to(ax.c2p(0.042, 560))
            lyl = Line(ly.get_bottom() + LEFT * 0.9 + DOWN * 0.05, py, color=C_YIELD, stroke_width=2, buff=0.1)
            ly.add(lyl)
            self.play(FadeIn(dy, scale=1.5), FadeIn(ly), run_time=0.8)
            self.until("w1", "before it necks")
            eneck = 0.1666
            pn = ax.c2p(eneck, float(np.interp(eneck, eps, sig)))
            dn = Dot(pn, color=C_TRESCA, radius=0.08)
            ln = VGroup(T("onset of necking", 22, C_TRESCA, weight=BOLD), M(r"\varepsilon\approx n\approx 17\,\%", size=32, color=C_TRESCA)
                        ).arrange(DOWN, buff=0.08, aligned_edge=RIGHT).next_to(pn, DOWN, buff=0.35).shift(LEFT * 0.2)
            self.play(FadeIn(dn, scale=1.5), FadeIn(ln), run_time=0.8)
            self.until("w1", "Yield is the start")
            b1 = BraceBetweenPoints(ax.c2p(0.0017, 0), ax.c2p(eneck, 0), direction=UP, color=C_TRESCA)
            b1.shift(UP * 0.12)
            bt = T("≈ 100 × the elastic strain", 22, C_TRESCA).next_to(b1, UP, buff=0.08)
            self.play(GrowFromCenter(b1), FadeIn(bt), run_time=0.9)
        w1 = VGroup(ax, tk, lab, head, curve, dy, ly, dn, ln, b1, bt)
        # ------------------------------------------------------------ w2: redistribution in a beam
        with self.say("w2") as d:
            self.play(FadeOut(w1), run_time=0.7)
            head2 = T("Redistribution: a rectangular section in bending", 28, INK, weight=SEMIBOLD).to_corner(UL, buff=0.4)
            H = 3.6
            sec = Rectangle(width=1.5, height=H, stroke_color=INK, stroke_width=2.5, fill_color=PANEL, fill_opacity=1)
            sec.move_to(LEFT * 5.0 + DOWN * 0.3)
            na = DashedLine(sec.get_left() + LEFT * 0.25, sec.get_right() + RIGHT * 0.25, color=DIM, stroke_width=2)
            # stress-profile axes
            o = np.array([-1.35, -0.3, 0.0])
            Wd = 1.6
            yax = Line(o + DOWN * H / 2, o + UP * H / 2, color=DIM, stroke_width=2)
            sy_l = DashedLine(o + RIGHT * Wd + DOWN * H / 2, o + RIGHT * Wd + UP * H / 2, color=C_YIELD, stroke_width=2)
            sy_r = DashedLine(o + LEFT * Wd + DOWN * H / 2, o + LEFT * Wd + UP * H / 2, color=C_YIELD, stroke_width=2)
            syt = VGroup(M(r"+\sigma_Y", size=28, color=C_YIELD).next_to(sy_l, UP, buff=0.08),
                         M(r"-\sigma_Y", size=28, color=C_YIELD).next_to(sy_r, UP, buff=0.08))
            r = ValueTracker(0.0)

            def prof():
                k = r.get_value()
                ys = np.linspace(-1, 1, 121)
                s = np.clip(k * ys, -1, 1)
                pts = [o + np.array([s_ * Wd, y * H / 2, 0]) for s_, y in zip(s, ys)]
                poly_t = Polygon(o, *[p for p, y in zip(pts, ys) if y >= 0], o + UP * H / 2, stroke_width=0,
                                 fill_color=C_X, fill_opacity=0.55)
                poly_c = Polygon(o + DOWN * H / 2, *[p for p, y in zip(pts, ys) if y <= 0], o, stroke_width=0,
                                 fill_color=C_Z, fill_opacity=0.55)
                edge = VMobject(stroke_color=INK, stroke_width=3).set_points_as_corners(pts)
                g = VGroup(poly_t, poly_c, edge)
                if k > 1:
                    yc = 1 / k
                    fill_sec = VGroup(Rectangle(width=sec.width, height=(1 - yc) * H / 2, stroke_width=0, fill_color=C_YIELD,
                                                fill_opacity=0.45).move_to(sec.get_center() + UP * (1 + yc) * H / 4),
                                      Rectangle(width=sec.width, height=(1 - yc) * H / 2, stroke_width=0, fill_color=C_YIELD,
                                                fill_opacity=0.45).move_to(sec.get_center() + DOWN * (1 + yc) * H / 4))
                    g.add(fill_sec)
                return g
            pr = always_redraw(prof)
            # M / My vs kappa / kappa_y
            ax2 = axes((0, 8), (0, 1.6), 4.4, 3.6, 1, 0.5).move_to(RIGHT * 4.45 + DOWN * 0.3)
            tk2 = ticks(ax2, [0, 2, 4, 6, 8], [0, 0.5, 1.0, 1.5], size=18)
            lb2 = VGroup(M(r"\kappa/\kappa_Y", size=30).next_to(ax2.x_axis.get_end(), DOWN, buff=0.4).align_to(ax2.x_axis.get_end(), RIGHT),
                         M(r"M/M_Y", size=30).next_to(ax2.y_axis.get_end(), UP, buff=0.15).align_to(ax2.y_axis, LEFT))
            kk = np.linspace(0, 8, 400)
            mm = np.where(kk <= 1, kk, 1.5 * (1 - 1 / (3 * np.maximum(kk, 1e-9) ** 2)))
            full = data_curve(ax2, kk, mm, C_VM, width=4)
            mp = hline(ax2, 1.5, C_YIELD)
            mpt = M(r"M_p=1.5\,M_Y", size=26, color=C_YIELD).next_to(ax2.c2p(8, 1.5), UP, buff=0.08).align_to(ax2.c2p(8, 1.5), RIGHT)
            part = full.copy()
            part.add_updater(lambda m: m.pointwise_become_partial(full, 0, max(1e-4, r.get_value() / 8)))
            dot = Dot(color=INK, radius=0.07).add_updater(
                lambda m: m.move_to(ax2.c2p(r.get_value(), float(np.interp(r.get_value(), kk, mm)))))
            part.update(); dot.update()
            self.play(FadeIn(head2), FadeIn(sec), Create(na), Create(yax), FadeIn(sy_l), FadeIn(sy_r), FadeIn(syt),
                      Create(ax2), FadeIn(tk2), FadeIn(lb2), FadeIn(mp), FadeIn(mpt), run_time=1.2)
            self.add(pr, part, dot)
            self.until("w2", "In a beam")
            self.play(r.animate.set_value(1.0), run_time=self.till("w2", "They stop"), rate_func=smooth)
            l1 = T("outer fibres reach yield", 22, C_YIELD).next_to(sec, DOWN, buff=0.25)
            self.play(FadeIn(l1), run_time=0.5)
            self.play(r.animate.set_value(2.5), run_time=self.till("w2", "The stress"), rate_func=linear)
            core = T("elastic core", 19, INK).move_to(sec.get_center() + UP * 0.22)
            self.play(FadeIn(core), run_time=0.4)
            self.play(r.animate.set_value(8.0), run_time=max(0.6, self.left() - 0.8), rate_func=linear)
            fin = T("+49 % moment after first yield", 22, C_VM, weight=BOLD).next_to(ax2, UP, buff=0.3)
            self.play(FadeIn(fin), run_time=0.5)
        pr.clear_updaters(); part.clear_updaters(); dot.clear_updaters()
        w2 = VGroup(head2, sec, na, yax, sy_l, sy_r, syt, pr, ax2, tk2, lb2, part, dot, mp, mpt, l1, core, fin)
        # ------------------------------------------------------------ w3: failure modes
        modes = [("Plastic collapse", "unbounded deformation at constant load", C_VM),
                 ("Local failure", "ductile fracture where strain and triaxiality are high", C_X),
                 ("Ratcheting", "strain that grows every cycle", C_SHEAR),
                 ("Fatigue", "crack initiation and growth under cyclic stress", C_TRESCA),
                 ("Buckling", "instability of slender or compressed parts", C_Z)]
        phrases = ["Plastic collapse", "Local failure", "Ratcheting", "Fatigue", "And buckling"]
        with self.say("w3") as d:
            self.play(FadeOut(w2), run_time=0.7)
            head3 = T("Once yield is allowed, these are the failure modes", 30, INK, weight=SEMIBOLD).to_corner(UL, buff=0.45)
            self.play(FadeIn(head3), run_time=0.6)
            rows = VGroup()
            for nm, desc, col in modes:
                dot_ = Dot(radius=0.09, color=col)
                a = T(nm, 30, col, weight=BOLD)
                b = T(desc, 24, DIM)
                rows.add(VGroup(dot_, a, b))
            for rr in rows:
                rr[1].next_to(rr[0], RIGHT, buff=0.25)
                rr[2].next_to(rr[1], RIGHT, buff=0.35).align_to(rr[1], DOWN)
            rows.arrange(DOWN, buff=0.42, aligned_edge=LEFT).move_to(LEFT * 0.4 + UP * 0.2)
            for rr, ph in zip(rows, phrases):
                self.until("w3", ph)
                self.play(FadeIn(rr, shift=0.2 * RIGHT), run_time=0.6)
            self.until("w3", "Yield itself")
            y = VGroup(Dot(radius=0.09, color=DIM), T("Yield", 30, DIM, weight=BOLD), T("is not on the list", 24, DIM))
            y[1].next_to(y[0], RIGHT, buff=0.25); y[2].next_to(y[1], RIGHT, buff=0.35).align_to(y[1], DOWN)
            y.next_to(rows, DOWN, buff=0.55, aligned_edge=LEFT)
            st = strike(y[1], C_BAD, 5)
            self.play(FadeIn(y), run_time=0.5)
            self.play(Create(st), run_time=0.5)
        w3 = VGroup(head3, rows, y, st)
        # ------------------------------------------------------------ w4: codes
        cards = [("ASME BPVC VIII-2, Part 5", "Design by analysis of pressure vessels", "limit load · elastic–plastic · local strain · ratcheting"),
                 ("EN 13445-3, Annex B", "Direct route for unfired pressure vessels", "gross plastic deformation · progressive deformation"),
                 ("DNV-RP-C208", "Nonlinear FE capacity of offshore steel structures", "material curves · strain limits · resistance factors")]
        with self.say("w4") as d:
            self.play(FadeOut(w3), run_time=0.7)
            head4 = T("Each mode: its own analysis and acceptance criterion", 30, INK, weight=SEMIBOLD).to_corner(UL, buff=0.45)
            flow = VGroup(T("failure mode", 26, C_VM, weight=BOLD), Arrow(ORIGIN, RIGHT * 1.0, color=DIM, buff=0),
                          T("analysis that can see it", 26, INK, weight=BOLD), Arrow(ORIGIN, RIGHT * 1.0, color=DIM, buff=0),
                          T("acceptance criterion", 26, C_ASME, weight=BOLD)).arrange(RIGHT, buff=0.25)
            flow.next_to(head4, DOWN, buff=0.45).align_to(head4, LEFT)
            self.play(FadeIn(head4), run_time=0.6)
            self.play(LaggedStart(*[FadeIn(f_) for f_ in flow], lag_ratio=0.25), run_time=1.4)
            cg = VGroup()
            for a, b, c in cards:
                ta = T(a, 26, C_YIELD, weight=BOLD)
                tb = T(b, 22, INK)
                tc = T(c, 19, DIM)
                body = VGroup(ta, tb, tc).arrange(DOWN, buff=0.18, aligned_edge=LEFT)
                box = RoundedRectangle(width=12.0, height=body.height + 0.5, corner_radius=0.15, stroke_color=FAINT,
                                       stroke_width=1.5, fill_color=PANEL, fill_opacity=1)
                body.move_to(box).align_to(box, LEFT).shift(RIGHT * 0.35)
                cg.add(VGroup(box, body))
            cg.arrange(DOWN, buff=0.28).move_to(DOWN * 0.75)
            for card, ph in zip(cg, ["ASME", "EN 13445", "DNV-RP-C208"]):
                self.until("w4", ph)
                self.play(FadeIn(card, shift=0.2 * UP), run_time=0.6)
        self.wait(0.6)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.8)
