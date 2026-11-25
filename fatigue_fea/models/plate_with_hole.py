"""
Plate with a central hole (quarter model, plane stress) - cyclic elastic-plastic FE study.

Geometry: width W = 80 mm, hole d = 20 mm (d/W = 0.25), length 200 mm, t = 1 (per unit thickness).
Kt (gross) = 3.25, Kt (net) = 2.44 from linear-elastic FE.

Mechanical load cases (S355-type steel, Chaboche nonlinear kinematic hardening):
  hcf      : S = +/-70 MPa,  R = -1   -> elastic everywhere            (HCF, stress-life)
  shake    : S = 0..140 MPa, R = 0    -> yield in cycle 1, then elastic (elastic shakedown)
  lcf      : S = +/-180 MPa, R = -1   -> reversed plasticity at the notch (LCF, strain-life)
  ratchet_m: S = 0..285 MPa, R = 0    -> net-section plasticity + mean load -> material ratcheting

Thermo-mechanical cases (elastic-perfectly-plastic, sy = 355 MPa, as used for code ratcheting checks):
  constant primary tension S + cyclic "tent" temperature field T = lam(t) dT (1 - x/B)
  X = S_net / sy,   Y = E alpha dT / (2 sy)   (Bree-type parameters)
  tm_shake  : X = 0.30, Y = 1.5
  tm_altpl  : X = 0.25, Y = 2.5
  tm_ratchet: X = 0.50, Y = 2.5

Usage:  python models/plate_with_hole.py <case> [--coarse] [--ncyc N]
"""
import os, sys, time, argparse, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
from fem.mesh import plate_with_hole, element_edges_on
from fem.solver import FEModel2D, run_history
from fem.materials_lib import s355_chaboche, s355_epp
from fem.runner import CyclicRecorder, build_steps, triangle

RES = os.path.join(os.path.dirname(__file__), "..", "results")
SY, E, ALPHA = 355.0, 210000.0, 12e-6
NET = 0.75   # net / gross area ratio

CASES = {
    "hcf":       dict(kind="mech", mat="chaboche", lo=-70.0,  hi=70.0,  R=-1, ncyc=6),
    "shake":     dict(kind="mech", mat="chaboche", lo=0.0,    hi=140.0, R=0,  ncyc=12),
    "lcf":       dict(kind="mech", mat="chaboche", lo=-180.0, hi=180.0, R=-1, ncyc=12),
    "ratchet_m": dict(kind="mech", mat="chaboche", lo=0.0,    hi=285.0, R=0,  ncyc=12),
    "tm_shake":  dict(kind="tm", mat="epp", X=0.30, Y=1.5, ncyc=12),
    "tm_altpl":  dict(kind="tm", mat="epp", X=0.25, Y=2.5, ncyc=12),
    "tm_ratchet": dict(kind="tm", mat="epp", X=0.50, Y=2.5, ncyc=12),
}


def make_mesh(coarse=False):
    if coarse:
        return plate_with_hole(a=10, B=40, H=100, n_rad=18, n_ang=14, n_top=14)
    return plate_with_hole(a=10, B=40, H=100, n_rad=24, n_ang=18, n_top=16)


