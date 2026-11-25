"""9-node Lagrangian quadrilateral (Q9) with 3x3 Gauss integration."""
import numpy as np

# natural coordinates of the Q9 nodes (standard ordering)
Q9_NODES = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1],
                     [0, -1], [1, 0], [0, 1], [-1, 0], [0, 0]], dtype=float)
_IJ = [(0, 0), (2, 0), (2, 2), (0, 2), (1, 0), (2, 1), (1, 2), (0, 1), (1, 1)]


def _lag(t):
    return np.array([0.5 * t * (t - 1.0), (1.0 - t) * (1.0 + t), 0.5 * t * (t + 1.0)])


def _dlag(t):
    return np.array([t - 0.5, -2.0 * t, t + 0.5])


def q9_shape(xi, eta):
    """Returns N (9,), dN/dxi (9,), dN/deta (9,)."""
    Lx, Ly = _lag(xi), _lag(eta)
    dLx, dLy = _dlag(xi), _dlag(eta)
    N = np.array([Lx[i] * Ly[j] for i, j in _IJ])
    dNx = np.array([dLx[i] * Ly[j] for i, j in _IJ])
    dNy = np.array([Lx[i] * dLy[j] for i, j in _IJ])
    return N, dNx, dNy


def gauss_3x3():
    g = np.sqrt(0.6)
    pts1 = np.array([-g, 0.0, g])
    w1 = np.array([5.0, 8.0, 5.0]) / 9.0
    pts = np.array([[x, y] for y in pts1 for x in pts1])
    w = np.array([wx * wy for wy in w1 for wx in w1])
    return pts, w


# Q9 sub-triangulation for smooth (Gouraud) plotting: 8 triangles around node 9
Q9_TRIS = np.array([[0, 4, 8], [4, 1, 8], [1, 5, 8], [5, 2, 8],
                    [2, 6, 8], [6, 3, 8], [3, 7, 8], [7, 0, 8]])
# element outline (curved edges through mid-side nodes)
Q9_OUTLINE = [0, 4, 1, 5, 2, 6, 3, 7, 0]


def gauss_to_node_matrix():
    """Matrix X (9 nodes x 9 gauss) such that nodal = X @ gauss for a field
    that is biquadratic over the element (exact extrapolation for Q9 / 3x3)."""
    pts, _ = gauss_3x3()
    A = np.array([q9_shape(*p)[0] for p in pts])   # A[g, n]
    return np.linalg.inv(A)
