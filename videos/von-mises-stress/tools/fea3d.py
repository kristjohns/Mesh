"""3D linear-elastic FE analysis of a forged subsea tubular transition (pipe -> hub).

Geometry (mm): pipe OD 273.1 x 20 WT, hub OD 340, common ID 233.1, shoulder fillet R8.
Loads: axial force N, bending moment M (about y), torque T, applied as beam-theory
tractions on both end faces (self-equilibrated, 3-2-1 support => zero reactions).
Elements: quadratic tetrahedra (curved, isoparametric), S355: E = 210 GPa, nu = 0.3.

Outputs build/fea/fea3d.npz (+ assets/fea/summary.json numbers used in the video).
"""
import json
import os
import time

import gmsh
import numpy as np
import pyamg
import scipy.sparse as sp
from skfem import (Basis, BilinearForm, ElementTetP1, ElementTetP2, ElementVector, FacetBasis,
                   LinearForm, MeshTet2, asm, condense, solve)
from skfem.helpers import dot, sym_grad, trace, eye
from skfem.models.elasticity import lame_parameters, linear_elasticity

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "build", "fea")
os.makedirs(OUT, exist_ok=True)
os.makedirs(os.path.join(ROOT, "assets", "fea"), exist_ok=True)

# ---------------------------------------------------------------- parameters
Ri, Ro1, Ro2, RHO = 116.55, 136.55, 170.0, 8.0
L1, L2 = 600.0, 420.0
ZS, L = L1, L1 + L2
E, NU = 210000.0, 0.3
N_AX, M_B, T_Q = 1.0e6, 60.0e6, 80.0e6          # N, N*mm, N*mm  (1.0 MN, 60 kNm, 80 kNm)
HF, HMAX, GROW = float(os.environ.get("HF", 3.0)), 20.0, 0.33


def section(Ro):
    A = np.pi * (Ro ** 2 - Ri ** 2)
    I = np.pi / 4 * (Ro ** 4 - Ri ** 4)
    return A, I, 2 * I


A1, I1, J1 = section(Ro1)
A2, I2, J2 = section(Ro2)

t0 = time.time()
# ---------------------------------------------------------------- geometry + mesh
gmsh.initialize()
gmsh.option.setNumber("General.Terminal", 0)
gmsh.model.add("transition")
occ = gmsh.model.occ
P = lambda r, z: occ.addPoint(r, 0, z)
p1, p2, p3 = P(Ri, 0), P(Ro1, 0), P(Ro1, ZS - RHO)
pc, p4, p5 = P(Ro1 + RHO, ZS - RHO), P(Ro1 + RHO, ZS), P(Ro2, ZS)
p6, p7 = P(Ro2, L), P(Ri, L)
curves = [occ.addLine(p1, p2), occ.addLine(p2, p3), occ.addCircleArc(p3, pc, p4),
          occ.addLine(p4, p5), occ.addLine(p5, p6), occ.addLine(p6, p7), occ.addLine(p7, p1)]
surf = occ.addPlaneSurface([occ.addCurveLoop(curves)])
# revolve in four quarters and fuse -> avoids a degenerate seam
parts = []
for k in range(4):
    s = occ.copy([(2, surf)])
    occ.rotate(s, 0, 0, 0, 0, 0, 1, k * np.pi / 2)
    out = occ.revolve(s, 0, 0, 0, 0, 0, 1, np.pi / 2)
    parts += [d for d in out if d[0] == 3]
occ.remove([(2, surf)], recursive=True)
occ.fragment(parts[:1], parts[1:])
occ.synchronize()

expr = (f"Min({HMAX}, {HF} + {GROW}*Max(Sqrt((Sqrt(x*x+y*y)-{Ro1 + RHO})^2+(z-{ZS - RHO})^2)-{RHO}, 0))")
f = gmsh.model.mesh.field.add("MathEval")
gmsh.model.mesh.field.setString(f, "F", expr)
gmsh.model.mesh.field.setAsBackgroundMesh(f)
for opt in ("Mesh.MeshSizeExtendFromBoundary", "Mesh.MeshSizeFromPoints", "Mesh.MeshSizeFromCurvature"):
    gmsh.option.setNumber(opt, 0)
