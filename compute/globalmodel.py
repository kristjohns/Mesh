"""Global wellhead / conductor model: beams on nonlinear Winkler (p-y) springs.

Planar model (lateral displacement u and rotation theta per node).
Two concentric strings:
  outer: conductor (36" x 1.5")  + conductor housing (LPWH)
  inner: surface casing (20" x 0.625") + HP wellhead housing + BOP/LMRP (stiff)
Couplings:
  cement (below top of cement): stiff lateral links between strings
  HPWHH / LPWH: lateral contacts with small gaps + rotational shoulder spring (bilinear)
  LPWH / template: lateral gap element to a template spring (flexible template)
Soil: Matlock / API soft clay p-y springs on the conductor (static or cyclic).
"""
import json
import numpy as np

STEEL_E = 207e9
D_COND, T_COND = 0.9144, 0.0381
D_CAS, T_CAS = 0.508, 0.015875


def I_pipe(D, t):
    return np.pi / 64 * (D ** 4 - (D - 2 * t) ** 4)


EI_COND = STEEL_E * I_pipe(D_COND, T_COND)
EI_CAS = STEEL_E * I_pipe(D_CAS, T_CAS)
EI_LPWH = STEEL_E * I_pipe(0.96, 0.075)
EI_HPWHH = STEEL_E * I_pipe(0.70, 0.112)
EI_BOP = 5e12

Z_TIP = -60.0          # conductor penetration
Z_LPWH_BOT = 0.8       # conductor / housing weld
Z_LPWH_TOP = 2.6
Z_HP_BOT = 1.2         # casing / HPWHH weld
Z_LOWER_CONTACT = 1.4
Z_TEMPLATE = 2.0       # template receptacle elevation
Z_SHOULDER = 2.2
Z_UPPER_CONTACT = 2.45
Z_WH = 3.6             # wellhead datum (top of HPWHH)
Z_LOAD = 3.6 + 13.0    # LMRP flex joint
Z_TOC = 0.0            # top of cement


class Soil:
    def __init__(self, su0=3.0e3, k_su=1.5e3, gamma=7.0e3, eps50=0.01, J=0.5, D=D_COND,
                 cyclic=False, disturbed_depth=0.0, disturbed_factor=1.0):
        self.su0, self.k_su, self.gamma, self.eps50, self.J, self.D = su0, k_su, gamma, eps50, J, D
        self.cyclic = cyclic
        self.dd, self.df = disturbed_depth, disturbed_factor

    def su(self, X):
        s = self.su0 + self.k_su * X
        if X < self.dd:
            s *= self.df
        return s

    def pu(self, X):
        c, D = self.su(X), self.D
        return min((3 * c + self.gamma * X + self.J * c * X / D) * D, 9 * c * D)

    def XR(self):
        # depth where shallow and deep pu formulas meet
        Xs = np.linspace(0, 60, 6001)
        for X in Xs:
            c = self.su0 + self.k_su * X
            if 3 * c + self.gamma * X + self.J * c * X / self.D >= 9 * c:
                return X
        return 60.0

    def curve(self, X):
        """API RP 2GEO soft clay table: returns (y, p) points (p per unit length)."""
        yc = 2.5 * self.eps50 * self.D
        pu = self.pu(X)
        if not self.cyclic:
            yr = [0.0, 0.1, 0.3, 1.0, 3.0, 8.0, 30.0]
            pr = [0.0, 0.23, 0.33, 0.50, 0.72, 1.00, 1.00]
        else:
            XR = self.XR()
            if X >= XR:
                yr = [0.0, 0.1, 0.3, 1.0, 3.0, 30.0]
                pr = [0.0, 0.23, 0.33, 0.50, 0.72, 0.72]
            else:
                f = 0.72 * X / XR
                yr = [0.0, 0.1, 0.3, 1.0, 3.0, 15.0, 30.0]
                pr = [0.0, 0.23, 0.33, 0.50, 0.72, f, f]
        return np.array(yr) * yc, np.array(pr) * pu


