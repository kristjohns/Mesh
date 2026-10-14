"""Hot-spot stress at the two housing welds, from the local solid model (DNV-RP-C203 section 4).

The half model of localmodel.py is rebuilt with the mesh refined below the two girth welds:
  * conductor housing (LPWH) to 36" conductor,  z = 0.8 m, wall t = 38.1 mm
  * HP housing (HPWHH) to 20" surface casing,    z = 1.2 m, wall t = 15.9 mm
After the lock-ring preload step a bending moment is applied at the top of the HP housing.
The fatigue stress is the change from the preload state (a stress range does not care about the
static preload). On the outer surface of each pipe, on the tension side, the axial stress is read
at 0.5 t and 1.5 t from the weld toe and extrapolated linearly to the toe:
    sigma_hs = 1.5 sigma(0.5t) - 0.5 sigma(1.5t)
Both surfaces are read (outer weld toe and inside weld toe): a thickness transition whose
mid-surface steps sideways adds local wall bending that raises the stress on one surface only.
The nominal stress is M c / I (c = outer radius) with M the moment that pipe carries at the toe
section (integrated from the solid model), so SCF = sigma_hs / sigma_nom can be combined with section
moments from the global beam model.  Writes ../video/data/hotspot.json.
"""
import json
import time
import numpy as np
import localmodel as L
from localmodel import Mesh2D, rect

T_COND = L.R_COND_O - L.R_COND_I      # 38.1 mm
T_CAS = L.R_CAS_O - L.R_BORE          # 15.9 mm
WELDS = {
    "lpwh": dict(z=L.Z_COND_TOP, r_out=L.R_COND_O, r_in=L.R_COND_I, t=T_COND, group="O"),
    "hpwhh": dict(z=L.Z_CAS_TOP, r_out=L.R_CAS_O, r_in=L.R_BORE, t=T_CAS, group="I"),
}


def build_profile_refined():
    """localmodel.build_profile with elements of about t/2 in length below both welds."""
    m = Mesh2D()
    gi = lambda r, z: "I"
    go = lambda r, z: "O"

    def gc(r, z):
        if abs(r - L.R_CAS_O) < 1e-9:
            return "I"
        if abs(r - L.R_COND_I) < 1e-9:
            return "O"
        return "C"

    # inner body: surface casing + HPWHH
    m.block(rect(L.R_BORE, L.R_CAS_O, L.Z_BOT, L.Z_TOC), 4, 15, "casing", 0, gi)
    m.block(rect(L.R_BORE, L.R_CAS_O, L.Z_TOC, 0.90), 4, 18, "casing", 0, gi)
    m.block(rect(L.R_BORE, L.R_CAS_O, 0.90, L.Z_CAS_TOP), 4, 38, "casing", 0, gi)          # 7.9 mm
    m.block([(L.R_BORE, L.Z_CAS_TOP), (L.R_CAS_O, L.Z_CAS_TOP), (L.R_HP_O, L.Z_HP_TAPER), (L.R_BORE, L.Z_HP_TAPER)],
            4, 20, "hpwhh", 0, gi)
    m.block(rect(L.R_BORE, L.R_HP_O, L.Z_HP_TAPER, L.Z_SHOULDER), 4, 28, "hpwhh", 0, gi)
    m.block(rect(L.R_BORE, L.R_HP_O, L.Z_SHOULDER, L.Z_RING_TOP), 4, 10, "hpwhh", 0, gi)
    m.block(rect(L.R_HP_O, L.R_RING, L.Z_SHOULDER, L.Z_RING_TOP), 5, 10, "hpwhh", 0, gi)
    m.block(rect(L.R_BORE, L.R_HP_O, L.Z_RING_TOP, L.Z_HP_TOP), 4, 30, "hpwhh", 0, gi)
    # cement
    m.block(rect(L.R_CAS_O, L.R_COND_I, L.Z_BOT, L.Z_TOC), 6, 15, "cement", 1, gc)
    # outer body: conductor + LPWH
    m.block(rect(L.R_COND_I, L.R_COND_O, L.Z_BOT, L.Z_TOC), 5, 15, "conductor", 0, go)
    m.block(rect(L.R_COND_I, L.R_COND_O, L.Z_TOC, 0.40), 5, 8, "conductor", 0, go)
    m.block(rect(L.R_COND_I, L.R_COND_O, 0.40, L.Z_COND_TOP), 5, 21, "conductor", 0, go)    # 19 mm
    m.block([(L.R_COND_I, L.Z_COND_TOP), (L.R_COND_O, L.Z_COND_TOP), (L.R_LP_O, L.Z_LP_TAPER), (L.R_LP_LOW_I, L.Z_LP_TAPER)],
            5, 16, "lpwh", 0, go)
    m.block(rect(L.R_LP_LOW_I, L.R_LP_BORE, L.Z_LP_TAPER, L.Z_SHOULDER), 2, 36, "lpwh", 0, go)
    m.block(rect(L.R_LP_BORE, L.R_LP_O, L.Z_LP_TAPER, L.Z_SHOULDER), 3, 36, "lpwh", 0, go)
    m.block(rect(L.R_LP_BORE, L.R_LP_O, L.Z_SHOULDER, L.Z_RING_TOP), 3, 10, "lpwh", 0, go)
    m.block(rect(L.R_GROOVE, L.R_LP_O, L.Z_RING_TOP, L.Z_GROOVE_TOP), 2, 3, "lpwh", 0, go)
    m.block(rect(L.R_LP_BORE, L.R_LP_O, L.Z_GROOVE_TOP, L.Z_LP_TOP), 3, 3, "lpwh", 0, go)
    m.pts = np.array(m.pts)
    m.quads = np.array(m.quads)
    m.qbody = np.array(m.qbody)
    m.qmat = np.array(m.qmat)
    return m


