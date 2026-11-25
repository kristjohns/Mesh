from figstyle import *
from matplotlib.patches import FancyArrowPatch


def loop_last(case):
    d = load(f"plate_{case}.npz")
    last = d["T_cycle"] == d["T_cycle"].max()
    e, s = d["T_root_eyy"][last] * 100, d["T_root_syy"][last]
    return np.r_[e, e[:1]], np.r_[s, s[:1]]


def darrow(ax, p0, p1, color, lw=1.2, ms=8):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="<|-|>", mutation_scale=ms, color=color, lw=lw, shrinkA=0, shrinkB=0))


# ----------------------------------------------------------------------------- Figure 1
def fig1():
    fig = plt.figure(figsize=(TEXTWIDTH, 3.05))
    axa = fig.add_axes([0.065, 0.14, 0.30, 0.76])
    axb = fig.add_axes([0.45, 0.14, 0.54, 0.76])
    # (a) loop anatomy
    e, s = loop_last("lcf")
    axa.fill(e, s, color=ORANGE, alpha=0.18, lw=0)
    axa.plot(e, s, color=ORANGE, lw=2.0)
    axa.axhline(0, color=LGRAY, lw=0.8, zorder=0); axa.axvline(0, color=LGRAY, lw=0.8, zorder=0)
    emax, emin, smax, smin = e.max(), e.min(), s.max(), s.min()
    # crossings of sigma = 0 -> plastic strain range
    zc = np.nonzero(np.diff(np.sign(s)) != 0)[0]
    xz = sorted([e[k] - s[k] * (e[k + 1] - e[k]) / (s[k + 1] - s[k]) for k in zc])[:2]
    darrow(axa, (xz[0], 0), (xz[1], 0), PINK, lw=1.4)
    axa.text(0.5 * (xz[0] + xz[1]), 28, r"$\Delta\varepsilon_p = %.2f\,\%%$" % (xz[1] - xz[0]), color=PINK, ha="center", fontsize=8.5)
    darrow(axa, (emin, smin - 75), (emax, smin - 75), TXT)
    axa.text(0, smin - 70, r"$\Delta\varepsilon = %.2f\,\%%$" % (emax - emin), ha="center", va="top", fontsize=8.5)
    darrow(axa, (emax + 0.07, smin), (emax + 0.07, smax), TXT)
    axa.text(emax + 0.1, 0, r"$\Delta\sigma$" + "\n" + f"{smax - smin:.0f}\nMPa", va="center", ha="left", fontsize=8.5)
    area = 0.5 * abs(np.sum(e[:-1] * s[1:] - e[1:] * s[:-1])) / 100.0     # MPa * strain = MJ/m3
    axa.text(-0.07, -175, "area = plastic work\n" + r"$\Delta W \approx %.1f$ MJ/m$^3$" % area + "\nevery cycle", ha="center",
             fontsize=7.4, color="#9A5B00", va="center")
    axa.set_xlim(emin - 0.12, emax + 0.42)
    axa.set_ylim(smin - 160, smax + 90)
    axa.set_xlabel(r"strain $\varepsilon$ [%]")
    axa.set_ylabel(r"stress $\sigma$ [MPa]")
    axa.set_title("(a) One stabilised cycle at the notch root", loc="left", fontsize=9)
    # (b) strain-life map
    N = np.logspace(0, 9, 400)
    el = SF / E * (2 * N) ** B
    pl = EF * (2 * N) ** C
    Nt = 0.5 * (EF * E / SF) ** (1 / (B - C))
    axb.fill_between([1, Nt], 1e-4, 1, color=ORANGE, alpha=0.09, lw=0)
    axb.fill_between([Nt, 1e7], 1e-4, 1, color=BLUE, alpha=0.07, lw=0)
    axb.fill_between([1e7, 1e9], 1e-4, 1, color=VIOLET, alpha=0.08, lw=0)
    axb.loglog(N, el, color=BLUE, lw=1.6)
    m = pl > 1e-4
    axb.loglog(N[m], pl[m], color=ORANGE, lw=1.6)
    axb.loglog(N, el + pl, color=TXT, lw=2.4)
    axb.text(3e5, 0.00175, "elastic part (Basquin)", color=BLUE, fontsize=7.2, rotation=-4, ha="center")
    axb.text(2.5e4, 3.2e-4, "plastic part\n(Coffin–Manson)", color=ORANGE, fontsize=7.2, ha="left")
    axb.text(25, 0.06, "total", color=TXT, fontsize=7.6, fontweight="bold")
    et = SF / E * (2 * Nt) ** B
    axb.plot([Nt], [et], "o", color=PINK, ms=6, zorder=5)
    axb.annotate("transition " + r"$N_t\approx 3\,300$" + "\n(elastic = plastic)", (Nt, et), xytext=(2.0, 2.2e-4),
                 fontsize=7.4, color=PINK, ha="left", arrowprops=dict(arrowstyle="-|>", color=PINK, lw=0.9))
    for x, t, col in [(55, "LOW-CYCLE", ORANGE), (1.6e5, "HIGH-CYCLE", BLUE), (1.0e8, "VERY HIGH", VIOLET)]:
        axb.text(x, 0.55, t, color=col, fontweight="bold", fontsize=8.5, ha="center")
    axb.text(55, 0.33, "plastic strain dominates\n→ ductility controls", color="#9A5B00", fontsize=7, ha="center", va="top")
    axb.text(1.6e5, 0.33, "elastic strain dominates\n→ strength controls", color="#145F8F", fontsize=7, ha="center", va="top")
    axb.text(1.0e8, 0.33, "internal 'fish-eye'\ncracks", color="#5B3BA0", fontsize=7, ha="center", va="top")
    # FE cases + inset loops (same scale) connected to the case points
    for (x0, y0), case, col, Nc, ea, title in [((0.50, 0.42), "lcf", ORANGE, 4093, 0.003826, "case 3: ±180 MPa\nfat loop → 4 100 cycles"),
                                               ((0.79, 0.42), "hcf", BLUE, 5.64e6, 0.001083, "case 1: ±70 MPa\nthin line → 5.6 M cycles")]:
        axb.plot([Nc], [ea], "s", color=col, ms=5.5, mec="white", mew=0.8, zorder=6)
        ins = axb.inset_axes([x0, y0, 0.15, 0.24])
        ei, si = loop_last(case)
        ins.fill(ei, si, color=col, alpha=0.2, lw=0)
        ins.plot(ei, si, color=col, lw=1.4)
        ins.axhline(0, color=LGRAY, lw=0.5); ins.axvline(0, color=LGRAY, lw=0.5)
        ins.set_xlim(-0.45, 0.45); ins.set_ylim(-420, 420)
        ins.set_xticks([]); ins.set_yticks([])
        for sp in ins.spines.values():
            sp.set_visible(True); sp.set_color(col); sp.set_linewidth(0.8)
        ins.text(0.5, 1.04, title, transform=ins.transAxes, ha="center", fontsize=6.6, color=col, va="bottom")
        axb.annotate("", xy=(Nc, ea), xytext=(x0 + 0.075, y0), textcoords=axb.transAxes,
                     arrowprops=dict(arrowstyle="-|>", color=col, lw=0.8, shrinkB=4))
    axb.set_xlim(1, 1e9); axb.set_ylim(1e-4, 1)
    axb.set_xlabel(r"cycles to failure $N_f$")
    axb.set_ylabel(r"strain amplitude $\varepsilon_a$")
    axb.set_title("(b) Where the regimes sit on the strain–life curve", loc="left", fontsize=9)
    save(fig, "fig01_overview")


