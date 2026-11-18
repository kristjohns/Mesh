"""Section 4 - intuition through loading cases A-E."""
from common import *  # noqa: F401,F403

PHI, THETA = 66 * DEGREES, -52 * DEGREES
RIGHTV = np.array([-np.sin(THETA), np.cos(THETA), 0])
UPV = np.array([-np.cos(PHI) * np.cos(THETA), -np.cos(PHI) * np.sin(THETA), np.sin(PHI)])


def screen(x, y):
    """World point that appears near screen coords (x, y) for the fixed camera orientation."""
    return RIGHTV * x + UPV * y


def fixed(scene, *mobs):
    scene.add_fixed_in_frame_mobjects(*mobs)
    scene.remove(*mobs)
    return mobs[0] if len(mobs) == 1 else mobs


def case_title(letter, name):
    t = VGroup(T(f"Case {letter}", size=26, color=C_YIELD, weight=BOLD), T(name, size=34, weight=SEMIBOLD))
    t.arrange(DOWN, aligned_edge=LEFT, buff=0.1).to_corner(UL).shift(RIGHT * 0.1 + DOWN * 0.05)
    return t


def principal_bars(vals, colors, label, x0, y0, width=5.0, scale=1.2):
    """Number line with principal stresses and their pairwise differences (spread)."""
    nl = NumberLine(x_range=[-1.2, 1.2, 0.5], length=width, color=DIM, include_ticks=False, stroke_width=2)
    nl.move_to([x0, y0, 0])
    g = VGroup(nl)
    for v, c, lab in zip(vals, colors, label):
        p = nl.n2p(v)
        g.add(Dot(p, color=c, radius=0.08))
        if lab:
            g.add(MathTex(lab, color=c, font_size=34).next_to(p, DOWN, 0.15))
    return g


