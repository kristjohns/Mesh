"""Adds HEX8I (incompatible modes) results to the cantilever study."""
import json
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl
from localmodel import hex8i_stiffness, D_matrix

E, NU, L = 1000.0, 0.3, 10.0
d = json.load(open("/home/user/Mesh/video/data/cantilever.json"))
res = []
for n in [1, 2, 3, 4, 6]:
    nx = 10 * n
    xs, ys = np.linspace(0, L, nx + 1), np.linspace(0, 1, n + 1)
    idx = np.arange((nx + 1) * (n + 1) ** 2).reshape(nx + 1, n + 1, n + 1)
    X = np.array([(x, y, z) for x in xs for y in ys for z in ys])
    H = np.array([[idx[i, j, k], idx[i + 1, j, k], idx[i + 1, j + 1, k], idx[i, j + 1, k],
                   idx[i, j, k + 1], idx[i + 1, j, k + 1], idx[i + 1, j + 1, k + 1], idx[i, j + 1, k + 1]]
                  for i in range(nx) for j in range(n) for k in range(n)])
    Ke, _ = hex8i_stiffness(X[H], np.repeat(D_matrix(E, NU)[None], len(H), 0))
    dofs = (3 * H[:, :, None] + np.arange(3)).reshape(len(H), 24)
    K = sp.csr_matrix((Ke.ravel(), (np.repeat(dofs, 24, 1).ravel(), np.tile(dofs, (1, 24)).ravel())),
                      shape=(3 * len(X),) * 2)
    f = np.zeros(3 * len(X))
    tip = np.where(np.isclose(X[:, 0], L))[0]
    w = np.array([(0.5 if np.isclose(X[i, 1], 0) or np.isclose(X[i, 1], 1) else 1) *
                  (0.5 if np.isclose(X[i, 2], 0) or np.isclose(X[i, 2], 1) else 1) for i in tip])
    f[3 * tip + 2] = -w / w.sum()
    fx = np.where(np.isclose(X[:, 0], 0))[0]
    free = np.setdiff1d(np.arange(3 * len(X)), np.r_[3 * fx, 3 * fx + 1, 3 * fx + 2])
    u = np.zeros(3 * len(X))
    u[free] = spl.spsolve(K[free][:, free].tocsc(), f[free])
    ratio = -u[3 * tip + 2].mean() / d["w_ref"]
    res.append(dict(n=n, ndof=3 * len(X), ratio=float(ratio)))
    print("HEX8I", n, round(ratio, 4))
d["convergence"]["HEX8I"] = res
json.dump(d, open("/home/user/Mesh/video/data/cantilever.json", "w"))
