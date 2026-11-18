"""The five 'yield but no failure' analyses.  usage: python cases.py [1 2 3 4 5]

Outputs -> ../build/fe/caseN.json (curves, key numbers) and ../build/frames/caseN_*/f_XXXXX.png (field frames).
"""
import json
import os
import sys
import time

import numpy as np

from epfem import Material, Model, dnv_type_curve, gmsh_t6, structured_t6, triaxiality, von_mises
from plots import draw_field

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "build", "fe")
FR = os.path.join(ROOT, "build", "frames")
os.makedirs(OUT, exist_ok=True)
E, NU = 210000.0, 0.3


def S355_epp():
    return Material(E, NU, 355.0, name="S355 elastic-perfectly plastic")


def S355_true():
    return Material(E, NU, 357.0, hardening=dnv_type_curve(), name="S355 true stress-strain (plateau + power law)")


def save(name, data):
    json.dump(data, open(os.path.join(OUT, f"{name}.json"), "w"), indent=1, default=float)


def frames(model, hist, keys, sy, folder, win, **kw):
    d = os.path.join(FR, folder)
    os.makedirs(d, exist_ok=True)
    for i, k in enumerate(keys):
        snap = hist["snap"][k]
        vm = model.nodal(von_mises(snap["sig"]))
        eb = model.nodal(snap["eb"])
        draw_field(model, snap["u"], vm, eb, sy, os.path.join(d, f"f_{i:05d}.png"), win, **kw)


def ligament_fraction(model, eb, pred):
    """Fraction of Gauss points on a section (pred on GP coords) that are plastic."""
    xq = model.XQ.reshape(-1, 2)
    sel = pred(xq[:, 0], xq[:, 1])
    return float((eb[sel] > 1e-6).mean()) if sel.any() else 0.0


# ======================================================================= case 1: plate with a hole
def case1():
    W2, H2, a, t = 100.0, 200.0, 30.0, 20.0

    def build(occ):
        r = occ.addRectangle(0, 0, 0, W2, H2)
        d = occ.addDisk(0, 0, 0, a, a)
        occ.cut([(2, r)], [(2, d)])
    X, T = gmsh_t6(build, f"Min(7, 0.8 + 0.12*Max(Sqrt(x*x+y*y)-{a}, 0))")
    res = {}
    for tag, mat in (("epp", S355_epp()), ("true", S355_true()), ("elastic", Material(E, NU, 1e9))):
        m = Model(X, T, mat, mode="pstress", thickness=t)
        m.fix(m.nodes_where(lambda x, y: np.isclose(x, 0)), 0)
        m.fix(m.nodes_where(lambda x, y: np.isclose(y, 0)), 1)
        top = m.nodes_where(lambda x, y: np.isclose(y, H2))
        dmax = 1.2 if tag != "elastic" else 0.2
        m.fix(top, 1, lambda s, d=dmax: d * s)
        n = 90 if tag != "elastic" else 2
        ts = np.r_[0, np.linspace(0, 1, n + 1)[1:] ** 1.4]
        mon = dict(P=lambda md, u, f: 2 * f[2 * top + 1].sum() / 1e3,
                   d=lambda md, u, f: float(u[2 * top[0] + 1]),
                   eb=lambda md, u, f: float(md.state["eb"].max()),
                   lig=lambda md, u, f: ligament_fraction(md, md.state["eb"], lambda x, y: (y < 1.5) & (x > a)),
                   vmax=lambda md, u, f: float(md.nodal(von_mises(md.sig)).max()) if tag == "elastic" else 0.0)
        t0 = time.time()
        H = m.solve(ts, monitors=mon, keep=set(range(len(ts))) if tag == "epp" else None)
        print(f"case1 {tag}: {time.time() - t0:.0f}s conv={H['converged']} Pmax={max(H['P']):.0f} kN", flush=True)
        res[tag] = H
        if tag == "epp":
            m_epp, H_epp = m, H
        if tag == "elastic":
            sig_net = H["P"][-1] * 1e3 / ((2 * W2 - 2 * a) * t)
            kt = H["vmax"][-1] / sig_net
    Pl_net = 355.0 * (2 * W2 - 2 * a) * t / 1e3
    Pe = np.array(res["epp"]["P"]); lig = np.array(res["epp"]["lig"]); ebm = np.array(res["epp"]["eb"])
    i_y = int(np.argmax(ebm > 1e-7))
    P_first = float(Pe[i_y - 1] + (Pe[i_y] - Pe[i_y - 1]) * 0.0) if i_y > 0 else float(Pe[0])
    P_first_el = 355.0 / kt * (2 * W2 - 2 * a) * t / 1e3
    # frames: every 2nd snapshot, full plate by mirroring
    keys = sorted(res["epp"]["snap"])[1::2]
    frames(m_epp, res["epp"], keys, 355.0, "case1", (-105, 105, -78.75, 78.75), size=(8, 6), dpi=220,
           mirror=("x", "y"))
    Pd = 600.0
    out = dict(W=2 * W2, d=2 * a, t=t, kt_net=kt, P_first_yield_elastic=P_first_el, P_first_yield_fe=P_first,
               P_limit_net_section=Pl_net, P_limit_fe=float(Pe.max()), design_load=Pd,
               elastic_peak_at_design=kt * Pd * 1e3 / ((2 * W2 - 2 * a) * t), factored_load=1.5 * Pd,
               frame_keys=[int(k) for k in keys],
               curves={k: dict(P=res[k]["P"], d=res[k]["d"], eb=res[k]["eb"], lig=res[k]["lig"]) for k in ("epp", "true")})
    save("case1", out)
    print(json.dumps({k: v for k, v in out.items() if not isinstance(v, (dict, list))}, indent=1, default=float))


