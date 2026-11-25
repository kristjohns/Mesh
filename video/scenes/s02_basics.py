import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from common import *
from scipy.spatial import Voronoi


def bounded_voronoi(pts, xmin, xmax, ymin, ymax):
    """Voronoi cells clipped to a box (mirror trick). Returns list of polygons."""
    P = pts
    mirrored = [P,
                np.c_[2 * xmin - P[:, 0], P[:, 1]], np.c_[2 * xmax - P[:, 0], P[:, 1]],
                np.c_[P[:, 0], 2 * ymin - P[:, 1]], np.c_[P[:, 0], 2 * ymax - P[:, 1]]]
    allp = np.vstack(mirrored)
    vor = Voronoi(allp)
    polys = []
    for i in range(len(P)):
        reg = vor.regions[vor.point_region[i]]
        if -1 in reg or len(reg) == 0:
            continue
        poly = vor.vertices[reg]
        c = poly.mean(axis=0)
        ang = np.arctan2(poly[:, 1] - c[1], poly[:, 0] - c[0])
        polys.append(poly[np.argsort(ang)])
    return polys


def clip_line_to_poly(p0, d, poly):
    """Infinite line p0 + t d clipped to convex polygon -> (a, b) or None."""
    tmin, tmax = -1e9, 1e9
    n = len(poly)
    c = poly.mean(axis=0)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        e = b - a
        nrm = np.array([e[1], -e[0]])
        if np.dot(nrm, c - a) > 0:      # inward normal
            nrm = -nrm
        # points inside satisfy dot(nrm, x - a) <= 0
        den = np.dot(nrm, d)
        num = -np.dot(nrm, p0 - a)
        if abs(den) < 1e-12:
            if num < 0:
                return None
            continue
        t = num / den
        if den > 0:
            tmax = min(tmax, t)
        else:
            tmin = max(tmin, t)
    if tmin >= tmax:
        return None
    return p0 + tmin * d, p0 + tmax * d


