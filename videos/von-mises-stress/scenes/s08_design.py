"""Section 8 - from stress to safety factor; Section 9 - conclusion."""
from common import *  # noqa: F401,F403

S = (240.0, 80.0, -40.0)
SY = 355.0


class S08_Design(NScene):
    def construct(self):
        section_card(self, 8, "From stress to safety factor")
        # ---------------------------------------------------------------- g1 given
        given = VGroup(T("given", size=22, color=DIM),
                       M(r"\sigma_Y=355\ \text{MPa}\ \ (\text{S355})", size=38, color=C_YIELD),
                       M(r"\sigma_1=240", r",\ \ ", r"\sigma_2=80", r",\ \ ", r"\sigma_3=-40", r"\ \ \text{MPa}",
                         size=36)).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        for k_, c_ in ((0, C_X), (2, C_Y), (4, C_Z)):
            given[2][k_].set_color(c_)
        gbox = SurroundingRectangle(given, color=FAINT, buff=0.25, corner_radius=0.12)
        gg = VGroup(given, gbox).to_corner(UL).shift(DOWN * 0.1)
        nl = NumberLine(x_range=[-80, 280, 40], length=6.2, color=DIM, include_numbers=True, font_size=22,
                        stroke_width=2, numbers_to_exclude=[]).move_to([-3.6, -1.9, 0])
        unit = T("MPa", size=20, color=DIM).next_to(nl, RIGHT, 0.15)
        dots = VGroup()
        for k, (v, c) in enumerate(zip(S, COMP)):
            p = nl.n2p(v)
            dots.add(Dot(p, radius=0.09, color=c), MathTex(rf"\sigma_{k + 1}", color=c, font_size=34).next_to(p, UP, 0.2))
        with self.say("g1") as d:
            self.play(FadeIn(gg), run_time=1.0)
            self.until("g1", "At the critical")
            self.play(Create(nl), FadeIn(unit), run_time=0.8)
            self.play(LaggedStart(*[FadeIn(x) for x in dots], lag_ratio=0.15), run_time=1.0)
        X0 = 3.25
        # ---------------------------------------------------------------- g2 mean stress & deviators
        with self.say("g2") as d:
            st1 = M(r"\sigma_m=\frac{240+80-40}{3}=", r"93.3\ \text{MPa}", size=38).move_to([X0, 2.9, 0])
            st1[1].set_color(C_HYD)
            self.play(Write(st1), run_time=1.6)
            pm = nl.n2p(280 / 3)
            mline = DashedLine(pm + DOWN * 0.3, pm + UP * 1.6, color=C_HYD, stroke_width=2.5)
            mlab = MathTex(r"\sigma_m", color=C_HYD, font_size=32).next_to(mline, UP, 0.05)
            self.play(Create(mline), FadeIn(mlab), run_time=0.7)
            self.until("g2", "Subtracting")
            st2 = M(r"s_i=\sigma_i-\sigma_m:\quad", r"146.7,\ \ -13.3,\ \ -133.3", size=36).next_to(st1, DOWN, 0.35)
            st2[1].set_color(C_DEV)
            arrs = VGroup()
            for k, v in enumerate(S):
                y = 0.55 + 0.32 * k
                arrs.add(Arrow(pm + UP * y, nl.n2p(v) + UP * y, buff=0, color=C_DEV, stroke_width=4,
                               max_tip_length_to_length_ratio=0.15))
            self.play(Write(st2), LaggedStart(*[GrowArrow(a) for a in arrs], lag_ratio=0.2), run_time=1.8)
            ok = M(r"\textstyle\sum s_i=0\ \checkmark", size=34, color=C_GOOD).next_to(st2, DOWN, 0.25)
            self.play(FadeIn(ok), run_time=0.5)
        # ---------------------------------------------------------------- g3 differences, squares
        with self.say("g3") as d:
            rows = VGroup(
                M(r"\sigma_1-\sigma_2=160", r"\quad\rightarrow\quad", r"25\,600", size=34),
                M(r"\sigma_2-\sigma_3=120", r"\quad\rightarrow\quad", r"14\,400", size=34),
                M(r"\sigma_3-\sigma_1=-280", r"\quad\rightarrow\quad", r"78\,400", size=34)).arrange(DOWN, buff=0.22,
                                                                                               aligned_edge=RIGHT)
            rows.next_to(ok, DOWN, 0.45).set_x(X0)
            for r_ in rows:
                r_[2].set_color(C_SHEAR)
            self.play(LaggedStart(*[FadeIn(r_[0]) for r_ in rows], lag_ratio=0.3), run_time=1.6)
            self.until("g3", "Their squares")
            self.play(LaggedStart(*[FadeIn(VGroup(r_[1], r_[2])) for r_ in rows], lag_ratio=0.3), run_time=1.6)
            line = Line(LEFT, RIGHT, color=DIM).set_width(2.2).next_to(rows, DOWN, 0.15).align_to(rows, RIGHT)
            sm = M(r"\Sigma=118\,400", r"\qquad\tfrac12\Sigma=", r"59\,200", size=36).next_to(line, DOWN, 0.2)
            sm.align_to(rows, RIGHT)
            sm[2].set_color(C_VM)
            self.until("g3", "sum to")
            self.play(Create(line), Write(sm[0]), run_time=1.0)
            self.until("g3", "Half of that")
            self.play(Write(sm[1:]), run_time=1.0)
        # ---------------------------------------------------------------- g4 result
        with self.say("g4") as d:
            res = M(r"\sigma_{vm}=\sqrt{59\,200}=", r"243.3\ \text{MPa}", size=46).move_to([X0, -2.35, 0])
            res[1].set_color(C_VM)
            box = caption_box(res, color=C_VM)
            self.play(Write(res), run_time=1.4)
            self.play(Create(box), run_time=0.5)
            self.until("g4", "confirmed")
            chk = M(r"3J_2=\tfrac32\left(146.7^2+13.3^2+133.3^2\right)=59\,200\ \checkmark", size=30, color=C_GOOD)
            chk.next_to(box, DOWN, 0.25)
            self.play(FadeIn(chk), run_time=0.8)
        # ---------------------------------------------------------------- g5 safety factor
        with self.say("g5") as d:
            calc = VGroup(st1, st2, ok, rows, line, sm)
            self.play(FadeOut(calc), FadeOut(chk), VGroup(res, box).animate.move_to([X0, 2.75, 0]).scale(0.85),
                      FadeOut(VGroup(nl, unit, dots, mline, mlab, arrs)), run_time=0.8)
            fos = M(r"\text{FoS}=\frac{\sigma_Y}{\sigma_{vm}}=\frac{355}{243.3}=", r"1.46", size=44).move_to([X0, 1.35, 0])
            fos[1].set_color(C_YIELD)
            ut = M(r"\text{utilization}=68.5\%,\quad\text{margin}\approx112\ \text{MPa}", size=32, color=DIM)
            ut.next_to(fos, DOWN, 0.3)
            self.play(Write(fos), run_time=1.6)
            self.play(FadeIn(ut), run_time=0.6)
            # bar comparison of the three criteria
            ax0 = np.array([-6.4, -2.9, 0])
            items = [("von Mises", 1.459, C_VM, ""), ("Tresca", 355 / 280, C_TRESCA, "more conservative"),
                     ("max. principal stress", 355 / 240, C_STEEL, "unconservative")]
            bars = VGroup()
            for k, (name, f, col, note) in enumerate(items):
                y = -0.75 - 0.85 * k
                bar = Rectangle(width=f * 2.6, height=0.42, fill_color=col, fill_opacity=0.85, stroke_width=0)
                bar.move_to([ax0[0] + 2.6 + f * 1.3, y, 0])
                lab = T(name, size=22, color=INK).next_to(bar, LEFT, 0.2)
                val = T(f"{f:.2f}", size=26, color=col, weight=BOLD).next_to(bar, RIGHT, 0.15)
                nt = T(note, size=20, color=DIM).next_to(val, RIGHT, 0.25)
                bars.add(VGroup(bar, lab, val, nt))
            one = DashedLine([ax0[0] + 5.2, -0.35, 0], [ax0[0] + 5.2, -2.75, 0], color=DIM, stroke_width=2)
            onel = M(r"\text{FoS}=1", size=24, color=DIM).next_to(one, UP, 0.05)
            hdr = T("safety factor against first yield", size=24, color=DIM).move_to([ax0[0] + 4.6, 0.1, 0])
            self.play(FadeIn(hdr), Create(one), FadeIn(onel), FadeIn(bars[0]), run_time=1.0)
            self.until("g5", "Tresca gives")
            self.play(FadeIn(bars[1]), run_time=0.8)
            self.until("g5", "The largest principal")
            self.play(FadeIn(bars[2]), run_time=0.8)
            self.wait(self.left(0.6))
            self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)
        # ---------------------------------------------------------------- g6 vocabulary
        with self.say("g6") as d:
            defs = [("yield strength  σ_Y", "material property — tension test", C_YIELD),
                    ("equivalent stress  σ_vm", "describes the stress state at a point", C_VM),
                    ("safety factor", "σ_Y / σ_vm", C_SHEAR),
                    ("design allowable", "σ_Y reduced by code partial / usage factors", C_TRESCA)]
            cards = VGroup()
            for title, body, col in defs:
                t_ = T(title, size=30, color=col, weight=SEMIBOLD)
                b_ = T(body, size=22, color=INK)
                g = VGroup(t_, b_).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
                fr = RoundedRectangle(width=6.2, height=1.55, corner_radius=0.15, stroke_color=col, stroke_width=2,
                                      fill_color=PANEL, fill_opacity=0.9)
                g.move_to(fr).align_to(fr, LEFT).shift(RIGHT * 0.35)
                cards.add(VGroup(fr, g))
            cards.arrange_in_grid(2, 2, buff=(0.4, 0.45))
            foot = T("S355: specified minimum yield strength falls with plate thickness (EN 10025)", size=20, color=DIM)
            foot.to_edge(DOWN, 0.4)
            head = T("keep the terms distinct", size=34, weight=SEMIBOLD).to_edge(UP, 0.6)
            self.play(FadeIn(head), run_time=0.5)
            cues = ["Yield strength", "Equivalent stress", "The safety factor", "And the design"]
            for c_, q in zip(cards, cues):
                self.until("g6", q)
                self.play(FadeIn(c_, shift=UP * 0.15), run_time=0.7)
            self.play(FadeIn(foot), run_time=0.5)
            self.wait(self.left(0.6))
            self.play(FadeOut(VGroup(cards, foot, head)), run_time=0.6)
        # ---------------------------------------------------------------- g7 below yield is not enough
        with self.say("g7") as d:
            ttl = T("σ_vm < σ_Y is necessary, not sufficient", size=36, weight=SEMIBOLD).to_edge(UP, 0.5)
            self.play(FadeIn(ttl), run_time=0.7)
            # fatigue: S-N curve
            ax = Axes(x_range=[0, 1, 1], y_range=[0, 1, 1], x_length=2.6, y_length=1.7, tips=False,
                      axis_config=dict(color=DIM, stroke_width=1.5, include_ticks=False))
            sn = ax.plot(lambda x: 0.85 * (1 - x) ** 2 + 0.12, x_range=[0, 1], color=C_SHEAR, stroke_width=4)
            fat = VGroup(ax, sn)
            # buckling: bowed column
            col = VGroup(Line(DOWN * 0.9, UP * 0.9, color=DIM, stroke_width=3).set_opacity(0.5),
                         ArcBetweenPoints(DOWN * 0.9, UP * 0.9, angle=-0.9, color=C_TRESCA, stroke_width=6),
                         Arrow(UP * 1.6, UP * 0.95, buff=0, color=C_X, stroke_width=5),
                         Arrow(DOWN * 1.6, DOWN * 0.95, buff=0, color=C_X, stroke_width=5))
            # fracture: plate with a crack
            plate = Rectangle(width=2.4, height=1.6, fill_color=C_STEEL, fill_opacity=0.3, stroke_color=INK,
                              stroke_width=2)
            crack = VMobject(color=C_BAD, stroke_width=4).set_points_as_corners(
                [plate.get_left() + RIGHT * 0.0, plate.get_left() + RIGHT * 0.5 + UP * 0.05,
                 plate.get_left() + RIGHT * 0.8 - UP * 0.04, plate.get_left() + RIGHT * 1.1])
            frac = VGroup(plate, crack)
            # deformation: connector gap / leak
            f1 = Rectangle(width=0.5, height=1.8, fill_color=C_STEEL, fill_opacity=0.6, stroke_color=INK).shift(LEFT * 0.4)
            f2 = Rectangle(width=0.5, height=1.8, fill_color=C_STEEL, fill_opacity=0.6, stroke_color=INK).shift(RIGHT * 0.4)
            f2.rotate(-0.12, about_point=f2.get_bottom())
            drops = VGroup(*[Dot(radius=0.05, color=C_Z).move_to([0.05 + 0.12 * k, 0.75 - 0.25 * k, 0]) for k in range(3)])
            defo = VGroup(f1, f2, drops)
            icons = [(fat, "fatigue", "stress ranges, millions of cycles"),
                     (col, "buckling", "slender members, shells"),
                     (frac, "fracture", "cracks — toughness governs"),
                     (defo, "deformation", "leaks, misalignment")]
            panel = VGroup()
            for ic, name, sub in icons:
                ic.scale_to_fit_height(1.55)
                n_ = T(name, size=28, weight=SEMIBOLD)
                s_ = T(sub, size=20, color=DIM)
                panel.add(VGroup(ic, n_, s_).arrange(DOWN, buff=0.25))
            panel.arrange(RIGHT, buff=0.6).move_to(DOWN * 0.3)
            if panel.width > 12.8:
                panel.scale_to_fit_width(12.8)
            for p_, q in zip(panel, ["Welded joints", "Slender members", "Cracks cause", "And excessive"]):
                self.until("g7", q)
                self.play(FadeIn(p_, shift=UP * 0.15), run_time=0.7)
            self.wait(self.left(0.6))
            self.play(FadeOut(VGroup(ttl, panel)), run_time=0.6)