def element_stress(s3, u):
    ue = u[s3.edofs]
    return L.hex8i_centre_stress(s3.X[s3.hex], s3.Dm, s3.Rrec, ue)   # (ne, 6) xx yy zz xy yz zx


def pipe_rows(s3, w, k):
    """Element rows of a pipe wall below a weld, in theta sector k: returns z-centres (sorted)
    and for each row the list of element indices ordered from inner to outer radius."""
    m = s3.m
    q = m.quads
    rc = m.pts[q, 0].mean(axis=1)
    zc = m.pts[q, 1].mean(axis=1)
    sel = np.where((rc > w["r_in"]) & (rc < w["r_out"]) & (zc < w["z"]) & (zc > w["z"] - 0.25))[0]
    rows = {}
    for qi in sel:
        rows.setdefault(round(zc[qi], 7), []).append(qi)
    zs = np.array(sorted(rows))
    out = []
    nq = len(q)
    for z in zs:
        qs = sorted(rows[z], key=lambda i: rc[i])
        out.append([k * nq + i for i in qs])
    return zs, out, rc


def surface_axial(s3, sig, w, k, side="out"):
    """Axial stress on the outer (or inner) surface along z, by linear extrapolation of the two
    outermost (innermost) element-centre values through the wall (k = theta sector)."""
    zs, rows, rc = pipe_rows(s3, w, k)
    m = s3.m
    nq = len(m.quads)
    surf = []
    for row in rows:
        a, b = (row[-2], row[-1]) if side == "out" else (row[1], row[0])
        ra, rb = rc[a % nq], rc[b % nq]
        sa, sb = sig[a, 2], sig[b, 2]
        r_s = w["r_out"] if side == "out" else w["r_in"]
        surf.append(sb + (sb - sa) * (r_s - rb) / (rb - ra))
    return zs, np.array(surf)


def section_moment(s3, sig, w, zrow):
    """Bending moment carried by the pipe (about the y axis) at the element row nearest zrow,
    integrated over the half model and doubled. Elements store centre stress; area = r dr dtheta."""
    m = s3.m
    q = m.quads
    nq = len(q)
    rc = m.pts[q, 0].mean(axis=1)
    zc = m.pts[q, 1].mean(axis=1)
    dr = np.ptp(m.pts[q, 0], axis=1)
    sel = np.where((rc > w["r_in"]) & (rc < w["r_out"]) & (np.abs(zc - zrow) < 1e-6))[0]
    dth = s3.th[1] - s3.th[0]
    M = 0.0
    for kk in range(s3.nth):
        th = 0.5 * (s3.th[kk] + s3.th[kk + 1])
        for qi in sel:
            e = kk * nq + qi
            x = rc[qi] * np.cos(th)
            M += sig[e, 2] * x * rc[qi] * dr[qi] * dth
    return 2 * M


