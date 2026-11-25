from figstyle import *
from matplotlib.patches import FancyArrowPatch, Circle


# ----------------------------------------------------------------------------- Figure 3: notches
def fig3():
    fig = plt.figure(figsize=(TEXTWIDTH, 2.45))
    axa = fig.add_axes([0.0, 0.05, 0.215, 0.76])
    cax = fig.add_axes([0.222, 0.20, 0.011, 0.50])
    axb = fig.add_axes([0.35, 0.17, 0.30, 0.71])
    axc = fig.add_axes([0.74, 0.17, 0.25, 0.71])
    d = load("plate_hcf.npz")
    nodes, elems = d["nodes"], d["elems"]
    v = d["F_syy"][9] / 70.0
    P, Es = mirrored(nodes, elems)
    m = field(axa, P, Es, np.tile(v, 4), -0.6, 3.3, STRESS_CMAP)
    axa.set_xlim(-42, 42); axa.set_ylim(-50, 50)
    clean(axa)
    for x in np.linspace(-32, 32, 5):
        axa.annotate("", xy=(x, 58), xytext=(x, 50.5), arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=1.0), annotation_clip=False)
        axa.annotate("", xy=(x, -58), xytext=(x, -50.5), arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=1.0), annotation_clip=False)
    axa.annotate(r"$K_t=3.25$", xy=(10.5, 0), xytext=(2, -36), fontsize=8.5, color=TXT, fontweight="bold",
                 bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85),
                 arrowprops=dict(arrowstyle="-|>", color=TXT, lw=1.0))
    axa.text(0, 17, "−1", color="white", fontsize=7.5, ha="center")
    cb = fig.colorbar(m, cax=cax, ticks=[0, 1, 2, 3])
    cb.ax.tick_params(labelsize=6.5, length=2)
    cb.outline.set_visible(False)
    cax.set_title(r"$\sigma_{yy}/S$", fontsize=7, pad=3)
    panel_label(axa, "(a) elastic stress ÷ remote stress", x=0.0, y=1.09)
    # (b) ligament
    lig = np.nonzero(np.abs(nodes[:, 1]) < 1e-9)[0]
    lig = lig[np.argsort(nodes[lig, 0])]
    xs, sy = nodes[lig, 0], v[lig]
    a = 10.0
    xk = np.linspace(10, 40, 200)
    axb.plot(xk, 1 + 0.5 * (a / xk) ** 2 + 1.5 * (a / xk) ** 4, color=GRAY, lw=1.2, ls="--", label="infinite plate (Kirsch): 3.0")
    axb.plot(xs, sy, color=ORANGE, lw=2.2, label="FE, finite width: 3.25")
    axb.axhline(1 / 0.75, color=BLUE, lw=1, ls=":")
    axb.text(39.5, 1 / 0.75 + 0.04, "net-section average = 1.33", color=BLUE, fontsize=7, ha="right", va="bottom")
    axb.annotate("peak at the hole edge\n→ fatigue starts here", xy=(10.2, sy[0]), xytext=(17, 2.75), fontsize=7.2,
                 arrowprops=dict(arrowstyle="-|>", color=TXT, lw=0.8))
    axb.set_xlim(10, 40); axb.set_ylim(0, 3.5)
    axb.set_xlabel("distance from centre along the ligament [mm]")
    axb.set_ylabel(r"$\sigma_{yy}/S$")
    axb.legend(loc="upper right", bbox_to_anchor=(1.0, 0.62), fontsize=6.8)
    panel_label(axb, "(b) the concentration is local")
    # (c) notch sensitivity
    r = np.linspace(0.01, 10, 300)
    for su, col, lab in [(510, BLUE, r"S355, $S_u\approx510$ MPa ($a=0.32$ mm)"), (1400, GREEN, r"high-strength, $S_u\approx1400$ MPa")]:
        aP = 0.0254 * (2070.0 / su) ** 1.8
        axc.plot(r, 1 / (1 + aP / r), color=col, lw=2, label=lab)
    q10 = 1 / (1 + 0.0254 * (2070 / 510) ** 1.8 / 10)
    axc.plot([10], [q10], "o", color=ORANGE, ms=6, zorder=5, clip_on=False)
    axc.annotate("our hole: r = 10 mm\nq = 0.97 → K$_f$ ≈ 3.18", xy=(10, q10), xytext=(3.2, 0.45), fontsize=7.2, color="#9A5B00",
                 arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=0.8))
    axc.text(0.25, 0.08, "sharp notch: steep gradient,\nsmall stressed volume → q < 1", fontsize=6.6, color=GRAY)
    axc.set_xlim(0, 10.3); axc.set_ylim(0, 1.05)
    axc.set_xlabel("notch radius r [mm]"); axc.set_ylabel("notch sensitivity q")
    axc.legend(loc="lower right", bbox_to_anchor=(1.0, 0.18), fontsize=6.2)
    panel_label(axc, r"(c) $K_f$ ≤ $K_t$")
    save(fig, "fig03_notch")


