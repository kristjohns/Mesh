"""2D plane-strain demonstration of hourglassing with one-point integrated Q4 elements.

Simply supported deep beam with a concentrated load at the top centre.
Full integration (2x2) vs one-point integration with a very weak hourglass control.
"""
import json
import numpy as np
from scipy.sparse.linalg import spsolve
from skfem import MeshQuad, ElementVector, ElementQuad1, Basis, asm, condense
from skfem.models.elasticity import linear_elasticity, lame_parameters

LX, LY, NX, NY = 8.0, 1.6, 20, 4
E, NU = 1000.0, 0.3


def run(one_point, eps=0.0):
    m = MeshQuad.init_tensor(np.linspace(0, LX, NX + 1), np.linspace(0, LY, NY + 1))
    e = ElementVector(ElementQuad1())
    lam, mu = lame_parameters(E, NU)
    if one_point:
        ib = Basis(m, e, quadrature=(np.array([[0.5], [0.5]]), np.array([1.0])))
    else:
        ib = Basis(m, e, intorder=2)
    K = asm(linear_elasticity(lam, mu), ib)
    if eps > 0:
        K = K + eps * asm(linear_elasticity(lam, mu), Basis(m, e, intorder=2))
    f = np.zeros(K.shape[0])
    top_mid = np.where(np.isclose(m.p[0], LX / 2) & np.isclose(m.p[1], LY))[0][0]
    f[ib.nodal_dofs[1, top_mid]] = -1.0
    left = np.where(np.isclose(m.p[0], 0) & np.isclose(m.p[1], 0))[0][0]
    right = np.where(np.isclose(m.p[0], LX) & np.isclose(m.p[1], 0))[0][0]
    D = np.array([ib.nodal_dofs[0, left], ib.nodal_dofs[1, left], ib.nodal_dofs[1, right]])
    Kc, fc, xc, I = condense(K, f, D=D)
    u = np.zeros(K.shape[0])
    u[I] = spsolve(Kc.tocsc(), fc)
    U = u[ib.nodal_dofs].T
    return m, U


out = {"LX": LX, "LY": LY, "nx": NX, "ny": NY}
m, U_full = run(False)
_, U_hg = run(True, eps=3e-4)
out["p"] = np.round(m.p.T, 5).tolist()
out["quads"] = m.t.T.tolist()
out["u_full"] = np.round(U_full, 6).tolist()
out["u_hg"] = np.round(U_hg, 6).tolist()
print("max |v| full:", np.abs(U_full[:, 1]).max(), " one-point:", np.abs(U_hg[:, 1]).max())
with open("/home/user/Mesh/video/data/hourglass.json", "w") as fh:
    json.dump(out, fh)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig, axs = plt.subplots(2, 1, figsize=(10, 5))
for ax, U, t in [(axs[0], U_full, "full"), (axs[1], U_hg, "1-pt")]:
    s = 0.3 / np.abs(U).max()
    q = m.p.T + s * U
    for el in m.t.T:
        poly = q[[el[0], el[1], el[2], el[3], el[0]]]
        ax.plot(poly[:, 0], poly[:, 1], "k-", lw=0.7)
    ax.set_aspect("equal")
    ax.set_title(t)
plt.savefig("/tmp/claude-0/-home-user-Mesh/c131553b-1455-59eb-a52d-b9f2446358da/scratchpad/hg.png", dpi=70)