# ======================================================================= case 2: plastic hinge (pure bending)
def case2():
    """Constant-moment region of a 100 x 50 mm S355 beam: end rotation prescribed (plane sections)."""
    Lb, h, b = 300.0, 100.0, 50.0
    X, T = structured_t6(0, Lb, -h / 2, h / 2, 60, 24)
    My = 355.0 * b * h ** 2 / 6.0
    Mp = 1.5 * My
    th_max = 0.12
    res = {}
    for tag, mat in (("epp", S355_epp()), ("true", S355_true())):
        m = Model(X, T, mat, mode="pstress", thickness=b)
        left = m.nodes_where(lambda x, y: np.isclose(x, 0))
        right = m.nodes_where(lambda x, y: np.isclose(x, Lb))
        m.fix(left, 0)
        m.fix(m.nodes_where(lambda x, y: np.isclose(x, 0) & np.isclose(y, 0)), 1)
        for n in right:
            yn = m.X[n, 1]
            m.fixed[2 * int(n)] = (lambda s, yn=yn: -th_max * s * yn)
        ts = np.r_[0, np.linspace(0, 1, 121)[1:] ** 1.7]
        mon = dict(M=lambda md, u, f: float(-(f[2 * right] * md.X[right, 1]).sum() / 1e6),
                   th=lambda md, u, f: float(-(u[2 * right[np.argmax(md.X[right, 1])]]) / (h / 2)),
                   eb=lambda md, u, f: float(md.state["eb"].max()),
                   depth=lambda md, u, f: ligament_fraction(md, md.state["eb"], lambda x, y: np.abs(x - Lb / 2) < 3.0))
        t0 = time.time()
        H = m.solve(ts, monitors=mon, keep=set(range(len(ts))) if tag == "epp" else None)
        print(f"case2 {tag}: {time.time() - t0:.0f}s conv={H['converged']} Mmax={max(H['M']):.2f} kNm "
              f"(My={My/1e6:.2f}, Mp={Mp/1e6:.2f})", flush=True)
        res[tag] = H
        if tag == "epp":
            m_epp = m
    th = np.array(res["epp"]["th"]); kappa = th / Lb
    ky = 2 * 355.0 / (E * h)
    M_an = np.where(kappa <= ky, E * (b * h ** 3 / 12) * kappa, Mp * (1 - (ky / np.maximum(kappa, 1e-12)) ** 2 / 3)) / 1e6

    def tes(M, th):
        M, th = np.asarray(M), np.asarray(th)
        k = M[2] / th[2]
        g = M - 0.5 * k * th
        i = int(np.argmax(g < 0)) if np.any(g < 0) else len(g) - 1
        f = g[i - 1] / (g[i - 1] - g[i])
        return float(M[i - 1] + f * (M[i] - M[i - 1])), float(th[i - 1] + f * (th[i] - th[i - 1])), float(k)
    tes_epp = tes(res["epp"]["M"], res["epp"]["th"])
    tes_true = tes(res["true"]["M"], res["true"]["th"])
    ebm = np.array(res["epp"]["eb"]); i_y = int(np.argmax(ebm > 1e-7))
    keys = sorted(res["epp"]["snap"])[1::2]
    frames(m_epp, res["epp"], keys, 355.0, "case2", (-6, Lb + 6, -84.2, 84.2), size=(8, 4.2), dpi=240,
           mirror=(), outline=True)
    out = dict(depth=h, width=b, length=Lb, M_y=My / 1e6, M_p=Mp / 1e6, M_first_yield_fe=float(res["epp"]["M"][i_y]),
               M_max_epp=float(max(res["epp"]["M"])), M_max_true=float(max(res["true"]["M"])),
               tes_epp=tes_epp, tes_true=tes_true, kappa_y=ky, frame_keys=[int(k) for k in keys],
               M_analytic=M_an.tolist(),
               curves={k: dict(M=res[k]["M"], th=res[k]["th"], eb=res[k]["eb"], depth=res[k]["depth"]) for k in res})
    save("case2", out)
    print(json.dumps({k: v for k, v in out.items() if not isinstance(v, (dict, list))}, indent=1, default=float))


