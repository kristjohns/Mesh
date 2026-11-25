"""Structured (mapped) Q9 meshes."""
import numpy as np


def _graded(n, ratio):
    """n elements between 0 and 1, size ratio last/first = ratio; returns 2n+1
    parameter values (corner + mid-side nodes)."""
    if abs(ratio - 1.0) < 1e-12:
        c = np.linspace(0.0, 1.0, n + 1)
    else:
        q = ratio ** (1.0 / (n - 1)) if n > 1 else 1.0
        h = q ** np.arange(n)
        c = np.concatenate([[0.0], np.cumsum(h)]) / h.sum()
    full = np.empty(2 * n + 1)
    full[0::2] = c
    full[1::2] = 0.5 * (c[:-1] + c[1:])
    return full


def _grid_to_q9(G):
    """G: (2nx+1, 2ny+1, 2) node grid -> list of Q9 connectivity in grid indices."""
    nx = (G.shape[0] - 1) // 2
    ny = (G.shape[1] - 1) // 2
    els = []
    for ej in range(ny):
        for ei in range(nx):
            i0, j0 = 2 * ei, 2 * ej
            els.append([(i0, j0), (i0 + 2, j0), (i0 + 2, j0 + 2), (i0, j0 + 2),
                        (i0 + 1, j0), (i0 + 2, j0 + 1), (i0 + 1, j0 + 2), (i0, j0 + 1),
                        (i0 + 1, j0 + 1)])
    return els


class Mesh:
    def __init__(self, nodes, elems):
        self.nodes = np.asarray(nodes, float)
        self.elems = np.asarray(elems, int)

    @property
    def nn(self):
        return self.nodes.shape[0]

    @property
    def ne(self):
        return self.elems.shape[0]


def merge_blocks(blocks, tol=1e-9):
    """blocks: list of node grids (2nx+1, 2ny+1, 2). Returns Mesh with merged nodes."""
    all_nodes, all_els = [], []
    offset = 0
    for G in blocks:
        nxp, nyp = G.shape[0], G.shape[1]
        idx = lambda ij: offset + ij[0] * nyp + ij[1]
        all_nodes.append(G.reshape(-1, 2))
        for e in _grid_to_q9(G):
            all_els.append([idx(ij) for ij in e])
        offset += nxp * nyp
    nodes = np.concatenate(all_nodes)
    key = np.round(nodes / tol).astype(np.int64)
    _, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
    inv = inv.ravel()
    # keep node order by first appearance
    order = np.argsort(first)
    remap = np.empty_like(order)
    remap[order] = np.arange(order.size)
    new_nodes = nodes[first[order]]
    els = remap[inv[np.array(all_els)]]
    return Mesh(new_nodes, els)


def plate_with_hole(a=10.0, B=40.0, H=100.0, n_rad=18, n_ang=14, n_top=14,
                    rad_ratio=12.0, top_ratio=4.0):
    """Quarter model of a plate (half-width B, half-length H) with a central hole
    of radius a. Symmetry planes x = 0 and y = 0. Q9 elements.
    n_ang elements per 45 degree sector, n_rad radial elements, n_top elements
    in the upper rectangular block (y from B to H)."""
    s = _graded(n_rad, rad_ratio)                     # 0 at hole, 1 at outer square
    blocks = []
    # block A: theta 0..45 deg, outer edge x = B
    th = np.linspace(0.0, np.pi / 4, 2 * n_ang + 1)
    G = np.zeros((s.size, th.size, 2))
    for j, t in enumerate(th):
        pin = a * np.array([np.cos(t), np.sin(t)])
        pout = np.array([B, B * np.tan(t)])
        G[:, j, :] = (1 - s)[:, None] * pin + s[:, None] * pout
    blocks.append(G)
    # block B: theta 45..90 deg, outer edge y = B
    th = np.linspace(np.pi / 4, np.pi / 2, 2 * n_ang + 1)
    G = np.zeros((s.size, th.size, 2))
    for j, t in enumerate(th):
        pin = a * np.array([np.cos(t), np.sin(t)])
        pout = np.array([B / np.tan(t) if t < np.pi / 2 - 1e-12 else 0.0, B])
        G[:, j, :] = (1 - s)[:, None] * pin + s[:, None] * pout
    blocks.append(G)
    # top block: x from B..0 (matching block B outer edge), y from B..H
    xs = G[-1, :, 0]                                  # x positions along y = B
    ys = B + (H - B) * _graded(n_top, top_ratio)
    T = np.zeros((xs.size, ys.size, 2))
    # orientation: first index must run so that (i, j) is counter-clockwise:
    # i along -x (x decreasing) and j along +y gives clockwise -> use x increasing
    xs_inc = xs[::-1]
    for i, x in enumerate(xs_inc):
        T[i, :, 0] = x
        T[i, :, 1] = ys
    blocks.append(T)
    mesh = merge_blocks(blocks)
    X, Y = mesh.nodes[:, 0], mesh.nodes[:, 1]
    r = np.hypot(X, Y)
    tol = 1e-7 * B
    mesh.sets = {
        "hole": np.nonzero(np.abs(r - a) < tol)[0],
        "x0": np.nonzero(np.abs(X) < tol)[0],
        "y0": np.nonzero(np.abs(Y) < tol)[0],
        "top": np.nonzero(np.abs(Y - H) < tol)[0],
        "right": np.nonzero(np.abs(X - B) < tol)[0],
    }
    mesh.geom = dict(a=a, B=B, H=H)
    return mesh


def element_edges_on(mesh, node_set):
    """Return list of 3-node element edges (corner, mid, corner) lying on node_set."""
    S = set(int(i) for i in node_set)
    edges = []
    local = [(0, 4, 1), (1, 5, 2), (2, 6, 3), (3, 7, 0)]
    for e in mesh.elems:
        for (i, m, j) in local:
            if e[i] in S and e[m] in S and e[j] in S:
                edges.append((e[i], e[m], e[j]))
    return np.array(edges, int)
