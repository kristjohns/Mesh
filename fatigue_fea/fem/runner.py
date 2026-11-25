"""Cyclic load-history runner with probe and field recording."""
import numpy as np
from .solver import run_history
from .material import von_mises, equivalent_strain, SQ2


def mandel3_to_tensor4(s3):
    """in-plane Mandel [11,22,sqrt2*12] -> 4-comp Mandel with 33 = 0 (plane stress)."""
    out = np.zeros(s3.shape[:-1] + (4,))
    out[..., 0], out[..., 1], out[..., 3] = s3[..., 0], s3[..., 1], s3[..., 2]
    return out


class CyclicRecorder:
    def __init__(self, model, probes, field_steps=None, end_of_cycle_fields=True,
                 top_nodes=None, right_nodes=None):
        """probes: dict name -> node id. field_steps: set of step indices at which
        full nodal fields are stored (None = none)."""
        self.m = model
        self.probes = probes
        self.field_steps = set() if field_steps is None else set(field_steps)
        self.eoc = end_of_cycle_fields
        self.top_nodes = top_nodes
        self.right_nodes = right_nodes
        self.rows = []          # per-step scalars
        self.fields = {}        # step -> dict of nodal arrays
        self.eoc_fields = {}    # cycle -> dict of nodal arrays
        self.steps_meta = None

    def _nodal(self, u, st):
        m = self.m
        sig4 = mandel3_to_tensor4(st["sig"])
        sn = m.gauss_to_nodes(st["sig"])                       # Mandel in-plane
        vm = m.gauss_to_nodes(von_mises(sig4))
        pe = m.gauss_to_nodes(st["p"])
        epn = m.gauss_to_nodes(st["eps_p"])                    # 4 comps Mandel
        en = m.nodal_strain(u)                                  # Voigt total in-plane
        return sn, vm, pe, epn, en

    def __call__(self, k, tag, u, st):
        sn, vm, pe, epn, en = self._nodal(u, st)
        row = dict(step=k, **tag)
        for name, nid in self.probes.items():
            row[f"{name}_sxx"] = sn[nid, 0]
            row[f"{name}_syy"] = sn[nid, 1]
            row[f"{name}_sxy"] = sn[nid, 2] / SQ2
            row[f"{name}_vm"] = vm[nid]
            row[f"{name}_peeq"] = pe[nid]
            row[f"{name}_epyy"] = epn[nid, 1]
            row[f"{name}_epxx"] = epn[nid, 0]
            row[f"{name}_exx"] = en[nid, 0]
            row[f"{name}_eyy"] = en[nid, 1]
        if self.top_nodes is not None:
            row["uy_top"] = float(np.mean(u[2 * self.top_nodes + 1]))
        if self.right_nodes is not None:
            row["ux_right"] = float(np.mean(u[2 * self.right_nodes]))
        row["n_plastic_gp"] = int(np.count_nonzero(st["plastic"]))
        self.rows.append(row)
        want_field = k in self.field_steps
        want_eoc = self.eoc and tag.get("end_of_cycle", False)
        if want_field or want_eoc:
            fd = dict(vm=vm.astype(np.float32), peeq=pe.astype(np.float32),
                      syy=sn[:, 1].astype(np.float32), sxx=sn[:, 0].astype(np.float32),
                      ux=u[0::2].astype(np.float32), uy=u[1::2].astype(np.float32),
                      epyy=epn[:, 1].astype(np.float32), epxx=epn[:, 0].astype(np.float32),
                      epzz=epn[:, 2].astype(np.float32), epxy=(epn[:, 3] / SQ2).astype(np.float32))
            if want_field:
                self.fields[k] = fd
            if want_eoc:
                self.eoc_fields[tag["cycle"]] = fd

    def table(self):
        keys = self.rows[0].keys()
        return {k: np.array([r[k] for r in self.rows]) for k in keys}


def build_steps(S_fun, lam_fun, ncycles, ninc_half, f_unit, T_unit_gp=None, preload=None):
    """Increment list over ncycles. S_fun(tc), lam_fun(tc) with tc in cycles.
    preload: (S_pre, n_pre) -> ramp from 0 to S_pre before cycling (cycle 0)."""
    steps = []
    if preload is not None:
        S_pre, n_pre = preload
        for s in np.linspace(0, S_pre, n_pre + 1)[1:]:
            st = {"fext": s * f_unit, "tag": dict(cycle=0, tc=0.0, S=s, lam=0.0, end_of_cycle=False)}
            if T_unit_gp is not None:
                st["dT_gp"] = 0.0 * T_unit_gp
            steps.append(st)
    n_per = 2 * ninc_half
    for c in range(1, ncycles + 1):
        for j in range(1, n_per + 1):
            tc = (c - 1) + j / n_per
            S = S_fun(tc)
            lam = lam_fun(tc)
            st = {"fext": S * f_unit,
                  "tag": dict(cycle=c, tc=tc, S=S, lam=lam, end_of_cycle=(j == n_per))}
            if T_unit_gp is not None:
                st["dT_gp"] = lam * T_unit_gp
            steps.append(st)
    return steps


def triangle(tc, lo, hi, start="lo"):
    """Triangle wave with period 1 (in cycles): lo -> hi -> lo (start='lo')
    or for fully reversed use lo=-A, hi=+A with start='mid' (0 -> +A -> -A -> 0)."""
    f = tc % 1.0
    if abs(f) < 1e-12 and tc > 0:
        f = 1.0
    if start == "lo":
        return lo + (hi - lo) * (2 * f if f <= 0.5 else 2 * (1 - f))
    # start at mid: 0 -> hi (0.25) -> lo (0.75) -> 0 (1.0)
    mid = 0.5 * (lo + hi)
    A = 0.5 * (hi - lo)
    if f <= 0.25:
        return mid + A * (4 * f)
    if f <= 0.75:
        return mid + A * (1 - 4 * (f - 0.25))
    return mid - A + A * 4 * (f - 0.75)
