"""Section 2 - the physical origin of yielding."""
from common import *  # noqa: F401,F403


def edge_disp(x, y, b, nu=0.3):
    """Volterra displacement field of an edge dislocation (Burgers vector b along +x, slip plane y = 0)."""
    r2 = np.maximum(x * x + y * y, (0.45 * b) ** 2)
    th = np.arctan2(y, x)
    ux = b / (2 * np.pi) * (th + x * y / (2 * (1 - nu) * r2))
    uy = -b / (2 * np.pi) * ((1 - 2 * nu) / (4 * (1 - nu)) * np.log(r2 / b ** 2) + (x * x - y * y) / (4 * (1 - nu) * r2))
    return ux, uy


class Lattice(VGroup):
    """2D lattice block whose atoms follow an edge dislocation at x = xd (tracker) and a rigid slip s."""

    def __init__(self, nx=21, ny=5, a=0.4, center=ORIGIN, atom_r=0.07):
        super().__init__()
        self.a, self.nx, self.ny = a, nx, ny
        xs = (np.arange(nx) - (nx - 1) / 2) * a
        ys = (np.arange(-ny, ny) + 0.5) * a
        X, Y = np.meshgrid(xs, ys, indexing="ij")
        self.X0, self.Y0 = X, Y
        self.c = np.array(center, dtype=float)
        self.xd = ValueTracker(-20.0)        # dislocation core position (far left = perfect crystal)
        self.slip = ValueTracker(0.0)         # rigid slip of the upper half (in units of a)
        self.atoms = VGroup(*[Dot(radius=atom_r, color="#C9D3E3") for _ in range(X.size)])
        self.bonds_h, self.bonds_v, self.bonds_x = VGroup(), VGroup(), VGroup()
        bs = dict(stroke_width=2.2, color="#4A5A78")
        for j in range(2 * ny):
            for i in range(nx - 1):
                self.bonds_h.add(Line(LEFT, RIGHT, **bs))
        for i in range(nx):
            for j in range(2 * ny - 1):
                if j == ny - 1:
                    continue
                self.bonds_v.add(Line(DOWN, UP, **bs))
        for i in range(nx):
            self.bonds_x.add(Line(DOWN, UP, **bs))
        self.add(self.bonds_h, self.bonds_v, self.bonds_x, self.atoms)
        self.highlight = False
        self.add_updater(lambda m: m.refresh())
        self.refresh()

    def positions(self):
        a = self.a
        xd = self.xd.get_value()
        ux, uy = edge_disp(self.X0 - xd, self.Y0, a)
        lower = self.Y0 < 0
        ux = ux - ux[lower].mean() if xd < 10 else ux - ux[lower].mean()
        uy = uy - uy[lower].mean()
        ux = ux + np.where(self.Y0 > 0, self.slip.get_value() * a, 0.0)
        return self.X0 + ux + self.c[0], self.Y0 + uy + self.c[1]

    def refresh(self):
        X, Y = self.positions()
        nx, ny = self.nx, self.ny
        P = lambda i, j: np.array([X[i, j], Y[i, j], 0.0])
        k = 0
        for i in range(nx):
            for j in range(2 * ny):
                self.atoms[k].move_to(P(i, j)); k += 1
        k = 0
        for j in range(2 * ny):
            for i in range(nx - 1):
                self.bonds_h[k].put_start_and_end_on(P(i, j), P(i + 1, j)); k += 1
        k = 0
        for i in range(nx):
            for j in range(2 * ny - 1):
                if j == ny - 1:
                    continue
                self.bonds_v[k].put_start_and_end_on(P(i, j), P(i, j + 1)); k += 1
        # bonds across the slip plane re-form to the nearest atom above
        up = X[:, ny]; xd = self.xd.get_value() + self.c[0]
        for i in range(nx):
            jj = int(np.argmin(np.abs(up - X[i, ny - 1])))
            ln = self.bonds_x[i]
            if abs(up[jj] - X[i, ny - 1]) < 0.8 * self.a:
                ln.put_start_and_end_on(P(i, ny - 1), P(jj, ny)); ln.set_opacity(1)
            else:
                ln.set_opacity(0)
        if self.highlight:
            col = int(np.argmin(np.abs(up - xd)))
            on = -20 < self.xd.get_value() < (nx / 2 + 0.2) * self.a
            for i in range(nx):
                for j in range(ny, 2 * ny):
                    self.atoms[i * 2 * ny + j].set_color(C_SHEAR if (on and i == col) else "#C9D3E3")
        return self


