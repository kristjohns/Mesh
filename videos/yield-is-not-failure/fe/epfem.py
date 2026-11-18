"""epfem - a compact small-strain elastic-plastic finite element solver.

* 6-node isoparametric triangles (curved edges), 3-point Gauss rule
* plane strain, plane stress (sigma_33 = 0 enforced at every Gauss point) and axisymmetric
* J2 (von Mises) plasticity, associative flow, isotropic hardening of any form
  - radial return mapping with the algorithmically consistent tangent (Simo & Taylor)
* thermal strains, prescribed displacements, edge tractions/pressure, DOF ties
  (generalised plane strain), Newton-Raphson with automatic step cutting
Tensors are stored in Mandel notation [11, 22, 33, sqrt(2)*12] so that a:b = a.b.
"""
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import splu

R2 = np.sqrt(2.0)
MV = np.array([1.0, 1.0, 1.0, 0.0])                 # identity in Mandel form
IDEV = np.eye(4) - np.outer(MV, MV) / 3.0           # deviatoric projector


# ------------------------------------------------------------------ material
class Material:
    """Isotropic elastic, J2-plastic. hardening(ebar) -> (sigma_y, d sigma_y / d ebar)."""

    def __init__(self, E, nu, sy0, hardening=None, alpha=0.0, name=""):
        self.E, self.nu, self.sy0, self.alpha, self.name = E, nu, sy0, alpha, name
        self.G = E / (2 * (1 + nu))
        self.K = E / (3 * (1 - 2 * nu))
        self.hard = hardening

    def sy(self, eb):
        if self.hard is None:
            return np.full_like(eb, self.sy0, dtype=float), np.zeros_like(eb, dtype=float)
        return self.hard(eb)


def dnv_type_curve(sy1=357.0, sy2=366.0, ep_y1=0.004, ep_y2=0.015, K=740.0, n=0.166):
    """Yield plateau followed by power-law hardening (form used in DNV-RP-C208), returns hardening(ebar)."""
    shift = (sy2 / K) ** (1.0 / n) - ep_y2

    def h(eb):
        eb = np.asarray(eb, dtype=float)
        s = np.empty_like(eb); d = np.empty_like(eb)
        b = eb <= ep_y2                                   # yield plateau (slight slope sy1 -> sy2)
        c = ~b
        s[b] = sy1 + (sy2 - sy1) * (eb[b] / ep_y2)
        d[b] = (sy2 - sy1) / ep_y2
        x = eb[c] + shift
        s[c] = K * x ** n
        d[c] = K * n * x ** (n - 1)
        return s, d
    return h


def return_map(mat, eps, ep_n, eb_n, eth):
    """3D J2 radial return on 4-component (Mandel) states. Returns sigma, D, ep, eb, plastic mask."""
    G, K = mat.G, mat.K
    ee = eps - ep_n - eth[:, None] * MV
    tr = ee[:, 0] + ee[:, 1] + ee[:, 2]
    s_tr = 2 * G * (ee - tr[:, None] * MV / 3.0)
    ns = np.linalg.norm(s_tr, axis=1)
    q = np.sqrt(1.5) * ns
    sy, _ = mat.sy(eb_n)
    pl = (q - sy) > 1e-10 * mat.sy0
    dg = np.zeros_like(q)
    if pl.any():
        qp, ebp = q[pl], eb_n[pl]
        x = np.zeros_like(qp)
        for _ in range(50):
            syx, hx = mat.sy(ebp + x)
            r = qp - 3 * G * x - syx
            x = np.maximum(x + r / (3 * G + hx), 0.0)
            if np.max(np.abs(r)) < 1e-9 * mat.sy0:
                break
        dg[pl] = x
    nh = s_tr / np.maximum(ns, 1e-300)[:, None]
    s = s_tr - (2 * G * np.sqrt(1.5) * dg)[:, None] * nh
    sig = s + (K * tr)[:, None] * MV
    ep = ep_n + (np.sqrt(1.5) * dg)[:, None] * nh
    eb = eb_n + dg
    D = np.broadcast_to(K * np.outer(MV, MV) + 2 * G * IDEV, (len(q), 4, 4)).copy()
    if pl.any():
        _, hx = mat.sy(eb[pl])
        a = 2 * G * (1 - 3 * G * dg[pl] / q[pl])
        b = 6 * G * G * (dg[pl] / q[pl] - 1.0 / (3 * G + hx))
        D[pl] = (K * np.outer(MV, MV))[None] + a[:, None, None] * IDEV[None] + \
            b[:, None, None] * np.einsum("ni,nj->nij", nh[pl], nh[pl])
    return sig, D, ep, eb, pl


