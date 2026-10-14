"""4-slot subsea template: frame geometry (shared with the 3D visuals) and a 3D frame
analysis giving the lateral stiffness of a well-slot receptacle.

Coordinates [m]: x along the long side, y across, z up from the mudline.
"""
import json
import numpy as np

E, G = 207e9, 79.6e9

SECTIONS = {
    # name: (kind, dims)  kind tube: (D, t) ; box: (h, b, t)
    "girder": ("box", (1.0, 0.6, 0.030)),
    "slotframe": ("box", (0.6, 0.45, 0.025)),
    "ring": ("box", (0.45, 0.35, 0.040)),
    "column": ("tube", (0.610, 0.025)),
    "brace": ("tube", (0.406, 0.016)),
    "strut": ("tube", (0.356, 0.020)),
    "roof": ("tube", (0.406, 0.016)),
    "slope": ("tube", (0.324, 0.0127)),
}


def section_props(name):
    kind, d = SECTIONS[name]
    if kind == "tube":
        D, t = d
        Di = D - 2 * t
        A = np.pi / 4 * (D ** 2 - Di ** 2)
        I = np.pi / 64 * (D ** 4 - Di ** 4)
        return A, I, I, 2 * I
    h, b, t = d
    A = h * b - (h - 2 * t) * (b - 2 * t)
    Iy = (b * h ** 3 - (b - 2 * t) * (h - 2 * t) ** 3) / 12
    Iz = (h * b ** 3 - (h - 2 * t) * (b - 2 * t) ** 3) / 12
    Am = (h - t) * (b - t)
    J = 4 * Am ** 2 * t / (2 * (h - t) + 2 * (b - t))
    return A, Iy, Iz, J


XL = [-12.0, -7.5, -3.5, 3.5, 7.5, 12.0]
YL = [-10.0, -6.5, -2.5, 2.5, 6.5, 10.0]
Z_BOT = 1.0
Z_SLOT = 2.0
Z_ROOF = 7.5
SLOTS = [(5.5, 4.5), (-5.5, 4.5), (-5.5, -4.5), (5.5, -4.5)]
ANCHORS = [(10.0, 8.0), (-10.0, 8.0), (-10.0, -8.0), (10.0, -8.0)]
R_RECEPTACLE = 0.75


