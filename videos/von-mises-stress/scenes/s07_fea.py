"""Section 7 - real engineering application: finite element analysis of a subsea transition piece."""
from common import *  # noqa: F401,F403

FR = os.path.join(BUILD, "frames")
FEA = os.path.join(BUILD, "fea")
SUMM = json.load(open(os.path.join(ROOT, "assets", "fea", "summary.json")))
AXI = json.load(open(os.path.join(FEA, "axi.json")))


def panel_box(w, h, title=None):
    fr = RoundedRectangle(width=w, height=h, corner_radius=0.12, stroke_color=FAINT, stroke_width=1.5,
                          fill_color=PANEL, fill_opacity=0.88)
    if title:
        t = T(title, size=20, color=DIM).next_to(fr.get_corner(UL), DR, buff=0.15)
        return VGroup(fr, t)
    return VGroup(fr)


def model_tree():
    g = SUMM["geometry"]; ld = SUMM["loads"]; ms = SUMM["mesh"]
    rows = [("Model", "forged pipe-to-hub transition", INK),
            ("Material", "S355 · E = 210 GPa · ν = 0.3", INK),
            ("Geometry", f"OD 273.1 × 20 → hub OD 340 · R{g['fillet']:.0f} fillet", INK),
            ("Loads", f"N = {ld['N_MN']:.1f} MN · M = {ld['M_kNm']:.0f} kNm · T = {ld['T_kNm']:.0f} kNm", C_SHEAR),
            ("Mesh", f"{ms['tets'] / 1000:.0f}k quadratic tets · {ms['dofs'] / 1000:.0f}k DOF", INK),
            ("Analysis", "linear elastic, static", INK)]
    items = VGroup()
    for k, v, c in rows:
        items.add(VGroup(T(k, size=18, color=DIM), T(v, size=18, color=c)).arrange(DOWN, aligned_edge=LEFT, buff=0.06))
    items.arrange(DOWN, aligned_edge=LEFT, buff=0.18)
    box = panel_box(items.width + 0.5, items.height + 0.75, "MODEL TREE")
    items.move_to(box[0]).shift(DOWN * 0.15)
    return VGroup(box, items).to_corner(UL, buff=0.25)


class S07a_FEAModel(NScene):
    def construct(self):
        section_card(self, 7, "Finite element analysis in practice")
        seq = FrameSequence(os.path.join(FR, "fea_model"))
        anc = json.load(open(os.path.join(FR, "fea_model", "anchors.json")))
        tree = model_tree()
        with self.say("f1") as d:
            self.add(seq.start())
            self.play(FadeIn(seq), run_time=0.6)
            self.play(FadeIn(tree, shift=0.1 * RIGHT), run_time=0.8)
            for key, col, off in (("N", C_X, UP * 0.4), ("M", C_Y, UP * 0.45 + RIGHT * 0.3), ("T", C_SHEAR, DOWN * 0.5)):
                lab = MathTex(key, color=col, font_size=46)
                track(lab, seq, anc[key], off)
                self.play(FadeIn(lab), run_time=0.35)
            self.wait(self.left(0.1))
        seq2 = FrameSequence(os.path.join(FR, "fea_mesh"))
        with self.say("f2") as d:
            for m_ in list(self.mobjects):
                if m_ is not tree:
                    m_.clear_updaters()
                    self.remove(m_)
            self.add(seq2.start())
            self.bring_to_front(tree)
            info = VGroup(T("10-node tetrahedra", size=24, color=INK),
                          T(f"h ≈ {SUMM['mesh']['h_fillet']} mm at the fillet, 20 mm far away", size=22, color=DIM))
            info.arrange(DOWN, aligned_edge=LEFT, buff=0.1).to_corner(DR, buff=0.4)
            ib = BackgroundRectangle(info, fill_color=PANEL, fill_opacity=0.85, buff=0.18)
            self.play(FadeIn(ib), FadeIn(info), run_time=0.6)
            self.wait(self.left(0.2))
        seq2.clear_updaters()