class S04a_CasesAB(N3DScene):
    def construct(self):
        self.set_camera_orientation(phi=PHI, theta=THETA, zoom=0.95)
        card = VGroup(T("04", size=34, color=C_YIELD, weight=BOLD), T("Five loading cases", size=50, weight=SEMIBOLD))
        card.arrange(DOWN, buff=0.3)
        fixed(self, card)
        self.play(FadeIn(card), run_time=0.8); self.wait(0.8); self.play(FadeOut(card), run_time=0.6)
        CPOS = screen(-3.7, -0.3)
        # ---------------------------------------------------------------- Case A
        sigA = np.diag([1.0, 0, 0])
        cubeA = stress_cube(sigA, size=1.9, scale=1.1).move_to(CPOS)
        titA = fixed(self, case_title("A", "Uniaxial tension"))
        mA = VGroup(M(r"\sigma_1=\sigma,\quad \sigma_2=\sigma_3=0", size=40),
                    M(r"\sigma_{vm}=\sqrt{\tfrac12\left[(\sigma-0)^2+(0-0)^2+(0-\sigma)^2\right]}", size=38),
                    M(r"\sigma_{vm}=|\sigma|", size=50, color=C_VM)).arrange(DOWN, buff=0.45, aligned_edge=LEFT)
        mA.move_to([2.6, 1.0, 0])
        fixed(self, mA)
        with self.say("a1") as d:
            self.play(FadeIn(titA), FadeIn(cubeA.cube), run_time=0.8)
            self.play(LaggedStart(*[GrowFromPoint(a, CPOS) for a in cubeA.normals], lag_ratio=0.2), run_time=1.0)
            spin = lambda m, dt: m.rotate(0.12 * dt, axis=OUT, about_point=CPOS)
            cubeA.add_updater(spin)
            self.play(Write(mA[0]), run_time=1.2)
            self.until("a1", "Two differences")
            self.play(Write(mA[1]), run_time=1.6)
            self.until("a1", "and sigma")
            self.play(Write(mA[2]), run_time=0.9)
        with self.say("a2") as d:
            dec = M(r"(\sigma,0,0)", r"=", r"\tfrac{\sigma}{3}(1,1,1)", r"+", r"\left(\tfrac{2\sigma}{3},-\tfrac{\sigma}{3},-\tfrac{\sigma}{3}\right)",
                    size=38).move_to([2.6, -1.4, 0])
            dec[2].set_color(C_HYD); dec[4].set_color(C_DEV)
            labs = VGroup(T("hydrostatic: no role", size=22, color=C_HYD).next_to(dec[2], DOWN, 0.2),
                          T("deviator", size=22, color=C_DEV).next_to(dec[4], DOWN, 0.2))
            cal = T("calibrated on this test:  σ_vm = σ_Y at yield", size=24, color=DIM).move_to([2.6, -2.7, 0])
            fixed(self, dec, labs, cal)
            self.play(FadeIn(cal), run_time=0.6)
            self.until("a2", "Yet even here")
            self.play(Write(dec), run_time=1.6)
            self.play(FadeIn(labs), run_time=0.5)
            self.wait(self.left(0.6))
            cubeA.clear_updaters()
            self.play(FadeOut(VGroup(titA, mA, dec, labs, cal, cubeA)), run_time=0.6)
        # ---------------------------------------------------------------- Case B (view nearly down z)
        self.move_camera(phi=38 * DEGREES, theta=-90 * DEGREES, run_time=1.0)
        CPOS = np.array([-3.7, -0.2, 0.0])
        sigB = np.array([[0, 1.0, 0], [1.0, 0, 0], [0, 0, 0]])
        cubeB = stress_cube(sigB, size=1.9, scale=1.1).move_to(CPOS)
        titB = fixed(self, case_title("B", "Pure shear"))
        mB = VGroup(M(r"\tau_{xy}=\tau,\quad \text{all other components}=0", size=38),
                    M(r"\sigma_{vm}=\sqrt{3\tau_{xy}^2}=\sqrt3\,|\tau|", size=44),
                    M(r"\tau_Y=\frac{\sigma_Y}{\sqrt3}\approx 0.577\,\sigma_Y", size=46, color=C_VM),
                    M(r"\text{S355:}\ \ \tau_Y\approx 205\ \text{MPa}", size=36, color=DIM)).arrange(DOWN, buff=0.4,
                                                                                         aligned_edge=LEFT)
        mB.move_to([2.6, 0.9, 0])
        fixed(self, mB)
        with self.say("b1") as d:
            self.play(FadeIn(titB), FadeIn(cubeB.cube), run_time=0.7)
            self.play(LaggedStart(*[GrowFromPoint(a, a.get_center()) for a in cubeB.shears], lag_ratio=0.15),
                      run_time=1.0)
            self.play(Write(mB[0]), run_time=1.2)
            self.until("b1", "The Cartesian form")
            self.play(Write(mB[1]), run_time=1.4)
            self.until("b1", "and yield in shear")
            self.play(Write(mB[2]), run_time=1.4)
            self.until("b1", "For S three")
            self.play(FadeIn(mB[3]), run_time=0.6)
        with self.say("b2") as d:
            self.play(FadeOut(mB), run_time=0.5)
            # rotate the element 45 deg about z: shear -> +tau / -tau principal stresses
            prin = VGroup()
            e1 = np.array([1, 1, 0]) / np.sqrt(2); e2 = np.array([1, -1, 0]) / np.sqrt(2)
            h = 0.95
            for vec, sgn_s, col in ((e1, 1, C_X), (e2, -1, C_Z)):
                for sgn in (1, -1):
                    p0 = CPOS + sgn * vec * h
                    outer = p0 + sgn * vec * 1.0
                    st, en = (p0, outer) if sgn_s > 0 else (outer, p0)
                    prin.add(Arrow3D(st, en, color=col, thickness=0.025, height=0.22, base_radius=0.07, resolution=8))
            self.play(Rotate(cubeB.cube, PI / 4, axis=OUT, about_point=CPOS), FadeOut(cubeB.shears), run_time=1.6)
            self.play(LaggedStart(*[GrowFromPoint(a, CPOS) for a in prin], lag_ratio=0.15), run_time=1.0)
            pl = VGroup(M(r"+\tau", color=C_X, size=40), M(r"-\tau", color=C_Z, size=40))
            pl[0].move_to(CPOS + e1 * 2.35); pl[1].move_to(CPOS + e2 * 2.35)
            for p_ in pl:
                self.add_fixed_orientation_mobjects(p_)
            self.remove(*pl)
            self.play(FadeIn(pl), run_time=0.5)
            # spread comparison
            self.until("b2", "Its principal differences")
            barS = principal_bars([1.0, 0.0, -1.0], [C_X, C_Y, C_Z], [r"\tau", "0", r"-\tau"], 2.6, 1.9)
            barU = principal_bars([1.0, 0.0, 0.0], [C_X, C_Y, C_Z], [r"\sigma", "", ""], 2.6, -0.5)

            sS = M(r"\text{differences } \tau,\ \tau,\ 2\tau\ \Rightarrow\ \textstyle\sum(\Delta\sigma)^2=6\tau^2", size=34)
            sS.next_to(barS, DOWN, 0.45)
            sU = M(r"\text{differences } \sigma,\ \sigma,\ 0\ \Rightarrow\ \textstyle\sum(\Delta\sigma)^2=2\sigma^2", size=34)
            sU.next_to(barU, DOWN, 0.45)
            tS = T("pure shear", size=24, color=C_SHEAR).next_to(barS, UP, 0.2)
            tU = T("uniaxial tension", size=24, color=DIM).next_to(barU, UP, 0.2)
            fixed(self, barS, barU, sS, sU, tS, tU)
            self.play(FadeIn(barS), FadeIn(tS), run_time=0.7)
            self.play(Write(sS), run_time=1.4)
            self.until("b2", "against two sigma")
            self.play(FadeIn(barU), FadeIn(tU), Write(sU), run_time=1.4)
            self.until("b2", "So shear")
            res = M(r"6\tau^2=2\sigma_Y^2\ \Rightarrow\ \tau_Y=\sigma_Y/\sqrt3", size=40, color=C_VM).move_to([2.6, -2.9, 0])
            fixed(self, res)
            self.play(Write(res), run_time=1.3)
            self.wait(self.left(0.6))
            self.play(FadeOut(VGroup(titB, cubeB.cube, prin, pl, barS, barU, sS, sU, tS, tU, res)), run_time=0.6)


