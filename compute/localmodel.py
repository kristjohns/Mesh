"""Local solid model of the wellhead: HPWHH in conductor housing (LPWH).

* 2D (r,z) block-structured quad mesh per body, revolved through 180 deg -> half model
  with a symmetry plane (y = 0) containing the plane of bending.
* 8-node hexahedra with incompatible modes (Wilson/Taylor), 2x2x2 Gauss.
* Contact by node-to-segment penalty pairs (slave = finer HPWHH side):
    - landing shoulder (axial normal, sticking when closed)
    - preloaded lock ring (compression-only axial connector with pre-compression)
    - upper and lower radial contacts with initial clearances
* Loads on top of HPWHH applied through a distributing coupling (moment + shear).
* The same 2D mesh is also solved as an axisymmetric model for the preload step.
"""
import json
import os
import sys
import time
import numpy as np
import scipy.sparse as sp

os.environ.setdefault("PYPARDISO_MKL_RT", "/usr/local/lib/libmkl_rt.so.3")
import pypardiso  # noqa: E402

STEEL = (207e9, 0.3)
CEMENT = (10e9, 0.2)

R_BORE = 0.2381
R_CAS_O = 0.2540
R_HP_O = 0.345
R_RING = 0.400
R_LP_LOW_I = 0.356
R_LP_BORE = 0.405
R_GROOVE = 0.430
R_LP_O = 0.480
R_COND_I = 0.4191
R_COND_O = 0.4572

Z_BOT = -1.5
Z_TOC = 0.0
Z_COND_TOP = 0.8
Z_LP_TAPER = 1.1
Z_CAS_TOP = 1.2
Z_HP_TAPER = 1.5
Z_SHOULDER = 2.2
Z_RING_TOP = 2.45
Z_GROOVE_TOP = 2.52
Z_LP_TOP = 2.6
Z_HP_TOP = 3.6


# ---------------------------------------------------------------- 2D block mesher
class Mesh2D:
    def __init__(self):
        self.keys = {}
        self.pts = []
        self.grp = []
        self.quads = []
        self.qbody = []
        self.qmat = []

    def node(self, r, z, group):
        k = (round(r, 7), round(z, 7), group)
        if k not in self.keys:
            self.keys[k] = len(self.pts)
            self.pts.append((r, z))
            self.grp.append(group)
        return self.keys[k]

    def block(self, corners, nr, nz, body, mat, group_fn):
        (r00, z00), (r10, z10), (r11, z11), (r01, z01) = corners
        ids = np.zeros((nr + 1, nz + 1), int)
        for i in range(nr + 1):
            s = i / nr
            for j in range(nz + 1):
                t = j / nz
                r = (1 - s) * (1 - t) * r00 + s * (1 - t) * r10 + s * t * r11 + (1 - s) * t * r01
                z = (1 - s) * (1 - t) * z00 + s * (1 - t) * z10 + s * t * z11 + (1 - s) * t * z01
                ids[i, j] = self.node(r, z, group_fn(r, z))
        for i in range(nr):
            for j in range(nz):
                self.quads.append((ids[i, j], ids[i + 1, j], ids[i + 1, j + 1], ids[i, j + 1]))
                self.qbody.append(body)
                self.qmat.append(mat)


def rect(r0, r1, z0, z1):
    return [(r0, z0), (r1, z0), (r1, z1), (r0, z1)]


def build_profile(fine=1):
    m = Mesh2D()
    gi = lambda r, z: "I"
    go = lambda r, z: "O"

    def gc(r, z):
        if abs(r - R_CAS_O) < 1e-9:
            return "I"
        if abs(r - R_COND_I) < 1e-9:
            return "O"
        return "C"

    f = fine
    # ---- inner body: surface casing + HPWHH
    m.block(rect(R_BORE, R_CAS_O, Z_BOT, Z_TOC), 4, 15 * f, "casing", 0, gi)
    m.block(rect(R_BORE, R_CAS_O, Z_TOC, Z_CAS_TOP), 4, 24 * f, "casing", 0, gi)
    m.block([(R_BORE, Z_CAS_TOP), (R_CAS_O, Z_CAS_TOP), (R_HP_O, Z_HP_TAPER), (R_BORE, Z_HP_TAPER)],
            4, 10 * f, "hpwhh", 0, gi)
    m.block(rect(R_BORE, R_HP_O, Z_HP_TAPER, Z_SHOULDER), 4, 28 * f, "hpwhh", 0, gi)
    m.block(rect(R_BORE, R_HP_O, Z_SHOULDER, Z_RING_TOP), 4, 10 * f, "hpwhh", 0, gi)
    m.block(rect(R_HP_O, R_RING, Z_SHOULDER, Z_RING_TOP), 5, 10 * f, "hpwhh", 0, gi)
    m.block(rect(R_BORE, R_HP_O, Z_RING_TOP, Z_HP_TOP), 4, 30 * f, "hpwhh", 0, gi)
    # ---- cement (bonded to casing and conductor)
    m.block(rect(R_CAS_O, R_COND_I, Z_BOT, Z_TOC), 6, 15 * f, "cement", 1, gc)
    # ---- outer body: conductor + conductor housing (LPWH)
    m.block(rect(R_COND_I, R_COND_O, Z_BOT, Z_TOC), 5, 15 * f, "conductor", 0, go)
    m.block(rect(R_COND_I, R_COND_O, Z_TOC, Z_COND_TOP), 5, 16 * f, "conductor", 0, go)
    m.block([(R_COND_I, Z_COND_TOP), (R_COND_O, Z_COND_TOP), (R_LP_O, Z_LP_TAPER), (R_LP_LOW_I, Z_LP_TAPER)],
            5, 10 * f, "lpwh", 0, go)
    # lower body split so that r = R_LP_BORE is a node line
    m.block(rect(R_LP_LOW_I, R_LP_BORE, Z_LP_TAPER, Z_SHOULDER), 2, 36 * f, "lpwh", 0, go)
    m.block(rect(R_LP_BORE, R_LP_O, Z_LP_TAPER, Z_SHOULDER), 3, 36 * f, "lpwh", 0, go)
    m.block(rect(R_LP_BORE, R_LP_O, Z_SHOULDER, Z_RING_TOP), 3, 10 * f, "lpwh", 0, go)
    m.block(rect(R_GROOVE, R_LP_O, Z_RING_TOP, Z_GROOVE_TOP), 2, 3 * f, "lpwh", 0, go)
    m.block(rect(R_LP_BORE, R_LP_O, Z_GROOVE_TOP, Z_LP_TOP), 3, 3 * f, "lpwh", 0, go)
    # the r in [R_LP_BORE, R_GROOVE] part above the groove must connect to the r>R_GROOVE part:
    # nodes at (R_GROOVE, Z_GROOVE_TOP) are shared through the key, which is what we want.
    m.pts = np.array(m.pts)
    m.quads = np.array(m.quads)
    m.qbody = np.array(m.qbody)
    m.qmat = np.array(m.qmat)
    return m


