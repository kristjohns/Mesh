"""
Rate-independent J2 (von Mises) cyclic plasticity, fully vectorised over material points.

Hardening
---------
* Nonlinear kinematic hardening (Chaboche, sum of Armstrong-Frederick back-stresses)
      d(alpha_i) = 2/3 C_i d(eps_p) - gamma_i alpha_i dp
  gamma_i = 0 gives linear (Prager) kinematic hardening.
* Nonlinear isotropic hardening (Voce)
      R(p) = Q_inf (1 - exp(-b p))
* Elastic-perfectly-plastic is obtained with C = [], Q_inf = 0.

Integration: fully implicit backward Euler with a scalar Newton iteration on the
plastic multiplier increment dp, and the algorithmically consistent tangent.

Tensor storage: Mandel notation for the 4 in-plane-problem components
    [11, 22, 33, sqrt(2)*12]
so that the double contraction is an ordinary dot product.
"""
import numpy as np

SQ2 = np.sqrt(2.0)
M_VEC = np.array([1.0, 1.0, 1.0, 0.0])           # identity tensor (Mandel)
I4 = np.eye(4)
P_DEV = I4 - np.outer(M_VEC, M_VEC) / 3.0        # deviatoric projector


class J2Material:
    def __init__(self, E=210000.0, nu=0.3, sigma0=355.0, C=(), gamma=(),
                 Q_inf=0.0, b_iso=0.0, alpha_th=12e-6, name="material"):
        self.E, self.nu = float(E), float(nu)
        self.G = E / (2.0 * (1.0 + nu))
        self.K = E / (3.0 * (1.0 - 2.0 * nu))
        self.lam = self.K - 2.0 * self.G / 3.0
        self.sigma0 = float(sigma0)
        self.C = np.atleast_1d(np.asarray(C, dtype=float))
        self.gamma = np.atleast_1d(np.asarray(gamma, dtype=float))
        assert self.C.shape == self.gamma.shape
        self.nback = self.C.size
        self.Q_inf, self.b_iso = float(Q_inf), float(b_iso)
        self.alpha_th = float(alpha_th)
        self.name = name
        self.Ce = self.K * np.outer(M_VEC, M_VEC) + 2.0 * self.G * P_DEV

    # ------------------------------------------------------------------ state
    def new_state(self, n):
        return {
            "eps_p": np.zeros((n, 4)),
            "alpha": np.zeros((n, max(self.nback, 1), 4)),
            "p": np.zeros(n),
        }

    def copy_state(self, st):
        return {k: v.copy() for k, v in st.items()}

    # ------------------------------------------------------------- hardening
    def R(self, p):
        return self.Q_inf * (1.0 - np.exp(-self.b_iso * p))

    def dR(self, p):
        return self.Q_inf * self.b_iso * np.exp(-self.b_iso * p)

    # -------------------------------------------------------- return mapping
    def update(self, eps, st, dT=None, want_tangent=True):
        """eps: (n,4) total strain (Mandel). st: state at t_n (not modified).
        dT: (n,) temperature change from the stress-free reference.
        Returns sigma (n,4), tangent (n,4,4), new state dict, plastic mask."""
        n = eps.shape[0]
        G, K = self.G, self.K
        eps_th = 0.0 if dT is None else (self.alpha_th * dT)[:, None] * M_VEC[None, :]
        ee_tr = eps - st["eps_p"] - eps_th
        sig_tr = ee_tr @ self.Ce.T
        s_tr = sig_tr @ P_DEV.T
        alpha_n = st["alpha"]                       # (n, nb, 4)
        a_sum = alpha_n.sum(axis=1)
        xi_tr = s_tr - a_sum
        q_tr = np.sqrt(1.5 * np.einsum("ij,ij->i", xi_tr, xi_tr))
        sy_n = self.sigma0 + self.R(st["p"])
        f_tr = q_tr - sy_n
        plastic = f_tr > 1e-10 * self.sigma0

        sig = sig_tr.copy()
        new = self.copy_state(st)
        Ct = np.broadcast_to(self.Ce, (n, 4, 4)).copy() if want_tangent else None

        if not np.any(plastic):
            return sig, Ct, new, plastic

        idx = np.nonzero(plastic)[0]
        s_t = s_tr[idx]
        al = alpha_n[idx]                           # (m, nb, 4)
        p_n = st["p"][idx]
        C, gam = self.C, self.gamma
        nb = self.nback

        # ---- scalar Newton for dp (vectorised over plastic points)
        Hsum0 = 3.0 * G + (C.sum() if nb else 0.0)
        dp = np.maximum(f_tr[idx] / (Hsum0 + self.dR(p_n)), 0.0)
        for it in range(60):
            if nb:
                beta = 1.0 / (1.0 + gam[None, :] * dp[:, None])            # (m, nb)
                xi_t = s_t - np.einsum("mk,mkj->mj", beta, al)
                a_vec = np.einsum("mk,mkj->mj", gam[None, :] * beta**2, al)
                Ht = 3.0 * G + (C[None, :] * beta).sum(axis=1)
                dHt = -(C[None, :] * gam[None, :] * beta**2).sum(axis=1)
            else:
                xi_t = s_t
                a_vec = np.zeros_like(s_t)
                Ht = np.full(dp.shape, 3.0 * G)
                dHt = np.zeros_like(dp)
            q_t = np.sqrt(1.5 * np.einsum("ij,ij->i", xi_t, xi_t))
            nvec = 1.5 * xi_t / q_t[:, None]
            F = q_t - Ht * dp - self.sigma0 - self.R(p_n + dp)
            dF = np.einsum("ij,ij->i", nvec, a_vec) - Ht - dp * dHt - self.dR(p_n + dp)
            step = -F / dF
            dp = np.maximum(dp + step, 0.0)
            if np.max(np.abs(F)) < 1e-9 * self.sigma0:
                break
        else:
            raise RuntimeError("local return mapping did not converge")

        # ---- final consistent quantities
        if nb:
            beta = 1.0 / (1.0 + gam[None, :] * dp[:, None])
            xi_t = s_t - np.einsum("mk,mkj->mj", beta, al)
            a_vec = np.einsum("mk,mkj->mj", gam[None, :] * beta**2, al)
            Ht = 3.0 * G + (C[None, :] * beta).sum(axis=1)
            dHt = -(C[None, :] * gam[None, :] * beta**2).sum(axis=1)
        else:
            xi_t = s_t
            a_vec = np.zeros_like(s_t)
            Ht = np.full(dp.shape, 3.0 * G)
            dHt = np.zeros_like(dp)
        q_t = np.sqrt(1.5 * np.einsum("ij,ij->i", xi_t, xi_t))
        nvec = 1.5 * xi_t / q_t[:, None]
        deps_p = dp[:, None] * nvec

        sig[idx] = sig_tr[idx] - 2.0 * G * deps_p
        new["eps_p"][idx] = st["eps_p"][idx] + deps_p
        new["p"][idx] = p_n + dp
        if nb:
            new["alpha"][idx] = beta[:, :, None] * (al + (2.0 / 3.0) * C[None, :, None] * dp[:, None, None] * nvec[:, None, :])

        if want_tangent:
            D = Ht + dp * dHt + self.dR(p_n + dp) - np.einsum("ij,ij->i", nvec, a_vec)
            Q = P_DEV[None, :, :] - (2.0 / 3.0) * np.einsum("mi,mj->mij", nvec, nvec)
            Qa = np.einsum("mij,mj->mi", Q, a_vec)
            left = nvec + (1.5 * dp / q_t)[:, None] * Qa
            Ct[idx] = (self.Ce[None, :, :]
                       - (6.0 * G * G * dp / q_t)[:, None, None] * Q
                       - (4.0 * G * G / D)[:, None, None] * np.einsum("mi,mj->mij", left, nvec))
        return sig, Ct, new, plastic


