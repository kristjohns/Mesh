"""Pre-render all finite element image sequences used by the manim scenes."""
import os, sys, json
import numpy as np
from multiprocessing import Pool
from fe_render import (render_field, mirrored, colorbar_png, STRESS_CMAP, PLAST_CMAP, DIVERGE, RES, OUT)
import matplotlib

PX_BIG, PX_SMALL = 700, 440
from matplotlib.colors import LinearSegmentedColormap
CORE_CMAP = LinearSegmentedColormap.from_list("core", [(0.0, "#4CC9F0"), (0.03, "#2a6f97"), (0.05, "#5a2a6b"),
                                                       (0.4, "#c13a7a"), (0.75, "#f0605d"), (1.0, "#ffd166")])
XL, YL = (-42, 42), (-62, 62)


def jobs_for(case, values_fn, idxs, tag, vmin, vmax, cmap, scale, px_w, source="F", xlim=XL, ylim=YL,
             mesh_lines=True):
    d = np.load(os.path.join(RES, f"plate_{case}.npz"))
    nodes, elems = d["nodes"], d["elems"]
    ux, uy = d[f"{source}_ux"], d[f"{source}_uy"]
    od = os.path.join(OUT, tag)
    os.makedirs(od, exist_ok=True)
    jobs = []
    for j, i in enumerate(idxs):
        fn = os.path.join(od, f"{j:04d}.png")
        if os.path.exists(fn):
            continue
        v = values_fn(d, i)
        P, E, UX, UY = mirrored(nodes, elems, ux[i], uy[i])
        V = np.tile(v, 4)
        Pd = P + scale * np.stack([UX, UY], axis=1)
        jobs.append(((Pd, E, V, fn, vmin, vmax, cmap, xlim, ylim), dict(px_w=px_w, mesh_lines=mesh_lines)))
    return jobs


def field(name, source="F"):
    return lambda d, i: d[f"{source}_{name}"][i]


def cyc_plastic(case):
    """max over the last cycle of the equivalent plastic strain change (nodal)."""
    d = np.load(os.path.join(RES, f"plate_{case}.npz"))
    comps = [d["F_epxx"][-40:], d["F_epyy"][-40:], d["F_epzz"][-40:], d["F_epxy"][-40:]]
    # reference: end of previous cycle = EOC[-2]
    ref = [d["EOC_epxx"][-2], d["EOC_epyy"][-2], d["EOC_epzz"][-2], d["EOC_epxy"][-2]]
    dxx, dyy, dzz, dxy = [c - r[None, :] for c, r in zip(comps, ref)]
    eq = np.sqrt(2.0 / 3.0 * (dxx ** 2 + dyy ** 2 + dzz ** 2 + 2 * dxy ** 2))
    return eq.max(axis=0)


def weld_jobs():
    d = np.load(os.path.join(RES, "weld_tjoint.npz"))
    meta = json.loads(str(d["meta"]))
    nodes, elems = d["nodes"], d["elems"]
    jobs = []
    for kind in ["bending", "membrane"]:
        s1 = d[f"{kind}_s1"]
        ux, uy = d[f"{kind}_ux"], d[f"{kind}_uy"]
        P, E, UX, UY = mirrored(nodes, elems, ux, uy, quadrants=2)
        V = np.tile(s1, 2)
        od = os.path.join(OUT, f"weld_{kind}")
        os.makedirs(od, exist_ok=True)
        for tag, xl, yl, px, ml in [("full", (-95, 95), (-12, 68), 1500, False), ("toe", (9.0, 19.0), (16.5, 24.0), 900, True),
                                     ("mid", (-2, 60), (-4, 34), 1100, True)]:
            fn = os.path.join(od, f"{tag}.png")
            if not os.path.exists(fn):
                jobs.append(((P, E, V, fn, -20, 280, STRESS_CMAP, xl, yl), dict(px_w=px, mesh_lines=ml, line_alpha=0.22)))
    return jobs


def run(jobs):
    def _one(a):
        return a
    with Pool(4) as p:
        p.map(_work, jobs, chunksize=4)


