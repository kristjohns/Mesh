"""Compute the Bree regime map numerically with the through-wall fibre model and
compare with Bree's analytical boundaries. Saves results/bree_map.npz"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
from fem.bree import simulate, classify, bree_boundaries

RES = os.path.join(os.path.dirname(__file__), "..", "results")

nx, ny = 81, 81
xs = np.linspace(0.0125, 0.9875, nx)
ys = np.linspace(0.025, 3.975, ny)
XX, YY = np.meshgrid(xs, ys)
res = simulate(XX.ravel(), YY.ravel(), ncyc=24, ninc=20, nfib=160)
cls = classify(res, tol=1e-5).reshape(ny, nx)
rat = res["ratchet_per_cycle"].reshape(ny, nx)
prange = res["plastic_range_last"].reshape(ny, nx)

# check against analytical prediction
def bree_class(X, Y):
    if X + Y <= 1.0:
        return 0
    rat = (Y <= 2.0 and X + Y / 4.0 > 1.0) or (Y > 2.0 and X * Y > 1.0)
    if rat:
        return 3
    return 2 if Y > 2.0 else 1
ana = np.vectorize(bree_class)(XX, YY)
agree = np.mean(ana == cls)
print(f"Bree map: {nx*ny} load points, agreement with analytical regimes = {agree*100:.1f} %")
mis = np.argwhere(ana != cls)
print("disagreeing points (near boundaries):", len(mis))

# three representative histories for animation
reps = {"S": (0.4, 1.2), "P": (0.25, 3.0), "R1": (0.75, 1.6), "R2": (0.5, 3.0), "E": (0.3, 0.5)}
hist = {}
for k, (X, Y) in reps.items():
    r = simulate([X], [Y], ncyc=6, ninc=30, nfib=160, record=0)
    hist[k] = r["hist"]
    print(f"{k}: X={X}, Y={Y}: ratchet/cycle={r['ratchet_per_cycle'][0]:.4f} (eps_y units), plastic range={r['plastic_range_last'][0]:.4f}")
os.makedirs(RES, exist_ok=True)
save = dict(xs=xs, ys=ys, cls=cls, ana=ana, ratchet=rat, prange=prange, y=res["y"])
for k, h in hist.items():
    for kk, v in h.items():
        save[f"h_{k}_{kk}"] = v
    save[f"h_{k}_XY"] = np.array(reps[k])
for k, (bx, by) in bree_boundaries().items():
    save[f"b_{k}_x"], save[f"b_{k}_y"] = bx, by
np.savez_compressed(os.path.join(RES, "bree_map.npz"), **save)
