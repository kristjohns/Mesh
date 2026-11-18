"""Cold-open image: linear-elastic von Mises at the transition fillet under 1.7 x design load (fictitious > yield)."""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.tri as mtri  # noqa: E402
import numpy as np  # noqa: E402

from epfem import Material, Model, gmsh_t6, von_mises  # noqa: E402
from plots import BG  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "build", "frames")
os.makedirs(OUT, exist_ok=True)
Ri, Ro1, Ro2, RHO, ZS, L = 116.55, 136.55, 170.0, 8.0, 600.0, 1020.0


def build(occ):
    P = lambda r, z: occ.addPoint(r, z, 0)
    p1, p2, p3 = P(Ri, 0), P(Ro1, 0), P(Ro1, ZS - RHO)
    pc, p4, p5, p6, p7 = P(Ro1 + RHO, ZS - RHO), P(Ro1 + RHO, ZS), P(Ro2, ZS), P(Ro2, L), P(Ri, L)
    cur = [occ.addLine(p1, p2), occ.addLine(p2, p3), occ.addCircleArc(p3, pc, p4), occ.addLine(p4, p5),
           occ.addLine(p5, p6), occ.addLine(p6, p7), occ.addLine(p7, p1)]
    occ.addPlaneSurface([occ.addCurveLoop(cur)])


X, T = gmsh_t6(build, f"Min(9, 0.35 + 0.2*Max(Sqrt((x-{Ro1 + RHO})^2+(y-{ZS - RHO})^2)-{RHO}, 0))")
m = Model(X, T, Material(210000.0, 0.3, 1e9), mode="axisym")
m.fix(m.nodes_where(lambda x, y: np.isclose(y, L)), 1)
unit = m.edge_load(m.edges_where(lambda x, y: np.isclose(y, 0)), traction=(0.0, -1.0))
m.loads.append(lambda s: s * 1.7 * 150.0 * unit)
m.solve(np.array([0.0, 1.0]), monitors=dict(a=lambda md, u, f: 0.0))
vm = m.nodal(von_mises(m.sig))
print("elastic peak at 1.7x:", vm.max())
tri = m.subtriangles()
Tz = mtri.Triangulation(m.X[:, 1], m.X[:, 0], tri)          # z horizontal, r vertical
win = (ZS - 34, ZS + 14, Ro1 - 13.5, Ro1 + 13.5)
fig = plt.figure(figsize=(8, 4.5), dpi=240, facecolor=BG)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_facecolor(BG)
vmax = 560.0
ax.tricontourf(Tz, np.clip(vm, 0, vmax * 0.9999), levels=np.linspace(0, vmax, 15), cmap="turbo")
ax.tricontour(Tz, vm, levels=[355.0], colors=["white"], linewidths=2.0, linestyles="--")
ax.set_xlim(win[0], win[1]); ax.set_ylim(win[2], win[3]); ax.set_aspect("equal"); ax.axis("off")
fig.savefig(os.path.join(OUT, "open_elastic.png"), facecolor=BG)
plt.close(fig)
np.save(os.path.join(OUT, "open_elastic_peak.npy"), np.array([vm.max()]))