class S09_Conclusion(N3DScene):
    def construct(self):
        self.set_camera_orientation(phi=66 * DEGREES, theta=-50 * DEGREES, zoom=0.9)
        sig = np.array([[1.0, 0.45, 0.2], [0.45, 0.25, -0.3], [0.2, -0.3, -0.45]])
        sm = np.trace(sig) / 3
        th, ph = -50 * DEGREES, 66 * DEGREES
        right = np.array([-np.sin(th), np.cos(th), 0])
        upv = np.array([-np.cos(ph) * np.cos(th), -np.cos(ph) * np.sin(th), np.sin(ph)])
        full = stress_cube(sig, size=1.7, scale=0.95)
        hydc = stress_cube(sm * np.eye(3), size=1.4, scale=1.4, shear=False)
        for a in hydc.normals:
            a.set_color(C_HYD)
        devc = stress_cube(sig - sm * np.eye(3), size=1.4, scale=0.95)
        for a in devc.normals:
            a.set_color(C_DEV)
        hydc.move_to(right * -3.6 + upv * -0.6)
        devc.move_to(right * 3.6 + upv * -0.6)
        lh = VGroup(T("hydrostatic", size=30, color=C_HYD, weight=SEMIBOLD), T("changes volume", size=24, color=DIM))
        ld = VGroup(T("deviatoric", size=30, color=C_DEV, weight=SEMIBOLD), T("changes shape → slip → yield", size=24,
                                                                              color=DIM))
        for g, x in ((lh, -3.6), (ld, 3.6)):
            g.arrange(DOWN, buff=0.12).move_to([x, -2.6, 0])
            self.add_fixed_in_frame_mobjects(g); self.remove(g)
        with self.say("z1") as d:
            self.play(FadeIn(full), run_time=1.0)
            self.begin_ambient_camera_rotation(rate=0.08)
            self.until("z1", "Every stress state")
            self.play(TransformFromCopy(full, hydc), TransformFromCopy(full, devc), FadeOut(full), run_time=1.8)
            self.play(FadeIn(lh), FadeIn(ld), run_time=0.8)
            self.until("z1", "In ductile metals")
            self.play(hydc.animate.set_opacity(0.25), FadeOut(lh), devc.animate.scale(1.15), run_time=1.2)
        with self.say("z2") as d:
            self.stop_ambient_camera_rotation()
            self.play(FadeOut(VGroup(hydc, devc, ld)), run_time=0.6)
            eq = M(r"\sigma_{vm}=\sqrt{\tfrac12\left[(\sigma_1-\sigma_2)^2+(\sigma_2-\sigma_3)^2+(\sigma_3-\sigma_1)^2\right]}",
                   size=50)
            eq[0][0:3].set_color(C_VM)
            box = caption_box(eq, color=C_VM, buff=0.3)
            grp = VGroup(eq, box).move_to(UP * 0.6)
            self.add_fixed_in_frame_mobjects(grp); self.remove(grp)
            self.play(Write(eq), run_time=2.4)
            self.play(Create(box), run_time=0.6)
        with self.say("z3") as d:
            lines = ["Von Mises stress transforms a complex three-dimensional stress state",
                     "into one physically meaningful quantity that can be compared",
                     "against the material's uniaxial yield strength."]
            stmt = VGroup(*[T(s, size=30, color=INK) for s in lines]).arrange(DOWN, buff=0.18).move_to(DOWN * 1.7)
            self.add_fixed_in_frame_mobjects(stmt); self.remove(stmt)
            for s_ in stmt:
                self.play(FadeIn(s_, shift=UP * 0.08), run_time=self.left() / 4)
            self.wait(self.left(0.2))
        self.wait(1.2)
        self.play(FadeOut(VGroup(grp, stmt)), run_time=1.0)
        end = VGroup(T("THE PHYSICS OF FAILURE", size=46, weight=BOLD),
                     T("Understanding von Mises Stress", size=30, color=DIM)).arrange(DOWN, buff=0.25)
        cred = T("Narration: synthetic voice (Kokoro TTS) · Animation: Manim · FE analysis: gmsh + scikit-fem",
                 size=18, color=DIM).to_edge(DOWN, 0.5)
        self.add_fixed_in_frame_mobjects(end, cred); self.remove(end, cred)
        self.play(FadeIn(end), FadeIn(cred), run_time=1.2)
        self.wait(3.0)
        self.play(FadeOut(VGroup(end, cred)), run_time=1.5)
        self.wait(0.5)
