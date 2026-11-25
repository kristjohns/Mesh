"""
Cross-check of the in-house cyclic-plasticity solver against CalculiX (ccx).

Plate with a central hole, plane stress, elastic-perfectly-plastic (sy = 355 MPa),
remote gross stress cycled 0 -> +220 -> -220 -> +220 MPa.
The same mesh is used (Q9 -> 8-node CPS8 for CalculiX, centre node dropped).
Compared: notch-root stress/strain history and the top-edge displacement.
"""
import os, sys, subprocess, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
from fem.mesh import plate_with_hole, element_edges_on
from fem.solver import FEModel2D, run_history
from fem.materials_lib import s355_epp

OUT = os.path.join(os.path.dirname(__file__), "ccx_run")
os.makedirs(OUT, exist_ok=True)

mesh = plate_with_hole(a=10, B=40, H=100, n_rad=18, n_ang=14, n_top=14)
mat = s355_epp()
S_path = [0.0, 220.0, -220.0, 220.0]
n_inc = 22   # increments per half cycle in the in-house run

# ------------------------------------------------------------------ in-house
m = FEModel2D(mesh, mat, "plane_stress", 1.0)
m.fix(mesh.sets["x0"], 0)
m.fix(mesh.sets["y0"], 1)
edges = element_edges_on(mesh, mesh.sets["top"])
f1 = m.edge_load_vector(edges, (0.0, 1.0))
steps, Svals = [], []
for a, b in zip(S_path[:-1], S_path[1:]):
    for s in np.linspace(a, b, n_inc + 1)[1:]:
        steps.append({"fext": s * f1, "tag": s})
        Svals.append(s)
root = int(np.argmin(np.hypot(mesh.nodes[:, 0] - 10, mesh.nodes[:, 1])))
top_node = int(mesh.sets["top"][np.argmin(mesh.nodes[mesh.sets["top"], 0])])
hist = {"S": [], "syy": [], "eyy": [], "uy_top": [], "peeq": []}


def cb(k, tag, u, st):
    sn = m.gauss_to_nodes(st["sig"])
    en = m.nodal_strain(u)
    pn = m.gauss_to_nodes(st["p"])
    hist["S"].append(tag)
    hist["syy"].append(sn[root, 1])
    hist["eyy"].append(en[root, 1])
    hist["uy_top"].append(u[2 * top_node + 1])
    hist["peeq"].append(pn[root])


run_history(m, steps, callback=cb)
for k in hist:
    hist[k] = np.array(hist[k])

# ------------------------------------------------------------------ CalculiX
inp = os.path.join(OUT, "plate.inp")
with open(inp, "w") as fh:
    fh.write("*HEADING\nPlate with hole, plane stress, EPP, cyclic\n*NODE, NSET=NALL\n")
    used = np.unique(mesh.elems[:, :8])
    for i in used:
        fh.write(f"{i+1}, {mesh.nodes[i,0]:.10f}, {mesh.nodes[i,1]:.10f}, 0.0\n")
    fh.write("*ELEMENT, TYPE=CPS8, ELSET=EALL\n")
    for e, conn in enumerate(mesh.elems):
        c = conn[:8] + 1
        fh.write(f"{e+1}, " + ", ".join(str(x) for x in c) + "\n")

    def nset(name, ids):
        fh.write(f"*NSET, NSET={name}\n")
        ids = list(ids + 1)
        for j in range(0, len(ids), 12):
            fh.write(", ".join(str(x) for x in ids[j:j+12]) + "\n")
    used_set = set(used.tolist())
    nset("X0", np.array([i for i in mesh.sets["x0"] if i in used_set]))
    nset("Y0", np.array([i for i in mesh.sets["y0"] if i in used_set]))
    nset("ROOT", np.array([root]))
    nset("TOPN", np.array([top_node]))
    fh.write("*MATERIAL, NAME=STEEL\n*ELASTIC\n210000., 0.3\n*PLASTIC\n355., 0.\n")
    fh.write("*SOLID SECTION, ELSET=EALL, MATERIAL=STEEL\n1.\n")
    fh.write("*BOUNDARY\nX0, 1, 1\nY0, 2, 2\n")
    # top-edge consistent nodal loads per unit stress
    f1_nodes = {i: f1[2 * i + 1] for i in mesh.sets["top"] if abs(f1[2 * i + 1]) > 0}
    fh.write("*AMPLITUDE, NAME=AMP\n0., 0., 1., 220., 2., -220., 3., 220.\n")
    fh.write("*STEP, INC=1000\n*STATIC\n0.04545, 3., 1e-6, 0.04545\n")
    fh.write("*CLOAD, AMPLITUDE=AMP\n")
    for i, v in f1_nodes.items():
        fh.write(f"{i+1}, 2, {v:.10e}\n")
    fh.write("*NODE PRINT, NSET=ROOT\nU\n*EL PRINT, ELSET=EALL\nS\n")
    fh.write("*NODE FILE, NSET=NALL\nU\n*EL FILE\nS, E, PEEQ\n")
    fh.write("*NODE PRINT, NSET=TOPN\nU\n")
    fh.write("*END STEP\n")