# ---------------------------------------------------------------- element routines
G2 = np.array([-1, 1]) / np.sqrt(3)


def D_matrix(E, nu):
    lam = E * nu / ((1 + nu) * (1 - 2 * nu))
    mu = E / (2 * (1 + nu))
    D = np.zeros((6, 6))
    D[:3, :3] = lam
    D[np.arange(3), np.arange(3)] += 2 * mu
    D[3:, 3:] = np.eye(3) * mu
    return D


HEX_NAT = np.array([[-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
                    [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]], float)


def hex_shape_grad(xi):
    """dN/dxi (8x3) at natural point xi (3,)"""
    g = np.zeros((8, 3))
    for a in range(8):
        sa = HEX_NAT[a]
        f = 1 + sa * xi
        g[a, 0] = 0.125 * sa[0] * f[1] * f[2]
        g[a, 1] = 0.125 * sa[1] * f[0] * f[2]
        g[a, 2] = 0.125 * sa[2] * f[0] * f[1]
    return g


def B_from_grad(dN):
    """dN: (ne, n, 3) -> B (ne, 6, 3n) with Voigt order xx,yy,zz,xy,yz,zx"""
    ne, n, _ = dN.shape
    B = np.zeros((ne, 6, 3 * n))
    B[:, 0, 0::3] = dN[:, :, 0]
    B[:, 1, 1::3] = dN[:, :, 1]
    B[:, 2, 2::3] = dN[:, :, 2]
    B[:, 3, 0::3] = dN[:, :, 1]
    B[:, 3, 1::3] = dN[:, :, 0]
    B[:, 4, 1::3] = dN[:, :, 2]
    B[:, 4, 2::3] = dN[:, :, 1]
    B[:, 5, 0::3] = dN[:, :, 2]
    B[:, 5, 2::3] = dN[:, :, 0]
    return B


def hex8i_stiffness(X, Dm):
    """X: (ne, 8, 3) coordinates; Dm: (ne, 6, 6). Returns K (ne,24,24), recovery R (ne,9,24)."""
    ne = X.shape[0]
    Kuu = np.zeros((ne, 24, 24))
    Kua = np.zeros((ne, 24, 9))
    Kaa = np.zeros((ne, 9, 9))
    J0 = np.einsum("eai,aj->eij", X, hex_shape_grad(np.zeros(3)))  # dx/dxi at centre
    detJ0 = np.linalg.det(J0)
    J0inv = np.linalg.inv(J0)
    for x1 in G2:
        for x2 in G2:
            for x3 in G2:
                xi = np.array([x1, x2, x3])
                dNn = hex_shape_grad(xi)
                J = np.einsum("eai,aj->eij", X, dNn)
                detJ = np.linalg.det(J)
                Jinv = np.linalg.inv(J)
                dN = np.einsum("aj,eji->eai", dNn, Jinv)
                Bu = B_from_grad(dN)
                # incompatible modes P_k = 1 - xi_k^2, derivative wrt natural: -2 xi_k e_k
                dP = np.zeros((3, 3))
                for k in range(3):
                    dP[k, k] = -2 * xi[k]
                dPx = np.einsum("kj,eji->eki", dP, J0inv) * (detJ0 / detJ)[:, None, None]
                Ba = B_from_grad(dPx)
                w = detJ
                DBu = np.einsum("eij,ejk->eik", Dm, Bu)
                DBa = np.einsum("eij,ejk->eik", Dm, Ba)
                Kuu += np.einsum("eji,ejk->eik", Bu, DBu) * w[:, None, None]
                Kua += np.einsum("eji,ejk->eik", Bu, DBa) * w[:, None, None]
                Kaa += np.einsum("eji,ejk->eik", Ba, DBa) * w[:, None, None]
    Kaa_inv = np.linalg.inv(Kaa)
    Rrec = -np.einsum("eij,ekj->eik", Kaa_inv, Kua)  # alpha = R u   (ne,9,24)
    K = Kuu + np.einsum("eij,ejk->eik", Kua, Rrec)
    return K, Rrec


def hex8i_centre_stress(X, Dm, Rrec, ue):
    dNn = hex_shape_grad(np.zeros(3))
    J = np.einsum("eai,aj->eij", X, dNn)
    Jinv = np.linalg.inv(J)
    dN = np.einsum("aj,eji->eai", dNn, Jinv)
    Bu = B_from_grad(dN)
    # incompatible-mode derivatives vanish at the centre
    eps = np.einsum("eij,ej->ei", Bu, ue)
    return np.einsum("eij,ej->ei", Dm, eps)


def von_mises(s):
    sxx, syy, szz, sxy, syz, szx = s.T
    return np.sqrt(0.5 * ((sxx - syy) ** 2 + (syy - szz) ** 2 + (szz - sxx) ** 2) +
                   3 * (sxy ** 2 + syz ** 2 + szx ** 2))


# axisymmetric Q4 with incompatible modes (r,z), strains: rr, zz, tt, rz
Q_NAT = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1]], float)


