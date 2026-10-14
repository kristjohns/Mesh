"""Cantilever element-type study (3D solid elements).

Clamped cantilever, L=10, b=h=1, tip shear load on the end face.
Compares TET4, TET10, HEX8 (full integration), HEX8 (reduced, 1-point),
HEX20 (serendipity) for different numbers of elements through the thickness.
Outputs normalized tip deflections and deformed edge polylines for the video.
"""
import json
import numpy as np
from scipy.sparse.linalg import spsolve
from skfem import (MeshHex, MeshTet, ElementVector, ElementHex1, ElementHexS2,
                   ElementTetP1, ElementTetP2, Basis, FacetBasis, asm, condense,
                   LinearForm)
from skfem.models.elasticity import linear_elasticity, lame_parameters

L, B, H = 10.0, 1.0, 1.0
E, NU, P = 1000.0, 0.3, 1.0

CASES = {
    "TET4":  dict(mesh="tet", elem=ElementTetP1, intorder=2),
    "TET10": dict(mesh="tet", elem=ElementTetP2, intorder=4),
    "HEX8":  dict(mesh="hex", elem=ElementHex1, intorder=2),
    "HEX8R": dict(mesh="hex", elem=ElementHex1, intorder=1),
    "HEX20": dict(mesh="hex", elem=ElementHexS2, intorder=4),
    "HEX20R": dict(mesh="hex", elem=ElementHexS2, intorder=2),
}


def make_mesh(kind, n):
    xs = np.linspace(0, L, 10 * n + 1)
    ys = np.linspace(0, B, n + 1)
    zs = np.linspace(0, H, n + 1)
    if kind == "hex":
        return MeshHex.init_tensor(xs, ys, zs)
    return MeshTet.init_tensor(xs, ys, zs)


def solve(case, n, hourglass_eps=0.0):
    c = CASES[case]
    m = make_mesh(c["mesh"], n)
    e = ElementVector(c["elem"]())
    if c["mesh"] == "hex" and c["intorder"] == 1:
        # one-point (reduced) integration at the element centre
        ib = Basis(m, e, quadrature=(np.array([[0.5], [0.5], [0.5]]), np.array([1.0])))
    else:
        ib = Basis(m, e, intorder=c["intorder"])
    lam, mu = lame_parameters(E, NU)
    K = asm(linear_elasticity(lam, mu), ib)
    if hourglass_eps > 0:
        # weak artificial stiffness (like a too-small hourglass control)
        ibf = Basis(m, e, intorder=2)
        K = K + hourglass_eps * asm(linear_elasticity(lam, mu), ibf)
    fb = FacetBasis(m, e, facets=m.facets_satisfying(lambda x: np.isclose(x[0], L)),
                    intorder=max(c["intorder"], 2) + 1)

    @LinearForm
    def traction(v, w):
        return -P / (B * H) * v.value[2]

    f = asm(traction, fb)
    D = ib.get_dofs(lambda x: np.isclose(x[0], 0.0)).all()
    try:
        Kc, fc, xc, I = condense(K, f, D=D)
        u = np.zeros(K.shape[0])
        u[I] = spsolve(Kc.tocsc(), fc)
        if not np.all(np.isfinite(u)):
            raise RuntimeError("non-finite")
    except Exception as ex:  # singular
        print("solve failed", case, n, ex)
        return None
    # tip deflection: average w over the end-face corner nodes
    tipn = np.where(np.isclose(m.p[0], L))[0]
    w = u[ib.nodal_dofs[2, tipn]].mean()
    return dict(mesh=m, basis=ib, u=u, w=w, ndof=K.shape[0])


def edges_polylines(res, nsamp=7):
    """Sample every boundary edge of the mesh, return undeformed points and displacements."""
    m, ib, u = res["mesh"], res["basis"], res["u"]
    # boundary edges: edges whose both nodes lie on the outer surface
    edges = m.edges.T
    p = m.p
    on_b = (np.isclose(p[1], 0) | np.isclose(p[1], B) | np.isclose(p[2], 0) |
            np.isclose(p[2], H) | np.isclose(p[0], 0) | np.isclose(p[0], L))
    keep = []
    for a, b in edges:
        pa, pb = p[:, a], p[:, b]
        mid = 0.5 * (pa + pb)
        # an edge is on the surface if its midpoint is on one of the 6 faces
        if (np.isclose(mid[1], 0) or np.isclose(mid[1], B) or np.isclose(mid[2], 0)
                or np.isclose(mid[2], H)):
            keep.append((a, b))
    s = np.linspace(0, 1, nsamp)
    pts = []
    for a, b in keep:
        for si in s:
            pts.append(p[:, a] * (1 - si) + p[:, b] * si)
    pts = np.array(pts).T
    # nudge points slightly inside to make the probe robust
    ctr = np.array([[L / 2], [B / 2], [H / 2]])
    pts_in = pts + (ctr - pts) * 1e-9
    P = ib.probes(pts_in)
    disp = (P @ u).reshape(3, -1) if (P @ u).size == 3 * pts.shape[1] else None
    if disp is None:
        raise RuntimeError("probe shape")
    return dict(npl=len(keep), nsamp=nsamp,
                p=np.round(pts.T, 5).tolist(), d=np.round(disp.T, 6).tolist())


def main():
    out = {"L": L, "B": B, "H": H, "E": E, "nu": NU, "P": P}
    I = B * H ** 3 / 12
    G = E / (2 * (1 + NU))
    w_beam = P * L ** 3 / (3 * E * I) + P * L / (5 / 6 * G * B * H)
    ref = solve("HEX20", 6)
    out["w_ref"] = float(-ref["w"])
    out["w_beam"] = w_beam
    print("reference HEX20 n=6:", -ref["w"], "Timoshenko beam:", w_beam)
    conv = {}
    for case in ["TET4", "TET10", "HEX8", "HEX20", "HEX20R", "HEX8R"]:
        conv[case] = []
        for n in [1, 2, 3, 4, 6]:
            if case in ("TET10", "HEX20", "HEX20R") and n > 4:
                continue
            r = solve(case, n)
            if r is None:
                continue
            ratio = -r["w"] / out["w_ref"]
            conv[case].append(dict(n=n, ndof=int(r["ndof"]), ratio=float(ratio)))
            print(case, n, r["ndof"], round(ratio, 4))
    out["convergence"] = conv
    vis = {}
    for case in ["TET4", "TET10", "HEX8", "HEX20"]:
        r = solve(case, 1)
        vis[case] = edges_polylines(r)
        vis[case]["ratio"] = float(-r["w"] / out["w_ref"])
    # Hourglassing: reduced-integration HEX8 with very weak control, 2 through thickness
    r = solve("HEX8R", 2, hourglass_eps=2e-3)
    if r is not None:
        vis["HEX8R"] = edges_polylines(r)
        vis["HEX8R"]["ratio"] = float(-r["w"] / out["w_ref"])
        print("HEX8R (weak hourglass ctrl) ratio", vis["HEX8R"]["ratio"])
    out["vis"] = vis
    with open("/home/user/Mesh/video/data/cantilever.json", "w") as fh:
        json.dump(out, fh)


if __name__ == "__main__":
    main()
