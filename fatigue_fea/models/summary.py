"""Collect the key results of all analyses into results/summary.json and print a table."""
import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
from fem.fatigue import coffin_manson_life, neuber, glinka, transition_life
from fem.materials_lib import RO, STRAIN_LIFE as SL

RES = os.path.join(os.path.dirname(__file__), "..", "results")
KT = 3.249
out = {"material": {"cyclic_RO": RO, "strain_life": SL,
                    "transition_life_cycles": transition_life(SL["E"], SL["sf"], SL["b"], SL["ef"], SL["c"])}}

plate = {}
for case in ["hcf", "shake", "lcf", "ratchet_m", "tm_shake", "tm_altpl", "tm_ratchet"]:
    fn = os.path.join(RES, f"plate_{case}.npz")
    if not os.path.exists(fn):
        continue
    d = np.load(fn)
    meta = json.loads(str(d["meta"]))
    cyc = d["T_cycle"]
    last = cyc == cyc.max()
    s, e = d["T_root_syy"][last], d["T_root_eyy"][last]
    smax, smin, emax, emin = s.max(), s.min(), e.max(), e.min()
    ea = 0.5 * (emax - emin)
    sm = 0.5 * (smax + smin)
    root = int(d["probes"][0])
    peeq_eoc = d["EOC_peeq"][:, root]
    uy = d["T_uy_top"][d["T_end_of_cycle"]]
    r = dict(cfg=meta["cfg"], runtime_s=meta["runtime_s"], n_cycles=int(cyc.max()),
             notch_root_last_cycle=dict(sigma_max=float(smax), sigma_min=float(smin), sigma_mean=float(sm),
                                        eps_amp_pct=float(ea * 100), eps_mean_pct=float(0.5 * (emax + emin) * 100)),
             peeq_root_end_of_cycles_pct=[float(x * 100) for x in peeq_eoc],
             peeq_increment_last_cycle_pct=float((peeq_eoc[-1] - peeq_eoc[-2]) * 100) if len(peeq_eoc) > 1 else None,
             plate_end_disp_end_of_cycles_um=[float(x * 1000) for x in uy],
             ratchet_per_cycle_last_um=float((uy[-1] - uy[-2]) * 1000) if len(uy) > 1 else None)
    if meta["cfg"]["kind"] == "mech":
        r["life_coffin_manson"] = coffin_manson_life(ea, SL["E"], SL["sf"], SL["b"], SL["ef"], SL["c"])
        r["life_morrow"] = coffin_manson_life(ea, SL["E"], SL["sf"], SL["b"], SL["ef"], SL["c"], sigma_m=sm, method="morrow")
        r["life_swt"] = coffin_manson_life(ea, SL["E"], SL["sf"], SL["b"], SL["ef"], SL["c"], method="swt", smax=smax)
        Sa = 0.5 * (d["T_S"][last].max() - d["T_S"][last].min())
        ds, de = neuber(KT, 2 * Sa, RO["E"], RO["Kp"], RO["nprime"], branch=True)
        gs, ge = glinka(KT, 2 * Sa, RO["E"], RO["Kp"], RO["nprime"], branch=True)
        r["neuber_eps_amp_pct"] = de / 2 * 100
        r["glinka_eps_amp_pct"] = ge / 2 * 100
    plate[case] = r
out["plate_with_hole"] = plate

w = os.path.join(RES, "weld_tjoint.npz")
if os.path.exists(w):
    out["weld_t_joint"] = json.loads(str(np.load(w)["meta"]))
b = os.path.join(RES, "bree_map.npz")
if os.path.exists(b):
    d = np.load(b)
    out["bree_map"] = dict(points=int(d["cls"].size), agreement_with_Bree=float(np.mean(d["cls"] == d["ana"])))
json.dump(out, open(os.path.join(RES, "summary.json"), "w"), indent=1, default=float)

print(f"{'case':11s} {'sig_max':>8s} {'sig_min':>8s} {'eps_a %':>8s} {'dPEEQ/cyc %':>11s} {'ratchet um/cyc':>14s} {'N (C-M)':>10s}")
for k, r in plate.items():
    nr = r["notch_root_last_cycle"]
    N = r.get("life_coffin_manson")
    print(f"{k:11s} {nr['sigma_max']:8.1f} {nr['sigma_min']:8.1f} {nr['eps_amp_pct']:8.4f} "
          f"{(r['peeq_increment_last_cycle_pct'] or 0):11.4f} {(r['ratchet_per_cycle_last_um'] or 0):14.3f} "
          f"{(f'{N:10.3g}' if N else '         -')}")
if "bree_map" in out:
    print("Bree map agreement:", out["bree_map"])
