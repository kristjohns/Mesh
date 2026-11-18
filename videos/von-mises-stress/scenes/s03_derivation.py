"""Section 3 - deriving the von Mises criterion (principal stresses -> energy split -> J2 -> sigma_vm)."""
from common import *  # noqa: F401,F403

S1C, S2C, S3C = C_X, C_Y, C_Z
SIDEBAR_X = -5.2


def sig_colors(m):
    """Colour sigma_1/2/3 and s_1/2/3 glyph groups inside a MathTex by matching tex strings."""
    return m


class Sidebar(VGroup):
    """Running list of established results (left column)."""

    def __init__(self):
        super().__init__()
        self.title = T("established", size=20, color=DIM).move_to([SIDEBAR_X, 3.55, 0])
        self.rule = Line([SIDEBAR_X - 1.75, 3.3, 0], [SIDEBAR_X + 1.75, 3.3, 0], color=FAINT, stroke_width=1.5)
        self.items = VGroup()
        self.add(self.title, self.rule, self.items)

    def push(self, scene, tex_mob, run_time=0.9):
        tgt = tex_mob.copy()
        tgt.scale(0.8)
        if tgt.width > 3.55:
            tgt.scale_to_fit_width(3.55)
        y = 2.95 - sum(it.height + 0.34 for it in self.items)
        tgt.move_to([SIDEBAR_X, y - tgt.height / 2, 0])
        scene.play(TransformFromCopy(tex_mob, tgt), run_time=run_time)
        self.items.add(tgt)