def axi_D(E, nu):
    lam = E * nu / ((1 + nu) * (1 - 2 * nu))
    mu = E / (2 * (1 + nu))
    D = np.zeros((4, 4))
    D[:3, :3] = lam
    D[np.arange(3), np.arange(3)] += 2 * mu
    D[3, 3] = mu
    return D


def axi_q4i_stiffness(X, Dm):
    ne = X.shape[0]
    Kuu = np.zeros((ne, 8, 8))
    Kua = np.zeros((ne, 8, 4))
    Kaa = np.zeros((ne, 4, 4))

    def grads(xi):
        g = np.zeros((4, 2))
        N = np.zeros(4)
        for a in range(4):
            s = Q_NAT[a]
            N[a] = 0.25 * (1 + s[0] * xi[0]) * (1 + s[1] * xi[1])
            g[a, 0] = 0.25 * s[0] * (1 + s[1] * xi[1])
            g[a, 1] = 0.25 * s[1] * (1 + s[0] * xi[0])
        return N, g

    _, g0 = grads(np.zeros(2))
    J0 = np.einsum("eai,aj->eij", X, g0)
    detJ0 = np.linalg.det(J0)
    J0inv = np.linalg.inv(J0)
    for x1 in G2:
        for x2 in G2:
            xi = np.array([x1, x2])
            N, g = grads(xi)
            J = np.einsum("eai,aj->eij", X, g)
            detJ = np.linalg.det(J)
            Jinv = np.linalg.inv(J)
            dN = np.einsum("aj,eji->eai", g, Jinv)
            r = X[:, :, 0] @ N
            Bu = np.zeros((ne, 4, 8))
            Bu[:, 0, 0::2] = dN[:, :, 0]
            Bu[:, 1, 1::2] = dN[:, :, 1]
            Bu[:, 2, 0::2] = N[None, :] / r[:, None]
            Bu[:, 3, 0::2] = dN[:, :, 1]
            Bu[:, 3, 1::2] = dN[:, :, 0]
            dP = np.diag(-2 * xi)
            dPx = np.einsum("kj,eji->eki", dP, J0inv) * (detJ0 / detJ)[:, None, None]
            P = 1 - xi ** 2
            Ba = np.zeros((ne, 4, 4))
            # modes for u_r: cols 0,1 ; u_z: cols 2,3
            Ba[:, 0, 0:2] = dPx[:, :, 0]
            Ba[:, 3, 0:2] = dPx[:, :, 1]
            Ba[:, 2, 0:2] = P[None, :] / r[:, None]
            Ba[:, 1, 2:4] = dPx[:, :, 1]
            Ba[:, 3, 2:4] = dPx[:, :, 0]
            w = detJ * r
            DBu = np.einsum("eij,ejk->eik", Dm, Bu)
            DBa = np.einsum("eij,ejk->eik", Dm, Ba)
            Kuu += np.einsum("eji,ejk->eik", Bu, DBu) * w[:, None, None]
            Kua += np.einsum("eji,ejk->eik", Bu, DBa) * w[:, None, None]
            Kaa += np.einsum("eji,ejk->eik", Ba, DBa) * w[:, None, None]
    Rrec = -np.einsum("eij,ekj->eik", np.linalg.inv(Kaa), Kua)
    return Kuu + np.einsum("eij,ejk->eik", Kua, Rrec), Rrec


def axi_centre_stress(X, Dm, ue):
    N = np.full(4, 0.25)
    g = 0.25 * Q_NAT.copy()
    J = np.einsum("eai,aj->eij", X, g)
    dN = np.einsum("aj,eji->eai", g, np.linalg.inv(J))
    r = X[:, :, 0] @ N
    ne = X.shape[0]
    Bu = np.zeros((ne, 4, 8))
    Bu[:, 0, 0::2] = dN[:, :, 0]
    Bu[:, 1, 1::2] = dN[:, :, 1]
    Bu[:, 2, 0::2] = N[None, :] / r[:, None]
    Bu[:, 3, 0::2] = dN[:, :, 1]
    Bu[:, 3, 1::2] = dN[:, :, 0]
    eps = np.einsum("eij,ej->ei", Bu, ue)
    s = np.einsum("eij,ej->ei", Dm, eps)  # rr, zz, tt, rz
    srr, szz, stt, srz = s.T
    vm = np.sqrt(0.5 * ((srr - szz) ** 2 + (szz - stt) ** 2 + (stt - srr) ** 2) + 3 * srz ** 2)
    return s, vm


