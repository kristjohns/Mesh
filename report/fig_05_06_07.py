from figstyle import *
from fem.fatigue import coffin_manson_life, neuber, glinka


def rainflow_idx(x):
    x = np.asarray(x, float)
    dx = np.diff(x)
    tp = [0] + [k + 1 for k in range(len(dx) - 1) if dx[k] * dx[k + 1] < 0] + [len(x) - 1]
    stack, out = [], []
    for p in tp:
        stack.append(p)
        while len(stack) >= 3:
            X = abs(x[stack[-1]] - x[stack[-2]]); Y = abs(x[stack[-2]] - x[stack[-3]])
            if X < Y:
                break
            if len(stack) == 3:
                out.append((stack[0], stack[1], Y, 0.5)); stack.pop(0)
            else:
                out.append((stack[-3], stack[-2], Y, 1.0))
                last = stack.pop(); stack.pop(); stack.pop(); stack.append(last)
    for k in range(len(stack) - 1):
        out.append((stack[k], stack[k + 1], abs(x[stack[k + 1]] - x[stack[k]]), 0.5))
    return out


# ----------------------------------------------------------------------------- Figure 5: rainflow + Miner
def fig5():
    U = load("uniaxial_studies.npz")
    x = U["va_x"] * 100           # strain [%]
    cyc = rainflow_idx(x)
    fig = plt.figure(figsize=(TEXTWIDTH, 2.05))
    axa = fig.add_axes([0.06, 0.2, 0.50, 0.68])
    axb = fig.add_axes([0.66, 0.2, 0.33, 0.68])
    axa.plot(x, color=GRAY, lw=0.9)
    full = sorted([c for c in cyc if c[3] == 1.0], key=lambda c: -c[2])
    cols = [RED, ORANGE, VIOLET, GREEN]
    for k, (i, j, r, cnt) in enumerate(full[:4]):
        col = cols[k]
        axa.plot([i, j], [x[i], x[j]], "o", color=col, ms=3.5, zorder=5)
        axa.plot([i, j], [x[i], x[i]], color=col, lw=0.8, ls=":")
        axa.annotate("", xy=(j, x[j]), xytext=(j, x[i]), arrowprops=dict(arrowstyle="<|-|>", color=col, lw=1.1, mutation_scale=7))
    axa.text(5, 0.43, "rainflow pairs peaks and valleys into closed cycles (the 4 largest are marked)", fontsize=7, color=TXT, va="top")
    axa.set_xlim(0, len(x)); axa.set_ylim(-0.3, 0.45)
    axa.set_xlabel("time (one load block)"); axa.set_ylabel(r"notch strain $\varepsilon$ [%]")
    panel_label(axa, "(a) an irregular history at a notch")
    # damage per range bin
    ranges = np.array([c[2] for c in cyc]); counts = np.array([c[3] for c in cyc])
    N = np.array([coffin_manson_life(r / 200.0, E, SF, B, EF, C) for r in ranges])
    dmg = counts / N
    bins = np.linspace(0, ranges.max() * 1.0001, 6)
    k = np.digitize(ranges, bins) - 1
    cshare = np.array([counts[k == b].sum() for b in range(5)]) / counts.sum() * 100
    dshare = np.array([dmg[k == b].sum() for b in range(5)]) / dmg.sum() * 100
    xb = np.arange(5)
    axb.bar(xb - 0.19, cshare, width=0.38, color=LGRAY, label="share of cycles")
    axb.bar(xb + 0.19, dshare, width=0.38, color=RED, label="share of damage")
    labs = [f"{bins[b]:.2f}–{bins[b+1]:.2f}" for b in range(5)]
    axb.set_xticks(xb); axb.set_xticklabels(labs, fontsize=6.2, rotation=20)
    axb.set_xlabel(r"strain range $\Delta\varepsilon$ [%]")
    axb.set_ylabel("%")
    axb.legend(loc="upper left", fontsize=6.8)
    D = dmg.sum()
    axb.text(0.03, 0.72, r"$D_{block}=\sum n_i/N_i=%.1f\times10^{-4}$" % (D * 1e4) + f"\n→ failure after ≈ {1/D:,.0f} blocks",
             transform=axb.transAxes, ha="left", va="top", fontsize=6.9)
    panel_label(axb, "(b) big cycles dominate the damage")
    save(fig, "fig05_rainflow")
    return D