# ------------------------------------------------------------------ T6 element
GP = np.array([[1 / 6, 1 / 6], [2 / 3, 1 / 6], [1 / 6, 2 / 3]])
GW = np.full(3, 1 / 6)


def t6_shape(xi, eta):
    L1, L2, L3 = 1 - xi - eta, xi, eta
    N = np.array([L1 * (2 * L1 - 1), L2 * (2 * L2 - 1), L3 * (2 * L3 - 1), 4 * L1 * L2, 4 * L2 * L3, 4 * L3 * L1])
    dxi = np.array([-(4 * L1 - 1), 4 * L2 - 1, 0.0, 4 * (L1 - L2), 4 * L3, -4 * L3])
    deta = np.array([-(4 * L1 - 1), 0.0, 4 * L3 - 1, -4 * L2, 4 * L2, 4 * (L1 - L3)])
    return N, np.vstack([dxi, deta])


class Model:
    def __init__(self, X, T, mat, mode="axisym", thickness=1.0):
        self.X = np.asarray(X, dtype=float)
        self.T = np.asarray(T, dtype=int)
        self.mat, self.mode, self.th = mat, mode, thickness
        ne = len(self.T)
        self.ne, self.nn = ne, len(self.X)
        self.ndof = 2 * self.nn
        nq = 3
        B = np.zeros((ne, nq, 4, 12))
        W = np.zeros((ne, nq))
        XQ = np.zeros((ne, nq, 2))
        xe = self.X[self.T]                                    # (ne, 6, 2)
        for q in range(nq):
            N, dN = t6_shape(*GP[q])
            J = np.einsum("ia,eaj->eij", dN, xe)              # J[i,j] = d x_j / d xi_i
            det = J[:, 0, 0] * J[:, 1, 1] - J[:, 0, 1] * J[:, 1, 0]
            if np.any(det <= 0):
                raise ValueError("element with non-positive Jacobian")
            Ji = np.empty_like(J)
            Ji[:, 0, 0], Ji[:, 1, 1] = J[:, 1, 1] / det, J[:, 0, 0] / det
            Ji[:, 0, 1], Ji[:, 1, 0] = -J[:, 0, 1] / det, -J[:, 1, 0] / det
            dNx = np.einsum("eij,ja->eia", Ji, dN)              # (ne,2,6): d N_a / d x_i
            xq = np.einsum("a,eaj->ej", N, xe)
            XQ[:, q] = xq
            B[:, q, 0, 0::2] = dNx[:, 0]
            B[:, q, 1, 1::2] = dNx[:, 1]
            B[:, q, 3, 0::2] = dNx[:, 1] / R2
            B[:, q, 3, 1::2] = dNx[:, 0] / R2
            if mode == "axisym":
                B[:, q, 2, 0::2] = N[None, :] / xq[:, 0:1]
                W[:, q] = GW[q] * det * 2 * np.pi * xq[:, 0]
            else:
                W[:, q] = GW[q] * det * thickness
        self.B, self.W, self.XQ = B, W, XQ
        self.edof = np.empty((ne, 12), dtype=int)
        self.edof[:, 0::2] = 2 * self.T
        self.edof[:, 1::2] = 2 * self.T + 1
        ii = np.repeat(self.edof, 12, axis=1).ravel()
        jj = np.tile(self.edof, (1, 12)).ravel()
        self._ij = (ii, jj)
        ng = ne * nq
        self.state = dict(ep=np.zeros((ng, 4)), eb=np.zeros(ng), e33=np.zeros(ng))
        self.u = np.zeros(self.ndof)
        self.fixed = {}          # dof -> callable(t) or value
        self.ties = []           # lists of dofs tied to their first entry
        self.loads = []          # callables t -> full force vector contributions
        self.temperature = None  # callable (t, XQ (ng,2)) -> (ng,) temperature change

    # ---------------------------------------------------------------- helpers
    def nodes_where(self, pred):
        return np.where(pred(self.X[:, 0], self.X[:, 1]))[0]

    def fix(self, nodes, comp, value=0.0):
        for n in np.atleast_1d(nodes):
            self.fixed[2 * int(n) + comp] = value

    def tie(self, nodes, comp):
        self.ties.append([2 * int(n) + comp for n in nodes])

    def edges_where(self, pred):
        """Boundary-candidate element edges (3-node, corner-mid-corner) whose nodes all satisfy pred."""
        loc = [(0, 3, 1), (1, 4, 2), (2, 5, 0)]
        out = []
        ok = pred(self.X[:, 0], self.X[:, 1])
        for e, tri in enumerate(self.T):
            for a, m, b in loc:
                if ok[tri[a]] and ok[tri[m]] and ok[tri[b]]:
                    out.append((e, tri[a], tri[m], tri[b]))
        return out

    def edge_load(self, edges, traction=None, pressure=None):
        """Consistent nodal forces of a traction vector (tx, ty) or a pressure (normal, inward positive)."""
        f = np.zeros(self.ndof)
        gp = np.array([-np.sqrt(0.6), 0.0, np.sqrt(0.6)]); gw = np.array([5, 8, 5]) / 9.0
        for e, a, m, b in edges:
            xa, xm, xb = self.X[a], self.X[m], self.X[b]
            cen = self.X[self.T[e]].mean(axis=0)
            for s, w in zip(gp, gw):
                Na, Nb, Nm = s * (s - 1) / 2, s * (s + 1) / 2, 1 - s * s
                dNa, dNb, dNm = s - 0.5, s + 0.5, -2 * s
                x = Na * xa + Nb * xb + Nm * xm
                dx = dNa * xa + dNb * xb + dNm * xm
                ds = np.linalg.norm(dx)
                if pressure is not None:
                    nrm = np.array([dx[1], -dx[0]]) / ds
                    if np.dot(nrm, x - cen) < 0:
                        nrm = -nrm
                    tvec = -pressure * nrm
                else:
                    tvec = np.asarray(traction, dtype=float)
                fac = w * ds * (2 * np.pi * x[0] if self.mode == "axisym" else self.th)
                for node, Nv in ((a, Na), (b, Nb), (m, Nm)):
                    f[2 * node:2 * node + 2] += Nv * tvec * fac
        return f

    # ---------------------------------------------------------------- core
    def _constitutive(self, u, t, st):
        ue = u[self.edof]
        eps = np.einsum("eqij,ej->eqi", self.B, ue).reshape(-1, 4)
        eth = np.zeros(len(eps))
        if self.temperature is not None and self.mat.alpha:
            eth = self.mat.alpha * self.temperature(t, self.XQ.reshape(-1, 2))
        if self.mode == "pstress":
            e33 = st["e33"].copy()
            for _ in range(30):
                eps[:, 2] = e33
                sig, D, ep, eb, pl = return_map(self.mat, eps, st["ep"], st["eb"], eth)
                r = sig[:, 2]
                if np.max(np.abs(r)) < 1e-7 * self.mat.sy0:
                    break
                e33 = e33 - r / D[:, 2, 2]
            Dc = D - np.einsum("ni,nj->nij", D[:, :, 2], D[:, 2, :]) / D[:, 2, 2][:, None, None]
            Dc[:, 2, :] = 0.0; Dc[:, :, 2] = 0.0
            D = Dc
            new = dict(ep=ep, eb=eb, e33=e33)
        else:
            sig, D, ep, eb, pl = return_map(self.mat, eps, st["ep"], st["eb"], eth)
            new = dict(ep=ep, eb=eb, e33=st["e33"])
        return sig, D, new, pl, eps

    def _assemble(self, sig, D):
        nq = 3
        S = sig.reshape(self.ne, nq, 4)
        Dq = D.reshape(self.ne, nq, 4, 4)
        fe = np.einsum("eqij,eqi,eq->ej", self.B, S, self.W)
        fint = np.zeros(self.ndof)
        np.add.at(fint, self.edof.ravel(), fe.ravel())
        Ke = np.einsum("eqki,eqkl,eqlj,eq->eij", self.B, Dq, self.B, self.W, optimize=True)
        K = sp.coo_matrix((Ke.ravel(), self._ij), shape=(self.ndof, self.ndof)).tocsr()
        return fint, K

    def _reduction(self):
        """Map full dofs -> reduced dofs (ties)."""
        red = np.arange(self.ndof)
        for grp in self.ties:
            red[grp] = grp[0]
        uniq, inv = np.unique(red, return_inverse=True)
        Tm = sp.csr_matrix((np.ones(self.ndof), (np.arange(self.ndof), inv)), shape=(self.ndof, len(uniq)))
        return Tm, uniq, inv

    def solve(self, times, monitors=None, maxit=30, tol=1e-7, max_cuts=10, keep=None, verbose=False):
        """Incremental Newton-Raphson over the pseudo-time list `times` (first entry = start).

        monitors: dict name -> callable(model, u, fint) evaluated after each converged increment.
        keep: set of indices into `times` whose full state is stored (for plotting).
        Returns history dict; history['converged'] False if the analysis failed to converge
        (which, for load control, is the usual signature of plastic collapse).
        """
        Tm, uniq, inv = self._reduction()
        nred = len(uniq)
        fixed_red = {}
        for dof, val in self.fixed.items():
            fixed_red[inv[dof]] = val
        pres = np.array(sorted(fixed_red))
        free = np.setdiff1d(np.arange(nred), pres)
        hist = {k: [] for k in (monitors or {})}
        hist["t"] = []
        hist["snap"] = {}
        hist["converged"] = True
        keep = set(keep or [])
        ur = Tm.T @ self.u / np.maximum(np.asarray(Tm.sum(axis=0)).ravel(), 1)
        st = {k: v.copy() for k, v in self.state.items()}
        t_old = times[0]
        # tangent and internal force at the starting state (for the consistent predictor)
        sig0, D0, _, _, _ = self._constitutive(Tm @ ur, t_old, st)
        fint0, K0 = self._assemble(sig0, D0)
        K_last = (Tm.T @ K0 @ Tm).tocsc()
        fint_last = Tm.T @ fint0
        k_target = 1
        while k_target < len(times):
            t_new = times[k_target]
            dt = t_new - t_old
            cuts = 0
            while True:
                t_try = t_old + dt
                ut = ur.copy()
                for i, d in enumerate(pres):
                    v = fixed_red[d]
                    ut[d] = v(t_try) if callable(v) else v
                fext = sum((L(t_try) for L in self.loads), np.zeros(self.ndof))
                fext_r = Tm.T @ fext
                # consistent predictor: interior response to the load / prescribed-displacement increment
                dup = ut[pres] - ur[pres] if len(pres) else np.zeros(0)
                rhs = (fext_r - fint_last)[free]
                if len(pres):
                    rhs = rhs - K_last[free][:, pres] @ dup
                try:
                    ut[free] += splu(K_last[free][:, free]).solve(rhs)
                except Exception:
                    pass
                ok = False
                dun = np.inf
                for it in range(maxit):
                    u_full = Tm @ ut
                    sig, D, new, pl, eps = self._constitutive(u_full, t_try, st)
                    fint, K = self._assemble(sig, D)
                    fint_r = Tm.T @ fint
                    res = fext_r - fint_r
                    scale = max(np.linalg.norm(fext_r[free]), np.linalg.norm(fint_r[pres]) if len(pres) else 0.0, 1e-8)
                    rn = np.linalg.norm(res[free]) / scale
                    if verbose:
                        print(f"   t={t_try:.5f} it={it} r={rn:.2e} plastic={pl.sum()}")
                    if it > 0 and (rn < tol or dun < 1e-10 * max(np.linalg.norm(ut), 1e-9)):
                        ok = True
                        break
                    Kr = (Tm.T @ K @ Tm).tocsc()
                    Kff = Kr[free][:, free]
                    try:
                        du = splu(Kff).solve(res[free])
                    except Exception:
                        break
                    if not np.all(np.isfinite(du)):
                        break
                    ut[free] += du
                    dun = np.linalg.norm(du)
                if ok:
                    K_last = (Tm.T @ K @ Tm).tocsc()
                    fint_last = fint_r
                    break
                cuts += 1
                if cuts > max_cuts:
                    hist["converged"] = False
                    hist["t_fail"] = t_try
                    self.u = Tm @ ur
                    self.state = st
                    return hist
                dt /= 2.0
            # accept increment
            ur = ut
            st = new
            self.u = Tm @ ur
            self.state = st
            self.sig = sig
            self.fint = fint
            self.plastic = pl
            t_old = t_try
            if abs(t_old - t_new) < 1e-12 * max(1.0, abs(t_new)):
                hist["t"].append(t_new)
                for name, fn in (monitors or {}).items():
                    hist[name].append(fn(self, self.u, fint))
                if k_target in keep:
                    hist["snap"][k_target] = dict(u=self.u.copy(), sig=sig.copy(), eb=st["eb"].copy(),
                                                  ep=st["ep"].copy())
                k_target += 1
        return hist

    # ---------------------------------------------------------------- post-processing
    def nodal(self, gp_values):
        """Extrapolate Gauss-point values (ng,) or (ng,k) to nodes (corner extrapolation + averaging)."""
        A = np.array([[2 / 3, 1 / 6, 1 / 6], [1 / 6, 2 / 3, 1 / 6], [1 / 6, 1 / 6, 2 / 3]])
        Ai = np.linalg.inv(A)
        g = np.asarray(gp_values).reshape(self.ne, 3, -1)
        vert = np.einsum("kq,eqc->ekc", Ai, g)
        mids = np.stack([(vert[:, 0] + vert[:, 1]) / 2, (vert[:, 1] + vert[:, 2]) / 2, (vert[:, 2] + vert[:, 0]) / 2], 1)
        allv = np.concatenate([vert, mids], axis=1)            # (ne,6,c)
        out = np.zeros((self.nn, allv.shape[2])); cnt = np.zeros(self.nn)
        np.add.at(out, self.T.ravel(), allv.reshape(-1, allv.shape[2]))
        np.add.at(cnt, self.T.ravel(), 1)
        out /= cnt[:, None]
        return out[:, 0] if out.shape[1] == 1 else out

    def subtriangles(self):
        t = self.T
        return np.vstack([t[:, [0, 3, 5]], t[:, [3, 1, 4]], t[:, [5, 4, 2]], t[:, [3, 4, 5]]])


