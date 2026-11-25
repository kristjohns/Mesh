import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "fatigue_fea"))
from common import *
from fem.material import J2Material
from fem.matpoint import uniaxial, triangle_wave
from fem.fatigue import coffin_manson_life, neuber, glinka

E = 210000.0
KP, NP = 596.0, 0.076
SF, B, EF, C = 952.0, -0.089, 0.737, -0.668
KT, SA = 3.249, 180.0


def ro_eps(s):
    return s / E + (np.abs(s) / KP) ** (1 / NP) * np.sign(s)


class S05LCF(SyncScene):
    scene_id = "s05_lcf"

    def construct(self):
        self.tag = chapter_tag(4, "Low-cycle fatigue")
        self.add(self.tag)
        self.part_title()
        self.part_cyclic()
        self.part_life()
        self.part_notch()
        self.part_other()
        self.part_codes()
        self.finish()

    def clear(self, rt=0.6):
        objs = [m for m in self.mobjects if m is not self.tag]
        if objs:
            self.play(*[FadeOut(m) for m in objs], run_time=rt)

    def part_title(self):
        t = T("LOW-CYCLE FATIGUE", 72, AMBER, weight=BOLD)
        s = T("where strain takes over", 32, MUTED).next_to(t, DOWN, buff=0.3)
        self.play(FadeIn(t, scale=1.1), FadeIn(s), run_time=1.0)
        self.wait_until(self.end("a") - 0.1)
        self.play(FadeOut(VGroup(t, s)), run_time=0.4)

    # ------------------------------------------------------------------ b, c
    def part_cyclic(self):
        self.cue("b")
        hard = J2Material(E=E, nu=0.3, sigma0=180.0, C=[40000.0], gamma=[250.0], Q_inf=130.0, b_iso=6.0)
        soft = J2Material(E=E, nu=0.3, sigma0=420.0, C=[40000.0], gamma=[250.0], Q_inf=-120.0, b_iso=6.0)
        h = triangle_wave(0.006, 8, nper_quarter=40)
        rh = uniaxial(hard, h, "strain")
        rs = uniaxial(soft, h, "strain")
        def panel(xc, title, col, r):
            ax = Axes(x_range=[-0.7, 0.7, 0.35], y_range=[-560, 560, 280], x_length=5.2, y_length=4.2,
                      axis_config={"color": GRID, "stroke_width": 2, "include_ticks": False}, tips=False).move_to([xc, -0.4, 0])
            tt = T(title, 26, col, weight=BOLD).next_to(ax, UP, buff=0.25)
            xl = M(r"\varepsilon", 28, MUTED).next_to(ax.x_axis.get_right(), DOWN, buff=0.1)
            yl = M(r"\sigma", 28, MUTED).next_to(ax.y_axis.get_top(), LEFT, buff=0.1)
            loops = VGroup()
            n1 = 160
            for k in range(8):
                sl = slice(k * n1, (k + 1) * n1 + 1)
                c = interpolate_color(ManimColor(MUTED), ManimColor(col), (k + 1) / 8)
                loops.add(loop_curve(ax, r["eps11"][sl] * 100, r["sig11"][sl], c, 2.2 if k < 7 else 4))
            return VGroup(ax, tt, xl, yl), loops
        g1, l1 = panel(-3.4, "cyclic hardening (annealed, soft)", GREEN, rh)
        g2, l2 = panel(3.4, "cyclic softening (cold-worked, HSS)", RED, rs)
        self.play(FadeIn(g1), FadeIn(g2), run_time=0.8)
        self.play(LaggedStart(*[Create(l) for l in l1], lag_ratio=0.6), LaggedStart(*[Create(l) for l in l2], lag_ratio=0.6), run_time=7.0)
        st = T("loops stabilise after a while", 24, MUTED).to_edge(DOWN, buff=0.4)
        self.play(FadeIn(st), run_time=0.6)
        # cyclic stress-strain curve from stable loop tips
        self.wait_until(self.start("b") + self.dur("b") * 0.55)
        self.play(FadeOut(VGroup(g1, l1, g2, l2, st)), run_time=0.6)
        U = load_npz("uniaxial_studies.npz")
        ax = Axes(x_range=[-0.9, 0.9, 0.3], y_range=[-480, 480, 160], x_length=7.0, y_length=5.3,
                  axis_config={"color": GRID, "stroke_width": 2, "include_ticks": False}, tips=False).move_to(LEFT * 2.6 + DOWN * 0.4)
        xl = M(r"\varepsilon\;[\%]", 28, MUTED).next_to(ax.x_axis.get_right(), DOWN, buff=0.12)
        yl = M(r"\sigma\;[\mathrm{MPa}]", 28, MUTED).next_to(ax.y_axis.get_top(), RIGHT, buff=0.12)
        self.play(Create(ax), FadeIn(xl), FadeIn(yl), run_time=0.6)
        loops = VGroup()
        tips = VGroup()
        n1 = 320
        for key, col in [("loop_20", CYAN), ("loop_40", GREEN), ("loop_80", AMBER)]:
            e, s = U[f"{key}_eps"][-n1 - 1:] * 100, U[f"{key}_sig"][-n1 - 1:]
            loops.add(loop_curve(ax, e, s, col, 3))
            k = np.argmax(e)
            tips.add(Dot(ax.c2p(e[k], s[k]), radius=0.08, color=WHITE_))
        self.play(LaggedStart(*[Create(l) for l in loops], lag_ratio=0.4), run_time=2.4)
        self.play(FadeIn(tips, scale=2), run_time=0.6)
        ss = np.linspace(0, 405, 200)
        cyc = VMobject().set_points_smoothly([ax.c2p(ro_eps(x) * 100, x) for x in ss]).set_stroke(WHITE_, 5)
        eq = M(r"\varepsilon_a=\frac{\sigma_a}{E}+\left(\frac{\sigma_a}{K'}\right)^{1/n'}", 40, TXT).move_to(RIGHT * 3.9 + UP * 1.6)
        vals = T("K′ = 596 MPa,  n′ = 0.076", 24, MUTED).next_to(eq, DOWN, buff=0.25)
        lab = T("cyclic stress–strain curve", 26, WHITE_, weight=BOLD).next_to(eq, UP, buff=0.3)
        self.play(Create(cyc), FadeIn(lab), run_time=1.6)
        self.play(Write(eq), FadeIn(vals), run_time=1.4)
        self.wait_until(self.end("b") - 0.2)
        # ---- c: Masing
        self.cue("c")
        self.play(FadeOut(loops[0]), FadeOut(loops[1]), FadeOut(tips[:2]), run_time=0.5)
        e8 = U["loop_80_eps"][-n1 - 1:] * 100
        s8 = U["loop_80_sig"][-n1 - 1:]
        kmin = np.argmin(e8)
        e0, s0 = e8[kmin], s8[kmin]
        ds = np.linspace(0, 2 * 405, 200)
        branch = VMobject().set_points_smoothly([ax.c2p(e0 + (d / E + 2 * (d / (2 * KP)) ** (1 / NP)) * 100, s0 + d) for d in ds]).set_stroke(PINK, 5)
        cyc_copy = cyc.copy()
        self.play(Transform(cyc_copy, branch), run_time=2.0)
        meq = M(r"\frac{\Delta\varepsilon}{2}=\frac{\Delta\sigma}{2E}+\left(\frac{\Delta\sigma}{2K'}\right)^{1/n'}", 34, PINK).next_to(vals, DOWN, buff=0.55)
        mt = T("Masing: branch = cyclic curve × 2", 24, PINK, weight=BOLD).next_to(meq, DOWN, buff=0.25)
        self.play(Write(meq), FadeIn(mt), run_time=1.4)
        self.wait_until(self.end("c") - 0.2)

    # ------------------------------------------------------------------ d, e
    def part_life(self):
        self.cue("d")
        self.clear()
        eq = M(r"\varepsilon_a=", r"\frac{\sigma_f'}{E}(2N_f)^{b}", r"+", r"\varepsilon_f'(2N_f)^{c}", size=54).move_to(UP * 2.1)
        eq[1].set_color(CYAN); eq[3].set_color(AMBER)
        self.play(Write(eq), run_time=1.6)
        b1 = Brace(eq[1], DOWN, color=CYAN); b1t = T("elastic (Basquin)", 22, CYAN).next_to(b1, DOWN, buff=0.1)
        b2 = Brace(eq[3], DOWN, color=AMBER); b2t = T("plastic (Coffin–Manson)", 22, AMBER).next_to(b2, DOWN, buff=0.1)
        self.play(GrowFromCenter(b1), FadeIn(b1t), run_time=0.7)
        self.play(GrowFromCenter(b2), FadeIn(b2t), run_time=0.7)
        params = VGroup(M(r"\sigma_f'=952\,\mathrm{MPa}", 30), M(r"b=-0.089", 30), M(r"\varepsilon_f'=0.737", 30), M(r"c=-0.668", 30)
                        ).arrange(RIGHT, buff=0.6).move_to(DOWN * 0.3)
        pt = T("S355-type steel (representative published values, illustrative)", 20, MUTED).next_to(params, DOWN, buff=0.2)
        self.wait_until(self.start("d") + self.dur("d") * 0.55)
        self.play(FadeIn(params, shift=UP * 0.1), FadeIn(pt), run_time=1.0)
        self.wait_until(self.end("d") - 0.2)
        # ---- e: mean stress
        self.cue("e")
        self.play(FadeOut(VGroup(b1, b1t, b2, b2t, params, pt)), eq.animate.scale(0.75).to_edge(UP, buff=0.9), run_time=0.8)
        mo = VGroup(T("Morrow", 26, GREEN, weight=BOLD),
                    M(r"\varepsilon_a=\frac{\sigma_f'-\sigma_m}{E}(2N_f)^{b}+\varepsilon_f'(2N_f)^{c}", 30, TXT)).arrange(DOWN, buff=0.15)
        sw = VGroup(T("Smith–Watson–Topper", 26, PINK, weight=BOLD),
                    M(r"\sigma_{\max}\,\varepsilon_a=\frac{\sigma_f'^2}{E}(2N_f)^{2b}+\sigma_f'\varepsilon_f'(2N_f)^{b+c}", 30, TXT)).arrange(DOWN, buff=0.15)
        mo.move_to(LEFT * 3.5 + DOWN * 0.3)
        sw.move_to(RIGHT * 3.4 + DOWN * 0.3)
        self.play(FadeIn(mo, shift=UP * 0.2), run_time=1.0)
        self.wait_until(self.start("e") + self.dur("e") * 0.5)
        self.play(FadeIn(sw, shift=UP * 0.2), run_time=1.0)
        hint = T("tensile mean stress → shorter life, mostly in the long-life (elastic) regime", 22, MUTED).to_edge(DOWN, buff=0.7)
        self.play(FadeIn(hint), run_time=0.6)
        self.wait_until(self.end("e") - 0.2)

    # ------------------------------------------------------------------ f, g
    def part_notch(self):
        self.cue("f")
        self.clear()
        ax = Axes(x_range=[0, 0.6, 0.1], y_range=[0, 650, 100], x_length=7.2, y_length=5.4,
                  axis_config={"color": GRID, "stroke_width": 2, "include_ticks": True, "tick_size": 0.05}, tips=False
                  ).move_to(LEFT * 2.5 + DOWN * 0.35)
        xt = VGroup(*[T(f"{v:.1f}", 18, MUTED).next_to(ax.c2p(v, 0), DOWN, buff=0.1) for v in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]])
        yt = VGroup(*[T(str(v), 18, MUTED).next_to(ax.c2p(0, v), LEFT, buff=0.1) for v in [200, 400, 600]])
        xl = M(r"\varepsilon_a\;[\%]", 28, MUTED).next_to(xt, DOWN, buff=0.12)
        yl = M(r"\sigma_a\;[\mathrm{MPa}]", 28, MUTED).next_to(ax.c2p(0, 650), UP, buff=0.12)
        self.play(Create(ax), FadeIn(xt), FadeIn(yt), FadeIn(xl), FadeIn(yl), run_time=0.8)
        ss = np.linspace(0, 470, 200)
        cyc = VMobject().set_points_smoothly([ax.c2p(ro_eps(x) * 100, x) for x in ss]).set_stroke(WHITE_, 4)
        cl = T("cyclic curve", 20, WHITE_).next_to(ax.c2p(0.55, 400), DOWN, buff=0.1)
        sel = KT * SA
        eline = Line(ax.c2p(0, 0), ax.c2p(sel / E * 100, sel), color=CYAN, stroke_width=3)
        ep = Dot(ax.c2p(sel / E * 100, sel), radius=0.08, color=CYAN)
        epl = M(r"K_t S_a = 585", 26, CYAN).next_to(ep, LEFT, buff=0.12)
        self.play(Create(cyc), FadeIn(cl), run_time=1.0)
        self.play(Create(eline), FadeIn(ep), FadeIn(epl), run_time=1.0)
        # Neuber hyperbola
        Cn = sel ** 2 / E
        hyp = ax.plot(lambda e: Cn / (e / 100), x_range=[0.252, 0.6], color=AMBER, stroke_width=4)
        neq = M(r"\sigma\,\varepsilon=\frac{(K_t S)^2}{E}", 36, AMBER).move_to(RIGHT * 3.9 + UP * 1.9)
        nt = T("Neuber", 26, AMBER, weight=BOLD).next_to(neq, UP, buff=0.15)
        self.wait_until(self.start("f") + 5.5)
        self.play(Create(hyp), Write(neq), FadeIn(nt), run_time=1.6)
        sN, eN = neuber(KT, SA, E, KP, NP)
        sG, eG = glinka(KT, SA, E, KP, NP)
        pN = Dot(ax.c2p(eN * 100, sN), radius=0.1, color=AMBER)
        self.play(FadeIn(pN, scale=2), run_time=0.6)
        # Glinka: energy areas
        self.wait_until(self.start("f") + 12.5)
        tri = Polygon(ax.c2p(0, 0), ax.c2p(sel / E * 100, sel), ax.c2p(sel / E * 100, 0), fill_color=CYAN, fill_opacity=0.18, stroke_width=0)
        sg = np.linspace(0, sG, 80)
        under = Polygon(ax.c2p(0, 0), *[ax.c2p(ro_eps(x) * 100, x) for x in sg], ax.c2p(eG * 100, 0),
                        fill_color=GREEN, fill_opacity=0.25, stroke_width=0)
        geq = M(r"\int_0^{\varepsilon}\sigma\,d\varepsilon=\frac{(K_t S)^2}{2E}", 34, GREEN).next_to(neq, DOWN, buff=0.6)
        gt = T("Glinka (energy density)", 26, GREEN, weight=BOLD).next_to(geq, UP, buff=0.15)
        pG = Dot(ax.c2p(eG * 100, sG), radius=0.1, color=GREEN)
        self.play(FadeIn(tri), FadeIn(under), Write(geq), FadeIn(gt), run_time=1.6)
        self.play(FadeIn(pG, scale=2), run_time=0.6)
        vals = VGroup(T(f"Neuber: ε_a = {eN*100:.3f} %", 22, AMBER), T(f"Glinka: ε_a = {eG*100:.3f} %", 22, GREEN)
                      ).arrange(DOWN, aligned_edge=LEFT, buff=0.12).next_to(geq, DOWN, buff=0.5)
        self.wait_until(self.start("f") + self.dur("f") * 0.82)
        self.play(FadeIn(vals), run_time=0.8)
        self.wait_until(self.end("f") - 0.2)
        # ---- g: FE result
        self.cue("g")
        d = load_npz("plate_lcf.npz")
        last = d["T_cycle"] == d["T_cycle"].max()
        e_fe, s_fe = d["T_root_eyy"][last], d["T_root_syy"][last]
        ea = 0.5 * (e_fe.max() - e_fe.min())
        sa = 0.5 * (s_fe.max() - s_fe.min())
        loop = loop_curve(ax, np.abs(e_fe) * 100, np.abs(s_fe), RED, 2)
        loop.set_stroke(opacity=0.0)
        pF = Dot(ax.c2p(ea * 100, sa), radius=0.12, color=RED)
        fl = T(f"FE: ε_a = {ea*100:.3f} %", 24, RED, weight=BOLD).next_to(vals, DOWN, buff=0.15, aligned_edge=LEFT)
        self.play(FadeIn(pF, scale=2.5), FadeIn(fl), Flash(pF, color=RED), run_time=1.2)
        br = T("Glinka  <  FE  <  Neuber", 30, TXT, weight=BOLD).to_edge(DOWN, buff=0.35).shift(RIGHT * 3.6)
        self.play(FadeIn(br, shift=UP * 0.1), run_time=0.8)
        # life on the strain-life curve
        self.wait_until(self.start("g") + self.dur("g") * 0.62)
        self.play(*[FadeOut(m) for m in self.mobjects if m is not self.tag], run_time=0.6)
        la = LogAxes((1, 7), (-3.3, -1.3), x_length=8.6, y_length=4.6).move_to(LEFT * 0.6 + DOWN * 0.4)
        xt = la.xlabels(range(1, 8), 22)
        yt = la.ylabels([-3, -2], 22)
        xl = M(r"\text{cycles to failure }N_f", 26, MUTED).next_to(xt, DOWN, buff=0.1)
        tot = lambda lN: np.log10(SF / E * (2 * 10 ** lN) ** B + EF * (2 * 10 ** lN) ** C)
        curve = la.plot(tot, x_range=[1, 7], color=WHITE_, stroke_width=4)
        self.play(Create(la), FadeIn(xt), FadeIn(yt), FadeIn(xl), Create(curve), run_time=1.2)
        rows = []
        for lab, e_, col in [("Glinka", eG, GREEN), ("FE", ea, RED), ("Neuber", eN, AMBER)]:
            N = coffin_manson_life(e_, E, SF, B, EF, C)
            x, y = np.log10(N), np.log10(e_)
            dot = Dot(la.c2p(x, y), radius=0.1, color=col)
            vline = DashedLine(la.c2p(x, y), la.c2p(x, -3.3), color=col, stroke_width=2)
            hline = DashedLine(la.c2p(1, y), la.c2p(x, y), color=col, stroke_width=2)
            rows.append((dot, vline, hline, T(f"{lab}: N ≈ {N:,.0f}", 24, col, weight=BOLD)))
        tbl = VGroup(*[r[3] for r in rows]).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to(RIGHT * 4.6 + UP * 1.6)
        for dot, vl, hl, t in rows:
            self.play(Create(hl), Create(vl), FadeIn(dot, scale=2), FadeIn(t), run_time=0.8)
        self.wait_until(self.end("g") - 0.2)

    # ------------------------------------------------------------------ h
    def part_other(self):
        self.cue("h")
        self.clear()
        c1 = VGroup(T("hysteresis energy", 26, AMBER, weight=BOLD),
                    M(r"\Delta W=\oint\sigma\,d\varepsilon,\qquad \Delta W\,N_f^{\,\alpha}=C", 32, TXT)).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        c2 = VGroup(T("Brown–Miller (critical plane)", 26, CYAN, weight=BOLD),
                    M(r"\frac{\Delta\gamma_{\max}}{2}+S\,\frac{\Delta\varepsilon_n}{2}=f(2N_f)", 32, TXT)).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        c3 = VGroup(T("Fatemi–Socie (non-proportional)", 26, PINK, weight=BOLD),
                    M(r"\frac{\Delta\gamma_{\max}}{2}\left(1+k\,\frac{\sigma_{n,\max}}{\sigma_y}\right)=g(2N_f)", 32, TXT)).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        grp = VGroup(c1, c2, c3).arrange(DOWN, aligned_edge=LEFT, buff=0.55).move_to(DOWN * 0.2)
        for c in grp:
            self.play(FadeIn(c, shift=RIGHT * 0.2), run_time=0.8)
            self.wait(1.6)
        self.wait_until(self.end("h") - 0.2)

    # ------------------------------------------------------------------ i
    def part_codes(self):
        self.cue("i")
        self.clear()
        head = T("How design codes package it", 32, TXT, weight=BOLD).to_edge(UP, buff=0.85)
        self.play(FadeIn(head), run_time=0.6)
        def box(title, col, lines, w=6.4):
            t = T(title, 24, col, weight=BOLD)
            body = VGroup(*lines).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
            g = VGroup(t, body).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
            r = card(w, g.height + 0.6).move_to(g)
            r.set_stroke(col, 1.5)
            return VGroup(r, g)
        a1 = box("ASME VIII-2 · elastic route", CYAN, [
            M(r"S_{alt}=K_e\,\frac{\Delta S_P}{2}", 32),
            M(r"K_e=\begin{cases}1 & \Delta S_n\le S_{PS}\\ 1+\frac{1-n}{n(m-1)}\left(\frac{\Delta S_n}{S_{PS}}-1\right) & \\ 1/n & \Delta S_n\ge m\,S_{PS}\end{cases}", 26),
            T("plasticity correction above the shakedown limit", 18, MUTED)])
        a2 = box("ASME VIII-2 · elastic-plastic route", AMBER, [
            M(r"\Delta\varepsilon_{eff}=\frac{\Delta S_P}{E}+\Delta\varepsilon_{peq}", 32),
            M(r"S_{alt}=\frac{E\,\Delta\varepsilon_{eff}}{2}\;\rightarrow\;\text{fatigue curve}", 28),
            T("Δε_peq from a cyclic elastic-plastic analysis", 18, MUTED)])
        a3 = box("DNV-RP-C203 · low-cycle fatigue", GREEN, [
            T("elastic hot-spot stress range × plasticity correction", 22, TXT),
            M(r"D_{total}=D_{LCF}+D_{HCF}", 32),
            T("low- and high-cycle damage are added", 18, MUTED)], w=6.4)
        a1.move_to(LEFT * 3.45 + UP * 0.35)
        a2.move_to(RIGHT * 3.45 + UP * 1.3)
        a3.move_to(RIGHT * 3.45 + DOWN * 2.05)
        self.play(FadeIn(a1, shift=UP * 0.2), run_time=1.0)
        self.wait_until(self.start("i") + self.dur("i") * 0.42)
        self.play(FadeIn(a2, shift=UP * 0.2), run_time=1.0)
        self.wait_until(self.start("i") + self.dur("i") * 0.74)
        self.play(FadeIn(a3, shift=UP * 0.2), run_time=1.0)