# ---------------------------------------------------------------- contact pair definitions (2D)
def line_nodes(m, cond, group):
    idx = [i for i, (p, g) in enumerate(zip(m.pts, m.grp)) if g == group and cond(p[0], p[1])]
    return np.array(idx)


def make_pairs2d(m):
    """Return list of 2D pair definitions: slave node, master nodes (a,b), weight, normal(r,z), g0,
    kind, tributary length in the (r,z) plane (dl) and its mean radius (for area)."""
    pts = m.pts
    pairs = []

    def segs(master_idx, coord):
        order = np.argsort(pts[master_idx, coord])
        return master_idx[order]

    def project(sl, mast, coord):
        c = pts[sl, coord]
        mc = pts[mast, coord]
        if c < mc[0] - 1e-9 or c > mc[-1] + 1e-9:
            return None
        k = np.searchsorted(mc, c) - 1
        k = min(max(k, 0), len(mc) - 2)
        w = (c - mc[k]) / (mc[k + 1] - mc[k])
        return mast[k], mast[k + 1], w

    def trib(slaves, coord):
        c = pts[slaves, coord]
        o = np.argsort(c)
        c = c[o]
        t = np.zeros(len(c))
        t[1:] += 0.5 * np.diff(c)
        t[:-1] += 0.5 * np.diff(c)
        out = np.zeros(len(c))
        out[o] = t
        return out

    # landing shoulder: slave = HPWHH ring underside (z = Z_SHOULDER, r in [R_HP_O, R_RING])
    sl = line_nodes(m, lambda r, z: abs(z - Z_SHOULDER) < 1e-9 and R_HP_O - 1e-9 <= r <= R_RING + 1e-9, "I")
    ma = segs(line_nodes(m, lambda r, z: abs(z - Z_SHOULDER) < 1e-9 and r <= R_LP_BORE + 1e-9, "O"), 0)
    tr = trib(sl, 0)
    for s, t in zip(sl, tr):
        pr = project(s, ma, 0)
        if pr is None:
            continue
        pairs.append(dict(s=s, a=pr[0], b=pr[1], w=pr[2], n=(0.0, -1.0), g0=0.0, kind="shoulder",
                          dl=t, r=pts[s, 0]))
    # lock ring connector: slave = ring top (z = Z_RING_TOP, r in [0.367, R_RING]),
    # master = groove upper face (z = Z_GROOVE_TOP, r in [R_LP_BORE, R_GROOVE]) mapped linearly
    sl = line_nodes(m, lambda r, z: abs(z - Z_RING_TOP) < 1e-9 and 0.366 <= r <= R_RING + 1e-9, "I")
    sl = sl[np.argsort(pts[sl, 0])]
    ma = segs(line_nodes(m, lambda r, z: abs(z - Z_GROOVE_TOP) < 1e-9 and R_LP_BORE - 1e-9 <= r <= R_GROOVE + 1e-9, "O"), 0)
    tr = trib(sl, 0)
    for k, (s, t) in enumerate(zip(sl, tr)):
        s_map = k / (len(sl) - 1)
        c = pts[ma[0], 0] + s_map * (pts[ma[-1], 0] - pts[ma[0], 0])
        kk = min(np.searchsorted(pts[ma, 0], c) - 1, len(ma) - 2)
        kk = max(kk, 0)
        w = (c - pts[ma[kk], 0]) / (pts[ma[kk + 1], 0] - pts[ma[kk], 0])
        pairs.append(dict(s=s, a=ma[kk], b=ma[kk + 1], w=w, n=(0.0, 1.0), g0=None, kind="lock",
                          dl=t, r=pts[s, 0]))
    # upper radial contact: ring OD (r = R_RING) vs LPWH bore (r = R_LP_BORE)
    sl = line_nodes(m, lambda r, z: abs(r - R_RING) < 1e-9 and Z_SHOULDER - 1e-9 <= z <= Z_RING_TOP + 1e-9, "I")
    ma = segs(line_nodes(m, lambda r, z: abs(r - R_LP_BORE) < 1e-9 and Z_SHOULDER - 1e-9 <= z <= Z_RING_TOP + 1e-9, "O"), 1)
    tr = trib(sl, 1)
    for s, t in zip(sl, tr):
        pr = project(s, ma, 1)
        if pr is None:
            continue
        pairs.append(dict(s=s, a=pr[0], b=pr[1], w=pr[2], n=(1.0, 0.0), g0=R_LP_BORE - R_RING,
                          kind="upper", dl=t, r=pts[s, 0]))
    # lower radial contact: HPWHH body OD vs LPWH lower ID
    sl = line_nodes(m, lambda r, z: abs(r - R_HP_O) < 1e-9 and Z_HP_TAPER - 1e-9 <= z <= Z_SHOULDER - 1e-9, "I")
    ma = segs(line_nodes(m, lambda r, z: abs(r - R_LP_LOW_I) < 1e-9 and Z_LP_TAPER - 1e-9 <= z <= Z_SHOULDER + 1e-9, "O"), 1)
    tr = trib(sl, 1)
    for s, t in zip(sl, tr):
        pr = project(s, ma, 1)
        if pr is None:
            continue
        pairs.append(dict(s=s, a=pr[0], b=pr[1], w=pr[2], n=(1.0, 0.0), g0=R_LP_LOW_I - R_HP_O,
                          kind="lower", dl=t, r=pts[s, 0]))
    return pairs


