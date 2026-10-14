# Meshing with Purpose — FEA best practice, subsea wellhead & template case study

An animated, narrated explainer video (≈17 min, 1080p30) on finite element best practice for
structural analysis: element types, mesh size, soil springs and boundary conditions, worked
through on a subsea template with conductor, surface casing, conductor housing (LPWH) and
high-pressure wellhead housing (HPWHH).

Every result shown in the video was computed for it with the models in `compute/`.

## Contents

| Path | What |
|---|---|
| `output/` | Final video (`.mp4`, soft English subtitles) and `.srt` |
| `compute/` | Python FE models that produce all the data in `video/data/` |
| `video/narration/` | Narration script (`script.json`) and TTS generator |
| `video/src/` | Animation engine (Three.js + Canvas 2D + KaTeX) and the 14 scenes |
| `video/render.mjs` | Deterministic frame renderer (headless Chromium → ffmpeg) |
| `video/audio.py` | Soundtrack: narration, procedural score, SFX, ducking; subtitles |
| `video/assemble.py` | Cross-fades the scene chunks and muxes audio + subtitles |

## The computations (`compute/`)

| Script | Model | Used in |
|---|---|---|
| `cantilever.py`, `cantilever_hex8i.py` | 3D cantilever, 1–6 elements through the thickness: TET4, TET10, HEX8 (full / one-point), HEX20, HEX8 incompatible modes | element locking, hourglassing |
| `hourglass.py` | 2D Q4 mesh, full vs one-point integration | hourglass pattern |
| `notch.py` | Plane-stress stepped bar, quadratic triangles (gmsh + scikit-fem), fillet vs sharp corner, 7 refinement levels | mesh convergence & singularity |
| `localmodel.py` | Half 3D solid model of HPWHH in LPWH (37 368 incompatible-mode hexes, 139 749 DOF), penalty node-to-segment contact at the landing shoulder, pre-loaded lock ring, radial contacts; plus the same section as an axisymmetric model | axisymmetric vs 3D, contact lift-off, moment–rotation |
| `template.py` | 3D frame model of the 4-slot template (272 beam members), fixed vs suction-anchor foundation springs | template stiffness at the slot |
| `globalmodel.py`, `run_global.py` | Global beam model: conductor + casing + housings + BOP, cement links, interface springs calibrated from the local model, API/Matlock soft-clay p-y springs, template gap element | soil springs, mesh study, fixity, soil bounds, load sharing, hand-calc check |

Key numbers (all from these models): one element through the thickness gives TET4 22 %,
HEX8 65 %, TET10 98 %, HEX20 99 %, HEX8-incompatible 99 % of the correct tip deflection;
the filleted shoulder converges to Kt ≈ 2.29 (within 1 % at ≈ 12 elements around the fillet)
while the sharp corner grows ≈ 37 % per halving; peak conductor moment 2.96 MNm 5 m below the
mudline (+19 %); fixing the conductor at the mudline underestimates wellhead deflection by 96 %;
the 30 mm template gap closes at ≈ 50 kN and the contact force reaches 266 kN (1.8 × H);
lock-ring pre-load 7.3 MN, lift-off above ≈ 1.4 MNm, 43 % of the shoulder open at 3 MNm,
interface stiffness after lift-off 47 % of initial.

## Rebuilding

```bash
pip install numpy scipy gmsh scikit-fem pypardiso kokoro-onnx soundfile matplotlib
cd compute && python3 cantilever.py && python3 cantilever_hex8i.py && python3 hourglass.py \
  && python3 notch.py && python3 localmodel.py && python3 template.py && python3 run_global.py
cd ../video && npm install
python3 narration/tts.py            # needs Kokoro model files in ../tts_models
./render_all.sh                      # renders build/chunks/*.mp4 (Mesa llvmpipe via EGL)
python3 audio.py && python3 assemble.py
```

Preview a single frame: `node render.mjs --scene s06_axisym --stills 12.5,30`.
