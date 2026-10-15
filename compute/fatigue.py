"""Wellhead fatigue, worked through with the DNV-RP-C203 S-N method.  Writes ../video/data/fatigue.json.

Chain (one function per link):
  1. sea states      example Hs-Tp scatter diagram (3-parameter Weibull Hs, lognormal Tp | Hs)
  2. riser load      lateral force at the LMRP flex joint per sea state: JONSWAP spectrum times an
                     assumed linear transfer function (stands in for a global riser analysis)
  3. load-to-stress  global beam model (globalmodel.py: p-y soil, cement, shoulder spring calibrated
                     on the local model, template gap) gives the section moment at each hot spot as a
                     nonlinear function of the flex-joint force; SCFs from hotspot.py (FE hot-spot
                     stress) or from the C203 misalignment formula (girth weld)
  4. cycle counting  rainflow (ASTM E1049 four-point rule) on 3-hour stress histories
  5. S-N curve       C203 table values, environment, thickness correction (t / 25 mm)^k
  6. damage          Palmgren-Miner per sea state, weighted by probability -> damage per day of
                     riser-connected operation; Weibull closed form as a check
  7. design check    life / DFF against the planned connected time
"""
import json
import math
import numpy as np
from scipy.special import gamma as G, gammainc, gammaincc
from scipy.stats import lognorm
from globalmodel import Model, Soil, PWL, Gap, Z_LOAD

np.random.seed(0)
DATA = "/home/user/Mesh/video/data/"

# ------------------------------------------------------------------------------------ S-N curves
# DNV-RP-C203 (2024) S-N curves: (m1, log a1, m2, log a2, k).  In air the slope changes at 5e6 cycles
# for B1-C2 and at 1e7 for D-W3, in seawater with cathodic protection at 1e6; free corrosion has one slope.
SN_AIR = {
    "B1": (4.0, 15.117, 5, 17.222, 0.00), "B2": (4.0, 14.885, 5, 16.931, 0.00),
    "C": (3.5, 13.640, 5, 16.615, 0.05), "C1": (3.5, 13.473, 5, 16.377, 0.10),
    "C2": (3.5, 13.301, 5, 16.130, 0.15), "D": (3.0, 12.164, 5, 15.606, 0.20),
    "E": (3.0, 12.010, 5, 15.350, 0.20), "F": (3.0, 11.855, 5, 15.091, 0.25),
    "F1": (3.0, 11.699, 5, 14.832, 0.25), "F3": (3.0, 11.546, 5, 14.576, 0.25),
    "G": (3.0, 11.398, 5, 14.330, 0.25), "W1": (3.0, 11.261, 5, 14.101, 0.25),
    "W2": (3.0, 11.107, 5, 13.845, 0.25), "W3": (3.0, 10.970, 5, 13.617, 0.25),
}
SN_CP_LA1 = {"B1": 14.977, "B2": 14.745, "C": 13.431, "C1": 13.264, "C2": 13.091, "D": 11.764, "E": 11.610,
             "F": 11.455, "F1": 11.299, "F3": 11.146, "G": 10.998, "W1": 10.861, "W2": 10.707, "W3": 10.570}
SN_CP = {k: (m1, SN_CP_LA1[k], m2, la2, kk) for k, (m1, la1, m2, la2, kk) in SN_AIR.items()}
SN_FC_LA = {"B1": (12.436, 0.0), "B2": (12.262, 0.0), "C": (12.115, 0.15), "C1": (11.972, 0.15),
            "C2": (11.824, 0.15), "D": (11.687, 0.20), "E": (11.533, 0.20), "F": (11.378, 0.25),
            "F1": (11.222, 0.25), "F3": (11.068, 0.25), "G": (10.921, 0.25), "W1": (10.784, 0.25),
            "W2": (10.630, 0.25), "W3": (10.493, 0.25)}
SN_FC = {k: (3.0, la, None, None, kk) for k, (la, kk) in SN_FC_LA.items()}
T_REF = 0.025


