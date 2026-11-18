"""Axisymmetric (r-z) FE study of the same pipe-to-hub transition under axial tension.

* mesh-refinement series for (a) the R8 shoulder fillet and (b) a perfectly sharp corner
* stress-classification-line (SCL) linearization through the wall at the fillet hot spot
* principal-stress trajectories ("load flow lines") around the shoulder
* contour / mesh images for the video

Quadratic 6-node triangles (curved), linear elastic, E = 210 GPa, nu = 0.3.
Outputs: build/fea/axi.json, build/fea/axi_*.png
"""
import json
import os
import time

import gmsh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.tri as mtri  # noqa: E402
import numpy as np  # noqa: E402
from scipy.interpolate import RegularGridInterpolator  # noqa: E402
from skfem import (Basis, BilinearForm, ElementTriP2, ElementVector, FacetBasis, LinearForm,  # noqa: E402
                   MeshTri, MeshTri2, asm, condense, solve)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "build", "fea")
os.makedirs(OUT, exist_ok=True)

Ri, Ro1, Ro2, RHO = 116.55, 136.55, 170.0, 8.0
ZS, L = 600.0, 1020.0
E, NU = 210000.0, 0.3
LAM = E * NU / ((1 + NU) * (1 - 2 * NU))
MU = E / (2 * (1 + NU))
SIG_NOM = 100.0                       # MPa axial in the pipe wall
BG = "#0B0F19"


def build_mesh(sharp, hc, hmax=8.0, grow=0.22):
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.add("axi")
    occ = gmsh.model.occ
    P = lambda r, z: occ.addPoint(r, z, 0)
    if sharp:
        pts = [P(Ri, 0), P(Ro1, 0), P(Ro1, ZS), P(Ro2, ZS), P(Ro2, L), P(Ri, L)]
        cur = [occ.addLine(pts[i], pts[(i + 1) % 6]) for i in range(6)]
        expr = f"Min({hmax}, {hc} + {grow}*Sqrt((x-{Ro1})^2+(y-{ZS})^2))"
    else:
        p1, p2, p3 = P(Ri, 0), P(Ro1, 0), P(Ro1, ZS - RHO)
        pc, p4, p5, p6, p7 = P(Ro1 + RHO, ZS - RHO), P(Ro1 + RHO, ZS), P(Ro2, ZS), P(Ro2, L), P(Ri, L)
        cur = [occ.addLine(p1, p2), occ.addLine(p2, p3), occ.addCircleArc(p3, pc, p4), occ.addLine(p4, p5),
               occ.addLine(p5, p6), occ.addLine(p6, p7), occ.addLine(p7, p1)]
        expr = (f"Min({hmax}, {hc} + {grow}*Max(Sqrt((x-{Ro1 + RHO})^2+(y-{ZS - RHO})^2)-{RHO}, 0))")
    occ.addPlaneSurface([occ.addCurveLoop(cur)])
    occ.synchronize()
    f = gmsh.model.mesh.field.add("MathEval")
    gmsh.model.mesh.field.setString(f, "F", expr)
    gmsh.model.mesh.field.setAsBackgroundMesh(f)
    for opt in ("Mesh.MeshSizeExtendFromBoundary", "Mesh.MeshSizeFromPoints", "Mesh.MeshSizeFromCurvature"):
        gmsh.option.setNumber(opt, 0)
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    gmsh.option.setNumber("Mesh.ElementOrder", 2)
    gmsh.model.mesh.generate(2)
    tags, coords, _ = gmsh.model.mesh.getNodes()
    xyz = coords.reshape(-1, 3)[:, :2]
    idx = {t: i for i, t in enumerate(tags)}
    et, _, en = gmsh.model.mesh.getElements(2)
    conn = np.vectorize(idx.get)(en[list(et).index(9)].reshape(-1, 6))   # 6-node triangles
    gmsh.finalize()
    verts = np.unique(conn[:, :3])
    vmap = -np.ones(len(xyz), dtype=np.int64); vmap[verts] = np.arange(len(verts))
    m = MeshTri2.from_mesh(MeshTri(xyz[verts].T.copy(), vmap[conn[:, :3]].T.copy()))
    # curved edge nodes from gmsh (order: v0 v1 v2 e01 e12 e20)
    nv = len(verts)
    key = lambda a, b: np.minimum(a, b) * nv + np.maximum(a, b)
    mid = {}
    for i, j, k in [(0, 1, 3), (1, 2, 4), (2, 0, 5)]:
        for kk, pos in zip(key(vmap[conn[:, i]], vmap[conn[:, j]]), xyz[conn[:, k]]):
            mid[kk] = pos
    dl = m.doflocs.copy()
    for n, kk in enumerate(key(m.facets[0], m.facets[1])):
        dl[:, nv + n] = mid[kk]
    return MeshTri2(dl, m.t)


def strains(u, r):
    return u.grad[0, 0], u.grad[1, 1], u.value[0] / r, 0.5 * (u.grad[0, 1] + u.grad[1, 0])


