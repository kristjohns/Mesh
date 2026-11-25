"""
Bree problem: thin cylinder wall under constant pressure (primary membrane stress)
and cyclic through-wall linear temperature gradient (secondary stress).

Through-wall "fibre" discretisation (1-D finite elements in the wall thickness),
uniaxial hoop stress, total strain uniform through the wall (no bending), equilibrium
    mean(sigma_i) = X * sy
Thermal: free thermal strain alpha*T(y), T linear through the wall, so the elastic
thermal stress at the wall surfaces is +/- Y*sy.
Normalised units: sy = 1, E = 1.

Material: elastic-perfectly plastic (Bree's assumption) or linear kinematic.
Vectorised over a batch of (X, Y) load points.
"""
import numpy as np


def simulate(Xs, Ys, ncyc=20, ninc=24, nfib=120, H_kin=0.0, record=None):
    """Xs, Ys: 1-D arrays (batch). Returns dict of metrics; if record is an int
    index, also returns the full history for that batch member."""
    Xs = np.asarray(Xs, float)[:, None]
    Ys = np.asarray(Ys, float)[:, None]
    nb = Xs.shape[0]
    y = (np.arange(nfib) + 0.5) / nfib - 0.5           # fibre positions, -1/2..1/2
    ep = np.zeros((nb, nfib))                           # plastic strain
    al = np.zeros((nb, nfib))                           # back-stress (kinematic)
    eps = np.zeros(nb)
    hist = {"lam": [], "eps": [], "sig": [], "ep": [], "cycle": []}

    def solve(lam):
        nonlocal ep, al, eps
        eth = lam * 2.0 * Ys * y[None, :]               # thermal strain (norm.)
        # exact bracket: sigma_i = clip(eps - c_i) with c_i = ep_i + eth_i (+ back-stress)
        cc = ep + eth
        margin = 2.0 + (np.max(np.abs(al), axis=1) if H_kin > 0 else 0.0)
        lo = cc.min(axis=1) - margin
        hi = cc.max(axis=1) + margin
        # bisection on the uniform strain (monotone equilibrium)
        for _ in range(64):
            mid = 0.5 * (lo + hi)
            s_tr = mid[:, None] - ep - eth
            if H_kin == 0.0:
                s = np.clip(s_tr, -1.0, 1.0)
            else:
                xi = s_tr - al
                over = np.maximum(np.abs(xi) - 1.0, 0.0)
                dep = np.sign(xi) * over / (1.0 + H_kin)
                s = s_tr - dep
            g = s.mean(axis=1) - Xs[:, 0]
            hi = np.where(g > 0, mid, hi)
            lo = np.where(g > 0, lo, mid)
        e = 0.5 * (lo + hi)
        s_tr = e[:, None] - ep - eth
        if H_kin == 0.0:
            s = np.clip(s_tr, -1.0, 1.0)
            ep = e[:, None] - eth - s
        else:
            xi = s_tr - al
            over = np.maximum(np.abs(xi) - 1.0, 0.0)
            dep = np.sign(xi) * over / (1.0 + H_kin)
            s = s_tr - dep
            ep = ep + dep
            al = al + H_kin * dep
        eps = e
        return s

    # primary load with no thermal gradient
    s = solve(0.0)
    plastic_first = np.zeros(nb, bool)
    eps_eoc = [eps.copy()]
    ep_min = np.full((nb, nfib), np.inf)
    ep_max = np.full((nb, nfib), -np.inf)
    ep_prev_cycle_end = ep.copy()
    dep_last = None
    lam_path = np.concatenate([np.linspace(0, 1, ninc + 1)[1:], np.linspace(1, 0, ninc + 1)[1:]])
    for c in range(1, ncyc + 1):
        ep_min[:] = ep
        ep_max[:] = ep
        for lam in lam_path:
            s = solve(lam)
            ep_min = np.minimum(ep_min, ep)
            ep_max = np.maximum(ep_max, ep)
            if record is not None:
                hist["lam"].append(lam)
                hist["eps"].append(eps[record])
                hist["sig"].append(s[record].copy())
                hist["ep"].append(ep[record].copy())
                hist["cycle"].append(c)
        if c == 1:
            plastic_first = np.any(np.abs(ep) > 1e-12, axis=1)
        eps_eoc.append(eps.copy())
        dep_last = ep - ep_prev_cycle_end
        ep_prev_cycle_end = ep.copy()
    eps_eoc = np.array(eps_eoc)                         # (ncyc+1, nb)
    ratchet = eps_eoc[-1] - eps_eoc[-2]
    prange = np.max(ep_max - ep_min, axis=1)           # plastic strain range last cycle
    out = dict(ratchet_per_cycle=ratchet, plastic_range_last=prange,
               plastic_first=plastic_first, eps_eoc=eps_eoc, y=y)
    if record is not None:
        out["hist"] = {k: np.array(v) for k, v in hist.items()}
    return out


def classify(res, tol=1e-6):
    """0 elastic, 1 shakedown, 2 alternating plasticity, 3 ratcheting."""
    r = np.abs(res["ratchet_per_cycle"])
    pr = res["plastic_range_last"]
    cls = np.full(r.shape, 1)
    cls[~res["plastic_first"]] = 0
    cls[(pr > tol) & (r <= tol)] = 2
    cls[r > tol] = 3
    return cls


def bree_boundaries():
    """Analytical Bree (1967) boundaries for an EPP material, returned as polylines in (X, Y)."""
    X1 = np.linspace(0.0, 1.0, 200)
    elastic = (X1, 1.0 - X1)
    Xa = np.linspace(0.5, 1.0, 100)
    ratchet_R1 = (Xa, 4.0 * (1.0 - Xa))
    Yb = np.linspace(2.0, 4.0, 100)
    ratchet_R2 = (1.0 / Yb, Yb)
    plast = (np.array([0.0, 0.5]), np.array([2.0, 2.0]))
    return dict(elastic=elastic, ratchet_R1=ratchet_R1, ratchet_R2=ratchet_R2, plastic=plast)
