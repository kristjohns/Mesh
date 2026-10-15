// Step 5, continued: the Weibull closed form of C203 section 5.4, eq. (5.1) to (5.4) term by term,
// fitted to the long-term stress ranges at the girth weld and compared with the full rainflow sum.
import { makeBackdrop } from '../../engine/env.js';
import { Plot } from '../../engine/draw2d.js';
import { keyLine } from '../common.js';
import { chainBar, heading, formulaWalk, texSteps, refChip, fmtInt } from './fcommon.js';
import { PAL, seg, env, ease, clamp, lerp, rgba } from '../../engine/util.js';

export default async function weibull(ctx) {
  const { d2, cue, at, renderer, data, tex } = ctx;
  const F = data.fatigue;
  const DG = F.damage.cg, WB = F.worked.weibull, WS = F.worked.sn;
  const back = makeBackdrop();
  const w1 = cue('wb1'), w2 = cue('wb2'), w3 = cue('wb3'), w4 = cue('wb4'), w5 = cue('wb5'), w6 = cue('wb6');
  const h = WB.h, q = WB.q;
  const n0x = 1000, ds0x = q * Math.pow(Math.log(n0x), 1 / h);
  const SUPD = '⁰¹²³⁴⁵⁶⁷⁸';
  const H = (id, k, s) => `\\htmlClass{fw-${id}-${k}}{${s}}`;
  const R = { x: 1040, w: 770 };

  return {
    render(t) {
      back.render(renderer);
      const A = env(t, 0.3, ctx.duration, 0.6, 0.5);
      heading(d2, 'The Weibull shortcut', 110, 150, A, { sub: 'DNV-RP-C203 section 5.4, term by term' });
      // ------------------------------------------------------------ left: long-term distribution and the fit
      const E = DG.exceed;
      d2.panel(80, 210, 880, 800, { alpha: A });
      const WP = new Plot(d2, { x: 200, y: 270, w: 700, h: 600, xr: [0, 140], yr: [-8, 0] });
      WP.axes({ alpha: A, xticks: [0, 20, 40, 60, 80, 100, 120, 140], yticks: [0, -2, -4, -6, -8], fs: 18, fmty: (v) => (v === 0 ? '1' : `10⁻${SUPD[-v]}`),
        xlabel: 'stress range Δσ [MPa]', ylabel: 'probability of exceedance Q', ylabelOff: 66 });
      d2.text('long-term stress ranges at the girth weld (rainflow, all sea states)', 110, 252, { size: 19, weight: 700, color: PAL.ink2, alpha: A });
      const pq = seg(t, w1 + 0.6, 1.6);
      const pts = E.Q.map((Q, k) => [E.s[k], Math.log10(Q)]).filter((p) => p[0] > 0.5 && p[0] <= 140);
      WP.points(pts, { color: PAL.orange, r: 5, progress: pq, alpha: A });
      const fq = seg(t, at('wb2', 'Fitted to our') - 0.3, 1.2);
      const wpts = [];
      for (let i = 0; i <= 100; i++) { const s = 140 * i / 100; wpts.push([s, Math.log10(Math.exp(-Math.pow(s / q, h)))]); }
      WP.clipBegin(); WP.curve(wpts, { color: PAL.cyan, width: 3.5, progress: fq, alpha: A }); WP.clipEnd();
      d2.text(`Weibull fit: h = ${h.toFixed(2)}, q = ${q.toFixed(1)} MPa`, WP.x + WP.w - 10, WP.y + 34, { size: 21, weight: 750, color: PAL.cyan, align: 'right', alpha: A * fq });
      // eq. (5.2) on the plot: the largest range in n0 cycles
      const lq = A * env(t, at('wb3', 'In n nought') - 0.3, w4 + 1.0, 0.6, 0.6);
      if (lq > 0) {
        const yQ = WP.Y(Math.log10(1 / n0x));
        d2.line(WP.X(0), yQ, WP.X(ds0x), yQ, { color: PAL.violet, width: 2, dash: [8, 6], alpha: lq });
        d2.line(WP.X(ds0x), yQ, WP.X(ds0x), WP.Y(-8), { color: PAL.violet, width: 2, dash: [8, 6], alpha: lq });
        d2.circle(WP.X(ds0x), yQ, 9, { fill: PAL.violet, alpha: lq, glow: PAL.violet });
        d2.text(`Q = 1/n₀, n₀ = ${n0x}`, WP.X(2), yQ - 12, { size: 19, weight: 700, color: PAL.violet, alpha: lq });
        d2.text(`Δσ₀ = ${ds0x.toFixed(0)} MPa`, WP.X(ds0x) - 10, WP.Y(-8) - 14, { size: 19, weight: 700, color: PAL.violet, align: 'right', alpha: lq });
      }
      // ------------------------------------------------------------ right: the equations
      d2.panel(1000, 210, 840, 800, { alpha: A });
      // wb1: why
      const iA = A * env(t, w1 + 0.3, w2 - 0.1, 0.6, 0.5);
      if (iA > 0) {
        d2.text('If the long-term stress ranges', R.x, 300, { size: 28, weight: 750, alpha: iA });
        d2.text('follow a 2-parameter Weibull distribution,', R.x, 340, { size: 28, weight: 750, alpha: iA });
        d2.text('Miner\'s sum has a closed form:', R.x, 400, { size: 26, color: PAL.ink2, alpha: iA * seg(t, at('wb1', 'closed-form') - 0.3, 0.6) });
        d2.text('no cycle counting needed', R.x, 440, { size: 26, color: PAL.ink2, alpha: iA * seg(t, at('wb1', "don't need") - 0.3, 0.6) });
      }
      // wb2: eq. (5.1)
      const aA = A * env(t, w2 - 0.2, w3 - 0.1, 0.6, 0.5);
      if (aA > 0) {
        refChip(d2, 'C203 eq. (5.1)', R.x - 10, 246, aA);
        formulaWalk(ctx, t, {
          id: 'f10bA', x: R.x, y: 290, size: 52, alpha: aA, tOff: w3,
          latex: `${H('f10bA', 'Q', 'Q(\\Delta\\sigma)')} = \\exp\\!\\left[-\\left(\\dfrac{\\Delta\\sigma}{${H('f10bA', 'q', 'q')}}\\right)^{${H('f10bA', 'h', 'h')}}\\right]`,
          rows: [
            { k: 'Q', sym: 'Q', text: 'probability that a range exceeds Δσ', t: at('wb2', 'the probability'), col: PAL.orange },
            { k: 'q', sym: 'q', text: 'scale parameter, MPa', t: at('wb2', 'q is the scale'), col: PAL.cyan },
            { k: 'h', sym: 'h', text: 'shape parameter: how fast the tail drops', t: at('wb2', 'h is the shape'), col: PAL.green },
          ],
          legend: { x: R.x, y: 450, w: R.w, gap: 84, symW: 110, size: 24, symSize: 32 },
        });
        const fz = seg(t, at('wb2', 'Fitted to our') - 0.3, 0.6);
        tex.show('f10bfit', `h = ${h.toFixed(2)}, \\qquad q = ${q.toFixed(1)}\\ \\mathrm{MPa}`, R.x, 760, { size: 38, alpha: aA * fz, color: PAL.cyan });
      }
      // wb3: eq. (5.2)
      const bA = A * env(t, w3 - 0.2, w4 - 0.1, 0.6, 0.5);
      if (bA > 0) {
        refChip(d2, 'C203 eq. (5.2)', R.x - 10, 246, bA);
        formulaWalk(ctx, t, {
          id: 'f10bB', x: R.x, y: 290, size: 52, alpha: bA, tOff: w4,
          latex: `q = \\dfrac{${H('f10bB', 'd', '\\Delta\\sigma_0')}}{(\\ln ${H('f10bB', 'n', 'n_0')})^{1/h}}`,
          rows: [
            { k: 'd', sym: '\\Delta\\sigma_0', text: 'the largest stress range out of n₀ cycles', t: at('wb3', 'the largest range'), col: PAL.violet },
            { k: 'n', sym: 'n_0', text: 'number of cycles in the period considered', t: at('wb3', 'natural log'), col: PAL.amber },
          ],
          legend: { x: R.x, y: 470, w: R.w, gap: 84, symW: 110, size: 24, symSize: 32 },
        });
        const eq = seg(t, at('wb3', 'natural log') + 0.4, 0.6);
        tex.show('f10bB2', `\\Leftrightarrow\\; \\Delta\\sigma_0 = q\\,(\\ln n_0)^{1/h}`, R.x, 670, { size: 38, alpha: bA * eq, color: PAL.violet });
      }
      // wb4: eq. (5.3)
      const cA = A * env(t, w4 - 0.2, w5 - 0.1, 0.6, 0.5);
      if (cA > 0) {
        refChip(d2, 'C203 eq. (5.3), one slope', R.x - 10, 246, cA);
        formulaWalk(ctx, t, {
          id: 'f10bC', x: R.x, y: 290, size: 50, alpha: cA, tOff: w5,
          latex: `D = \\dfrac{${H('f10bC', 'n', '\\nu_0\\, T_d')}}{${H('f10bC', 'a', '\\bar a')}}\\; ${H('f10bC', 'g', 'q^{m}\\, \\Gamma\\!\\left(1 + \\dfrac{m}{h}\\right)')} \\;\\le\\; \\eta`,
          rows: [
            { k: 'n', sym: '\\nu_0 T_d', text: 'total number of cycles', sub: 'ν₀: average zero up-crossing frequency, T_d: time', t: at('wb4', 'Nu nought'), col: PAL.amber },
            { k: 'g', sym: 'q^m\\Gamma(1+\\tfrac{m}{h})', text: 'the mean of Δσᵐ over the Weibull distribution', t: at('wb4', 'q to the m'), col: PAL.cyan },
            { k: 'a', sym: '\\bar a', text: 'S-N intercept, as in eq. (2.8)', t: at('wb4', 'divided by a bar') - 0.4, col: PAL.violet },
          ],
          legend: { x: R.x, y: 450, w: R.w, gap: 92, symW: 230, size: 23, symSize: 28 },
        });
        const mq = seg(t, at('wb4', "Miner's sum") - 0.3, 0.6);
        tex.show('f10bC2', '= \\dfrac{n_{total} \\cdot \\overline{\\Delta\\sigma^{m}}}{\\bar a} \\quad\\text{(Miner, analytically)}', R.x, 760, { size: 34, alpha: cA * mq, color: PAL.amber });
      }
      // wb5: eq. (5.4)
      const dA = A * env(t, w5 - 0.2, w6 - 0.1, 0.6, 0.5);
      if (dA > 0) {
        refChip(d2, 'C203 eq. (5.4), two slopes', R.x - 10, 246, dA);
        const x_ = `\\left(\\tfrac{S_1}{q}\\right)^{h}`;
        formulaWalk(ctx, t, {
          id: 'f10bD', x: R.x, y: 280, size: 36, alpha: dA, tOff: w6,
          latex: `\\begin{aligned} D = \\nu_0 T_d \\Big[ & ${H('f10bD', 'u', `\\dfrac{q^{m_1}}{\\bar a_1}\\,\\Gamma\\!\\left(1 + \\tfrac{m_1}{h};\\, ${x_}\\right)`)} \\\\ + & ${H('f10bD', 'l', `\\dfrac{q^{m_2}}{\\bar a_2}\\,\\gamma\\!\\left(1 + \\tfrac{m_2}{h};\\, ${x_}\\right)`)} \\Big] \\le \\eta \\end{aligned}`,
          rows: [
            { k: null, sym: 'S_1', text: 'stress range at the bend of the S-N curve', t: at('wb5', 'at the bend'), col: PAL.ink },
            { k: 'u', sym: '\\Gamma(\\,;\\,)', text: 'complementary incomplete gamma: ranges above S₁', sub: 'steep branch: m₁, ā₁', t: at('wb5', 'The complementary'), col: PAL.amber },
            { k: 'l', sym: '\\gamma(\\,;\\,)', text: 'incomplete gamma: ranges below S₁', sub: 'shallow branch: m₂, ā₂', t: at('wb5', 'The incomplete gamma'), col: PAL.cyan },
          ],
          legend: { x: R.x, y: 530, w: R.w, gap: 96, symW: 130, size: 23, symSize: 30 },
        });
      }
      // wb6: numbers and comparison
      const eA = A * seg(t, w6 - 0.2, 0.6);
      if (eA > 0) {
        refChip(d2, 'girth weld, per day of operation', R.x - 10, 246, eA);
        texSteps(ctx, t, 'f10bW', [
          { tex: `\\nu_0 \\cdot 1\\,\\mathrm{day} = ${fmtInt(WB.nu_day).replace(',', '{,}')}, \\quad h = ${h.toFixed(3)}`, t: at('wb6', 'twelve thousand') - 0.2, size: 28, dy: 0 },
          { tex: `q_t = ${q.toFixed(2)} \\cdot ${WS.tf.toFixed(3)} = ${WB.q_t.toFixed(1)}\\ \\mathrm{MPa}\\ \\text{(thickness corrected)}`, t: at('wb6', 'after the thickness'), size: 28, dy: 56 },
          { tex: `\\Gamma\\!\\left(1 + \\tfrac{3}{${h.toFixed(2)}}\\right) = ${WB.G1.toFixed(2)}, \\quad \\left(\\tfrac{S_1}{q_t}\\right)^{h} = ${WB.x.toFixed(2)}`, t: at('wb6', 'after the thickness') + 1.5, size: 28, dy: 112 },
        ], R.x, 290, { alpha: eA });
        const rows = [
          ['rainflow + Miner, all sea states', WB.life, PAL.orange, at('wb6', 'two-slope form') - 0.6],
          ['Weibull, eq. (5.4), two slopes', WB.life_wb2, PAL.cyan, at('wb6', 'two-slope form')],
          ['Weibull, eq. (5.3), one slope', WB.life_wb1, PAL.red, at('wb6', 'single slope')],
        ];
        d2.text('fatigue life, days of operation', R.x, 500, { size: 23, weight: 750, alpha: eA * seg(t, rows[0][3] - 0.3, 0.6) });
        rows.forEach(([lab, v, col, tt], k) => {
          const qq = seg(t, tt - 0.2, 0.8, ease.out);
          const y = 560 + k * 110;
          d2.text(lab, R.x, y, { size: 22, weight: 650, alpha: eA * clamp(qq * 2) });
          d2.rect(R.x, y + 16, 520 * v / 1600 * qq, 34, { fill: rgba(col, 0.75), alpha: eA });
          const rel = k === 0 ? '' : `  (${v > WB.life ? '+' : '−'}${Math.round(Math.abs(v / WB.life - 1) * 100)} %)`;
          d2.text(`${fmtInt(v)}${rel}`, R.x + 10 + 520 * v / 1600 * qq, y + 42, { size: 22, weight: 800, color: col, alpha: eA * clamp(qq * 2) });
        });
        const sq = seg(t, at('wb6', 'on the safe side') - 0.3, 0.6);
        d2.panel(R.x - 10, 900, R.w + 20, 86, { alpha: eA * sq, accent: PAL.amber, fill: 'rgba(30,24,8,0.9)' });
        d2.text('closed form: use a shape parameter on the safe side', R.x + 14, 938, { size: 22, weight: 750, color: PAL.amber, alpha: eA * sq });
        d2.text('C203 [2.1.2]', R.x + 14, 968, { size: 18, color: PAL.ink2, alpha: eA * sq });
      }
      chainBar(d2, 5, { alpha: A });
    },
  };
}