@BilinearForm
def axi_stiffness(u, v, w):
    r = w.x[0]
    a = strains(u, r); b = strains(v, r)
    tra, trb = a[0] + a[1] + a[2], b[0] + b[1] + b[2]
    return (LAM * tra * trb + 2 * MU * (a[0] * b[0] + a[1] * b[1] + a[2] * b[2] + 2 * a[3] * b[3])) * r


@LinearForm
def pull(v, w):
    return -SIG_NOM * v[1] * w.x[0]          # traction t_z = -sigma_nom on the pipe end z = 0


def solve_case(sharp, hc):
    m = build_mesh(sharp, hc)
    ev = ElementVector(ElementTriP2())
    ib = Basis(m, ev, intorder=4)
    K = asm(axi_stiffness, ib)
    end0 = m.facets_satisfying(lambda x: np.abs(x[1]) < 1e-6)
    f = asm(pull, FacetBasis(m, ev, facets=end0, intorder=4))
    endL = m.facets_satisfying(lambda x: np.abs(x[1] - L) < 1e-6)
    D = ib.get_dofs(endL).all("u^2")
    u = solve(*condense(K, f, D=D))
    uh = ib.interpolate(u)
    r = ib.global_coordinates().value[0]
    err, ezz, ett, erz = strains(uh, r)
    tr = err + ezz + ett
    S = dict(rr=LAM * tr + 2 * MU * err, zz=LAM * tr + 2 * MU * ezz, tt=LAM * tr + 2 * MU * ett, rz=2 * MU * erz)
    vmq = np.sqrt(0.5 * ((S["rr"] - S["zz"]) ** 2 + (S["zz"] - S["tt"]) ** 2 + (S["tt"] - S["rr"]) ** 2) + 3 * S["rz"] ** 2)
    # nodal (P2) L2 projection of components
    sb = Basis(m, ElementTriP2(), intorder=4)
    Mm = asm(BilinearForm(lambda a, b, w: a * b), sb)
    from scipy.sparse.linalg import splu
    lu = splu(Mm.tocsc())
    nod = {k: lu.solve(asm(LinearForm(lambda v, w: w["q"] * v), sb, q=v_)) for k, v_ in S.items()}
    vmn = np.sqrt(0.5 * ((nod["rr"] - nod["zz"]) ** 2 + (nod["zz"] - nod["tt"]) ** 2 + (nod["tt"] - nod["rr"]) ** 2)
                  + 3 * nod["rz"] ** 2)
    return dict(m=m, ib=ib, sb=sb, u=u, vmq=vmq, nod=nod, vmn=vmn, nel=m.nelements)


t0 = time.time()
levels = [4.0, 2.0, 1.0, 0.5, 0.25, 0.125, 0.0625, 0.03125]
series = {"fillet": [], "sharp": []}
keep = {}
for name, sharp in (("fillet", False), ("sharp", True)):
    for hc in levels:
        R = solve_case(sharp, hc)
        rec = dict(h=hc, nel=int(R["nel"]), kt_nodal=float(R["vmn"].max() / SIG_NOM),
                   kt_gauss=float(R["vmq"].max() / SIG_NOM))
        series[name].append(rec)
        print(name, rec, f"({time.time() - t0:.0f}s)", flush=True)
        if hc in (2.0, 0.5, 0.125, 0.03125):
            keep[(name, hc)] = R

# ------------------------------------------------------------------ SCL linearization (finest fillet)
R = keep[("fillet", levels[-1])]
m, sb = R["m"], R["sb"]
nv = m.nvertices
P = m.p[:, :nv]
onfil = np.where((np.abs(np.hypot(P[0] - (Ro1 + RHO), P[1] - (ZS - RHO)) - RHO) < 1e-3))[0]
hs = onfil[np.argmax(R["vmn"][sb.nodal_dofs[0][onfil]])]
hx, hz = P[:, hs]
npts = 81
xs = np.linspace(hx, Ri, npts); zs_ = np.full(npts, hz)
xs[0] -= 0.03; xs[-1] += 0.03


def probes(R, pts):
    """Interpolation matrix for P2 nodal fields at points (on the straight-sided twin mesh)."""
    m2 = R["m"]
    ml = MeshTri(m2.p[:, :m2.nvertices].copy(), m2.t.copy())
    return Basis(ml, ElementTriP2()).probes(pts)


Pm = probes(R, np.vstack([xs, zs_]))
prof = {k: Pm @ v for k, v in R["nod"].items()}
tthk = hx - Ri
s = np.linspace(0, tthk, npts)                     # 0 at the fillet surface, t at the bore


def linearize(sig):
    mem = np.trapezoid(sig, s) / tthk
    ben = 6.0 / tthk ** 2 * np.trapezoid(sig * (tthk / 2 - s), s)     # + at s = 0
    lin = mem + ben * (1 - 2 * s / tthk)
    return float(mem), float(ben), lin


lin = {k: linearize(v) for k, v in prof.items()}