# ======================================================================= case 3: thick-walled cylinder (HPHT)
def case3():
    a, b, h = 50.0, 100.0, 2.0
    sy = 517.0                                                  # 75 ksi low-alloy forging
    nr = 40
    xs = a + (b - a) * (np.linspace(0, 1, 2 * nr + 1) ** 1.3)
    X, T = structured_t6(a, b, 0, h, nr, 1, xgrade=xs)
    k_ = sy / np.sqrt(3)
    p_y_hill, p_c_hill = k_ * (1 - a ** 2 / b ** 2), 2 * k_ * np.log(b / a)
    # (a) displacement-controlled run to collapse -> p-u curve and plastic radius
    m = Model(X, T, Material(E, NU, sy), mode="axisym")
    m.fix(m.nodes_where(lambda x, y: np.isclose(y, 0)), 1)
    m.fix(m.nodes_where(lambda x, y: np.isclose(y, h)), 1)
    bore = m.nodes_where(lambda x, y: np.isclose(x, a))
    m.fix(bore, 0, lambda s: 0.6 * s)
    area = 2 * np.pi * a * h
    mon = dict(p=lambda md, u, f: -f[2 * bore].sum() / area * -1.0,
               u=lambda md, u, f: float(u[2 * bore[0]]),
               c=lambda md, u, f: float(md.XQ.reshape(-1, 2)[md.state["eb"] > 0, 0].max()) if (md.state["eb"] > 0).any() else a)
    H = m.solve(np.r_[0, np.linspace(0.01, 1, 100)], monitors=mon)
    pcurve = np.abs(np.array(H["p"]))
    # (b) pressure-controlled: design pressure 20 ksi, global check at 2.4x, then unload (residual stress)
    pd = 137.9
    m2 = Model(X, T, Material(E, NU, sy), mode="axisym")
    m2.fix(m2.nodes_where(lambda x, y: np.isclose(y, 0)), 1)
    m2.fix(m2.nodes_where(lambda x, y: np.isclose(y, h)), 1)
    edges = m2.edges_where(lambda x, y: np.isclose(x, a))
    unit = m2.edge_load(edges, pressure=1.0)
    hist_p = lambda s: 2.4 * pd * (s if s <= 1 else 2 - s)       # up to 2.4 pd, then back to zero
    m2.loads.append(lambda s: hist_p(s) * unit)
    ts = np.r_[0, np.linspace(0.05, 1, 20), np.linspace(1.05, 2, 20)]
    H2 = m2.solve(ts, keep={20, 40}, monitors=dict(p=lambda md, u, f: 0.0))
    xq = m2.XQ.reshape(-1, 2)

    def profile(sig):
        order = np.argsort(xq[:, 0])
        r = xq[order, 0]
        ss = sig[order]
        return dict(r=r.tolist(), s_rr=ss[:, 0].tolist(), s_zz=ss[:, 1].tolist(), s_tt=ss[:, 2].tolist(),
                    vm=von_mises(ss).tolist())
    s_max = H2["snap"][20]["sig"]; s_res = H2["snap"][40]["sig"]
    eb_max = H2["snap"][20]["eb"]
    c_at = float(xq[eb_max > 0, 0].max()) if (eb_max > 0).any() else a
    # Hill: plastic radius at 2.4 pd
    cs = np.linspace(a, b, 20001)
    pp = k_ * (2 * np.log(cs / a) + 1 - cs ** 2 / b ** 2)
    c_hill = float(np.interp(2.4 * pd, pp, cs))
    # Lame elastic peak at design and at 2.4x
    lame_vm = lambda p: p * np.sqrt(0.5 * ((-1 - (b**2 + a**2) / (b**2 - a**2)) ** 2 + ((b**2 + a**2) / (b**2 - a**2) - 0.6 * a**2 / (b**2 - a**2)) ** 2 + (0.6 * a**2 / (b**2 - a**2) + 1) ** 2))
    out = dict(a=a, b=b, sy=sy, p_design=pd, p_global=2.4 * pd, p_y_hill=p_y_hill, p_c_hill=p_c_hill,
               p_c_fe=float(pcurve.max()), c_fe_at_global=c_at, c_hill_at_global=c_hill,
               plastic_wall_fraction=(c_at - a) / (b - a),
               vm_bore_elastic_design=lame_vm(pd), vm_bore_elastic_global=lame_vm(2.4 * pd),
               residual_hoop_bore=float(np.array(profile(s_res)["s_tt"])[0]),
               reverse_yield_limit=2 * p_y_hill,
               curve=dict(p=pcurve.tolist(), u=H["u"], c=H["c"]),
               at_global=profile(s_max), residual=profile(s_res))
    save("case3", out)
    print(json.dumps({k: v for k, v in out.items() if not isinstance(v, (dict, list))}, indent=1, default=float))