class S02a_Micro(NScene):
    def construct(self):
        section_card(self, 2, "The physical origin of yielding")
        # ---------------------------------------------------------------- m1 polycrystal
        cen = np.load(os.path.join(BUILD, "assets", "polycrystal_centers.npy"))
        k = int(np.argmin(np.sum((cen - [0.5, 0.52]) ** 2, axis=1)))
        img = ZoomImage(os.path.join(BUILD, "assets", "polycrystal.png"), focus=(cen[k, 0], 1 - cen[k, 1]))
        with self.say("m1") as d:
            self.play(FadeIn(img), run_time=1.2)
            lab1 = T("grains", size=30, color=INK).to_corner(UL).shift(DOWN * 0.2)
            lab2 = T("grain boundaries", size=30, color=INK).next_to(lab1, DOWN, aligned_edge=LEFT)
            sub = T("each grain: a lattice of iron atoms (BCC ferrite), oriented differently", size=24, color=DIM)
            sub.to_edge(DOWN, buff=0.4)
            bg = BackgroundRectangle(VGroup(lab1, lab2), fill_color=BG, fill_opacity=0.75, buff=0.2)
            bg2 = BackgroundRectangle(sub, fill_color=BG, fill_opacity=0.75, buff=0.15)
            self.play(FadeIn(bg), FadeIn(lab1), FadeIn(lab2), FadeIn(bg2), FadeIn(sub), run_time=1.0)
            self.wait(max(0.1, d - 5.2))
            self.play(FadeOut(VGroup(bg, lab1, lab2, bg2, sub)), img.zoom.animate.set_value(5.0),
                      run_time=2.6, rate_func=smooth)
        # ---------------------------------------------------------------- m2 slip
        lat = Lattice(center=DOWN * 0.35)
        slip_line = DashedLine(LEFT * 4.6 + DOWN * 0.35, RIGHT * 4.6 + DOWN * 0.35, color=C_SHEAR,
                               stroke_width=2.5, dash_length=0.12)
        with self.say("m2") as d:
            self.play(FadeOut(img), FadeIn(lat), run_time=1.0)
            tau_top = Arrow(LEFT * 1.5, RIGHT * 1.5, color=C_SHEAR, buff=0, stroke_width=6).next_to(lat, UP, 0.25)
            tau_bot = Arrow(RIGHT * 1.5, LEFT * 1.5, color=C_SHEAR, buff=0, stroke_width=6).next_to(lat, DOWN, 0.25)
            tt = M(r"\tau", color=C_SHEAR).next_to(tau_top, UP, 0.1)
            tb = M(r"\tau", color=C_SHEAR).next_to(tau_bot, DOWN, 0.1)
            self.play(GrowArrow(tau_top), GrowArrow(tau_bot), FadeIn(tt), FadeIn(tb), Create(slip_line),
                      run_time=1.2)
            sp = T("slip plane", size=24, color=C_SHEAR).next_to(slip_line, RIGHT, 0.15)
            self.play(FadeIn(sp), run_time=0.4)
            self.play(lat.slip.animate.set_value(1.0), run_time=2.6, rate_func=smooth)
            notes = VGroup(T("lattice intact", size=26, color=C_GOOD), T("volume unchanged", size=26, color=C_GOOD))
            notes.arrange(RIGHT, buff=0.8).to_edge(UP, buff=0.35)
            self.play(FadeIn(notes, shift=DOWN * 0.1), run_time=0.6)
            self.wait(max(0.1, self.left() - 0.8))
            self.play(lat.slip.animate.set_value(0.0), FadeOut(notes), run_time=0.8)
        # ---------------------------------------------------------------- m3 rigid slip needs huge stress
        with self.say("m3") as d:
            lat.bonds_x.set_color(C_BAD)
            self.play(lat.bonds_x.animate.set_stroke(width=5), run_time=0.6)
            eq = M(r"\tau_{\text{theory}}\approx\frac{G}{2\pi}\approx 13\ \text{GPa}", size=40).move_to([-2.9, 3.05, 0])
            self.until("m3", "needing")
            self.play(Write(eq), run_time=1.4)
            self.until("m3", "Real metals")
            eq2 = M(r"\tau_{\text{real}}\approx 10\text{ to }200\ \text{MPa}", size=40, color=C_GOOD).move_to([2.9, 3.05, 0])
            note = T("iron: G ≈ 82 GPa", size=22, color=DIM).next_to(eq, DOWN, 0.15)
            self.play(Write(eq2), FadeIn(note), run_time=1.2)
            self.wait(self.left(0.6))
            self.play(lat.bonds_x.animate.set_stroke(width=2.2).set_color("#4A5A78"), FadeOut(VGroup(eq, eq2, note)),
                      run_time=0.6)
        # ---------------------------------------------------------------- m4 dislocation glide
        with self.say("m4") as d:
            lat.highlight = True
            lat.xd.set_value(-4.9)
            perp = MathTex(r"\perp", color=C_SHEAR, font_size=56)
            perp.add_updater(lambda m: m.move_to([lat.xd.get_value() + lat.c[0], lat.c[1] + 0.05, 0]))
            lab = T("edge dislocation: an extra half-plane", size=26, color=C_SHEAR).to_edge(UP, 0.35)
            self.play(FadeIn(perp), FadeIn(lab), run_time=0.8)
            self.play(lat.xd.animate.set_value(-2.0), run_time=2.0, rate_func=linear)
            self.until("m4", "Under")
            self.play(lat.xd.animate.set_value(4.9), run_time=self.till("m4", "When it exits", minimum=2.5),
                      rate_func=linear)
            self.play(lat.xd.animate.set_value(30.0), run_time=0.6, rate_func=linear)
            perp.clear_updaters()
            self.remove(perp)
            b = T("slipped by one atomic spacing  b", size=26, color=INK).next_to(lab, DOWN, 0.2)
            self.play(FadeIn(b), run_time=0.6)
            self.wait(self.left(0.7))
            lat.highlight = False
            self.play(FadeOut(VGroup(lat, slip_line, sp, tau_top, tau_bot, tt, tb, lab, b)), run_time=0.7)
        # ---------------------------------------------------------------- m5 Schmid's law
        with self.say("m5") as d:
            ang = 45 * DEGREES
            w, h = 1.6, 4.6
            nsl = 7
            # slabs separated by inclined planes (normal at angle phi to the load axis)
            nrm = np.array([np.sin(ang), np.cos(ang), 0])      # slip-plane normal
            sd = np.array([np.cos(ang), -np.sin(ang), 0])      # slip direction (in plane)
            offs = ValueTracker(0.0)
            base = LEFT * 3.6

            def slabs():
                g = VGroup()
                cut = np.linspace(-h / 2 - w, h / 2 + w, nsl + 1)
                for k_ in range(nsl):
                    # clip the bar between two inclined lines y = c - x*tan(ang)
                    pts = []
                    for (c0, c1) in [(cut[k_], cut[k_ + 1])]:
                        for x_ in np.linspace(-w / 2, w / 2, 2):
                            pass
                    c0, c1 = cut[k_], cut[k_ + 1]
                    poly = [[-w / 2, max(-h / 2, min(h / 2, c0 + w / 2 * np.tan(ang)))],
                            [w / 2, max(-h / 2, min(h / 2, c0 - w / 2 * np.tan(ang)))],
                            [w / 2, max(-h / 2, min(h / 2, c1 - w / 2 * np.tan(ang)))],
                            [-w / 2, max(-h / 2, min(h / 2, c1 + w / 2 * np.tan(ang)))]]
                    shift = sd * offs.get_value() * (k_ - (nsl - 1) / 2)
                    P = [np.array([p_[0], p_[1], 0]) + shift + base for p_ in poly]
                    g.add(Polygon(*P, color=C_STEEL, fill_color=C_STEEL, fill_opacity=0.35, stroke_width=1.5))
                return g
            bar = always_redraw(slabs)
            sig_t = Arrow(base + UP * 2.4, base + UP * 3.4, color=C_X, buff=0, stroke_width=6)
            sig_b = Arrow(base + DOWN * 2.4, base + DOWN * 3.4, color=C_X, buff=0, stroke_width=6)
            sl = M(r"\sigma", color=C_X).next_to(sig_t, RIGHT, 0.15)
            self.play(FadeIn(bar), GrowArrow(sig_t), GrowArrow(sig_b), FadeIn(sl), run_time=1.0)
            eq = M(r"\tau_R", r"=", r"\sigma", r"\cos\phi\,\cos\lambda", size=54).shift(RIGHT * 2.6 + UP * 1.4)
            eq[0].set_color(C_SHEAR); eq[2].set_color(C_X)
            nt = VGroup(T("resolved shear stress on the slip plane,", size=24, color=DIM),
                        T("in the slip direction (Schmid's law)", size=24, color=DIM)).arrange(DOWN, aligned_edge=LEFT)
            nt.next_to(eq, DOWN, 0.4).align_to(eq, LEFT)
            mx = M(r"\max \;(\phi=\lambda=45^\circ):\ \ \tau_R=\tfrac{1}{2}\sigma", size=36, color=INK)
            mx.next_to(nt, DOWN, 0.5).align_to(eq, LEFT)
            self.play(Write(eq), FadeIn(nt), run_time=1.5)
            self.until("m5", "Even a crystal")
            self.play(offs.animate.set_value(0.16), FadeIn(mx), run_time=self.till("m5", "on inclined", minimum=1.5) + 1.0)
            self.wait(self.left(0.6))
            bar.clear_updaters()
            self.play(FadeOut(VGroup(bar, sig_t, sig_b, sl, eq, nt, mx)), run_time=0.6)
        # ---------------------------------------------------------------- m6 hydrostatic: no shear anywhere
        with self.say("m6") as d:
            sq = Square(2.6, color=INK, stroke_width=2, fill_color=C_STEEL, fill_opacity=0.15).shift(LEFT * 3)
            arrs = VGroup()
            for v in (UP, DOWN, LEFT, RIGHT):
                for o in (-0.6, 0, 0.6):
                    perp_v = np.array([-v[1], v[0], 0])
                    s0 = sq.get_center() + v * 2.3 + perp_v * o
                    arrs.add(Arrow(s0, s0 - v * 0.9, buff=0, color=C_HYD, stroke_width=5,
                                   max_tip_length_to_length_ratio=0.3))
            pl = M(r"p", color=C_HYD, size=44).next_to(arrs, UP, 0.05)
            self.play(FadeIn(sq), LaggedStart(*[GrowArrow(a_) for a_ in arrs], lag_ratio=0.05), FadeIn(pl),
                      run_time=1.4)
            th = ValueTracker(0.0)
            ctr = sq.get_center()

            def cutline():
                t_ = th.get_value()
                dvec = np.array([np.cos(t_), np.sin(t_), 0])
                n_ = np.array([-np.sin(t_), np.cos(t_), 0])
                ln = Line(ctr - 1.7 * dvec, ctr + 1.7 * dvec, color=C_SHEAR, stroke_width=3)
                tr = Arrow(ctr, ctr - 1.0 * n_, buff=0, color=C_HYD, stroke_width=6)
                return VGroup(ln, tr)
            cl = always_redraw(cutline)
            txt = VGroup(M(r"\mathbf{t}=-p\,\mathbf{n}", size=46),
                         M(r"\sigma_n=-p", size=40, color=C_HYD),
                         M(r"\tau=0\ \text{on every plane}", size=40, color=C_SHEAR)).arrange(DOWN, buff=0.35,
                                                                                         aligned_edge=LEFT)
            txt.shift(RIGHT * 2.8 + UP * 0.6)
            self.play(FadeIn(cl), Write(txt[0]), run_time=1.0)
            self.play(th.animate.set_value(PI), FadeIn(txt[1]), FadeIn(txt[2]), run_time=3.2, rate_func=smooth)
            self.until("m6", "No resolved")
            chain = T("no resolved shear  →  no glide  →  no yielding", size=30, color=INK)
            chain.to_edge(DOWN, buff=1.0)
            self.play(FadeIn(chain, shift=UP * 0.1), run_time=0.8)
            self.until("m6", "as Bridgman")
            br = T("Bridgman, 1952: hydrostatic pressure barely changes the yield of metals", size=22, color=DIM)
            br.next_to(chain, DOWN, 0.3)
            self.play(FadeIn(br), run_time=0.6)
            self.wait(self.left(0.6))
            cl.clear_updaters()
            self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)


