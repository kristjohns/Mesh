"""
2-D small-strain finite element solver (plane stress / plane strain), Q9 elements,
implicit Newton-Raphson with consistent tangent, load + temperature + prescribed
displacement histories, automatic cut-back.
"""
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from .elements import q9_shape, gauss_3x3, gauss_to_node_matrix, Q9_NODES
from .material import update_plane_stress, SQ2

_DV = np.array([1.0, 1.0, 1.0 / SQ2])        # Voigt <-> Mandel shear scaling


class FEModel2D:
    def __init__(self, mesh, material, mode="plane_stress", thickness=1.0):
        assert mode in ("plane_stress", "plane_strain")
        self.mesh, self.mat, self.mode, self.t = mesh, material, mode, float(thickness)
        self.nn, self.ne = mesh.nn, mesh.ne
        self.ndof = 2 * self.nn
        self._precompute()
        self.fixed = np.zeros(self.ndof, bool)

    # ---------------------------------------------------------------- setup
    def _precompute(self):
        X = self.mesh.nodes[self.mesh.elems]                 # (ne, 9, 2)
        pts, w = gauss_3x3()
        ng = len(w)
        self.ng = ng
        Ngp = np.zeros((ng, 9))
        B = np.zeros((self.ne, ng, 3, 18))
        wdet = np.zeros((self.ne, ng))
        xgp = np.zeros((self.ne, ng, 2))
        for g, (xi, eta) in enumerate(pts):
            N, dNx, dNy = q9_shape(xi, eta)
            Ngp[g] = N
            J = np.stack([dNx @ X, dNy @ X], axis=1)          # (ne, 2, 2): rows d/dxi, d/deta
            detJ = J[:, 0, 0] * J[:, 1, 1] - J[:, 0, 1] * J[:, 1, 0]
            if np.any(detJ <= 0):
                raise ValueError("non-positive Jacobian in mesh")
            Jinv = np.linalg.inv(J)
            dN = np.einsum("eij,jn->ein", Jinv, np.stack([dNx, dNy]))  # (ne, 2, 9) d/dx, d/dy
            B[:, g, 0, 0::2] = dN[:, 0]
            B[:, g, 1, 1::2] = dN[:, 1]
            B[:, g, 2, 0::2] = dN[:, 1]
            B[:, g, 2, 1::2] = dN[:, 0]
            wdet[:, g] = w[g] * detJ * self.t
            xgp[:, g] = N @ X
        self.B, self.wdet, self.Ngp, self.xgp = B, wdet, Ngp, xgp
        dofs = np.empty((self.ne, 18), int)
        dofs[:, 0::2] = 2 * self.mesh.elems
        dofs[:, 1::2] = 2 * self.mesh.elems + 1
        self.edofs = dofs
        self.rows = np.repeat(dofs, 18, axis=1).ravel()
        self.cols = np.tile(dofs, (1, 18)).ravel()
        self.X2N = gauss_to_node_matrix()
        # B at element nodes (for nodal strains)
        Bn = np.zeros((self.ne, 9, 3, 18))
        for k, (xi, eta) in enumerate(Q9_NODES):
            N, dNx, dNy = q9_shape(xi, eta)
            J = np.stack([dNx @ X, dNy @ X], axis=1)
            Jinv = np.linalg.inv(J)
            dN = np.einsum("eij,jn->ein", Jinv, np.stack([dNx, dNy]))
            Bn[:, k, 0, 0::2] = dN[:, 0]
            Bn[:, k, 1, 1::2] = dN[:, 1]
            Bn[:, k, 2, 0::2] = dN[:, 1]
            Bn[:, k, 2, 1::2] = dN[:, 0]
        self.Bnode = Bn
        self.node_count = np.bincount(self.mesh.elems.ravel(), minlength=self.nn).astype(float)

    def new_state(self):
        st = self.mat.new_state(self.ne * self.ng)
        st["e33"] = np.zeros(self.ne * self.ng)
        return st

    def fix(self, nodes, comp, value=0.0):
        d = 2 * np.asarray(nodes) + comp
        self.fixed[d] = True

    # --------------------------------------------------------- loads
    def edge_load_vector(self, edges, traction):
        """edges: (m,3) node ids (corner, mid, corner); traction (tx, ty) per unit
        area (force/length^2 times thickness applied). Returns nodal force vector."""
        f = np.zeros(self.ndof)
        g = np.sqrt(0.6)
        pts = [-g, 0.0, g]
        ws = [5 / 9, 8 / 9, 5 / 9]
        for e in edges:
            P = self.mesh.nodes[list(e)]
            for s, w in zip(pts, ws):
                N = np.array([0.5 * s * (s - 1), 1 - s * s, 0.5 * s * (s + 1)])
                dN = np.array([s - 0.5, -2 * s, s + 0.5])
                ds = np.linalg.norm(dN @ P)
                for k, n in enumerate(e):
                    f[2 * n] += N[k] * traction[0] * ds * w * self.t
                    f[2 * n + 1] += N[k] * traction[1] * ds * w * self.t
        return f

    def nodal_to_gauss(self, nodal):
        return (nodal[self.mesh.elems] @ self.Ngp.T).ravel()   # (ne*ng,)

    # ------------------------------------------------------- assembly
    def assemble(self, u, st_n, dT_gp=None, e33_guess=None, want_K=True):
        ue = u[self.edofs]                                         # (ne, 18)
        epsv = np.einsum("egij,ej->egi", self.B, ue).reshape(-1, 3)
        epsm = epsv * _DV[None, :]
        if self.mode == "plane_stress":
            guess = st_n["e33"] if e33_guess is None else e33_guess
            sig3, C3, new, e33, plastic = update_plane_stress(self.mat, epsm, guess, st_n, dT_gp)
            new["e33"] = e33
        else:
            eps4 = np.zeros((epsm.shape[0], 4))
            eps4[:, [0, 1, 3]] = epsm
            sig4, C4, new, plastic = self.mat.update(eps4, st_n, dT_gp)
            new["e33"] = np.zeros(epsm.shape[0])
            new["s33"] = sig4[:, 2]
            ip = [0, 1, 3]
            sig3 = sig4[:, ip]
            C3 = C4[:, ip][:, :, ip]
        sigv = (sig3 * _DV[None, :]).reshape(self.ne, self.ng, 3)
        fint_e = np.einsum("egij,egi,eg->ej", self.B, sigv, self.wdet)
        fint = np.bincount(self.edofs.ravel(), weights=fint_e.ravel(), minlength=self.ndof)
        K = None
        if want_K:
            Cv = (C3 * _DV[None, :, None] * _DV[None, None, :]).reshape(self.ne, self.ng, 3, 3)
            Ke = np.einsum("egki,egkl,eglj,eg->eij", self.B, Cv, self.B, self.wdet, optimize=True)
            K = sp.coo_matrix((Ke.ravel(), (self.rows, self.cols)), shape=(self.ndof, self.ndof)).tocsr()
        new["sig"] = sig3          # Mandel in-plane [11, 22, sqrt2*12]
        new["plastic"] = plastic
        return fint, K, new

    # --------------------------------------------------------- Newton
    def solve_step(self, u0, st_n, fext, dT_gp=None, u_presc=None, tol=1e-7, maxit=25, verbose=False):
        """One load increment. u_presc: full-length vector with prescribed values on
        fixed dofs (default 0). Returns (u, new_state, iterations) or raises."""
        free = ~self.fixed
        u = u0.copy()
        if u_presc is not None:
            u[self.fixed] = u_presc[self.fixed]
        else:
            u[self.fixed] = 0.0
        e33_guess = st_n["e33"]
        for it in range(maxit):
            fint, K, new = self.assemble(u, st_n, dT_gp, e33_guess)
            r = fext - fint
            rnorm = np.linalg.norm(r[free])
            ref = max(np.linalg.norm(fext[free]), np.linalg.norm(fint), 1e-9 * self.mat.sigma0 * self.t)
            if verbose:
                print(f"    it {it}: |r|/ref = {rnorm/ref:.3e}")
            if rnorm <= tol * ref and it > 0:
                return u, new, it
            Kff = K[free][:, free]
            du = spla.spsolve(Kff.tocsc(), r[free])
            if not np.all(np.isfinite(du)):
                raise RuntimeError("singular tangent")
            u[free] += du
            e33_guess = new["e33"]
        raise RuntimeError("Newton did not converge")

    # ---------------------------------------------------- post-processing
    def gauss_to_nodes(self, vals):
        """vals: (ne*ng, k) or (ne*ng,) -> nodal averaged (nn, k)."""
        v = vals.reshape(self.ne, self.ng, -1)
        ve = np.einsum("ng,egk->enk", self.X2N, v)                 # (ne, 9 nodes, k)
        out = np.zeros((self.nn, v.shape[2]))
        for k in range(v.shape[2]):
            out[:, k] = np.bincount(self.mesh.elems.ravel(), weights=ve[:, :, k].ravel(), minlength=self.nn)
        out /= self.node_count[:, None]
        return out if vals.ndim > 1 else out[:, 0]

    def nodal_strain(self, u):
        ue = u[self.edofs]
        en = np.einsum("enij,ej->eni", self.Bnode, ue)              # Voigt (ne, 9, 3)
        out = np.zeros((self.nn, 3))
        for k in range(3):
            out[:, k] = np.bincount(self.mesh.elems.ravel(), weights=en[:, :, k].ravel(), minlength=self.nn)
        return out / self.node_count[:, None]


