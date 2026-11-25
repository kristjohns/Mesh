"""
Material data used in the study (S355-type structural steel, illustrative values).

Cyclic stress-strain curve (stabilised, Ramberg-Osgood):
    eps_a = sigma_a/E + (sigma_a/K')^(1/n')     K' = 596 MPa, n' = 0.076
Strain-life (Coffin-Manson-Basquin):
    eps_a = sigma_f'/E (2N)^b + eps_f' (2N)^c
    sigma_f' = 952 MPa, b = -0.089, eps_f' = 0.737, c = -0.668
These are representative of published S355 low-cycle-fatigue test data; they are
used here for illustration only. Use test data for the actual material in design.
"""
from .material import J2Material

E_STEEL = 210000.0
NU_STEEL = 0.3

RO = dict(E=E_STEEL, Kp=596.0, nprime=0.076)
STRAIN_LIFE = dict(E=E_STEEL, sf=952.0, b=-0.089, ef=0.737, c=-0.668)
SIGMA_U = 510.0     # nominal ultimate strength used for mean-stress diagrams
SIGMA_Y = 355.0     # nominal (monotonic) yield strength


def s355_chaboche():
    """Chaboche (3 Armstrong-Frederick back-stresses) fitted to the stabilised
    cyclic curve above, sigma0 = 250 MPa (cyclic proportional limit)."""
    return J2Material(E=E_STEEL, nu=NU_STEEL, sigma0=250.0,
                      C=[485000.0, 42400.0, 6840.0], gamma=[8000.0, 800.0, 80.0],
                      name="S355 Chaboche (cyclic)")


def s355_prager():
    """Linear (Prager) kinematic hardening, same proportional limit - for comparison."""
    return J2Material(E=E_STEEL, nu=NU_STEEL, sigma0=250.0, C=[30000.0], gamma=[0.0],
                      name="S355 linear kinematic")


def s355_epp(sy=SIGMA_Y):
    """Elastic-perfectly plastic (as required by e.g. ASME VIII-2 for ratcheting checks)."""
    return J2Material(E=E_STEEL, nu=NU_STEEL, sigma0=sy, C=[], gamma=[], name="S355 EPP")
