"""Run all global-model studies and write video/data/global.json."""
import json
import numpy as np
from globalmodel import (Model, Soil, PWL, Gap, Linear, D_COND, EI_COND, EI_CAS, Z_WH, Z_LOAD,
                         Z_TEMPLATE, matlock_smooth)

loc = json.load(open("/home/user/Mesh/video/data/wellhead_local.json"))
tpl = json.load(open("/home/user/Mesh/video/data/template.json"))
rot = np.array([0.0] + [r["rot_rel"] for r in loc["results"][1:]])
Mloc = np.array([r["M"] for r in loc["results"]])
SHOULDER = PWL(np.r_[rot, rot[-1] * 3], np.r_[Mloc, Mloc[-1] + (Mloc[-1] - Mloc[-2]) / (rot[-1] - rot[-2]) * rot[-1] * 2])
K_TEMPLATE = tpl["k_slot"]["foundation_k_x"]
GAP = 0.030
H_BASE = 150e3

out = {"H_base": H_BASE, "z_wh": Z_WH, "z_load": Z_LOAD, "gap": GAP, "k_template": K_TEMPLATE,
       "D": D_COND}


def summarize(m, u):
    zo, uo, to = m.profile(u, "outer")
    zi, ui, ti = m.profile(u, "inner")
    zmo, Mo = m.moments(u, "outer")
    zmi, Mi = m.moments(u, "inner")
    below = zmo <= 1e-9
    Mtot = Mo.copy()
    Mtot[below] += np.interp(zmo[below], zmi, Mi)
    k = np.argmax(np.abs(Mtot * below))
    iwh = np.argmin(np.abs(zi - Z_WH))
    return dict(zo=zo, uo=uo, to=to, zi=zi, ui=ui, ti=ti, zmo=zmo, Mo=Mo, zmi=zmi, Mi=Mi, Mtot=Mtot,
                Mpeak=float(Mtot[k]), zpeak=float(zmo[k]), u_wh=float(ui[iwh]), th_wh=float(ti[iwh]),
                M_mud=float(np.interp(0.0, zmo, Mtot)), u_mud=float(np.interp(0.0, zo, uo)))


def r(a, n=5):
    return np.round(np.asarray(a, float), n).tolist()


# ---------------------------------------------------------------- 1. base case
soil = Soil()
m = Model(soil, le_top=0.25, shoulder=SHOULDER)
u, hist = m.solve(H_BASE, nsteps=12)
s = summarize(m, u)
st = m.spring_state(u)
base = dict(zo=r(s["zo"]), uo=r(s["uo"], 6), zi=r(s["zi"]), ui=r(s["ui"], 6), zmo=r(s["zmo"]),
            Mo=r(s["Mo"], 0), zmi=r(s["zmi"]), Mi=r(s["Mi"], 0), Mtot=r(s["Mtot"], 0),
            Mpeak=s["Mpeak"], zpeak=s["zpeak"], u_wh=s["u_wh"], th_wh=s["th_wh"], M_mud=s["M_mud"],
            u_mud=s["u_mud"],
            springs=[dict(z=q["z"], p=q["p"], pu=q["pu"], mob=q["mob"], y=q["y"]) for q in st])
steps = []
for k, uh in enumerate(hist):
    sk = summarize(m, uh)
    stk = m.spring_state(uh)
    steps.append(dict(H=H_BASE * (k + 1) / len(hist), uo=r(sk["uo"], 6), ui=r(sk["ui"], 6),
                      Mtot=r(sk["Mtot"], 0), Mi=r(sk["Mi"], 0), mob=r([q["mob"] for q in stk], 3),
                      p=r([q["p"] for q in stk], 0)))
base["steps"] = steps
out["base"] = base
print(f"BASE: u_wh={s['u_wh'] * 1e3:.1f} mm th_wh={np.degrees(s['th_wh']):.3f} deg "
      f"M_mud={s['M_mud'] / 1e6:.2f} MNm Mpeak={s['Mpeak'] / 1e6:.2f} at z={s['zpeak']:.2f}, "
      f"springs at pu: {sum(q['mob'] > 0.99 for q in st)} max mob {max(q['mob'] for q in st):.2f}")
# p-y curves at selected depths for plotting
curves = []
for X in [0.5, 2.0, 5.0, 10.0, 20.0]:
    y, p = soil.curve(X)
    yc = 2.5 * soil.eps50 * soil.D
    ys = np.linspace(0, 10 * yc, 120)
    curves.append(dict(X=X, table_y=r(y), table_p=r(p, 0), y=r(ys), p=r(matlock_smooth(ys, yc, soil.pu(X)), 0),
                       pu=soil.pu(X)))