# ---------------------------------------------------------------------------
# helpers for plane stress: iterate eps33 so that sigma33 = 0
# ---------------------------------------------------------------------------
def update_plane_stress(mat, eps_inplane, eps33_guess, st, dT=None, tol=1e-8, maxit=30):
    """eps_inplane: (n,3) = [e11, e22, sqrt2*e12] Mandel. Returns sigma (n,3 Mandel),
    condensed tangent (n,3,3), new state, eps33 (n,), plastic mask."""
    n = eps_inplane.shape[0]
    eps = np.zeros((n, 4))
    eps[:, 0] = eps_inplane[:, 0]
    eps[:, 1] = eps_inplane[:, 1]
    eps[:, 3] = eps_inplane[:, 2]
    e33 = eps33_guess.copy()
    for it in range(maxit):
        eps[:, 2] = e33
        sig, Ct, new, plastic = mat.update(eps, st, dT)
        s33 = sig[:, 2]
        if np.max(np.abs(s33)) < tol * mat.sigma0:
            break
        e33 = e33 - s33 / Ct[:, 2, 2]
    else:
        raise RuntimeError("plane-stress iteration failed")
    ip = [0, 1, 3]
    Cps = Ct[:, ip][:, :, ip] - np.einsum("mi,mj->mij", Ct[:, ip, 2], Ct[:, 2, ip]) / Ct[:, 2, 2][:, None, None]
    return sig[:, ip], Cps, new, e33, plastic