def build():
    nodes = []
    key = {}

    def N(x, y, z):
        k = (round(x, 4), round(y, 4), round(z, 4))
        if k not in key:
            key[k] = len(nodes)
            nodes.append(k)
        return key[k]

    members = []

    def M(a, b, sec, group):
        if a != b:
            members.append((a, b, sec, group))

    # bottom frame: perimeter and internal grid girders
    for y in YL:
        for x0, x1 in zip(XL[:-1], XL[1:]):
            if y in (-10.0, 10.0, -2.5, 2.5) or abs(x0) >= 7.5 or abs(x1) >= 7.5 or y in (-6.5, 6.5):
                M(N(x0, y, Z_BOT), N(x1, y, Z_BOT), "girder", "bottom")
    for x in XL:
        for y0, y1 in zip(YL[:-1], YL[1:]):
            M(N(x, y0, Z_BOT), N(x, y1, Z_BOT), "girder", "bottom")
    # bottom plan diagonals in the corner bays (anchor bays)
    for sx in (-1, 1):
        for sy in (-1, 1):
            M(N(sx * 12, sy * 10, Z_BOT), N(sx * 7.5, sy * 6.5, Z_BOT), "brace", "bottom")
            M(N(sx * 12, sy * 6.5, Z_BOT), N(sx * 7.5, sy * 10, Z_BOT), "brace", "bottom")
    # anchors: interface node at each anchor top tied to surrounding bottom nodes
    anchor_nodes = []
    for ax, ay in ANCHORS:
        a = N(ax, ay, Z_BOT)
        anchor_nodes.append(a)
        sx, sy = np.sign(ax), np.sign(ay)
        for (x, y) in [(12 * sx, 10 * sy), (7.5 * sx, 10 * sy), (12 * sx, 6.5 * sy), (7.5 * sx, 6.5 * sy)]:
            M(a, N(x, y, Z_BOT), "girder", "anchor")
    # well slots: square frame at slot level, legs to the bottom frame, receptacle ring + struts
    receptacles = []
    for (cx, cy) in SLOTS:
        x0, x1 = cx - 2.0, cx + 2.0
        y0, y1 = cy - 2.0, cy + 2.0
        sq = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        for (xa, ya), (xb, yb) in zip(sq, sq[1:] + sq[:1]):
            M(N(xa, ya, Z_SLOT), N(xb, yb, Z_SLOT), "slotframe", "slot")
            M(N(xa, ya, Z_BOT), N(xa, ya, Z_SLOT), "column", "slot")
            # diagonal in each vertical face
            M(N(xa, ya, Z_BOT), N(0.5 * (xa + xb), 0.5 * (ya + yb), Z_SLOT), "brace", "slot")
            M(N(xb, yb, Z_BOT), N(0.5 * (xa + xb), 0.5 * (ya + yb), Z_SLOT), "brace", "slot")
        ring = []
        for k in range(8):
            a = k * np.pi / 4
            ring.append(N(cx + R_RECEPTACLE * np.cos(a), cy + R_RECEPTACLE * np.sin(a), Z_SLOT))
        for k in range(8):
            M(ring[k], ring[(k + 1) % 8], "ring", "receptacle")
        # struts: 0/90/180/270 to mid-edges, 45/... to corners
        mids = [(x1, cy), (cx, y1), (x0, cy), (cx, y0)]
        for k, (mx, my) in enumerate(mids):
            M(ring[2 * k], N(mx, my, Z_SLOT), "strut", "receptacle")
        cors = [(x1, y1), (x0, y1), (x0, y0), (x1, y0)]
        for k, (mx, my) in enumerate(cors):
            M(ring[2 * k + 1], N(mx, my, Z_SLOT), "strut", "receptacle")
        receptacles.append(ring)
    # columns from slot-level corners up to the roof (protective structure)
    roof_x = [-7.5, -3.5, 3.5, 7.5]
    roof_y = [-6.5, -2.5, 2.5, 6.5]
    for x in roof_x:
        for y in roof_y:
            base_z = Z_SLOT if (abs(x) in (3.5, 7.5) and abs(y) in (2.5, 6.5)) else Z_BOT
            M(N(x, y, base_z), N(x, y, Z_ROOF), "column", "column")
    # roof grid
    for y in roof_y:
        for x0, x1 in zip(roof_x[:-1], roof_x[1:]):
            M(N(x0, y, Z_ROOF), N(x1, y, Z_ROOF), "roof", "roof")
    for x in roof_x:
        for y0, y1 in zip(roof_y[:-1], roof_y[1:]):
            M(N(x, y0, Z_ROOF), N(x, y1, Z_ROOF), "roof", "roof")
    # sloped protective sides: from roof perimeter down to bottom perimeter
    for x in roof_x:
        M(N(x, 6.5, Z_ROOF), N(x, 10.0, Z_BOT), "slope", "slope")
        M(N(x, -6.5, Z_ROOF), N(x, -10.0, Z_BOT), "slope", "slope")
    for y in roof_y:
        M(N(7.5, y, Z_ROOF), N(12.0, y, Z_BOT), "slope", "slope")
        M(N(-7.5, y, Z_ROOF), N(-12.0, y, Z_BOT), "slope", "slope")
    for sx in (-1, 1):
        for sy in (-1, 1):
            M(N(sx * 7.5, sy * 6.5, Z_ROOF), N(sx * 12, sy * 10, Z_BOT), "slope", "slope")
    # mid-height ring of the sloped sides (stiffening)
    return nodes, members, anchor_nodes, receptacles


ANCHOR_SPRINGS = np.array([80e6, 80e6, 400e6, 4e9, 4e9, 2e9])  # kx, ky, kz, rx, ry, rz