def main():
    m = build_profile_refined()
    print("2D quads", len(m.quads))
    pairs2d = L.make_pairs2d(m)
    s3 = L.Solid3D(m, nth=36)
    s3.assemble()
    s3.build_pairs(pairs2d)
    s3.bcs()
    t0 = time.time()
    u0, state = s3.solve_contact(np.zeros(s3.ndof), verbose=False)
    sig0 = element_stress(s3, u0)
    out = dict(cases=[], welds={})
    levels = [0.25e6, 0.5e6, 1.0e6]
    sig_list = []
    for M in levels:
        F = s3.top_load(M / 2, M / 13.0 / 2)
        u, st = s3.solve_contact(F, state=state.copy(), verbose=False)
        sig_list.append(element_stress(s3, u) - sig0)
        print(f"M={M / 1e6:.2f} MNm solved ({time.time() - t0:.0f}s)")
    k_t = s3.nth - 1          # sector next to theta = pi: tension side (top pushed towards +x)
    for name, w in WELDS.items():
        t = w["t"]
        I = np.pi / 4 * (w["r_out"] ** 4 - w["r_in"] ** 4)
        res = dict(z=w["z"], t=t, r_out=w["r_out"], r_in=w["r_in"], I=I, levels=[])
        for M, sig in zip(levels, sig_list):
            lev = dict(M_top=M)
            for side in ("out", "in"):
                zs, surf = surface_axial(s3, sig, w, k_t, side)
                # the sector centre is at theta = pi - dth/2: scale to theta = pi
                surf = surf / np.cos(0.5 * (s3.th[1] - s3.th[0]))
                surf = surf * np.sign(surf.mean())  # report the tension side as positive
                d = w["z"] - zs                     # distance from the toe
                s05 = np.interp(0.5 * t, d[::-1], surf[::-1])
                s15 = np.interp(1.5 * t, d[::-1], surf[::-1])
                lev[side] = dict(s05=s05, s15=s15, shs=1.5 * s05 - 0.5 * s15, d=np.round(d, 5).tolist(),
                                 surf=np.round(surf / 1e6, 4).tolist())
            # nominal stress: moment carried by the pipe, extrapolated to the toe section
            zrow = zs[np.argmin(np.abs(d - 1.5 * t))]
            Msec = abs(section_moment(s3, sig, w, zrow))
            zrow2 = zs[np.argmin(np.abs(d - 3.0 * t))]
            Msec2 = abs(section_moment(s3, sig, w, zrow2))
            Mtoe = Msec + (Msec - Msec2) * (zrow - w["z"]) / (zrow2 - zrow)
            snom_out = Mtoe * w["r_out"] / I
            snom_in = Mtoe * w["r_in"] / I
            lev.update(M_toe=Mtoe, snom=snom_out, snom_in=snom_in,
                       scf_out=lev["out"]["shs"] / snom_out, scf_in=lev["in"]["shs"] / snom_out)
            lev["side"] = "out" if lev["scf_out"] >= lev["scf_in"] else "in"
            lev["scf"] = max(lev["scf_out"], lev["scf_in"])
            res["levels"].append(lev)
            print(f"{name} M={M / 1e6:.2f}: Mtoe={Mtoe / 1e3:.1f} kNm  snom={snom_out / 1e6:.2f} MPa | "
                  f"outer: {lev['out']['s05'] / 1e6:.2f} {lev['out']['s15'] / 1e6:.2f} -> {lev['out']['shs'] / 1e6:.2f} "
                  f"(SCF {lev['scf_out']:.3f}) | inner: {lev['in']['s05'] / 1e6:.2f} {lev['in']['s15'] / 1e6:.2f} -> "
                  f"{lev['in']['shs'] / 1e6:.2f} (SCF {lev['scf_in']:.3f})")
        res["scf"] = res["levels"][1]["scf"]
        res["side"] = res["levels"][1]["side"]
        out["welds"][name] = res
    # surface field for the video: outer-surface axial stress (MPa) on the loaded state 0.5 MNm
    sig = sig_list[1]
    acc = np.zeros(s3.nn)
    cnt = np.zeros(s3.nn)
    for a in range(8):
        np.add.at(acc, s3.hex[:, a], sig[:, 2])
        np.add.at(cnt, s3.hex[:, a], 1)
    szz_n = acc / np.maximum(cnt, 1)
    surf = L.surface_export(s3, [szz_n], [u0 * 0.0])
    out["surface"] = dict(X=surf["X"], quads=surf["quads"], quad_body=surf["quad_body"],
                          szz=surf["states"][0]["vm"], M_top=levels[1])
    # 2D profile for drawing the section with the mesh
    out["profile"] = dict(pts=np.round(m.pts, 6).tolist(), quads=m.quads.tolist(), body=m.qbody.tolist())
    # section stress (theta = pi row of elements) for the section plot
    nq = len(m.quads)
    out["section_szz"] = np.round(sig[(s3.nth - 1) * nq:(s3.nth) * nq, 2] / 1e6, 3).tolist()
    out["n_hex"] = int(len(s3.hex))
    out["n_dof"] = int(s3.ndof)
    with open("/home/user/Mesh/video/data/hotspot.json", "w") as fh:
        json.dump(out, fh)
    print("written, hexes", len(s3.hex), "dofs", s3.ndof)


if __name__ == "__main__":
    main()