class SN:
    def __init__(self, cls, env="cp", t=T_REF):
        tab = {"air": SN_AIR, "cp": SN_CP, "fc": SN_FC}[env]
        self.cls, self.env = cls, env
        self.m1, self.la1, self.m2, self.la2, self.k = tab[cls]
        self.tf = max(1.0, t / T_REF) ** self.k          # thickness correction on stress
        if self.m2 is not None:
            # knee: intersection of the two branches
            self.logS1 = (self.la2 - self.la1) / (self.m2 - self.m1)
            self.N1 = 10 ** (self.la1 - self.m1 * self.logS1)
        else:
            self.logS1, self.N1 = -np.inf, np.inf

    def N(self, ds):
        """cycles to failure for stress ranges ds [MPa] (before thickness correction)"""
        s = np.maximum(np.asarray(ds, float) * self.tf, 1e-9)
        ls = np.log10(s)
        if self.m2 is None:
            return 10 ** (self.la1 - self.m1 * ls)
        return np.where(ls >= self.logS1, 10 ** (self.la1 - self.m1 * ls), 10 ** (self.la2 - self.m2 * ls))

    def curve(self, n=60):
        Ns = np.logspace(3, 9, n)
        out = []
        for Nn in Ns:
            if self.m2 is None or Nn <= self.N1:
                s = 10 ** ((self.la1 - math.log10(Nn)) / self.m1)
            else:
                s = 10 ** ((self.la2 - math.log10(Nn)) / self.m2)
            out.append([float(Nn), float(s)])
        return out


# ------------------------------------------------------------------------------------ rainflow
def reversals(x):
    d = np.diff(x)
    keep = np.r_[True, d[1:] * d[:-1] < 0, True]
    idx = np.where(np.r_[True, d != 0])[0]  # drop flat repeats
    x2 = x[idx]
    d = np.diff(x2)
    keep = np.r_[True, d[1:] * d[:-1] < 0, True]
    return idx[keep], x2[keep]


def rainflow(x, trace=False):
    """ASTM E1049 rainflow counting. Returns (ranges, counts[1 or 0.5], means) and optionally the
    extraction trace [(i_a, i_b, kind)] in terms of reversal indices."""
    _, r = reversals(np.asarray(x, float))
    stack = []
    rng, cnt, mean, tr = [], [], [], []
    for i, v in enumerate(r):
        stack.append(i)
        while len(stack) >= 3:
            X = abs(r[stack[-1]] - r[stack[-2]])
            Y = abs(r[stack[-2]] - r[stack[-3]])
            if X < Y:
                break
            if len(stack) == 3:
                rng.append(Y); cnt.append(0.5); mean.append(0.5 * (r[stack[-2]] + r[stack[-3]]))
                tr.append((stack[-3], stack[-2], "half"))
                stack.pop(0)
            else:
                rng.append(Y); cnt.append(1.0); mean.append(0.5 * (r[stack[-2]] + r[stack[-3]]))
                tr.append((stack[-3], stack[-2], "full"))
                last = stack.pop()
                stack.pop()
                stack.pop()
                stack.append(last)
    for a, b in zip(stack[:-1], stack[1:]):
        rng.append(abs(r[b] - r[a])); cnt.append(0.5); mean.append(0.5 * (r[a] + r[b]))
        tr.append((a, b, "residue"))
    out = (np.array(rng), np.array(cnt), np.array(mean))
    return (out, r, tr) if trace else out


# ------------------------------------------------------------------------------------ sea states
HS_EDGES = np.arange(0.0, 13.0, 1.0)
TP_EDGES = np.arange(2.0, 22.0, 1.0)
WB = dict(alpha=1.90, beta=1.35, gamma=0.55)        # 3-parameter Weibull for Hs (scale, shape, location)


def tp_median(hs):
    return 4.5 + 2.6 * hs ** 0.6


