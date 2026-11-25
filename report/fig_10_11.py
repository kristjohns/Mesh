from figstyle import *
from matplotlib.colors import ListedColormap
from matplotlib.patches import FancyArrowPatch


# ----------------------------------------------------------------------------- Figure 10: shakedown + Bree
def fig10():
    fig = plt.figure(figsize=(TEXTWIDTH, 2.55))
    axa = fig.add_axes([0.01, 0.13, 0.26, 0.75])
    axb = fig.add_axes([0.355, 0.15, 0.30, 0.73])
    # (a) Melan
    t = np.linspace(0, 2 * np.pi, 300)
    a, b = np.sqrt(2.0), np.sqrt(2.0 / 3.0)
    ex = (a * np.cos(t) - b * np.sin(t)) / np.sqrt(2); ey = (a * np.cos(t) + b * np.sin(t)) / np.sqrt(2)
    axa.fill(ex, ey, color=BLUE, alpha=0.07, lw=0)
    axa.plot(ex, ey, color=TXT, lw=1.3)
    axa.text(0.55, 1.28, "yield surface", fontsize=6.8, color=TXT)
    A = np.array([1.45, 0.25])
    axa.plot([0, A[0]], [0, A[1]], color=ORANGE, lw=2.6, solid_capstyle="round")
    axa.text(1.0, -0.12, "elastic stress\npath (cycled)", fontsize=6.6, color="#9A5B00", va="top")
    rho = np.array([-0.62, -0.05])
    axa.plot([rho[0], A[0] + rho[0]], [rho[1], A[1] + rho[1]], color=GREEN, lw=2.6, solid_capstyle="round")
    axa.add_patch(FancyArrowPatch(tuple(A), tuple(A + rho), arrowstyle="-|>", mutation_scale=8, color=PINK, lw=1.2))
    axa.text(A[0] - 0.25, A[1] + 0.12, r"$+\rho$", color=PINK, fontsize=9)
    axa.text(-1.55, 0.95, "with residual stress ρ\nit fits inside\n→ elastic shakedown", fontsize=6.6, color="#1E7A3A")
    L = np.array([2.3, 0.4])
    s0 = np.array([-0.75, -0.95])
    axa.plot([s0[0], s0[0] + L[0]], [s0[1], s0[1] + L[1]], color=RED, lw=2.2, ls=(0, (3, 1.5)))
    axa.text(-1.55, -1.58, "range > 2σ$_y$: never fits\n→ cyclic plasticity", fontsize=6.6, color=RED, va="bottom")
    axa.set_xlim(-1.6, 1.6); axa.set_ylim(-1.6, 1.6); axa.set_aspect("equal")
    axa.axhline(0, color=LGRAY, lw=0.5, zorder=0); axa.axvline(0, color=LGRAY, lw=0.5, zorder=0)
    axa.set_xticks([]); axa.set_yticks([])
    axa.set_xlabel(r"$\sigma_1/\sigma_y$", labelpad=2); axa.set_ylabel(r"$\sigma_2/\sigma_y$", labelpad=2)
    panel_label(axa, "(a) Melan's shakedown theorem", x=0.0)
    # (b) Bree map
    d = load("bree_map.npz")
    cls = d["cls"]
    cmap = ListedColormap([BLUE, GREEN, ORANGE, RED])
    axb.imshow(cls, origin="lower", extent=[0, 1, 0, 4], aspect="auto", cmap=cmap, vmin=-0.5, vmax=3.5, alpha=0.78,
               interpolation="nearest")
    xx = np.linspace(0, 1, 50)
    axb.plot(xx, 1 - xx, color=TXT, lw=1.1)
    xa = np.linspace(0.5, 1.0, 40); axb.plot(xa, 4 * (1 - xa), color=TXT, lw=1.1)
    yb = np.linspace(2.0, 4.0, 40); axb.plot(1 / yb, yb, color=TXT, lw=1.1)
    axb.plot([0, 0.5], [2, 2], color=TXT, lw=1.1)
    for (x, y, s_) in [(0.2, 0.35, "E"), (0.33, 1.25, "S"), (0.12, 3.2, "P"), (0.83, 1.45, "R$_1$"), (0.62, 3.2, "R$_2$")]:
        axb.text(x, y, s_, fontsize=11, fontweight="bold", color="white", ha="center", va="center")
    axb.set_xlim(0, 1); axb.set_ylim(0, 4)
    axb.set_xlabel(r"primary  $X=\sigma_p/\sigma_y$"); axb.set_ylabel(r"secondary  $Y=\sigma_t/\sigma_y$")
    axb.text(0.5, -0.32, "", transform=axb.transAxes)
    panel_label(axb, "(b) Bree diagram, computed", x=0.0)
    # (c) mini loops
    reps = [("S", "S: shakedown", GREEN), ("P", "P: alternating plasticity", ORANGE), ("R1", "R$_1$: ratcheting", RED),
            ("R2", "R$_2$: ratcheting + reversed", RED)]
    y = d["y"]
    for k, (key, lab, col) in enumerate(reps):
        X, Y = d[f"h_{key}_XY"]
        axb.plot([X], [Y], "o", color="white", mec=TXT, ms=5, zorder=6)
        axb.text(X + 0.025, Y + 0.08, key.replace("1", "₁").replace("2", "₂"), fontsize=6.5, color=TXT)
        r, c = divmod(k, 2)
        ax = fig.add_axes([0.765 + c * 0.12, 0.53 - r * 0.42, 0.1, 0.33])
        sig = d[f"h_{key}_sig"][:, 0]
        eps = d[f"h_{key}_eps"] - d[f"h_{key}_lam"] * 2 * Y * y[0]
        eps = np.r_[0, eps]; sig = np.r_[X if False else sig[0] * 0 + sig[0], sig]
        ax.plot(eps, sig, color=col, lw=1.1)
        ax.axhline(0, color=LGRAY, lw=0.5, zorder=0)
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_title(lab, fontsize=6.4, color=col, pad=2)
        if k == 0:
            ax.text(-0.05, 1.32, "(c) inner-wall loops", transform=ax.transAxes, fontsize=9.5, fontweight="bold")
    save(fig, "fig10_bree")