# ======================================================================= case 4: local strain at the transition fillet
def case4():
    Ri, Ro1, Ro2, RHO, ZS, L = 116.55, 136.55, 170.0, 8.0, 600.0, 1020.0

    def build(occ):
        P = lambda r, z: occ.addPoint(r, z, 0)
        p1, p2, p3 = P(Ri, 0), P(Ro1, 0), P(Ro1, ZS - RHO)
        pc, p4, p5, p6, p7 = P(Ro1 + RHO, ZS - RHO), P(Ro1 + RHO, ZS), P(Ro2, ZS), P(Ro2, L), P(Ri, L)
        cur = [occ.addLine(p1, p2), occ.addLine(p2, p3), occ.addCircleArc(p3, pc, p4), occ.addLine(p4, p5),
               occ.addLine(p5, p6), occ.addLine(p6, p7), occ.addLine(p7, p1)]
        occ.addPlaneSurface([occ.addCurveLoop(cur)])
    X, T = gmsh_t6(build, f"Min(9, 0.35 + 0.2*Max(Sqrt((x-{Ro1 + RHO})^2+(y-{ZS - RHO})^2)-{RHO}, 0))")
    A1 = np.pi * (Ro1 ** 2 - Ri ** 2)
    sd = 150.0                                                  # design nominal axial stress (MPa)
    res = {}
    for tag, mat in (("true", S355_true()), ("elastic", Material(E, NU, 1e9))):
        m = Model(X, T, mat, mode="axisym")
        m.fix(m.nodes_where(lambda x, y: np.isclose(y, L)), 1)
        e0 = m.edges_where(lambda x, y: np.isclose(y, 0))
        unit = m.edge_load(e0, traction=(0.0, -1.0))
        lf_max = 2.0
        m.loads.append(lambda s, U=unit: s * lf_max * sd * U)
        ts = np.r_[0, np.linspace(0, 1, 81)[1:]] if tag == "true" else np.array([0, 0.5])

        def at_max(md):
            eb = md.state["eb"]; i = int(np.argmax(eb))
            return dict(eb=float(eb[i]), eta=float(triaxiality(md.sig)[i]), r=float(md.XQ.reshape(-1, 2)[i, 0]),
                        z=float(md.XQ.reshape(-1, 2)[i, 1]), vm=float(von_mises(md.sig)[i]))
        mon = dict(lf=lambda md, u, f: 0.0, mx=lambda md, u, f: at_max(md),
                   vmax=lambda md, u, f: float(md.nodal(von_mises(md.sig)).max()) if tag == "elastic" else 0.0)
        t0 = time.time()
        H = m.solve(ts, monitors=mon, keep=set(range(len(ts))) if tag == "true" else None)
        H["lf"] = [lf_max * s for s in H["t"]]
        print(f"case4 {tag}: {time.time() - t0:.0f}s conv={H['converged']}", flush=True)
        res[tag] = H
        if tag == "true":
            m_true = m
    kt = res["elastic"]["vmax"][-1] / (0.5 * lf_max * sd)
    lf = np.array(res["true"]["lf"]); ebm = np.array([d["eb"] for d in res["true"]["mx"]])
    eta = np.array([d["eta"] for d in res["true"]["mx"]])
    i17 = int(np.argmin(np.abs(lf - 1.7)))
    # ASME VIII-2 5.3.3 triaxial strain limit for ferritic steel (Table 5.7): S355, Rm = 470, A = 22 %
    R = 355.0 / 470.0
    m2 = 0.60 * (1.0 - R)
    eLu = max(m2, 2.0 * np.log(1.0 + 22.0 / 100.0))
    asl = 2.2
    eL = lambda e: eLu * np.exp(-(asl / (1.0 + m2)) * (e - 1.0 / 3.0))
    lf_first = float(355.0 / (kt * sd))
    # Neuber estimate at 1.7x (local elastic stress -> sigma*eps = const)
    s_el = kt * 1.7 * sd
    from scipy.optimize import brentq
    h = dnv_type_curve()
    def neuber(s):
        epl = brentq(lambda e: h(np.array([e]))[0][0] - s, 0, 3.0) if s > 357 else 0.0
        return s * (s / E + epl) - s_el ** 2 / E
    s_n = brentq(neuber, 1.0, 850.0)
    ep_neuber = (brentq(lambda e: h(np.array([e]))[0][0] - s_n, 0, 3.0) if s_n > 357 else 0.0)
    keys = sorted(res["true"]["snap"])[1::1]
    frames(m_true, res["true"], keys, 357.0, "case4", (ZS - 34, ZS + 14, Ro1 - 13.5, Ro1 + 13.5), size=(8, 4.5),
           dpi=240, swap=True, outline=True)
    out = dict(kt=kt, design_sigma=sd, lf_first_yield=lf_first, lf_local=1.7, eb_at_17=float(ebm[i17]),
               eta_at_17=float(eta[i17]), eL_at_17=float(eL(eta[i17])), utilisation_17=float(ebm[i17] / eL(eta[i17])),
               R=R, m2=m2, eLu=eLu, alpha_sl=asl, elastic_peak_at_17=s_el, neuber_ep_at_17=ep_neuber,
               where=res["true"]["mx"][i17], frame_keys=[int(k) for k in keys],
               curve=dict(lf=lf.tolist(), eb=ebm.tolist(), eta=eta.tolist(), eL=[float(eL(e)) for e in eta]))
    save("case4", out)
    print(json.dumps({k: v for k, v in out.items() if not isinstance(v, (dict, list))}, indent=1, default=float))


