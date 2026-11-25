# Mesh — Low-cycle vs high-cycle fatigue, explained with FEA

This repository contains a narrated, animated explainer video (≈ 20 min) on
**low-cycle fatigue (LCF) vs high-cycle fatigue (HCF)**, the methods used to predict
fatigue life in each regime, and **accumulated plastic strain, shakedown and
ratcheting** — together with all finite element models, the solver and the
animation code used to make it.

| Folder | Content |
|---|---|
| `fatigue_fea/` | Cyclic-plasticity FE solver (Python), models, verification, results summary |
| `video/` | Narration script, TTS, manim scenes, FE frame rendering, assembly |

The rendered video is `video/output/LCF_vs_HCF_fatigue.mp4` (1080p30, H.264/AAC,
soft English subtitles), with the subtitles also in `video/output/LCF_vs_HCF_fatigue.srt`.

## Chapters

1. **How fatigue works:** slip bands, extrusions/intrusions, stage I/II cracks, beach marks, and how a load cycle is described (σmax, σmin, σa, σm, R).
2. **LCF vs HCF:** plasticity, not cycle count, separates them. Covers hysteresis loops, the strain–life curve, the transition life (≈ 3 300 cycles for the S355-type steel), VHCF and fish-eyes, and notch-root strain control.
3. **High-cycle fatigue:**
   - S–N curves (Basquin), the fatigue limit and Marin factors.
   - Haigh diagram (Goodman, Gerber, Soderberg, SWT).
   - Kt from FE (3.25 gross / 2.44 net) and Kf with Peterson notch sensitivity.
   - Welded joints: nominal stress, structural hot-spot (DNV-RP-C203 0.5t/1.5t extrapolation) and effective notch stress (r = 1 mm, FAT 225).
   - Rainflow counting with Palmgren–Miner, and multiaxial criteria.
4. **Low-cycle fatigue:**
   - Cyclic hardening and softening, the cyclic stress–strain curve and Masing behaviour.
   - Coffin–Manson–Basquin, with Morrow and SWT mean-stress corrections.
   - Notch strain by Neuber, Glinka and elastic-plastic FE.
   - Energy and critical-plane methods, plus the ASME VIII-2 and DNV-RP-C203 approaches.
5. **FE study of a plate with a hole:** elastic HCF, elastic shakedown, alternating plasticity (LCF) and ratcheting.
6. **Accumulated plastic strain:**
   - PEEQ definition, and why PEEQ alone is ambiguous.
   - Melan's theorem and the computed Bree diagram.
   - Thermo-mechanical ratcheting of the holed plate and the elastic-core criterion.
   - Hardening-model effects on material ratcheting.
   - Code acceptance criteria (ASME VIII-2, EN 13445-3, EN 1993-1-6 LS2, ASME local strain limit) and damage summation.
7. **Workflow:** an assessment flowchart from linear-elastic screening to elastic-plastic cyclic analysis.

## Key results (from `fatigue_fea/results/summary.json`)

Plate 80 × 200 mm with a Ø20 hole, plane stress, 1152 Q9 elements, S355-type steel with Chaboche cyclic plasticity:

| Case | Remote stress | Notch-root response (stabilised) | PEEQ growth / cycle | Life (strain–life) |
|---|---|---|---|---|
| HCF | ±70 MPa | elastic, σa = 227 MPa | 0 | ≈ 5.6 × 10⁶ |
| Elastic shakedown | 0 → 140 MPa | yields once, then elastic; local σm = +115 MPa | 0 | 5.6 × 10⁶ (no σm) → 1.6 × 10⁶ (Morrow) → 0.63 × 10⁶ (SWT) |
| Alternating plasticity | ±180 MPa | εa = 0.383 % (Glinka 0.321 %, Neuber 0.431 %) | 0.82 % | ≈ 4 100 |
| Ratcheting (mechanical) | 0 → 285 MPa | loops walk, mean strain ≈ 3 % and growing | 0.38 % | ductility exhaustion governs |

Thermo-mechanical cases have constant tension plus a cyclic temperature field and use an elastic–perfectly plastic material:

- **X = 0.25, Y = 2.5:** alternating plasticity. The plate length stops changing, and an elastic core remains in the ligament.
- **X = 0.50, Y = 2.5:** structural ratcheting at +22.5 µm per cycle. No elastic core remains.

The Bree diagram was computed with a through-wall fibre model over 6 561 load points × 24 cycles. It matches Bree's (1967) analytical boundaries at 6 560 of 6 561 points; the one miss lies exactly on a boundary.

For the welded T-joint (FAT 80 nominal, Δσ_nom = 100 MPa in bending):

- **Hot-spot stress:** 99 MPa, giving ≈ 1.5 × 10⁶ cycles on DNV curve D.
- **Effective notch stress:** 271 MPa, giving ≈ 1.1 × 10⁶ cycles on FAT 225.

## Verification of the solver

- **Constitutive model (single material point):**
  - The stabilised Chaboche loops match the closed-form solution σa = σ0 + Σ Cᵢ/γᵢ tanh(γᵢ εpa) within 0.25 MPa.
  - The consistent tangent matches finite differences to about 3 × 10⁻¹¹.
  - Linear kinematic hardening gives no uniaxial ratcheting.
- **Elastic Kt:** Kt,net = 2.437 against Peterson's 2.43 for d/W = 0.25 (mesh-converged).
- **Cyclic EPP plate vs CalculiX 2.21** on the same mesh (Q9 vs CPS8), within about 2 % on notch strain, PEEQ and displacement (`fatigue_fea/verification/compare_calculix.py`).

## Reproducing

```bash
pip install numpy scipy matplotlib meshio manim kokoro-onnx soundfile onnxruntime
apt-get install calculix-ccx gmsh texlive-latex-extra texlive-fonts-extra dvisvgm   # ccx/gmsh/LaTeX

cd fatigue_fea
python verification/test_material.py           # material-point checks
python verification/compare_calculix.py        # cross-check vs CalculiX
for c in hcf shake lcf ratchet_m tm_shake tm_altpl tm_ratchet; do python models/plate_with_hole.py $c; done
python models/bree_map.py; python models/weld_t_joint.py; python models/uniaxial_studies.py
python models/summary.py

cd ../video
python tts.py <dir with kokoro-v1.0.onnx and voices-v1.0.bin>   # narration (Kokoro TTS)
python make_frames.py; python make_bree_frames.py              # FE image sequences
./build_all.sh                                                  # manim scenes, 1080p30
python assemble.py                                              # mux, concatenate, subtitles
```

Large intermediate results (`*.npz`, audio, frames, renders) are not committed. The scripts above regenerate them.

## Notes and limitations

- The strain–life and cyclic parameters are representative of published S355 data and are **illustrative**. Use test data for the actual material in design.
- Code clauses are summarised for orientation only. Always apply the edition of ASME VIII-2, EN 13445-3, EN 1993-1-6 or DNV-RP-C203 that governs your project, including its national annexes.
- 2-D plane-stress and plane-strain models are used. Real components may need 3-D models, multiaxial and non-proportional fatigue criteria, residual stresses, and environment and temperature effects.