def frame_stiffness(nodes, members, supports, springs=None):
    X = np.array(nodes)
    nn = len(X)
    K = np.zeros((6 * nn, 6 * nn))
    for a, b, sec, _ in members:
        A, Iy, Iz, J = section_props(sec)
        d = X[b] - X[a]
        L = np.linalg.norm(d)
        ex = d / L
        ref = np.array([0, 0, 1.0]) if abs(ex[2]) < 0.9 else np.array([1.0, 0, 0])
        ey = np.cross(ref, ex)
        ey /= np.linalg.norm(ey)
        ez = np.cross(ex, ey)
        T3 = np.vstack([ex, ey, ez])
        k = np.zeros((12, 12))
        EA, GJ = E * A / L, G * J / L
        k[0, 0] = k[6, 6] = EA
        k[0, 6] = k[6, 0] = -EA
        k[3, 3] = k[9, 9] = GJ
        k[3, 9] = k[9, 3] = -GJ
        for (I, v, th, sgn) in [(Iz, 1, 5, 1), (Iy, 2, 4, -1)]:
            c = E * I / L ** 3
            idx = [v, th, v + 6, th + 6]
            kb = c * np.array([[12, 6 * L * sgn, -12, 6 * L * sgn],
                               [6 * L * sgn, 4 * L ** 2, -6 * L * sgn, 2 * L ** 2],
                               [-12, -6 * L * sgn, 12, -6 * L * sgn],
                               [6 * L * sgn, 2 * L ** 2, -6 * L * sgn, 4 * L ** 2]])
            for i in range(4):
                for j in range(4):
                    k[idx[i], idx[j]] += kb[i, j]
        T = np.zeros((12, 12))
        for i in range(4):
            T[3 * i:3 * i + 3, 3 * i:3 * i + 3] = T3
        kg = T.T @ k @ T
        dofs = np.r_[6 * a + np.arange(6), 6 * b + np.arange(6)]
        K[np.ix_(dofs, dofs)] += kg
    if springs is not None:
        for s in supports:
            K[6 * s + np.arange(6), 6 * s + np.arange(6)] += springs
        return K, np.arange(6 * nn)
    fixed = np.concatenate([6 * s + np.arange(6) for s in supports])
    free = np.setdiff1d(np.arange(6 * nn), fixed)
    return K, free


def main():
    nodes, members, anchors, receptacles = build()
    print(len(nodes), "nodes", len(members), "members")
    out = {}
    disp_modes = {}
    for label, springs in [("fixed", None), ("foundation", ANCHOR_SPRINGS)]:
      K, free = frame_stiffness(nodes, members, anchors, springs)
      Kf = K[np.ix_(free, free)]
      for dirn, comp in [("x", 0), ("y", 1)]:
        F = np.zeros(K.shape[0])
        ring = receptacles[0]
        for n in ring:
            F[6 * n + comp] = 1e6 / len(ring)
        u = np.zeros(K.shape[0])
        u[free] = np.linalg.solve(Kf, F[free])
        d = np.mean([u[6 * n + comp] for n in ring])
        out[label + "_k_" + dirn] = 1e6 / d
        disp_modes[label + dirn] = u.reshape(-1, 6)[:, :3]
        print(f"{label}: template stiffness at slot receptacle in {dirn}: {1e6 / d / 1e6:.1f} MN/m")
    data = dict(nodes=nodes, members=[dict(a=a, b=b, sec=s, group=g) for a, b, s, g in members],
                sections={k: dict(kind=v[0], dims=v[1]) for k, v in SECTIONS.items()},
                anchors=[dict(x=x, y=y, node=n) for (x, y), n in zip(ANCHORS, anchors)],
                slots=[dict(x=x, y=y) for x, y in SLOTS], receptacle_radius=R_RECEPTACLE,
                z_bottom=Z_BOT, z_slot=Z_SLOT, z_roof=Z_ROOF, k_slot=out,
                mode_x=np.round(disp_modes["foundationx"] / np.abs(disp_modes["foundationx"]).max(), 5).tolist(),
                mode_x_fixed=np.round(disp_modes["fixedx"] / np.abs(disp_modes["fixedx"]).max(), 5).tolist())
    with open("/home/user/Mesh/video/data/template.json", "w") as fh:
        json.dump(data, fh)


if __name__ == "__main__":
    main()
