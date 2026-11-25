"""
Fatigue life toolkit: stress-life, strain-life, mean-stress corrections,
notch rules, rainflow counting and Palmgren-Miner damage.
"""
import numpy as np
from scipy.optimize import brentq


# ----------------------------------------------------------------- stress-life
def basquin_life(sigma_a, sf, b):
    """sigma_a = sf (2N)^b  ->  N (cycles)."""
    return 0.5 * (sigma_a / sf) ** (1.0 / b)


def goodman_equiv(sa, sm, su):
    return sa / (1 - sm / su)


def gerber_equiv(sa, sm, su):
    return sa / (1 - (sm / su) ** 2)


def soderberg_equiv(sa, sm, sy):
    return sa / (1 - sm / sy)


def swt_equiv_stress(sa, smax):
    return np.sqrt(np.maximum(smax, 0.0) * sa)


# ----------------------------------------------------------------- strain-life
def coffin_manson_life(eps_a, E, sf, b, ef, c, sigma_m=0.0, method="none", smax=None):
    """Solve for N (cycles). method: 'none' | 'morrow' | 'swt'."""
    def f(log2N):
        x = 10.0 ** log2N
        if method == "swt":
            return (sf ** 2 / E) * x ** (2 * b) + sf * ef * x ** (b + c) - smax * eps_a
        s_f = sf - (sigma_m if method == "morrow" else 0.0)
        return s_f / E * x ** b + ef * x ** c - eps_a
    try:
        l = brentq(f, -1.0, 12.0)
    except ValueError:
        return np.inf
    return 0.5 * 10.0 ** l


def transition_life(E, sf, b, ef, c):
    """2N_t where elastic and plastic strain amplitudes are equal -> returns N_t (cycles)."""
    return 0.5 * (ef * E / sf) ** (1.0 / (b - c))


def ramberg_osgood_strain(sig, E, Kp, nprime):
    return sig / E + (np.abs(sig) / Kp) ** (1.0 / nprime) * np.sign(sig)


# ----------------------------------------------------------------- notch rules
def neuber(Kt, S, E, Kp, nprime, branch=False):
    """Neuber: sigma*eps = (Kt S)^2 / E with the cyclic curve
    (branch=True uses the Masing hysteresis branch: ranges and factor 2)."""
    if branch:
        rhs = (Kt * S) ** 2 / E
        g = lambda ds: ds * (ds / E + 2 * (ds / (2 * Kp)) ** (1 / nprime)) - rhs
        ds = brentq(g, 1e-6, 5e3)
        return ds, ds / E + 2 * (ds / (2 * Kp)) ** (1 / nprime)
    rhs = (Kt * S) ** 2 / E
    g = lambda s: s * ramberg_osgood_strain(s, E, Kp, nprime) - rhs
    s = brentq(g, 1e-6, 5e3)
    return s, ramberg_osgood_strain(s, E, Kp, nprime)


def glinka(Kt, S, E, Kp, nprime, branch=False):
    """Glinka ESED: strain energy density at the notch equals the elastic value.
    W = s^2/(2E) + s/(n'+1) (s/K')^(1/n')."""
    if branch:
        rhs = (Kt * S) ** 2 / (2 * E)
        g = lambda ds: ds ** 2 / (2 * E) + ds / (nprime + 1) * 2 * (ds / (2 * Kp)) ** (1 / nprime) - rhs
        ds = brentq(g, 1e-6, 5e3)
        return ds, ds / E + 2 * (ds / (2 * Kp)) ** (1 / nprime)
    rhs = (Kt * S) ** 2 / (2 * E)
    g = lambda s: s ** 2 / (2 * E) + s / (nprime + 1) * (s / Kp) ** (1 / nprime) - rhs
    s = brentq(g, 1e-6, 5e3)
    return s, ramberg_osgood_strain(s, E, Kp, nprime)


# ----------------------------------------------------------------- rainflow
def turning_points(x):
    x = np.asarray(x, float)
    dx = np.diff(x)
    keep = np.concatenate([[True], (dx[1:] * dx[:-1]) < 0, [True]])
    tp = x[keep]
    # remove repeated values
    out = [tp[0]]
    for v in tp[1:]:
        if v != out[-1]:
            out.append(v)
    return np.array(out)


def rainflow(x):
    """ASTM E1049 rainflow counting. Returns list of (range, mean, count) with
    count 1.0 (full cycle) or 0.5 (half cycle)."""
    pts = list(turning_points(x))
    stack, cycles = [], []
    for p in pts:
        stack.append(p)
        while len(stack) >= 3:
            X = abs(stack[-1] - stack[-2])
            Y = abs(stack[-2] - stack[-3])
            if X < Y:
                break
            if len(stack) == 3:
                cycles.append((Y, 0.5 * (stack[-2] + stack[-3]), 0.5))
                stack.pop(0)
            else:
                cycles.append((Y, 0.5 * (stack[-2] + stack[-3]), 1.0))
                last = stack.pop()
                stack.pop(); stack.pop()
                stack.append(last)
    for i in range(len(stack) - 1):
        cycles.append((abs(stack[i + 1] - stack[i]), 0.5 * (stack[i + 1] + stack[i]), 0.5))
    return cycles


def miner_damage(cycles, life_fun):
    """cycles: list of (range, mean, count); life_fun(range, mean) -> N."""
    return sum(n / life_fun(r, m) for r, m, n in cycles if r > 0)


# ----------------------------------------------------------------- S-N curves for welds
DNV_D_AIR = dict(m1=3.0, loga1=12.164, m2=5.0, loga2=15.606, N_knee=1e7, k=0.20, t_ref=25.0)


def dnv_sn_life(dsigma, curve=DNV_D_AIR, t=None):
    """Two-slope DNV-RP-C203 S-N curve (in air). Thickness correction (t/t_ref)^k if t>t_ref."""
    ds = np.asarray(dsigma, float)
    if t is not None and t > curve["t_ref"]:
        ds = ds * (t / curve["t_ref"]) ** curve["k"]
    N1 = 10 ** (curve["loga1"] - curve["m1"] * np.log10(ds))
    N2 = 10 ** (curve["loga2"] - curve["m2"] * np.log10(ds))
    return np.where(N1 <= curve["N_knee"], N1, N2)
