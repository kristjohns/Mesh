"""Mesh convergence at a shoulder: fillet (converges) vs sharp corner (singular).

Plane stress, stepped flat bar in tension, half model with symmetry at y=0.
Quadratic triangles (TRI6). Element size at the corner is refined systematically.
"""
import json
import numpy as np
import gmsh
from scipy.sparse.linalg import spsolve
from skfem import (MeshTri, ElementVector, ElementTriP2, ElementTriP1, Basis, FacetBasis,
                   asm, condense, LinearForm)
from skfem.helpers import sym_grad
from skfem.models.elasticity import linear_elasticity, lame_parameters

HW, HN, LW, LN = 0.75, 0.5, 2.0, 2.0  # half widths, lengths (wide / narrow)
E, NU = 1.0, 0.3


def build_mesh(r, hc, hg=0.12):
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.add("bar")
    geo = gmsh.model.geo
    pA = geo.addPoint(-LW, 0, 0)
    pB = geo.addPoint(LN, 0, 0)
    pC = geo.addPoint(LN, HN, 0)
    pF = geo.addPoint(0, HW, 0)
    pG = geo.addPoint(-LW, HW, 0)
    lines = [geo.addLine(pA, pB), geo.addLine(pB, pC)]
    if r > 0:
        pD = geo.addPoint(r, HN, 0)
        pc = geo.addPoint(r, HN + r, 0)
        pE = geo.addPoint(0, HN + r, 0)
        lines.append(geo.addLine(pC, pD))
        arc = geo.addCircleArc(pD, pc, pE)
        lines.append(arc)
        lines.append(geo.addLine(pE, pF))
        hot_curves, hot_points = [arc], []
    else:
        pK = geo.addPoint(0, HN, 0)
        lines.append(geo.addLine(pC, pK))
        lines.append(geo.addLine(pK, pF))
        hot_curves, hot_points = [], [pK]
    lines.append(geo.addLine(pF, pG))
    lines.append(geo.addLine(pG, pA))
    cl = geo.addCurveLoop(lines)
    geo.addPlaneSurface([cl])
    geo.synchronize()
    f = gmsh.model.mesh.field
    d = f.add("Distance")
    if hot_curves:
        f.setNumbers(d, "CurvesList", hot_curves)
        f.setNumber(d, "Sampling", 400)
    else:
        f.setNumbers(d, "PointsList", hot_points)
    t = f.add("Threshold")
    f.setNumber(t, "InField", d)
    f.setNumber(t, "SizeMin", hc)
    f.setNumber(t, "SizeMax", hg)
    f.setNumber(t, "DistMin", max(0.5 * r, 2 * hc) if r > 0 else 2 * hc)
    # grow smoothly (~25 % per element) away from the hot spot
    f.setNumber(t, "DistMax", max(0.5 * r, 2 * hc) + 6 * hg)
    f.setAsBackgroundMesh(t)
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    gmsh.model.mesh.generate(2)
    nodeTags, coords, _ = gmsh.model.mesh.getNodes()
    xyz = coords.reshape(-1, 3)[:, :2]
    tag2idx = {t: i for i, t in enumerate(nodeTags)}
    etypes, etags, enodes = gmsh.model.mesh.getElements(2)
    tri = np.array([tag2idx[t] for t in enodes[0]]).reshape(-1, 3)
    gmsh.finalize()
    # drop unused nodes (geometry points not in mesh)
    used = np.unique(tri)
    remap = -np.ones(len(xyz), int)
    remap[used] = np.arange(len(used))
    return MeshTri(xyz[used].T, remap[tri].T)


def solve(m):
    e = ElementVector(ElementTriP2())
    ib = Basis(m, e, intorder=4)
    lam, mu = lame_parameters(E, NU)
    lam_ps = 2 * lam * mu / (lam + 2 * mu)
    K = asm(linear_elasticity(lam_ps, mu), ib)
    fb = FacetBasis(m, e, facets=m.facets_satisfying(lambda x: np.isclose(x[0], LN)))

    @LinearForm
    def trac(v, w):
        return 1.0 * v.value[0]

    f = asm(trac, fb)
    Dx = ib.get_dofs(lambda x: np.isclose(x[0], -LW)).nodal["u^1"]
    Dy = ib.get_dofs(lambda x: np.isclose(x[1], 0.0)).nodal["u^2"]
    Dy_e = ib.get_dofs(lambda x: np.isclose(x[1], 0.0)).facet.get("u^2", np.array([], int))
    Dx_e = ib.get_dofs(lambda x: np.isclose(x[0], -LW)).facet.get("u^1", np.array([], int))
    D = np.unique(np.concatenate([Dx, Dy, Dy_e, Dx_e]))
    Kc, fc, xc, I = condense(K, f, D=D)
    u = np.zeros(K.shape[0])
    u[I] = spsolve(Kc.tocsc(), fc)
    # stresses at quadrature points
    w = ib.interpolate(u)
    eps = sym_grad(w)
    tr = eps[0, 0] + eps[1, 1]
    sxx = 2 * mu * eps[0, 0] + lam_ps * tr
    syy = 2 * mu * eps[1, 1] + lam_ps * tr
    sxy = 2 * mu * eps[0, 1]
    s1 = 0.5 * (sxx + syy) + np.sqrt((0.5 * (sxx - syy)) ** 2 + sxy ** 2)
    # averaged nodal stress (L2 projection onto P1), and unaveraged element-corner extrapolation
    sb = Basis(m, ElementTriP1(), intorder=4)
    s1_nodal = sb.project(s1)
    return u, ib, s1_nodal, s1


def main():
    nom = 1.0
    out = {"HW": HW, "HN": HN, "LW": LW, "LN": LN, "series": {}, "meshes": {}}
    r = 0.1
    hcs = [0.1, 0.05, 0.025, 0.0125, 0.00625, 0.003125, 0.0015625]
    for label, rr in [("fillet", r), ("sharp", 0.0)]:
        series = []
        for hc in hcs:
            m = build_mesh(rr, hc)
            u, ib, s1n, s1q = solve(m)
            # peak in the corner region
            near = (np.abs(m.p[0]) < 0.4) & (m.p[1] > 0.3)
            peak = float(s1n[near].max())
            peakq = float(s1q.max())
            series.append(dict(hc=hc, nel=int(m.t.shape[1]), peak=peak / nom, peak_qp=peakq / nom))
            print(label, hc, m.t.shape[1], round(peak, 4), round(peakq, 4))
            if True:
                out["meshes"][f"{label}_{hc}"] = dict(
                    p=np.round(m.p.T, 5).tolist(), t=m.t.T.tolist(),
                    s1=np.round(s1n, 4).tolist(), hc=hc)
        out["series"][label] = series
    with open("/home/user/Mesh/video/data/notch.json", "w") as fh:
        json.dump(out, fh)


if __name__ == "__main__":
    main()
