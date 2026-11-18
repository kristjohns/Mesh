"""Sections 5 & 6 - the von Mises yield surface in principal stress space; von Mises vs Tresca."""
from common import *  # noqa: F401,F403
from manim.utils.space_ops import z_to_vector

U = 2.0                                   # Manim units per sigma_Y
R_VM = np.sqrt(2 / 3)                     # cylinder radius in sigma_Y
NHAT = np.ones(3) / np.sqrt(3)
PHI0, TH0 = 70 * DEGREES, -60 * DEGREES
PHI_AX, TH_AX = np.arccos(1 / np.sqrt(3)), 45 * DEGREES      # looking down the hydrostatic axis


def W(v):
    """sigma/sigma_Y coordinates -> Manim world point."""
    return np.asarray(v, dtype=float) * U


def dev(v):
    v = np.asarray(v, dtype=float)
    return v - v.mean()


def make_axes():
    ax = VGroup()
    labs = VGroup()
    for i, (col, lab) in enumerate(zip(COMP, [r"\sigma_1", r"\sigma_2", r"\sigma_3"])):
        e = np.eye(3)[i]
        ax.add(Line(W(-1.45 * e), W(1.55 * e), color=col, stroke_width=2.5))
        ax.add(Cone(base_radius=0.06, height=0.2, direction=e, resolution=8, fill_color=col, fill_opacity=1,
                    stroke_width=0).move_to(W(1.55 * e)))
        labs.add(MathTex(lab, color=col, font_size=40).move_to(W(1.75 * e)))
    return ax, labs


def plane_disk(radius, color, opacity, center=ORIGIN):
    c = Circle(radius=radius * U, fill_color=color, fill_opacity=opacity, stroke_color=color, stroke_width=1.5)
    c.apply_matrix(z_to_vector(NHAT)).move_to(W(center))
    return c


def vm_cylinder(length=1.9, opacity=0.22):
    cyl = Cylinder(radius=R_VM * U, height=2 * length * U, direction=NHAT, show_ends=False, resolution=(4, 40),
                   fill_color=C_VM, fill_opacity=opacity, stroke_width=0.6, stroke_color=C_VM,
                   checkerboard_colors=False)
    return cyl


def pi_basis():
    ea = dev([1, 0, 0]); ea /= np.linalg.norm(ea)
    eb = np.cross(NHAT, ea)
    return ea, eb


def circle3d(radius, center=(0, 0, 0), color=C_VM, width=5):
    ea, eb = pi_basis()
    c = np.asarray(center, dtype=float)
    return ParametricFunction(lambda t: W(c + radius * (np.cos(t) * ea + np.sin(t) * eb)), t_range=[0, TAU],
                              color=color, stroke_width=width)


def tresca_vertices():
    vs = [dev(s * np.eye(3)[i]) for i in range(3) for s in (1, -1)]
    ea, eb = pi_basis()
    vs.sort(key=lambda v: np.arctan2(v @ eb, v @ ea))
    return vs


def tresca_prism(length=1.9, opacity=0.18):
    vs = tresca_vertices()
    faces = VGroup()
    for k in range(6):
        a, b = vs[k], vs[(k + 1) % 6]
        pts = [W(a - length * NHAT * np.sqrt(3) / np.sqrt(3) * 1.0 * 1 + 0) for _ in range(1)]
        p = [W(a - length * NHAT), W(b - length * NHAT), W(b + length * NHAT), W(a + length * NHAT)]
        faces.add(Polygon(*p, fill_color=C_TRESCA, fill_opacity=opacity, stroke_color=C_TRESCA, stroke_width=1.5))
    return faces