# ----------------------------------------------------------------------------- Figure 6: LCF notch analysis
def fig6():
    U = load("uniaxial_studies.npz")
    fig = plt.figure(figsize=(TEXTWIDTH, 2.45))
    axa = fig.add_axes([0.06, 0.17, 0.27, 0.71])
    axb = fig.add_axes([0.40, 0.17, 0.27, 0.71])
    axc = fig.add_axes([0.745, 0.17, 0.25, 0.71])
    n1 = 320
    tips = []
    for key, col, lab in [("loop_20", BLUE, "±0.2 %"), ("loop_40", GREEN, "±0.4 %"), ("loop_80", ORANGE, "±0.8 %")]:
        e, s = U[f"{key}_eps"][-n1 - 1:] * 100, U[f"{key}_sig"][-n1 - 1:]
        axa.plot(e, s, color=col, lw=1.4)
        k = np.argmax(e); tips.append((e[k], s[k]))
        axa.text(e[k] + 0.03, s[k] - 60, lab, color=col, fontsize=6.6, fontweight="bold")
    ss = np.linspace(0, 405, 200)
    axa.plot(ro_eps(ss) * 100, ss, color=TXT, lw=2.2, label="cyclic curve")
    axa.plot([t[0] for t in tips], [t[1] for t in tips], "o", color=TXT, ms=4, zorder=6)
    e8, s8 = U["loop_80_eps"][-n1 - 1:] * 100, U["loop_80_sig"][-n1 - 1:]
    kmin = np.argmin(e8)
    ds = np.linspace(0, 810, 200)
    axa.plot(e8[kmin] + (ds / E + 2 * (ds / (2 * KP)) ** (1 / NP)) * 100, s8[kmin] + ds, color=PINK, lw=1.3, ls="--",
             label="Masing: 2 × cyclic curve")
    axa.axhline(0, color=LGRAY, lw=0.6, zorder=0); axa.axvline(0, color=LGRAY, lw=0.6, zorder=0)
    axa.set_xlim(-0.9, 0.9); axa.set_ylim(-480, 520)
    axa.set_xlabel(r"strain [%]"); axa.set_ylabel(r"stress [MPa]")
    axa.legend(loc="lower right", fontsize=6.0, handlelength=1.4)
    panel_label(axa, "(a) stable loops → cyclic curve")
    # (b) Neuber / Glinka / FE
    sel = KT * 180.0
    sN, eN = neuber(KT, 180.0, E, KP, NP)
    sG, eG = glinka(KT, 180.0, E, KP, NP)
    d = load("plate_lcf.npz")
    last = d["T_cycle"] == d["T_cycle"].max()
    eF = 0.5 * (d["T_root_eyy"][last].max() - d["T_root_eyy"][last].min())
    sF = 0.5 * (d["T_root_syy"][last].max() - d["T_root_syy"][last].min())
    ss = np.linspace(0, 470, 200)
    axb.fill([0, sel / E * 100, sel / E * 100], [0, sel, 0], color=BLUE, alpha=0.12, lw=0)
    sg = np.linspace(0, sG, 100)
    axb.fill(np.r_[0, ro_eps(sg) * 100, eG * 100], np.r_[0, sg, 0], color=GREEN, alpha=0.18, lw=0)
    axb.plot(ro_eps(ss) * 100, ss, color=TXT, lw=2, label="cyclic curve")
    axb.plot([0, sel / E * 100], [0, sel], color=BLUE, lw=1.4)
    axb.plot([sel / E * 100], [sel], "o", color=BLUE, ms=4.5)
    axb.text(sel / E * 100 - 0.01, sel + 8, r"elastic: $K_tS_a$ = 585", color=BLUE, fontsize=7, ha="right", va="bottom")
    ee = np.linspace(0.25, 0.6, 100)
    axb.plot(ee, sel ** 2 / E / (ee / 100), color=ORANGE, lw=1.6, label=r"Neuber: $\sigma\varepsilon=(K_tS)^2/E$")
    for (ex, sx, col, lab, dx, dy) in [(eN, sN, ORANGE, "Neuber\n0.431 %", 0.075, 25), (eF, sF, RED, "FE\n0.383 %", 0.0, -95),
                                       (eG, sG, GREEN, "Glinka\n0.321 %", -0.07, 25)]:
        axb.plot([ex * 100], [sx], "o", color=col, ms=6, zorder=6, mec="white", mew=0.6)
        axb.text(ex * 100 + dx, sx + dy, lab, color=col, fontsize=6.8, ha="center", fontweight="bold")
    axb.text(0.21, 175, "Glinka: equal\nenergy areas", color="#1E7A3A", fontsize=6.4, ha="center")
    axb.set_xlim(0, 0.6); axb.set_ylim(0, 650)
    axb.set_xlabel(r"strain amplitude $\varepsilon_a$ [%]"); axb.set_ylabel(r"stress amplitude $\sigma_a$ [MPa]")
    axb.legend(loc="lower right", fontsize=6.2)
    panel_label(axb, "(b) notch strain: 3 estimates")
    # (c) lives
    Nn = np.logspace(1, 7, 200)
    axc.loglog(Nn, strain_life(Nn) * 100, color=TXT, lw=2)
    for ex, col, lab in [(eG, GREEN, "Glinka"), (eF, RED, "FE"), (eN, ORANGE, "Neuber")]:
        Nl = coffin_manson_life(ex, E, SF, B, EF, C)
        axc.plot([Nl], [ex * 100], "o", color=col, ms=6, zorder=6, mec="white", mew=0.6)
        axc.plot([Nl, Nl], [0.08, ex * 100], color=col, lw=0.9, ls=":")
        axc.text(Nl * 1.15, ex * 100 * 1.04, f"{lab}: {Nl:,.0f}", color=col, fontsize=7, fontweight="bold")
    axc.set_xlim(1e2, 1e5); axc.set_ylim(0.15, 1.0)
    axc.set_xlabel(r"cycles to failure $N_f$"); axc.set_ylabel(r"$\varepsilon_a$ [%]")
    axc.text(1.3e2, 0.18, "±13 % in strain → ×2.3 in life", fontsize=6.8, color=GRAY)
    panel_label(axc, "(c) → life")
    from matplotlib.ticker import NullFormatter, FixedLocator
    axc.yaxis.set_major_locator(FixedLocator([0.2, 0.3, 0.5, 1.0])); axc.set_yticklabels(["0.2", "0.3", "0.5", "1.0"])
    axc.yaxis.set_minor_formatter(NullFormatter())
    save(fig, "fig06_lcf")
    return eN, eG, eF