gmsh.option.setNumber("Mesh.Algorithm3D", 10)   # HXT
gmsh.option.setNumber("Mesh.ElementOrder", 2)
gmsh.option.setNumber("Mesh.HighOrderOptimize", 1)
gmsh.model.mesh.generate(3)
gmsh.model.mesh.removeDuplicateNodes()

# extract quadratic tets (gmsh type 11: 10-node tet)
tags, coords, _ = gmsh.model.mesh.getNodes()
xyz = coords.reshape(-1, 3)
idx = {t: i for i, t in enumerate(tags)}
etypes, etags, enodes = gmsh.model.mesh.getElements(3)
k11 = list(etypes).index(11)
conn = np.vectorize(idx.get)(enodes[k11].reshape(-1, 10))
gmsh.finalize()
print(f"mesh: {conn.shape[0]} tets, {xyz.shape[0]} nodes  ({time.time() - t0:.0f}s)", flush=True)

# gmsh tet10 node order: v0 v1 v2 v3 e01 e12 e02 e03 e23 e13
verts = np.unique(conn[:, :4])
vmap = -np.ones(xyz.shape[0], dtype=np.int64)
vmap[verts] = np.arange(len(verts))
p = xyz[verts].T.copy()
t = vmap[conn[:, :4]].T.copy()
# build curved mesh: straight MeshTet2 first, then move edge nodes onto gmsh's curved positions
from skfem import MeshTet  # noqa: E402
m = MeshTet2.from_mesh(MeshTet(p, t))
t = m.t
edge_mid = {}
pairs = [(0, 1, 4), (1, 2, 5), (0, 2, 6), (0, 3, 7), (2, 3, 8), (1, 3, 9)]
for i, j, kk in pairs:
    vi, vj = vmap[conn[:, i]], vmap[conn[:, j]]
    key = np.minimum(vi, vj) * len(verts) + np.maximum(vi, vj)
    for kk_, pos in zip(key, xyz[conn[:, kk]]):
        edge_mid[kk_] = pos
e = m.edges
ekey = np.minimum(e[0], e[1]) * len(verts) + np.maximum(e[0], e[1])
dl = m.doflocs.copy()
nv = p.shape[1]
for n, kk_ in enumerate(ekey):
    dl[:, nv + n] = edge_mid[kk_]
m = MeshTet2(dl, t)
print(f"skfem mesh ready: {m.nelements} elements, {m.nvertices} vertices ({time.time() - t0:.0f}s)", flush=True)

# ---------------------------------------------------------------- FE system
lam, mu = lame_parameters(E, NU)
ev = ElementVector(ElementTetP2())
ib = Basis(m, ev, intorder=4)
K = asm(linear_elasticity(lam, mu), ib)
print(f"K assembled: {K.shape[0]} dofs, nnz {K.nnz/1e6:.1f}M ({time.time() - t0:.0f}s)", flush=True)

end0 = m.facets_satisfying(lambda x: np.abs(x[2]) < 1e-6)
endL = m.facets_satisfying(lambda x: np.abs(x[2] - L) < 1e-6)
fb0, fbL = FacetBasis(m, ev, facets=end0, intorder=4), FacetBasis(m, ev, facets=endL, intorder=4)


@LinearForm
def trac_L(v, w):
    x, y, _ = w.x
    return (T_Q / J2) * (-y) * v[0] + (T_Q / J2) * x * v[1] + (N_AX / A2 + M_B * x / I2) * v[2]


@LinearForm
def trac_0(v, w):
    x, y, _ = w.x
    return (T_Q / J1) * y * v[0] - (T_Q / J1) * x * v[1] - (N_AX / A1 + M_B * x / I1) * v[2]


fvec = asm(trac_L, fbL) + asm(trac_0, fb0)

# dof bookkeeping
comp = np.zeros(ib.N, dtype=int)
for c_ in range(3):
    comp[ib.nodal_dofs[c_]] = c_
    comp[ib.edge_dofs[c_]] = c_
X = ib.doflocs


def resultants(fv):
    F = np.array([fv[comp == c_].sum() for c_ in range(3)])
    fx, fy, fz = (np.where(comp == c_, fv, 0.0) for c_ in range(3))
    Mx = np.sum(X[1] * fz - X[2] * fy)
    My = np.sum(X[2] * fx - X[0] * fz)
    Mz = np.sum(X[0] * fy - X[1] * fx)
    return np.r_[F, Mx, My, Mz]