class S05_YieldSurface(N3DScene):
    def construct(self):
        self.set_camera_orientation(phi=PHI0, theta=TH0, zoom=0.86)
        card = VGroup(T("05", size=34, color=C_YIELD, weight=BOLD), T("The von Mises yield surface", size=50,
                                                                       weight=SEMIBOLD)).arrange(DOWN, buff=0.3)
        self.add_fixed_in_frame_mobjects(card); self.remove(card)
        self.play(FadeIn(card), run_time=0.8); self.wait(0.8); self.play(FadeOut(card), run_time=0.6)
        ax, labs = make_axes()
        hyd = Line(W(-1.7 * NHAT * np.sqrt(3)), W(1.7 * NHAT * np.sqrt(3)), color=C_HYD, stroke_width=4)
        hyd_lab = MathTex(r"\sigma_1=\sigma_2=\sigma_3", color=C_HYD, font_size=34).move_to(W(1.95 * np.ones(3)))
        disk = plane_disk(1.25, C_HYD, 0.10)
        pi_lab = MathTex(r"\pi\text{-plane}", color=C_HYD, font_size=34).move_to(W(dev([0, 0, 1]) * 1.55))
        # ---------------------------------------------------------------- y1 principal stress space
        with self.say("y1") as d:
            self.play(Create(ax), run_time=1.6)
            for l_ in labs:
                self.add_fixed_orientation_mobjects(l_)
            self.play(FadeIn(labs), run_time=0.6)
            self.begin_ambient_camera_rotation(rate=0.022)
            pts = VGroup(*[Dot3D(W(p_), radius=0.05, color=INK) for p_ in
                           ([0.6, 0.2, -0.3], [-0.4, 0.5, 0.1], [0.2, -0.6, 0.4], [0.8, 0.7, 0.1])])
            self.play(FadeIn(pts, lag_ratio=0.2), run_time=1.0)
            self.until("y1", "The line where")
            self.play(Create(hyd), run_time=1.2)
            self.add_fixed_orientation_mobjects(hyd_lab)
            self.play(FadeIn(hyd_lab), run_time=0.5)
            self.until("y1", "Perpendicular")
            self.play(FadeIn(disk), run_time=1.2)
            self.add_fixed_orientation_mobjects(pi_lab)
            self.play(FadeIn(pi_lab), FadeOut(pts), run_time=0.6)
        # ---------------------------------------------------------------- y3 decomposition of a point
        P = np.array([240.0, 80.0, -40.0]) / 355.0
        Pm = P.mean() * np.ones(3)
        with self.say("y3") as d:
            dotP = Dot3D(W(P), radius=0.07, color=C_VM)
            vP = Line(W([0, 0, 0]), W(P), color=INK, stroke_width=3)
            self.play(FadeIn(dotP), Create(vP), run_time=1.0)
            lP = MathTex(r"(\sigma_1,\sigma_2,\sigma_3)", font_size=30).move_to(W(P) + OUT * 0.55)
            self.add_fixed_orientation_mobjects(lP)
            self.play(FadeIn(lP), run_time=0.4)
            self.until("y3", "set by the mean")
            vh = Line(W([0, 0, 0]), W(Pm), color=C_HYD, stroke_width=7)
            self.play(Create(vh), run_time=1.0)
            self.until("y3", "the deviator itself")
            vd = Line(W(Pm), W(P), color=C_DEV, stroke_width=7)
            self.play(Create(vd), run_time=1.0)
            rho = MathTex(r"\rho=|\mathbf{s}|=\sqrt{2J_2}", color=C_DEV, font_size=34)
            rho.move_to(W((Pm + P) / 2) + OUT * -0.75)
            self.add_fixed_orientation_mobjects(rho)
            self.play(FadeIn(rho), FadeOut(lP), run_time=0.6)
        # ---------------------------------------------------------------- y4 the cylinder
        with self.say("y4") as d:
            cyl = vm_cylinder()
            loc = circle3d(R_VM)
            self.play(Create(loc), run_time=1.4)
            rr = MathTex(r"R=\sqrt{\tfrac23}\,\sigma_Y", color=C_VM, font_size=36)
            rr.move_to(W(dev([0, 0, 1]) / np.linalg.norm(dev([0, 0, 1])) * R_VM * 1.3) + OUT * 0.25)
            self.wait(0.5)
            self.until("y4", "everywhere along")
            self.play(FadeIn(cyl), run_time=2.0)
            eqc = MathTex(r"\sigma_{vm}=\sigma_Y\ \Longleftrightarrow\ |\mathbf{s}|=\sqrt{\tfrac23}\,\sigma_Y",
                          font_size=38, color=INK).to_corner(UL).shift(DOWN * 0.2)
            self.add_fixed_in_frame_mobjects(eqc); self.remove(eqc)
            self.play(Write(eqc), run_time=1.2)
        # ---------------------------------------------------------------- y5 why circular: look down the axis
        with self.say("y5") as d:
            self.stop_ambient_camera_rotation()
            self.play(FadeOut(pi_lab), FadeOut(hyd_lab), run_time=0.4)
            self.move_camera(phi=PHI_AX, theta=TH_AX, run_time=2.2)
            ea, eb = pi_basis()
            sd = dev(P) / np.linalg.norm(dev(P))
            ang = np.arctan2(sd @ eb, sd @ ea)
            arc = ParametricFunction(lambda t: W(0.42 * (np.cos(t) * ea + np.sin(t) * eb)), t_range=[0, ang],
                                     color=C_YIELD, stroke_width=4)
            proj = Line(W([0, 0, 0]), W(ea * 1.2), color=C_X, stroke_width=2.5)
            th_l = MathTex(r"\theta_{L}", color=C_YIELD, font_size=34).move_to(W(0.62 * (np.cos(ang / 2) * ea +
                                                                                         np.sin(ang / 2) * eb)))
            self.add_fixed_orientation_mobjects(th_l)
            self.play(Create(proj), Create(arc), FadeIn(th_l), run_time=1.0)
            note = VGroup(T("Lode angle θ_L ↔ third invariant J₃", size=24, color=C_YIELD),
                          T("von Mises depends on J₂ only → circle", size=24, color=INK)).arrange(DOWN, aligned_edge=LEFT)
            note.to_corner(DR).shift(UP * 0.3)
            self.add_fixed_in_frame_mobjects(note); self.remove(note)
            self.play(FadeIn(note), run_time=0.7)
            self.until("y5", "Infinitely long")
            self.move_camera(phi=PHI0, theta=TH0 + 8 * DEGREES, run_time=2.2)
            note2 = T("moving along the axis = adding pure pressure", size=24, color=C_HYD).next_to(note, UP, 0.2)
            note2.align_to(note, LEFT)
            self.add_fixed_in_frame_mobjects(note2); self.remove(note2)
            self.play(FadeIn(note2), run_time=0.6)
            self.wait(self.left(0.5))
            self.play(FadeOut(VGroup(note, note2, arc, proj, th_l, rho, vh, vd, vP)), run_time=0.5)
        # ---------------------------------------------------------------- y6 plane-stress slice
        with self.say("y6") as d:
            sq = Square(side_length=3.2 * U, fill_color=INK, fill_opacity=0.06, stroke_color=DIM, stroke_width=1.2)
            self.play(FadeIn(sq), FadeOut(disk), FadeIn(hyd_lab), run_time=1.0)
            ell = ParametricFunction(lambda t: W([np.cos(t) + np.sin(t) / np.sqrt(3), np.cos(t) - np.sin(t) / np.sqrt(3), 0]),
                                     t_range=[0, TAU], color=C_YIELD, stroke_width=6)
            self.play(Create(ell), run_time=2.0)
            eqe = MathTex(r"\sigma_3=0:\quad \sigma_1^2-\sigma_1\sigma_2+\sigma_2^2=\sigma_Y^2", font_size=36,
                          color=C_YIELD).next_to(eqc, DOWN, 0.3).align_to(eqc, LEFT)
            self.add_fixed_in_frame_mobjects(eqe); self.remove(eqe)
            self.play(Write(eqe), run_time=1.2)
            marks = VGroup()
            for p_, lab, col in (([1, 0, 0], "A", C_X), ([1 / np.sqrt(3), -1 / np.sqrt(3), 0], "B", C_SHEAR),
                                 ([1, 1, 0], "C", C_Y)):
                dt = Dot3D(W(p_), radius=0.08, color=col)
                tx = MathTex(rf"\mathbf{{{lab}}}", color=col, font_size=40).move_to(W(p_) + OUT * 0.4)
                self.add_fixed_orientation_mobjects(tx)
                marks.add(dt, tx)
            self.until("y6", "with uniaxial")
            self.play(LaggedStart(*[FadeIn(m_) for m_ in marks], lag_ratio=0.25), run_time=2.0)
            leg = T("A uniaxial · B pure shear · C equal biaxial", size=24, color=DIM).to_corner(DR).shift(UP * 0.3)
            self.add_fixed_in_frame_mobjects(leg); self.remove(leg)
            self.play(FadeIn(leg), run_time=0.5)
        # ---------------------------------------------------------------- y7 proportional loading
        with self.say("y7") as d:
            self.play(FadeOut(VGroup(sq, ell, marks, leg, eqe)), run_time=0.6)
            lam = ValueTracker(0.0)
            path = always_redraw(lambda: Line(W([0, 0, 0]), W(P * max(lam.get_value(), 1e-3)), color=INK,
                                              stroke_width=4))
            dot = always_redraw(lambda: Dot3D(W(P * lam.get_value()), radius=0.08, color=C_VM))
            self.add(path, dot)
            fos = 355.0 / 243.31
            self.play(lam.animate.set_value(fos), run_time=self.till("y7", "the safety factor", minimum=2.5),
                      rate_func=linear)
            flash = Dot3D(W(P * fos), radius=0.16, color=C_YIELD)
            self.play(FadeIn(flash, scale=0.4), run_time=0.4)
            ft = MathTex(r"\lambda=\frac{\sigma_Y}{\sigma_{vm}}=\frac{355}{243.3}=1.46", font_size=38, color=C_YIELD)
            ft.to_corner(DR).shift(UP * 0.5)
            self.add_fixed_in_frame_mobjects(ft); self.remove(ft)
            self.play(Write(ft), run_time=1.0)
            self.until("y7", "A hydrostatic path")
            h = ValueTracker(0.0)
            hdot = always_redraw(lambda: Dot3D(W(NHAT * h.get_value()), radius=0.08, color=C_HYD))
            self.add(hdot)
            self.play(h.animate.set_value(3.0), run_time=self.left(0.6), rate_func=linear)
            path.clear_updaters(); dot.clear_updaters(); hdot.clear_updaters()
            self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)