def matlock_smooth(y, yc, pu):
    y = np.abs(y)
    return np.where(y < 8 * yc, 0.5 * pu * np.cbrt(y / yc), pu)


class PWL:
    """Symmetric piecewise linear spring F(d) defined for d >= 0 by table (y, F)."""

    def __init__(self, y, F):
        self.y, self.F = np.asarray(y, float), np.asarray(F, float)

    def __call__(self, d):
        a = abs(d)
        if a >= self.y[-1]:
            f = self.F[-1] + (a - self.y[-1]) * 0.0
            kt = 1e-6 * self.F[-1] / self.y[-1]
        else:
            i = np.searchsorted(self.y, a, side="right") - 1
            i = min(max(i, 0), len(self.y) - 2)
            kt = (self.F[i + 1] - self.F[i]) / (self.y[i + 1] - self.y[i])
            f = self.F[i] + kt * (a - self.y[i])
        return np.sign(d) * f, kt


class Gap:
    def __init__(self, g, k):
        self.g, self.k = g, k

    def __call__(self, d):
        a = abs(d)
        if a <= self.g:
            return 0.0, 0.0
        return np.sign(d) * self.k * (a - self.g), self.k


class Bilinear:
    def __init__(self, k1, k2, M1):
        self.k1, self.k2, self.M1 = k1, k2, M1
        self.r1 = M1 / k1

    def __call__(self, d):
        a = abs(d)
        if a <= self.r1:
            return self.k1 * d, self.k1
        return np.sign(d) * (self.M1 + self.k2 * (a - self.r1)), self.k2


class Linear:
    def __init__(self, k):
        self.k = k

    def __call__(self, d):
        return self.k * d, self.k


def build_grid(le_top=0.25, uniform=None):
    """z-coordinates of nodes (shared by both strings where they overlap)."""
    zs = set()
    if uniform is not None:
        z = 0.0
        while z > Z_TIP - 1e-9:
            zs.add(round(z, 6))
            z -= uniform
        zs.add(Z_TIP)
    else:
        bands = [(0, -10, le_top), (-10, -20, 2 * le_top), (-20, -35, 1.0), (-35, Z_TIP, 2.5)]
        for z0, z1, h in bands:
            n = int(round((z0 - z1) / h))
            for zz in np.linspace(z0, z1, n + 1):
                zs.add(round(zz, 6))
    above = [0.4, Z_LPWH_BOT, Z_HP_BOT, Z_LOWER_CONTACT, 1.7, Z_TEMPLATE, Z_SHOULDER,
             Z_UPPER_CONTACT, Z_LPWH_TOP, 3.1, Z_WH]
    zs.update(above)
    zb = Z_WH
    while zb < Z_LOAD - 1e-9:
        zb += 1.0
        zs.add(round(min(zb, Z_LOAD), 6))
    return np.array(sorted(zs))


