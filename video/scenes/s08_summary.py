import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from common import *


def box(text, col, w=3.6, h=1.05, size=20):
    t = T(text, size, TXT)
    if t.width > w - 0.3:
        t.scale((w - 0.3) / t.width)
    r = RoundedRectangle(width=w, height=h, corner_radius=0.15, fill_color=col, fill_opacity=0.16,
                         stroke_color=col, stroke_width=2.2)
    t.move_to(r)
    return VGroup(r, t)


def diamond(text, col, w=3.9, h=1.55, size=19):
    d = Polygon([0, h / 2, 0], [w / 2, 0, 0], [0, -h / 2, 0], [-w / 2, 0, 0], fill_color=col, fill_opacity=0.12,
                stroke_color=col, stroke_width=2.2)
    t = T(text, size, TXT)
    if t.width > w * 0.62:
        t.scale(w * 0.62 / t.width)
    t.move_to(d)
    return VGroup(d, t)


def arrow(a, b, col=MUTED, label=None, lcol=None, side=UP):
    ar = Arrow(a, b, buff=0.08, color=col, stroke_width=3, max_tip_length_to_length_ratio=0.12)
    if label is None:
        return ar
    lt = T(label, 18, lcol or col, weight=BOLD).next_to(ar.get_center(), side, buff=0.08)
    return VGroup(ar, lt)


class S08Summary(SyncScene):
    scene_id = "s08_summary"

    def construct(self):
        tag = chapter_tag(7, "Putting it together")
        self.add(tag)
        A = box("linear-elastic FE analysis", CYAN, w=3.8, h=0.85).move_to(UP * 2.65)
        Bd = diamond("Δσ_eq ≤ 2 σ_y\neverywhere?", CYAN, w=3.6, h=1.45).move_to(UP * 1.0)
        C = box("HIGH-CYCLE FATIGUE\nlocal · hot-spot · notch stress\nmean-stress correction\nrainflow + Miner", C_EL, w=3.7, h=1.9, size=18).move_to(LEFT * 4.6 + DOWN * 0.6)
        D = box("elastic-plastic FE\ncyclic material model\nseveral cycles (≥ 3)", C_AP, w=3.4, h=1.45, size=18).move_to(RIGHT * 4.4 + UP * 1.0)
        Ed = diamond("ratcheting?\nstrain / dimensions grow,\nno elastic core", C_RT, w=3.8, h=1.65, size=17).move_to(RIGHT * 4.4 + DOWN * 1.05)
        F = box("redesign: reduce primary\nor secondary load", C_RT, w=3.3, h=1.0, size=18).move_to(RIGHT * 4.4 + DOWN * 3.1)
        G = box("stabilised loop → strain–life\ncheck ε_peq vs local strain limit", C_AP, w=3.8, h=1.15, size=17).move_to(LEFT * 0.1 + DOWN * 1.05)
        H = box("total damage  D = D_LCF + D_HCF ≤ 1", GREEN, w=4.4, h=0.8, size=20).move_to(LEFT * 2.3 + DOWN * 3.1)
        a1 = arrow(A.get_bottom(), Bd.get_top())
        a2 = arrow(Bd.get_left(), [C.get_top()[0], Bd.get_left()[1], 0], C_EL, "yes", side=UP)
        a2b = arrow([C.get_top()[0], Bd.get_left()[1], 0], C.get_top(), C_EL)
        a3 = arrow(Bd.get_right(), D.get_left(), C_AP, "no", side=UP)
        a3b = VGroup()
        a4 = arrow(D.get_bottom(), Ed.get_top(), C_AP)
        a5 = arrow(Ed.get_bottom(), F.get_top(), C_RT, "yes", side=RIGHT)
        a6 = arrow(Ed.get_left(), G.get_right(), C_AP, "no", side=UP)
        a6b = VGroup()
        a7 = arrow(G.get_bottom(), [G.get_bottom()[0], H.get_top()[1], 0], GREEN)
        a8 = arrow(C.get_bottom(), [C.get_bottom()[0], H.get_left()[1], 0] + RIGHT * 0.0, GREEN)
        a8 = VGroup(Line(C.get_bottom(), [C.get_bottom()[0], H.get_left()[1], 0], color=GREEN, stroke_width=3),
                    arrow([C.get_bottom()[0], H.get_left()[1], 0], H.get_left(), GREEN))
        self.wait_until(self.start("b"))
        self.play(FadeIn(A, shift=DOWN * 0.2), run_time=0.8)
        self.play(FadeIn(a1), FadeIn(Bd), run_time=1.0)
        self.wait_until(self.start("b") + self.dur("b") * 0.45)
        self.play(FadeIn(a2), FadeIn(a2b), FadeIn(C, shift=DOWN * 0.2), run_time=1.0)
        self.cue("c")
        self.play(FadeIn(a3), FadeIn(a3b), FadeIn(D, shift=DOWN * 0.2), run_time=1.0)
        self.wait_until(self.start("c") + self.dur("c") * 0.28)
        self.play(FadeIn(a4), FadeIn(Ed), run_time=1.0)
        self.play(FadeIn(a5), FadeIn(F), run_time=0.8)
        self.wait_until(self.start("c") + self.dur("c") * 0.5)
        self.play(FadeIn(a6), FadeIn(a6b), FadeIn(G, shift=DOWN * 0.2), run_time=1.0)
        self.wait_until(self.start("c") + self.dur("c") * 0.8)
        self.play(FadeIn(a7), FadeIn(a8), FadeIn(H, shift=LEFT * 0.2), run_time=1.0)
        # ---- d
        self.cue("d")
        chart = VGroup(A, Bd, C, D, Ed, F, G, H, a1, a2, a2b, a3, a3b, a4, a5, a6, a6b, a7, a8)
        self.play(chart.animate.set_opacity(0.07), run_time=0.8)
        lines = VGroup(
            VGroup(T("HIGH-CYCLE FATIGUE", 30, C_EL, weight=BOLD), T("stress amplitude · strength", 28, TXT)).arrange(RIGHT, buff=0.4),
            VGroup(T("LOW-CYCLE FATIGUE", 30, C_AP, weight=BOLD), T("plastic strain range · ductility", 28, TXT)).arrange(RIGHT, buff=0.4),
            VGroup(T("ACCUMULATED PLASTIC STRAIN", 30, C_RT, weight=BOLD), T("only meaningful once you know:\nshakedown, LCF — or ratcheting?", 26, TXT)).arrange(RIGHT, buff=0.4),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.55).move_to(DOWN * 0.2)
        for k, l in enumerate(lines):
            self.wait_until(self.start("d") + self.dur("d") * (0.02 + 0.3 * k))
            self.play(FadeIn(l, shift=RIGHT * 0.2), run_time=0.8)
        # ---- e
        self.cue("e")
        self.play(FadeOut(chart), FadeOut(lines), FadeOut(tag), run_time=0.5)
        ty = T("Thanks for watching", 54, TXT, weight=BOLD).move_to(UP * 0.4)
        cr = T("FE: in-house Q9 cyclic-plasticity solver, verified against CalculiX  ·  voice: Kokoro TTS", 20, MUTED).next_to(ty, DOWN, buff=0.4)
        self.play(FadeIn(ty, scale=1.1), FadeIn(cr), run_time=0.8)
        self.wait(1.5)
