"""Case 3 (thick cylinder: 2.4x global criterion, collapse, residual stress) and case 4 (local strain limit)."""
import numpy as np
from manim import *  # noqa: F401,F403

from ycommon import (BG, C_ASME, C_BAD, C_EPP, C_FRONT, C_GOOD, C_THEORY, C_TRUE, C_VM, C_X, C_Y, C_YIELD, C_Z, DIM,
                     EL_COLS, FAINT, INK, PANEL, PL_COLS, ImageSeq, M, NScene, T, ax_labels, axes, case_card,
                     case_header, cross_mark, data_curve, field_legend, follow, frame_index, grow_with, hline,
                     load_json, panel, ramp_at, strike, tick_mark, ticks, vline)

E = 210000.0


def uniq_profile(prof, keys):
    r = np.round(np.array(prof["r"]), 3)
    ru = np.unique(r)
    out = {"r": ru}
    for k in keys:
        v = np.array(prof[k])
        out[k] = np.array([v[r == x].mean() for x in ru])
    return out


class Y05_Cylinder(NScene):
    def construct(self):
        c3 = load_json("fe", "case3.json")
        a, b, sy = c3["a"], c3["b"], c3["sy"]
        pd, pg, py = c3["p_design"], c3["p_global"], c3["p_y_hill"]
        Pc, Cc, Uc = (np.array(c3["curve"][k]) for k in ("p", "c", "u"))
        G = uniq_profile(c3["at_global"], ["s_rr", "s_zz", "s_tt", "vm"])
        Rz = uniq_profile(c3["residual"], ["s_rr", "s_zz", "s_tt", "vm"])
        case_card(self, 3, "Thick-walled cylinder", "elastic–plastic analysis at 2.4 × design pressure")
        hdr = case_header(3, "High-pressure body as a thick-walled cylinder",
                          "axisymmetric, plane strain  ·  75 ksi forging, σY = 517 MPa  ·  elastic–perfectly plastic")
        CEN = np.array([-3.75, -0.35, 0.0])
        RO = 2.2
        sc = RO / b
        NR = 56
        radii = np.linspace(a, b, NR + 1)
        p = ValueTracker(0.0)
        mode = {"res": 0.0}

        def c_of(pp):
            return a if pp <= Pc[0] else float(np.interp(pp, Pc, Cc))

        def color_at(rm, pp):
            c = c_of(pp) if pp > py else a
            if pp > py and rm < c:
                return ramp_at(PL_COLS, 0.15 + 0.55 * (c - rm) / max(c - a, 1e-6))
            v = (pp / py) * (a / rm) ** 2 if pp <= py else (c / rm) ** 2
            return ramp_at(EL_COLS, v)

        def res_color(rm):
            s = float(np.interp(rm, Rz["r"], Rz["s_tt"]))
            x = float(np.clip(s / 300.0, -1, 1))
            return interpolate_color(ManimColor("#1A2436"), ManimColor("#6FA8FF" if x < 0 else "#FF6B6B"), min(1.0, abs(x) ** 0.8))

        rings = VGroup(*[Annulus(inner_radius=radii[i] * sc, outer_radius=radii[i + 1] * sc + 0.004, stroke_width=0,
                                 fill_opacity=1).move_to(CEN) for i in range(NR)])

        def upd_rings(g):
            pp = p.get_value()
            for i, ring in enumerate(g):
                rm = 0.5 * (radii[i] + radii[i + 1])
                col = ManimColor(color_at(rm, pp))
                if mode["res"] > 0:
                    col = interpolate_color(col, res_color(rm), mode["res"])
                ring.set_fill(col, opacity=1)
                ring.set_stroke(col, width=1.2, opacity=1)
        rings.add_updater(upd_rings)
        upd_rings(rings)
        edge = VGroup(Circle(radius=a * sc, color=INK, stroke_width=2).move_to(CEN),
                      Circle(radius=RO, color=INK, stroke_width=2).move_to(CEN))
        front = Circle(radius=a * sc, color=C_FRONT, stroke_width=3.5).move_to(CEN)
        front.add_updater(lambda m: m.set_width(2 * c_of(p.get_value()) * sc if p.get_value() > py else 2 * a * sc).move_to(CEN)
                          .set_stroke(opacity=1.0 if (p.get_value() > py and mode["res"] < 0.5) else 0.0))
        arrows = VGroup(*[Arrow(CEN + 0.25 * np.array([np.cos(t), np.sin(t), 0]), CEN + (a * sc - 0.05) * np.array([np.cos(t), np.sin(t), 0]),
                                buff=0, color=C_X, stroke_width=3, max_tip_length_to_length_ratio=0.35)
                          for t in np.linspace(0, TAU, 9)[:-1]])
        dims = VGroup(DoubleArrow(CEN + LEFT * a * sc, CEN + RIGHT * a * sc, buff=0, color=DIM, stroke_width=2, tip_length=0.12)
                      .shift(DOWN * 0.0), T("Ø100", 18, INK).move_to(CEN + DOWN * 0.3),
                      T("Ø200", 18, INK).next_to(edge[1], DOWN, buff=0.12))
        dims[0].set_opacity(0.0)
        top_y = edge[1].get_top()[1] + 0.35

        def readout():
            g = VGroup(M(r"p=", size=34), DecimalNumber(p.get_value(), num_decimal_places=0, font_size=34, color=INK),
                       T("MPa", 22, INK)).arrange(RIGHT, buff=0.1)
            g[2].align_to(g[1], DOWN)
            return g.move_to(np.array([CEN[0] - 0.9, top_y, 0]))

        def facout():
            g = VGroup(M(r"=", size=30, color=C_YIELD), DecimalNumber(p.get_value() / pd, num_decimal_places=2, font_size=30, color=C_YIELD),
                       M(r"\times\,p_{design}", size=30, color=C_YIELD)).arrange(RIGHT, buff=0.08)
            return g.move_to(np.array([CEN[0] + 1.15, top_y, 0]))
        prd = always_redraw(readout)
        fac = always_redraw(facout)
        leg = field_legend(width=1.5, size=16).next_to(edge[1], DOWN, buff=0.5)
        with self.say("c1") as d:
            self.play(FadeIn(hdr), run_time=0.6)
            self.add(rings)
            self.play(FadeIn(rings), Create(edge), run_time=1.0)
            self.until("c1", "100-millimetre")
            self.play(FadeIn(dims[1:]), run_time=0.6)
            self.until("c1", "rated for")
            self.add(front)
            self.play(FadeIn(prd), FadeIn(fac), FadeIn(arrows), FadeIn(leg), run_time=0.6)
            self.play(p.animate.set_value(pd), run_time=self.till("c1", "At that pressure"), rate_func=smooth)
            self.until("c1", "the bore reaches")
            lab = VGroup(M(r"\sigma_{vm,bore}=319\ \mathrm{MPa}=0.62\,\sigma_Y", size=34), T("elastic", 20, C_GOOD, weight=BOLD)
                         ).arrange(DOWN, buff=0.1).move_to(RIGHT * 3.7 + UP * 1.75)
            self.play(FadeIn(lab, shift=0.1 * UP), run_time=0.8)
        with self.say("c2") as d:
            crit = panel("ASME VIII-2 §5.2.4  ·  ELASTIC–PLASTIC",
                         ["loads factored by 2.4 (P + Ps + D)", "pass: the solution converges",
                          "(EPP model used here: conservative)"], color=C_ASME, size=20, width=6.3, buff=0.1)
            crit.move_to(RIGHT * 3.75 + UP * 1.75)
            self.play(FadeOut(lab), FadeIn(crit), run_time=0.8)
            self.until("c2", "At 48,000")
            elas = VGroup(T("linear elastic answer at the bore:", 20, DIM), T("766 MPa", 24, C_BAD, weight=BOLD)).arrange(RIGHT, buff=0.15)
            elas.next_to(crit, DOWN, buff=0.3)
            self.play(p.animate.set_value(pg), FadeIn(elas), run_time=2.4, rate_func=smooth)
            st_el = strike(elas[1], C_BAD, 4)
            self.play(Create(st_el), run_time=0.4)
            self.until("c2", "The elastic-plastic analysis")
            # stress profiles at 2.4x
            ax = axes((50, 100), (-400, 600), 5.4, 3.0, 10, 200).move_to(RIGHT * 3.85 + DOWN * 1.75)
            tk = ticks(ax, [50, 60, 70, 80, 90, 100], [-400, -200, 0, 200, 400, 600], size=16)
            lb = ax_labels(ax, "radius r [mm]", "stress at 2.4 × p [MPa]", size=18)
            curves = VGroup(data_curve(ax, G["r"], G["vm"], C_VM, 4), data_curve(ax, G["r"], G["s_tt"], C_X, 3),
                            data_curve(ax, G["r"], G["s_rr"], C_Z, 3), data_curve(ax, G["r"], G["s_zz"], C_Y, 2.5))
            names = VGroup(M(r"\sigma_{vm}", size=26, color=C_VM), M(r"\sigma_{\theta}", size=26, color=C_X),
                           M(r"\sigma_{r}", size=26, color=C_Z), M(r"\sigma_{z}", size=26, color=C_Y)).arrange(RIGHT, buff=0.3)
            names.next_to(ax, UP, buff=0.05).align_to(ax, RIGHT)
            self.play(FadeOut(elas), FadeOut(st_el), Create(ax), FadeIn(tk), FadeIn(lb), run_time=0.7)
            self.play(LaggedStart(*[Create(c_) for c_ in curves], lag_ratio=0.2), FadeIn(names), run_time=1.4)
            vf = vline(ax, c3["c_fe_at_global"], C_FRONT, width=2.5)
            vft = VGroup(T("plastic front", 18, C_FRONT, weight=BOLD), M(r"c_{FE}=65.40", size=26, color=C_FRONT),
                         M(r"c_{Hill}=65.37\ \mathrm{mm}", size=26, color=C_FRONT)).arrange(DOWN, buff=0.04, aligned_edge=LEFT)
            vft.next_to(ax.c2p(66, -380), UR, buff=0.08)
            wall = VGroup(T("31 %", 30, C_YIELD, weight=BOLD), T("of the wall", 17, C_YIELD), T("yielded", 17, C_YIELD)
                          ).arrange(DOWN, buff=0.04).move_to(CEN)
            self.until("c2", "the inner 31")
            self.play(FadeOut(arrows), FadeOut(dims[1]), FadeIn(wall), run_time=0.7)
            self.until("c2", "the plastic front")
            self.play(Create(vf), FadeIn(vft), run_time=0.8)
            self.until("c2", "and a converged")
            ok = VGroup(tick_mark(C_GOOD, 0.3), T("converged at 2.4 × p: passes", 21, C_GOOD, weight=BOLD)).arrange(RIGHT, buff=0.15)
            ok.next_to(crit, DOWN, buff=0.2).align_to(crit, LEFT)
            self.play(FadeIn(ok), run_time=0.7)
        with self.say("c3") as d:
            prof = VGroup(ax, tk, lb, curves, names, vf, vft)
            ax2 = axes((0, 0.6), (0, 450), 5.4, 3.0, 0.1, 100).move_to(RIGHT * 3.85 + DOWN * 1.75)
            tk2 = ticks(ax2, [0, 0.2, 0.4, 0.6], [0, 100, 200, 300, 400], size=16)
            lb2 = ax_labels(ax2, "bore displacement [mm]", "pressure p [MPa]", size=18)
            pu = data_curve(ax2, np.r_[0, Uc], np.r_[0, Pc], C_EPP, 4)
            lvls = VGroup(hline(ax2, pd, C_GOOD, width=1.8), hline(ax2, pg, C_ASME, width=1.8), hline(ax2, 413.8, C_BAD, width=1.8))
            lt = VGroup(T("design 137.9", 16, C_GOOD), T("2.4 × design 331", 16, C_ASME), T("collapse 413 (Hill 414)", 16, C_BAD))
            lt[0].next_to(lvls[0].get_end(), UP, buff=0.04).align_to(lvls[0].get_end(), RIGHT)
            lt[1].next_to(lvls[1].get_end(), DOWN, buff=0.06).align_to(lvls[1].get_end(), RIGHT)
            lt[2].next_to(ax2.c2p(0.02, 413.8), UP, buff=0.05).align_to(ax2.c2p(0.02, 0), LEFT)
            self.play(FadeOut(prof), Create(ax2), FadeIn(tk2), FadeIn(lb2), run_time=0.7)
            self.play(Create(pu), run_time=1.0)
            self.play(LaggedStart(*[Create(L_) for L_ in lvls], lag_ratio=0.2), FadeIn(lt), run_time=1.0)
            fx = T("= 3.0 × the rating", 18, C_BAD, weight=BOLD).next_to(lt[2], RIGHT, buff=0.15)
            self.play(FadeIn(fx), run_time=0.5)
            self.until("c3", "when the pressure is released")
            m_ = ValueTracker(0.0)
            rings.add_updater(lambda g: mode.__setitem__("res", m_.get_value()))
            self.play(p.animate.set_value(0.0), m_.animate.set_value(1.0), FadeOut(wall), FadeOut(leg), FadeOut(fac),
                      run_time=1.6, rate_func=smooth)
            res = VGroup(ax2, tk2, lb2, pu, lvls, lt, fx)
            ax3 = axes((50, 100), (-300, 100), 5.4, 3.0, 10, 100).move_to(RIGHT * 3.85 + DOWN * 1.75)
            tk3 = ticks(ax3, [50, 60, 70, 80, 90, 100], [-300, -200, -100, 0, 100], size=16)
            lb3 = ax_labels(ax3, "radius r [mm]", "residual stress [MPa]", size=18)
            rs = VGroup(data_curve(ax3, Rz["r"], Rz["s_tt"], C_X, 4), data_curve(ax3, Rz["r"], Rz["s_zz"], C_Y, 2.5),
                        data_curve(ax3, Rz["r"], Rz["s_rr"], C_Z, 2.5))
            z0 = hline(ax3, 0, FAINT, width=1.5)
            rn = VGroup(M(r"\sigma_{\theta}", size=26, color=C_X), M(r"\sigma_{z}", size=26, color=C_Y), M(r"\sigma_{r}", size=26, color=C_Z)
                        ).arrange(RIGHT, buff=0.3).next_to(ax3, UP, buff=0.05).align_to(ax3, RIGHT)
            self.play(FadeOut(res), Create(ax3), FadeIn(tk3), FadeIn(lb3), FadeIn(z0), run_time=0.7)
            self.play(Create(rs), FadeIn(rn), run_time=1.0)
            self.until("c3", "minus 284")
            dres = Dot(ax3.c2p(Rz["r"][0], Rz["s_tt"][0]), color=C_X, radius=0.08)
            tres = T("−284 MPa at the bore", 20, C_X, weight=BOLD).next_to(dres, UR, buff=0.12)
            cmp_ = T("compressive hoop stress at the bore", 19, "#6FA8FF").move_to(dims[2])
            self.play(FadeIn(dres, scale=1.5), FadeIn(tres), FadeOut(dims[2]), FadeIn(cmp_), run_time=0.8)
        with self.say("c4") as d:
            ineq = VGroup(M(r"\Delta p = 331\ \mathrm{MPa}\;<\;2\,p_Y=448\ \mathrm{MPa}", size=36),
                          T("unloading stays elastic → shakedown", 21, C_GOOD, weight=BOLD)).arrange(DOWN, buff=0.12)
            ineq.move_to(RIGHT * 3.75 + UP * 0.62)
            self.play(FadeOut(ok), FadeIn(ineq, shift=0.1 * UP), run_time=0.9)
            self.until("c4", "API 17 T R 8")
            api = panel("API 17TR8  ·  HPHT DESIGN GUIDELINE", ["subsea equipment above 15 ksi or 350 °F",
                                                                 "elastic–plastic analysis: ASME VIII-2 Part 5, VIII-3"],
                        color=C_YIELD, size=19, width=5.9, buff=0.1)
            api.move_to(crit)
            self.play(FadeOut(crit), FadeIn(api), run_time=0.9)
        rings.clear_updaters(); front.clear_updaters()
        self.wait(0.6)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.8)