class S07b_FEAMethod(NScene):
    def construct(self):
        # ---------------------------------------------------------------- f3 integration points -> stress -> vm
        with self.say("f3") as d:
            V = [np.array(p) for p in ([-5.9, -1.1, 0], [-3.1, -1.6, 0], [-4.1, 1.3, 0], [-4.75, -0.25, 0])]
            V[3] = np.array([-4.35, -0.4, 0])
            edges = [(0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3)]
            tet = VGroup(*[Line(V[a], V[b], color=INK if 3 not in (a, b) else DIM, stroke_width=3 if 3 not in (a, b) else 2)
                           for a, b in edges])
            tet.add(Polygon(V[0], V[1], V[2], fill_color=C_STEEL, fill_opacity=0.25, stroke_width=0))
            nodes = VGroup(*[Dot(v, radius=0.08, color=INK) for v in V])
            mids = VGroup(*[Dot((V[a] + V[b]) / 2, radius=0.06, color=DIM) for a, b in edges])
            gps = VGroup(*[MathTex(r"\times", color=C_YIELD, font_size=40).move_to(p) for p in (
                [-4.65, -0.85, 0], [-3.85, -0.75, 0], [-4.3, 0.15, 0], [-4.4, -0.45, 0])])
            lab_n = T("nodes: displacements u", size=22, color=INK).next_to(VGroup(tet, nodes), DOWN, 0.35)
            lab_g = T("Gauss points", size=22, color=C_YIELD).next_to(lab_n, DOWN, 0.12)
            self.play(Create(tet), FadeIn(nodes), FadeIn(mids), run_time=1.2)
            self.play(FadeIn(lab_n), run_time=0.5)
            self.until("f3", "it differentiates")
            self.play(LaggedStart(*[FadeIn(g, scale=0.5) for g in gps], lag_ratio=0.2), FadeIn(lab_g), run_time=1.0)
            chain = VGroup(
                M(r"\boldsymbol{\varepsilon}=\mathbf{B}\,\mathbf{u}_e", size=40),
                M(r"\boldsymbol{\sigma}=\mathbf{D}\,\boldsymbol{\varepsilon}", size=40),
                M(r"(\sigma_x,\sigma_y,\sigma_z,\tau_{xy},\tau_{yz},\tau_{zx})", size=34),
                M(r"\det(\boldsymbol\sigma-\lambda\mathbf I)=0\ \Rightarrow\ \sigma_1,\sigma_2,\sigma_3", size=34),
                M(r"\sigma_{vm}=\sqrt{3J_2}", size=40, color=C_VM)).arrange(DOWN, buff=0.42)
            chain.move_to([2.4, 0.1, 0])
            arrows = VGroup(*[Arrow(chain[i].get_bottom(), chain[i + 1].get_top(), buff=0.06, color=DIM, stroke_width=3,
                                    max_tip_length_to_length_ratio=0.3) for i in range(4)])
            notes = VGroup(T("strain at each Gauss point", size=20, color=DIM).next_to(chain[0], RIGHT, 0.35),
                           T("Hooke's law", size=20, color=DIM).next_to(chain[1], RIGHT, 0.35),
                           T("full tensor, 6 components", size=20, color=DIM).next_to(chain[2], RIGHT, 0.3),
                           T("eigenvalues", size=20, color=DIM).next_to(chain[3], RIGHT, 0.3),
                           T("invariant", size=20, color=DIM).next_to(chain[4], RIGHT, 0.35))
            self.play(Write(chain[0]), FadeIn(notes[0]), run_time=1.0)
            self.until("f3", "and Hooke")
            self.play(GrowArrow(arrows[0]), Write(chain[1]), FadeIn(notes[1]), run_time=0.9)
            self.play(GrowArrow(arrows[1]), Write(chain[2]), FadeIn(notes[2]), run_time=1.0)
            self.until("f3", "then principal")
            self.play(GrowArrow(arrows[2]), Write(chain[3]), FadeIn(notes[3]), run_time=1.0)
            self.until("f3", "and von Mises stress")
            self.play(GrowArrow(arrows[3]), Write(chain[4]), FadeIn(notes[4]), run_time=0.9)
            self.wait(self.left(0.5))
            self.play(FadeOut(VGroup(tet, nodes, mids, gps, lab_n, lab_g, chain, arrows, notes)), run_time=0.5)
        # ---------------------------------------------------------------- f4 averaging order matters
        with self.say("f4") as d:
            # two elements sharing a node: element A has sigma_x = 100, element B has sigma_y = 100
            A = Polygon([-6.2, -1.2, 0], [-3.6, -1.2, 0], [-3.6, 1.4, 0], fill_color="#2E5E8C", fill_opacity=0.8,
                        stroke_color=INK, stroke_width=2)
            B = Polygon([-6.2, -1.2, 0], [-3.6, 1.4, 0], [-6.2, 1.4, 0], fill_color="#8C3E5E", fill_opacity=0.8,
                        stroke_color=INK, stroke_width=2)
            node = Dot([-3.6, 1.4, 0], radius=0.11, color=C_YIELD)
            la = M(r"\text{A: }\sigma_x=100", size=30).move_to([-4.3, -0.55, 0])
            lb = M(r"\text{B: }\sigma_y=100", size=30).move_to([-5.45, 0.9, 0])
            self.play(FadeIn(A), FadeIn(B), FadeIn(node), FadeIn(la), FadeIn(lb), run_time=1.0)
            nd = T("shared node", size=22, color=C_YIELD).next_to(node, UR, 0.1)
            self.play(FadeIn(nd), run_time=0.4)
            r1 = VGroup(T("average the components, then von Mises", size=24, color=INK),
                        M(r"(\sigma_x,\sigma_y)=(50,50)\ \Rightarrow\ \sigma_{vm}=50\ \text{MPa}", size=34, color=C_VM))
            r2 = VGroup(T("von Mises per element, then average", size=24, color=INK),
                        M(r"\tfrac12(100+100)\ \Rightarrow\ \sigma_{vm}=100\ \text{MPa}", size=34, color=C_VM))
            for r_ in (r1, r2):
                r_.arrange(DOWN, aligned_edge=LEFT, buff=0.12)
            col = VGroup(r1, r2).arrange(DOWN, aligned_edge=LEFT, buff=0.5).move_to([2.6, 1.0, 0])
            self.until("f4", "Averaging components")
            self.play(FadeIn(r1), run_time=0.9)
            self.until("f4", "differs from")
            self.play(FadeIn(r2), run_time=0.9)
            real = T(f"this model at the fillet: {SUMM['vm_peak_nodal']:.1f} vs {SUMM['vm_peak_nodal_avg_invariant']:.1f} MPa",
                     size=22, color=DIM).next_to(col, DOWN, 0.35).align_to(col, LEFT)
            self.play(FadeIn(real), run_time=0.6)
            self.until("f4", "and large jumps")
            jump = VGroup(T("unaveraged values jump across element edges", size=24, color=C_SHEAR),
                          T("→ discretization error: refine the mesh", size=24, color=C_SHEAR)).arrange(
                DOWN, aligned_edge=LEFT, buff=0.1).move_to([1.6, -2.4, 0]).align_to(col, LEFT)
            edge = Line([-6.2, -1.2, 0], [-3.6, 1.4, 0], color=C_SHEAR, stroke_width=7)
            self.play(Create(edge), FadeIn(jump), run_time=0.9)
            self.wait(self.left(0.5))
            self.play(FadeOut(Group(*self.mobjects)), run_time=0.5)