def run_case(name, coarse=False, ncyc=None, ninc_half=20, field_cycles=(1, 2, 3), verbose=True):
    cfg = dict(CASES[name])
    if ncyc is not None:
        cfg["ncyc"] = ncyc
    mesh = make_mesh(coarse)
    mat = s355_chaboche() if cfg["mat"] == "chaboche" else s355_epp()
    m = FEModel2D(mesh, mat, "plane_stress", 1.0)
    m.fix(mesh.sets["x0"], 0)
    m.fix(mesh.sets["y0"], 1)
    f1 = m.edge_load_vector(element_edges_on(mesh, mesh.sets["top"]), (0.0, 1.0))
    X, Y = mesh.nodes.T
    root = int(np.argmin(np.hypot(X - 10, Y)))
    top90 = int(np.argmin(np.hypot(X, Y - 10)))          # hole edge at 90 deg
    edge = int(np.argmin(np.hypot(X - 40, Y)))           # free edge on the ligament
    probes = {"root": root, "top90": top90, "edge": edge}
    ncyc = cfg["ncyc"]
    n_per = 2 * ninc_half

    if cfg["kind"] == "mech":
        lo, hi = cfg["lo"], cfg["hi"]
        if cfg["R"] == -1:
            S_fun = lambda tc: triangle(tc, lo, hi, start="mid")
        else:
            S_fun = lambda tc: triangle(tc, lo, hi, start="lo")
        steps = build_steps(S_fun, lambda tc: 0.0, ncyc, ninc_half, f1)
        Tn = None
        pre = 0
    else:
        S = cfg["X"] * SY * NET
        dT = cfg["Y"] * 2 * SY / (E * ALPHA)
        Tn = 1.0 - X / 40.0
        Tg = m.nodal_to_gauss(Tn) * dT
        pre = 10
        steps = build_steps(lambda tc: S, lambda tc: triangle(tc, 0.0, 1.0), ncyc, ninc_half, f1, Tg,
                            preload=(S, pre))
        cfg["S"], cfg["dT"] = S, dT
    # field steps: every increment of the chosen cycles and of the last cycle
    fsteps = set()
    for c in list(field_cycles) + [ncyc]:
        start = pre + (c - 1) * n_per
        fsteps.update(range(start - (1 if c == 1 and pre == 0 else 0), start + n_per))
    fsteps.update(range(pre))
    fsteps = {s for s in fsteps if s >= 0}
    rec = CyclicRecorder(m, probes, field_steps=fsteps, end_of_cycle_fields=True,
                         top_nodes=mesh.sets["top"], right_nodes=mesh.sets["right"])
    t0 = time.time()
    _, _, nit = run_history(m, steps, callback=rec, verbose=verbose)
    dt = time.time() - t0
    tb = rec.table()
    # pack fields
    fkeys = sorted(rec.fields)
    names = list(next(iter(rec.fields.values())).keys())
    out = {f"T_{k}": v for k, v in tb.items()}
    for nm in names:
        out[f"F_{nm}"] = np.stack([rec.fields[s][nm] for s in fkeys])
        out[f"EOC_{nm}"] = np.stack([rec.eoc_fields[c][nm] for c in sorted(rec.eoc_fields)])
    out["F_steps"] = np.array(fkeys)
    out["EOC_cycles"] = np.array(sorted(rec.eoc_fields))
    out["nodes"] = mesh.nodes
    out["elems"] = mesh.elems
    out["probes"] = np.array([root, top90, edge])
    if Tn is not None:
        out["T_unit"] = Tn
    meta = dict(case=name, cfg=cfg, coarse=coarse, ninc_half=ninc_half, ncyc=ncyc, pre=pre,
                ne=mesh.ne, nn=mesh.nn, runtime_s=dt, newton_iterations=int(nit),
                material=mat.name)
    out["meta"] = np.array(json.dumps(meta))
    os.makedirs(RES, exist_ok=True)
    fn = os.path.join(RES, f"plate_{name}{'_coarse' if coarse else ''}.npz")
    np.savez_compressed(fn, **out)
    if verbose:
        eoc_u = tb["uy_top"][tb["end_of_cycle"]]
        print(f"[{name}] done in {dt:.0f}s, {nit} Newton its; uy_top end-of-cycle: {np.round(eoc_u, 4)}")
        print(f"[{name}] root PEEQ end-of-cycle: {np.round(out['EOC_peeq'][:, root] * 100, 4)} %")
    return fn


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("case")
    ap.add_argument("--coarse", action="store_true")
    ap.add_argument("--ncyc", type=int, default=None)
    ap.add_argument("--ninc", type=int, default=20)
    a = ap.parse_args()
    run_case(a.case, coarse=a.coarse, ncyc=a.ncyc, ninc_half=a.ninc)