class Model:
    def __init__(self, soil, le_top=0.25, uniform=None, fixed_mudline=False, template=None,
                 shoulder=None, linear_soil_k=None, soil_on=True, coupled_strings=True,
                 single_string=False):
        self.soil = soil
        z = build_grid(le_top, uniform)
        self.z = z
        # node lists
        self.nodes = []  # (string, z)
        self.outer = [i for i, zz in enumerate(z) if zz <= Z_LPWH_TOP + 1e-9]
        self.inner = [i for i, zz in enumerate(z)]
        self.idx_outer = {}
        self.idx_inner = {}
        n = 0
        for i in self.outer:
            self.idx_outer[i] = n
            n += 1
        for i in self.inner:
            self.idx_inner[i] = n
            n += 1
        self.nn = n
        self.ndof = 2 * n
        K = np.zeros((self.ndof, self.ndof))

        def add_beam(a, b, EI, L):
            k = EI / L ** 3 * np.array([[12, 6 * L, -12, 6 * L], [6 * L, 4 * L ** 2, -6 * L, 2 * L ** 2],
                                        [-12, -6 * L, 12, -6 * L], [6 * L, 2 * L ** 2, -6 * L, 4 * L ** 2]])
            d = [2 * a, 2 * a + 1, 2 * b, 2 * b + 1]
            K[np.ix_(d, d)] += k

        self.elems = []
        for s, lst, idx in [("outer", self.outer, self.idx_outer), ("inner", self.inner, self.idx_inner)]:
            for i0, i1 in zip(lst[:-1], lst[1:]):
                z0, z1 = z[i0], z[i1]
                zm = 0.5 * (z0 + z1)
                if s == "outer":
                    EI = EI_COND if zm < Z_LPWH_BOT else EI_LPWH
                else:
                    EI = EI_CAS if zm < Z_HP_BOT else (EI_HPWHH if zm < Z_WH else EI_BOP)
                if single_string and s == "outer":
                    EI = EI + (EI_CAS if zm < Z_HP_BOT else 0)
                add_beam(idx[i0], idx[i1], EI, z1 - z0)
                self.elems.append((s, idx[i0], idx[i1], EI, z0, z1))
        self.K = K
        # nonlinear/linear springs: (dof_a, dof_b or None, law, tag, info)
        self.springs = []
        zo = np.array([z[i] for i in self.outer])
        if soil_on and not fixed_mudline:
            for k, i in enumerate(self.outer):
                if z[i] > 1e-9:
                    continue
                # tributary length
                zl = z[self.outer[k - 1]] if k > 0 else z[i]
                zu = z[self.outer[k + 1]] if k + 1 < len(self.outer) else z[i]
                zu = min(zu, 0.0)
                trib = 0.5 * (zu - z[i]) + 0.5 * (z[i] - zl)
                if trib <= 0:
                    continue
                X = -z[i]
                if linear_soil_k is not None:
                    law = Linear(linear_soil_k * trib)
                else:
                    y, p = soil.curve(X)
                    law = PWL(y, p * trib)
                self.springs.append(dict(a=2 * self.idx_outer[i], b=None, law=law, tag="soil", X=X,
                                         trib=trib, z=z[i]))
        self.fixed = []
        if fixed_mudline:
            i0 = int(np.argmin(np.abs(z)))
            for i in self.outer:
                if z[i] <= 1e-9:
                    self.fixed += [2 * self.idx_outer[i], 2 * self.idx_outer[i] + 1]
            for i in self.inner:
                if z[i] <= 1e-9:
                    self.fixed += [2 * self.idx_inner[i], 2 * self.idx_inner[i] + 1]
        # cement coupling below TOC
        if coupled_strings:
            for i in self.outer:
                if z[i] <= Z_TOC + 1e-9:
                    self.springs.append(dict(a=2 * self.idx_outer[i], b=2 * self.idx_inner[i],
                                             law=Linear(5e10), tag="cement", z=z[i]))
            # HPWHH / LPWH lateral contacts (0.5 mm radial clearance)
            for zc, tag in [(Z_LOWER_CONTACT, "lower"), (Z_UPPER_CONTACT, "upper")]:
                i = int(np.argmin(np.abs(z - zc)))
                self.springs.append(dict(a=2 * self.idx_outer[i], b=2 * self.idx_inner[i],
                                         law=Gap(0.0005, 2e9), tag="contact_" + tag, z=z[i]))
            i = int(np.argmin(np.abs(z - Z_SHOULDER)))
            law = shoulder if shoulder is not None else Bilinear(8e9, 1.5e9, 1.2e6)
            self.springs.append(dict(a=2 * self.idx_outer[i] + 1, b=2 * self.idx_inner[i] + 1,
                                     law=law, tag="shoulder", z=z[i]))
        if single_string:
            # inner string tied to outer everywhere it overlaps (used for simple checks)
            for i in self.outer:
                self.springs.append(dict(a=2 * self.idx_outer[i], b=2 * self.idx_inner[i],
                                         law=Linear(5e11), tag="tie", z=z[i]))
        if template is not None:
            i = int(np.argmin(np.abs(z - Z_TEMPLATE)))
            self.springs.append(dict(a=2 * self.idx_outer[i], b=None, law=template, tag="template",
                                     z=z[i]))
        self.load_node = self.idx_inner[int(np.argmin(np.abs(z - Z_LOAD)))]
        self.wh_node = self.idx_inner[int(np.argmin(np.abs(z - Z_WH)))]

    def internal(self, u):
        R = self.K @ u
        Kt = self.K.copy()
        forces = []
        for s in self.springs:
            a, b = s["a"], s["b"]
            d = u[a] - (u[b] if b is not None else 0.0)
            f, kt = s["law"](d)
            R[a] += f
            Kt[a, a] += kt
            if b is not None:
                R[b] -= f
                Kt[b, b] += kt
                Kt[a, b] -= kt
                Kt[b, a] -= kt
            forces.append(f)
        return R, Kt, forces

    def solve(self, H, nsteps=20, M_extra=0.0, tol=1e-6, u0=None):
        u = np.zeros(self.ndof) if u0 is None else u0.copy()
        free = np.setdiff1d(np.arange(self.ndof), self.fixed)
        hist = []
        for step in range(1, nsteps + 1):
            F = np.zeros(self.ndof)
            F[2 * self.load_node] = H * step / nsteps
            F[2 * self.load_node + 1] = M_extra * step / nsteps
            for it in range(200):
                R, Kt, _ = self.internal(u)
                r = F - R
                r[self.fixed] = 0.0
                nr = np.linalg.norm(r[free])
                if nr < tol * max(1.0, abs(H)):
                    break
                du = np.zeros(self.ndof)
                du[free] = np.linalg.solve(Kt[np.ix_(free, free)], r[free])
                # simple line search to stabilise kinks in piecewise-linear laws
                alpha = 1.0
                for _ in range(8):
                    R2, _, _ = self.internal(u + alpha * du)
                    r2 = F - R2
                    r2[self.fixed] = 0
                    if np.linalg.norm(r2[free]) < nr or alpha < 0.02:
                        break
                    alpha *= 0.5
                u = u + alpha * du
            else:
                print("WARNING: not converged at step", step, nr)
            hist.append(u.copy())
        return u, hist

    # --- post-processing -------------------------------------------------
    def moments(self, u, string):
        """Bending moment at element ends: list of (z, M)."""
        out = []
        for s, a, b, EI, z0, z1 in self.elems:
            if s != string:
                continue
            L = z1 - z0
            ue = np.array([u[2 * a], u[2 * a + 1], u[2 * b], u[2 * b + 1]])
            for xi, zz in [(0.0, z0), (1.0, z1)]:
                d2 = np.array([(-6 + 12 * xi) / L ** 2, (-4 + 6 * xi) / L, (6 - 12 * xi) / L ** 2,
                               (-2 + 6 * xi) / L])
                out.append((zz, EI * d2 @ ue))
        # average duplicates at shared nodes
        acc = {}
        for zz, M in out:
            acc.setdefault(round(zz, 6), []).append(M)
        zz = np.array(sorted(acc))
        return zz, np.array([np.mean(acc[k]) for k in zz])

    def profile(self, u, string):
        idx = self.idx_outer if string == "outer" else self.idx_inner
        ii = sorted(idx, key=lambda i: self.z[i])
        return np.array([self.z[i] for i in ii]), np.array([u[2 * idx[i]] for i in ii]), \
            np.array([u[2 * idx[i] + 1] for i in ii])

    def spring_state(self, u):
        _, _, forces = self.internal(u)
        res = []
        for s, f in zip(self.springs, forces):
            if s["tag"] != "soil":
                continue
            pu = self.soil.pu(s["X"]) * s["trib"]
            res.append(dict(z=s["z"], p=f / s["trib"], pu=self.soil.pu(s["X"]), mob=abs(f) / pu,
                            y=u[s["a"]]))
        return res

    def spring_force(self, u, tag):
        _, _, forces = self.internal(u)
        return [f for s, f in zip(self.springs, forces) if s["tag"] == tag]