class S02Basics(SyncScene):
    scene_id = "s02_basics"

    def construct(self):
        tag = chapter_tag(1, "How fatigue works")
        self.add(tag)
        rng = np.random.default_rng(3)
        X0, X1, Y0, Y1 = -6.0, 6.0, -3.4, 2.6
        pts = np.c_[rng.uniform(X0, X1, 70), rng.uniform(Y0, Y1, 70)]
        polys = bounded_voronoi(pts, X0, X1, Y0, Y1)
        grains = VGroup()
        for p in polys:
            col = interpolate_color(ManimColor("#16203a"), ManimColor("#24345a"), rng.uniform())
            grains.add(Polygon(*[[x, y, 0] for x, y in p], fill_color=col, fill_opacity=1.0,
                               stroke_color="#3b4c75", stroke_width=1.6))
        surface = Line([X0, Y1, 0], [X1, Y1, 0], color=TXT, stroke_width=3)
        lab_surf = T("free surface", 22, MUTED).next_to(surface, UP, buff=0.12).to_edge(RIGHT, buff=0.8)
        # cyclic load arrows
        larr = VGroup(DoubleArrow([X0 - 0.05, -0.4, 0], [X0 - 0.95, -0.4, 0], buff=0, color=AMBER, stroke_width=5, tip_length=0.2),
                      DoubleArrow([X1 + 0.05, -0.4, 0], [X1 + 0.95, -0.4, 0], buff=0, color=AMBER, stroke_width=5, tip_length=0.2))
        llab = T("cyclic load", 20, AMBER).next_to(larr[1], DOWN, buff=0.15)
        self.play(LaggedStart(*[FadeIn(g) for g in grains], lag_ratio=0.01), run_time=1.6)
        self.play(Create(surface), FadeIn(lab_surf), GrowFromCenter(larr[0]), GrowFromCenter(larr[1]), FadeIn(llab), run_time=1.0)
        self.play(Wiggle(larr, scale_value=1.15, rotation_angle=0), run_time=1.0)
        # pick a surface grain near x = -1.5
        cand = [i for i, p in enumerate(polys) if p[:, 1].max() > Y1 - 1e-6 and -3 < p[:, 0].mean() < 0]
        gi = cand[0]
        gp = polys[gi]
        hl = grains[gi]
        self.play(hl.animate.set_fill("#2f4b84"), run_time=0.6)
        # slip bands at 45 deg
        d = np.array([1.0, -1.0]) / np.sqrt(2)
        c = gp.mean(axis=0)
        bands = VGroup()
        for off in np.linspace(-0.6, 0.6, 7):
            p0 = c + off * np.array([1.0, 1.0]) / np.sqrt(2)
            seg = clip_line_to_poly(p0, d, gp)
            if seg is not None:
                a, b = seg
                bands.add(Line([a[0], a[1], 0], [b[0], b[1], 0], color=CYAN, stroke_width=2.5))
        lbl_psb = T("persistent slip bands", 24, CYAN, weight=BOLD).move_to([c[0] + 2.8, c[1] - 1.4, 0])
        self.play(FadeOut(tag), self.camera.frame.animate.scale(0.55).move_to([c[0] + 0.6, Y1 - 1.2, 0]), run_time=1.6)
        self.play(LaggedStart(*[Create(b) for b in bands], lag_ratio=0.15), FadeIn(lbl_psb), run_time=1.6)
        # extrusions / intrusions on the free surface
        xs_ = np.linspace(gp[:, 0].min(), gp[:, 0].max(), 80)
        flat = VMobject().set_points_as_corners([[x, Y1, 0] for x in xs_]).set_stroke(TXT, 3)
        teeth = []
        for i, x in enumerate(xs_):
            k = (i // 8) % 4
            h = [0.0, 0.14, 0.0, -0.12][k] if 8 < i < 72 else 0.0
            teeth.append([x, Y1 + h, 0])
        jag = VMobject().set_points_as_corners(teeth).set_stroke(TXT, 3)
        lbl_ext = T("extrusions & intrusions", 22, AMBER, weight=BOLD).next_to(jag, UP, buff=0.25)
        self.remove(surface)
        surface_rest = VGroup(Line([X0, Y1, 0], [xs_[0], Y1, 0], color=TXT, stroke_width=3),
                              Line([xs_[-1], Y1, 0], [X1, Y1, 0], color=TXT, stroke_width=3))
        self.add(surface_rest, flat)
        self.play(Transform(flat, jag), FadeIn(lbl_ext), run_time=self.until("a", 1.0, -0.2))

        # ---------------------------------------------------------------- b
        self.cue("b")
        # crack: stage I (45 deg) then stage II (perpendicular to load -> vertical)
        start = np.array([xs_[38], Y1 - 0.1])
        p1 = start + 0.9 * d
        stage1 = [start, p1]
        stage2 = [p1]
        y = p1[1]
        x = p1[0]
        while y > Y0 + 1.6:
            y -= 0.3
            x += rng.normal(0, 0.06)
            stage2.append(np.array([x, y]))
        c1 = glow_line([[q[0], q[1], 0] for q in stage1], RED, 4)
        c2 = glow_line([[q[0], q[1], 0] for q in stage2], RED, 4)
        l1 = T("stage I: along slip planes", 20, RED, weight=BOLD).move_to([start[0] - 2.4, start[1] - 0.55, 0])
        self.play(FadeOut(lbl_psb), Create(c1), FadeIn(l1), run_time=1.6)
        self.play(self.camera.frame.animate.scale(1.0 / 0.55).move_to(ORIGIN), FadeIn(tag), run_time=1.4)
        mid2 = stage2[len(stage2) // 2]
        l2 = T("stage II:\n⟂ to max. principal stress", 22, RED, weight=BOLD).next_to([mid2[0], mid2[1], 0], LEFT, buff=0.3)
        self.play(Create(c2), FadeIn(l2), run_time=self.until("b", 0.55), rate_func=linear)
        # fracture surface inset
        circ_c = np.array([4.75, -0.7, 0])
        R = 1.65
        disc = Circle(radius=R, color=TXT, stroke_width=2.5).set_fill("#2b3550", 1).move_to(circ_c)
        init = circ_c + R * np.array([np.cos(2.3), np.sin(2.3), 0])
        beach = VGroup()
        for k, r in enumerate(np.linspace(0.35, 2.2, 7)):
            th = np.linspace(0, 2 * np.pi, 240)
            ptsb = np.c_[init[0] + r * np.cos(th), init[1] + r * np.sin(th)]
            inside = np.hypot(ptsb[:, 0] - circ_c[0], ptsb[:, 1] - circ_c[1]) < R - 0.02
            if inside.all() or not inside.any():
                continue
            # rotate so that the contiguous inside run starts at index 0 (handles wrap-around at theta = 0)
            k0 = int(np.nonzero(inside & ~np.roll(inside, 1))[0][0])
            ins = np.roll(inside, -k0)
            pr = np.roll(ptsb, -k0, axis=0)
            n_in = int(np.argmin(ins)) if not ins.all() else len(ins)
            seg = pr[:n_in]
            if len(seg) > 2:
                beach.add(VMobject().set_points_as_corners([[p[0], p[1], 0] for p in seg]).set_stroke(AMBER, 2, opacity=0.85))
        fast = VGroup()
        for k in range(160):
            a = rng.uniform(0, 2 * np.pi); rr = R * np.sqrt(rng.uniform(0.0, 1.0))
            p = circ_c + rr * np.array([np.cos(a), np.sin(a), 0])
            if np.linalg.norm(p - init) > 2.35:
                fast.add(Dot(p, radius=0.03, color=MUTED))
        inset_bg = card(4.4, 4.6).move_to(circ_c + DOWN * 0.15)
        inset_t = T("fracture surface", 22, MUTED, weight=BOLD).next_to(inset_bg.get_top(), DOWN, buff=0.15)
        star = Star(5, outer_radius=0.14, color=RED, fill_opacity=1).move_to(init)
        self.play(FadeOut(VGroup(larr[1], llab)), FadeIn(inset_bg), FadeIn(inset_t), FadeIn(disc), run_time=0.7)
        self.play(FadeIn(star, scale=2), run_time=0.4)
        self.play(LaggedStart(*[Create(b) for b in beach], lag_ratio=0.3), run_time=self.until("b", 0.98))
        lb = T("beach marks", 20, AMBER).next_to(disc, DOWN, buff=0.1)

        # ---------------------------------------------------------------- c
        self.cue("c")
        self.play(FadeIn(fast, lag_ratio=0.02), FadeIn(lb), run_time=1.2)
        lf = T("final fast fracture (rough zone)", 18, MUTED).next_to(lb, DOWN, buff=0.06)
        self.play(FadeIn(lf), Flash(disc.get_center() + RIGHT * 0.8 + DOWN * 0.6, color=RED, flash_radius=0.5), run_time=1.0)
        self.wait_until(self.end("c") - 0.2)

        # ---------------------------------------------------------------- d
        self.cue("d")
        everything = Group(*[m for m in self.mobjects if m is not tag])
        self.play(FadeOut(everything), run_time=0.8)
        head = T("fatigue life  =  crack initiation  +  crack growth", 36, TXT, weight=BOLD).move_to(UP * 2.0)
        self.play(FadeIn(head, shift=UP * 0.2), run_time=0.8)
        def lifebar(frac, y, label):
            W = 9.0
            a = Rectangle(width=W * frac, height=0.6, fill_color=CYAN, fill_opacity=0.85, stroke_width=0)
            b = Rectangle(width=W * (1 - frac), height=0.6, fill_color=RED, fill_opacity=0.85, stroke_width=0)
            VGroup(a, b).arrange(RIGHT, buff=0).move_to([0.9, y, 0])
            lab = T(label, 24, TXT).next_to(VGroup(a, b), LEFT, buff=0.35)
            return VGroup(a, b, lab)
        b1 = lifebar(0.85, 0.5, "smooth part, HCF")
        b2 = lifebar(0.25, -0.6, "notch · weld · LCF")
        leg = VGroup(VGroup(Square(0.25, fill_color=CYAN, fill_opacity=0.85, stroke_width=0), T("initiation", 22, MUTED)).arrange(RIGHT, buff=0.15),
                     VGroup(Square(0.25, fill_color=RED, fill_opacity=0.85, stroke_width=0), T("growth", 22, MUTED)).arrange(RIGHT, buff=0.15)
                     ).arrange(RIGHT, buff=0.6).move_to(DOWN * 1.7)
        self.play(GrowFromEdge(b1[0], LEFT), GrowFromEdge(b1[1], LEFT), FadeIn(b1[2]), run_time=1.2)
        self.play(GrowFromEdge(b2[0], LEFT), GrowFromEdge(b2[1], LEFT), FadeIn(b2[2]), FadeIn(leg), run_time=1.2)
        self.wait_until(self.end("d") - 0.3)

        # ---------------------------------------------------------------- e
        self.cue("e")
        self.play(FadeOut(VGroup(head, b1, b2, leg)), run_time=0.6)
        ax = Axes(x_range=[0, 4.2, 1], y_range=[-1.6, 3.4, 1], x_length=7.4, y_length=5.0,
                  axis_config={"color": GRID, "stroke_width": 2, "include_ticks": False}).move_to(LEFT * 2.6 + DOWN * 0.3)
        xl = T("time", 22, MUTED).next_to(ax.x_axis, RIGHT, buff=0.1)
        yl = M(r"\sigma", 34, MUTED).next_to(ax.y_axis, UP, buff=0.1)
        sm, sa = 1.0, 1.6
        wave = ax.plot(lambda t: sm + sa * np.sin(2 * np.pi * t / 1.4), x_range=[0, 4.2], color=AMBER, stroke_width=4)
        self.play(Create(ax), FadeIn(xl), FadeIn(yl), run_time=0.8)
        self.play(Create(wave), run_time=1.8, rate_func=linear)
        def hline(y, col):
            return DashedLine(ax.c2p(0, y), ax.c2p(4.2, y), color=col, stroke_width=2, dash_length=0.12)
        lmax, lmin, lmean = hline(sm + sa, RED), hline(sm - sa, CYAN), hline(sm, TXT)
        tmax = M(r"\sigma_{\max}", 32, RED).next_to(ax.c2p(4.2, sm + sa), RIGHT, buff=0.15)
        tmin = M(r"\sigma_{\min}", 32, CYAN).next_to(ax.c2p(4.2, sm - sa), RIGHT, buff=0.15)
        tmean = M(r"\sigma_m", 32, TXT).next_to(ax.c2p(4.2, sm), RIGHT, buff=0.15)
        self.play(Create(lmax), Create(lmin), FadeIn(tmax), FadeIn(tmin), run_time=1.2)
        x0 = 1.4 * 0.25
        br_range = BraceBetweenPoints(ax.c2p(1.4 * 1.25 + 0.12, sm - sa), ax.c2p(1.4 * 1.25 + 0.12, sm + sa), direction=RIGHT, color=PINK)
        t_range = M(r"\Delta\sigma", 40, PINK).next_to(br_range, RIGHT, buff=0.12).shift(UP * 0.6)
        self.play(GrowFromCenter(br_range), FadeIn(t_range), run_time=1.0)
        br_amp = BraceBetweenPoints(ax.c2p(x0 - 0.12, sm), ax.c2p(x0 - 0.12, sm + sa), direction=LEFT, color=GREEN)
        t_amp = M(r"\sigma_a", 34, GREEN).next_to(br_amp, LEFT, buff=0.1)
        self.play(GrowFromCenter(br_amp), FadeIn(t_amp), run_time=1.0)
        self.play(Create(lmean), FadeIn(tmean), run_time=0.8)
        eqR = VGroup(M(r"R=\frac{\sigma_{\min}}{\sigma_{\max}}", 40, TXT), M(r"\sigma_a=\frac{\Delta\sigma}{2}", 34, GREEN)).arrange(DOWN, buff=0.35).move_to(RIGHT * 4.9 + UP * 2.0)
        self.play(Write(eqR), run_time=1.0)
        # two standard cases
        def mini(Rv, label, y, col):
            a2 = Axes(x_range=[0, 2.8, 1], y_range=[-1.2, 1.2, 1], x_length=3.0, y_length=1.2,
                      axis_config={"color": GRID, "stroke_width": 1.5, "include_ticks": False})
            if Rv == -1:
                f = lambda t: np.sin(2 * np.pi * t / 1.4)
            else:
                f = lambda t: 0.5 - 0.5 * np.cos(2 * np.pi * t / 1.4)
            w = a2.plot(f, x_range=[0, 2.8], color=col, stroke_width=3)
            tt = T(label, 22, col, weight=BOLD).next_to(a2, UP, buff=0.08)
            return VGroup(a2, w, tt).move_to([4.9, y, 0])
        m1 = mini(-1, "R = −1  fully reversed", -0.55, CYAN)
        m2 = mini(0, "R = 0  pulsating tension", -2.55, AMBER)
        self.wait_until(self.start("e") + self.dur("e") * 0.78)
        self.play(FadeIn(m1, shift=LEFT * 0.2), run_time=0.8)
        self.play(FadeIn(m2, shift=LEFT * 0.2), run_time=0.8)
        self.finish()
