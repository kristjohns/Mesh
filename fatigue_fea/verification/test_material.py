"""Verification of the J2 / Chaboche return mapping at a single material point."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
from scipy.optimize import brentq
from fem.material import J2Material, chaboche_cyclic_curve
from fem.materials_lib import s355_chaboche, s355_prager, s355_epp, RO
from fem.matpoint import uniaxial, triangle_wave


def ro_amplitude(eps_a, E, Kp, nprime):
    return brentq(lambda s: s / E + (s / Kp) ** (1 / nprime) - eps_a, 1.0, 2000.0)


def test_stabilised_loop():
    mat = s355_chaboche()
    for ea in [0.002, 0.005, 0.01]:
        h = triangle_wave(ea, 6, nper_quarter=60)
        r = uniaxial(mat, h, control="strain")
        n = 240
        last = slice(-n, None)
        sa = 0.5 * (r["sig11"][last].max() - r["sig11"][last].min())
        epa = 0.5 * (r["epsp11"][last].max() - r["epsp11"][last].min())
        analytic = chaboche_cyclic_curve(epa, mat.sigma0, mat.C, mat.gamma)
        ro = ro_amplitude(ea, RO["E"], RO["Kp"], RO["nprime"])
        print(f"eps_a={ea:.3f}: FE sigma_a={sa:7.2f}  analytic Chaboche={analytic:7.2f}  "
              f"Ramberg-Osgood target={ro:7.2f}  (eps_pa={epa:.5f})")
        assert abs(sa - analytic) < 0.5


def test_tangent_fd():
    mat = s355_chaboche()
    rng = np.random.default_rng(1)
    st = mat.new_state(1)
    # pre-strain to build back-stress
    eps = np.array([[0.004, -0.001, -0.0015, 0.002]])
    _, _, st, _ = mat.update(eps, st)
    eps2 = eps + np.array([[-0.003, 0.002, 0.0005, -0.004]])
    sig, Ct, _, pl = mat.update(eps2, st)
    assert pl[0]
    h = 1e-8
    Cfd = np.zeros((4, 4))
    for j in range(4):
        d = np.zeros((1, 4)); d[0, j] = h
        sp, _, _, _ = mat.update(eps2 + d, st)
        sm, _, _, _ = mat.update(eps2 - d, st)
        Cfd[:, j] = (sp[0] - sm[0]) / (2 * h)
    err = np.max(np.abs(Cfd - Ct[0])) / np.max(np.abs(Ct[0]))
    print("consistent tangent vs finite difference, rel. error =", f"{err:.2e}")
    assert err < 1e-5


def test_ratcheting_models():
    """Stress-controlled cycling with mean stress: linear kinematic -> no ratcheting,
    Armstrong-Frederick/Chaboche -> ratcheting."""
    for mat in [s355_prager(), s355_chaboche()]:
        h = triangle_wave(300.0, 20, nper_quarter=40, mean=60.0)
        r = uniaxial(mat, h, control="stress")
        per = 160
        e_end = r["eps11"][per - 1::per]
        rate = np.diff(e_end)
        print(f"{mat.name:28s} ratchet strain per cycle: first {rate[0]*100:.4f} %, last {rate[-1]*100:.4f} %")


def test_epp_uniaxial():
    mat = s355_epp()
    r = uniaxial(mat, np.linspace(0, 0.01, 50), control="strain")
    assert abs(r["sig11"][-1] - 355.0) < 1e-6
    print("EPP uniaxial: stress at 1% strain =", round(r["sig11"][-1], 4))


if __name__ == "__main__":
    test_stabilised_loop()
    test_tangent_fd()
    test_ratcheting_models()
    test_epp_uniaxial()
    print("material tests passed")
