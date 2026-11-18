"""Section 1 - why do materials fail?  (cold open + title)"""
from common import *  # noqa: F401,F403

FR = os.path.join(BUILD, "frames")


def fixed(scene, *mobs):
    scene.add_fixed_in_frame_mobjects(*mobs)
    scene.remove(*mobs)
    return mobs[0] if len(mobs) == 1 else mobs


def dogbone(w=0.5, L=3.0, grip=0.9, gl=0.7):
    pts = [(-L / 2 - gl, grip / 2), (-L / 2, grip / 2), (-L / 2 + 0.35, w / 2), (L / 2 - 0.35, w / 2), (L / 2, grip / 2),
           (L / 2 + gl, grip / 2), (L / 2 + gl, -grip / 2), (L / 2, -grip / 2), (L / 2 - 0.35, -w / 2),
           (-L / 2 + 0.35, -w / 2), (-L / 2, -grip / 2), (-L / 2 - gl, -grip / 2)]
    return Polygon(*[np.array([x, y, 0]) for x, y in pts], color=INK, stroke_width=2, fill_color=C_STEEL,
                   fill_opacity=0.5)


class S01_Opening(N3DScene):
    def construct(self):
        self.set_camera_orientation(phi=66 * DEGREES, theta=-50 * DEGREES, zoom=1.0)
        # ---------------------------------------------------------------- o1 the component under load
        seqA = FrameSequence(os.path.join(FR, "open_a"))
        ancA = json.load(open(os.path.join(FR, "open_a", "anchors.json")))
        fixed(self, seqA)
        labs = {}
        for key, tex, txt, col in (("N", "N", "axial force", C_X), ("M", "M", "bending moment", C_Y),
                                   ("T", "T", "torque", C_SHEAR)):
            g = VGroup(MathTex(tex, color=col, font_size=46), T(txt, size=22, color=col)).arrange(RIGHT, buff=0.15)
            labs[key] = g
        offs = {"N": UP * 0.45, "M": UP * 0.5 + RIGHT * 0.4, "T": DOWN * 0.55 + RIGHT * 0.2}
        with self.say("o1") as d:
            self.add(seqA.start())
            nA = len(seqA.files)
            t_appear = {"N": 0.2, "M": 0.42, "T": 0.62}
            order = sorted(t_appear, key=t_appear.get)
            t_prev = 0.0
            for k in order:
                t_k = t_appear[k] * nA / 30.0 + 0.35
                self.wait(max(0.05, t_k - t_prev))
                t_prev = t_k
                lab = labs[k]
                fixed(self, lab)
                track(lab, seqA, ancA[k], offs[k])
                self.play(FadeIn(lab), run_time=0.5)
                t_prev += 0.5
        # ---------------------------------------------------------------- o2 stress field, dive, cube, tensor
        seqB = FrameSequence(os.path.join(FR, "open_b"))
        dB = DUR["o2"]
        seqB.fps = len(seqB.files) / (0.30 * dB)
        fixed(self, seqB)
        cb = colorbar(0, 300, n=14, height=3.2, width=0.26, size=20, title=r"\sigma_{vm}\ [\mathrm{MPa}]",
                      ticks=[0, 100, 200, 300])
        cb.to_edge(RIGHT, buff=0.55)
        fixed(self, cb)
        sig = np.array([[1.0, 0.42, 0.22], [0.42, 0.35, -0.28], [0.22, -0.28, -0.45]])
        cube = stress_cube(sig, size=1.9, scale=1.0)
        cube.shift(np.array([np.sin(50 * DEGREES), np.cos(50 * DEGREES), 0]) * -2.2)
        mat = matrix_tex([[r"\sigma_x", r"\tau_{xy}", r"\tau_{xz}"], [r"\tau_{yx}", r"\sigma_y", r"\tau_{yz}"],
                          [r"\tau_{zx}", r"\tau_{zy}", r"\sigma_z"]], size=40, h_buff=1.05)
        for i in range(3):
            mat.get_rows()[i][i].set_color(COMP[i])
        for (i, j) in [(0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1)]:
            mat.get_rows()[i][j].set_color(C_SHEAR)
        mlab = M(r"\boldsymbol{\sigma}=", size=46).next_to(mat, LEFT, 0.2)
        sym = VGroup(M(r"\tau_{xy}=\tau_{yx},\ \ \tau_{yz}=\tau_{zy},\ \ \tau_{zx}=\tau_{xz}", size=32, color=C_SHEAR),
                     T("symmetric: 6 independent components", size=24, color=DIM)).arrange(DOWN, buff=0.2)
        tens = VGroup(VGroup(mlab, mat), sym).arrange(DOWN, buff=0.4).move_to([3.4, 0.2, 0])
        fixed(self, tens)
        with self.say("o2") as d:
            self.remove(seqA)
            for lab in labs.values():
                lab.clear_updaters(); self.remove(lab)
            self.add(seqB.start())
            self.play(FadeIn(cb), run_time=0.6)
            self.wait(max(0.1, 0.30 * d - 0.6 - 0.1))
            # crossfade from the render to the 3D element
            self.play(FadeOut(seqB), FadeOut(cb), FadeIn(cube.cube), run_time=0.8)
            seqB.clear_updaters()
            self.play(LaggedStart(*[GrowFromPoint(a, cube.get_center()) for a in cube.normals], lag_ratio=0.15),
                      run_time=self.till("o2", "while three shear", minimum=1.0))
            self.play(LaggedStart(*[FadeIn(a) for a in cube.shears], lag_ratio=0.1),
                      run_time=self.till("o2", "Together", minimum=1.0))
            self.play(FadeIn(VGroup(mlab, mat)), run_time=0.9)
            self.until("o2", "symmetric")
            self.play(FadeIn(sym, shift=0.1 * UP), run_time=0.8)
            spin = lambda m, dt: m.rotate(0.1 * dt, axis=OUT, about_point=m.get_center())
            cube.add_updater(spin)
        # ---------------------------------------------------------------- o3 the tension test gives one number
        with self.say("o3") as d:
            self.play(FadeOut(sym), tens[0].animate.scale(0.75).to_corner(UL).shift(DOWN * 0.15), run_time=0.8)
            spec = dogbone().scale(0.9).move_to([2.2, 2.0, 0])
            arrL = Arrow([0.0, 2.0, 0], [-0.9, 2.0, 0], buff=0, color=C_X, stroke_width=6)
            arrR = Arrow([4.4, 2.0, 0], [5.3, 2.0, 0], buff=0, color=C_X, stroke_width=6)
            ax = Axes(x_range=[0, 1, 0.25], y_range=[0, 1.2, 0.3], x_length=4.6, y_length=2.6, tips=False,
                      axis_config=dict(color=DIM, stroke_width=2, include_ticks=False)).move_to([2.4, -1.4, 0])
            curve = ax.plot(lambda x: (x / 0.06 * 0.72) if x < 0.06 else 0.72 + 0.3 * (1 - np.exp(-(x - 0.06) / 0.25)),
                            x_range=[0, 1], color=INK, stroke_width=4)
            yp = Dot(ax.c2p(0.06, 0.72), color=C_YIELD, radius=0.08)
            ypl = M(r"\sigma_Y", color=C_YIELD, size=40).next_to(yp, LEFT, 0.2).shift(UP * 0.15)
            xl = M(r"\varepsilon", size=30, color=DIM).next_to(ax.x_axis, RIGHT, 0.1)
            yl = M(r"\sigma", size=30, color=DIM).next_to(ax.y_axis, UP, 0.1)
            tt = T("uniaxial tension test", size=24, color=DIM).next_to(spec, UP, 0.3)
            grp = VGroup(spec, arrL, arrR, ax, curve, yp, ypl, xl, yl, tt)
            fixed(self, grp)
            self.play(FadeIn(spec), FadeIn(tt), GrowArrow(arrL), GrowArrow(arrR), run_time=1.0)
            self.play(Create(ax), FadeIn(xl), FadeIn(yl), Create(curve), run_time=1.6)
            self.until("o3", "the yield strength")
            self.play(FadeIn(yp, scale=0.5), Write(ypl), run_time=0.8)
            self.until("o3", "So how do we decide")
            q = VGroup(M(r"\boldsymbol{\sigma}\ (6\ \text{components})", size=40),
                       M(r"\ \overset{?}{\longrightarrow}\ ", size=50, color=C_VM),
                       M(r"\sigma_Y\ (1\ \text{number})", size=40, color=C_YIELD)).arrange(RIGHT, buff=0.3)
            q.to_edge(DOWN, buff=0.45)
            qb = BackgroundRectangle(q, fill_color=BG, fill_opacity=0.85, buff=0.15)
            fixed(self, qb, q)
            self.play(FadeIn(qb), Write(q), run_time=1.6)
        # ---------------------------------------------------------------- o4 naive component check fails
        with self.say("o4") as d:
            cube.clear_updaters()
            self.play(FadeOut(VGroup(grp, q, qb, tens[0])), FadeOut(cube), run_time=0.7)
            # left: pure torsion
            hdr1 = T("pure torsion", size=30, weight=SEMIBOLD).move_to([-3.6, 2.9, 0])
            ax1 = Axes(x_range=[0, 3, 1], y_range=[0, 1.1, 0.25], x_length=4.6, y_length=3.0, tips=False,
                       axis_config=dict(color=DIM, stroke_width=2, include_ticks=False)).move_to([-3.6, 0.2, 0])
            b1 = Rectangle(width=1.0, height=3.0 * 1.0 / 1.1, fill_color=C_STEEL, fill_opacity=0.6, stroke_width=0)
            b1.move_to(ax1.c2p(0.8, 0.5), aligned_edge=DOWN).align_to(ax1.c2p(0, 0), DOWN)
            b2 = Rectangle(width=1.0, height=3.0 * 0.577 / 1.1, fill_color=C_VM, fill_opacity=0.85, stroke_width=0)
            b2.move_to(ax1.c2p(2.2, 0.3)).align_to(ax1.c2p(0, 0), DOWN)
            yl1 = DashedLine(ax1.c2p(0, 1.0), ax1.c2p(3, 1.0), color=C_YIELD, stroke_width=2)
            yl1l = M(r"\sigma_Y", size=30, color=C_YIELD).next_to(yl1, LEFT, 0.1)
            l1 = VGroup(T("component check", size=20, color=INK), M(r"\tau=\sigma_Y", size=30)).arrange(DOWN, buff=0.08)
            l1.next_to(b1, DOWN, 0.15)
            l2 = VGroup(T("actual yield", size=20, color=C_VM), M(r"\tau\approx0.58\,\sigma_Y", size=30, color=C_VM)).arrange(
                DOWN, buff=0.08).next_to(b2, DOWN, 0.15)
            x1 = T("✗", size=40, color=C_BAD).next_to(b1, UP, 0.1)
            # right: hydrostatic squeeze
            hdr2 = T("equal pressure from all sides", size=30, weight=SEMIBOLD).move_to([3.6, 2.9, 0])
            sq = Square(2.0, color=INK, stroke_width=2, fill_color=C_STEEL, fill_opacity=0.35).move_to([3.6, 0.4, 0])
            arrs = VGroup()
            for v in (UP, DOWN, LEFT, RIGHT):
                for o in (-0.5, 0.5):
                    pv_ = np.array([-v[1], v[0], 0])
                    s0 = sq.get_center() + v * 1.95 + pv_ * o
                    arrs.add(Arrow(s0, s0 - v * 0.8, buff=0, color=C_HYD, stroke_width=5,
                                   max_tip_length_to_length_ratio=0.3))
            pl2 = M(r"p\gg\sigma_Y", size=40, color=C_HYD).next_to(sq, DOWN, 1.05)
            ny = T("no yielding", size=30, color=C_GOOD, weight=SEMIBOLD).next_to(pl2, DOWN, 0.3)
            left = VGroup(hdr1, ax1, b1, b2, yl1, yl1l, l1, l2, x1)
            right = VGroup(hdr2, sq, arrs, pl2, ny)
            fixed(self, left, right)
            self.play(FadeIn(hdr1), Create(ax1), Create(yl1), FadeIn(yl1l), run_time=0.9)
            self.until("o4", "A shaft in pure")
            self.play(GrowFromEdge(b1, DOWN), FadeIn(l1), run_time=0.9)
            self.until("o4", "yields when")
            self.play(GrowFromEdge(b2, DOWN), FadeIn(l2), run_time=0.9)
            self.play(FadeIn(x1), run_time=0.4)
            self.until("o4", "And a solid specimen")
            self.play(FadeIn(hdr2), FadeIn(sq), LaggedStart(*[GrowArrow(a) for a in arrs], lag_ratio=0.05),
                      run_time=1.2)
            self.play(FadeIn(pl2), run_time=0.6)
            self.until("o4", "does not yield")
            self.play(FadeIn(ny, scale=0.8), run_time=0.6)
        # ---------------------------------------------------------------- o5 we need an equivalent stress
        with self.say("o5") as d:
            self.play(FadeOut(VGroup(left, right)), run_time=0.6)
            m2 = matrix_tex([[r"\sigma_x", r"\tau_{xy}", r"\tau_{xz}"], [r"\tau_{xy}", r"\sigma_y", r"\tau_{yz}"],
                             [r"\tau_{xz}", r"\tau_{yz}", r"\sigma_z"]], size=40, h_buff=1.0).move_to(LEFT * 3.6)
            for i in range(3):
                m2.get_rows()[i][i].set_color(COMP[i])
            for (i, j) in [(0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1)]:
                m2.get_rows()[i][j].set_color(C_SHEAR)
            arr = M(r"\longrightarrow", size=60, color=DIM)
            eqv = M(r"\sigma_{\text{eq}}", size=72, color=C_VM)
            cmp_ = M(r"\ \text{vs}\ \ \sigma_Y", size=56, color=C_YIELD)
            row = VGroup(arr, eqv, cmp_).arrange(RIGHT, buff=0.4).next_to(m2, RIGHT, 0.6)
            fixed(self, m2, row)
            self.play(FadeIn(m2), run_time=0.7)
            self.play(Write(arr), TransformFromCopy(m2, eqv), run_time=1.4)
            self.play(FadeIn(cmp_), run_time=0.6)
            self.until("o5", "To find it")
            self.wait(self.left(0.7))
            self.play(FadeOut(VGroup(m2, row)), run_time=0.7)
        # ---------------------------------------------------------------- title card
        title = T("THE PHYSICS OF FAILURE", size=64, weight=BOLD)
        sub = T("Understanding von Mises Stress", size=36, color=C_VM)
        tg = VGroup(title, sub).arrange(DOWN, buff=0.35)
        ln = Line(LEFT * 4.2, RIGHT * 4.2, color=C_YIELD, stroke_width=2).next_to(tg, DOWN, 0.4)
        fixed(self, tg, ln)
        self.play(FadeIn(title, shift=0.15 * UP), run_time=1.0)
        self.play(FadeIn(sub), Create(ln), run_time=0.9)
        self.wait(2.2)
        self.play(FadeOut(VGroup(tg, ln)), run_time=0.9)