K_AREA = 2.0e13      # penalty stiffness per unit contact area [N/m^3]
LOCK_K_AREA = 207e9 / 0.07 * 0.6   # lock-ring axial stiffness per unit area [N/m^3]
LOCK_DELTA0 = 0.30e-3  # lock-ring pre-compression [m]


# ---------------------------------------------------------------- 3D model
class Solid3D:
    def __init__(self, m, nth=36):
        self.m = m
        self.nth = nth
        th = np.linspace(0, np.pi, nth + 1)
        self.th = th
        n2 = len(m.pts)
        self.n2 = n2
        r, z = m.pts[:, 0], m.pts[:, 1]
        X = np.zeros((n2 * (nth + 1), 3))
        for k, t in enumerate(th):
            X[k * n2:(k + 1) * n2] = np.c_[r * np.cos(t), r * np.sin(t), z]
        self.X = X
        self.nn = len(X)
        q = m.quads
        hexes = []
        mats = []
        self.hex_q = []
        self.hex_k = []
        for k in range(nth):
            o0, o1 = k * n2, (k + 1) * n2
            h = np.c_[q[:, 0] + o0, q[:, 1] + o0, q[:, 1] + o1, q[:, 0] + o1,
                      q[:, 3] + o0, q[:, 2] + o0, q[:, 2] + o1, q[:, 3] + o1]
            hexes.append(h)
            mats.append(m.qmat)
            self.hex_q.append(np.arange(len(q)))
            self.hex_k.append(np.full(len(q), k))
        self.hex = np.vstack(hexes)
        self.mat = np.concatenate(mats)
        self.hex_q = np.concatenate(self.hex_q)
        self.hex_k = np.concatenate(self.hex_k)
        self.ndof = 3 * self.nn

    def node(self, i2, k):
        return k * self.n2 + i2

    def assemble(self):
        t0 = time.time()
        Xe = self.X[self.hex]
        Dm = np.where(self.mat[:, None, None] == 0, D_matrix(*STEEL), D_matrix(*CEMENT))
        self.Dm = Dm
        Ke, self.Rrec = hex8i_stiffness(Xe, Dm)
        dofs = (3 * self.hex[:, :, None] + np.arange(3)[None, None, :]).reshape(len(self.hex), 24)
        self.edofs = dofs
        I = np.repeat(dofs, 24, axis=1).ravel()
        J = np.tile(dofs, (1, 24)).ravel()
        self.K = sp.csr_matrix((Ke.ravel(), (I, J)), shape=(self.ndof, self.ndof))
        print(f"assembled {len(self.hex)} hexes, {self.ndof} dofs in {time.time() - t0:.1f}s")

    def build_pairs(self, pairs2d):
        """Expand the 2D pair definitions around the circumference."""
        self.pairs = []
        dth = self.th[1] - self.th[0]
        for k, t in enumerate(self.th):
            wth = dth * (0.5 if k in (0, self.nth) else 1.0)
            c, s = np.cos(t), np.sin(t)
            for p in pairs2d:
                nr, nz = p["n"]
                nvec = np.array([nr * c, nr * s, nz])
                area = p["dl"] * p["r"] * wth
                d = dict(p)
                d.update(S=self.node(p["s"], k), A=self.node(p["a"], k), B=self.node(p["b"], k),
                         nvec=nvec, area=area, k=k, theta=t)
                if p["kind"] == "shoulder":
                    d["tvecs"] = [np.array([c, s, 0.0]), np.array([-s, c, 0.0])]
                self.pairs.append(d)

    def pair_vectors(self, p, v):
        S, A, B, w = p["S"], p["A"], p["B"], p["w"]
        dofs = np.r_[3 * S + np.arange(3), 3 * A + np.arange(3), 3 * B + np.arange(3)]
        G = np.r_[v, -(1 - w) * v, -w * v]
        return dofs, G

    def bcs(self):
        fixed = []
        z = self.X[:, 2]
        bot = np.where(np.abs(z - Z_BOT) < 1e-9)[0]
        for i in bot:
            fixed += [3 * i, 3 * i + 1, 3 * i + 2]
        for k in (0, self.nth):
            for i2 in range(self.n2):
                fixed.append(3 * self.node(i2, k) + 1)
        self.fixed = np.unique(fixed)
        self.free = np.setdiff1d(np.arange(self.ndof), self.fixed)

    def top_load(self, M_half, H_half, N_half=0.0):
        """Distributing coupling on the HPWHH top face: moment about y, shear in x, axial."""
        F = np.zeros(self.ndof)
        top2 = np.where((np.abs(self.m.pts[:, 1] - Z_HP_TOP) < 1e-9) & (np.array(self.m.grp) == "I"))[0]
        rr = self.m.pts[top2, 0]
        o = np.argsort(rr)
        top2, rr = top2[o], rr[o]
        wr = np.zeros(len(rr))
        wr[1:] += 0.5 * np.diff(rr)
        wr[:-1] += 0.5 * np.diff(rr)
        dth = self.th[1] - self.th[0]
        ids, xs, ws = [], [], []
        for k, t in enumerate(self.th):
            wt = dth * (0.5 if k in (0, self.nth) else 1.0)
            for i2, r, w in zip(top2, rr, wr):
                ids.append(self.node(i2, k))
                xs.append(r * np.cos(t))
                ws.append(w * r * wt)
        ids, xs, ws = np.array(ids), np.array(xs), np.array(ws)
        # moment that drives the top towards +x (tension on the -x side): f_z = -c x
        cM = M_half / np.sum(ws * xs ** 2)
        F[3 * ids + 2] += -cM * xs * ws
        F[3 * ids + 0] += H_half * ws / ws.sum()
        F[3 * ids + 2] += -N_half * ws / ws.sum()
        self.top_ids = ids
        return F

    def solve_contact(self, F, state=None, maxit=40, verbose=True):
        """Penalty active-set iterations. state: dict pair_index -> active flag."""
        npairs = len(self.pairs)
        if state is None:
            state = np.array([p["kind"] in ("shoulder", "lock") for p in self.pairs])
        rows, cols, vals, rhs_extra = [], [], [], np.zeros(self.ndof)
        for it in range(maxit):
            rows, cols, vals = [], [], []
            rhs = F.copy()
            for i, p in enumerate(self.pairs):
                if not state[i]:
                    continue
                if p["kind"] == "lock":
                    kp, g0 = LOCK_K_AREA * p["area"], -LOCK_DELTA0
                else:
                    kp, g0 = K_AREA * p["area"], p["g0"]
                dofs, G = self.pair_vectors(p, p["nvec"])
                rows.append(np.repeat(dofs, 9))
                cols.append(np.tile(dofs, 9))
                vals.append(kp * np.outer(G, G).ravel())
                rhs[dofs] += kp * g0 * G
                if p["kind"] == "shoulder":
                    for tv in p["tvecs"]:
                        dofs, Gt = self.pair_vectors(p, tv)
                        rows.append(np.repeat(dofs, 9))
                        cols.append(np.tile(dofs, 9))
                        vals.append(kp * np.outer(Gt, Gt).ravel())
            if rows:
                Kc = sp.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))),
                                   shape=(self.ndof, self.ndof))
                Kt = self.K + Kc
            else:
                Kt = self.K
            Kff = Kt[self.free][:, self.free]
            u = np.zeros(self.ndof)
            u[self.free] = pypardiso.spsolve(Kff.tocsr(), rhs[self.free])
            # update active set
            new = state.copy()
            for i, p in enumerate(self.pairs):
                dofs, G = self.pair_vectors(p, p["nvec"])
                c = G @ u[dofs]
                g0 = -LOCK_DELTA0 if p["kind"] == "lock" else p["g0"]
                pen = c - g0
                new[i] = pen > 0
                p["pen"] = pen
            changed = int(np.sum(new != state))
            if verbose:
                print(f"   contact iteration {it}: changes {changed}, active {int(new.sum())}/{npairs}")
            state = new
            if changed == 0:
                break
        self.u = u
        return u, state

    def pair_forces(self, u, state):
        out = []
        for i, p in enumerate(self.pairs):
            dofs, G = self.pair_vectors(p, p["nvec"])
            c = G @ u[dofs]
            if p["kind"] == "lock":
                kp, g0 = LOCK_K_AREA * p["area"], -LOCK_DELTA0
            else:
                kp, g0 = K_AREA * p["area"], p["g0"]
            f = kp * (c - g0) if state[i] else 0.0
            out.append(dict(kind=p["kind"], theta=p["theta"], r=p["r"], f=f, pressure=f / p["area"],
                            k=p["k"], z=self.m.pts[p["s"], 1], gap=g0 - c))
        return out

    def stresses(self, u):
        ue = u[self.edofs]
        s = hex8i_centre_stress(self.X[self.hex], self.Dm, self.Rrec, ue)
        vm = von_mises(s)
        # nodal average
        acc = np.zeros(self.nn)
        cnt = np.zeros(self.nn)
        for a in range(8):
            np.add.at(acc, self.hex[:, a], vm)
            np.add.at(cnt, self.hex[:, a], 1)
        return vm, acc / np.maximum(cnt, 1), s

    def section_rotation(self, u, group, z0):
        """Rotation about y of the ring of nodes at elevation z0 in a body (plane fit of u_z vs x)."""
        sel2 = np.where((np.abs(self.m.pts[:, 1] - z0) < 1e-9) & (np.array(self.m.grp) == group))[0]
        ids = np.array([self.node(i2, k) for k in range(self.nth + 1) for i2 in sel2])
        x = self.X[ids, 0]
        uz = u[3 * ids + 2]
        A = np.c_[x, np.ones_like(x)]
        slope = np.linalg.lstsq(A, uz, rcond=None)[0][0]
        return -slope  # positive for the top moving to +x


