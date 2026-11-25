"""
Non-load-carrying transverse fillet-welded attachment (T-joint) - HCF assessment of a
welded detail with three methods: nominal stress, structural hot-spot stress and
effective notch stress.

Half model (symmetry at x = 0), plane strain, linear elastic, Q9 elements from gmsh.
Main plate t = 20 mm, attachment 10 mm thick x 40 mm high, fillet weld leg 8 mm,
weld toe rounded with the IIW reference radius r_ref = 1 mm (effective notch).
Nominal membrane stress range in the main plate: 100 MPa.
"""
import os, sys, subprocess, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
import meshio
from fem.mesh import Mesh, element_edges_on
from fem.solver import FEModel2D, run_history
from fem.material import J2Material, von_mises
from fem.runner import mandel3_to_tensor4
from fem.fatigue import dnv_sn_life

HERE = os.path.dirname(__file__)
RES = os.path.join(HERE, "..", "results")
WORK = os.path.join(RES, "weld_mesh")
os.makedirs(WORK, exist_ok=True)

t, L, ta, ha, w, r = 20.0, 150.0, 10.0, 40.0, 8.0, 1.0
x_toe = ta / 2 + w                      # 13 mm (sharp-toe position)
cx, cy = x_toe + r * (np.sqrt(2) - 1), t + r          # fillet centre
A = (cx, t)                                            # tangent point on plate surface
Bp = (cx - r / np.sqrt(2), cy - r / np.sqrt(2))       # tangent point on weld face

geo = f"""
SetFactory("Built-in");
lc = 3.0;
Point(1) = {{0, 0, 0, lc}};
Point(2) = {{{L}, 0, 0, lc}};
Point(3) = {{{L}, {t}, 0, lc}};
Point(4) = {{{A[0]}, {A[1]}, 0, lc}};
Point(5) = {{{cx}, {cy}, 0, lc}};
Point(6) = {{{Bp[0]}, {Bp[1]}, 0, lc}};
Point(7) = {{{ta/2}, {t + w}, 0, lc}};
Point(8) = {{{ta/2}, {t + ha}, 0, lc}};
Point(9) = {{0, {t + ha}, 0, lc}};
Line(1) = {{1, 2}};
Line(2) = {{2, 3}};
Line(3) = {{3, 4}};
Circle(4) = {{4, 5, 6}};
Line(5) = {{6, 7}};
Line(6) = {{7, 8}};
Line(7) = {{8, 9}};
Line(8) = {{9, 1}};
Curve Loop(1) = {{1, 2, 3, 4, 5, 6, 7, 8}};
Plane Surface(1) = {{1}};
Field[1] = Distance;
Field[1].CurvesList = {{4}};
Field[1].Sampling = 200;
Field[2] = Threshold;
Field[2].InField = 1;
Field[2].SizeMin = 0.05;
Field[2].SizeMax = 2.5;
Field[2].DistMin = 0.25;
Field[2].DistMax = 40;
Field[2].StopAtDistMax = 1;
Field[3] = Distance;
Field[3].CurvesList = {{3}};
Field[3].Sampling = 300;
Field[4] = Threshold;
Field[4].InField = 3;
Field[4].SizeMin = 0.8;
Field[4].SizeMax = 2.5;
Field[4].DistMin = 0.5;
Field[4].DistMax = 6;
Field[5] = Min;
Field[5].FieldsList = {{2, 4}};
Background Field = 5;
Mesh.MeshSizeExtendFromBoundary = 0;
Mesh.MeshSizeFromPoints = 0;
Mesh.MeshSizeFromCurvature = 0;
Mesh.Algorithm = 6;
Mesh.RecombineAll = 1;
Mesh.RecombinationAlgorithm = 3;
Mesh.ElementOrder = 2;
Mesh.SecondOrderIncomplete = 0;
Mesh.HighOrderOptimize = 0;
Physical Surface("weld") = {{1}};
"""
open(os.path.join(WORK, "tjoint.geo"), "w").write(geo)
subprocess.run(["gmsh", "-2", "tjoint.geo", "-format", "msh22", "-o", "tjoint.msh"], cwd=WORK,
               check=True, stdout=subprocess.DEVNULL)
msh = meshio.read(os.path.join(WORK, "tjoint.msh"))
pts = msh.points[:, :2]
quads = [c.data for c in msh.cells if c.type == "quad9"]
others = [c.type for c in msh.cells if c.type not in ("quad9", "line3", "vertex")]
assert quads and not others, f"unexpected cells {others}"
els = np.concatenate(quads)
# drop unused nodes
used = np.unique(els)
remap = -np.ones(pts.shape[0], int)
remap[used] = np.arange(used.size)
nodes = pts[used]
els = remap[els]
# orientation check (counter-clockwise)
def area_sign(e):
    P = nodes[e[:4]]
    return 0.5 * np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1])