out["py_curves"] = curves
out["soil"] = dict(su0=soil.su0, k_su=soil.k_su, gamma=soil.gamma, eps50=soil.eps50, J=soil.J,
                   XR=soil.XR(), yc=2.5 * soil.eps50 * soil.D)
cyc = Soil(cyclic=True)
curves_c = []
for X in [2.0, 10.0]:
    y, p = cyc.curve(X)
    curves_c.append(dict(X=X, table_y=r(y), table_p=r(p, 0)))
out["py_curves_cyclic"] = curves_c

# ---------------------------------------------------------------- 2. mesh study
mesh = []
for le in [4.0, 2.0, 1.0, 0.5, 0.25]:
    mm = Model(soil, uniform=le, shoulder=SHOULDER)
    uu, _ = mm.solve(H_BASE, nsteps=12)
    ss = summarize(mm, uu)
    zmo, Mo = mm.moments(uu, "outer")
    mesh.append(dict(le=le, Mpeak=ss["Mpeak"], zpeak=ss["zpeak"], u_wh=ss["u_wh"], th_wh=ss["th_wh"],
                     zmo=r(ss["zmo"]), Mtot=r(ss["Mtot"], 0)))
    print(f"MESH le={le}: Mpeak={ss['Mpeak'] / 1e6:.3f} at {ss['zpeak']:.2f}, u_wh={ss['u_wh'] * 1e3:.2f} mm")
ref = mesh[-1]
for q in mesh:
    q["err_M"] = (q["Mpeak"] - ref["Mpeak"]) / ref["Mpeak"]
    q["err_u"] = (q["u_wh"] - ref["u_wh"]) / ref["u_wh"]
out["mesh"] = mesh

# ---------------------------------------------------------------- 3. fixed at mudline
mf = Model(soil, fixed_mudline=True, shoulder=SHOULDER)
uf, _ = mf.solve(H_BASE, nsteps=4)
sf = summarize(mf, uf)
out["fixed"] = dict(zo=r(sf["zo"]), uo=r(sf["uo"], 6), zi=r(sf["zi"]), ui=r(sf["ui"], 6), u_wh=sf["u_wh"],
                    th_wh=sf["th_wh"], M_mud=sf["M_mud"], zmo=r(sf["zmo"]), Mtot=r(sf["Mtot"], 0))
print(f"FIXED: u_wh={sf['u_wh'] * 1e3:.1f} mm ({100 * (sf['u_wh'] / s['u_wh'] - 1):.0f}%), "
      f"th_wh={np.degrees(sf['th_wh']):.3f} ({100 * (sf['th_wh'] / s['th_wh'] - 1):.0f}%)")

# ---------------------------------------------------------------- 4. soil bounds
bounds = {}
for name, f, e50 in [("LB", 0.6, 0.02), ("BE", 1.0, 0.01), ("UB", 1.5, 0.005)]:
    sl = Soil(su0=3e3 * f, k_su=1.5e3 * f, eps50=e50)
    mb = Model(sl, shoulder=SHOULDER)
    ub, _ = mb.solve(H_BASE, nsteps=12)
    sb = summarize(mb, ub)
    bounds[name] = dict(zo=r(sb["zo"]), uo=r(sb["uo"], 6), zmo=r(sb["zmo"]), Mtot=r(sb["Mtot"], 0),
                        Mpeak=sb["Mpeak"], zpeak=sb["zpeak"], u_wh=sb["u_wh"], th_wh=sb["th_wh"])
    print(f"{name}: Mpeak={sb['Mpeak'] / 1e6:.2f} at z={sb['zpeak']:.2f}, u_wh={sb['u_wh'] * 1e3:.0f} mm")
out["bounds"] = bounds

# ---------------------------------------------------------------- 5. static vs cyclic
mc = Model(Soil(cyclic=True), shoulder=SHOULDER)
uc, _ = mc.solve(H_BASE, nsteps=12)
sc = summarize(mc, uc)
out["cyclic"] = dict(zmo=r(sc["zmo"]), Mtot=r(sc["Mtot"], 0), Mpeak=sc["Mpeak"], zpeak=sc["zpeak"],
                     u_wh=sc["u_wh"], zo=r(sc["zo"]), uo=r(sc["uo"], 6))
print(f"CYCLIC: Mpeak={sc['Mpeak'] / 1e6:.2f} at {sc['zpeak']:.2f}, u_wh={sc['u_wh'] * 1e3:.0f} mm")

