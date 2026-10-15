# Meshing with Purpose — FEA best practice, subsea wellhead & template case study

An animated, narrated explainer video (17 min, 1080p30) on finite element best practice for
structural analysis: element types, mesh size, soil springs and boundary conditions, worked
through on a subsea template with conductor, surface casing, conductor housing (LPWH) and
high-pressure wellhead housing (HPWHH).

Every result shown in the video was computed for it with the models in `compute/`.

## Contents

| Path | What |
|---|---|
| `output/` | Subtitles (`.srt`); the rendered `.mp4` (soft English subtitles) is written here by `assemble.py` but is git-ignored because it exceeds GitHub's file size limit |
| `compute/` | Python FE models that produce all the data in `video/data/` |
| `video/narration/` | Narration script (`script.json`) and TTS generator |
| `video/src/` | Animation engine (Three.js + Canvas 2D + KaTeX) and the 14 scenes |
| `video/render.mjs` | Deterministic frame renderer (headless Chromium → ffmpeg) |
| `video/audio.py` | Soundtrack: narration, procedural score, SFX, ducking; subtitles |
| `video/assemble.py` | Cross-fades the scene chunks and muxes audio + subtitles |
| `video/web/`, `video/tools_webparts.py` | Web player page; splits the final video into < 15 MB parts at narration pauses (`web/cuts.json`) for hosting as a claude.ai artifact |

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
python3 tools_webparts.py            # optional: player page + parts in build/web
```

Preview a single frame: `node render.mjs --scene s06_axisym --stills 12.5,30`.

# Every Wave Counts — fatigue design of a subsea wellhead with DNV-RP-C203

A second narrated explainer (24 min, 1080p30) built from the same models and engine: the DNV-RP-C203
fatigue method worked through on the wellhead above, for viewers with a basic understanding of
fatigue. Story: a cold open (cycles, a crack at a weld toe, welds nobody can inspect), a refresher
(stress range, S-N testing, mean − 2 SD design curves, the power law), a map of where each step lives
in the standard, then the six links of the C203 chain, each computed for this well. Every formula is
shown term by term (the term being explained is boxed in the formula, with a legend row for it) and
followed by a worked example with this well's numbers:

| Step | What the video shows | Computed in |
|---|---|---|
| 1 Sea states | Example Hs–Tp scatter diagram, JONSWAP spectra, an assumed riser transfer function to the flex-joint force (stands in for a global riser analysis, DNV-RP-E104 for wellheads) | `compute/fatigue.py` |
| 2 Stress | Load-to-moment transfer curves at three hot spots from the global model; nominal stress σ = M/W with W of a tube, worked for the conductor; hot-spot stress (structural stress: membrane + bending, the notch is in the S-N curve); 0.5t/1.5t linear extrapolation, σhs = 1.5σ0.5t − 0.5σ1.5t, and the quadratic eq. (4.9) for the thick conductor wall ([4.3.4.2]); misalignment SCF of the girth weld, eq. (3.9) with δ0 = 0.05t (Table 3-1) and the mid-wall correction of App. B.5, eq. (B.53) | `compute/fatigue.py`, `compute/hotspot.py` |
| 3 Cycles | Rainflow counting (ASTM E1049 three-point method, half cycles at the start point) animated on the real stress history; ranges, not means, for as-welded joints; the f_m reductions of [2.5] for base material and post-weld heat-treated joints | `compute/fatigue.py` |
| 4 S-N curve | C203 (2024) curve family B1–W3, detail classification (girth weld D in the shop, E on site, F3 at a one-sided root, Table A-9, [2.4.13]), air / seawater with CP / free corrosion; eq. (2.8), (2.9) with s_logN = 0.2, the two branches of the D curve and the bend at 83.4 MPa, no fatigue limit under variable amplitude, thickness effect eq. (2.10); worked example for 60 and 100 MPa | `compute/fatigue.py` |
| 5 Damage | Palmgren–Miner, eq. (2.3) with η = 1/DFF, two-slope split and two worked blocks; long-term damage map; Weibull closed form, eq. (5.1)–(5.4) term by term, against the full rainflow sum | `compute/fatigue.py` |
| 6 Check | Design fatigue factor and usage factor, lives of the three hot spots, sensitivities, and the options C203 gives to buy back margin (detail class, tolerances, grinding flush to C1 with δ0 = 0, Table 7-1 toe improvement and its limits, [2.1.2]) | `compute/fatigue.py` |

Key numbers: hot-spot SCF 1.60 at the HP housing weld (outside, linear) and 1.24 at the conductor
housing weld (inside, quadratic eq. 4.9; linear gives 1.15; the outside sees only 0.84), assuming both
housing welds are made from both sides; a one-sided conductor housing weld would put an F3 root on the
inside with 47 days allowed. Girth weld: eq. (3.9) gives 1.27 for 6 mm hi-lo (L = 40 mm weld width),
1.25 × the outer-fibre stress after eq. (B.53). About 12,100 cycles a day; seas with Hs 3–6 m give 73 %
of the girth-weld damage in 23 % of the time. Governing detail: the conductor girth weld 3 m below the
mudline (class D, shop-welded), 1,276 days of life, 128 days allowed with DFF 10 against a planned 120
days (utilisation 94 %); Weibull closed form +9 % (one slope: −28 %); +10 % stress costs 30 % of the
life; 8 mm misalignment (90 days) or a site weld, class E (82 days), fails the check; 4 mm tolerance
gives 192 days, grinding flush (C1, δ0 = 0) about 450 days. S-N data, δ0 and the classifications follow
DNV-RP-C203, edition October 2024 (amended October 2025).
The riser loads are illustrative, so the numbers demonstrate the method, not a specific well.

Rebuilding (after the computations above): `cd compute && python3 hotspot.py && python3 fatigue.py`, then

```bash
cd video
python3 narration/tts.py --video fatigue
N=3 VIDEO=fatigue ./render_all.sh      # build/fatigue/chunks/*.mp4 (resumable)
python3 audio.py --video fatigue && python3 assemble.py --video fatigue
python3 tools_webparts.py --video fatigue   # optional: player page + parts in build/fatigue/web
```

Preview a frame: `node render.mjs --video fatigue --scene f07_hotspot --stills 20,40`.
`video/projects.py` holds the per-video settings (script, timing, build folder, chapters).