class S07c_FEAResults(NScene):
    def construct(self):
        info = json.load(open(os.path.join(FR, "components", "info.json")))
        keys = ["srr", "stt", "szz", "srt", "stz", "srz"]
        # ---------------------------------------------------------------- f5 the raw tensor: six fields
        tiles = Group()
        for k in keys:
            im = ImageMobject(os.path.join(FR, "components", f"{k}.png"))
            im.width = 4.35
            fr = SurroundingRectangle(im, buff=0, stroke_color=FAINT, stroke_width=1.5)
            lab = MathTex(info[k]["label"], font_size=34, color=INK)
            rng = T(f"{info[k]['clim'][0]:.0f} … +{info[k]['clim'][1]:.0f} MPa", size=16, color=DIM)
            tag_ = VGroup(lab, rng).arrange(RIGHT, buff=0.2)
            bgk = BackgroundRectangle(tag_, fill_color=BG, fill_opacity=0.75, buff=0.08)
            tg = VGroup(bgk, tag_).move_to(im.get_corner(UL), aligned_edge=UL).shift(DR * 0.08)
            tiles.add(Group(im, fr, tg))
        tiles.arrange_in_grid(2, 3, buff=(0.2, 0.25)).move_to(DOWN * 0.15)
        head = T("raw output: six stress components (cylindrical r, θ, z)", size=26, color=INK).to_edge(UP, 0.25)
        with self.say("f5") as d:
            self.play(FadeIn(head), run_time=0.5)
            for t_ in tiles:
                self.play(FadeIn(t_, scale=0.96), run_time=0.45)
            self.until("f5", "None of them alone")
            q = T("which one decides yielding?", size=28, color=C_YIELD).to_edge(DOWN, 0.2)
            qb = BackgroundRectangle(q, fill_color=BG, fill_opacity=0.9, buff=0.1)
            self.play(FadeIn(qb), FadeIn(q), run_time=0.6)
        # ---------------------------------------------------------------- f6 combine -> von Mises field
        seq = FrameSequence(os.path.join(FR, "fea_vm"))
        anc = json.load(open(os.path.join(FR, "fea_vm", "anchors.json")))
        cb = colorbar(0, 300, n=14, height=3.6, width=0.28, size=20, ticks=[0, 50, 100, 150, 200, 250, 300])
        cb.to_edge(RIGHT, buff=0.6).shift(DOWN * 0.2)
        with self.say("f6") as d:
            self.play(*[t_.animate.scale(0.2).move_to(ORIGIN).set_opacity(0) for t_ in tiles], FadeOut(head),
                      FadeOut(q), FadeOut(qb), run_time=0.9)
            self.remove(*tiles)
            self.add(seq.start())
            eq = M(r"\sigma_{vm}=\sqrt{3J_2(\boldsymbol\sigma)}", size=36, color=C_VM).to_corner(UL, 0.35)
            eqb = BackgroundRectangle(eq, fill_color=BG, fill_opacity=0.8, buff=0.12)
            self.play(FadeIn(seq), FadeIn(cb), FadeIn(eqb), Write(eq), run_time=0.8)
            pipe = VGroup(T(f"≈ {SUMM['narr_pipe_vm']} MPa", size=24, color=INK), T("pipe wall", size=18, color=DIM))
            pipe.arrange(DOWN, buff=0.05)
            pk = VGroup(T(f"{SUMM['narr_peak_vm']} MPa", size=28, color=C_VM, weight=BOLD),
                        T("fillet root", size=18, color=DIM)).arrange(DOWN, buff=0.05)
            for g_ in (pipe, pk):
                g_.add_to_back(BackgroundRectangle(g_, fill_color=BG, fill_opacity=0.75, buff=0.08))
            self.until("f6", "About")
            track(pipe, seq, anc["pipe"], UP * 0.6)
            self.play(FadeIn(pipe), run_time=0.5)
            self.until("f6", "rising to")
            track(pk, seq, anc["peak"], UP * 0.75 + RIGHT * 0.5)
            self.play(FadeIn(pk), run_time=0.5)
            self.wait(self.left(0.1))
        # ---------------------------------------------------------------- f7 load flow lines (axisymmetric section)
        with self.say("f7") as d:
            pipe.clear_updaters(); pk.clear_updaters(); seq.clear_updaters()
            self.play(FadeOut(Group(seq, cb, eq, eqb, pipe, pk)), run_time=0.6)
            bg = ImageMobject(os.path.join(FEA, "axi_flow_bg.png"))
            bg.height = 8.0 * 0.95
            bg.move_to(ORIGIN)
            # image extent (z: 430..770, r: Ri-40..Ro2+30) -> Manim coordinates
            g = AXI["geometry"]
            z0, z1, r0, r1 = 430.0, 770.0, g["Ri"] - 40.0, g["Ro2"] + 30.0
            sx = bg.width / (z1 - z0); sy = bg.height / (r1 - r0)
            org = bg.get_corner(DL)
            P = lambda z, r: org + np.array([(z - z0) * sx, (r - r0) * sy, 0])
            bg.set_opacity(0.55)
            self.play(FadeIn(bg), run_time=0.8)
            lines = VGroup()
            for ln in AXI["trajectories"]:
                pts = [P(z, r) for z, r in ln if z0 < z < z1]
                if len(pts) > 2:
                    lines.add(VMobject(stroke_color=WHITE, stroke_width=2.6, stroke_opacity=0.9).set_points_smoothly(pts[::2]))
            ttl = VGroup(T("principal stress trajectories", size=26, color=INK),
                         T("axisymmetric section, axial load", size=20, color=DIM)).arrange(DOWN, aligned_edge=LEFT,
                                                                                             buff=0.08)
            ttl.to_corner(UL, 0.35)
            tb = BackgroundRectangle(ttl, fill_color=BG, fill_opacity=0.85, buff=0.12)
            self.play(FadeIn(tb), FadeIn(ttl), run_time=0.5)
            self.play(LaggedStart(*[Create(l_) for l_ in lines], lag_ratio=0.08), run_time=min(3.5, d * 0.4))
            self.until("f7", "and crowd together")
            ring = Circle(radius=0.55, color=C_YIELD, stroke_width=4).move_to(P(g["zs"] - 5, g["Ro1"] + 2.5))
            self.play(Create(ring), run_time=0.6)
            kt = T(f"K_t ≈ {AXI['series']['fillet'][-1]['kt_nodal']:.2f}  (R8 fillet)", size=26, color=C_YIELD)
            kt.next_to(ring, UP, 0.25)
            kb = BackgroundRectangle(kt, fill_color=BG, fill_opacity=0.85, buff=0.08)
            self.play(FadeIn(kb), FadeIn(kt), run_time=0.5)
            self.wait(self.left(0.5))
            self.play(FadeOut(Group(*self.mobjects)), run_time=0.5)