# ---------------------------------------------------------------- 6. template gap & load sharing
Hs = np.linspace(0, 250e3, 26)[1:]
sweep = dict(H=r(Hs, 0), free=[], gap=[], tied=[])
for label, law in [("free", None), ("gap", Gap(GAP, K_TEMPLATE)), ("tied", Linear(K_TEMPLATE))]:
    mt = Model(soil, shoulder=SHOULDER, template=law)
    uprev = None
    for H in Hs:
        ut, _ = mt.solve(H, nsteps=6)
        stt = summarize(mt, ut)
        R = mt.spring_force(ut, "template")
        Rt = float(R[0]) if R else 0.0
        i2 = int(np.argmin(np.abs(stt["zo"] - Z_TEMPLATE)))
        sweep[label].append(dict(R=Rt, M_mud=stt["M_mud"], Mpeak=stt["Mpeak"], u_lp=float(stt["uo"][i2]),
                                 u_wh=stt["u_wh"]))
    print(label, "H=150:", [round(q["R"] / 1e3), round(q["M_mud"] / 1e6, 2)] if (q := sweep[label][14]) else "")
out["template_sweep"] = sweep
# gap closes at
g = sweep["gap"]
Hc = None
for H, q in zip(Hs, g):
    if q["R"] > 1.0:
        Hc = H
        break
out["gap_close_H"] = Hc
print("gap closes at H ~", Hc)
# deformed profiles for the gap case at the base load
mt = Model(soil, shoulder=SHOULDER, template=Gap(GAP, K_TEMPLATE))
ut, hist_t = mt.solve(H_BASE, nsteps=12)
stt = summarize(mt, ut)
out["template_base"] = dict(zo=r(stt["zo"]), uo=r(stt["uo"], 6), zi=r(stt["zi"]), ui=r(stt["ui"], 6),
                            zmo=r(stt["zmo"]), Mtot=r(stt["Mtot"], 0), R=float(mt.spring_force(ut, "template")[0]),
                            steps=[dict(uo=r(summarize(mt, h)["uo"], 6), ui=r(summarize(mt, h)["ui"], 6),
                                        R=float(mt.spring_force(h, "template")[0])) for h in hist_t])

# ---------------------------------------------------------------- 7. hand-calculation check
# single beam (conductor + casing EI), linear springs, load H0, M0 at the mudline;
# compare with Hetenyi's semi-infinite beam on elastic foundation.
EI = EI_COND + EI_CAS
k = 4.0e6  # N/m per m
lam = (k / (4 * EI)) ** 0.25
H0, M0 = H_BASE, H_BASE * (Z_LOAD - 0.0)
y0 = 2 * H0 * lam / k + 2 * M0 * lam ** 2 / k
# FE: uniform 0.25 m beam with linear springs
n = 241
z = np.linspace(0, -60, n)
L = z[0] - z[1]
Kb = np.zeros((2 * n, 2 * n))
for i in range(n - 1):
    ke = EI / L ** 3 * np.array([[12, 6 * L, -12, 6 * L], [6 * L, 4 * L ** 2, -6 * L, 2 * L ** 2],
                                 [-12, -6 * L, 12, -6 * L], [6 * L, 2 * L ** 2, -6 * L, 4 * L ** 2]])
    d = [2 * i, 2 * i + 1, 2 * i + 2, 2 * i + 3]
    Kb[np.ix_(d, d)] += ke
for i in range(n):
    trib = L * (0.5 if i in (0, n - 1) else 1.0)
    Kb[2 * i, 2 * i] += k * trib
F = np.zeros(2 * n)
F[0] = H0
F[1] = -M0  # sign: moment pushing the top in +x for the beam oriented downwards
ub = np.linalg.solve(Kb, F)
out["handcalc"] = dict(k=k, lam=lam, Lc=1 / lam, y0_hetenyi=y0, y0_fe=float(ub[0]),
                       diff=float(abs(ub[0] - y0) / y0))
print(f"HAND CALC: Hetenyi y0={y0 * 1e3:.2f} mm, FE {ub[0] * 1e3:.2f} mm, 1/lambda={1 / lam:.2f} m")

# ---------------------------------------------------------------- 8. coupled vs uncoupled springs
out["uncoupled"] = dict(small=2 ** (1 / 3), ultimate=np.sqrt(2))
# characteristic length using a secant modulus of the BE curve at 2 m depth, y = y50
with open("/home/user/Mesh/video/data/global.json", "w") as fh:
    json.dump(out, fh)
print("written")