def von_mises(sig4):
    """sig4: (...,4) Mandel stress -> von Mises equivalent stress."""
    s = sig4 @ P_DEV.T
    return np.sqrt(1.5 * np.sum(s * s, axis=-1))


def equivalent_strain(e4):
    """von Mises equivalent of a (deviatoric) plastic strain tensor, Mandel (...,4)."""
    return np.sqrt(2.0 / 3.0 * np.sum(e4 * e4, axis=-1))


# ---------------------------------------------------------------------------
# Calibration: stabilised (Masing) loop tip of a Chaboche material under
# symmetric strain control  sigma_a = sigma0 + sum C_i/gamma_i tanh(gamma_i eps_pa)
# ---------------------------------------------------------------------------
def chaboche_cyclic_curve(eps_pa, sigma0, C, gamma):
    eps_pa = np.asarray(eps_pa, dtype=float)
    out = np.full_like(eps_pa, sigma0)
    for c, g in zip(C, gamma):
        out += c / g * np.tanh(g * eps_pa) if g > 0 else c * eps_pa
    return out


def fit_chaboche_to_ramberg_osgood(Kp, nprime, sigma0=None, nback=3, eps_range=(2e-5, 2e-2)):
    """Least-squares fit of a Chaboche model's stabilised curve to the cyclic
    Ramberg-Osgood curve sigma_a = K' eps_pa^n'."""
    from scipy.optimize import least_squares
    e = np.logspace(np.log10(eps_range[0]), np.log10(eps_range[1]), 200)
    target = Kp * e**nprime
    fix_s0 = sigma0 is not None

    def unpack(x):
        if fix_s0:
            s0 = sigma0
            rest = x
        else:
            s0 = x[0]
            rest = x[1:]
        lC = rest[:nback]
        lg = rest[nback:]
        return s0, np.exp(lC), np.exp(lg)

    def res(x):
        s0, C, g = unpack(x)
        return (chaboche_cyclic_curve(e, s0, C, g) - target) / target

    x0 = ([] if fix_s0 else [0.6 * Kp * 0.002**nprime]) + list(np.log([2e5, 3e4, 2e3][:nback])) + list(np.log([2000, 200, 10][:nback]))
    sol = least_squares(res, np.array(x0, dtype=float))
    s0, C, g = unpack(sol.x)
    return s0, C, g, np.max(np.abs(res(sol.x)))