def von_mises(sig):
    s = sig - (sig[:, 0] + sig[:, 1] + sig[:, 2])[:, None] * MV / 3.0
    return np.sqrt(1.5) * np.linalg.norm(s, axis=1)


def triaxiality(sig):
    return (sig[:, 0] + sig[:, 1] + sig[:, 2]) / 3.0 / np.maximum(von_mises(sig), 1e-12)


# ------------------------------------------------------------------ meshing
def gmsh_t6(build, size_expr, hmin=None):
    """Mesh a 2D OCC geometry (built by `build(occ)`) with 6-node triangles; returns X (n,2), T (e,6)."""
    import gmsh
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.add("m")
    occ = gmsh.model.occ
    build(occ)
    occ.synchronize()
    f = gmsh.model.mesh.field.add("MathEval")
    gmsh.model.mesh.field.setString(f, "F", size_expr)
    gmsh.model.mesh.field.setAsBackgroundMesh(f)
    for opt in ("Mesh.MeshSizeExtendFromBoundary", "Mesh.MeshSizeFromPoints", "Mesh.MeshSizeFromCurvature"):
        gmsh.option.setNumber(opt, 0)
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    gmsh.option.setNumber("Mesh.ElementOrder", 2)
    gmsh.option.setNumber("Mesh.SecondOrderLinear", 0)
    gmsh.model.mesh.generate(2)
    tags, coords, _ = gmsh.model.mesh.getNodes()
    xyz = coords.reshape(-1, 3)[:, :2]
    idx = {t_: i for i, t_ in enumerate(tags)}
    et, _, en = gmsh.model.mesh.getElements(2)
    conn = np.vectorize(idx.get)(en[list(et).index(9)].reshape(-1, 6))
    gmsh.finalize()
    used = np.unique(conn)
    remap = -np.ones(len(xyz), dtype=int); remap[used] = np.arange(len(used))
    X = xyz[used]; T = remap[conn]
    # orient counter-clockwise
    a, b, c = X[T[:, 0]], X[T[:, 1]], X[T[:, 2]]
    neg = ((b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])) < 0
    T[neg] = T[neg][:, [0, 2, 1, 5, 4, 3]]
    return X, T


