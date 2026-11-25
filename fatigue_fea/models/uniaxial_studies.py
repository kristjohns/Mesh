"""Material-point studies used in the video:
 1. strain-controlled hysteresis loops at several amplitudes (cyclic curve / Masing)
 2. stress-controlled cycling with a mean stress: ratcheting predicted by
    linear kinematic (Prager), single Armstrong-Frederick and multi-component Chaboche
 3. a variable-amplitude strain history at a notch root (rainflow + Miner demo)
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
from fem.material import J2Material
from fem.materials_lib import s355_chaboche, s355_prager, RO, STRAIN_LIFE as SL
from fem.matpoint import uniaxial, triangle_wave
from fem.fatigue import rainflow, coffin_manson_life, turning_points

RES = os.path.join(os.path.dirname(__file__), "..", "results")
out = {}

# 1. loops
mat = s355_chaboche()
for ea in [0.002, 0.004, 0.008]:
    h = triangle_wave(ea, 3, nper_quarter=80)
    r = uniaxial(mat, h, control="strain")
    out[f"loop_{int(ea*1e4)}_eps"] = r["eps11"]
    out[f"loop_{int(ea*1e4)}_sig"] = r["sig11"]

# 2. ratcheting with three hardening rules (same proportional limit, similar loop shape)
af1 = J2Material(E=210000, nu=0.3, sigma0=250.0, C=[60000.0], gamma=[300.0], name="Armstrong-Frederick")
mats = {"prager": s355_prager(), "af": af1, "chaboche": s355_chaboche()}
for k, mt in mats.items():
    h = triangle_wave(300.0, 15, nper_quarter=60, mean=60.0)
    r = uniaxial(mt, h, control="stress")
    out[f"rat_{k}_eps"] = r["eps11"]
    out[f"rat_{k}_sig"] = r["sig11"]
    out[f"rat_{k}_p"] = r["p"]
    per = 240
    eoc = r["eps11"][per - 1::per]
    print(f"{mt.name:26s}: strain at end of cycles 1,5,15 = {eoc[0]*100:.3f}, {eoc[4]*100:.3f}, {eoc[-1]*100:.3f} %")

# 3. variable amplitude notch-root strain history (synthetic, narrow-band)
rng = np.random.default_rng(7)
n = 400
t = np.arange(n)
env = 0.0022 * (0.55 + 0.45 * np.sin(2 * np.pi * t / 160.0) ** 2)
x = env * np.sin(2 * np.pi * t / 9.7 + rng.normal(0, 0.25, n).cumsum() * 0.15) + rng.normal(0, 0.0002, n)
tp = turning_points(x)
cyc = rainflow(tp)
D = 0.0
for rng_, mean, cnt in cyc:
    ea = rng_ / 2
    if ea > 0:
        D += cnt / coffin_manson_life(ea, SL["E"], SL["sf"], SL["b"], SL["ef"], SL["c"])
print(f"variable amplitude block: {len(tp)} turning points, {len(cyc)} rainflow (half-)cycles, Miner damage per block = {D:.3e} -> blocks to failure = {1/D:.0f}")
out["va_x"] = x
out["va_tp"] = tp
out["va_cycles"] = np.array(cyc)
np.savez_compressed(os.path.join(RES, "uniaxial_studies.npz"), **out)