def scatter():
    a, b, g = WB["alpha"], WB["beta"], WB["gamma"]
    cdf = lambda h: 1 - np.exp(-np.maximum((h - g) / a, 0) ** b)
    P = np.zeros((len(HS_EDGES) - 1, len(TP_EDGES) - 1))
    for i in range(len(HS_EDGES) - 1):
        h0, h1 = HS_EDGES[i], HS_EDGES[i + 1]
        ph = cdf(h1) - cdf(h0)
        hc = max(0.5 * (h0 + h1), g + 0.05)
        dist = lognorm(s=0.12, scale=tp_median(hc))
        pt = dist.cdf(TP_EDGES[1:]) - dist.cdf(TP_EDGES[:-1])
        P[i] = ph * pt / pt.sum()
    return P / P.sum()


def jonswap(f, hs, tp):
    fp = 1 / tp
    r = tp / math.sqrt(hs)
    gam = 5.0 if r <= 3.6 else (math.exp(5.75 - 1.15 * r) if r < 5 else 1.0)
    w, wp = 2 * np.pi * f, 2 * np.pi * fp
    sig = np.where(w <= wp, 0.07, 0.09)
    A = 1 - 0.287 * math.log(gam)
    Sw = A * 5 / 16 * hs ** 2 * wp ** 4 * np.where(w > 0, w, 1) ** -5 * np.exp(-1.25 * (wp / np.where(w > 0, w, 1)) ** 4) \
        * gam ** np.exp(-0.5 * ((w - wp) / (sig * wp)) ** 2)
    Sw = np.where(w > 0, Sw, 0)
    return Sw * 2 * np.pi      # per Hz


# assumed transfer function: flex-joint lateral force per metre of wave amplitude [N/m]
G0, T0, SPREAD = 21.0e3, 9.0, 0.42


def G_riser(f):
    T = 1 / np.maximum(f, 1e-6)
    return G0 * np.exp(-0.5 * (np.log(T / T0) / SPREAD) ** 2)


DT = 0.25
TSIM = 3 * 3600.0


def force_series(hs, tp, seed, T=TSIM):
    n = int(T / DT)
    f = np.fft.rfftfreq(n, DT)
    df = f[1] - f[0]
    S = jonswap(f, hs, tp)
    rs = np.random.default_rng(seed)
    ph = rs.uniform(0, 2 * np.pi, len(f))
    amp_eta = np.sqrt(2 * S * df)
    Xe = amp_eta * np.exp(1j * ph) * n / 2
    eta = np.fft.irfft(Xe, n)
    F = np.fft.irfft(Xe * G_riser(f), n)
    return np.arange(n) * DT, eta, F


# ------------------------------------------------------------------------------------ global model
def shoulder_law():
    loc = json.load(open(DATA + "wellhead_local.json"))
    rot = np.array([0.0] + [r["rot_rel"] for r in loc["results"][1:]])
    Mloc = np.array([r["M"] for r in loc["results"]])
    return PWL(np.r_[rot, rot[-1] * 3], np.r_[Mloc, Mloc[-1] + (Mloc[-1] - Mloc[-2]) / (rot[-1] - rot[-2]) * rot[-1] * 2])


Z_GIRTH = -3.0
HOTSPOTS = [
    dict(id="hp", name="HP housing weld", sub="HP housing to 20 in surface casing", z=1.2, string="inner",
         D=0.508, t=0.015875, method="hot spot (FE)", cls="D", env="cp"),
    dict(id="lp", name="Conductor housing weld", sub="conductor housing to 36 in conductor", z=0.8, string="outer",
         D=0.9144, t=0.0381, method="hot spot (FE)", cls="D", env="cp"),
    dict(id="cg", name="Conductor girth weld", sub="3 m below the mudline", z=Z_GIRTH, string="outer",
         D=0.9144, t=0.0381, method="nominal + SCF", cls="D", env="cp"),
]
DELTA_M = 0.006   # girth weld misalignment (hi-lo) [m]
L_WELD = 0.040    # width of the girth weld cap at the surface [m]


def girth_scf(dm, t=0.0381, D=0.9144, L=L_WELD):
    """C203 eq. (3.9), butt weld in a tubular, equal thickness; delta0 = 0.05t is in the S-N data (Table 3-1)"""
    alpha = 0.91 * L / math.sqrt(D * t)
    return max(1.0, 1 + 3 * (dm - 0.05 * t) / t * math.exp(-alpha))