# ----------------------------------------------------------------------------- Figure 4: welds
def fig4():
    w = load("weld_tjoint.npz")
    meta = json.loads(str(w["meta"]))
    bm = meta["bending"]
    t, x_toe, cx, cy, rr = meta["t"], meta["x_toe"], meta["cx"], meta["cy"], meta["r"]
    nodes, elems = w["nodes"], w["elems"]
    s1 = w["bending_s1"]
    fig = plt.figure(figsize=(TEXTWIDTH, 4.0))
    axa = fig.add_axes([0.0, 0.56, 0.62, 0.40])
    cax = fig.add_axes([0.625, 0.62, 0.010, 0.26])
    axd = fig.add_axes([0.76, 0.665, 0.235, 0.27])
    axb = fig.add_axes([0.065, 0.08, 0.46, 0.37])
    axc = fig.add_axes([0.60, 0.02, 0.40, 0.42])
    # (a) whole joint
    P, Es = mirrored(nodes, elems, quadrants=2)
    m = field(axa, P, Es, np.tile(s1, 2), -20, 280, STRESS_CMAP)
    axa.set_xlim(-100, 100); axa.set_ylim(-14, 82)
    clean(axa)
    axa.annotate("", xy=(0, 78), xytext=(0, 61), arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=1.6), annotation_clip=False)
    axa.text(4, 70, "P (load through the attachment)", color="#9A5B00", fontsize=7.2)
    for sx in (1, -1):
        axa.add_patch(Circle((sx * x_toe, t + 0.3), 3.2, fill=False, ec="white", lw=1.2))
    axa.annotate("weld toe:\nsharp notch +\nresidual stress ≈ yield", xy=(x_toe + 2, t + 2), xytext=(40, 40), fontsize=7.2,
                 arrowprops=dict(arrowstyle="-|>", color=TXT, lw=0.8))
    axa.text(-98, -12, "max. principal stress, Δσ$_{nom}$ = 100 MPa at the toe section (beam theory)", fontsize=6.6, color=GRAY)
    cb = fig.colorbar(m, cax=cax, ticks=[0, 100, 200])
    cb.ax.tick_params(labelsize=6.5, length=2); cb.outline.set_visible(False)
    cax.set_title("MPa", fontsize=6.5, pad=2)
    panel_label(axa, "(a) fillet-welded attachment, plate in bending", x=0.0, y=0.98)
    # (b) surface stress + extrapolation
    sd, ss = w["bending_surf_d"], w["bending_surf_sxx"]
    keep = sd <= 52
    axb.plot(sd[keep], ss[keep], color=TXT, lw=2.0, label="FE surface stress")
    grad = (bm["s15"] - bm["s05"]) / t
    xl_ = np.linspace(0, 52, 50)
    axb.plot(xl_, bm["hs_dnv"] + grad * xl_, color=GREEN, lw=1.4, ls="--", label="linear structural part")
    axb.fill_between(sd[keep], bm["hs_dnv"] + grad * sd[keep], ss[keep], where=ss[keep] > bm["hs_dnv"] + grad * sd[keep],
                     color=RED, alpha=0.18, lw=0)
    axb.text(2.0, 190, "nonlinear notch peak\n(local geometry)", color=RED, fontsize=7)
    for xx, yy, lab in [(0.5 * t, bm["s05"], "0.5t"), (1.5 * t, bm["s15"], "1.5t")]:
        axb.plot([xx], [yy], "o", color=ORANGE, ms=5.5, zorder=5)
        axb.text(xx, yy + 12, lab, color="#9A5B00", fontsize=7.5, ha="center")
    axb.plot([0, 1.5 * t], [bm["hs_dnv"], bm["s15"]], color=ORANGE, lw=1.2, ls=":")
    axb.plot([0], [bm["hs_dnv"]], "*", color=ORANGE, ms=12, zorder=6, clip_on=False)
    axb.annotate(r"$\sigma_{hs}=%.0f$ MPa" % bm["hs_dnv"], xy=(0, bm["hs_dnv"]), xytext=(9, 45), fontsize=8, color="#9A5B00",
                 arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=0.8))
    axb.set_xlim(0, 52); axb.set_ylim(0, 290)
    axb.set_xlabel("distance from the weld toe [mm]  (t = 20 mm)"); axb.set_ylabel(r"surface stress $\sigma_{xx}$ [MPa]")
    axb.legend(loc="upper right", fontsize=6.8)
    panel_label(axb, "(b) hot-spot: read at 0.5t and 1.5t, extrapolate")
    # (c) notch zoom
    m2 = field(axc, nodes, elems, s1, -20, 280, STRESS_CMAP, mesh=True, lw=0.12, alpha=0.35)
    axc.set_xlim(9.0, 19.0); axc.set_ylim(16.5, 24.0)
    clean(axc)
    th = np.linspace(0, 2 * np.pi, 200)
    axc.plot(cx + rr * np.cos(th), cy + rr * np.sin(th), color=TXT, lw=0.9, ls="--")
    axc.annotate("", xy=(cx + rr * 0.707, cy + rr * 0.707), xytext=(cx, cy), arrowprops=dict(arrowstyle="-|>", color=TXT, lw=0.9))
    axc.plot([cx], [cy], "o", color=TXT, ms=2)
    axc.text(cx + 0.85, cy + 0.85, r"fictitious radius $r_{ref}$ = 1 mm", color=TXT, fontsize=7.5)
    kn = int(w["bending_k_notch"])
    axc.plot(*nodes[kn], "*", color="white", ms=10, mec=TXT, mew=0.4)
    axc.annotate(r"peak $\sigma_{notch}=%.0f$ MPa" % bm["s_notch"], xy=nodes[kn], xytext=(14.3, 17.4), fontsize=8, color=TXT,
                 fontweight="bold", bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85),
                 arrowprops=dict(arrowstyle="-|>", color=TXT, lw=0.8))
    panel_label(axc, "(c) effective notch stress (toe rounded, r = 1 mm)", x=0.0, y=1.0)
    # (d) lives
    lives = [("nominal\nFAT 80", 2e6 * (80 / 100) ** 3, BLUE), ("hot spot\nDNV D", bm["lives"]["hotspot_DNV_D"], GREEN),
             ("notch\nFAT 225", bm["lives"]["notch_FAT225"], RED)]
    for k, (lab, Nl, col) in enumerate(lives):
        axd.barh(2 - k, Nl / 1e6, color=col, height=0.6)
        axd.text(Nl / 1e6 + 0.03, 2 - k, f"{Nl/1e6:.2f} M", va="center", fontsize=7.5, color=col, fontweight="bold")
    axd.set_yticks([2, 1, 0]); axd.set_yticklabels([l[0] for l in lives], fontsize=7)
    axd.set_xlim(0, 2.0); axd.set_xlabel("predicted life [million cycles]", fontsize=7.5)
    panel_label(axd, "(d) three routes agree", x=-0.35)
    save(fig, "fig04_weld")


if __name__ == "__main__":
    fig3()
    fig4()
