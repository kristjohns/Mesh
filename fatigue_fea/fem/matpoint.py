"""
Single material point driver (uniaxial stress state) for J2Material.

Mixed control: the axial component is either strain- or stress-controlled,
all other stress components are zero (sigma22 = sigma33 = sigma12 = 0).
"""
import numpy as np
from .material import J2Material


def uniaxial(mat: J2Material, history, control="strain", tol=1e-9, maxit=50):
    """history: 1D array of axial strain (control='strain') or axial stress
    (control='stress') values, applied sequentially (each value one increment).
    Returns dict with arrays eps11, sig11, p, epsp11."""
    st = mat.new_state(1)
    eps = np.zeros((1, 4))
    out = {"eps11": [], "sig11": [], "p": [], "epsp11": []}
    for target in history:
        if control == "strain":
            eps[0, 0] = target
            free = [1, 2]
        else:
            free = [0, 1, 2]
        for it in range(maxit):
            sig, Ct, new, _ = mat.update(eps, st)
            r = sig[0].copy()
            if control == "stress":
                r[0] -= target
            r = r[free]
            if np.max(np.abs(r)) < tol * mat.sigma0:
                break
            Kff = Ct[0][np.ix_(free, free)]
            eps[0, free] -= np.linalg.solve(Kff, r)
        else:
            raise RuntimeError("material point driver did not converge")
        st = new
        out["eps11"].append(eps[0, 0])
        out["sig11"].append(sig[0, 0])
        out["p"].append(st["p"][0])
        out["epsp11"].append(st["eps_p"][0, 0])
    return {k: np.array(v) for k, v in out.items()}


def triangle_wave(amplitude, ncycles, nper_quarter=25, mean=0.0, start_at_mean=True):
    """0 -> +A -> -A -> +A ... sampled with nper_quarter points per quarter cycle."""
    q = np.linspace(0, 1, nper_quarter + 1)[1:]
    seg = [q, 1 - q, -q, -1 + q]
    one = np.concatenate(seg)
    wave = np.concatenate([one] * ncycles)
    return mean + amplitude * wave