# ---------------------------------------------------------------- axisymmetric model (preload only)
class Axi:
    def __init__(self, m):
        self.m = m
        self.nn = len(m.pts)
        self.ndof = 2 * self.nn

    def assemble(self):
        m = self.m
        Xe = m.pts[m.quads]
        Dm = np.where(m.qmat[:, None, None] == 0, axi_D(*STEEL), axi_D(*CEMENT))
        self.Dm = Dm
        Ke, self.Rrec = axi_q4i_stiffness(Xe, Dm)
        dofs = (2 * m.quads[:, :, None] + np.arange(2)[None, None, :]).reshape(len(m.quads), 8)
        self.edofs = dofs
        I = np.repeat(dofs, 8, axis=1).ravel()
        J = np.tile(dofs, (1, 8)).ravel()
        self.K = sp.csr_matrix((Ke.ravel(), (I, J)), shape=(self.ndof, self.ndof))

    def solve_preload(self, pairs2d):
        m = self.m
        fixed = []
        for i, (r, z) in enumerate(m.pts):
            if abs(z - Z_BOT) < 1e-9:
                fixed += [2 * i, 2 * i + 1]
        free = np.setdiff1d(np.arange(self.ndof), fixed)
        state = np.array([p["kind"] in ("shoulder", "lock") for p in pairs2d])
        for it in range(30):
            rows, cols, vals = [], [], []
            rhs = np.zeros(self.ndof)
            for i, p in enumerate(pairs2d):
                if not state[i]:
                    continue
                area = p["dl"] * p["r"]  # per radian
                if p["kind"] == "lock":
                    kp, g0 = LOCK_K_AREA * area, -LOCK_DELTA0
                else:
                    kp, g0 = K_AREA * area, p["g0"]
                vecs = [np.array(p["n"])]
                if p["kind"] == "shoulder":
                    vecs.append(np.array([1.0, 0.0]))
                for v in vecs:
                    dofs = np.r_[2 * p["s"] + np.arange(2), 2 * p["a"] + np.arange(2), 2 * p["b"] + np.arange(2)]
                    G = np.r_[v, -(1 - p["w"]) * v, -p["w"] * v]
                    rows.append(np.repeat(dofs, 6))
                    cols.append(np.tile(dofs, 6))
                    vals.append(kp * np.outer(G, G).ravel())
                    if v is vecs[0]:
                        rhs[dofs] += kp * g0 * G
            Kc = sp.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))),
                               shape=(self.ndof, self.ndof))
            Kt = (self.K + Kc)[free][:, free]
            u = np.zeros(self.ndof)
            u[free] = pypardiso.spsolve(Kt.tocsr(), rhs[free])
            new = state.copy()
            for i, p in enumerate(pairs2d):
                v = np.array(p["n"])
                dofs = np.r_[2 * p["s"] + np.arange(2), 2 * p["a"] + np.arange(2), 2 * p["b"] + np.arange(2)]
                G = np.r_[v, -(1 - p["w"]) * v, -p["w"] * v]
                g0 = -LOCK_DELTA0 if p["kind"] == "lock" else p["g0"]
                new[i] = (G @ u[dofs] - g0) > 0
            if np.all(new == state):
                break
            state = new
        self.u = u
        ue = u[self.edofs]
        s, vm = axi_centre_stress(m.pts[m.quads], self.Dm, ue)
        acc = np.zeros(self.nn)
        cnt = np.zeros(self.nn)
        for a in range(4):
            np.add.at(acc, m.quads[:, a], vm)
            np.add.at(cnt, m.quads[:, a], 1)
        # preload: total lock force (full circumference)
        P = 0.0
        for i, p in enumerate(pairs2d):
            if p["kind"] == "lock" and state[i]:
                v = np.array(p["n"])
                dofs = np.r_[2 * p["s"] + np.arange(2), 2 * p["a"] + np.arange(2), 2 * p["b"] + np.arange(2)]
                G = np.r_[v, -(1 - p["w"]) * v, -p["w"] * v]
                P += LOCK_K_AREA * p["dl"] * p["r"] * (G @ u[dofs] + LOCK_DELTA0) * 2 * np.pi
        return vm, acc / np.maximum(cnt, 1), P