# ----------------------------------------------------------------------------- Figure 11: ratcheting
def cyc_plastic(d):
    comps = [d["F_epxx"][-40:], d["F_epyy"][-40:], d["F_epzz"][-40:], d["F_epxy"][-40:]]
    ref = [d["EOC_epxx"][-2], d["EOC_epyy"][-2], d["EOC_epzz"][-2], d["EOC_epxy"][-2]]
    dxx, dyy, dzz, dxy = [c - r[None, :] for c, r in zip(comps, ref)]
    return np.sqrt(2.0 / 3.0 * (dxx ** 2 + dyy ** 2 + dzz ** 2 + 2 * dxy ** 2)).max(axis=0)


def fig11():
    fig = plt.figure(figsize=(TEXTWIDTH, 4.1))
    # row 1: structural ratcheting
    ax0 = fig.add_axes([0.0, 0.55, 0.13, 0.36])
    da = load("plate_tm_altpl.npz"); dr = load("plate_tm_ratchet.npz")
    P, Es = mirrored(da["nodes"], da["elems"])
    field(ax0, P, Es, np.tile(da["T_unit"], 4), 0, 1, matplotlib.colormaps["coolwarm"])
    ax0.set_xlim(-42, 42); ax0.set_ylim(-62, 62); clean(ax0)
    for x in np.linspace(-30, 30, 4):
        ax0.annotate("", xy=(x, 74), xytext=(x, 63), arrowprops=dict(arrowstyle="-|>", color=TXT, lw=0.9), annotation_clip=False)
        ax0.annotate("", xy=(x, -74), xytext=(x, -63), arrowprops=dict(arrowstyle="-|>", color=TXT, lw=0.9), annotation_clip=False)
    ax0.text(0.5, -0.17, "constant tension\n+ cyclic ΔT (hot centre)", transform=ax0.transAxes, ha="center", fontsize=6.4, va="top")
    panel_label(ax0, "(a) load", x=0.0, y=1.08)
    for k, (d, lab, col, verdict) in enumerate([(da, "(b) X = 0.25", C_AP, "elastic core\nsurvives → OK"),
                                                 (dr, "(c) X = 0.5", C_RT, "no elastic core\n→ ratchets")]):
        ax = fig.add_axes([0.17 + k * 0.17, 0.55, 0.15, 0.36])
        cp = cyc_plastic(d)
        core = np.where(cp < 1e-6, 0.0, np.clip(np.log10(cp / 1e-6) / 4.0, 0.05, 1.0))
        field(ax, P, Es, np.tile(core, 4), 0, 1, CORE_CMAP)
        ax.set_xlim(-42, 42); ax.set_ylim(-62, 62); clean(ax)
        panel_label(ax, lab, x=0.0, y=1.08)
        ax.text(0.5, -0.06, verdict, transform=ax.transAxes, ha="center", fontsize=7.2, color=col, fontweight="bold", va="top")
    fig.text(0.17, 0.455, "blue: no plastic flow during a cycle  ·  red: plastic flow every cycle", fontsize=6.4, color=GRAY, ha="left")
    ax3 = fig.add_axes([0.59, 0.585, 0.40, 0.33])
    for d, col, lab in [(da, C_AP, "X = 0.25: stops changing"), (dr, C_RT, "X = 0.5: +22.5 µm every cycle")]:
        eoc = d["T_uy_top"][d["T_end_of_cycle"]] * 1000
        pre = d["T_uy_top"][9] * 1000
        ax3.plot(np.arange(0, len(eoc) + 1), np.r_[pre, eoc], "o-", color=col, lw=1.6, ms=3, label=lab)
    ax3.set_xlabel("cycle"); ax3.set_ylabel("plate-end displacement [µm]")
    ax3.legend(loc="upper left", fontsize=6.8)
    ax3.set_xlim(0, 12)
    panel_label(ax3, "(d) ASME check: do dimensions keep changing?", x=0.0)
    # row 2: material ratcheting
    U = load("uniaxial_studies.npz")
    spec = [("prager", "(e) linear kinematic", BLUE), ("af", "(f) Armstrong–Frederick", RED), ("chaboche", "(g) Chaboche, 3 terms", ORANGE)]
    for k, (key, lab, col) in enumerate(spec):
        ax = fig.add_axes([0.07 + k * 0.33, 0.08, 0.26, 0.28])
        e, s = U[f"rat_{key}_eps"] * 100, U[f"rat_{key}_sig"]
        ax.plot(e, s, color=col, lw=0.8)
        ax.set_xlim(-0.4, 2.2); ax.set_ylim(-400, 420)
        ax.axhline(0, color=LGRAY, lw=0.5, zorder=0); ax.axvline(0, color=LGRAY, lw=0.5, zorder=0)
        ax.set_xlabel("strain [%]", fontsize=7, labelpad=1)
        if k == 0:
            ax.set_ylabel("stress [MPa]", fontsize=7)
        ax.tick_params(labelsize=6.3)
        ax.text(0.97, 0.06, f"after 15 cycles:\n{e[-1]:.2f} %", transform=ax.transAxes, ha="right", fontsize=7.2, color=col,
                fontweight="bold", bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.9), zorder=10)
        panel_label(ax, lab, x=0.0)
    fig.text(0.5, 0.405, "material ratcheting under stress control (σm = 60 MPa, σa = 300 MPa): the hardening model decides",
             ha="center", fontsize=7.4, color=TXT, fontweight="bold")
    save(fig, "fig11_ratchet")


if __name__ == "__main__":
    fig10()
    fig11()