class S04b_CasesCD(N3DScene):
    def construct(self):
        self.set_camera_orientation(phi=PHI, theta=THETA, zoom=0.95)
        CPOS = screen(-3.7, -0.3)
        # ---------------------------------------------------------------- Case C
        sigC = np.diag([1.0, 1.0, 0.0])
        cubeC = stress_cube(sigC, size=1.9, scale=1.0).move_to(CPOS)
        titC = fixed(self, case_title("C", "Equal biaxial tension"))
        mC = VGroup(M(r"\sigma_1=\sigma_2=\sigma,\quad\sigma_3=0", size=40),
                    M(r"\sigma_{vm}=\sqrt{\tfrac12\left[0^2+\sigma^2+\sigma^2\right]}=|\sigma|", size=42, color=C_VM),
                    T("thin spherical shell:  σ_θ = σ_φ = pR / 2t", size=24, color=DIM)).arrange(DOWN, buff=0.45,
                                                                                         aligned_edge=LEFT)
        mC.move_to([2.6, 1.6, 0])
        fixed(self, mC)
        with self.say("cc1") as d:
            self.play(FadeIn(titC), FadeIn(cubeC.cube), run_time=0.7)
            self.play(LaggedStart(*[GrowFromPoint(a, CPOS) for a in cubeC.normals], lag_ratio=0.15), run_time=1.0)
            self.play(Write(mC[0]), run_time=1.0)
            self.play(FadeIn(mC[2]), run_time=0.6)
            self.until("cc1", "The differences")
            self.play(Write(mC[1]), run_time=1.4)
        with self.say("cc2") as d:
            dec = M(r"(\sigma,\sigma,0)", r"=", r"(\sigma,\sigma,\sigma)", r"+", r"(0,0,-\sigma)", size=42)
            dec.move_to([2.6, -0.6, 0])
            dec[2].set_color(C_HYD); dec[4].set_color(C_DEV)
            la = VGroup(T("hydrostatic: invisible", size=22, color=C_HYD).next_to(dec[2], DOWN, 0.2),
                        T("uniaxial compression", size=22, color=C_DEV).next_to(dec[4], DOWN, 0.62))
            concl = M(r"\Rightarrow\ \sigma_{vm}=\sigma_{vm}(\text{uniaxial})=|\sigma|", size=38, color=C_VM)
            concl.move_to([2.6, -2.2, 0])
            fixed(self, dec, la, concl)
            self.play(Write(dec), run_time=1.8)
            self.play(FadeIn(la), run_time=0.6)
            # element squeezed thinner in z
            self.until("cc2", "The hydrostatic part")
            self.play(cubeC.cube.animate.apply_matrix(np.diag([1.08, 1.08, 0.8]), about_point=CPOS), run_time=1.6)
            self.until("cc2", "despite two")
            self.play(Write(concl), run_time=1.4)
            self.wait(self.left(0.6))
            self.play(FadeOut(VGroup(titC, mC, dec, la, concl, cubeC)), run_time=0.6)
        # ---------------------------------------------------------------- Case D
        sigD = -0.8 * np.eye(3)
        cubeD = stress_cube(sigD, size=1.9, scale=0.9).move_to(CPOS)
        for a in cubeD.normals:
            a.set_color(C_HYD)
        titD = fixed(self, case_title("D", "Hydrostatic stress"))
        mD = VGroup(M(r"\sigma_1=\sigma_2=\sigma_3=p", size=42),
                    M(r"\sigma_{vm}=\sqrt{\tfrac12\left[0+0+0\right]}=0", size=44, color=C_VM),
                    T("for any p — no distortion, no yield", size=26, color=INK)).arrange(DOWN, buff=0.45,
                                                                                    aligned_edge=LEFT)
        mD.move_to([2.6, 1.3, 0])
        fixed(self, mD)
        with self.say("dd1") as d:
            self.play(FadeIn(titD), FadeIn(cubeD.cube), run_time=0.6)
            self.play(LaggedStart(*[GrowFromPoint(a, a.get_center()) for a in cubeD.normals], lag_ratio=0.08),
                      run_time=1.0)
            self.play(Write(mD[0]), run_time=0.9)
            self.until("dd1", "Every difference")
            self.play(Write(mD[1]), run_time=1.2)
            self.play(FadeIn(mD[2]), run_time=0.5)
        with self.say("dd2") as d:
            self.play(FadeOut(VGroup(cubeD, mD)), run_time=0.6)
            # subsea illustration (2D overlay)
            sea = Rectangle(width=14.3, height=6.3, fill_color="#06223A", fill_opacity=1, stroke_width=0)
            sea.move_to([0, -0.85, 0])
            grad = VGroup(*[Rectangle(width=14.3, height=0.3, fill_color="#0B3A5E", fill_opacity=0.25 * (1 - k / 21),
                                      stroke_width=0).move_to([0, 2.25 - k * 0.3, 0]) for k in range(21)])
            depth = VGroup(T("3000 m", size=30, weight=BOLD), M(r"p\approx\rho g h\approx 30\ \text{MPa}", size=34))
            depth.arrange(DOWN, aligned_edge=LEFT).move_to([-5.3, 1.75, 0])
            blk = Square(1.5, fill_color=C_STEEL, fill_opacity=0.9, stroke_color=INK, stroke_width=2).move_to([-2.6, 0.35, 0])
            blk_arr = VGroup()
            for v in (UP, DOWN, LEFT, RIGHT):
                for o in (-0.45, 0.45):
                    pv_ = np.array([-v[1], v[0], 0])
                    s0 = blk.get_center() + v * 1.45 + pv_ * o
                    blk_arr.add(Arrow(s0, s0 - v * 0.55, buff=0, color=C_HYD, stroke_width=4,
                                      max_tip_length_to_length_ratio=0.35))
            blk_t = VGroup(T("solid block", size=26, weight=SEMIBOLD),
                           M(r"\boldsymbol{\sigma}=-30\,\mathbf{I}\ \text{MPa}", size=32, color=C_HYD),
                           M(r"\sigma_{vm}=0", size=36, color=C_GOOD)).arrange(DOWN, buff=0.18)
            blk_t.next_to(blk, DOWN, 0.7)
            ring = Annulus(inner_radius=0.95, outer_radius=1.12, fill_color=C_STEEL, fill_opacity=0.95,
                           stroke_color=INK, stroke_width=2).move_to([3.0, 0.35, 0])
            inside = Circle(radius=0.95, fill_color="#0B0F19", fill_opacity=1, stroke_width=0).move_to(ring)
            in_t = T("1 atm", size=22, color=DIM).move_to(ring)
            ring_arr = VGroup(*[Arrow(ring.get_center() + 1.75 * np.array([np.cos(a), np.sin(a), 0]),
                                      ring.get_center() + 1.2 * np.array([np.cos(a), np.sin(a), 0]), buff=0, color=C_HYD,
                                      stroke_width=4, max_tip_length_to_length_ratio=0.35)
                                for a in np.linspace(0, TAU, 10, endpoint=False)])
            pipe_t = VGroup(T("sealed pipe, D/t = 20", size=26, weight=SEMIBOLD),
                            M(r"\sigma_\theta\approx-\frac{pD}{2t}\approx-300\ \text{MPa}", size=32, color=C_SHEAR),
                            M(r"\sigma_{vm}\approx 250\ \text{MPa}", size=36, color=C_BAD)).arrange(DOWN, buff=0.18)
            pipe_t.next_to(ring, DOWN, 0.7)
            fixed(self, sea, grad, depth, blk, blk_arr, blk_t, inside, ring, in_t, ring_arr, pipe_t)
            self.play(FadeIn(sea), FadeIn(grad), FadeIn(depth), run_time=1.0)
            self.play(FadeIn(blk), LaggedStart(*[GrowArrow(a) for a in blk_arr], lag_ratio=0.05), run_time=1.0)
            self.play(FadeIn(blk_t), run_time=0.8)
            self.until("dd2", "A sealed pipe")
            self.play(FadeIn(inside), FadeIn(ring), FadeIn(in_t), LaggedStart(*[GrowArrow(a) for a in ring_arr],
                                                                             lag_ratio=0.05), run_time=1.2)
            self.play(FadeIn(pipe_t), run_time=1.0)
            self.until("dd2", "It is the pressure")
            msg = T("the pressure difference distorts — not the pressure", size=28, color=INK).to_edge(DOWN, 0.3)
            fixed(self, msg)
            self.play(FadeIn(msg), run_time=0.7)
            self.wait(self.left(0.5))
            self.play(FadeOut(VGroup(sea, grad, depth, blk, blk_arr, blk_t, ring, inside, in_t, ring_arr, pipe_t, msg)),
                      run_time=0.6)
        with self.say("dd3") as d:
            l1 = VGroup(T("pressure-sensitive materials", size=30, weight=SEMIBOLD, color=C_YIELD),
                        T("soils · concrete · polymers · porous and cast metals", size=26, color=INK))
            l1.arrange(DOWN, aligned_edge=LEFT, buff=0.15)
            dp = M(r"\text{Drucker–Prager:}\ \ \sqrt{J_2}=k-\alpha I_1", size=38)
            gu = T("Gurson: yield depends on void volume fraction and mean stress", size=24, color=DIM)
            l2 = VGroup(T("dense steel", size=30, weight=SEMIBOLD, color=C_YIELD),
                        M(r"\text{triaxiality}\ \ \eta=\sigma_m/\sigma_{vm}\ \uparrow\ \Rightarrow\ \text{void growth}\uparrow,"
                          r"\ \text{ductility}\downarrow", size=34))
            l2.arrange(DOWN, aligned_edge=LEFT, buff=0.15)
            col = VGroup(l1, dp, gu, l2).arrange(DOWN, aligned_edge=LEFT, buff=0.38).move_to([0.4, -0.3, 0])
            fixed(self, col)
            self.play(FadeIn(l1), run_time=0.8)
            self.until("dd3", "and need criteria")
            self.play(Write(dp), FadeIn(gu), run_time=1.4)
            self.until("dd3", "And in steel")
            self.play(FadeIn(l2), run_time=1.0)
            self.wait(self.left(0.6))
            self.play(FadeOut(VGroup(col, titD)), run_time=0.6)