# ----------------------------------------------------------------------------- Figure 2
def fig2():
    fig = plt.figure(figsize=(TEXTWIDTH, 2.55))
    axa = fig.add_axes([0.07, 0.16, 0.40, 0.72])
    axb = fig.add_axes([0.58, 0.16, 0.41, 0.72])
    # (a) S-N curve
    ND = 2e6
    Se = SF * (2 * ND) ** B
    N = np.logspace(3, 9, 300)
    sn = np.where(N < ND, SF * (2 * N) ** B, Se)
    rng = np.random.default_rng(5)
    for lev in [470, 420, 380, 340, 300, 275]:
        N0 = 0.5 * (lev / SF) ** (1 / B)
        Ns = N0 * 10 ** rng.normal(0, 0.2, 4)
        Ns = Ns[Ns < 3e6]
        axa.plot(Ns, np.full(Ns.shape, lev), "o", color=TXT, ms=3, alpha=0.75)
    for lev in [240]:
        axa.annotate("", xy=(1.0e7, 228), xytext=(4.4e6, 228), arrowprops=dict(arrowstyle="-|>", color=GRAY, lw=0.8))
    axa.text(4.0e6, 228, "run-outs", fontsize=6.2, color=GRAY, ha="right", va="center")
    axa.loglog(N, sn, color=BLUE, lw=2.2)
    axa.loglog(N, 330 * (N / 1e3) ** -0.11, color=VIOLET, lw=1.3, ls="--")
    axa.text(1.3e4, 205, "aluminium: no limit", color=VIOLET, fontsize=6.8, ha="left", va="top", rotation=-9)
    axa.loglog([ND, 1e9], [Se * 0.62] * 2, color=ORANGE, lw=1.4, ls="--")
    axa.annotate("", xy=(2.5e8, Se * 0.64), xytext=(2.5e8, Se * 0.97), arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=1))
    axa.text(2.4e6, Se * 0.75, "corrected for surface, size,\nload, temperature, reliability", fontsize=6.3,
             color="#9A5B00", va="center")
    axa.plot([ND], [Se], "o", color=PINK, ms=5, zorder=5)
    axa.text(ND * 0.85, Se * 0.9, "knee", fontsize=7, color=PINK, ha="right", va="top")
    axa.text(1.3e3, 560, r"$\sigma_a = 952\,(2N)^{-0.089}$", fontsize=8.5, color=BLUE)
    axa.text(6e7, Se * 1.06, r"$S_e \approx %d$ MPa" % round(Se), fontsize=8, color=BLUE, ha="center")
    axa.set_xlim(1e3, 1e9); axa.set_ylim(80, 700)
    axa.set_yticks([100, 200, 300, 500]); axa.set_yticklabels(["100", "200", "300", "500"])
    from matplotlib.ticker import NullFormatter
    axa.yaxis.set_minor_formatter(NullFormatter())
    axa.set_xlabel("cycles to failure $N$"); axa.set_ylabel(r"stress amplitude $\sigma_a$ [MPa]")
    axa.set_title("(a) S–N (Wöhler) curve", loc="left", fontsize=9)
    # (b) Haigh diagram
    m = np.linspace(0, SU, 200)
    axb.fill_between(m, 0, Se * (1 - m / SU), color=BLUE, alpha=0.08, lw=0)
    axb.plot(m, Se * (1 - m / SU), color=BLUE, lw=1.8, label="Goodman (to $S_u$)")
    axb.plot(m, Se * (1 - (m / SU) ** 2), color=GREEN, lw=1.8, label="Gerber (parabola)")
    ms_ = np.linspace(0, SY, 100)
    axb.plot(ms_, Se * (1 - ms_ / SY), color=RED, lw=1.8, label="Soderberg (to $S_y$)")
    ms2 = np.linspace(0, 520, 200)
    axb.plot(ms2, 0.5 * (-ms2 + np.sqrt(ms2 ** 2 + 4 * Se ** 2)), color=ORANGE, lw=1.8, label=r"SWT: $\sqrt{\sigma_{max}\sigma_a}=S_e$")
    axb.plot([-150, 0], [Se, Se], color=BLUE, lw=1.8, ls=":")
    axb.text(-75, Se + 10, "compression:\nno benefit assumed", fontsize=6.6, color=BLUE, ha="center", va="bottom")
    pm, pa = 115.1, 227.4
    axb.plot([pm], [pa], "o", color=TXT, ms=6, zorder=6)
    axb.annotate("case 2 notch root (σm = +115, σa = 227):\nsafe by Gerber, finite life by the others",
                 (pm, pa), xytext=(150, 300), fontsize=6.6, ha="left",
                 arrowprops=dict(arrowstyle="-|>", color=TXT, lw=0.8))
    axb.text(140, 60, "infinite life\n(Goodman)", fontsize=7, color="#145F8F", ha="center")
    axb.set_xlim(-150, 530); axb.set_ylim(0, 330)
    axb.set_xlabel(r"mean stress $\sigma_m$ [MPa]"); axb.set_ylabel(r"amplitude $\sigma_a$ [MPa]")
    axb.legend(loc="upper right", bbox_to_anchor=(1.0, 0.72), fontsize=6.8)
    axb.set_title("(b) Haigh diagram: same point, different verdicts", loc="left", fontsize=9)
    save(fig, "fig02_hcf")


if __name__ == "__main__":
    fig1()
    fig2()