class Y06_Fillet(NScene):
    def construct(self):
        c4 = load_json("fe", "case4.json")
        lf = np.array(c4["curve"]["lf"]); eb = np.array(c4["curve"]["eb"]); eLc = np.array(c4["curve"]["eL"])
        n = len(lf)
        fidx = frame_index(c4["frame_keys"])
        k17 = int(np.argmin(np.abs(lf - 1.7)))
        case_card(self, 4, "Notch strain at the fillet", "local failure: triaxial strain limit at 1.7 × loads")
        hdr = case_header(4, "Local strain at the transition-piece fillet",
                          "axisymmetric  ·  S355, true stress–strain curve  ·  ASME VIII-2 §5.3.3")
        IH = 3.9
        IW = IH * 16 / 9
        IC = np.array([-3.45, 0.7, 0.0])
        ZS, Ro1, RHO = 600.0, 136.55, 8.0
        win = (ZS - 34, ZS + 14, Ro1 - 13.5, Ro1 + 13.5)
        s_ = IW / 48.0
        mm = lambda z, r: IC + np.array([(z - (win[0] + win[1]) / 2) * s_, (r - (win[2] + win[3]) / 2) * s_, 0.0])
        # outline of the section in the window: pipe outer surface, fillet arc, shoulder face
        arc = [mm(ZS - RHO + RHO * np.sin(t), Ro1 + RHO - RHO * np.cos(t)) for t in np.linspace(0, PI / 2, 24)]
        outline = VMobject(stroke_color=INK, stroke_width=3).set_points_as_corners(
            [mm(win[0], Ro1)] + arc + [mm(ZS, win[3])])
        body = Polygon(mm(win[0], win[2]), mm(win[0], Ro1), *arc, mm(ZS, win[3]), mm(win[1], win[3]), mm(win[1], win[2]),
                       stroke_width=0, fill_color="#1A2436", fill_opacity=1)
        lds = VGroup(*[Arrow(mm(win[0] + 6, r), mm(win[0] - 1.5, r), buff=0, color=C_X, stroke_width=4,
                             max_tip_length_to_length_ratio=0.4) for r in np.linspace(win[2] + 2.5, Ro1 - 2.5, 4)])
        ldt = VGroup(M(r"\sigma_{nom}=150\ \mathrm{MPa}", size=28, color=C_X), T("pipe wall, axial", 17, DIM)).arrange(DOWN, buff=0.05)
        ldt.move_to(mm(573.5, 143.0))
        lbl = VGroup(T("pipe", 18, DIM).move_to(mm(574, 127)), T("flange", 18, DIM).move_to(mm(607, 146)),
                     T("fillet R8", 18, INK).move_to(mm(588, 145.5)))
        schem = VGroup(body, outline, lds, ldt, lbl)
        k = ValueTracker(0.0)
        img = ImageSeq("case4", IH, index_fn=lambda: fidx(k.get_value()))
        img.move_to(IC)
        frame = SurroundingRectangle(img, buff=0, stroke_color=FAINT, stroke_width=1.5)
        leg = field_legend(width=1.8, size=17).next_to(img, DOWN, buff=0.28)
        # plot: equivalent plastic strain (log) vs load factor
        ax = axes((0, 2.0), (0, 5), 5.3, 4.3, 0.25, 1).move_to(RIGHT * 3.95 + DOWN * 0.45)
        LG = lambda e: np.log10(np.maximum(e, 1e-9) * 100) + 3.0          # strain -> plot y (0 = 0.001 %)
        tk = ticks(ax, [0, 0.5, 1.0, 1.5, 2.0], [], size=17)
        ylab = VGroup(*[T(t_, 16, DIM).next_to(ax.c2p(0, y), LEFT, buff=0.12) for t_, y in
                        zip(["0.001 %", "0.01 %", "0.1 %", "1 %", "10 %", "100 %"], [0, 1, 2, 3, 4, 5])])
        lb = VGroup(T("load factor × design", 19, INK).next_to(ax.x_axis.get_end(), DOWN, buff=0.45).align_to(ax.x_axis.get_end(), RIGHT),
                    VGroup(T("strain at the fillet root", 19, INK), M(r"\bar\varepsilon_p", size=28)).arrange(RIGHT, buff=0.12)
                    .next_to(ax.y_axis.get_end(), UP, buff=0.15).align_to(ax.y_axis, LEFT))
        msk = eb > 1e-7
        lg = LG(eb)
        x_eb = np.r_[c4["lf_first_yield"], lf[msk]]
        y_eb = np.r_[0.0, lg[msk]]
        i0 = int(np.argmax(msk))
        full = data_curve(ax, x_eb, y_eb, C_YIELD, width=4.5)
        kk = ValueTracker(0.0)          # index into (x_eb, y_eb)
        with self.say("f1") as d:
            self.play(FadeIn(hdr), run_time=0.6)
            self.play(FadeIn(body), Create(outline), run_time=1.0)
            self.play(LaggedStart(*[GrowArrow(a_) for a_ in lds], lag_ratio=0.1), FadeIn(ldt), FadeIn(lbl), run_time=1.0)
            self.until("f1", "The fillet's stress concentration")
            kt = VGroup(M(r"K_t=2.19", size=40), T("linear elastic FE", 18, DIM)).arrange(DOWN, buff=0.08, aligned_edge=LEFT)
            pk = VGroup(M(r"\sigma_{peak}=2.19\times150=329\ \mathrm{MPa}<\sigma_Y", size=34)).arrange(DOWN)
            fy = VGroup(M(r"\text{first yield at }1.08\times\text{design}", size=34, color=C_YIELD))
            info = VGroup(kt, pk, fy).arrange(DOWN, buff=0.35, aligned_edge=LEFT).move_to(RIGHT * 3.7 + UP * 0.6)
            self.play(FadeIn(kt, shift=0.1 * UP), run_time=0.7)
            self.until("f1", "so the elastic peak")
            self.play(FadeIn(pk, shift=0.1 * UP), run_time=0.7)
            self.until("f1", "Yield begins")
            self.play(FadeIn(fy, shift=0.1 * UP), run_time=0.7)
            self.wait(max(0.1, self.left() - 1.0))
            self.play(FadeOut(schem), FadeIn(img), FadeIn(frame), FadeIn(leg), run_time=0.9)
        with self.say("f2") as d:
            self.play(FadeOut(info), Create(ax), FadeIn(tk), FadeIn(ylab), FadeIn(lb), run_time=0.8)
            v108 = vline(ax, c4["lf_first_yield"], FAINT, width=1.8)
            v17 = vline(ax, 1.7, C_ASME, width=2.2)
            v17t = T("1.7 × design", 18, C_ASME).next_to(v17.get_end(), UP, buff=0.05)
            self.play(Create(v108), Create(v17), FadeIn(v17t), run_time=0.6)
            # first: frames to first yield (elastic), then strain grows with the curve
            kfy = float(np.interp(c4["lf_first_yield"], lf, np.arange(n)))
            self.play(k.animate.set_value(kfy), run_time=1.6, rate_func=linear)
            part = grow_with(full, kk, len(x_eb))
            dot = follow(ax, x_eb, y_eb, kk, color=INK)
            self.add(part, dot)
            j17 = int(np.argmin(np.abs(x_eb - 1.7)))
            run = max(1.0, self.till("f2", "the peak equivalent") - 0.2)
            self.play(k.animate.set_value(k17), kk.animate.set_value(j17), run_time=run, rate_func=linear)
            d17 = Dot(ax.c2p(1.7, LG(c4["eb_at_17"])), color=C_YIELD, radius=0.09)
            t17 = VGroup(M(r"\bar\varepsilon_{p}=", size=30, color=C_YIELD), T("0.18 %", 24, C_YIELD, weight=BOLD)).arrange(RIGHT, buff=0.1)
            t17.next_to(d17, LEFT, buff=0.2).shift(UP * 0.25)
            self.play(FadeIn(d17, scale=1.5), FadeIn(t17), run_time=0.7)
        img.clear_updaters()
        with self.say("f3") as d:
            eL = data_curve(ax, lf[i0:], LG(eLc[i0:]), C_ASME, width=4)
            eLt = VGroup(M(r"\varepsilon_L(\eta)", size=30, color=C_ASME), T("strain limit", 18, C_ASME)).arrange(RIGHT, buff=0.12)
            eLt.next_to(ax.c2p(1.1, LG(eLc[i0])), UP, buff=0.12)
            form = VGroup(
                T("ASME VIII-2 §5.3.3  ·  triaxial strain limit", 21, C_ASME, weight=BOLD),
                M(r"\varepsilon_L=\varepsilon_{Lu}\,\exp\!\Big[-\frac{\alpha_{sl}}{1+m_2}\Big(\frac{\sigma_1+\sigma_2+\sigma_3}{3\,\sigma_e}-\frac13\Big)\Big]", size=34),
                M(r"\varepsilon_{Lu}=2\ln(1+0.22)=0.398,\quad m_2=0.60\,(1-\tfrac{355}{470})=0.147,\quad \alpha_{sl}=2.2", size=26),
                M(r"\eta=\frac{\sigma_1+\sigma_2+\sigma_3}{3\,\sigma_e}=0.556\;\Rightarrow\;\varepsilon_L=0.260", size=32),
                M(r"\varepsilon_{peq}+\varepsilon_{cf}\;\le\;\varepsilon_L:\qquad 0.0018\;\le\;0.260", size=34, color=C_GOOD),
                T("utilisation 0.7 %   (any forming strain is added to the demand)", 19, C_GOOD),
            ).arrange(DOWN, buff=0.26, aligned_edge=LEFT)
            if form.width > 6.3:
                form.scale_to_fit_width(6.3)
            box = RoundedRectangle(width=form.width + 0.5, height=form.height + 0.5, corner_radius=0.14, stroke_color=C_ASME,
                                   stroke_width=2, fill_color=PANEL, fill_opacity=0.95)
            fg = VGroup(box, form).move_to(np.array([-3.5, -0.3, 0]))
            form.move_to(box)
            self.play(FadeOut(img), FadeOut(frame), FadeOut(leg), FadeIn(box), FadeIn(form[0]), FadeIn(form[1]), run_time=1.0)
            self.until("f3", "For S three fifty-five")
            self.play(FadeIn(form[2]), Create(eL), FadeIn(eLt), run_time=1.0)
            self.until("f3", "At the fillet's triaxiality")
            self.play(FadeIn(form[3]), run_time=0.8)
            dL = Dot(ax.c2p(1.7, LG(c4["eL_at_17"])), color=C_ASME, radius=0.09)
            tL = T("26 %", 22, C_ASME, weight=BOLD).next_to(dL, UR, buff=0.08)
            self.play(FadeIn(dL, scale=1.5), FadeIn(tL), run_time=0.6)
            self.until("f3", "The demand")
            self.play(FadeIn(form[4]), run_time=0.8)
            self.until("f3", "Here it is")
            gap = DoubleArrow(d17.get_center(), dL.get_center(), buff=0.12, color=C_GOOD, stroke_width=3, tip_length=0.15)
            gt = T("× 140", 22, C_GOOD, weight=BOLD).next_to(gap, RIGHT, buff=0.1)
            self.play(GrowFromCenter(gap), FadeIn(gt), FadeIn(form[5]), run_time=0.8)
        with self.say("f4") as d:
            # Neuber construction on the stress-strain curve
            from epfem import dnv_type_curve
            hh = dnv_type_curve()
            axN = axes((0, 0.006), (0, 600), 5.6, 3.8, 0.001, 100).move_to(np.array([-3.4, -0.6, 0]))
            tkN = ticks(axN, [0, 0.002, 0.004, 0.006], [0, 200, 400, 600], xfmt="{:.1%}", size=16)
            lbN = ax_labels(axN, "local total strain", "local stress [MPa]", size=18)
            ee = np.linspace(0, 0.006, 300)
            ss = np.array([E * e if E * e <= 357 else 0.0 for e in ee])
            for i, e in enumerate(ee):
                if E * e > 357:
                    # solve sigma/E + ep = e on the true curve (plateau region)
                    lo, hi = 357.0, 400.0
                    for _ in range(40):
                        mid = 0.5 * (lo + hi)
                        epl = e - mid / E
                        if float(hh(np.array([max(epl, 0.0)]))[0][0]) > mid:
                            lo = mid
                        else:
                            hi = mid
                    ss[i] = 0.5 * (lo + hi)
            mat = data_curve(axN, ee, ss, C_TRUE, 4)
            C2 = c4["elastic_peak_at_17"] ** 2 / E
            en = np.linspace(C2 / 600, 0.006, 200)
            neub = data_curve(axN, en, C2 / en, C_Y, 3, dashed=True)
            pel = Dot(axN.c2p(c4["elastic_peak_at_17"] / E, c4["elastic_peak_at_17"]), color=INK, radius=0.07)
            pelt = T("elastic 558", 17, INK).next_to(pel, LEFT, buff=0.1)
            sN = 357.0 + 9.0 * (c4["neuber_ep_at_17"] / 0.015)
            pN = Dot(axN.c2p(sN / E + c4["neuber_ep_at_17"], sN), color=C_Y, radius=0.08)
            pNt = VGroup(T("Neuber", 18, C_Y, weight=BOLD), M(r"\varepsilon_p=0.24\,\%", size=26, color=C_Y)).arrange(DOWN, buff=0.04)
            pNt.next_to(pN, UR, buff=0.12).shift(DOWN * 0.05)
            sF = c4["where"]["vm"]
            pF = Dot(axN.c2p(sF / E + c4["eb_at_17"], sF), color=C_YIELD, radius=0.08)
            pFt = VGroup(T("FE", 18, C_YIELD, weight=BOLD), M(r"\varepsilon_p=0.18\,\%", size=26, color=C_YIELD)).arrange(DOWN, buff=0.04)
            pFt.next_to(pF, DOWN, buff=0.3)
            nf = M(r"\sigma\,\varepsilon=\frac{(K_t\,S)^2}{E}", size=32, color=C_Y).move_to(axN.c2p(0.0052, 545))
            self.play(FadeOut(fg), Create(axN), FadeIn(tkN), FadeIn(lbN), run_time=0.8)
            self.play(Create(mat), FadeIn(pel), FadeIn(pelt), run_time=0.8)
            self.play(Create(neub), FadeIn(nf), run_time=1.0)
            self.play(FadeIn(pN, scale=1.5), FadeIn(pNt), run_time=0.6)
            dN = Dot(ax.c2p(1.7, LG(c4["neuber_ep_at_17"])), color=C_Y, radius=0.08)
            dNt = T("Neuber 0.24 %", 18, C_Y).move_to(ax.c2p(1.2, LG(0.0007)))
            dNl = Line(dNt.get_right() + RIGHT * 0.05, dN.get_center(), color=C_Y, stroke_width=1.5, buff=0.08)
            self.play(FadeIn(pF, scale=1.5), FadeIn(pFt), FadeIn(dN), FadeIn(dNt), Create(dNl), run_time=0.7)
            self.until("f4", "At a smooth notch")
            nxt = VGroup(T("Next check at this notch:", 22, INK), T("fatigue", 24, C_BAD, weight=BOLD)).arrange(RIGHT, buff=0.15)
            nxt.to_edge(DOWN, buff=0.3).shift(RIGHT * 3.3)
            self.until("f4", "Fatigue at that notch")
            self.play(FadeIn(nxt, shift=0.1 * UP), run_time=0.7)
        self.wait(0.6)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.8)
