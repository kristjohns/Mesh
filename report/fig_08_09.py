from figstyle import *
from fem.fatigue import coffin_manson_life
from matplotlib.colors import Normalize

CASES = [("hcf", "1 · ELASTIC (HCF)", C_EL, 9), ("shake", "2 · ELASTIC SHAKEDOWN", C_SD, 19),
         ("lcf", "3 · ALTERNATING PLASTICITY", C_AP, 9), ("ratchet_m", "4 · RATCHETING", C_RT, 19)]


# ----------------------------------------------------------------------------- Figure 8: four regimes
def fig8():
    fig = plt.figure(figsize=(TEXTWIDTH, 5.55))
    W = 0.245
    xs = [0.005 + k * 0.25 for k in range(4)]
    verdict = {}
    for k, (case, title, col, jpk) in enumerate(CASES):
        d = load(f"plate_{case}.npz")
        x0 = xs[k]
        # row 1: von Mises at peak of last cycle + plastic zone contour
        ax1 = fig.add_axes([x0, 0.648, W, 0.29])
        idx = 120 + jpk
        P, Es, UX, UY = mirrored(d["nodes"], d["elems"], d["F_ux"][idx], d["F_uy"][idx])
        m = field(ax1, P, Es, np.tile(d["F_vm"][idx], 4), 0, 400, STRESS_CMAP)
        pe = np.tile(d["F_peeq"][idx], 4)
        if pe.max() > 1e-4:
            tris = Es[:, Q9_TRIS].reshape(-1, 3)
            tri = Triangulation(P[:, 0], P[:, 1], tris)
            ax1.tricontour(tri, pe, levels=[1e-4], colors="white", linewidths=0.9)
        ax1.set_xlim(-40, 40); ax1.set_ylim(-34, 34)
        clean(ax1)
        ax1.text(0.5, 1.13, title, transform=ax1.transAxes, ha="center", fontsize=7.6, fontweight="bold", color=col)
        load_txt = {"hcf": "S = ±70 MPa", "shake": "S = 0 → 140 MPa", "lcf": "S = ±180 MPa", "ratchet_m": "S = 0 → 285 MPa"}[case]
        ax1.text(0.5, 1.02, load_txt, transform=ax1.transAxes, ha="center", fontsize=7, color=TXT)
        # row 2: notch-root loops (all cycles, darker = later)
        ax2 = fig.add_axes([x0 + 0.045, 0.355, W - 0.06, 0.225])
        e, s, cyc = d["T_root_eyy"] * 100, d["T_root_syy"], d["T_cycle"]
        nc = cyc.max()
        e = np.r_[0, e]; s = np.r_[0, s]; cyc = np.r_[1, cyc]
        for c in range(1, nc + 1):
            mm = cyc == c
            i0 = np.nonzero(mm)[0][0]
            sl = slice(max(i0 - 1, 0), np.nonzero(mm)[0][-1] + 1)
            shade = 0.25 + 0.75 * c / nc
            ax2.plot(e[sl], s[sl], color=col, lw=0.9 if c < nc else 1.8, alpha=shade)
        ax2.axhline(0, color=LGRAY, lw=0.5, zorder=0); ax2.axvline(0, color=LGRAY, lw=0.5, zorder=0)
        ax2.set_ylim(-430, 430)
        ax2.tick_params(labelsize=6.3)
        ax2.set_xlabel("notch strain [%]", fontsize=7, labelpad=1)
        if k == 0:
            ax2.set_ylabel("notch stress [MPa]", fontsize=7)
        # row 3: PEEQ vs cycles
        ax3 = fig.add_axes([x0 + 0.045, 0.125, W - 0.06, 0.15])
        tc = np.r_[0, d["T_tc"]]
        pe_t = np.r_[0, d["T_root_peeq"] * 100]
        ax3.plot(tc, pe_t, color=col, lw=1.8)
        ax3.set_xlim(0, nc)
        top = max(pe_t.max() * 1.25, 0.12)
        ax3.set_ylim(0, top)
        ax3.tick_params(labelsize=6.3)
        ax3.set_xlabel("cycle", fontsize=7, labelpad=1)
        if k == 0:
            ax3.set_ylabel("PEEQ [%]", fontsize=7)
        # verdict
        last = d["T_cycle"] == nc
        ea = 0.5 * (d["T_root_eyy"][last].max() - d["T_root_eyy"][last].min())
        if case == "hcf":
            v = "elastic every cycle\nN ≈ 5.6 million"
            ax3.text(0.5, 0.5, "PEEQ = 0", transform=ax3.transAxes, ha="center", fontsize=7.5, color=col, fontweight="bold")
        elif case == "shake":
            v = "yields once, then elastic\nlocal σm = +115 MPa → N ≈ 0.6–1.6 M"
            ax3.text(0.5, 0.55, "one step, then flat", transform=ax3.transAxes, ha="center", fontsize=7, color=col)
        elif case == "lcf":
            v = f"closed loop, ε$_a$ = {ea*100:.2f} %\nN ≈ 4 100 cycles"
            ax3.text(0.05, 0.75, "+0.82 % / cycle", transform=ax3.transAxes, fontsize=7, color="#9A5B00")
        else:
            v = "loops walk to the right\nstrain drifts → ductility exhaustion"
            ax3.text(0.05, 0.75, "+0.38 % / cycle", transform=ax3.transAxes, fontsize=7, color=col)
        fig.text(x0 + W / 2, 0.005, v, ha="center", va="bottom", fontsize=7, color=col, fontweight="bold")
    cax = fig.add_axes([0.30, 0.612, 0.40, 0.011])
    cb = fig.colorbar(m, cax=cax, orientation="horizontal", ticks=[0, 100, 200, 300, 400])
    cb.ax.tick_params(labelsize=6.3, length=2); cb.outline.set_visible(False)
    cax.text(-0.02, 0.5, "von Mises at peak load [MPa]", transform=cax.transAxes, ha="right", va="center", fontsize=6.8)
    cax.text(1.02, 0.5, "white line: plastic zone", transform=cax.transAxes, ha="left", va="center", fontsize=6.8)
    save(fig, "fig08_regimes")