# rigid-body shaped correction on the hub-end face so the load is exactly self-equilibrated
Ldofs = ib.get_dofs(endL).all()
R0 = resultants(fvec)
cols = []
for kk in range(6):
    g = np.zeros(6); g[kk] = 1.0
    a_, b_ = g[:3], g[3:]
    df = np.zeros(ib.N)
    for c_ in range(3):
        sel = Ldofs[comp[Ldofs] == c_]
        xs = X[:, sel]
        rot = np.cross(b_[:, None], xs, axis=0)
        df[sel] = a_[c_] + rot[c_]
    cols.append(df)
Gm = np.array([resultants(cc) for cc in cols]).T
coef = np.linalg.solve(Gm, -R0)
fvec = fvec + sum(ci * cc for ci, cc in zip(coef, cols))
print("load resultants before/after correction:", np.round(R0, 3), np.round(resultants(fvec), 6), flush=True)

# 3-2-1 support on three hub-end vertices
PV = m.p[:, :m.nvertices]
vL = np.where(np.abs(PV[2] - L) < 1e-6)[0]
pick = lambda target: vL[np.argmin(np.sum((PV[:2, vL] - np.array(target)[:, None]) ** 2, axis=0))]
vA, vB, vC = pick([Ro2, 0]), pick([-Ro2, 0]), pick([0, Ro2])
D = np.r_[ib.nodal_dofs[:, vA], ib.nodal_dofs[1:, vB], ib.nodal_dofs[2:, vC]]
I_free = np.setdiff1d(np.arange(ib.N), D)
Kf = K[I_free][:, I_free].tocsr()
ff = fvec[I_free]
Xf = X[:, I_free]; cf = comp[I_free]
B = np.zeros((len(I_free), 6))
for c_ in range(3):
    B[cf == c_, c_] = 1.0
# rotations
B[cf == 1, 3] = -Xf[2, cf == 1]; B[cf == 2, 3] = Xf[1, cf == 2]
B[cf == 0, 4] = Xf[2, cf == 0]; B[cf == 2, 4] = -Xf[0, cf == 2]
B[cf == 0, 5] = -Xf[1, cf == 0]; B[cf == 1, 5] = Xf[0, cf == 1]
ml = pyamg.smoothed_aggregation_solver(Kf, B=B, max_coarse=2000)
res = []
uf = ml.solve(ff, tol=1e-10, accel="cg", maxiter=400, residuals=res)
print(f"AMG-CG: {len(res)} its, rel.res {res[-1]/res[0]:.2e} ({time.time() - t0:.0f}s)", flush=True)
u = np.zeros(ib.N); u[I_free] = uf

# ---------------------------------------------------------------- stresses at integration points
uh = ib.interpolate(u)
eps = sym_grad(uh)
sig = 2 * mu * eps + eye(lam * trace(eps), 3)          # (3,3,ne,nq) at Gauss points
sxx, syy, szz = sig[0, 0], sig[1, 1], sig[2, 2]
sxy, syz, szx = sig[0, 1], sig[1, 2], sig[2, 0]
vm_q = np.sqrt(0.5 * ((sxx - syy) ** 2 + (syy - szz) ** 2 + (szz - sxx) ** 2) + 3 * (sxy ** 2 + syz ** 2 + szx ** 2))
qx = ib.global_coordinates().value                      # (3,ne,nq)
iq = np.unravel_index(np.argmax(vm_q), vm_q.shape)
print(f"max von Mises at Gauss points: {vm_q.max():.1f} MPa at {qx[:, iq[0], iq[1]].round(1)}", flush=True)

# ---------------------------------------------------------------- nodal (averaged) fields by L2 projection
ib1 = Basis(m, ElementTetP1(), quadrature=ib.quadrature)
Mm = asm(BilinearForm(lambda uu, vv, w: uu * vv), ib1).tocsr()
dinv = 1.0 / Mm.diagonal()