class S03a_Derivation(NScene):
    def construct(self):
        section_card(self, 3, "Deriving the von Mises criterion")
        sb = Sidebar()
        divider = Line([-3.2, 3.6, 0], [-3.2, -3.6, 0], color=FAINT, stroke_width=1.5)
        CX = 1.95                                     # centre of the main board
        # ---------------------------------------------------------------- v1 principal orientation
        with self.say("v1") as d:
            sx, sy, txy = 1.0, 0.15, 0.55
            th = ValueTracker(0.0)
            ctr = np.array([CX - 2.6, 0.2, 0])

            def element():
                t_ = th.get_value()
                c2, s2 = np.cos(2 * t_), np.sin(2 * t_)
                a_ = (sx + sy) / 2 + (sx - sy) / 2 * c2 + txy * s2
                b_ = (sx + sy) / 2 - (sx - sy) / 2 * c2 - txy * s2
                t2 = -(sx - sy) / 2 * s2 + txy * c2
                R = np.array([[np.cos(t_), -np.sin(t_), 0], [np.sin(t_), np.cos(t_), 0], [0, 0, 1]])
                ex, ey = R[:, 0], R[:, 1]
                h = 1.1
                sq = Square(2 * h, color=INK, stroke_width=2, fill_color=C_STEEL, fill_opacity=0.18)
                sq.rotate(t_).move_to(ctr)
                g = VGroup(sq)
                for vec, val, col in ((ex, a_, S1C), (ey, b_, S2C)):
                    for sgn in (1, -1):
                        p0 = ctr + sgn * vec * h
                        ln = 0.3 + 1.2 * abs(val)
                        st, en = (p0, p0 + sgn * vec * ln) if val > 0 else (p0 + sgn * vec * ln, p0)
                        g.add(Arrow(st, en, buff=0, color=col, stroke_width=5, max_tip_length_to_length_ratio=0.3))
                if abs(t2) > 0.02:
                    for vec, other in ((ex, ey), (ey, ex)):
                        for sgn in (1, -1):
                            p0 = ctr + sgn * vec * (h + 0.12)
                            dd = sgn * np.sign(t2) * other * (0.25 + 1.6 * abs(t2)) / 2
                            g.add(Arrow(p0 - dd, p0 + dd, buff=0, color=C_SHEAR, stroke_width=5,
                                        max_tip_length_to_length_ratio=0.35))
                return g
            el = always_redraw(element)
            self.play(FadeIn(el), Create(divider), FadeIn(sb), run_time=1.0)
            thp = 0.5 * np.arctan2(2 * txy, sx - sy)
            self.play(th.animate.set_value(thp), run_time=self.till("v1", "The normal stresses", minimum=2.0),
                      rate_func=smooth)
            el.clear_updaters()
            lab = T("principal orientation: no shear", size=24, color=DIM).next_to(el, DOWN, 0.4)
            self.play(FadeIn(lab), run_time=0.5)
            eq1 = M(r"\det(\boldsymbol{\sigma}-\lambda\mathbf{I})=0", size=44).move_to([CX + 1.4, 1.5, 0])
            eq2 = M(r"\lambda^3-I_1\lambda^2+I_2\lambda-I_3=0", size=44).next_to(eq1, DOWN, 0.5)
            roots = M(r"\lambda\in\{", r"\sigma_1", r",\,", r"\sigma_2", r",\,", r"\sigma_3", r"\}", r",\quad",
                      r"\sigma_1\ge\sigma_2\ge\sigma_3", size=40).next_to(eq2, DOWN, 0.5)
            roots[1].set_color(S1C); roots[3].set_color(S2C); roots[5].set_color(S3C)
            self.until("v1", "eigenvalues")
            self.play(Write(eq1), run_time=1.0)
            self.play(Write(eq2), run_time=1.0)
            self.play(FadeIn(roots), run_time=0.8)
        # ---------------------------------------------------------------- v2 invariants
        with self.say("v2") as d:
            self.play(FadeOut(VGroup(el, lab, eq1, roots)), eq2.animate.move_to([CX, 2.7, 0]), run_time=0.8)
            inv = VGroup(
                M(r"I_1=\sigma_x+\sigma_y+\sigma_z", r"=\sigma_1+\sigma_2+\sigma_3", size=36),
                M(r"I_2=\sigma_x\sigma_y+\sigma_y\sigma_z+\sigma_z\sigma_x-\tau_{xy}^2-\tau_{yz}^2-\tau_{zx}^2",
                  size=32),
                M(r"=\sigma_1\sigma_2+\sigma_2\sigma_3+\sigma_3\sigma_1", size=32),
                M(r"I_3=\det\boldsymbol{\sigma}", r"=\sigma_1\sigma_2\sigma_3", size=36),
            ).arrange(DOWN, buff=0.32, aligned_edge=LEFT).move_to([CX, 0.55, 0])
            inv[2].align_to(inv[1], RIGHT)
            self.play(LaggedStart(*[FadeIn(x, shift=0.1 * RIGHT) for x in inv], lag_ratio=0.25), run_time=2.4)
            self.until("v2", "For an isotropic")
            iso = M(r"\text{isotropy}\ \Rightarrow\ f(\boldsymbol{\sigma})=f(I_1,I_2,I_3)", size=40, color=C_YIELD)
            iso.move_to([CX, -1.9, 0])
            self.play(Write(iso), run_time=1.2)
            sb.push(self, iso)
            self.wait(self.left(0.6))
            self.play(FadeOut(VGroup(inv, eq2, iso)), run_time=0.6)
        # ---------------------------------------------------------------- v3 deviators on a number line
        with self.say("v3") as d:
            nl = NumberLine(x_range=[-80, 320, 40], length=8.4, color=DIM, include_numbers=False,
                            stroke_width=2).move_to([CX, -0.6, 0])
            vals = ValueTracker(0.0)
            base = [240, 80, -40]
            cols = [S1C, S2C, S3C]

            def numline_objs():
                sh = vals.get_value()
                v = [b + sh for b in base]
                sm_ = sum(v) / 3
                g = VGroup()
                for k_, (x_, c_) in enumerate(zip(v, cols)):
                    p_ = nl.n2p(x_)
                    g.add(Dot(p_, radius=0.09, color=c_))
                    g.add(MathTex(rf"\sigma_{k_ + 1}", color=c_, font_size=36).next_to(p_, DOWN, 0.22))
                    y_off = 0.55 + 0.42 * k_
                    st = nl.n2p(sm_) + UP * y_off
                    en = p_ + UP * y_off
                    if abs(x_ - sm_) > 1:
                        g.add(Arrow(st, en, buff=0, color=C_DEV, stroke_width=4, max_tip_length_to_length_ratio=0.12))
                        g.add(MathTex(rf"s_{k_ + 1}", color=C_DEV, font_size=30).next_to(en, RIGHT if x_ > sm_ else LEFT,
                                                                                   0.1))
                pm = nl.n2p(sm_)
                g.add(DashedLine(pm + DOWN * 0.35, pm + UP * 1.9, color=C_HYD, stroke_width=2.5))
                g.add(MathTex(r"\sigma_m", color=C_HYD, font_size=34).next_to(pm + UP * 1.9, UP, 0.08))
                return g
            objs = always_redraw(numline_objs)
            e1 = M(r"\sigma_m=\tfrac{1}{3}I_1", r",\qquad", r"s_i=\sigma_i-\sigma_m", size=40).move_to([CX, 2.75, 0])
            e1[0].set_color(C_HYD); e1[2].set_color(C_DEV)
            self.play(Create(nl), FadeIn(objs), Write(e1), run_time=1.6)
            self.until("v3", "which always sum")
            e2 = M(r"s_1+s_2+s_3=0", size=40, color=C_DEV).next_to(e1, DOWN, 0.35)
            self.play(Write(e2), run_time=0.9)
            self.until("v3", "and do not change")
            self.play(vals.animate.set_value(70), run_time=1.4)
            self.play(vals.animate.set_value(-30), run_time=1.2)
            self.play(vals.animate.set_value(0), run_time=0.8)
            objs.clear_updaters()
            sb.push(self, e2)
            self.play(FadeOut(VGroup(nl, objs, e1, e2)), run_time=0.5)
        # ---------------------------------------------------------------- v4 energy, Hooke split
        with self.say("v4") as d:
            u0 = M(r"U", r"=", r"\tfrac12\,\boldsymbol{\sigma}:\boldsymbol{\varepsilon}", size=48).move_to([CX, 2.5, 0])
            sdec = M(r"\boldsymbol{\sigma}", r"=", r"\sigma_m\mathbf{I}", r"+", r"\mathbf{s}", size=44)
            edec = M(r"\boldsymbol{\varepsilon}", r"=", r"\frac{\sigma_m}{3K}\mathbf{I}", r"+", r"\frac{1}{2G}\mathbf{s}",
                     size=44)
            sdec[2].set_color(C_HYD); sdec[4].set_color(C_DEV); edec[2].set_color(C_HYD); edec[4].set_color(C_DEV)
            grp = VGroup(sdec, edec).arrange(DOWN, buff=0.45, aligned_edge=LEFT).move_to([CX, 0.5, 0])
            kk = VGroup(M(r"K=\frac{E}{3(1-2\nu)}\ \text{(bulk)}", size=32, color=C_HYD),
                        M(r"G=\frac{E}{2(1+\nu)}\ \text{(shear)}", size=32, color=C_DEV)).arrange(RIGHT, buff=0.8)
            kk.move_to([CX, -1.6, 0])
            self.play(Write(u0), run_time=1.2)
            self.until("v4", "In Hooke")
            self.play(FadeIn(sdec), run_time=0.8)
            self.play(FadeIn(edec), run_time=1.0)
            self.until("v4", "bulk modulus")
            self.play(FadeIn(kk[0]), run_time=0.6)
            self.until("v4", "shear modulus")
            self.play(FadeIn(kk[1]), run_time=0.6)
        # ---------------------------------------------------------------- v5 cross terms vanish
        with self.say("v5") as d:
            self.play(FadeOut(VGroup(grp, kk)), u0.animate.move_to([CX, 2.8, 0]), run_time=0.6)
            ex = M(r"U=", r"\frac{\sigma_m^2}{2K}", r"+", r"\frac{\sigma_m}{4G}\,\mathbf{I}:\mathbf{s}", r"+",
                   r"\frac{\sigma_m}{6K}\,\mathbf{s}:\mathbf{I}", r"+", r"\frac{\mathbf{s}:\mathbf{s}}{4G}", size=42)
            ex.move_to([CX, 1.55, 0])
            if ex.width > 9.4:
                ex.scale_to_fit_width(9.4)
            ex[1].set_color(C_HYD); ex[7].set_color(C_DEV)
            self.play(Write(ex), run_time=2.0)
            self.until("v5", "because")
            note = M(r"\mathbf{I}:\mathbf{s}=\operatorname{tr}\mathbf{s}=0", size=40, color=C_YIELD).move_to([CX, 0.2, 0])
            self.play(Write(note), run_time=1.0)
            x1 = Cross(ex[3], stroke_color=C_BAD, stroke_width=5)
            x2 = Cross(ex[5], stroke_color=C_BAD, stroke_width=5)
            self.play(Create(x1), Create(x2), run_time=0.8)
            self.until("v5", "The energy separates")
            res = M(r"U", r"=", r"\underbrace{\frac{\sigma_m^2}{2K}}_{U_{\text{vol}}}", r"+",
                    r"\underbrace{\frac{\mathbf{s}:\mathbf{s}}{4G}}_{U_{\text{dist}}}", size=46).move_to([CX, -1.6, 0])
            res[2].set_color(C_HYD); res[4].set_color(C_DEV)
            self.play(Write(res), run_time=1.4)
            sb.push(self, res)
            self.wait(self.left(0.5))
            self.play(FadeOut(VGroup(ex, x1, x2, note, u0)), res.animate.move_to([CX, 2.4, 0]), run_time=0.5)
        # ---------------------------------------------------------------- v6 J2
        with self.say("v6") as d:
            j2 = M(r"J_2", r"\equiv\tfrac12\,\mathbf{s}:\mathbf{s}", r"=\tfrac12\left(s_1^2+s_2^2+s_3^2\right)", size=46)
            j2.move_to([CX, 0.7, 0]); j2[0].set_color(C_DEV)
            ud = M(r"U_{\text{dist}}", r"=", r"\frac{J_2}{2G}", size=50).move_to([CX, -0.9, 0])
            ud[0].set_color(C_DEV)
            self.play(Write(j2), run_time=1.6)
            self.play(Write(ud), run_time=1.0)
            sb.push(self, ud, run_time=0.8)
            self.wait(self.left(0.5))
            self.play(FadeOut(VGroup(res, ud)), j2.animate.move_to([CX, 2.85, 0]).scale(0.85), run_time=0.5)
        # ---------------------------------------------------------------- v7 the key identity
        with self.say("v7") as d:
            l1 = M(r"(s_1-s_2)^2+(s_2-s_3)^2+(s_3-s_1)^2", r"=", r"2\textstyle\sum s_i^2", r"-",
                   r"2\textstyle\sum_{i<j} s_is_j", size=33)
            l2 = M(r"0=(s_1+s_2+s_3)^2", r"=", r"\textstyle\sum s_i^2", r"+", r"2\textstyle\sum_{i<j} s_is_j", size=33)
            l3 = M(r"\Rightarrow\ \textstyle\sum_{i<j}(s_i-s_j)^2", r"=", r"3\textstyle\sum s_i^2", r"=", r"6J_2",
                   size=38)
            l4 = M(r"s_i-s_j=(\sigma_i-\sigma_m)-(\sigma_j-\sigma_m)", r"=", r"\sigma_i-\sigma_j", size=36)
            l5 = M(r"J_2", r"=", r"\tfrac16\left[(\sigma_1-\sigma_2)^2+(\sigma_2-\sigma_3)^2+(\sigma_3-\sigma_1)^2\right]",
                   size=40)
            stack = VGroup(l1, l2, l3, l4, l5).arrange(DOWN, buff=0.38).move_to([CX, -0.25, 0])
            if stack.width > 9.4:
                stack.scale_to_fit_width(9.4)
            for l_ in (l1, l2, l3, l4):
                l_.align_to(stack, LEFT)
            l5[0].set_color(C_DEV)
            self.play(Write(l1), run_time=1.6)
            self.play(Write(l2), run_time=1.6)
            self.play(Write(l3), run_time=1.2)
            self.until("v7", "And a difference")
            self.play(Write(l4), run_time=1.4)
            self.until("v7", "So J two")
            self.play(Write(l5), run_time=1.6)
            box = caption_box(l5, color=C_DEV)
            self.play(Create(box), run_time=0.5)
            sb.push(self, l5)
            self.wait(self.left(0.5))
            self.play(FadeOut(VGroup(l1, l2, l3, l4, l5, box, j2)), run_time=0.5)
        # ---------------------------------------------------------------- v8 calibration in the tension test
        with self.say("v8") as d:
            names = T("Huber 1904 · von Mises 1913 · Hencky 1924", size=24, color=DIM).move_to([CX, 3.0, 0])
            hyp = M(r"\text{yield when}\quad U_{\text{dist}}=U_{\text{dist}}\big|_{\text{tension test at yield}}",
                    size=40).move_to([CX, 2.2, 0])
            hyp[0].set_color(INK)
            self.play(FadeIn(names), Write(hyp), run_time=1.8)
            self.until("v8", "sigma one equal")
            tt = M(r"\sigma_1=\sigma_Y,\quad \sigma_2=\sigma_3=0", size=42).move_to([CX, 0.95, 0])
            tt[0][3:5].set_color(C_YIELD)
            self.play(Write(tt), run_time=1.2)
            nb = VGroup(M(r"\sigma_Y", color=C_YIELD, size=38), T(": yield strength", size=24, color=INK),
                        M(r"\neq", size=38), M(r"\sigma_y", color=S2C, size=38),
                        T(": normal stress in y", size=24, color=INK)).arrange(RIGHT, buff=0.15)
            nb.move_to([CX, -0.1, 0])
            nbb = SurroundingRectangle(nb, color=FAINT, buff=0.18, corner_radius=0.1)
            self.until("v8", "written sigma capital")
            self.play(FadeIn(nb), Create(nbb), run_time=0.9)
            jy = M(r"J_2\big|_Y=\tfrac16\left(\sigma_Y^2+0+\sigma_Y^2\right)=\frac{\sigma_Y^2}{3}", size=40)
            jy.move_to([CX, -1.35, 0])
            uy = M(r"U_{\text{dist}}\big|_Y=\frac{\sigma_Y^2}{6G}", size=42, color=C_DEV).move_to([CX, -2.6, 0])
            self.until("v8", "and the other")
            self.play(Write(jy), run_time=1.2)
            self.play(Write(uy), run_time=0.9)
        # ---------------------------------------------------------------- v9 equate -> sigma_vm
        with self.say("v9") as d:
            self.play(FadeOut(VGroup(names, hyp, tt, nb, nbb, jy)), uy.animate.move_to([CX, 2.6, 0]), run_time=0.6)
            eq = M(r"\frac{J_2}{2", r"G", r"}", r"=", r"\frac{\sigma_Y^2}{6", r"G", r"}", size=54).move_to([CX, 1.3, 0])
            self.play(Write(eq), run_time=1.2)
            self.until("v9", "The shear modulus cancels")
            c1 = Line(eq[1].get_corner(DL), eq[1].get_corner(UR), color=C_BAD, stroke_width=5)
            c2 = Line(eq[5].get_corner(DL), eq[5].get_corner(UR), color=C_BAD, stroke_width=5)
            self.play(Create(c1), Create(c2), run_time=0.7)
            nt = T("independent of the elastic constants", size=24, color=DIM).next_to(eq, DOWN, 0.3)
            self.play(FadeIn(nt), run_time=0.5)
            self.until("v9", "What remains")
            r3 = M(r"3J_2=\sigma_Y^2", size=46).move_to([CX, -0.35, 0])
            self.play(Write(r3), run_time=0.8)
            vm = M(r"\sigma_{vm}", r"\equiv", r"\sqrt{\tfrac12\left[(\sigma_1-\sigma_2)^2+(\sigma_2-\sigma_3)^2+(\sigma_3-\sigma_1)^2\right]}",
                   size=42).move_to([CX, -1.75, 0])
            vm[0].set_color(C_VM)
            self.play(Write(vm), run_time=2.2)
            self.until("v9", "Equivalently")
            vm2 = M(r"=\sqrt{3J_2}", size=44, color=C_VM).next_to(vm, DOWN, 0.35)
            box = caption_box(VGroup(vm, vm2), color=C_VM)
            self.play(Write(vm2), Create(box), run_time=1.0)
            sb.push(self, VGroup(vm[0], vm2).copy().arrange(RIGHT, buff=0.1))
            self.wait(self.left(0.6))
            self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)


