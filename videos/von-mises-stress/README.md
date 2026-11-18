# The Physics of Failure – Understanding von Mises Stress

A ~15-minute engineering documentary built from the brief in [`TOPIC.md`](TOPIC.md).
Everything in it is generated from code in this folder: animation (Manim), narration
(Kokoro TTS), the finite element analyses (gmsh + scikit-fem) and their renders (PyVista).

## Structure

| Section | Scenes | Content |
|---|---|---|
| 1 Opening | `S01_Opening` | real FE model under N, M, T; stress field builds; Cauchy tensor; why component checks fail; title |
| 2 Physical origin | `S02a_Micro`, `S02b_Decomposition` | polycrystal, slip, Frenkel estimate, edge-dislocation glide (Volterra field), Schmid's law, hydrostatic = no shear; σ = σ_m I + s; volume vs shape |
| 3 Derivation | `S03a_Derivation`, `S03b_RMSShear`, `S03c_Cartesian` | principal stresses & invariants → energy split U_vol + U_dist → J₂ → calibration in tension → σ_vm; RMS shear over all planes; Cartesian form; scope & limits |
| 4 Loading cases | `S04a_CasesAB`, `S04b_CasesCD`, `S04c_CaseE` | uniaxial, pure shear (√3 explained via principal spread), equal biaxial, hydrostatic (subsea example), tension + torsion ellipse |
| 5 Yield surface | `S05_YieldSurface` | Haigh–Westergaard space, hydrostatic axis, π-plane, cylinder R = √(2/3) σ_Y, plane-stress slice, proportional load path |
| 6 Tresca | `S06_Tresca` | hexagonal prism, π-plane comparison, 0.500 vs 0.577 σ_Y, smoothness & radial return |
| 7 FEA | `S07a`–`S07d` | 3D model, quadratic tets, Gauss-point stresses, averaging order, six raw components → von Mises, stress trajectories, convergence vs sharp-corner singularity, SCL linearization, constitutive caveat |
| 8 Design | `S08_Design` | σ₁,σ₂,σ₃ = 240, 80, −40 MPa, S355 → σ_vm = 243.3 MPa, FoS = 1.46 (Tresca 1.27, max-principal 1.48), vocabulary, other limit states |
| 9 Conclusion | `S09_Conclusion` | hydrostatic vs deviatoric, final equation and statement |

## Finite element analyses (real, not mocked)

* `tools/fea3d.py` — pipe OD 273.1 × 20 mm → hub OD 340 mm, R8 shoulder fillet, S355 (E = 210 GPa, ν = 0.3).
  Loads N = 1.0 MN, M = 60 kNm, T = 80 kNm as self-equilibrated beam tractions; curved 10-node tetrahedra;
  AMG-preconditioned CG. Far-field σ_vm = 146.8 MPa (beam theory: 146.7 MPa). Fillet-root peak
  (Gauss points) 270 → 284 → 289 MPa for h = 3.5 → 2.0 → 1.3 mm; nodal (averaged components) ≈ 300 MPa.
* `tools/fea_axi.py` — axisymmetric model of the same transition under axial load: refinement study
  h = 4 → 0.03 mm. R8 fillet: Kt → 2.19 (converged). Sharp corner: Kt 2.3 → 14.1 and still rising
  (r^−0.46 singularity). SCL linearization at the hot spot: P_L = 77, P_L + P_b = 130, total 216 MPa.
* `tools/render_fea.py` — offscreen PyVista renders of the 3D results (frame sequences + stills).

Numbers quoted in the narration come from `assets/fea/summary.json`.

## Build

Requirements: Python 3.11+, `manim`, `scikit-fem`, `gmsh`, `pyamg`, `pyvista`, `kokoro-onnx`, `soundfile`,
`matplotlib`, `scipy`; LaTeX (`texlive-latex-extra`, `dvisvgm`); `ffmpeg`; `xvfb` for offscreen rendering.
The Kokoro model files (`kokoro-v1.0.onnx`, `voices-v1.0.bin`) go in `build/models/`
(Hugging Face: `fastrtc/kokoro-onnx`).

```bash
python tools/tts.py --speed 1.12            # narration -> build/audio/*.wav + durations.json
HF=1.3 python tools/fea3d.py                # 3D FE analysis   (~10 min)
python tools/fea_axi.py                     # axisymmetric study (~15 s)
python tools/make_assets.py                 # polycrystal illustration
xvfb-run -a python tools/render_fea.py      # FE renders (frame sequences)
xvfb-run -a python tools/render_fea.py --shots components
tools/render_scenes.sh h 3 S01_Opening S02a_Micro ...   # all 17 scenes at 1080p30
python tools/assemble.py                    # -> build/von_mises_stress.mp4 (+ .srt)
```

Scene timing is driven by the measured narration durations (`with self.say("id")` blocks in
`scenes/common.py`); the assembler lays each voice clip at the time logged by the scene.
The narration voice is synthetic (Kokoro `af_heart`); the score is procedural.