class S07d_FEAPitfalls(NScene):
    def construct(self):
        ser = AXI["series"]
        # ---------------------------------------------------------------- f8 convergence vs singularity
        with self.say("f8") as d:
            ax = Axes(x_range=[-5.2, 2.2, 1], y_range=[0, 15, 3], x_length=6.6, y_length=4.4, tips=False,
                      axis_config=dict(color=DIM, stroke_width=2, include_ticks=True, tick_size=0.05),
                      y_axis_config=dict(include_numbers=True, font_size=22)).move_to([-2.9, -0.35, 0])
            xt = VGroup()
            for e in (-5, -4, -3, -2, -1, 0, 1, 2):
                v = 2.0 ** e
                xt.add(T(f"{v:g}", size=16, color=DIM).next_to(ax.c2p(e, 0), DOWN, 0.15))
            xl = T("element size at the corner  h  [mm]  (log scale)", size=20, color=DIM).next_to(ax, DOWN, 0.45)
            yl = M(r"K_t=\sigma_{vm,\max}/\sigma_{\text{nom}}", size=28, color=DIM).next_to(ax, UP, 0.15).align_to(ax, LEFT)
            self.play(Create(ax), FadeIn(xt), FadeIn(xl), FadeIn(yl), run_time=1.0)
            pf = [ax.c2p(np.log2(r["h"]), r["kt_nodal"]) for r in ser["fillet"]]
            ps = [ax.c2p(np.log2(r["h"]), r["kt_nodal"]) for r in ser["sharp"]]
            fil = VGroup(*[Dot(p, color=C_GOOD, radius=0.07) for p in pf])
            fl = VMobject(stroke_color=C_GOOD, stroke_width=3).set_points_as_corners(pf[::-1])
            shp = VGroup(*[Dot(p, color=C_BAD, radius=0.07) for p in ps])
            sl = VMobject(stroke_color=C_BAD, stroke_width=3).set_points_as_corners(ps[::-1])
            lf = T("R8 fillet: converges", size=22, color=C_GOOD).next_to(pf[0], UP, 0.25).shift(LEFT * 0.4)
            ls = T("sharp corner: no limit", size=22, color=C_BAD).next_to(ps[-1], RIGHT, 0.15).shift(DOWN * 0.1)
            # inset images of the sharp-corner mesh at three refinements
            ins = Group()
            for h in (2, 0.5, 0.03125):
                im = ImageMobject(os.path.join(FEA, f"axi_sharp_h{h:g}.png"))
                im.height = 1.75
                kt = [r for r in ser["sharp"] if abs(r["h"] - h) < 1e-9][0]["kt_nodal"]
                cap = T(f"h = {h:g} mm   Kt = {kt:.1f}", size=16, color=INK).next_to(im, DOWN, 0.08)
                ins.add(Group(im, SurroundingRectangle(im, buff=0, stroke_color=FAINT, stroke_width=1), cap))
            ins.arrange(DOWN, buff=0.18).move_to([4.95, -0.1, 0])
            self.play(LaggedStart(*[FadeIn(x) for x in fil[::-1]], lag_ratio=0.12), Create(fl), run_time=1.6)
            self.play(FadeIn(lf), run_time=0.5)
            self.until("f8", "Model the corner")
            self.play(LaggedStart(*[FadeIn(x) for x in shp[::-1]], lag_ratio=0.15), Create(sl), run_time=2.0)
            self.play(FadeIn(ls), run_time=0.4)
            self.until("f8", "elasticity predicts")
            wl = M(r"\sigma\propto r^{\lambda-1},\ \ \lambda=0.545\ \ (\text{Williams, 1952})", size=30, color=C_BAD)
            wl.next_to(yl, RIGHT, 0.5)
            self.play(Write(wl), run_time=1.2)
            self.until("f8", "Each refinement")
            self.play(LaggedStart(*[FadeIn(x, shift=0.1 * LEFT) for x in ins], lag_ratio=0.3), run_time=1.6)
            c3 = SUMM["convergence_3d"]
            tbl = T("3D model, fillet root (Gauss pts): " + " → ".join(f"{c['gauss']:.0f}" for c in c3) + " MPa",
                    size=18, color=C_GOOD).next_to(xl, DOWN, 0.15)
            self.play(FadeIn(tbl), run_time=0.5)
            self.wait(self.left(0.5))
            self.play(FadeOut(Group(*self.mobjects)), run_time=0.5)
        # ---------------------------------------------------------------- f9 stress linearization along an SCL
        with self.say("f9") as d:
            scl = AXI["scl"]
            s = np.array(scl["s"]); szz = np.array(scl["szz"]); lin = np.array(scl["szz_lin"])
            tk = scl["thickness"]
            ax = Axes(x_range=[0, tk, 5], y_range=[0, 240, 40], x_length=6.2, y_length=4.2, tips=False,
                      axis_config=dict(color=DIM, stroke_width=2, include_ticks=True, tick_size=0.05),
                      y_axis_config=dict(include_numbers=True, font_size=22),
                      x_axis_config=dict(include_numbers=True, font_size=22)).move_to([-2.3, -0.4, 0])
            xl = T("distance through the wall from the fillet surface  [mm]", size=20, color=DIM).next_to(ax, DOWN, 0.4)
            yl = M(r"\sigma_{zz}\ [\mathrm{MPa}]", size=30, color=DIM).next_to(ax, UP, 0.15).align_to(ax, LEFT)
            tot = ax.plot_line_graph(s, szz, add_vertex_dots=False, line_color=C_VM, stroke_width=5)
            mem = DashedLine(ax.c2p(0, scl["szz_mem"]), ax.c2p(tk, scl["szz_mem"]), color=C_HYD, stroke_width=4)
            mb = Line(ax.c2p(0, lin[0]), ax.c2p(tk, lin[-1]), color=C_TRESCA, stroke_width=4)
            pk = DoubleArrow(ax.c2p(0.6, lin[0]), ax.c2p(0.6, szz[0]), buff=0, color=C_YIELD, stroke_width=3,
                             tip_length=0.15)
            leg = VGroup(VGroup(Line(ORIGIN, RIGHT * 0.5, color=C_VM, stroke_width=5), T("total (FE)", size=22)).arrange(RIGHT),
                         VGroup(DashedLine(ORIGIN, RIGHT * 0.5, color=C_HYD, stroke_width=4),
                                T(f"membrane {scl['szz_mem']:.0f} MPa", size=22)).arrange(RIGHT),
                         VGroup(Line(ORIGIN, RIGHT * 0.5, color=C_TRESCA, stroke_width=4),
                                T(f"membrane + bending", size=22)).arrange(RIGHT),
                         VGroup(Line(ORIGIN, RIGHT * 0.5, color=C_YIELD, stroke_width=4), T("peak (nonlinear part)", size=22)
                                ).arrange(RIGHT)).arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to([4.2, 1.2, 0])
            vals = VGroup(T(f"σ_vm  membrane  P_L = {scl['vm_PL']:.0f} MPa", size=22, color=C_HYD),
                          T(f"σ_vm  P_L + P_b = {scl['vm_PL_Pb']:.0f} MPa", size=22, color=C_TRESCA),
                          T(f"σ_vm  total at surface = {scl['vm_total_surface']:.0f} MPa", size=22, color=C_VM),
                          T("each category has its own limit (e.g. ASME VIII-2 Part 5)", size=18, color=DIM)).arrange(
                DOWN, aligned_edge=LEFT, buff=0.16).move_to([4.2, -1.4, 0])
            ttl = T("stress classification line through the wall at the hot spot", size=24, color=INK).to_edge(UP, 0.3)
            self.play(FadeIn(ttl), Create(ax), FadeIn(xl), FadeIn(yl), run_time=1.0)
            self.until("f9", "Check convergence")
            self.play(Create(tot), FadeIn(leg[0]), run_time=1.2)
            self.until("f9", "linearize")
            self.play(Create(mem), FadeIn(leg[1]), run_time=0.9)
            self.play(Create(mb), FadeIn(leg[2]), run_time=0.9)
            self.play(GrowFromCenter(pk), FadeIn(leg[3]), run_time=0.7)
            self.until("f9", "and apply")
            self.play(FadeIn(vals, shift=0.1 * UP), run_time=1.0)
            self.wait(self.left(0.5))
            self.play(FadeOut(Group(*self.mobjects)), run_time=0.5)
        # ---------------------------------------------------------------- f10 constitutive assumption
        with self.say("f10") as d:
            ax = Axes(x_range=[0, 1, 0.25], y_range=[0, 1.6, 0.4], x_length=6.0, y_length=4.0, tips=False,
                      axis_config=dict(color=DIM, stroke_width=2, include_ticks=False)).move_to([-2.6, -0.3, 0])
            xl = M(r"\varepsilon", size=32, color=DIM).next_to(ax.x_axis, RIGHT, 0.1)
            yl = M(r"\sigma", size=32, color=DIM).next_to(ax.y_axis, UP, 0.1)
            ey = 0.25
            elastic = ax.plot(lambda x: x / ey, x_range=[0, 0.38], color=C_Z, stroke_width=4)
            plastic = ax.plot(lambda x: x / ey if x < ey else 1 + 0.25 * (1 - np.exp(-(x - ey) / 0.3)),
                              x_range=[0, 1], color=INK, stroke_width=4)
            sy = DashedLine(ax.c2p(0, 1), ax.c2p(1, 1), color=C_YIELD, stroke_width=2)
            syl = M(r"\sigma_Y", size=32, color=C_YIELD).next_to(sy, LEFT, 0.1)
            pkd = Dot(ax.c2p(0.36, 0.36 / ey), color=C_Z, radius=0.08)
            pkl = T("linear elastic FE: peak above σ_Y", size=22, color=C_Z).next_to(pkd, RIGHT, 0.2)
            real = T("real steel: yields locally, load redistributes", size=22, color=INK).next_to(ax.c2p(0.62, 1.2), UP, 0.25)
            self.play(Create(ax), FadeIn(xl), FadeIn(yl), Create(sy), FadeIn(syl), run_time=1.0)
            self.play(Create(elastic), run_time=1.2)
            self.play(FadeIn(pkd), FadeIn(pkl), run_time=0.6)
            self.until("f10", "while real steel")
            self.play(Create(plastic), FadeIn(real), run_time=1.6)
            self.until("f10", "A local elastic")
            nxt = VGroup(T("a local elastic peak above σ_Y is a signal, not a verdict", size=26, color=C_YIELD),
                         T("→ elastic–plastic analysis (e.g. DNV-RP-C208), strain or fatigue checks", size=22,
                           color=INK)).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([2.6, 2.4, 0])
            self.play(FadeIn(nxt, shift=0.1 * DOWN), run_time=1.0)
            self.wait(self.left(0.6))
            self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)