class S03b_RMSShear(N3DScene):
    """Sphere of plane normals coloured by the shear traction magnitude; RMS shear ~ sqrt(J2)."""

    def construct(self):
        self.set_camera_orientation(phi=66 * DEGREES, theta=-35 * DEGREES, zoom=1.0)
        S = np.diag([240.0, 80.0, -40.0])
        tmax = 140.0
        import matplotlib
        cm = matplotlib.colormaps["inferno"]

        def tau_n(n):
            t = S @ n
            sn = n @ t
            return np.sqrt(max(t @ t - sn * sn, 0.0))
        R = 1.85
        sph = Surface(lambda u, v: R * np.array([np.cos(u) * np.sin(v), np.sin(u) * np.sin(v), np.cos(v)]),
                      u_range=[0, TAU], v_range=[0, PI], resolution=(40, 22), stroke_width=0.0, fill_opacity=1.0)
        for face in sph:
            c = face.get_center()
            n = c / np.linalg.norm(c)
            val = tau_n(n) / tmax
            face.set_fill(matplotlib.colors.to_hex(cm(0.08 + 0.85 * val)), opacity=1.0)
            face.set_stroke(width=0)
        th_, ph_ = -35 * DEGREES, 66 * DEGREES
        right_ = np.array([-np.sin(th_), np.cos(th_), 0])
        C0 = right_ * -3.3
        sph.shift(C0)
        axes_lab = VGroup()
        for i, (vec, col, lab) in enumerate(((RIGHT, S1C, r"\sigma_1"), (UP, S2C, r"\sigma_2"), (OUT, S3C, r"\sigma_3"))):
            a = Arrow3D(C0 + vec * (R + 0.05), C0 + vec * (R + 0.75), color=col, thickness=0.02,
                        resolution=8, height=0.2, base_radius=0.06)
            axes_lab.add(a)
        ball = VGroup(sph, axes_lab)
        eq = VGroup(
            M(r"\tau(\mathbf{n})=\sqrt{|\boldsymbol{\sigma}\mathbf{n}|^2-(\mathbf{n}\cdot\boldsymbol{\sigma}\mathbf{n})^2}",
              size=36),
            M(r"\langle\tau^2\rangle_{\text{all planes}}=\tfrac25\,J_2", size=40),
            M(r"\tau_{\text{rms}}=\sqrt{\tfrac25 J_2}\quad\Rightarrow\quad", r"\sigma_{vm}=\sqrt{\tfrac{15}{2}}\;\tau_{\text{rms}}",
              size=40),
        ).arrange(DOWN, buff=0.45, aligned_edge=LEFT).to_corner(UR).shift(DOWN * 0.8 + LEFT * 0.2)
        eq[2][1].set_color(C_VM)
        cap = T("shear traction on every plane through the point", size=22, color=DIM).to_corner(DL).shift(UP * 0.3 + RIGHT * 0.6)
        cred = T("Novozhilov, 1952", size=20, color=DIM).next_to(eq, DOWN, 0.4).align_to(eq, LEFT)
        bar = VGroup(*[Rectangle(width=0.35, height=0.22, fill_color=matplotlib.colors.to_hex(cm(0.08 + 0.85 * k / 9)),
                                 fill_opacity=1, stroke_width=0) for k in range(10)]).arrange(RIGHT, buff=0)
        bar.next_to(cap, UP, 0.25).align_to(cap, LEFT).shift(RIGHT * 0.7)
        b0 = M(r"\tau=0", size=26).next_to(bar, LEFT, 0.15)
        b1 = M(r"\tau_{\max}", size=26).next_to(bar, RIGHT, 0.15)
        for mob in (eq, cap, cred, bar, b0, b1):
            self.add_fixed_in_frame_mobjects(mob); self.remove(mob)
        with self.say("r1") as d:
            self.play(FadeIn(ball), FadeIn(cap), FadeIn(bar), FadeIn(b0), FadeIn(b1), run_time=1.2)
            ball.add_updater(lambda m, dt: m.rotate(0.22 * dt, axis=OUT, about_point=C0))
            self.play(Write(eq[0]), run_time=1.4)
            self.until("r1", "the root-mean-square")
            self.play(Write(eq[1]), run_time=1.2)
            self.play(Write(eq[2]), FadeIn(cred), run_time=1.6)
            self.wait(self.left(0.7))
            ball.clear_updaters()
            self.play(FadeOut(Group(*self.mobjects)), run_time=0.7)