def vm_of(c):
    rr, zz, tt, rz = c
    return float(np.sqrt(0.5 * ((rr - zz) ** 2 + (zz - tt) ** 2 + (tt - rr) ** 2) + 3 * rz ** 2))


PL = vm_of([lin[k][0] for k in ("rr", "zz", "tt", "rz")])
PLPb = vm_of([lin[k][0] + lin[k][1] for k in ("rr", "zz", "tt", "rz")])
total_surface = vm_of([prof[k][0] for k in ("rr", "zz", "tt", "rz")])
scl = dict(hot_spot=[float(hx), float(hz)], thickness=float(tthk), s=s.tolist(),
           szz=prof["zz"].tolist(), szz_mem=lin["zz"][0], szz_ben=lin["zz"][1], szz_lin=lin["zz"][2].tolist(),
           vm_PL=PL, vm_PL_Pb=PLPb, vm_total_surface=total_surface)
print("SCL:", {k: v for k, v in scl.items() if not isinstance(v, list)}, flush=True)

# ------------------------------------------------------------------ principal stress trajectories
R = keep[("fillet", levels[-1])]
m = R["m"]; nv = m.nvertices
tri_rz = mtri.Triangulation(m.p[0, :nv], m.p[1, :nv], m.t.T)
nd = R["sb"].nodal_dofs[0]
itp = {k: mtri.LinearTriInterpolator(tri_rz, R["nod"][k][nd]) for k in ("rr", "zz", "rz")}


def direction(r, z, prev):
    a, b, c = (float(itp[k](r, z)) if not np.ma.is_masked(itp[k](r, z)) else np.nan for k in ("rr", "zz", "rz"))
    if np.isnan(a + b + c):
        return None
    th = 0.5 * np.arctan2(2 * c, a - b)               # angle of sigma_1 from the r axis
    d = np.array([np.cos(th), np.sin(th)])
    if prev is not None and d @ prev < 0:
        d = -d
    return d


lines = []
for r0 in np.linspace(Ri + 1.0, Ro1 - 0.6, 10):
    x = np.array([r0, 380.0]); d = np.array([0.0, 1.0]); path = [x.copy()]
    for _ in range(4000):
        d1 = direction(*x, d)
        if d1 is None:
            break
        d2 = direction(*(x + 0.2 * d1), d1)
        if d2 is None:
            break
        x = x + 0.4 * d2; d = d2; path.append(x.copy())
        if x[1] > 820:
            break
    lines.append(np.array(path)[::3][:, ::-1].tolist())      # stored as (z, r)
print("trajectories:", [len(l) for l in lines], flush=True)


# ------------------------------------------------------------------ images (axis horizontal: z -> right, r -> up)
def draw(R, fname, win, vmax, show_mesh=True, levels_=14, dpi=200, size=(8, 8)):
    m = R["m"]; nv = m.nvertices
    P = m.p[:, :nv]
    tri = mtri.Triangulation(P[1], P[0], m.t.T)
    vm = R["vmn"][R["sb"].nodal_dofs[0]] / SIG_NOM
    fig = plt.figure(figsize=size, dpi=dpi, facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_facecolor(BG)
    lv = np.linspace(0, vmax, levels_ + 1)
    ax.tricontourf(tri, np.clip(vm, 0, vmax * 0.9999), levels=lv, cmap="turbo")
    if show_mesh:
        ax.triplot(tri, color="#0B0F19", lw=0.35, alpha=0.8)
    ax.set_xlim(win[0], win[1]); ax.set_ylim(win[2], win[3]); ax.set_aspect("equal"); ax.axis("off")
    fig.savefig(os.path.join(OUT, fname), facecolor=BG); plt.close(fig)


WIN = (ZS - 14.0, ZS + 10.0, Ro1 - 12.0, Ro1 + 12.0)            # 24 mm window around the shoulder corner
for (name, hc), R in keep.items():
    draw(R, f"axi_{name}_h{hc:g}.png", WIN, vmax=3.0)
draw(keep[("sharp", levels[-1])], "axi_sharp_zoom_tiny.png", (ZS - 0.6, ZS + 0.4, Ro1 - 0.5, Ro1 + 0.5), vmax=3.0)
FLOW_WIN = (490.0, 710.0, Ri - 40.05, Ri - 40.05 + 220.0 * 9 / 16)     # exactly 16:9 so the image maps linearly
draw(keep[("fillet", levels[-1])], "axi_flow_bg.png", FLOW_WIN, vmax=3.0, show_mesh=False, size=(16, 9), dpi=160)

json.dump(dict(sig_nom=SIG_NOM, levels=levels, series=series, scl=scl, trajectories=lines, flow_win=FLOW_WIN,
               geometry=dict(Ri=Ri, Ro1=Ro1, Ro2=Ro2, rho=RHO, zs=ZS, L=L)),
          open(os.path.join(OUT, "axi.json"), "w"))
print(f"done ({time.time() - t0:.0f}s)")