def _work(job):
    a, k = job
    render_field(*a, **k)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    J = []
    first3 = list(range(0, 120))
    # intro: LCF von Mises, cycles 1-3, big
    J += jobs_for("lcf", field("vm"), first3, "intro_lcf_vm", 0, 400, STRESS_CMAP, 25, PX_BIG)
    # four mechanical cases, von Mises, cycles 1-3 + PEEQ end-of-cycle
    for c in ["hcf", "shake", "lcf", "ratchet_m"]:
        J += jobs_for(c, field("vm"), first3, f"fea_{c}_vm", 0, 400, STRESS_CMAP, 25, PX_SMALL)
        d = np.load(os.path.join(RES, f"plate_{c}.npz"))
        neoc = d["EOC_peeq"].shape[0]
        J += jobs_for(c, field("peeq", "EOC"), list(range(neoc)), f"fea_{c}_peeq", 0, 0.03, PLAST_CMAP, 0,
                      PX_SMALL, source="EOC")
    # Kt map (elastic, peak of first cycle)
    J += jobs_for("hcf", lambda d, i: d["F_syy"][i] / 70.0, [9], "kt_map", -0.6, 3.3, STRESS_CMAP, 0, PX_BIG)
    # local plastic zone in the shakedown case at first peak
    J += jobs_for("shake", field("peeq"), [19], "shake_zone", 0, 0.001, PLAST_CMAP, 0, PX_BIG)
    J += jobs_for("shake", field("vm"), [19], "shake_vm_peak", 0, 400, STRESS_CMAP, 0, PX_BIG)
    # thermo-mechanical cases
    for c in ["tm_altpl", "tm_ratchet", "tm_shake"]:
        d = np.load(os.path.join(RES, f"plate_{c}.npz"))
        J += jobs_for(c, field("vm"), list(range(10, 130)), f"{c}_vm", 0, 360, STRESS_CMAP, 25, PX_SMALL)
        neoc = d["EOC_peeq"].shape[0]
        J += jobs_for(c, field("peeq", "EOC"), list(range(neoc)), f"{c}_peeq", 0, 0.05, PLAST_CMAP, 0,
                      PX_SMALL, source="EOC")
        cp = cyc_plastic(c)
        np.save(os.path.join(OUT, f"{c}_cycplast.npy"), cp)
        core = np.where(cp < 1e-6, 0.0, np.clip(np.log10(cp / 1e-6) / 4.0, 0.05, 1.0))
        J += jobs_for(c, lambda d, i, core=core: core, [0], f"{c}_core", 0, 1, CORE_CMAP,
                      0, PX_SMALL, source="EOC")
        # temperature field
        J += jobs_for(c, lambda d, i: d["T_unit"], [0], f"{c}_temp", 0, 1,
                      matplotlib.colormaps["coolwarm"], 0, PX_SMALL, source="EOC", mesh_lines=False)
    J += weld_jobs()
    print(len(J), "frames to render")
    with Pool(4) as p:
        p.map(_work, J, chunksize=8)
    # colourbars
    colorbar_png(os.path.join(OUT, "cb_vm.png"), STRESS_CMAP, 0, 400, "MPa", [0, 100, 200, 300, 400])
    colorbar_png(os.path.join(OUT, "cb_peeq.png"), PLAST_CMAP, 0, 3, "%", [0, 1, 2, 3])
    colorbar_png(os.path.join(OUT, "cb_kt.png"), STRESS_CMAP, -0.6, 3.3, "", [0, 1, 2, 3])
    colorbar_png(os.path.join(OUT, "cb_weld.png"), STRESS_CMAP, -20, 280, "MPa", [0, 100, 200])
    colorbar_png(os.path.join(OUT, "cb_vm360.png"), STRESS_CMAP, 0, 360, "MPa", [0, 100, 200, 300])
    colorbar_png(os.path.join(OUT, "cb_peeq5.png"), PLAST_CMAP, 0, 5, "%", [0, 1, 2, 3, 4, 5])
    print("done")