class S03c_Cartesian(NScene):
    def construct(self):
        # ---------------------------------------------------------------- c1 shear terms count twice
        with self.say("c1") as d:
            sm = matrix_tex([[r"s_x", r"\tau_{xy}", r"\tau_{xz}"], [r"\tau_{yx}", r"s_y", r"\tau_{yz}"],
                             [r"\tau_{zx}", r"\tau_{zy}", r"s_z"]], size=40, h_buff=1.0)
            for i in range(3):
                sm.get_rows()[i][i].set_color(COMP[i])
            for (i, j) in [(0, 1), (1, 0), (0, 2), (2, 0), (1, 2), (2, 1)]:
                sm.get_rows()[i][j].set_color(C_SHEAR)
            lab = M(r"\mathbf{s}=", size=44).next_to(sm, LEFT, 0.2)
            grp = VGroup(lab, sm).move_to([-3.6, 1.3, 0])
            self.play(FadeIn(grp), run_time=0.8)
            pairs = [((0, 1), (1, 0)), ((0, 2), (2, 0)), ((1, 2), (2, 1))]
            self.until("c1", "each shear stress")
            for (a_, b_) in pairs:
                self.play(Indicate(sm.get_rows()[a_[0]][a_[1]], color=WHITE), Indicate(sm.get_rows()[b_[0]][b_[1]],
                                                                                     color=WHITE), run_time=0.55)
            ss = M(r"\mathbf{s}:\mathbf{s}=s_x^2+s_y^2+s_z^2", r"+2\left(\tau_{xy}^2+\tau_{yz}^2+\tau_{zx}^2\right)",
                   size=40).move_to([2.6, 1.6, 0])
            ss[1].set_color(C_SHEAR)
            self.play(Write(ss), run_time=1.6)
            j2 = M(r"J_2=\tfrac12\left(s_x^2+s_y^2+s_z^2\right)", r"+\tau_{xy}^2+\tau_{yz}^2+\tau_{zx}^2", size=40)
            j2.next_to(ss, DOWN, 0.5)
            j2[1].set_color(C_SHEAR)
            self.until("c1", "So it contributes")
            self.play(Write(j2), run_time=1.4)
        # ---------------------------------------------------------------- c2 normal part = differences only
        with self.say("c2") as d:
            fin = M(r"\sigma_{vm}", r"=\sqrt{", r"\sigma_x^2+\sigma_y^2+\sigma_z^2-\sigma_x\sigma_y-\sigma_y\sigma_z-\sigma_z\sigma_x",
                    r"+3\left(\tau_{xy}^2+\tau_{yz}^2+\tau_{zx}^2\right)", r"}", size=40).move_to([0, -1.0, 0])
            fin[0].set_color(C_VM); fin[3].set_color(C_SHEAR)
            br = Brace(fin[2], DOWN, color=DIM)
            brt = M(r"=\tfrac12\left[(\sigma_x-\sigma_y)^2+(\sigma_y-\sigma_z)^2+(\sigma_z-\sigma_x)^2\right]", size=32,
                    color=DIM).next_to(br, DOWN, 0.15)
            br2 = Brace(fin[3], DOWN, color=C_SHEAR)
            br2t = T("3 × each shear²", size=22, color=C_SHEAR).next_to(br2, DOWN, 0.15)
            self.play(Write(fin), run_time=min(2.0, d * 0.45))
            self.play(GrowFromCenter(br), FadeIn(brt), GrowFromCenter(br2), FadeIn(br2t), run_time=1.0)
            box = caption_box(fin, color=C_VM)
            self.play(Create(box), run_time=0.5)
        # ---------------------------------------------------------------- c3 yield condition + scope
        with self.say("c3") as d:
            keep = VGroup(fin, box)
            self.play(FadeOut(VGroup(grp, ss, j2, br, brt, br2, br2t)), keep.animate.scale(0.72).to_edge(UP, 0.35),
                      run_time=0.8)
            yc = M(r"\text{yield:}\quad", r"\sigma_{vm}", r"=", r"\sigma_Y", size=46).next_to(keep, DOWN, 0.4)
            yc[1].set_color(C_VM); yc[3].set_color(C_YIELD)
            self.play(Write(yc), run_time=1.0)
            # stress-strain curve (schematic)
            ax = Axes(x_range=[0, 1, 0.25], y_range=[0, 1.2, 0.3], x_length=5.6, y_length=3.4, tips=False,
                      axis_config=dict(color=DIM, stroke_width=2, include_ticks=False)).move_to([-3.75, -1.6, 0])
            xl = M(r"\varepsilon", size=32, color=DIM).next_to(ax.x_axis, RIGHT, 0.1)
            yl = M(r"\sigma", size=32, color=DIM).next_to(ax.y_axis, UP, 0.1)

            def curve(x):
                ey = 0.05
                if x < ey:
                    return x / ey * 0.7
                if x < 0.62:
                    return 0.7 + 0.32 * (1 - np.exp(-(x - ey) / 0.18))
                return 0.7 + 0.32 * (1 - np.exp(-(0.62 - ey) / 0.18)) - 1.1 * (x - 0.62) ** 2
            cv = ax.plot(curve, x_range=[0, 0.92], color=INK, stroke_width=4)
            yp = Dot(ax.c2p(0.05, 0.7), color=C_YIELD, radius=0.08)
            ypl = M(r"\sigma_Y", color=C_YIELD, size=34).next_to(yp, LEFT, 0.15)
            fr = Dot(ax.c2p(0.92, curve(0.92)), color=C_BAD, radius=0.08)
            self.play(Create(ax), FadeIn(xl), FadeIn(yl), Create(cv), run_time=1.6)
            self.play(FadeIn(yp), FadeIn(ypl), run_time=0.5)
            on = T("onset of yield ← von Mises", size=22, color=C_YIELD).next_to(yp, RIGHT, 0.35).shift(DOWN * 0.45)
            self.play(FadeIn(on), run_time=0.5)
            items = VGroup(*[T(s, size=25, color=INK) for s in (
                "• isotropic, homogeneous",
                "• ductile: plastic flow by slip",
                "• pressure-insensitive",
                "• equal yield in tension & compression",
                "• initial yield, at a point")]).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
            items.move_to([4.15, -1.35, 0])
            self.until("c3", "Precisely")
            self.play(LaggedStart(*[FadeIn(i_, shift=0.1 * RIGHT) for i_ in items], lag_ratio=0.3),
                      run_time=self.till("c3", "It says nothing", minimum=1.5))
            self.until("c3", "Necking")
            nk = VGroup(T("necking & fracture:", size=21, color=C_BAD), T("different physics", size=21, color=C_BAD))
            nk.arrange(DOWN, buff=0.08).next_to(fr, DOWN, 0.25)
            self.play(FadeIn(fr), FadeIn(nk), run_time=0.7)
            self.wait(self.left(0.6))
            self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)