class S02b_Decomposition(N3DScene):
    def construct(self):
        self.set_camera_orientation(phi=68 * DEGREES, theta=-58 * DEGREES, zoom=0.82)
        # ---------------------------------------------------------------- d1 decomposition
        lhs = matrix_tex([[r"\sigma_x", r"\tau_{xy}", r"\tau_{xz}"], [r"\tau_{xy}", r"\sigma_y", r"\tau_{yz}"],
                          [r"\tau_{xz}", r"\tau_{yz}", r"\sigma_z"]], size=34, h_buff=0.95)
        for (i, j) in [(0, 0), (1, 1), (2, 2)]:
            lhs.get_rows()[i][j].set_color(COMP[i])
        for (i, j) in [(0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1)]:
            lhs.get_rows()[i][j].set_color(C_SHEAR)
        hyd = matrix_tex([[r"\sigma_m", "0", "0"], ["0", r"\sigma_m", "0"], ["0", "0", r"\sigma_m"]], size=34,
                         h_buff=0.8)
        hyd.set_color(C_HYD)
        dev = matrix_tex([[r"\sigma_x-\sigma_m", r"\tau_{xy}", r"\tau_{xz}"],
                          [r"\tau_{xy}", r"\sigma_y-\sigma_m", r"\tau_{yz}"],
                          [r"\tau_{xz}", r"\tau_{yz}", r"\sigma_z-\sigma_m"]], size=34, h_buff=1.55)
        dev.set_color(C_DEV)
        eqn = VGroup(lhs, M("=", size=46), hyd, M("+", size=46), dev).arrange(RIGHT, buff=0.25)
        eqn.scale_to_fit_width(12.6).move_to(UP * 1.25)
        lab_s = M(r"\boldsymbol{\sigma}", size=40).next_to(lhs, DOWN, 0.2)
        lab_h = M(r"\sigma_m\mathbf{I}", r"\ \text{hydrostatic}", size=34, color=C_HYD).next_to(hyd, DOWN, 0.2)
        lab_d = M(r"\mathbf{s}", r"\ \text{deviatoric}", size=34, color=C_DEV).next_to(dev, DOWN, 0.2)
        sm = M(r"\sigma_m=\tfrac{1}{3}\operatorname{tr}\boldsymbol{\sigma}=\tfrac{1}{3}(\sigma_x+\sigma_y+\sigma_z)",
               size=40).move_to(DOWN * 1.55)
        trs = M(r"\operatorname{tr}\mathbf{s}=0", size=40, color=C_DEV).next_to(sm, DOWN, 0.35)
        with self.say("d1") as d:
            self.add_fixed_in_frame_mobjects(eqn, lab_s, lab_h, lab_d, sm, trs)
            for mob in (eqn, lab_s, lab_h, lab_d, sm, trs):
                self.remove(mob)
            self.play(FadeIn(lhs), FadeIn(lab_s), run_time=0.8)
            self.until("d1", "one third")
            self.play(Write(sm), run_time=1.4)
            self.until("d1", "defines a hydrostatic")
            self.play(FadeIn(eqn[1]), FadeIn(hyd), FadeIn(lab_h), run_time=1.0)
            self.until("d1", "What remains")
            self.play(FadeIn(eqn[3]), FadeIn(dev), FadeIn(lab_d), run_time=1.0)
            self.until("d1", "with zero trace")
            self.play(Write(trs), run_time=0.8)
        # move equation up & small; three cubes appear
        top = VGroup(eqn, lab_s, lab_h, lab_d)
        self.play(top.animate.scale(0.6).to_edge(UP, buff=0.2), FadeOut(sm), FadeOut(trs), run_time=0.8)
        xs = [-5.0, 0.0, 5.0]
        cubes = []
        for i, x in enumerate(xs):
            c = Cube(side_length=1.75, fill_color=C_STEEL, fill_opacity=0.35, stroke_color=INK, stroke_width=1.5)
            c.shift(RIGHT * x * 0.95 + DOWN * 0.6 * 0 + OUT * 0)
            cubes.append(c)
        # map screen-x positions to 3D: with theta=-58deg, use the screen's right vector in world coords
        th, ph = -58 * DEGREES, 68 * DEGREES
        right = np.array([-np.sin(th), np.cos(th), 0])
        upv = np.array([-np.cos(ph) * np.cos(th), -np.cos(ph) * np.sin(th), np.sin(ph)])
        for c, x in zip(cubes, xs):
            c.move_to(right * x + upv * -0.9)
        titles = [M(r"\text{hydrostatic}", size=34, color=C_HYD), M(r"\text{pure shear}", size=34, color=C_DEV),
                  M(r"\text{combined}", size=34, color=INK)]
        notes = [M(r"\Delta V\neq 0,\ \text{shape kept}", size=30, color=C_HYD),
                 M(r"\Delta V=0,\ \text{shape changes}", size=30, color=C_DEV),
                 M(r"\Delta V\neq0\ \&\ \text{distortion}", size=30, color=INK)]
        for k_, (tt, nn) in enumerate(zip(titles, notes)):
            xx = [-4.15, 0.0, 4.15][k_]
            tt.move_to([xx, -2.55, 0]); nn.move_to([xx, -3.2, 0])
            self.add_fixed_in_frame_mobjects(tt, nn); self.remove(tt, nn)
        # deformation gradients (exaggerated for visibility)
        Fh = np.eye(3) * 1.22
        lam = 1.32
        Rz = np.array([[np.cos(PI / 4), -np.sin(PI / 4), 0], [np.sin(PI / 4), np.cos(PI / 4), 0], [0, 0, 1]])
        Fs = Rz @ np.diag([lam, 1 / lam, 1]) @ Rz.T
        Fc = 1.15 * Fs

        def arrows_for(c, kind):
            g = VGroup()
            ctr = c.get_center()
            hh = 0.8
            e = np.eye(3)
            if kind in ("h", "c"):
                for i in range(3):
                    for sgn in (1, -1):
                        p0 = ctr + sgn * e[i] * (hh + 0.05)
                        g.add(Arrow3D(p0, p0 + sgn * e[i] * 0.7, color=C_HYD, thickness=0.03, height=0.2,
                                      base_radius=0.07, resolution=8))
            if kind in ("s", "c"):
                for (i, j) in [(0, 1), (1, 0)]:
                    for sgn in (1, -1):
                        p0 = ctr + sgn * e[i] * (hh + 0.05)
                        g.add(Arrow3D(p0 - sgn * e[j] * 0.45, p0 + sgn * e[j] * 0.45, color=C_DEV, thickness=0.03,
                                      height=0.2, base_radius=0.07, resolution=8))
            return g
        with self.say("d2") as d:
            a0 = arrows_for(cubes[0], "h")
            self.play(FadeIn(cubes[0]), FadeIn(titles[0]), run_time=0.8)
            self.play(FadeIn(a0), run_time=0.6)
            ctr0 = cubes[0].get_center()
            self.play(cubes[0].animate.apply_matrix(Fh, about_point=ctr0), FadeIn(notes[0]), run_time=2.0)
            self.play(cubes[0].animate.apply_matrix(np.linalg.inv(Fh), about_point=ctr0), run_time=1.2)
            self.play(cubes[0].animate.apply_matrix(Fh, about_point=ctr0), run_time=1.2)
        with self.say("d3") as d:
            a1 = arrows_for(cubes[1], "s")
            ctr1 = cubes[1].get_center()
            self.play(FadeIn(cubes[1]), FadeIn(titles[1]), FadeIn(a1), run_time=0.8)
            self.play(cubes[1].animate.apply_matrix(Fs, about_point=ctr1), FadeIn(notes[1]),
                      run_time=max(1.0, d - 1.2))
        with self.say("d4") as d:
            a2 = arrows_for(cubes[2], "c")
            ctr2 = cubes[2].get_center()
            self.play(FadeIn(cubes[2]), FadeIn(titles[2]), FadeIn(a2), run_time=0.8)
            self.play(cubes[2].animate.apply_matrix(Fc, about_point=ctr2), FadeIn(notes[2]),
                      run_time=max(1.0, d - 1.2))
        # ---------------------------------------------------------------- d5 energy choice
        with self.say("d5") as d:
            self.play(*[FadeOut(m_) for m_ in [*cubes, a0, a1, a2, *titles, *notes, top]], run_time=0.8)
            u = M(r"U", r"=", r"U_{\text{vol}}", r"+", r"U_{\text{dist}}", size=60).shift(UP * 1.6)
            u[2].set_color(C_HYD); u[4].set_color(C_DEV)
            self.add_fixed_in_frame_mobjects(u); self.remove(u)
            self.play(Write(u), run_time=1.2)
            b1 = VGroup(T("Total strain energy  U", size=30, color=INK),
                        T("Beltrami, 1885 — predicts yield under pure pressure", size=24, color=DIM)).arrange(
                DOWN, aligned_edge=LEFT, buff=0.15)
            b2 = VGroup(T("Distortion energy  U_dist", size=30, color=C_DEV),
                        T("Huber 1904 · von Mises 1913 · Hencky 1924", size=24, color=DIM)).arrange(
                DOWN, aligned_edge=LEFT, buff=0.15)
            col = VGroup(b1, b2).arrange(DOWN, aligned_edge=LEFT, buff=0.6).shift(DOWN * 0.9 + LEFT * 0.6)
            x1 = T("✗", size=44, color=C_BAD).next_to(b1, LEFT, 0.4)
            x2 = T("✓", size=44, color=C_GOOD).next_to(b2, LEFT, 0.4)
            self.add_fixed_in_frame_mobjects(col, x1, x2); self.remove(col, x1, x2)
            self.until("d5", "rather than")
            self.play(FadeIn(b2), FadeIn(x2), run_time=0.8)
            self.play(FadeIn(b1), run_time=0.8)
            self.until("d5", "would predict")
            self.play(FadeIn(x1), b1.animate.set_opacity(0.55), run_time=0.8)
            self.wait(self.left(0.6))
            self.play(FadeOut(VGroup(u, col, x1, x2)), run_time=0.6)
