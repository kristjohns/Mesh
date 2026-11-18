import numpy as np, time
from epfem import *
a, b, h = 50.0, 100.0, 2.0
sy = 517.0
mat = Material(210000.0, 0.3, sy)
# graded radial node spacing (denser at the bore)
nr = 40
xs = a + (b - a) * (np.linspace(0, 1, 2 * nr + 1) ** 1.3)
X, T = structured_t6(a, b, 0, h, nr, 1, xgrade=xs)
m = Model(X, T, mat, mode="axisym")
m.fix(m.nodes_where(lambda x, y: np.isclose(y, 0)), 1)
m.fix(m.nodes_where(lambda x, y: np.isclose(y, h)), 1)        # plane strain (eps_z = 0)
bore = m.nodes_where(lambda x, y: np.isclose(x, a))
umax = 0.6
m.fix(bore, 0, lambda t: umax * t)
area = 2 * np.pi * a * h
mon = dict(p=lambda md, u, f: -f[2 * bore].sum() / area * -1,
           u=lambda md, u, f: u[2 * bore[0]],
           c=lambda md, u, f: md.XQ.reshape(-1, 2)[md.state["eb"] > 0, 0].max() if (md.state["eb"] > 0).any() else a)
ts = np.r_[0, np.linspace(0.02, 1, 60)]
t0 = time.time()
H = m.solve(ts, monitors=mon)
print(f"solve {time.time()-t0:.1f}s converged={H['converged']}")
k = sy / np.sqrt(3)
py_hill = k * (1 - a**2 / b**2); pc_hill = 2 * k * np.log(b / a)
p = np.array(H["p"]); print("p range", p.min(), p.max())
print(f"Hill: p_y={py_hill:.1f}  p_c={pc_hill:.1f} MPa;  FE max p = {np.abs(p).max():.1f}")
# first yield in FE: first step with plasticity
cs = np.array(H["c"])
for pp, c in zip(np.abs(p), cs):
    if c > a + 0.01:
        hill_p = k * (2 * np.log(c / a) + 1 - c**2 / b**2)
        print(f"  p={pp:7.1f}  plastic radius c={c:6.2f} mm   Hill p(c)={hill_p:7.1f}")