def surface_export(model, vm_nodal_list, u_list):
    """Boundary surface of the half model (revolved boundary edges + symmetry-plane faces)."""
    m = model.m
    # boundary edges of the 2D mesh (edges belonging to one quad); note quads of different
    # bodies that touch at contact lines have distinct nodes, so contact faces are boundaries.
    edges = {}
    for qi, q in enumerate(m.quads):
        for a, b in [(0, 1), (1, 2), (2, 3), (3, 0)]:
            key = tuple(sorted((q[a], q[b])))
            edges.setdefault(key, []).append((qi, q[a], q[b]))
    bedges = [v[0] for k, v in edges.items() if len(v) == 1]
    used2 = sorted(set([e[1] for e in bedges] + [e[2] for e in bedges]))
    tris = []
    vid = {}
    verts = []

    def V(i2, k):
        key = (i2, k)
        if key not in vid:
            vid[key] = len(verts)
            verts.append(model.node(i2, k))
        return vid[key]

    body_of_node = {}
    for qi, q in enumerate(m.quads):
        for n in q:
            body_of_node[n] = m.qbody[qi]
    quads = []
    quad_body = []
    for (qi, a, b) in bedges:
        for k in range(model.nth):
            quads.append((V(a, k), V(b, k), V(b, k + 1), V(a, k + 1)))
            quad_body.append(m.qbody[qi])
    # symmetry planes: 2D quads at k = 0 and k = nth
    for k in (0, model.nth):
        for qi, q in enumerate(m.quads):
            v = [V(n, k) for n in q]
            quads.append(tuple(v) if k == model.nth else (v[0], v[3], v[2], v[1]))
            quad_body.append(m.qbody[qi])
    verts = np.array(verts)
    out = dict(X=np.round(model.X[verts], 5).ravel().tolist(),
               quads=np.array(quads).ravel().tolist(),
               quad_body=quad_body,
               states=[])
    for vm, u in zip(vm_nodal_list, u_list):
        U = u.reshape(-1, 3)[verts]
        out["states"].append(dict(vm=np.round(vm[verts] / 1e6, 2).tolist(),
                                  u=np.round(U, 7).ravel().tolist()))
    # mesh edges to draw on the surface: revolved boundary-edge lines at each theta station and
    # the circumferential lines through boundary nodes
    return out