KEYS = ("fext", "dT_gp", "u_presc")


def _lerp(a, b, f):
    if b is None:
        return None
    if a is None:
        a = np.zeros_like(b)
    return a + f * (b - a)


def run_history(model, steps, state=None, u=None, callback=None, tol=1e-7, max_cuts=10, verbose=False):
    """steps: iterable of dicts {fext, dT_gp (or None), u_presc (or None), tag}.
    Each step is one increment; on non-convergence the increment is bisected
    (linear interpolation between the last converged load state and the target).
    callback(step_index, tag, u, state) is called after each completed step."""
    if state is None:
        state = model.new_state()
    if u is None:
        u = np.zeros(model.ndof)
    cur = {"fext": np.zeros(model.ndof), "dT_gp": None, "u_presc": None}
    total_it = 0
    for k, s in enumerate(steps):
        tgt = {key: s.get(key) for key in KEYS}
        h, cuts = 1.0, 0
        while True:
            trial = {key: _lerp(cur[key], tgt[key], h) for key in KEYS}
            try:
                u_new, st_new, nit = model.solve_step(u, state, trial["fext"], trial["dT_gp"],
                                                      trial["u_presc"], tol=tol)
            except (RuntimeError, np.linalg.LinAlgError) as err:
                cuts += 1
                if cuts > max_cuts:
                    raise
                h *= 0.5
                if verbose:
                    print(f"  step {k}: cut-back ({err}); h = {h}")
                continue
            u, state, cur = u_new, st_new, trial
            total_it += nit
            if h >= 1.0 - 1e-12:
                break
            h = min(1.0, 2.0 * h)          # fraction of the *remaining* distance
        if callback is not None:
            callback(k, s.get("tag"), u, state)
    return u, state, total_it