subprocess.run(["ccx", "-i", "plate"], cwd=OUT, check=True, stdout=subprocess.DEVNULL)

# parse .frd: nodal S, E, PEEQ blocks for ROOT and U for TOPN
frd = open(os.path.join(OUT, "plate.frd")).read().splitlines()
res = {"S": [], "E": [], "PEEQ": [], "DISP": []}
cur, time_val, times = None, None, []
for line in frd:
    if line.startswith("    1PSTEP"):
        pass
    if line.startswith("  100CL"):
        time_val = float(line[12:24])
    if line.startswith(" -4"):
        name = line.split()[1]
        cur = name if name in ("STRESS", "TOSTRAIN", "PE", "DISP") else None
        if cur == "DISP":
            times.append(time_val)
            res["DISP"].append({})
        elif cur == "STRESS":
            res["S"].append({})
        elif cur == "TOSTRAIN":
            res["E"].append({})
        elif cur == "PE":
            res["PEEQ"].append({})
        continue
    if cur and line.startswith(" -1"):
        nid = int(line[3:13])
        vals = [float(line[13 + 12 * j: 25 + 12 * j]) for j in range((len(line) - 13) // 12)]
        key = {"STRESS": "S", "TOSTRAIN": "E", "PE": "PEEQ", "DISP": "DISP"}[cur]
        res[key][-1][nid] = vals
times = np.array(times)
ccx = {
    "t": times,
    "syy": np.array([d[root + 1][1] for d in res["S"]]),
    "eyy": np.array([d[root + 1][1] for d in res["E"]]),
    "peeq": np.array([d[root + 1][0] for d in res["PEEQ"]]),
    "uy_top": np.array([d[top_node + 1][1] for d in res["DISP"]]),
}
amp_t = np.array([0, 1, 2, 3.0]); amp_v = np.array(S_path)
ccx["S"] = np.interp(ccx["t"], amp_t, amp_v)

# compare at the three reversal points and print
print(" point      in-house syy / eyy / uy_top / PEEQ      |   CalculiX syy / eyy / uy_top / PEEQ")
for target_t, idx in [(1.0, n_inc - 1), (2.0, 2 * n_inc - 1), (3.0, 3 * n_inc - 1)]:
    j = int(np.argmin(np.abs(ccx["t"] - target_t)))
    print(f"S={S_path[int(target_t)]:+6.0f}: {hist['syy'][idx]:8.2f} {hist['eyy'][idx]*100:7.4f}% {hist['uy_top'][idx]:8.5f} {hist['peeq'][idx]*100:7.4f}%"
          f"   |  {ccx['syy'][j]:8.2f} {ccx['eyy'][j]*100:7.4f}% {ccx['uy_top'][j]:8.5f} {ccx['peeq'][j]*100:7.4f}%")
np.savez(os.path.join(os.path.dirname(__file__), "..", "results", "verification_ccx.npz"),
         **{"inhouse_" + k: v for k, v in hist.items()}, **{"ccx_" + k: v for k, v in ccx.items()})