def transfer_curves(soil, template, H_max=250e3, n=26):
    sh = shoulder_law()
    m = Model(soil, le_top=0.25, shoulder=sh, template=template)
    Hs = np.linspace(0, H_max, n)
    out = {hs["id"]: [0.0] for hs in HOTSPOTS}
    diag = []
    u = None
    for H in Hs[1:]:
        u, _ = m.solve(H, nsteps=3, u0=None)
        zmo, Mo = m.moments(u, "outer")
        zmi, Mi = m.moments(u, "inner")
        for hs in HOTSPOTS:
            zz, MM = (zmi, Mi) if hs["string"] == "inner" else (zmo, Mo)
            out[hs["id"]].append(float(np.interp(hs["z"], zz, MM)))
        diag.append((H, zmo, Mo, zmi, Mi, m.profile(u, "outer"), m.profile(u, "inner")))
    return Hs, out, diag


# ------------------------------------------------------------------------------------ main
def main():
    out = {}
    hot = json.load(open(DATA + "hotspot.json"))
    soil = Soil(cyclic=True)
    tpl = json.load(open(DATA + "template.json"))
    K_T = tpl["k_slot"]["foundation_k_x"]
    Hs, curves, diag = transfer_curves(soil, Gap(0.030, K_T))
    # SCFs
    scf = {"hp": hot["welds"]["hpwhh"]["scf"], "lp": hot["welds"]["lpwh"]["scf"]}
    t_c = 0.0381
    scf["cg"] = girth_scf(DELTA_M, t_c)
    for hs in HOTSPOTS:
        D, t = hs["D"], hs["t"]
        I = np.pi / 64 * (D ** 4 - (D - 2 * t) ** 4)
        hs["W"] = I / (D / 2)
        hs["scf"] = scf[hs["id"]]
        sn = SN(hs["cls"], hs["env"], t)
        hs["tf"] = sn.tf
        hs["M"] = curves[hs["id"]]
        hs["sigma"] = [hs["scf"] * M / hs["W"] / 1e6 for M in curves[hs["id"]]]    # hot-spot stress [MPa]
        print(f"{hs['id']}: SCF={hs['scf']:.3f} tf={sn.tf:.3f} W={hs['W']:.4e} "
              f"stress at 25 kN: {np.interp(25e3, Hs, hs['sigma']):.2f} MPa")
    out["H"] = (Hs / 1e3).tolist()
    # moment diagrams for the video at a fatigue-size load
    Hd = 25e3
    k = int(np.argmin([abs(d[0] - Hd) for d in diag]))
    H, zmo, Mo, zmi, Mi, po, pi = diag[k]
    out["diagram"] = dict(H=H / 1e3, zo=np.round(zmo, 3).tolist(), Mo=np.round(Mo / 1e3, 2).tolist(),
                          zi=np.round(zmi, 3).tolist(), Mi=np.round(Mi / 1e3, 2).tolist(),
                          uo_z=np.round(po[0], 3).tolist(), uo=np.round(po[1] * 1e3, 4).tolist(),
                          ui_z=np.round(pi[0], 3).tolist(), ui=np.round(pi[1] * 1e3, 4).tolist())
    zz = np.array(zmo)
    kk = np.argmax(np.abs(Mo) * (zz < 0))
    out["diagram"]["zpeak"] = float(zz[kk])
    out["diagram"]["Mpeak"] = float(Mo[kk] / 1e3)

    # ---- sea states
    P = scatter()
    out["scatter"] = dict(hs_edges=HS_EDGES.tolist(), tp_edges=TP_EDGES.tolist(), P=np.round(P, 7).tolist(),
                          weibull=WB)
    f = np.linspace(0.02, 0.5, 300)
    out["G"] = dict(T=(1 / f).tolist(), G=(G_riser(f) / 1e3).tolist(), G0=G0 / 1e3, T0=T0)

    # ---- per sea state: force -> stress -> rainflow -> damage
    sns = {hs["id"]: SN(hs["cls"], hs["env"], hs["t"]) for hs in HOTSPOTS}
    Hgrid = np.r_[-Hs[::-1], Hs[1:]]
    sig_fun = {}
    for hs in HOTSPOTS:
        sg = np.array(hs["sigma"])
        sig_fun[hs["id"]] = (Hgrid, np.r_[-sg[::-1], sg[1:]])
    dmg = {hs["id"]: np.zeros_like(P) for hs in HOTSPOTS}       # damage per hour
    cycles_per_hour = np.zeros_like(P)
    long_ranges = {hs["id"]: [] for hs in HOTSPOTS}
    seed = 1
    for i in range(P.shape[0]):
        for j in range(P.shape[1]):
            if P[i, j] < 2e-6:
                continue
            hsv = max(0.5 * (HS_EDGES[i] + HS_EDGES[i + 1]), 0.3)
            tpv = 0.5 * (TP_EDGES[j] + TP_EDGES[j + 1])
            t, eta, F = force_series(hsv, tpv, seed)
            seed += 1
            for hs in HOTSPOTS:
                xg, yg = sig_fun[hs["id"]]
                s = np.interp(F, xg, yg)
                rg, cn, _ = rainflow(s)
                dmg[hs["id"]][i, j] = np.sum(cn / sns[hs["id"]].N(rg)) / (TSIM / 3600)
                long_ranges[hs["id"]].append((P[i, j], rg, cn))
                if hs["id"] == "lp":
                    cycles_per_hour[i, j] = cn.sum() / (TSIM / 3600)
    out["damage"] = {}
    for hs in HOTSPOTS:
        d = dmg[hs["id"]]
        Dday = float(np.sum(P * d) * 24)
        life_days = 1 / Dday
        contrib = P * d / np.sum(P * d)
        out["damage"][hs["id"]] = dict(D_day=Dday, life_days=life_days, contrib=np.round(contrib, 6).tolist(),
                                       d_hour=d.tolist())
        print(f"{hs['id']}: damage/day {Dday:.3e}  life {life_days:.0f} days ({life_days / 365.25:.1f} yr)")
    out["cycles_per_day"] = float(np.sum(P * cycles_per_hour) * 24)
    print("cycles/day", out["cycles_per_day"])

    # ---- the example sea state, for the animations
    hs_ex, tp_ex = 3.5, 9.5
    t, eta, F = force_series(hs_ex, tp_ex, 4242)
    xg, yg = sig_fun["cg"]
    s = np.interp(F, xg, yg)
    n_show = int(180 / DT)
    (rg, cn, mn), rev, trace = rainflow(s, trace=True)
    out["example"] = dict(hs=hs_ex, tp=tp_ex, dt=DT, eta=np.round(eta[:n_show], 4).tolist(),
                          F=np.round(F[:n_show] / 1e3, 3).tolist(), s=np.round(s[:n_show], 3).tolist())
    # spectrum
    fr = np.linspace(0.03, 0.4, 200)
    out["example"]["spec_f"] = fr.tolist()
    out["example"]["S_eta"] = jonswap(fr, hs_ex, tp_ex).tolist()
    out["example"]["S_F"] = (jonswap(fr, hs_ex, tp_ex) * (G_riser(fr) / 1e3) ** 2).tolist()
    # rainflow histogram (3 h)
    sn = sns["cg"]
    bins = np.arange(0, np.ceil(rg.max() / 2.5) * 2.5 + 2.5, 2.5)
    hist, _ = np.histogram(rg, bins=bins, weights=cn)
    dbin = np.array([np.sum(cn[(rg >= a) & (rg < b)] / sn.N(rg[(rg >= a) & (rg < b)])) for a, b in zip(bins[:-1], bins[1:])])
    out["example"]["hist"] = dict(edges=bins.tolist(), n=hist.tolist(), dmg=dbin.tolist(),
                                  D_3h=float(np.sum(cn / sn.N(rg))), cycles=float(cn.sum()))
    # the rainflow demo: a short stretch of the stress history with its reversals and extraction trace
    # pick a stretch of about 15 reversals that holds several small cycles riding on larger ones
    ridx_all, rv_all = reversals(s)
    best, nrev = None, 15
    for k0 in range(0, min(len(rv_all) - nrev, 3000)):
        (_, cn_w, _), _, tr_w = rainflow(rv_all[k0:k0 + nrev], trace=True)
        full = sum(1 for a in tr_w if a[2] == "full")
        span = rv_all[k0:k0 + nrev].max() - rv_all[k0:k0 + nrev].min()
        score = full + 0.02 * span
        if best is None or score > best[0]:
            best = (score, k0)
    k0 = best[1]
    i0 = max(0, ridx_all[k0] - 4)
    i1 = ridx_all[k0 + nrev - 1] + 5
    seg = s[i0:i1]
    (rg2, cn2, mn2), rev2, tr2 = rainflow(seg, trace=True)
    ridx, _ = reversals(seg)
    out["rf_demo"] = dict(s=np.round(seg, 3).tolist(), t0=i0 * DT, rev_idx=ridx.tolist(), rev=np.round(rev2, 3).tolist(),
                          trace=[[int(a), int(b), k] for a, b, k in tr2], ranges=np.round(rg2, 3).tolist(),
                          counts=cn2.tolist())
    print("demo reversals", len(rev2), "cycles", len(tr2))

    # ---- S-N curves for plotting
    out["sn"] = {}
    for env in ("air", "cp", "fc"):
        out["sn"][env] = {c: SN(c, env).curve() for c in (["B1", "C", "D", "E", "F", "F1", "F3", "G", "W3"] if env == "air" else ["D", "F1"])}
    out["sn_table"] = {c: SN_AIR[c] for c in SN_AIR}
    out["sn_table_cp"] = {c: SN_CP[c] for c in SN_CP}
    out["sn_knee"] = {env: dict(N=SN("D", env).N1, S=10 ** SN("D", env).logS1) for env in ("air", "cp")}

    # ---- long-term distribution and the Weibull closed form (C203 section 5)
    for hs in HOTSPOTS:
        allr = np.concatenate([r for p, r, c in long_ranges[hs["id"]]])
        allw = np.concatenate([p * c / (TSIM / 3600) for p, r, c in long_ranges[hs["id"]]])  # cycles per hour
        nu_h = allw.sum()
        order = np.argsort(allr)[::-1]
        sr, w = allr[order], allw[order]
        exc = np.cumsum(w) / nu_h          # exceedance probability
        # fit ln(-ln Q) = h ln s - h ln q on the upper part (Q < 0.3)
        sel = (exc < 0.3) & (exc > 1e-7)
        A = np.c_[np.log(sr[sel]), np.ones(sel.sum())]
        coef = np.linalg.lstsq(A, np.log(-np.log(exc[sel])), rcond=None)[0]
        h = coef[0]
        q = math.exp(-coef[1] / h)
        snh = sns[hs["id"]]
        qt = q * snh.tf
        # damage per day, closed form: single slope (first branch) and bilinear
        nu_day = nu_h * 24
        D1 = nu_day / 10 ** snh.la1 * qt ** snh.m1 * G(1 + snh.m1 / h)
        S1 = 10 ** snh.logS1
        x = (S1 / qt) ** h
        D2 = nu_day * (qt ** snh.m1 / 10 ** snh.la1 * G(1 + snh.m1 / h) * gammaincc(1 + snh.m1 / h, x)
                       + qt ** snh.m2 / 10 ** snh.la2 * G(1 + snh.m2 / h) * gammainc(1 + snh.m2 / h, x))
        dd = out["damage"][hs["id"]]
        dd.update(weibull_h=h, weibull_q=q, nu_day=nu_day, D_day_wb1=D1, D_day_wb2=D2,
                  life_wb2=1 / D2, life_wb1=1 / D1)
        # exceedance curve for plotting (thinned, log spaced in Q)
        Qs = np.logspace(-8, 0, 60)
        sQ = [float(np.interp(Qv, exc, sr)) for Qv in Qs]
        dd["exceed"] = dict(Q=Qs.tolist(), s=sQ)
        dd["n_year"] = nu_h * 8766
        print(f"{hs['id']}: Weibull h={h:.3f} q={q:.2f} MPa  life: direct {dd['life_days']:.0f} d, "
              f"closed form bilinear {1 / D2:.0f} d, single slope {1 / D1:.0f} d")

    # ---- environments for the governing detail
    gov = min(HOTSPOTS, key=lambda hs: out["damage"][hs["id"]]["life_days"])
    env_life = {}
    for env in ("air", "cp", "fc"):
        snh = SN(gov["cls"], env, gov["t"])
        tot = 0.0
        for p, r, c in long_ranges[gov["id"]]:
            tot += p * np.sum(c / snh.N(r)) / (TSIM / 3600)
        env_life[env] = 1 / (tot * 24)
    out["env_life"] = env_life
    print("environment lives (days):", {k: round(v) for k, v in env_life.items()})

    # ---- sensitivity: stress scaling, misalignment, soil bounds (governing detail)
    def life_scaled(hsid, factor, cls=None, env=None):
        hs = next(h for h in HOTSPOTS if h["id"] == hsid)
        snh = SN(cls or hs["cls"], env or hs["env"], hs["t"])
        tot = 0.0
        for p, r, c in long_ranges[hsid]:
            tot += p * np.sum(c / snh.N(r * factor)) / (TSIM / 3600)
        return 1 / (tot * 24)
    sens = {"stress": [[fct, life_scaled(gov["id"], fct)] for fct in (0.8, 0.9, 1.0, 1.1, 1.2, 1.3)]}
    # misalignment of the girth weld
    sens["misalign"] = []
    for dm in (0.0, 0.002, 0.004, 0.006, 0.008, 0.010, 0.012):
        s_new = girth_scf(dm, t_c)
        sens["misalign"].append([dm * 1e3, s_new, life_scaled("cg", s_new / scf["cg"])])
    # soil bounds: recompute transfer curves for LB and UB soils
    sens["soil"] = {}
    for name, fs, e50 in (("LB", 0.6, 0.02), ("BE", 1.0, 0.01), ("UB", 1.5, 0.005)):
        sl = Soil(su0=3e3 * fs, k_su=1.5e3 * fs, eps50=e50, cyclic=True)
        Hs2, cv2, _ = transfer_curves(sl, Gap(0.030, K_T), n=14)
        res = {}
        for hs in HOTSPOTS:
            # ratio of stress transfer at fatigue-size loads (10-40 kN) relative to the best estimate
            r = np.mean([np.interp(Hv, Hs2, cv2[hs["id"]]) / np.interp(Hv, Hs, curves[hs["id"]]) for Hv in (10e3, 20e3, 40e3)])
            res[hs["id"]] = dict(ratio=r, life=life_scaled(hs["id"], r))
        sens["soil"][name] = res
        print("soil", name, {k: (round(v["ratio"], 3), round(v["life"])) for k, v in res.items()})
    # the girth weld made on site instead of in the shop with the pipe rotated: S-N class E ([3.3.7.3])
    sens["class_E"] = life_scaled("cg", 1.0, cls="E")
    print("girth weld as class E:", round(sens["class_E"]))
    out["sens"] = sens
    out["hotspots"] = [{k: v for k, v in hs.items()} for hs in HOTSPOTS]
    out["scf"] = scf
    out["girth"] = dict(delta_m=DELTA_M, t=t_c, D=0.9144, L=L_WELD, scf=scf["cg"],
                        alpha=0.91 * L_WELD / math.sqrt(0.9144 * t_c))
    out["governing"] = gov["id"]
    out["dff"] = 10
    out["plan_days"] = 120
    for hs in HOTSPOTS:
        L_ = out["damage"][hs["id"]]["life_days"]
        print(f"{hs['id']}: life {L_:.0f} d, allowable with DFF 10: {L_ / 10:.0f} d")
    with open(DATA + "fatigue.json", "w") as fh:
        json.dump(out, fh)
    print("written")


if __name__ == "__main__":
    main()