class S04c_CaseE(N3DScene):
    def construct(self):
        self.set_camera_orientation(phi=70 * DEGREES, theta=-62 * DEGREES, zoom=0.9)
        tit = fixed(self, case_title("E", "Axial force + torque"))
        r, Ls = 0.85, 5.0
        shaft = Cylinder(radius=r, height=Ls, direction=RIGHT, resolution=(28, 6), fill_color=C_STEEL,
                         fill_opacity=1.0, stroke_width=0.3, stroke_color="#5A6578", checkerboard_colors=False)
        shaft.move_to(ORIGIN)
        ends = VGroup()
        for sgn in (1, -1):
            ends.add(Arrow3D(np.array([sgn * Ls / 2, 0, 0]), np.array([sgn * (Ls / 2 + 1.1), 0, 0]), color=C_X,
                             thickness=0.04, height=0.3, base_radius=0.1, resolution=8))
        tor = VGroup()
        for sgn in (1, -1):
            t0_, t1_ = 0.3, 0.3 + 1.6 * PI
            arc = ParametricFunction(lambda t, s=sgn: np.array([s * (Ls / 2 - 0.35),
                                                               (r + 0.25) * np.cos(t if s > 0 else t0_ + t1_ - t),
                                                               (r + 0.25) * np.sin(t if s > 0 else t0_ + t1_ - t)]),
                                     t_range=[t0_, t1_], color=C_SHEAR, stroke_width=6)
            tor.add(arc)
            pend = arc.get_end(); pprev = arc.point_from_proportion(0.97)
            tor.add(Arrow3D(pprev, pend + (pend - pprev) * 3, color=C_SHEAR, thickness=0.02, height=0.25,
                            base_radius=0.09, resolution=8))
        # surface element on top of the shaft
        el = Square(0.6, fill_color=C_VM, fill_opacity=0.35, stroke_color=INK, stroke_width=2)
        el.move_to(np.array([0.3, 0, r + 0.01]))
        el_s = VGroup(Arrow3D(np.array([0.6, 0, r + 0.02]), np.array([1.25, 0, r + 0.02]), color=C_X, thickness=0.025,
                              height=0.18, base_radius=0.06, resolution=8),
                      Arrow3D(np.array([0.0, 0, r + 0.02]), np.array([-0.65, 0, r + 0.02]), color=C_X, thickness=0.025,
                              height=0.18, base_radius=0.06, resolution=8),
                      Arrow3D(np.array([0.62, -0.25, r + 0.03]), np.array([0.62, 0.25, r + 0.03]), color=C_SHEAR,
                              thickness=0.022, height=0.16, base_radius=0.055, resolution=8),
                      Arrow3D(np.array([-0.02, 0.25, r + 0.03]), np.array([-0.02, -0.25, r + 0.03]), color=C_SHEAR,
                              thickness=0.022, height=0.16, base_radius=0.055, resolution=8))
        mE = VGroup(M(r"\sigma=\frac{N}{A}", r",\qquad", r"\tau=\frac{T\,r}{J}", size=40),
                    M(r"\sigma_{vm}", r"=\sqrt{\sigma^2+3\tau^2}", size=52)).arrange(DOWN, buff=0.45)
        mE[0][0].set_color(C_X); mE[0][2].set_color(C_SHEAR); mE[1][0].set_color(C_VM)
        mE.to_corner(UR).shift(DOWN * 0.6 + LEFT * 0.3)
        fixed(self, mE)
        with self.say("e1") as d:
            self.play(FadeIn(tit), FadeIn(shaft), run_time=1.0)
            self.begin_ambient_camera_rotation(rate=0.07)
            self.play(*[GrowFromPoint(a, a.get_start()) for a in ends], run_time=0.8)
            self.play(*[Create(t_) for t_ in tor], run_time=1.0)
            self.until("e1", "At the surface")
            self.play(FadeIn(el), *[FadeIn(a) for a in el_s], run_time=0.9)
            self.play(Write(mE[0]), run_time=1.2)
            self.until("e1", "The von Mises")
            self.play(Write(mE[1]), run_time=1.3)
        with self.say("e2") as d:
            self.stop_ambient_camera_rotation()
            self.play(FadeOut(VGroup(shaft, ends, tor, el, el_s)), mE.animate.scale(0.8).to_corner(UL).shift(DOWN * 1.3),
                      run_time=0.8)
            ax = Axes(x_range=[0, 1.2, 0.25], y_range=[0, 0.7, 0.25], x_length=6.4, y_length=4.0, tips=False,
                      axis_config=dict(color=DIM, stroke_width=2, include_ticks=False)).move_to([1.6, -0.35, 0])
            xl = M(r"\sigma/\sigma_Y", size=32, color=C_X).next_to(ax.x_axis, RIGHT, 0.1)
            yl = M(r"\tau/\sigma_Y", size=32, color=C_SHEAR).next_to(ax.y_axis, UP, 0.1)
            vmc = ax.plot_parametric_curve(lambda t: np.array([np.cos(t), np.sin(t) / np.sqrt(3), 0]),
                                           t_range=[0, PI / 2], color=C_VM, stroke_width=5)
            trc = DashedVMobject(ax.plot_parametric_curve(lambda t: np.array([np.cos(t), np.sin(t) / 2, 0]),
                                                          t_range=[0, PI / 2], color=C_TRESCA, stroke_width=4), num_dashes=40)
            vlab = M(r"\sigma^2+3\tau^2=\sigma_Y^2", size=32, color=C_VM).move_to(ax.c2p(0.95, 0.56))
            tlab = M(r"\sigma^2+4\tau^2=\sigma_Y^2\ \text{(Tresca)}", size=28, color=C_TRESCA).move_to(ax.c2p(0.5, 0.15))
            k1 = M(r"1", size=30).next_to(ax.c2p(1, 0), DOWN, 0.15)
            k2 = M(r"0.577", size=28, color=C_VM).next_to(ax.c2p(0, 1 / np.sqrt(3)), LEFT, 0.12)
            k3 = M(r"0.5", size=28, color=C_TRESCA).next_to(ax.c2p(0, 0.5), LEFT, 0.12)
            el_t = T("elastic", size=26, color=DIM).move_to(ax.c2p(0.35, 0.22))
            plot = VGroup(ax, xl, yl, vmc, trc, vlab, tlab, k1, k2, k3, el_t)
            fixed(self, plot)
            self.play(Create(ax), FadeIn(xl), FadeIn(yl), run_time=1.0)
            self.play(Create(vmc), FadeIn(vlab), FadeIn(k1), FadeIn(k2), FadeIn(el_t), run_time=1.6)
            self.until("e2", "In 1931")
            tq = VGroup(T("Taylor & Quinney, 1931", size=26, weight=SEMIBOLD),
                        T("thin-walled tubes in tension + torsion", size=22, color=DIM),
                        T("Cu, Al, mild steel: closer to von Mises", size=22, color=DIM)).arrange(DOWN, aligned_edge=LEFT,
                                                                                            buff=0.12)
            tq.to_corner(DR).shift(UP * 0.2 + LEFT * 0.1)
            fixed(self, tq)
            self.play(FadeIn(tq), run_time=0.8)
            self.until("e2", "than to the maximum")
            self.play(Create(trc), FadeIn(tlab), FadeIn(k3), run_time=1.4)
            shf = M(r"\text{solid shaft, bending + torsion:}\ \ \sigma_{vm}=\frac{32}{\pi d^3}\sqrt{M^2+\tfrac34T^2}",
                    size=30, color=INK).to_edge(DOWN, 0.25)
            fixed(self, shf)
            self.play(FadeIn(shf), run_time=0.8)
            self.wait(self.left(0.4) + 1.6)
            self.play(FadeOut(VGroup(plot, tq, shf, mE, tit)), run_time=0.6)
