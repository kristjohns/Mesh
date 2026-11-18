# Yield Is Not Failure

A 10-minute film that answers a follow-up question to *The Physics of Failure*:

> If yielding is not failure because the stress redistributes, show five finite element cases where you get yield but not
> failure, explain how you determine that, and say what the criteria are.

Output: `output/yield_is_not_failure.mp4` (1080p30, AAC stereo, soft English subtitles) and `output/yield_is_not_failure.srt`.

## The five cases

Every number in the film comes from the elastic-plastic analyses in `fe/` (`assets/fe/*.json`). The solver was written
for this film: `fe/epfem.py` (6-node triangles, J2 radial return with consistent tangent, Newton-Raphson,
plane stress / plane strain / axisymmetric, thermal strain, DOF ties).

| Case | Model | First yield | What decides | Result |
|---|---|---|---|---|
| 1. Plate with a hole | plane stress, S355, EPP, W 200 / d 60 / t 20 mm | 421 kN (K_t,net = 2.36) | Limit load: ASME VIII-2 §5.2.3, EPP with σy = 1.5 S, converged at 1.5 × loads | FE limit 996 kN (σY·A_net = 994 kN). First yield at 42 % of collapse. Allowable design load 549 kN, where the elastic peak is 463 MPa. Same answer as Pm ≤ S |
| 2. Plastic hinge | plane stress, 100 × 50 mm section, pure bending | 29.6 kN·m | Shape factor and twice-elastic-slope (TES) collapse load, allowable = 2/3 of collapse | EPP approaches Mp = 44.4 kN·m (max. difference from the closed form 0.02 % of Mp). TES with the true curve: 43.0 kN·m, allowable 28.6 kN·m ≈ M_Y |
| 3. Thick-walled cylinder (HPHT body) | axisymmetric plane strain, a/b = 50/100 mm, 75 ksi forging (517 MPa), EPP | 224 MPa (Hill 223.9) | Elastic-plastic global criterion: converged at 2.4 × design (ASME VIII-2 §5.2.4) | Design 20 ksi (137.9 MPa), bore at 62 % of yield. At 2.4 × design, 31 % of the wall is plastic (c = 65.40 mm, Hill 65.37) and the solution converges. Collapse at 413 MPa = 3.0 × rating (Hill 413.8). Residual hoop stress at the bore after unloading: −284 MPa. Shakedown because 331 < 2 p_Y = 448 MPa |
| 4. Transition-piece fillet | axisymmetric, S355 true stress-strain curve, R8 fillet | 1.08 × design (K_t = 2.19) | Local failure at 1.7 × loads: ε_peq + ε_cf ≤ ε_L (ASME VIII-2 §5.3.3, triaxial strain limit) | Elastic peak at 1.7 × would be 558 MPa. FE: ε_peq = 0.18 %, triaxiality 0.556, ε_L = 26.0 % (ε_Lu = 0.398, m2 = 0.147, α_sl = 2.2). Utilisation 0.7 %. Neuber: 0.24 % |
| 5. Bree cylinder | axisymmetric, open ends, R 200 / t 10 mm, EPP, cyclic through-wall ΔT under constant pressure, 10 cycles | first heat-up | Cyclic elastic-plastic ratcheting check (ASME VIII-2 §5.5.7): shakedown, an elastic core, or no permanent change in dimensions | (X, Y) = (0.3, 1.4): shakedown, hoop strain constant at 0.060 %. (0.1, 2.6): alternating plasticity, diameter stable, plastic strain reverses every cycle, so a fatigue check follows. (0.6, 2.4): ratcheting, about +0.03 % hoop strain per cycle without stabilising |

**Validation.** `fe/validate_cylinder.py` checks the solver against Hill's exact thick-cylinder solution:

- first yield: 224.0 MPa from FE, against 223.9 MPa;
- collapse: 413.1 MPa from FE, against 413.8 MPa;
- the plastic front lies within 0.5 % of the exact position.

## Caveats

- The code clauses (ASME VIII-2 Part 5, EN 13445-3 Annex B, DNV-RP-C208 and API 17TR8) are summarised from secondary
  sources. The load-case combinations are simplified to the dominant pressure, static-head and dead-weight terms. Check
  the edition in force before using any of them.
- All analyses use small-strain theory. ASME §5.2.4 asks for large-deformation theory and the true curve. Case 3 uses
  an elastic-perfectly plastic material instead, which is conservative for hardening but leaves out geometric softening.
- The S355 and 75 ksi properties are representative. They come from no certificate. The S355 true-curve form follows
  DNV-RP-C208.
- The narration is synthetic: Kokoro TTS, voice af_heart.

## Reproduce

```bash
cd fe && python validate_cylinder.py && for i in 1 2 3 4 5; do python cases.py $i; done && python extra_images.py && cd ..
python tools/tts.py --speed 1.12                         # needs kokoro-onnx models in build/models
MANIM=manim tools/render_scenes.sh h 4 Y00_Open Y01_Why Y02_Method Y03_Plate Y04_Beam Y05_Cylinder Y06_Fillet Y07_Bree Y08_Criteria
python tools/assemble.py --quality 1080p30 --out output/yield_is_not_failure.mp4
```

Requirements: Manim CE 0.19+ with LaTeX, gmsh, numpy/scipy/matplotlib, soundfile and ffmpeg.