def structured_t6(x0, x1, y0, y1, nx, ny, xgrade=None):
    """Structured T6 mesh of a rectangle (optionally graded in x: list of node x-coordinates)."""
    xs = np.linspace(x0, x1, 2 * nx + 1) if xgrade is None else np.asarray(xgrade)
    nxn = len(xs)
    ys = np.linspace(y0, y1, 2 * ny + 1)
    XX, YY = np.meshgrid(xs, ys, indexing="ij")
    X = np.column_stack([XX.ravel(), YY.ravel()])
    nid = lambda i, j: i * len(ys) + j
    T = []
    for i in range(0, nxn - 1, 2):
        for j in range(0, len(ys) - 1, 2):
            p = [nid(i, j), nid(i + 2, j), nid(i + 2, j + 2), nid(i, j + 2)]
            m = dict(b=nid(i + 1, j), r=nid(i + 2, j + 1), t=nid(i + 1, j + 2), l=nid(i, j + 1), c=nid(i + 1, j + 1))
            T.append([p[0], p[1], p[2], m["b"], m["r"], m["c"]])
            T.append([p[0], p[2], p[3], m["c"], m["t"], m["l"]])
    T = np.array(T)
    used = np.unique(T)
    remap = -np.ones(len(X), dtype=int); remap[used] = np.arange(len(used))
    return X[used], remap[T]
