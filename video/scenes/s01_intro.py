import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from common import *


class S01Intro(SyncScene):
    scene_id = "s01_intro"

    def construct(self):
        lcf = load_npz("plate_lcf.npz")
        hcf = load_npz("plate_hcf.npz")

        # ---------------------------------------------------------------- a
        tr = ValueTracker(0)
        plate = FrameSeq(frames("intro_lcf_vm"), tr, height=6.1, loop=True).move_to(LEFT * 3.4 + DOWN * 0.05)
        tr.add_updater(lambda m, dt: m.increment_value(dt * 40 / 2.2))   # one load cycle per 2.2 s
        self.add(tr)
        # load arrows on top / bottom of the plate (pulsing)
        def arrows():
            s = np.sin(2 * np.pi * self.now / 2.2)
            g = VGroup()
            top = plate.get_top()[1]
            bot = plate.get_bottom()[1]
            for x in np.linspace(plate.get_left()[0] + 0.45, plate.get_right()[0] - 0.45, 5):
                L = 0.42 * s
                col = AMBER if s > 0 else CYAN
                if abs(L) > 0.05:
                    g.add(Arrow([x, top + 0.15 + (0 if L > 0 else -L), 0], [x, top + 0.15 + (L if L > 0 else 0), 0],
                                buff=0, color=col, stroke_width=4, max_tip_length_to_length_ratio=0.45))
                    g.add(Arrow([x, bot - 0.15 - (0 if L > 0 else -L), 0], [x, bot - 0.15 - (L if L > 0 else 0), 0],
                                buff=0, color=col, stroke_width=4, max_tip_length_to_length_ratio=0.45))
            return g
        arr = always_redraw(arrows)

        counter_lbl = T("LOAD CYCLES", 22, MUTED, weight=BOLD)
        ntr = ValueTracker(0.0)
        counter_lbl.move_to(RIGHT * 3.7 + UP * 2.5)
        counter = always_redraw(lambda: T(f"{int(10 ** ntr.get_value()):,}", 72, TXT, weight=BOLD).next_to(counter_lbl, DOWN, buff=0.25))
        cgroup = VGroup(counter_lbl, counter)

        self.play(FadeIn(plate, scale=0.96), run_time=1.6)
        self.add(arr)
        self.play(FadeIn(counter_lbl), run_time=0.5)
        self.add(cgroup)
        self.play(ntr.animate.set_value(6.3), run_time=self.until("a", 1.0) + 2.0, rate_func=rate_functions.ease_in_quad)

        # ---------------------------------------------------------------- b
        self.cue("b")
        title = T("FATIGUE", 64, AMBER, weight=BOLD).move_to(RIGHT * 3.7 + DOWN * 0.35)
        sub = T("failure under repeated loads\nwell below the static strength", 26, MUTED).next_to(title, DOWN, buff=0.3)
        self.play(FadeIn(title, shift=UP * 0.2), run_time=0.8)
        self.play(FadeIn(sub), run_time=0.8)
        # crack growing from the hole flanks
        pts_r = [mm2pt(plate, x, y) for x, y in [(10.3, 0), (12, 0.6), (14, -0.3), (16.5, 0.5), (19, -0.4), (22.5, 0.3)]]
        pts_l = [mm2pt(plate, -x, -y) for x, y in [(10.3, 0), (12, 0.6), (14, -0.3), (16.5, 0.5), (19, -0.4), (22.5, 0.3)]]
        cr = glow_line(pts_r, RED, 4)
        cl = glow_line(pts_l, RED, 4)
        self.play(Create(cr), Create(cl), run_time=3.0, rate_func=linear)
        self.wait_until(self.end("b") - 0.4)

        # ---------------------------------------------------------------- c
        self.cue("c")
        self.play(FadeOut(VGroup(title, sub, cgroup, cr, cl)), FadeOut(arr), plate.animate.set_opacity(0.0), run_time=0.8)
        self.remove(plate, arr)
        tr.clear_updaters()

        def regime_card(xc, head, color, sub1, data, ylab):
            box = card(6.2, 5.6).move_to([xc, -0.35, 0])
            h = T(head, 30, color, weight=BOLD).next_to(box.get_top(), DOWN, buff=0.35)
            ax = Axes(x_range=[-0.5, 0.5, 0.25], y_range=[-450, 450, 150], x_length=4.6, y_length=3.0,
                      axis_config={"color": GRID, "stroke_width": 2, "include_ticks": False}).next_to(h, DOWN, buff=0.35)
            xl = M(r"\varepsilon", 30, MUTED).next_to(ax.x_axis, RIGHT, buff=0.1)
            yl = M(r"\sigma", 30, MUTED).next_to(ax.y_axis, UP, buff=0.05)
            s = T(sub1, 22, TXT).next_to(ax, DOWN, buff=0.35)
            eps, sig = data
            curve = loop_curve(ax, eps * 100, sig, color, 3.5)
            return VGroup(box, h, ax, xl, yl, s), curve

        m1 = hcf["T_cycle"] <= 2
        m2 = lcf["T_cycle"] <= 3
        g1, c1 = regime_card(-3.4, "HIGH-CYCLE FATIGUE", CYAN, "elastic  ·  10⁵ – 10⁹ cycles  ·  stress-controlled",
                             (hcf["T_root_eyy"][m1], hcf["T_root_syy"][m1]), "")
        g2, c2 = regime_card(3.4, "LOW-CYCLE FATIGUE", AMBER, "plastic  ·  10² – 10⁴ cycles  ·  strain-controlled",
                             (lcf["T_root_eyy"][m2], lcf["T_root_syy"][m2]), "")
        self.play(FadeIn(g1, shift=RIGHT * 0.3), run_time=0.9)
        self.play(Create(c1), run_time=2.5, rate_func=linear)
        self.play(FadeIn(g2, shift=LEFT * 0.3), run_time=0.9)
        self.play(Create(c2), run_time=self.until("c", 1.0, -0.3), rate_func=linear)
        area = Polygon(*c2.get_points()[-160::4], fill_color=AMBER, fill_opacity=0.18, stroke_width=0)

        # ---------------------------------------------------------------- d
        self.cue("d")
        self.play(VGroup(g1, c1, g2, c2).animate.scale(0.55).to_edge(UP, buff=0.35), run_time=1.0)
        items = [("1", "Two regimes", "what separates LCF and HCF", CYAN),
                 ("2", "Life prediction", "stress–life · strain–life · notch & weld methods", GREEN),
                 ("3", "Accumulated plastic strain", "shakedown · ratcheting · code criteria", AMBER)]
        rows = VGroup()
        for n, a, b, col in items:
            num = Circle(radius=0.32, color=col, stroke_width=3).set_fill(col, 0.15)
            nt = T(n, 26, col, weight=BOLD).move_to(num)
            ta = T(a, 30, TXT, weight=BOLD)
            tb = T(b, 22, MUTED)
            txt = VGroup(ta, tb).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
            rows.add(VGroup(VGroup(num, nt), txt).arrange(RIGHT, buff=0.35))
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.45).move_to(DOWN * 1.25 + LEFT * 0.6)
        for r in rows:
            self.play(FadeIn(r, shift=RIGHT * 0.3), run_time=0.7)
            self.wait(0.6)
        q = T("PEEQ = ?", 40, AMBER, weight=BOLD).next_to(rows[2], RIGHT, buff=0.8)
        self.wait_until(self.start("d") + self.dur("d") * 0.62)
        self.play(Write(q), run_time=1.0)
        self.play(Indicate(q, color=RED, scale_factor=1.15), run_time=1.2)

        # ---------------------------------------------------------------- e
        self.cue("e")
        self.play(FadeOut(VGroup(g1, c1, g2, c2, rows, q)), run_time=0.8)
        bg = ImageMobject(os.path.join(FRAMES, "mesh_bg.png")).set_height(11.0).set_opacity(0.0).move_to(ORIGIN)
        self.add(bg)
        self.play(bg.animate.set_opacity(0.22), run_time=0.8)
        t1 = T("LOW-CYCLE  vs  HIGH-CYCLE", 66, TXT, weight=BOLD)
        t2 = T("FATIGUE", 96, AMBER, weight=BOLD)
        t3 = T("life prediction  ·  accumulated plastic strain  ·  ratcheting", 28, MUTED)
        ttl = VGroup(t1, t2, t3).arrange(DOWN, buff=0.3).move_to(UP * 0.5)
        badges = VGroup(pill("Q9 finite elements", CYAN), pill("Chaboche cyclic plasticity", AMBER),
                        pill("verified vs CalculiX", GREEN)).arrange(RIGHT, buff=0.35).next_to(ttl, DOWN, buff=0.7)
        self.play(FadeIn(t1, shift=UP * 0.2), run_time=0.8)
        self.play(FadeIn(t2, scale=1.15), run_time=0.8)
        self.play(FadeIn(t3), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(b, shift=UP * 0.2) for b in badges], lag_ratio=0.3), run_time=1.4)
        self.finish()