# ----------------------------------------------------------------------------- Figure 9: PEEQ vs strain
def fig9():
    d = load("plate_lcf.npz")
    m = d["T_cycle"] <= 4
    tc = np.r_[0, d["T_tc"][m]]
    eto = np.r_[0, d["T_root_eyy"][m] * 100]
    epl = np.r_[0, d["T_root_epyy"][m] * 100]
    pe = np.r_[0, d["T_root_peeq"][m] * 100]
    fig, ax = plt.subplots(figsize=(3.35, 2.1))
    ax.plot(tc, eto, color=BLUE, lw=1.4, label=r"total strain $\varepsilon_{yy}$")
    ax.plot(tc, epl, color=ORANGE, lw=1.4, label=r"plastic strain $\varepsilon_{p,yy}$")
    ax.plot(tc, pe, color=PINK, lw=2.4, label="PEEQ (accumulated)")
    ax.axhspan(-0.383, 0.383, color=BLUE, alpha=0.07, lw=0)
    ax.text(3.95, -0.6, "strain only oscillates: ±0.38 %", color=BLUE, fontsize=6.8, ha="right", va="bottom")
    i3 = np.searchsorted(tc, 3.0)
    ax.annotate("PEEQ: +0.82 % every cycle\n(= 2 × plastic strain range)", xy=(2.45, pe[np.searchsorted(tc, 2.45)]), xytext=(2.0, 0.62), fontsize=7.0,
                color=PINK, arrowprops=dict(arrowstyle="-|>", color=PINK, lw=0.8))
    ax.set_xlim(0, 4); ax.set_ylim(-0.65, 3.5)
    ax.set_xlabel("cycles (case 3, notch root)"); ax.set_ylabel("strain [%]")
    ax.legend(loc="upper left", fontsize=6.6, bbox_to_anchor=(0.0, 1.0))
    save(fig, "fig09_peeq")


if __name__ == "__main__":
    fig8()
    fig9()
