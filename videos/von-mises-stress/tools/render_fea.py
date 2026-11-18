"""Offscreen PyVista renders of the 3D FE results (frame sequences + stills).

usage: xvfb-run -a python tools/render_fea.py [--shots open_a,open_b,...] [--preview]
Frames: build/frames/<shot>/f_00000.png (1920x1080, 30 fps)
Anchors: build/frames/<shot>/anchors.json  (per-frame screen positions of 3D points, Manim units)
"""
import argparse
import json
import os

import numpy as np
import pyvista as pv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FR = os.path.join(ROOT, "build", "frames")
DUR = json.load(open(os.path.join(ROOT, "build", "audio", "durations.json")))
D = np.load(os.path.join(ROOT, "build", "fea", "fea3d.npz"))
SUMM = json.load(open(os.path.join(ROOT, "assets", "fea", "summary.json")))
W, H, FPS = 1920, 1080, 30
FW, FH = 14.222222, 8.0                       # Manim frame size
BG_BOT, BG_TOP = "#05070C", "#18202F"
C_N, C_M, C_T = "#FF6B6B", "#6BCB77", "#FFD93D"

P = D["p"].T.copy()
TRI = D["tri"].T
TET = D["t"].T
Ri, Ro1, Ro2, ZS, L = 116.55, 136.55, 170.0, 600.0, 1020.0
PEAK = np.array(D["peak_xyz"], dtype=float)
TH_PEAK = np.arctan2(PEAK[1], PEAK[0])

surf = pv.PolyData(P, np.hstack([np.full((len(TRI), 1), 3), TRI]).ravel())
for k in ("vm", "vm_inv", "srr", "stt", "szz", "srt", "stz", "srz"):
    surf.point_data[k] = D[k]
surf = surf.compute_normals(split_vertices=True, feature_angle=35, auto_orient_normals=True)
grid = pv.UnstructuredGrid({pv.CellType.TETRA: TET}, P)
for k in ("vm", "srr", "stt", "szz", "srt", "stz", "srz"):
    grid.point_data[k] = D[k]
# cut plane containing the axis and the peak point; keep the far half (camera sits on -n side)
n_cut = np.array([-np.sin(TH_PEAK), np.cos(TH_PEAK), 0.0])
half = grid.clip(normal=n_cut, origin=(0, 0, 0), invert=True).extract_surface()
half = half.compute_normals(split_vertices=True, feature_angle=35)

VM_MAX = 300.0