# ----------------------------------------------------------------------------- Figure 7: FE model
def fig7():
    d = load("plate_lcf.npz")
    nodes, elems = d["nodes"], d["elems"]
    fig = plt.figure(figsize=(TEXTWIDTH, 2.35))
    axa = fig.add_axes([0.0, 0.04, 0.17, 0.86])
    axb = fig.add_axes([0.19, 0.08, 0.22, 0.80])
    axc = fig.add_axes([0.49, 0.18, 0.22, 0.70])
    axd = fig.add_axes([0.83, 0.10, 0.165, 0.80])
    segs = [nodes[e[Q9_OUTLINE]] for e in elems]
    for ax, lw in [(axa, 0.2), (axb, 0.35)]:
        ax.add_collection(LineCollection(segs, colors="#3B4A6B", linewidths=lw))
        ax.set_aspect("equal"); clean(ax)
    axa.set_xlim(-8, 46); axa.set_ylim(-8, 112)
    for y in np.linspace(14, 96, 6):
        axa.plot([-2.5], [y], marker=">", color=BLUE, ms=4)
    for x in np.linspace(14, 38, 4):
        axa.plot([x], [-2.5], marker="^", color=BLUE, ms=4)
    for x in np.linspace(4, 36, 5):
        axa.annotate("", xy=(x, 110), xytext=(x, 101), arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=1))
    axa.text(-6, 55, "symmetry", rotation=90, color=BLUE, fontsize=6.8, va="center", ha="right")
    axa.add_patch(plt.Rectangle((0, 0), 16, 14, fill=False, ec=PINK, lw=1))
    panel_label(axa, "(a) quarter model", x=0.0, y=1.0)
    axb.set_xlim(0, 16); axb.set_ylim(0, 14)
    th = np.linspace(0, np.pi / 2, 50)
    axb.plot(10 * np.cos(th), 10 * np.sin(th), color=PINK, lw=1.2)
    axb.text(8.0, 12.6, "1152 Q9 elements\n4761 nodes · plane stress", fontsize=6.8, ha="center", va="top",
             bbox=dict(fc="white", ec="none", alpha=0.85, pad=1.5))
    panel_label(axb, "(b) graded mesh at the hole", x=0.0, y=1.0)
    for sp in axb.spines.values():
        sp.set_visible(True); sp.set_color(PINK); sp.set_linewidth(1)
    # (c) material
    from fem.material import chaboche_cyclic_curve
    ep = np.logspace(-5, np.log10(0.02), 200)
    axc.semilogx(ep, 596 * ep ** 0.076, color=TXT, lw=3.2, alpha=0.35, label="target: cyclic curve")
    axc.semilogx(ep, chaboche_cyclic_curve(ep, 250, [485000, 42400, 6840], [8000, 800, 80]), color=ORANGE, lw=1.5,
                 label="Chaboche, 3 back-stresses")
    axc.set_xlabel(r"plastic strain amplitude $\varepsilon_{pa}$"); axc.set_ylabel(r"$\sigma_a$ [MPa]")
    axc.legend(loc="upper left", fontsize=6.4)
    axc.text(1.5e-2, 262, r"$\sigma_0$ = 250 MPa" + "\n(cyclic proportional limit)", fontsize=6.2, color=GRAY, ha="right")
    panel_label(axc, "(c) S355-type steel, calibrated")
    # (d) load histories
    t = np.linspace(0, 3, 600)
    tri = lambda t: 2 * np.abs((t + 0.25) % 1 - 0.5) * 2 - 1   # -1..1 triangle starting at 0
    cases = [("1: ±70", 70 * np.sin(2 * np.pi * t), C_EL),
             ("2: 0→140", 70 - 70 * np.cos(2 * np.pi * t), C_SD),
             ("3: ±180", 180 * np.sin(2 * np.pi * t), C_AP),
             ("4: 0→285", 142.5 - 142.5 * np.cos(2 * np.pi * t), C_RT)]
    for k, (lab, y, col) in enumerate(cases):
        off = -k * 400
        axd.plot(t, y + off, color=col, lw=1.5)
        axd.axhline(off, color=LGRAY, lw=0.5, zorder=0)
        axd.text(-0.12, off, lab, color=col, fontsize=6.8, fontweight="bold", ha="right", va="center")
    axd.set_xlim(0, 3.05); axd.set_yticks([]); axd.set_xlabel("load cycles")
    axd.spines["left"].set_visible(False)
    panel_label(axd, "(d) load cases", x=-0.35)
    save(fig, "fig07_model")


if __name__ == "__main__":
    D = fig5()
    print("D per block", D)
    print(fig6())
    fig7()