def project(qvals):
    b = asm(LinearForm(lambda vv, w: w["q"] * vv), ib1, q=qvals)
    x, info = sp.linalg.cg(Mm, b, rtol=1e-10, maxiter=500, M=sp.diags(dinv))
    return x


comps = {k: project(v) for k, v in
         dict(sxx=sxx, syy=syy, szz=szz, sxy=sxy, syz=syz, szx=szx).items()}
vm_avg_components = np.sqrt(0.5 * ((comps["sxx"] - comps["syy"]) ** 2 + (comps["syy"] - comps["szz"]) ** 2 +
                                   (comps["szz"] - comps["sxx"]) ** 2) +
                            3 * (comps["sxy"] ** 2 + comps["syz"] ** 2 + comps["szx"] ** 2))
vm_avg_invariant = project(vm_q)
print(f"nodal max vM: averaged components {vm_avg_components.max():.1f}, averaged vM {vm_avg_invariant.max():.1f}"
      f" ({time.time() - t0:.0f}s)", flush=True)

# cylindrical components at vertices
xv, yv, zv = PV
th = np.arctan2(yv, xv); c, s = np.cos(th), np.sin(th)
Sx, Sy, Sz, Txy, Tyz, Tzx = (comps[k] for k in ("sxx", "syy", "szz", "sxy", "syz", "szx"))
s_rr = c * c * Sx + s * s * Sy + 2 * s * c * Txy
s_tt = s * s * Sx + c * c * Sy - 2 * s * c * Txy
s_rt = -s * c * Sx + s * c * Sy + (c * c - s * s) * Txy
s_tz = -s * Tzx + c * Tyz
s_rz = c * Tzx + s * Tyz

# nominal (beam theory) von Mises at the outer fibre of the pipe, tension side
sig_nom = N_AX / A1 + M_B * Ro1 / I1
tau_nom = T_Q * Ro1 / J1
vm_nom = float(np.sqrt(sig_nom ** 2 + 3 * tau_nom ** 2))
# FE value on pipe OD (tension side, x>0, y~0) far from the step (z = 250 mm)
far = np.argmin((xv - Ro1) ** 2 + yv ** 2 + (zv - 250.0) ** 2)
vm_far = float(vm_avg_components[far])
# peak location (nodal)
ipk = int(np.argmax(vm_avg_components))

bf = m.boundary_facets()
tri = m.facets[:, bf]
np.savez_compressed(os.path.join(OUT, "fea3d.npz"), p=PV, t=m.t, tri=tri, vm=vm_avg_components,
                    vm_inv=vm_avg_invariant, srr=s_rr, stt=s_tt, szz=Sz, srt=s_rt, stz=s_tz, srz=s_rz,
                    sxx=Sx, syy=Sy, sxy=Txy, syz=Tyz, szx=Tzx, u=u[ib.nodal_dofs],
                    peak_xyz=PV[:, ipk])
summ = dict(
    geometry=dict(Ri=Ri, Ro1=Ro1, Ro2=Ro2, fillet=RHO, L1=L1, L2=L2),
    loads=dict(N_MN=N_AX / 1e6, M_kNm=M_B / 1e6, T_kNm=T_Q / 1e6),
    mesh=dict(tets=int(m.nelements), vertices=int(m.nvertices), dofs=int(ib.N), h_fillet=HF),
    nominal=dict(sigma=round(sig_nom, 1), tau=round(tau_nom, 1), vm=round(vm_nom, 1)),
    vm_pipe_far_FE=round(vm_far, 1),
    vm_peak_nodal=round(float(vm_avg_components.max()), 1),
    vm_peak_nodal_avg_invariant=round(float(vm_avg_invariant.max()), 1),
    vm_peak_gauss=round(float(vm_q.max()), 1),
    peak_xyz=[round(float(v), 2) for v in PV[:, ipk]],
    Kt_vm=round(float(vm_avg_components.max()) / vm_nom, 3),
)
summ["narr_pipe_vm"] = int(5 * round(vm_far / 5))
summ["narr_peak_vm"] = int(5 * round(float(vm_avg_components.max()) / 5))
json.dump(summ, open(os.path.join(ROOT, "assets", "fea", "summary.json"), "w"), indent=1)
print(json.dumps(summ, indent=1))
print(f"done ({time.time() - t0:.0f}s)")