def smooth(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return (1 - t) * np.asarray(a, float) + t * np.asarray(b, float)


def new_plotter(size=(W, H)):
    pl = pv.Plotter(off_screen=True, window_size=size, lighting="light kit")
    pl.set_background(BG_BOT, top=BG_TOP)
    pl.enable_anti_aliasing("ssaa")
    return pl


METAL = dict(color="#A3ADBB", specular=1.0, specular_power=70, ambient=0.12, diffuse=0.66, smooth_shading=True)


def arc_arrow(center, axis, radius, a0, a1, color, tube=6.0, head=26.0):
    """Curved arrow (tube + cone) around `axis` through `center` from angle a0 to a1 (rad)."""
    axis = np.asarray(axis, float) / np.linalg.norm(axis)
    ref = np.array([1.0, 0, 0]) if abs(axis[0]) < 0.9 else np.array([0, 1.0, 0])
    e1 = np.cross(axis, ref); e1 /= np.linalg.norm(e1)
    e2 = np.cross(axis, e1)
    ang = np.linspace(a0, a1, 60)
    pts = np.array([center + radius * (np.cos(a) * e1 + np.sin(a) * e2) for a in ang])
    line = pv.Spline(pts, 120).tube(radius=tube)
    tip = pts[-1]
    tang = pts[-1] - pts[-2]; tang /= np.linalg.norm(tang)
    cone = pv.Cone(center=tip + tang * head * 0.5, direction=tang, height=head, radius=tube * 2.6, resolution=32)
    return line + cone


def straight_arrow(start, direction, length, color, tube=7.0):
    a = pv.Arrow(start=start, direction=direction, scale=length, tip_length=0.28, tip_radius=0.11,
                 shaft_radius=0.04, tip_resolution=40, shaft_resolution=40)
    return a


def load_glyphs():
    """Axial force N, bending moment M (about y), torque T at both ends."""
    g = []
    zc0, zc1 = -40.0, L + 40.0
    g.append((straight_arrow((0, 0, zc0), (0, 0, -1), 260, C_N), C_N))
    g.append((straight_arrow((0, 0, zc1), (0, 0, 1), 260, C_N), C_N))
    g.append((arc_arrow(np.array([0, 0, -95.0]), (0, 1, 0), 120, np.pi * 0.15, -np.pi * 0.95, C_M), C_M))
    g.append((arc_arrow(np.array([0, 0, L + 95.0]), (0, 1, 0), 120, np.pi * 1.15, np.pi * 0.05, C_M), C_M))
    g.append((arc_arrow(np.array([0, 0, 30.0]), (0, 0, 1), Ro1 + 45, 0.3, 0.3 + 1.6 * np.pi, C_T, tube=5.5), C_T))
    g.append((arc_arrow(np.array([0, 0, L - 30.0]), (0, 0, 1), Ro2 + 45, 0.3 + 1.6 * np.pi, 0.3, C_T, tube=5.5),
              C_T))
    return g


ANCHORS = {"N": (0, 0, L + 330), "M": (0, 150, L + 95), "T": (Ro2 + 70, 0, L - 30), "peak": tuple(PEAK),
           "pipe": (Ro1, 0, 250.0)}


def to_manim(pl, xyz):
    r = pl.renderer
    r.SetWorldPoint(*xyz, 1.0)
    r.WorldToDisplay()
    x, y, _ = r.GetDisplayPoint()
    sx, sy = pl.window_size
    return [round((x / sx - 0.5) * FW, 4), round((y / sy - 0.5) * FH, 4)]


def cam_orbit(focal, dist, yaw, pitch, up_hint=(1, 0, 0)):
    """Camera looking at `focal` from the +y side (pipe on the left, hub on the right, tension side up).

    yaw  : rotation about the vertical (x) axis; negative = towards the pipe end (sees the shoulder face)
    pitch: elevation above the y-z plane (towards +x, the tension side)
    """
    yaw, pitch = np.radians(yaw), np.radians(pitch)
    d = np.array([np.sin(pitch), np.cos(pitch) * np.cos(yaw), np.cos(pitch) * np.sin(yaw)])
    return [tuple(np.asarray(focal) + dist * d), tuple(focal), up_hint]


def render_shot(name, nframes, setup, update, anchors=()):
    out = os.path.join(FR, name)
    os.makedirs(out, exist_ok=True)
    pl = new_plotter()
    state = setup(pl)
    anc = {k: [] for k in anchors}
    for i in range(nframes):
        t = i / max(1, nframes - 1)
        update(pl, state, t, i)
        pl.render()
        pl.screenshot(os.path.join(out, f"f_{i:05d}.png"))
        for k in anchors:
            anc[k].append(to_manim(pl, ANCHORS[k]))
    json.dump(anc, open(os.path.join(out, "anchors.json"), "w"))
    pl.close()
    print(f"{name}: {nframes} frames", flush=True)


# ---------------------------------------------------------------- shots
def shot_open_a(nf):
    """Opening: steel component, loads appear one by one, slow orbit."""
    def setup(pl):
        pl.add_mesh(surf, **METAL)
        acts = []
        for mesh, col in load_glyphs():
            a = pl.add_mesh(mesh, color=col, ambient=0.3, diffuse=0.8, specular=0.4, smooth_shading=True)
            a.GetProperty().SetOpacity(0.0)
            acts.append(a)
        return acts

    def update(pl, acts, t, i):
        yaw = lerp(-34, -16, smooth(t)); pitch = lerp(16, 24, t)
        dist = lerp(2700, 2250, smooth(t))
        pl.camera_position = cam_orbit((0, 0, 540), dist, yaw, pitch)
        pl.camera.view_angle = 30
        for k, a in enumerate(acts):
            t0 = [0.2, 0.2, 0.42, 0.42, 0.62, 0.62][k]
            a.GetProperty().SetOpacity(float(smooth((t - t0) / 0.1)))
    return setup, update


def shot_open_b(nf):
    """Opening: cut-away, stress field builds with the load factor, camera dives to the hot spot."""
    def setup(pl):
        a = pl.add_mesh(half, scalars="vm", cmap="turbo", clim=[0, VM_MAX], n_colors=14, smooth_shading=True,
                        show_scalar_bar=False, specular=0.35, specular_power=30, ambient=0.18,
                        interpolate_before_map=True)
        return dict(actor=a, base=half.point_data["vm"].copy())

    def update(pl, st, t, i):
        lam = smooth(t / 0.45)
        half.point_data["vm"] = st["base"] * lam
        yaw = lerp(-16, -28, smooth(t)); pitch = lerp(24, 20, smooth(t))
        focal = lerp((0, 0, 540), PEAK + np.array([-10.0, 0, -12.0]), smooth((t - 0.35) / 0.65))
        dist = lerp(2250, 420, smooth((t - 0.38) / 0.62))
        pitch = lerp(24, 8, smooth((t - 0.35) / 0.65))
        pl.camera_position = cam_orbit(tuple(focal), dist, yaw, pitch)
        pl.camera.view_angle = 30
    return setup, update


def shot_fea_model(nf):
    def setup(pl):
        pl.add_mesh(surf, **METAL)
        for mesh, col in load_glyphs():
            pl.add_mesh(mesh, color=col, ambient=0.3, diffuse=0.8, specular=0.4, smooth_shading=True)
        return None

    def update(pl, st, t, i):
        pl.camera_position = cam_orbit((0, 0, 560), lerp(2500, 2300, t), lerp(-40, -10, t), lerp(14, 22, t))
        pl.camera.view_angle = 30
    return setup, update


def shot_fea_mesh(nf):
    def setup(pl):
        pl.add_mesh(surf, color="#C9D1DD", show_edges=True, edge_color="#202838", line_width=0.7,
                    ambient=0.25, diffuse=0.7, specular=0.2, smooth_shading=False)
        return None

    def update(pl, st, t, i):
        s = smooth(t)
        focal = lerp((0, 0, 560), PEAK, s)
        pl.camera_position = cam_orbit(tuple(focal), lerp(2300, 330, s), lerp(-10, -32, s), lerp(22, 30, s))
        pl.camera.view_angle = 30
    return setup, update


def shot_fea_vm(nf):
    def setup(pl):
        pl.add_mesh(half, scalars="vm", cmap="turbo", clim=[0, VM_MAX], n_colors=14, smooth_shading=True,
                    show_scalar_bar=False, specular=0.3, ambient=0.18, interpolate_before_map=True)
        pl.add_mesh(pv.Sphere(radius=2.2, center=PEAK), color="white")
        return None

    def update(pl, st, t, i):
        s = smooth(t)
        focal = lerp((0, 0, 600), PEAK, smooth((t - 0.45) / 0.55))
        dist = lerp(1500, 420, smooth((t - 0.45) / 0.55))
        yaw = lerp(-8, -26, s)
        pl.camera_position = cam_orbit(tuple(focal) if t < 0.45 else tuple(lerp(focal, PEAK + np.array([-10.0, 0, -12.0]),
                                                                               smooth((t - 0.45) / 0.55))),
                                       dist, yaw, lerp(22, 8, smooth((t - 0.4) / 0.6)))
        pl.camera.view_angle = 30
    return setup, update


COMP_KEYS = [("srr", r"\sigma_{rr}"), ("stt", r"\sigma_{\theta\theta}"), ("szz", r"\sigma_{zz}"),
             ("srt", r"\tau_{r\theta}"), ("stz", r"\tau_{\theta z}"), ("srz", r"\tau_{rz}")]
COMP_CAM = cam_orbit((Ro1 - 12, 0, ZS - 30), 470, -24, 7)


def stills_components():
    out = os.path.join(FR, "components"); os.makedirs(out, exist_ok=True)
    info = {}
    for k, lab in COMP_KEYS + [("vm", r"\sigma_{vm}")]:
        pl = new_plotter(size=(1280, 720))
        vals = half.point_data[k]
        if k == "vm":
            clim, cmap = [0, VM_MAX], "turbo"
        else:
            a = float(np.percentile(np.abs(vals), 99.5)); a = max(a, 1.0)
            clim, cmap = [-a, a], "turbo"
        pl.add_mesh(half, scalars=k, cmap=cmap, clim=clim, n_colors=14, smooth_shading=True,
                    show_scalar_bar=False, specular=0.3, ambient=0.2, interpolate_before_map=True)
        pl.camera_position = COMP_CAM
        pl.camera.view_angle = 30
        pl.render()
        pl.screenshot(os.path.join(out, f"{k}.png"))
        info[k] = dict(label=lab, clim=clim, cmap=cmap, min=float(vals.min()), max=float(vals.max()))
        pl.close()
    json.dump(info, open(os.path.join(out, "info.json"), "w"), indent=1)
    print("components done", flush=True)


SHOTS = {
    "open_a": (shot_open_a, lambda: DUR["o1"] + 0.3, ("N", "M", "T")),
    "open_b": (shot_open_b, lambda: 0.62 * DUR["o2"], ("peak",)),
    "fea_model": (shot_fea_model, lambda: DUR["f1"] + 0.3, ("N", "M", "T")),
    "fea_mesh": (shot_fea_mesh, lambda: DUR["f2"] + 0.3, ()),
    "fea_vm": (shot_fea_vm, lambda: DUR["f6"] + 0.3, ("peak", "pipe")),
}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--shots", default="open_a,open_b,fea_model,fea_mesh,fea_vm,components")
    ap.add_argument("--preview", action="store_true", help="render 3 stills per shot only")
    a = ap.parse_args()
    for s in a.shots.split(","):
        if s == "components":
            stills_components()
            continue
        fn, dur, anc = SHOTS[s]
        setup, update = fn(0)
        nf = int(round(dur() * FPS))
        if a.preview:
            out = os.path.join(FR, "preview"); os.makedirs(out, exist_ok=True)
            pl = new_plotter(size=(960, 540)); st = setup(pl)
            for t in (0.0, 0.5, 1.0):
                update(pl, st, t, 0); pl.render(); pl.screenshot(os.path.join(out, f"{s}_{t:.1f}.png"))
            pl.close(); print("preview", s, nf, "frames")
        else:
            render_shot(s, nf, setup, update, anc)