class S06_Tresca(N3DScene):
    def construct(self):
        self.set_camera_orientation(phi=PHI0, theta=TH0, zoom=0.86)
        card = VGroup(T("06", size=34, color=C_YIELD, weight=BOLD), T("Von Mises versus Tresca", size=50,
                                                                       weight=SEMIBOLD)).arrange(DOWN, buff=0.3)
        self.add_fixed_in_frame_mobjects(card); self.remove(card)
        self.play(FadeIn(card), run_time=0.8); self.wait(0.8); self.play(FadeOut(card), run_time=0.6)
        # ---------------------------------------------------------------- t1 hypotheses
        with self.say("t1") as d:
            tr = MathTex(r"\text{Tresca (1864):}\quad", r"\tau_{\max}=\frac{\sigma_1-\sigma_3}{2}", r"=\frac{\sigma_Y}{2}",
                         font_size=44)
            tr[1].set_color(C_TRESCA)
            vm = MathTex(r"\text{von Mises:}\quad", r"\sqrt{3J_2}", r"=\sigma_Y", font_size=44)
            vm[1].set_color(C_VM)
            hyp1 = T("slip on the single most stressed plane", size=26, color=C_TRESCA)
            hyp2 = T("shear averaged over all planes (distortion energy)", size=26, color=C_VM)
            col = VGroup(tr, hyp1, vm, hyp2).arrange(DOWN, buff=0.35)
            hyp1.align_to(tr, LEFT).shift(RIGHT * 0.3); hyp2.align_to(vm, LEFT).shift(RIGHT * 0.3)
            col.move_to(ORIGIN)
            self.add_fixed_in_frame_mobjects(col); self.remove(col)
            self.play(Write(tr), run_time=1.8)
            self.until("t1", "Tresca pictures")
            self.play(FadeIn(hyp1), run_time=0.7)
            self.until("t1", "von Mises averages")
            self.play(Write(vm), FadeIn(hyp2), run_time=1.2)
            self.wait(self.left(0.6))
            self.play(col.animate.scale(0.6).to_corner(UL), run_time=0.6)
        # ---------------------------------------------------------------- t2 prism inscribed; look down the axis
        ax, labs = make_axes()
        cyl = vm_cylinder(opacity=0.16)
        prism = tresca_prism()
        hyd = Line(W(-1.7 * NHAT * np.sqrt(3)), W(1.7 * NHAT * np.sqrt(3)), color=C_HYD, stroke_width=3)
        with self.say("t2") as d:
            self.play(Create(ax), Create(hyd), run_time=1.0)
            for l_ in labs:
                self.add_fixed_orientation_mobjects(l_)
            self.play(FadeIn(labs), FadeIn(cyl), run_time=0.8)
            self.play(FadeIn(prism), run_time=1.2)
            self.until("t2", "In the pi plane")
            self.move_camera(phi=PHI_AX, theta=TH_AX, run_time=2.2)
            # switch to an exact 2D pi-plane drawing (same orientation as this view)
            Rs = R_VM * U * 0.86 * 1.0
            ang = {1: 210, 2: 330, 3: 90}
            circ = Circle(radius=Rs, color=C_VM, stroke_width=5)
            hexa = Polygon(*[Rs * np.array([np.cos(np.radians(a)), np.sin(np.radians(a)), 0])
                             for a in (90, 150, 210, 270, 330, 30)], color=C_TRESCA, stroke_width=5)
            axes2 = VGroup()
            for i, a in ang.items():
                v = np.array([np.cos(np.radians(a)), np.sin(np.radians(a)), 0])
                axes2.add(DashedLine(ORIGIN, v * Rs * 1.45, color=COMP[i - 1], stroke_width=2))
                axes2.add(MathTex(rf"\sigma_{i}'", color=COMP[i - 1], font_size=30).move_to(v * Rs * 1.78))
            diag = VGroup(axes2, circ, hexa)
            self.add_fixed_in_frame_mobjects(diag); self.remove(diag)
            self.play(FadeIn(diag), FadeOut(VGroup(ax, labs, cyl, prism, hyd)), FadeOut(col), run_time=1.0)
            self.play(diag.animate.scale(1.55, about_point=ORIGIN), run_time=0.8)
            Rs = Rs * 1.55
            vlabs = VGroup()
            for a, txt, col in ((90, "uniaxial", C_Z), (210, "uniaxial", C_X), (330, "uniaxial", C_Y),
                                (270, "equal biaxial", INK), (30, "equal biaxial", INK), (150, "equal biaxial", INK)):
                v = np.array([np.cos(np.radians(a)), np.sin(np.radians(a)), 0])
                vlabs.add(Dot(v * Rs, radius=0.07, color=C_TRESCA))
                vlabs.add(T(txt, size=19, color=col).move_to(v * (Rs + 0.5) + (RIGHT * 0.75 if a == 90 else ORIGIN)))
            self.add_fixed_in_frame_mobjects(vlabs); self.remove(vlabs)
            self.until("t2", "they agree")
            self.play(FadeIn(vlabs, lag_ratio=0.1), run_time=1.2)
            self.until("t2", "and differ most")
            shear_pts = VGroup()
            for a in (0, 60, 120, 180, 240, 300):
                v = np.array([np.cos(np.radians(a)), np.sin(np.radians(a)), 0])
                shear_pts.add(Line(v * Rs * np.cos(np.radians(30)), v * Rs, color=C_SHEAR, stroke_width=6))
            sl = T("pure shear", size=22, color=C_SHEAR).move_to(np.array([np.cos(0), np.sin(0), 0]) * (Rs + 0.75))
            self.add_fixed_in_frame_mobjects(shear_pts, sl); self.remove(shear_pts, sl)
            self.play(Create(shear_pts), FadeIn(sl), run_time=1.0)
        # ---------------------------------------------------------------- t3 quantify
        with self.say("t3") as d:
            g = VGroup(diag, vlabs, shear_pts, sl)
            self.play(g.animate.scale(0.8).move_to([-3.5, -0.1, 0]), run_time=0.8)
            q = VGroup(VGroup(T("hexagon inside circle", size=26, color=INK),
                              T("⇒ Tresca never less conservative", size=26, color=INK)).arrange(DOWN, aligned_edge=LEFT,
                                                                                            buff=0.1),
                       M(r"\tau_Y^{\text{Tresca}}=0.500\,\sigma_Y", size=40, color=C_TRESCA),
                       M(r"\tau_Y^{\text{von Mises}}=0.577\,\sigma_Y", size=40, color=C_VM),
                       M(r"\frac{0.577}{0.500}=\frac{2}{\sqrt3}=1.155", size=40, color=C_SHEAR)).arrange(DOWN, buff=0.4,
                                                                                               aligned_edge=LEFT)
            q.move_to([3.55, 0.3, 0])
            self.add_fixed_in_frame_mobjects(q); self.remove(q)
            self.play(FadeIn(q[0]), run_time=0.7)
            self.until("t3", "In pure shear")
            self.play(Write(q[1]), run_time=1.0)
            self.play(Write(q[2]), run_time=1.0)
            self.play(Write(q[3]), run_time=1.0)
            self.until("t3", "Most ductile")
            ex = T("experiments on most ductile metals: closer to von Mises", size=22, color=DIM).next_to(q, DOWN, 0.4)
            ex.align_to(q, LEFT)
            self.add_fixed_in_frame_mobjects(ex); self.remove(ex)
            self.play(FadeIn(ex), run_time=0.6)
            self.wait(self.left(0.6))
            self.play(FadeOut(VGroup(q, ex)), run_time=0.5)
        # ---------------------------------------------------------------- t4 smoothness & radial return
        with self.say("t4") as d:
            txts = [m_ for m_ in vlabs if isinstance(m_, Text)] + [sl]
            self.play(g.animate.scale(1.25).move_to(ORIGIN), *[FadeOut(m_) for m_ in txts], run_time=0.7)
            Rs = R_VM * U * 0.86 * 1.55
            # unique normal on the circle vs normal cone at a hexagon corner
            a0 = np.radians(90)
            pc = Rs * np.array([np.cos(a0), np.sin(a0), 0])
            ncone = VGroup(*[Arrow(pc, pc + 0.9 * np.array([np.cos(a0 + t), np.sin(a0 + t), 0]), buff=0, color=C_TRESCA,
                                   stroke_width=3, max_tip_length_to_length_ratio=0.2)
                             for t in np.radians(np.linspace(-30, 30, 5))])
            a1 = np.radians(30)
            pv_ = Rs * np.array([np.cos(a1), np.sin(a1), 0])
            nvm = Arrow(pv_, pv_ + 1.0 * np.array([np.cos(a1), np.sin(a1), 0]), buff=0, color=C_VM, stroke_width=5,
                        max_tip_length_to_length_ratio=0.2)
            self.add_fixed_in_frame_mobjects(ncone, nvm); self.remove(ncone, nvm)
            self.play(GrowArrow(nvm), run_time=0.8)
            ln = M(r"\dot{\boldsymbol\varepsilon}^p\propto\frac{\partial f}{\partial\boldsymbol\sigma}\propto\mathbf{s}",
                   size=38, color=C_VM).to_corner(UR).shift(DOWN * 0.6)
            self.add_fixed_in_frame_mobjects(ln); self.remove(ln)
            self.play(Write(ln), run_time=1.0)
            self.until("t4", "That enables")
            a2 = np.radians(-20)
            trial = (Rs + 1.05) * np.array([np.cos(a2), np.sin(a2), 0])
            onc = Rs * np.array([np.cos(a2), np.sin(a2), 0])
            td = Dot(trial, color=INK, radius=0.08)
            tl = T("trial stress", size=22, color=INK).next_to(td, RIGHT, 0.12)
            rr = Arrow(trial, onc, buff=0.05, color=C_YIELD, stroke_width=5, max_tip_length_to_length_ratio=0.25)
            rl = T("radial return", size=22, color=C_YIELD).next_to(rr, DOWN, 0.1)
            self.add_fixed_in_frame_mobjects(td, tl, rr, rl); self.remove(td, tl, rr, rl)
            self.play(FadeIn(td), FadeIn(tl), run_time=0.5)
            self.play(GrowArrow(rr), FadeIn(rl), run_time=1.0)
            self.until("t4", "At Tresca")
            self.play(LaggedStart(*[GrowArrow(a) for a in ncone], lag_ratio=0.1), run_time=1.0)
            amb = T("corner: normal not unique", size=22, color=C_TRESCA).next_to(ncone, UP, 0.1)
            self.add_fixed_in_frame_mobjects(amb); self.remove(amb)
            self.play(FadeIn(amb), run_time=0.5)
            self.wait(self.left(0.6))
            self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)