flip = np.array([area_sign(e) < 0 for e in els])
els[flip] = els[flip][:, [0, 3, 2, 1, 7, 6, 5, 4, 8]]
mesh = Mesh(nodes, els)
X, Y = nodes.T
tol = 1e-6
mesh.sets = {"x0": np.nonzero(np.abs(X) < tol)[0], "xL": np.nonzero(np.abs(X - L) < tol)[0]}
print(f"weld mesh: {mesh.ne} Q9 elements, {mesh.nn} nodes")

mat = J2Material(E=210000.0, nu=0.3, sigma0=1e9)
S_nom = 100.0
corner = int(np.argmin(np.hypot(X, Y)))
support = int(np.argmin(np.hypot(X - L, Y)))
top_att = np.nonzero(np.abs(Y - (t + ha)) < tol)[0]


def solve_case(kind):
    m = FEModel2D(mesh, mat, "plane_strain", 1.0)
    m.fix(mesh.sets["x0"], 0)
    if kind == "membrane":
        m.fix([corner], 1)
        f = m.edge_load_vector(element_edges_on(mesh, mesh.sets["xL"]), (S_nom, 0.0))
    else:
        # 3-point bending: plate simply supported at x = L, attachment pulled up (hogging, toe in tension);
        # load scaled so that the nominal (beam) bending stress at the toe section = S_nom
        m.fix([support], 1)
        P_half = S_nom * t ** 2 / (6.0 * (L - x_toe))
        f = m.edge_load_vector(element_edges_on(mesh, top_att), (0.0, +P_half / (ta / 2)))
    u, st, _ = run_history(m, [{"fext": f}])
    sn = m.gauss_to_nodes(st["sig"])
    sxx, syy, sxy = sn[:, 0], sn[:, 1], sn[:, 2] / np.sqrt(2)
    s1 = 0.5 * (sxx + syy) + np.sqrt((0.5 * (sxx - syy)) ** 2 + sxy ** 2)
    vm = m.gauss_to_nodes(von_mises(mandel3_to_tensor4(st["sig"])))
    surf = np.nonzero((np.abs(Y - t) < 1e-6) & (X >= A[0] - 1e-9))[0]
    surf = surf[np.argsort(X[surf])]
    arc = np.nonzero(np.abs(np.hypot(X - cx, Y - cy) - r) < 1e-4)[0]
    k_notch = arc[np.argmax(s1[arc])]
    s_notch = s1[k_notch]
    d = X[surf] - x_toe
    sig_surf = sxx[surf]
    s05, s15 = np.interp(0.5 * t, d, sig_surf), np.interp(1.5 * t, d, sig_surf)
    s04, s10 = np.interp(0.4 * t, d, sig_surf), np.interp(1.0 * t, d, sig_surf)
    hs_dnv = 1.5 * s05 - 0.5 * s15
    hs_iiw = 1.67 * s04 - 0.67 * s10
    # through-thickness linearisation at the toe section (membrane + bending)
    sec = np.nonzero(np.abs(X - x_toe) < 0.6)[0]
    print(f"[{kind}] 0.5t={s05:.1f} 1.5t={s15:.1f} -> HS(DNV)={hs_dnv:.1f}; 0.4t={s04:.1f} 1.0t={s10:.1f} -> HS(IIW)={hs_iiw:.1f}; notch={s_notch:.1f} (Kw={s_notch/S_nom:.2f})")
    fat = lambda ds, F: 2e6 * (F / ds) ** 3
    lives = {"nominal_FAT80": fat(S_nom, 80.0), "hotspot_IIW_FAT100": fat(hs_iiw, 100.0),
             "hotspot_IIW_FAT90": fat(hs_iiw, 90.0), "hotspot_DNV_D": float(dnv_sn_life(hs_dnv)),
             "notch_FAT225": fat(s_notch, 225.0)}
    for k, v in lives.items():
        print(f"     life {k:20s}: {v:.3g}")
    return dict(sxx=sxx, syy=syy, sxy=sxy, s1=s1, vm=vm, ux=u[0::2], uy=u[1::2], surf_d=d, surf_sxx=sig_surf,
                arc_nodes=arc, k_notch=k_notch), dict(s05=s05, s15=s15, s04=s04, s10=s10, hs_dnv=hs_dnv,
                hs_iiw=hs_iiw, s_notch=s_notch, lives=lives)


out = dict(nodes=nodes, elems=els)
info = dict(t=t, L=L, ta=ta, ha=ha, w=w, r=r, x_toe=x_toe, S_nom=S_nom, cx=cx, cy=cy, ne=mesh.ne, nn=mesh.nn)
for kind in ["membrane", "bending"]:
    arr, inf = solve_case(kind)
    for k, v in arr.items():
        out[f"{kind}_{k}"] = v
    info[kind] = inf
out["meta"] = np.array(json.dumps(info))
np.savez_compressed(os.path.join(RES, "weld_tjoint.npz"), **out)