def main():
    m = build_profile(fine=1)
    print("2D nodes", len(m.pts), "quads", len(m.quads))
    pairs2d = make_pairs2d(m)
    from collections import Counter
    print("pairs:", Counter(p["kind"] for p in pairs2d))

    # ---- axisymmetric preload solution
    t0 = time.time()
    ax = Axi(m)
    ax.assemble()
    vm_ax_el, vm_ax_n, P_ax = ax.solve_preload(pairs2d)
    print(f"axisymmetric: preload {P_ax / 1e6:.2f} MN, max vM {vm_ax_el.max() / 1e6:.1f} MPa "
          f"({time.time() - t0:.1f}s)")

    # ---- 3D half model
    s3 = Solid3D(m, nth=36)
    s3.assemble()
    s3.build_pairs(pairs2d)
    s3.bcs()
    results = []
    M_list = [float(x) for x in np.arange(0, 3.0001e6, 0.25e6)]
    state = None
    vm_states, u_states = [], []
    for M in M_list:
        H = M / 13.0
        F = s3.top_load(M / 2, H / 2)
        t0 = time.time()
        u, state = s3.solve_contact(F, state=state, verbose=False)
        pf = s3.pair_forces(u, state)
        vm_el, vm_n, _ = s3.stresses(u)
        rot_hp = s3.section_rotation(u, "I", Z_RING_TOP)
        rot_lp = s3.section_rotation(u, "O", Z_SHOULDER)
        rot_top = s3.section_rotation(u, "I", Z_HP_TOP)
        lock_total = 2 * sum(p["f"] for p in pf if p["kind"] == "lock")
        sh_total = 2 * sum(p["f"] for p in pf if p["kind"] == "shoulder")
        # shoulder line force per unit circumference vs theta
        th_line = []
        for k in range(s3.nth + 1):
            fs = [p for p in pf if p["kind"] == "shoulder" and p["k"] == k]
            ftot = sum(p["f"] for p in fs)
            wth = (s3.th[1] - s3.th[0]) * (0.5 if k in (0, s3.nth) else 1)
            line = ftot / (wth * 0.378)  # N per metre of circumference at mean radius
            pmax = max(p["pressure"] for p in fs)
            th_line.append(dict(theta=float(s3.th[k]), line=float(line), pmax=float(pmax)))
        open_frac = np.mean([t["line"] <= 1e-6 for t in th_line])
        upper = [p for p in pf if p["kind"] == "upper" and p["f"] > 0]
        res = dict(M=M, H=H, rot_rel=rot_hp - rot_lp, rot_top=rot_top, lock=lock_total,
                   shoulder=sh_total, open_frac=float(open_frac), vm_max=float(vm_el.max()),
                   upper_force=2 * float(sum(p["f"] for p in upper)), shoulder_theta=th_line)
        results.append(res)
        vm_states.append(vm_n)
        u_states.append(u.copy())
        print(f"M={M / 1e6:.2f} MNm: lock {lock_total / 1e6:.2f} MN, shoulder {sh_total / 1e6:.2f} MN, "
              f"rel.rot {1e3 * (rot_hp - rot_lp):.4f} mrad, open {open_frac * 100:.0f}%, "
              f"upper {res['upper_force'] / 1e3:.0f} kN, vM max {vm_el.max() / 1e6:.0f} MPa "
              f"({time.time() - t0:.1f}s)")

    # axisymmetric vs 3D at the preload state: compare nodal von Mises on the theta = 90 deg section
    k90 = s3.nth // 2
    vm3_sec = np.array([vm_states[0][s3.node(i2, k90)] for i2 in range(s3.n2)])
    hp = np.array([b in ("hpwhh", "lpwh") for b in m.qbody])
    nodes_hp = np.unique(m.quads[hp])
    diff_max = abs(vm3_sec[nodes_hp].max() - vm_ax_n[nodes_hp].max()) / vm_ax_n[nodes_hp].max()
    print(f"preload: max nodal vM 3D {vm3_sec[nodes_hp].max() / 1e6:.1f} MPa, axisym "
          f"{vm_ax_n[nodes_hp].max() / 1e6:.1f} MPa, diff {100 * diff_max:.2f}%")

    data = dict(profile=dict(pts=np.round(m.pts, 6).tolist(), quads=m.quads.tolist(),
                             body=m.qbody.tolist(), grp=m.grp),
                pairs2d=[dict(kind=p["kind"], s=int(p["s"]), r=float(p["r"]),
                              z=float(m.pts[p["s"], 1])) for p in pairs2d],
                results=results,
                axi=dict(vm_nodal=np.round(vm_ax_n / 1e6, 2).tolist(), preload=P_ax,
                         vm3_section=np.round(vm3_sec / 1e6, 2).tolist(), diff=diff_max),
                nth=s3.nth, n3d_hex=int(len(s3.hex)), n3d_dof=int(s3.ndof), n2d_quad=int(len(m.quads)))
    with open("/home/user/Mesh/video/data/wellhead_local.json", "w") as fh:
        json.dump(data, fh)
    surf = surface_export(s3, vm_states, u_states)
    surf["M"] = M_list
    with open("/home/user/Mesh/video/data/wellhead_surface.json", "w") as fh:
        json.dump(surf, fh)
    print("written")


if __name__ == "__main__":
    main()