# ======================================================================= case 5: Bree cylinder - shakedown vs ratcheting
def case5():
    Rm, tw, h = 200.0, 10.0, 2.0
    sy, alpha = 355.0, 1.2e-5
    X, T = structured_t6(Rm - tw / 2, Rm + tw / 2, 0, h, 24, 1)
    runs = {}
    for name, (Xp, Yt) in dict(shakedown=(0.3, 1.4), ratchet=(0.6, 2.4), alternating=(0.1, 2.6)).items():
        mat = Material(E, NU, sy, alpha=alpha)
        m = Model(X, T, mat, mode="axisym")
        m.fix(m.nodes_where(lambda x, y: np.isclose(y, 0)), 1)
        top = m.nodes_where(lambda x, y: np.isclose(y, h))
        m.tie(top, 1)                                             # generalised plane strain, open ends
        p = Xp * sy * tw / Rm
        dT = Yt * sy * 2 * (1 - NU) / (E * alpha)
        edges = m.edges_where(lambda x, y: np.isclose(x, Rm - tw / 2))
        unit = m.edge_load(edges, pressure=1.0)
        ncyc = 10
        m.loads.append(lambda s, U=unit, p=p: p * min(s, 1.0) * U)  # ramp pressure in [0,1], then hold

        def theta(s):
            if s <= 1:
                return 0.0
            c = (s - 1) % 2.0
            return c if c <= 1 else 2 - c
        m.temperature = lambda s, xq, dT=dT: theta(s) * dT * ((Rm - xq[:, 0]) / tw)   # inner hotter, mean zero
        mid = m.nodes_where(lambda x, y: np.isclose(x, Rm) & np.isclose(y, 0))[0]
        inner = m.nodes_where(lambda x, y: np.isclose(x, Rm - tw / 2) & np.isclose(y, 0))[0]
        ts = [0.0] + list(np.linspace(0.1, 1, 10))
        for c in range(ncyc):
            ts += list(1 + 2 * c + np.linspace(0.1, 2.0, 20))
        mon = dict(hoop=lambda md, u, f: float(u[2 * mid]) / Rm, eb=lambda md, u, f: float(md.state["eb"].max()),
                   ebmean=lambda md, u, f: float(md.state["eb"].mean()),
                   theta=lambda md, u, f: 0.0)
        t0 = time.time()
        H = m.solve(np.array(ts), monitors=mon)
        H["theta"] = [theta(s) for s in H["t"]]
        ends = [i for i, s in enumerate(H["t"]) if s > 1 and abs(((s - 1) % 2.0)) < 1e-9]
        hoop_end = [H["hoop"][i] for i in ends]
        eb_end = [H["eb"][i] for i in ends]
        print(f"case5 {name}: {time.time() - t0:.0f}s conv={H['converged']} hoop at cycle ends {np.round(np.array(hoop_end) * 100, 4)} %",
              flush=True)
        runs[name] = dict(X=Xp, Y=Yt, p=p, dT=dT, t=H["t"], hoop=H["hoop"], eb=H["eb"], theta=H["theta"],
                          hoop_cycle_end=hoop_end, eb_cycle_end=eb_end)
    save("case5", dict(R=Rm, t=tw, sy=sy, runs=runs))


if __name__ == "__main__":
    which = [int(a) for a in sys.argv[1:]] or [1, 2, 3, 4, 5]
    for w in which:
        dict(enumerate([None, case1, case2, case3, case4, case5]))[w]()
