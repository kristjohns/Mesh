// Step 2, continued: the conductor girth weld. Misalignment SCF of C203 eq. (3.9), term by term, with
// delta0 from Table 3-1 and the mid-wall correction of App. B.5, eq. (B.53).
import { makeBackdrop } from '../../engine/env.js';
import { keyLine } from '../common.js';
import { chainBar, heading, formulaWalk, texSteps, refChip } from './fcommon.js';
import { PAL, seg, env, ease, clamp, lerp, rgba } from '../../engine/util.js';

export default async function misalign(ctx) {
  const { d2, cue, at, renderer, data, tex } = ctx;
  const F = data.fatigue;
  const G = F.girth;
  const back = makeBackdrop();
  const a1 = cue('a1'), a2 = cue('a2'), a3 = cue('a3'), a4 = cue('a4'), a5 = cue('a5'), a6 = cue('a6'), a7 = cue('a7'), a8 = cue('a8');
  const H = (k, s) => `\\htmlClass{fw-f07bE-${k}}{${s}}`;
  const H2 = (k, s) => `\\htmlClass{fw-f07bB-${k}}{${s}}`;
  const tmm = G.t * 1e3, d0 = 0.05 * tmm, ea = Math.exp(-G.alpha);
  const tEnd = at('a8', "That's one point two five") + 2.6;

  return {
    render(t) {
      back.render(renderer);
      const A = env(t, 0.3, ctx.duration, 0.6, 0.5);
      heading(d2, 'C · conductor girth weld', 110, 150, A, { sub: 'stress concentration from misalignment, C203 [3.3.7]' });
      // ------------------------------------------------------------ sketch: two pipe walls with hi-lo
      const cx = 480, cy = 430, T = 120, dm = 34;
      d2.panel(80, 210, 820, 490, { alpha: A });
      const wall = (x0, x1, y0) => d2.poly([[x0, y0 - T / 2], [x1, y0 - T / 2], [x1, y0 + T / 2], [x0, y0 + T / 2]], { fill: 'rgba(130,160,185,0.4)', stroke: '#9fb3c4', width: 2, alpha: A });
      wall(cx - 360, cx - 30, cy);
      wall(cx + 30, cx + 360, cy + dm);
      d2.poly([[cx - 60, cy - T / 2], [cx - 20, cy - T / 2 - 18], [cx + 30, cy - T / 2 - 10 + dm * 0.5], [cx + 60, cy - T / 2 + dm], [cx + 60, cy + T / 2 + dm], [cx + 20, cy + T / 2 + dm + 14], [cx - 30, cy + T / 2 + 10], [cx - 60, cy + T / 2]], { fill: 'rgba(176,152,108,0.6)', stroke: '#d1bd92', width: 2, alpha: A });
      d2.text('outside', cx - 340, cy - T / 2 - 16, { size: 18, color: PAL.ink3, alpha: A });
      d2.text('inside', cx - 340, cy + T / 2 + 30, { size: 18, color: PAL.ink3, alpha: A });
      d2.line(cx - 360, cy, cx - 30, cy, { color: PAL.ink3, width: 1.5, dash: [6, 6], alpha: A });
      d2.line(cx + 30, cy + dm, cx + 360, cy + dm, { color: PAL.ink3, width: 1.5, dash: [6, 6], alpha: A });
      const ph = 0.5 + 0.5 * Math.sin(t * 2.2);
      for (const s of [-1, 1]) d2.arrow(cx + s * 380, cy + (s > 0 ? dm : 0), cx + s * (405 + 25 * ph), cy + (s > 0 ? dm : 0), { color: PAL.cyan, width: 4, head: 14, alpha: A });
      // a2: the force jogs sideways and bends the wall
      const jq = seg(t, at('a2', 'jog sideways') - 0.4, 1.4, ease.inOutSine);
      if (jq > 0) {
        d2.path([[cx - 360, cy], [cx - 60, cy], [cx + 60, cy + dm], [cx + 360, cy + dm]], { color: PAL.red, width: 4, alpha: A * 0.9, progress: jq, glow: PAL.red });
        const dq = seg(t, at('a2', 'delta m') - 0.3, 0.6);
        d2.dim(cx + 250, cy - T / 2, cx + 250, cy - T / 2 + dm, '', { color: PAL.amber, alpha: A * dq });
        d2.text(`δm = ${Math.round(G.delta_m * 1e3)} mm`, cx + 268, cy - T / 2 + dm / 2 + 8, { size: 24, weight: 800, color: PAL.amber, alpha: A * dq });
        const bq = seg(t, at('a2', 'bends the wall') - 0.3, 0.8);
        d2.momentArrow(cx - 110, cy, 54, -Math.PI * 0.9, -Math.PI * 0.1, { color: PAL.red, width: 3, alpha: A * bq, progress: bq });
        d2.momentArrow(cx + 110, cy + dm, 54, Math.PI * 0.1, Math.PI * 0.9, { color: PAL.red, width: 3, alpha: A * bq, progress: bq });
        d2.text('local bending at the toe', cx, cy + T / 2 + dm + 70, { size: 22, weight: 700, color: PAL.red, align: 'center', alpha: A * bq });
      }
      d2.dim(cx - 300, cy - T / 2, cx - 300, cy + T / 2, '', { color: PAL.ink2, alpha: A });
      d2.text(`t = ${tmm.toFixed(1)} mm`, cx - 290, cy + 8, { size: 22, weight: 700, color: PAL.ink2, alpha: A });
      const lq = seg(t, at('a6', 'width of the weld') - 0.3, 0.6) * (1 - seg(t, a8 - 0.4, 0.6));
      if (lq > 0) {
        d2.dim(cx - 60, cy - T / 2 - 44, cx + 60, cy - T / 2 - 44, '', { color: PAL.green, alpha: A * lq });
        d2.text(`L = ${Math.round(G.L * 1e3)} mm`, cx, cy - T / 2 - 58, { size: 22, weight: 800, color: PAL.green, align: 'center', alpha: A * lq });
      }
      // ------------------------------------------------------------ lower left: why the 3, delta0, mid-wall stress
      const dA = A * env(t, at('a4', 'An eccentricity') - 0.4, a5 - 0.2, 0.6, 0.5);
      if (dA > 0) {
        d2.panel(80, 730, 820, 280, { alpha: dA, accent: PAL.orange });
        d2.text('why 3 e / t', 110, 772, { size: 22, weight: 750, color: PAL.orange, alpha: dA });
        texSteps(ctx, t, 'f07bD', [
          { tex: 'M = \\sigma_m\\, t\\, e', t: at('a4', 'creates a bending moment'), size: 30, dy: 0 },
          { tex: 'M_{side} = M/2', t: at('a4', 'shares it'), size: 30, dy: 64 },
          { tex: '\\sigma_b = \\dfrac{M/2}{t^2/6} = \\dfrac{3\\,e}{t}\\,\\sigma_m', t: at('a4', 'becomes three e'), size: 32, dy: 128, col: PAL.orange },
        ], 120, 800, { alpha: dA });
        d2.text('per unit length of weld', 520, 830, { size: 18, color: PAL.ink3, alpha: dA * seg(t, at('a4', 'creates a bending moment'), 0.6) });
        d2.text('the pipe on each side', 520, 894, { size: 18, color: PAL.ink3, alpha: dA * seg(t, at('a4', 'shares it'), 0.6) });
        d2.text('takes half', 520, 918, { size: 18, color: PAL.ink3, alpha: dA * seg(t, at('a4', 'shares it'), 0.6) });
      }
      const zA = A * env(t, a5 - 0.2, a8 - 0.2, 0.6, 0.5);
      if (zA > 0) {
        d2.panel(80, 730, 820, 280, { alpha: zA, accent: PAL.violet });
        refChip(d2, 'C203 Table 3-1', 110, 772, zA);
        d2.text('δ0: misalignment already in the S-N test data', 110, 830, { size: 23, weight: 700, color: PAL.violet, alpha: zA });
        d2.text(`as welded, tubular girth welds: δ0 = 0.05 t = ${d0.toFixed(1)} mm`, 110, 880, { size: 22, alpha: zA * seg(t, at('a5', 'five percent') - 0.3, 0.6) });
        d2.text('ground flush: δ0 = 0', 110, 920, { size: 22, alpha: zA * seg(t, at('a5', 'zero for') - 0.3, 0.6) });
        d2.text('(girth welds in pipelines and risers: δ0 = 0)', 110, 960, { size: 18, color: PAL.ink3, alpha: zA * seg(t, at('a5', 'zero for') + 0.4, 0.6) });
      }
      const mA = A * seg(t, a8 - 0.2, 0.6);
      if (mA > 0) {
        d2.panel(80, 730, 820, 280, { alpha: mA, accent: PAL.cyan });
        refChip(d2, 'C203 App. B.5', 110, 772, mA);
        // wall section with the global bending gradient
        const x0 = 110, x1 = 170, yT = 812, yB = 990;
        d2.poly([[x0, yT], [x1, yT], [x1, yB], [x0, yB]], { fill: 'rgba(130,160,185,0.35)', stroke: '#9fb3c4', width: 2, alpha: mA });
        d2.poly([[x1 + 20, yT], [x1 + 20 + 110, yT], [x1 + 20 + 110 * (G.D - 2 * G.t) / G.D, yB], [x1 + 20, yB]], { fill: rgba(PAL.cyan, 0.22), stroke: PAL.cyan, width: 2, alpha: mA });
        d2.text('σ_go', x1 + 140, yT + 8, { size: 20, weight: 800, color: PAL.cyan, alpha: mA });
        const ym = (yT + yB) / 2, xm = x1 + 20 + 110 * (G.D - G.t) / G.D;
        d2.line(x1 + 20, ym, xm, ym, { color: PAL.amber, width: 3, alpha: mA * seg(t, at('a8', 'mid-wall') - 0.3, 0.6) });
        d2.text('σ_gm', xm + 10, ym + 8, { size: 20, weight: 800, color: PAL.amber, alpha: mA * seg(t, at('a8', 'mid-wall') - 0.3, 0.6) });
        texSteps(ctx, t, 'f07bM', [
          { tex: `\\sigma_{gm} = \\sigma_{go}\\,\\dfrac{D - t}{D} = ${G.gm_ratio.toFixed(3)}\\,\\sigma_{go}`, t: at('a8', 'four percent') - 0.3, size: 28, dy: 0 },
          { tex: `\\sigma_{out} = (${G.scf39.toFixed(2)} - 1)\\cdot ${G.gm_ratio.toFixed(3)}\\,\\sigma_{go} + \\sigma_{go}`, t: at('a8', 'plus S C F minus one') - 0.2, size: 27, dy: 80 },
          { tex: `= ${G.scf.toFixed(2)}\\,\\sigma_{go}`, t: at('a8', "That's one point two five") - 0.4, size: 34, dy: 128, col: PAL.amber, dx: 40 },
        ], 400, 806, { alpha: mA });
      }
      // ------------------------------------------------------------ right: eq. (3.9) term by term
      const fA = A * env(t, a3 - 0.4, a8 - 0.1, 0.6, 0.5);
      d2.panel(940, 210, 900, 800, { alpha: A * seg(t, a1 + 0.5, 0.6) });
      if (A * seg(t, a1 + 0.5, 0.6) > 0 && t < a3) {
        const q = A * seg(t, a1 + 0.5, 0.6) * (1 - seg(t, a3 - 0.6, 0.5));
        d2.text('a standard detail:', 990, 300, { size: 28, weight: 750, alpha: q });
        d2.text('nominal stress × misalignment SCF', 990, 344, { size: 26, color: PAL.ink2, alpha: q });
        d2.text('no finite element model needed', 990, 388, { size: 26, color: PAL.ink2, alpha: q });
      }
      if (fA > 0) {
        refChip(d2, 'C203 eq. (3.9)', 970, 246, fA);
        const LG = { x: 990, y: 410, w: 820, gap: 72, symW: 230, size: 22, symSize: 28, alpha: 1 - seg(t, a7 - 0.4, 0.6) };
        formulaWalk(ctx, t, {
          id: 'f07bE', x: 990, y: 278, size: 54, alpha: fA, tOff: a7 - 0.3,
          latex: `SCF = ${H('one', '1')} + ${H('frac', `\\dfrac{3\\,(${H('dm', '\\delta_m')} - ${H('d0', '\\delta_0')})}{${H('t', 't')}}`)}\\; ${H('exp', 'e^{-\\alpha}')}`,
          rows: [
            { k: 'dm', sym: '\\delta_m', text: 'misalignment: hi-lo between the pipe ends', t: at('a3', 'three times delta m'), col: PAL.amber },
            { k: 't', sym: 't', text: 'wall thickness', t: at('a3', 'wall thickness'), col: PAL.cyan },
            { k: 'exp', sym: 'e^{-\\alpha}', text: 'spreads the bending over the weld width', t: at('a3', 'e to the minus'), col: PAL.green },
            { k: 'one', sym: '1', text: 'the stress without misalignment', t: at('a4', 'The one is'), col: PAL.ink },
            { k: 'frac', sym: '\\tfrac{3(\\delta_m-\\delta_0)}{t}', text: 'extra bending from the eccentricity', t: at('a4', 'The second term'), col: PAL.orange },
            { k: 'd0', sym: '\\delta_0', text: 'misalignment already in the S-N data', t: at('a5', 'Delta nought'), col: PAL.violet },
            { k: 'exp', sym: '\\alpha = \\tfrac{0.91\\,L}{\\sqrt{D\\,t}}', text: 'L: width of the weld at the surface', t: at('a6', 'Alpha brings'), col: PAL.green },
          ],
          legend: LG,
        });
        const wA = fA * seg(t, a7 - 0.3, 0.6);
        if (wA > 0) {
          d2.text('our girth weld', 990, 440, { size: 24, weight: 750, color: PAL.amber, alpha: wA });
          texSteps(ctx, t, 'f07bW', [
            { tex: `\\delta_m = 6\\ \\mathrm{mm},\\quad t = ${tmm.toFixed(1)}\\ \\mathrm{mm},\\quad L = ${Math.round(G.L * 1e3)}\\ \\mathrm{mm},\\quad D = ${(G.D * 1e3).toFixed(1)}\\ \\mathrm{mm}`, t: at('a7', 'six millimetres'), size: 28, dy: 0 },
            { tex: `\\alpha = \\dfrac{0.91 \\cdot ${Math.round(G.L * 1e3)}}{\\sqrt{${(G.D * 1e3).toFixed(1)} \\cdot ${tmm.toFixed(1)}}} = ${G.alpha.toFixed(3)}, \\qquad e^{-\\alpha} = ${ea.toFixed(2)}`, t: at('a7', 'Alpha is'), size: 30, dy: 70 },
            { tex: `\\delta_0 = 0.05 \\cdot ${tmm.toFixed(1)} = ${d0.toFixed(1)}\\ \\mathrm{mm}`, t: at('a7', 'Alpha is') + 1.2, size: 30, dy: 170 },
            { tex: `SCF = 1 + \\dfrac{3\\,(6 - ${d0.toFixed(1)})}{${tmm.toFixed(1)}} \\cdot ${ea.toFixed(2)} = ${G.scf39.toFixed(2)}`, t: at('a7', 'the S C F is'), size: 40, dy: 250, col: PAL.amber },
          ], 990, 480, { alpha: wA });
        }
      }
      // a8: eq. (B.53)
      const bA = A * env(t, a8 - 0.2, tEnd, 0.6, 0.5);
      if (bA > 0) {
        refChip(d2, 'C203 eq. (B.53)', 970, 246, bA);
        formulaWalk(ctx, t, {
          id: 'f07bB', x: 990, y: 290, size: 50, alpha: bA, tOff: tEnd,
          latex: `${H2('o', '\\sigma_{outside}')} = (${H2('k', 'SCF - 1')})\\, ${H2('m', '\\sigma_{gm}')} + ${H2('g', '\\sigma_{go}')}`,
          rows: [
            { k: 'm', sym: '\\sigma_{gm}', text: 'global bending stress at mid-wall', sub: 'drives the local bending from misalignment', t: at('a8', 'mid-wall'), col: PAL.amber },
            { k: 'g', sym: '\\sigma_{go}', text: 'global bending stress at the outer fibre', sub: 'the nominal stress, M / W', t: at('a8', 'outer-fibre stress'), col: PAL.cyan },
            { k: 'k', sym: 'SCF', text: 'from eq. (3.9)', sub: `${G.scf39.toFixed(2)}`, t: at('a8', 'plus S C F minus one'), col: PAL.orange },
          ],
          legend: { x: 990, y: 430, w: 820, gap: 92, symW: 160, size: 24, symSize: 30 },
        });
      }
      // summary of the three SCFs
      const sA = A * seg(t, tEnd - 0.3, 0.6);
      if (sA > 0) {
        d2.panel(940, 210, 900, 800, { alpha: sA, fill: 'rgba(12,28,46,0.98)' });
        d2.text('Stress concentration factors', 990, 275, { size: 32, weight: 750, alpha: sA });
        d2.text('applied to the outer-fibre nominal stress', 990, 312, { size: 21, color: PAL.ink2, alpha: sA });
        const rows = [
          ['A', 'HP housing weld', 'FE hot spot, linear, outside', F.scf.hp, PAL.violet],
          ['B', 'conductor housing weld', 'FE hot spot, quadratic, inside', F.scf.lp, PAL.cyan],
          ['C', 'conductor girth weld', 'eq. (3.9) with δ0 = 0.05t, eq. (B.53)', F.scf.cg, PAL.amber],
        ];
        rows.forEach(([L, n, m, v, col], k) => {
          const q = seg(t, tEnd + 0.2 + k * 0.35, 0.6);
          const y = 420 + k * 150;
          d2.circle(1002, y - 8, 22, { fill: rgba(col, 0.25), stroke: col, width: 2.5, alpha: sA * q });
          d2.text(L, 1002, y, { size: 22, weight: 800, color: col, align: 'center', alpha: sA * q });
          d2.text(n, 1046, y - 6, { size: 28, weight: 700, alpha: sA * q });
          d2.text(m, 1046, y + 28, { size: 21, color: PAL.ink2, alpha: sA * q });
          d2.text(v.toFixed(2), 1790, y + 10, { size: 48, weight: 800, color: col, align: 'right', alpha: sA * q });
        });
      }
      keyLine(d2, t, at('a7', 'the S C F is') + 1.5, a8 - 0.3, 'Six millimetres of hi-lo: 27 % more stress at the toe', { accent: PAL.amber, size: 28, y: 1046 });
      chainBar(d2, 2, { alpha: A });
    },
  };
}
