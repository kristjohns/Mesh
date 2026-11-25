import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "fatigue_fea"))
from common import *
from fem.material import chaboche_cyclic_curve
from fem.fatigue import coffin_manson_life

E = 210000.0
SF, B, EF, C = 952.0, -0.089, 0.737, -0.668
CASES = [("hcf", "1", "±70 MPa · R = −1", C_EL, "elastic"),
         ("shake", "2", "0 → 140 MPa · R = 0", C_SD, "elastic shakedown"),
         ("lcf", "3", "±180 MPa · R = −1", C_AP, "alternating plasticity"),
         ("ratchet_m", "4", "0 → 285 MPa · R = 0", C_RT, "ratcheting")]


class S06FEA(SyncScene):
    scene_id = "s06_fea"

    def construct(self):
        self.tag = chapter_tag(5, "Finite element study")
        self.add(self.tag)
        self.data = {c[0]: load_npz(f"plate_{c[0]}.npz") for c in CASES}
        self.part_model()
        self.part_material()
        self.part_cases()
        self.part_peeq()
        self.part_catch()
        self.finish()

    def clear(self, rt=0.6):
        objs = [m for m in self.mobjects if m is not self.tag]
        if objs:
            self.play(*[FadeOut(m) for m in objs], run_time=rt)

    # ------------------------------------------------------------------ a
    def part_model(self):
        q = img(os.path.join(FRAMES, "quarter_mesh.png"), height=6.0).move_to(LEFT * 3.2 + DOWN * 0.55)
        XL, YL = (-3, 43), (-3, 103)
        P = lambda x, y: mm2pt(q, x, y, XL, YL)
        self.play(FadeIn(q, scale=0.97), run_time=1.2)
        # symmetry supports
        sup = VGroup()
        for y in np.linspace(14, 98, 7):
            tri = Triangle(color=CYAN, stroke_width=2).scale(0.09).rotate(-PI / 2).move_to(P(0, y) + LEFT * 0.13)
            sup.add(tri)
        for x in np.linspace(14, 38, 4):
            tri = Triangle(color=CYAN, stroke_width=2).scale(0.09).rotate(PI).move_to(P(x, 0) + DOWN * 0.13)
            sup.add(tri)
        loads = VGroup(*[Arrow(P(x, 100) + UP * 0.05, P(x, 100) + UP * 0.55, buff=0, color=AMBER, stroke_width=4,
                               max_tip_length_to_length_ratio=0.35) for x in np.linspace(3, 37, 5)])
        st = M("S(t)", 30, AMBER).next_to(loads, RIGHT, buff=0.15)
        sym = T("symmetry", 20, CYAN).next_to(P(0, 50), LEFT, buff=0.3)
        self.play(LaggedStart(*[FadeIn(s) for s in sup], lag_ratio=0.05), FadeIn(sym), run_time=1.0)
        self.play(LaggedStart(*[GrowArrow(a) for a in loads], lag_ratio=0.1), FadeIn(st), run_time=1.0)
        info = VGroup(
            T("plate 80 × 200 mm, hole Ø20 (d/W = 0.25)", 24, TXT),
            T("quarter model · plane stress", 24, TXT),
            T("1152 nine-node quadratic elements (Q9)", 24, TXT),
            T("4761 nodes · graded toward the hole", 24, TXT),
            M(r"K_t=3.25\;(\text{gross}),\;2.44\;(\text{net})", 30, AMBER),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to(RIGHT * 2.9 + UP * 0.6)
        for k, it in enumerate(info):
            self.play(FadeIn(it, shift=LEFT * 0.2), run_time=0.6)
            self.wait(1.2)
        # zoom on the graded mesh at the hole
        self.play(self.camera.frame.animate.scale(0.45).move_to(P(10, 8)), FadeOut(self.tag), run_time=1.5)
        self.wait(0.8)
        self.play(self.camera.frame.animate.scale(1 / 0.45).move_to(ORIGIN), FadeIn(self.tag), run_time=1.2)
        self.wait_until(self.end("a") - 0.2)

    # ------------------------------------------------------------------ b
    def part_material(self):
        self.cue("b")
        self.clear()
        ax = LogAxes((-5, np.log10(0.02)), (200, 470), x_length=6.0, y_length=4.2, ystep=50).move_to(LEFT * 3.5 + DOWN * 0.6)
        xt = ax.xlabels([-5, -4, -3, -2], 22)
        yt = VGroup(*[T(str(v), 18, MUTED).next_to(ax.c2p(-5, v), LEFT, buff=0.1) for v in [250, 350, 450]])
        xl = M(r"\text{plastic strain amplitude }\varepsilon_{pa}", 24, MUTED).next_to(xt, DOWN, buff=0.1)
        yl = M(r"\sigma_a\;[\mathrm{MPa}]", 26, MUTED).next_to(ax.c2p(-5, 470), UP, buff=0.1)
        ro = ax.plot(lambda le: 596.0 * (10 ** le) ** 0.076, x_range=[-5, np.log10(0.02)], color=WHITE_, stroke_width=6)
        ch = ax.plot(lambda le: chaboche_cyclic_curve(10 ** le, 250.0, [485000, 42400, 6840], [8000, 800, 80]),
                     x_range=[-5, np.log10(0.02)], color=AMBER, stroke_width=3)
        leg = VGroup(VGroup(Line(ORIGIN, RIGHT * 0.5, color=WHITE_, stroke_width=6), T("cyclic curve (target)", 20, TXT)).arrange(RIGHT, buff=0.15),
                     VGroup(Line(ORIGIN, RIGHT * 0.5, color=AMBER, stroke_width=3), T("Chaboche, 3 back-stresses", 20, AMBER)).arrange(RIGHT, buff=0.15)
                     ).arrange(DOWN, aligned_edge=LEFT, buff=0.12).next_to(ax.c2p(-4.9, 465), DOWN + RIGHT, buff=0.1)
        self.play(Create(ax), FadeIn(xt), FadeIn(yt), FadeIn(xl), FadeIn(yl), run_time=0.8)
        self.play(Create(ro), run_time=1.2)
        self.play(Create(ch), FadeIn(leg), run_time=1.2)
        eqs = VGroup(M(r"d\boldsymbol{\alpha}_i=\tfrac{2}{3}C_i\,d\boldsymbol{\varepsilon}_p-\gamma_i\,\boldsymbol{\alpha}_i\,dp", 32, TXT),
                     M(r"\sigma_0=250\,\mathrm{MPa},\;\gamma_i=8000,\,800,\,80", 26, MUTED)).arrange(DOWN, buff=0.15)
        eqs.next_to(ax, UP, buff=0.55).shift(RIGHT * 0.3)
        self.play(Write(eqs), run_time=1.6)
        # verification card
        v = load_npz("verification_ccx.npz")
        rows = [("quantity", "in-house", "CalculiX"),
                ("notch strain at +220", f"{v['inhouse_eyy'][21]*100:.3f} %", f"{0.6039:.3f} %"),
                ("top displacement", f"{v['inhouse_uy_top'][21]:.4f} mm", "0.1133 mm"),
                ("PEEQ after 1 cycle", f"{v['inhouse_peeq'][-1]*100:.2f} %", "2.18 %")]
        tbl = VGroup()
        for r in rows:
            cells = VGroup(T(r[0], 20, MUTED if r[0] != "quantity" else TXT, weight=BOLD if r[0] == "quantity" else NORMAL), T(r[1], 20, CYAN if r[1] != "in-house" else TXT, weight=BOLD),
                           T(r[2], 20, GREEN if r[2] != "CalculiX" else TXT, weight=BOLD))
            cells[0].set(width=min(cells[0].width, 3.0))
            tbl.add(cells)
        for r in tbl:
            r[0].move_to(ORIGIN, aligned_edge=LEFT)
            r[1].move_to(RIGHT * 3.6)
            r[2].move_to(RIGHT * 5.3)
        tbl.arrange(DOWN, buff=0.25)
        for r in tbl:
            r[0].align_to(tbl, LEFT)
        box_t = T("verification: same mesh, cyclic EPP problem", 22, TXT, weight=BOLD)
        vt = VGroup(box_t, tbl).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        vbox = card(vt.width + 0.6, vt.height + 0.6).move_to(vt)
        vg = VGroup(vbox, vt).move_to(RIGHT * 3.4 + DOWN * 0.3)
        extra = VGroup(T("implicit return mapping + consistent tangent", 20, MUTED),
                       T("tangent check vs finite differences: 3·10⁻¹¹", 20, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.1).next_to(vg, DOWN, buff=0.25)
        self.wait_until(self.start("b") + self.dur("b") * 0.55)
        self.play(FadeIn(vg, shift=LEFT * 0.2), run_time=1.0)
        self.play(FadeIn(extra), run_time=0.8)
        self.wait_until(self.end("b") - 0.2)

    # ------------------------------------------------------------------ c - h
    def make_panel(self, case, num, load, col, regime, center):
        d = self.data[case]
        tr = ValueTracker(0)
        fe = FrameSeq(frames(f"fea_{case}_vm"), tr, height=2.6)
        e = d["T_root_eyy"] * 100
        s = d["T_root_syy"]
        lo, hi = min(e.min(), 0.0), max(e.max(), 0.05)
        pad = 0.08 * (hi - lo)
        ax = Axes(x_range=[lo - pad, hi + pad, (hi - lo) / 2], y_range=[-420, 420, 210], x_length=3.4, y_length=2.2,
                  axis_config={"color": GRID, "stroke_width": 1.5, "include_ticks": False}, tips=False)
        xl = T(f"ε  {lo:.2f} … {hi:.2f} %", 16, MUTED).next_to(ax, DOWN, buff=0.08)
        yl = M(r"\sigma_{yy}", 22, MUTED).next_to(ax.y_axis.get_top(), RIGHT, buff=0.05)
        head = VGroup(T(f"CASE {num}", 22, col, weight=BOLD), T(load, 20, TXT)).arrange(RIGHT, buff=0.25)
        body = Group(fe, VGroup(ax, xl, yl)).arrange(RIGHT, buff=0.3)
        grp = Group(head, body).arrange(DOWN, buff=0.15)
        frame = card(6.9, 3.4).move_to(grp)
        frame.set_stroke(col, 1.5)
        G = Group(frame, grp).move_to(center)
        reg = T(regime, 20, col, weight=BOLD).next_to(frame.get_bottom(), UP, buff=0.12).align_to(ax, LEFT)
        n_all = len(e)
        def loop_upd():
            k = int(np.clip(round(tr.get_value()), 1, n_all - 1))
            pts = [ax.c2p(e[i], s[i]) for i in range(0, k + 1)]
            m = VMobject().set_points_as_corners(pts).set_stroke(col, 3)
            return m
        loop = always_redraw(loop_upd)
        dot = always_redraw(lambda: Dot(ax.c2p(e[int(np.clip(round(tr.get_value()), 0, n_all - 1))],
                                               s[int(np.clip(round(tr.get_value()), 0, n_all - 1))]), radius=0.06, color=WHITE_))
        return dict(G=G, tr=tr, fe=fe, ax=ax, loop=loop, dot=dot, reg=reg, frame=frame, e=e, s=s, n=n_all)

    def part_cases(self):
        self.cue("c")
        self.clear()
        centers = [LEFT * 3.55 + UP * 1.35, RIGHT * 3.55 + UP * 1.35, LEFT * 3.55 + DOWN * 2.15, RIGHT * 3.55 + DOWN * 2.15]
        self.panels = []
        for (case, num, load, col, regime), c in zip(CASES, centers):
            p = self.make_panel(case, num, load, col, regime, c)
            self.panels.append(p)
        self.play(LaggedStart(*[FadeIn(p["G"], shift=UP * 0.15) for p in self.panels], lag_ratio=0.15), run_time=1.6)
        for p in self.panels:
            self.add(p["tr"], p["loop"], p["dot"])

        def focus(k):
            anims = []
            for j, p in enumerate(self.panels):
                anims.append(p["G"].animate.set_opacity(1.0 if j == k else 0.35))
            return anims

        def callout(lines, k):
            g = VGroup(*[T(t, 20, c, weight=w) for t, c, w in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
            p = self.panels[k]
            bg = card(g.width + 0.4, g.height + 0.3, color=BG, opacity=0.92).move_to(g)
            G = VGroup(bg, g)
            # place over the opposite column
            target = RIGHT * 3.55 if k in (0, 2) else LEFT * 3.55
            yc = p["G"].get_center()[1]
            G.move_to(target + UP * yc)
            return G

        dd = {c[0]: self.data[c[0]] for c in CASES}
        # ---- d: case 1
        self.cue("d")
        self.play(*focus(0), run_time=0.6)
        p = self.panels[0]
        self.play(p["tr"].animate.set_value(119), run_time=10.0, rate_func=linear)
        pk = dd["hcf"]["T_root_syy"].max()
        N1 = coffin_manson_life(dd["hcf"]["T_root_eyy"].max(), E, SF, B, EF, C)
        co = callout([(f"peak at hole: {pk:.0f} MPa < 250 MPa", TXT, NORMAL), ("everything elastic · PEEQ = 0", C_EL, BOLD),
                      (f"strain–life: N ≈ {N1/1e6:.1f} million → HCF", TXT, NORMAL)], 0)
        self.play(FadeIn(co), run_time=0.6)
        self.wait_until(self.end("d") - 0.4)
        self.play(FadeOut(co), run_time=0.4)
        # ---- e: case 2
        self.cue("e")
        self.play(*focus(1), run_time=0.6)
        p = self.panels[1]
        self.play(p["tr"].animate.set_value(20), run_time=5.0, rate_func=linear)
        co = callout([("elastic peak would be 455 MPa", TXT, NORMAL), ("→ notch yields in cycle 1", AMBER, BOLD),
                      ("unloading leaves a residual stress", TXT, NORMAL)], 1)
        self.play(FadeIn(co), run_time=0.6)
        self.play(p["tr"].animate.set_value(119), run_time=10.0, rate_func=linear)
        co2 = callout([("from cycle 2: purely elastic", C_SD, BOLD), ("elastic shakedown", C_SD, BOLD),
                       ("PEEQ: one step, then flat", TXT, NORMAL)], 1)
        self.play(FadeOut(co), FadeIn(co2), run_time=0.6)
        self.wait_until(self.end("e") - 0.3)
        # ---- f: local mean stress
        self.cue("f")
        sh = dd["shake"]
        last = sh["T_cycle"] == sh["T_cycle"].max()
        smax, smin = sh["T_root_syy"][last].max(), sh["T_root_syy"][last].min()
        sm = 0.5 * (smax + smin)
        ax = p["ax"]
        mline = DashedLine(ax.c2p(ax.x_range[0], sm), ax.c2p(ax.x_range[1], sm), color=PINK, stroke_width=2.5)
        mt = T(f"σm = +{sm:.0f} MPa", 20, PINK, weight=BOLD).next_to(ax.c2p(ax.x_range[1], sm), UP, buff=0.05).shift(LEFT * 0.6)
        self.play(Create(mline), FadeIn(mt), run_time=0.8)
        ea = 0.5 * (sh["T_root_eyy"][last].max() - sh["T_root_eyy"][last].min())
        n0 = coffin_manson_life(ea, E, SF, B, EF, C)
        nm = coffin_manson_life(ea, E, SF, B, EF, C, sigma_m=sm, method="morrow")
        ns = coffin_manson_life(ea, E, SF, B, EF, C, method="swt", smax=smax)
        co3 = callout([(f"no mean stress: N ≈ {n0/1e6:.1f} M", TXT, NORMAL), (f"Morrow: N ≈ {nm/1e6:.1f} M", TXT, NORMAL),
                       (f"SWT: N ≈ {ns/1e6:.2f} M", TXT, NORMAL), ("shakedown removes plastic cycling, not fatigue", PINK, BOLD)], 1)
        self.play(FadeOut(co2), FadeIn(co3), run_time=0.6)
        self.wait_until(self.end("f") - 0.4)
        self.play(FadeOut(co3), run_time=0.4)
        # ---- g: case 3
        self.cue("g")
        self.play(*focus(2), run_time=0.6)
        p = self.panels[2]
        co = callout([("elastic range ≈ 1170 MPa  >  2 × yield", TXT, NORMAL), ("→ yield reverses every half cycle", AMBER, BOLD)], 2)
        self.play(FadeIn(co), run_time=0.6)
        self.play(p["tr"].animate.set_value(119), run_time=13.0, rate_func=linear)
        lc = dd["lcf"]
        last = lc["T_cycle"] == lc["T_cycle"].max()
        ea = 0.5 * (lc["T_root_eyy"][last].max() - lc["T_root_eyy"][last].min())
        N3 = coffin_manson_life(ea, E, SF, B, EF, C)
        co2 = callout([("closed loop: alternating plasticity", C_AP, BOLD), (f"ε_a = {ea*100:.2f} %  →  N ≈ {N3:,.0f} cycles", TXT, NORMAL),
                       ("low-cycle fatigue", C_AP, BOLD)], 2)
        self.play(FadeOut(co), FadeIn(co2), run_time=0.6)
        self.wait_until(self.end("g") - 0.4)
        self.play(FadeOut(co2), run_time=0.4)
        # ---- h: case 4
        self.cue("h")
        self.play(*focus(3), run_time=0.6)
        p = self.panels[3]
        rm = dd["ratchet_m"]
        co = callout([("net section yields, high mean load", TXT, NORMAL), ("the loop does not close: it walks", C_RT, BOLD)], 3)
        self.play(FadeIn(co), run_time=0.6)
        self.play(p["tr"].animate.set_value(p["n"] - 1), run_time=11.0, rate_func=linear)
        eoc = rm["T_uy_top"][rm["T_end_of_cycle"]]
        co2 = callout([("ratcheting", C_RT, BOLD), (f"plate end: +{(eoc[-1]-eoc[0])*1000:.1f} µm over {len(eoc)-1} cycles", TXT, NORMAL)], 3)
        self.play(FadeOut(co), FadeIn(co2), run_time=0.6)
        self.wait_until(self.end("h") - 0.3)
        self.play(FadeOut(co2), *[pp["G"].animate.set_opacity(1.0) for pp in self.panels], run_time=0.3)

    # ------------------------------------------------------------------ i
    def part_peeq(self):
        self.cue("i")
        for p in self.panels:
            p["loop"].clear_updaters(); p["dot"].clear_updaters(); p["fe"].clear_updaters()
        self.clear()
        ax = Axes(x_range=[0, 12, 2], y_range=[0, 10, 2], x_length=8.4, y_length=5.0,
                  axis_config={"color": GRID, "stroke_width": 2, "include_ticks": True, "tick_size": 0.05}, tips=False).move_to(LEFT * 1.3 + DOWN * 0.45)
        xt = VGroup(*[T(str(v), 20, MUTED).next_to(ax.c2p(v, 0), DOWN, buff=0.1) for v in range(0, 13, 2)])
        yt = VGroup(*[T(f"{v}", 20, MUTED).next_to(ax.c2p(0, v), LEFT, buff=0.1) for v in range(0, 11, 2)])
        xl = T("cycle", 22, MUTED).next_to(xt, DOWN, buff=0.1)
        yl = T("PEEQ at the notch root [%]", 22, MUTED).next_to(ax.c2p(0, 10), UP, buff=0.12).align_to(ax, LEFT)
        head = T("accumulated plastic strain at the notch root", 30, TXT, weight=BOLD).to_edge(UP, buff=0.85)
        self.play(FadeIn(head), Create(ax), FadeIn(xt), FadeIn(yt), FadeIn(xl), FadeIn(yl), run_time=0.8)
        curves, labs = [], []
        for case, num, load, col, regime in CASES:
            d = self.data[case]
            root = int(d["probes"][0])
            pe = np.concatenate([[0.0], d["EOC_peeq"][:, root] * 100])
            cyc = np.arange(len(pe))
            pts = [ax.c2p(c, min(v, 10)) for c, v in zip(cyc, pe)]
            # within-cycle steps for a staircase look
            T_ = d["T_root_peeq"] * 100
            tc = d["T_tc"]
            fine = [ax.c2p(0, 0)] + [ax.c2p(t, min(v, 10)) for t, v in zip(tc, T_)]
            cv = VMobject().set_points_as_corners(fine).set_stroke(col, 5)
            curves.append(cv)
            lb = T(f"{num} · {regime}", 22, col, weight=BOLD).next_to(fine[-1], RIGHT, buff=0.15)
            if case == "hcf":
                lb.next_to(fine[-1], UP, buff=0.25)
            labs.append(lb)
        for k in range(4):
            self.play(Create(curves[k]), FadeIn(labs[k]), run_time=1.6, rate_func=linear)
        self.wait_until(self.end("i") - 0.2)

    # ------------------------------------------------------------------ j
    def part_catch(self):
        self.cue("j")
        self.clear()
        lc, rm = self.data["lcf"], self.data["ratchet_m"]
        def loops_panel(d, col, title, sub, center, xr):
            ax = Axes(x_range=[xr[0], xr[1], (xr[1] - xr[0]) / 4], y_range=[-420, 420, 210], x_length=5.6, y_length=3.8,
                      axis_config={"color": GRID, "stroke_width": 2, "include_ticks": False}, tips=False).move_to(center)
            e, s = d["T_root_eyy"] * 100, d["T_root_syy"]
            lp = VMobject().set_points_as_corners([ax.c2p(x, y) for x, y in zip(e, s)]).set_stroke(col, 2.5)
            t = T(title, 28, col, weight=BOLD).next_to(ax, UP, buff=0.3)
            st_ = T(sub, 22, TXT).next_to(ax, DOWN, buff=0.35)
            xl = T(f"strain {xr[0]:.1f} … {xr[1]:.1f} %", 18, MUTED).next_to(ax, DOWN, buff=0.06)
            return VGroup(ax, t, st_, xl), lp
        g1, l1 = loops_panel(lc, C_AP, "alternating plasticity", "closed strain cycle → fatigue crack initiation", LEFT * 3.5 + UP * 0.1, (-0.5, 0.5))
        g2, l2 = loops_panel(rm, C_RT, "ratcheting", "net strain grows → ductility exhaustion", RIGHT * 3.5 + UP * 0.1, (0.0, 3.6))
        same = T("similar PEEQ trend  ≠  same problem", 30, TXT, weight=BOLD).to_edge(UP, buff=0.85)
        self.play(FadeIn(same), FadeIn(g1), FadeIn(g2), run_time=1.0)
        self.play(Create(l1), Create(l2), run_time=6.0, rate_func=linear)
        self.wait_until(self.end("j") - 0.2)
