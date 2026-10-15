// Step 4, continued: reading the S-N equation of C203 term by term: eq. (2.8), the design curve as mean
// minus two standard deviations (2.9), the two branches of the D curve in seawater with CP, no fatigue
// limit under variable amplitude, the thickness effect (2.10) and a worked example at the girth weld.
import { makeBackdrop } from '../../engine/env.js';
import { Plot } from '../../engine/draw2d.js';
import { keyLine } from '../common.js';
import { chainBar, heading, formulaWalk, texSteps, refChip, pow10, snCurvePts, snS } from './fcommon.js';
import { PAL, seg, env, ease, clamp, lerp, rgba } from '../../engine/util.js';

export default async function snequation(ctx) {
  const { d2, cue, at, renderer, data, tex } = ctx;
  const F = data.fatigue;
  const W = F.worked.sn;
  const back = makeBackdrop();
  const e1 = cue('e1'), e2 = cue('e2'), e3 = cue('e3'), e4 = cue('e4'), e5 = cue('e5'), e6 = cue('e6'), e7 = cue('e7');
  const cp = [W.m1, W.la1, W.m2, W.la2];
  const H = (k, s) => `\\htmlClass{fw-f09bT-${k}}{${s}}`;
  // illustrative test results scattered around the mean curve (log N normal, s = 0.2)
  let seed = 7;
  const rnd = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
  const gauss = () => { let u = 0; for (let i = 0; i < 6; i++) u += rnd(); return (u - 3) / Math.sqrt(0.5); };
  const tests = [];
  for (let i = 0; i < 26; i++) {
    const ls = Math.log10(60) + (Math.log10(300) - Math.log10(60)) * rnd();
    tests.push([Math.pow(10, W.la1 + 0.4 - 3 * ls + 0.2 * gauss()), Math.pow(10, ls)]);
  }

  return {
    render(t) {
      back.render(renderer);
      const A = env(t, 0.3, ctx.duration, 0.6, 0.5);
      heading(d2, 'Reading the S-N curve', 110, 150, A, { sub: 'DNV-RP-C203 section 2.4, term by term' });
      // ------------------------------------------------------------ left: the plot
      d2.panel(80, 210, 900, 800, { alpha: A });
      const P = new Plot(d2, { x: 190, y: 250, w: 740, h: 640, xr: [1e4, 1e12], yr: [1, 1000], xlog: true, ylog: true });
      P.axes({ alpha: A, xticks: [1e4, 1e6, 1e8, 1e10, 1e12], yticks: [1, 10, 100, 1000], fmtx: pow10, fmty: (v) => String(v),
        xlabel: 'cycles to failure N (log scale)', ylabel: 'stress range Δσ [MPa] (log scale)', fs: 19, ylabelOff: 70 });
      // e1/e2: the first branch as a straight line, extended to 1 MPa
      const l1q = seg(t, e1 + 0.8, 1.6, ease.inOutSine);
      const ext = [[Math.pow(10, W.la1 - 3 * Math.log10(1000)), 1000], [Math.pow(10, W.la1), 1]];
      const lineA = A * (1 - seg(t, e4 - 0.4, 0.6));
      P.clipBegin();
      P.curve(ext, { color: PAL.amber, width: 3.5, progress: l1q, alpha: lineA });
      P.clipEnd();
      const iq = seg(t, at('e2', 'log a bar is') - 0.3, 0.6) * (1 - seg(t, e4 - 0.4, 0.6));
      if (iq > 0) {
        d2.circle(P.X(Math.pow(10, W.la1)), P.Y(1), 10, { fill: PAL.violet, alpha: A * iq, glow: PAL.violet });
        d2.text(`log ā₁ = ${W.la1.toFixed(3)}`, P.X(Math.pow(10, W.la1)) - 14, P.Y(1) - 22, { size: 22, weight: 800, color: PAL.violet, align: 'right', alpha: A * iq });
        d2.text('at Δσ = 1 MPa', P.X(Math.pow(10, W.la1)) - 14, P.Y(1) - 50, { size: 18, color: PAL.ink2, align: 'right', alpha: A * iq });
      }
      const sq = seg(t, at('e2', 'negative inverse slope') - 0.3, 0.8) * (1 - seg(t, e3 - 0.4, 0.6));
      if (sq > 0) {
        const Na = 1e6, Nb = 1e9, Sa = Math.pow(10, (W.la1 - 6) / 3), Sb = Math.pow(10, (W.la1 - 9) / 3);
        d2.path([[P.X(Na), P.Y(Sa)], [P.X(Nb), P.Y(Sa)], [P.X(Nb), P.Y(Sb)]], { color: PAL.green, width: 2.5, alpha: A * sq, progress: sq });
        d2.text('m = 3 decades in N', (P.X(Na) + P.X(Nb)) / 2, P.Y(Sa) - 12, { size: 20, weight: 750, color: PAL.green, align: 'center', alpha: A * sq });
        d2.text('1 decade', P.X(Nb) + 10, (P.Y(Sa) + P.Y(Sb)) / 2 + 6, { size: 20, weight: 750, color: PAL.green, alpha: A * sq });
      }
      // e3: mean curve and the test scatter
      const mq = A * env(t, e3 - 0.2, e4 - 0.2, 0.6, 0.6);
      if (mq > 0) {
        const tq = seg(t, e3 + 0.4, 1.4);
        tests.forEach(([N, S], i) => { if (i / tests.length < tq) d2.circle(P.X(N), P.Y(S), 4.5, { fill: PAL.ink2, alpha: mq * 0.8 }); });
        const meanL = [[Math.pow(10, W.la1 + 0.4 - 3 * Math.log10(1000)), 1000], [Math.pow(10, W.la1 + 0.4), 1]];
        P.clipBegin();
        P.curve(meanL, { color: PAL.ink, width: 2.5, dash: [10, 7], alpha: mq * seg(t, at('e3', 'shifts the mean') - 0.3, 0.6) });
        P.clipEnd();
        const aq = seg(t, at('e3', 'the shift is') - 0.3, 0.6);
        const Sx = 30, N1 = Math.pow(10, W.la1 - 3 * Math.log10(Sx)), N0 = N1 * Math.pow(10, 0.4);
        d2.arrow(P.X(N0), P.Y(Sx), P.X(N1), P.Y(Sx), { color: PAL.red, width: 3, head: 11, alpha: mq * aq });
        d2.text('− 2 s = − 0.4 in log N', P.X(N0) + 12, P.Y(Sx) + 30, { size: 20, weight: 750, color: PAL.red, alpha: mq * aq });
        d2.text('mean of the tests', P.X(3e5) + 10, P.Y(snS([3, W.la1 + 0.4, null, null], 3e5)) - 14, { size: 19, weight: 700, color: PAL.ink, alpha: mq * seg(t, at('e3', 'shifts the mean') - 0.3, 0.6) });
        d2.text('test results (illustrative)', P.x + 20, P.y + 30, { size: 18, color: PAL.ink2, alpha: mq * tq });
      }
      // e4..: the full two-branch curve
      const bq = A * seg(t, e4 - 0.4, 0.8);
      if (bq > 0) {
        const pts = snCurvePts(cp, 1e4, 1e12, 120);
        P.clipBegin();
        P.curve(pts.filter((p) => p[0] <= W.N1 * 1.001), { color: PAL.amber, width: 4, alpha: bq, progress: seg(t, e4 - 0.2, 1.0) });
        P.curve(pts.filter((p) => p[0] >= W.N1 * 0.999), { color: PAL.cyan, width: 4, alpha: bq, progress: seg(t, at('e4', 'Beyond that') - 0.3, 1.2) });
        P.clipEnd();
        const kq = seg(t, at('e4', 'The two branches meet') - 0.3, 0.6);
        d2.circle(P.X(W.N1), P.Y(W.S1), 10, { fill: PAL.ink, alpha: bq * kq, glow: PAL.ink });
        d2.text(`${W.S1.toFixed(1)} MPa at 10⁶`, P.X(W.N1) + 16, P.Y(W.S1) - 14, { size: 21, weight: 800, color: PAL.ink, alpha: bq * kq });
        d2.text('m₁ = 3', P.X(3e4) + 6, P.Y(snS(cp, 3e4)) - 16, { size: 22, weight: 800, color: PAL.amber, alpha: bq });
        d2.text('m₂ = 5', P.X(1e9), P.Y(snS(cp, 1e9)) - 18, { size: 22, weight: 800, color: PAL.cyan, alpha: bq * seg(t, at('e4', 'Beyond that'), 0.6) });
        d2.text('D curve, seawater with CP', P.x + 20, P.y + 30, { size: 20, weight: 700, color: PAL.ink2, alpha: bq * (1 - seg(t, e6 + 2, 0.6)) });
        // e5: no fatigue limit
        const nq = seg(t, e5 - 0.2, 0.8) * (1 - seg(t, e6 - 0.3, 0.6));
        if (nq > 0) {
          d2.line(P.X(W.N1), P.Y(W.S1), P.X(1e12), P.Y(W.S1), { color: PAL.ink2, width: 2.5, dash: [10, 8], alpha: bq * nq });
          d2.cross(P.X(3e10), P.Y(W.S1) - 30, 16, { progress: seg(t, at('e5', 'no fatigue limit') - 0.2, 0.8), alpha: bq * nq });
          d2.text('no cut-off', P.X(3e10) + 26, P.Y(W.S1) - 24, { size: 20, weight: 750, color: PAL.ink2, alpha: bq * nq });
          const gq = seg(t, at('e5', 'shallower') - 0.3, 0.8);
          P.clipBegin();
          P.curve(snCurvePts(cp, W.N1, 1e12), { color: PAL.green, width: 6, alpha: bq * nq * gq, glow: PAL.green });
          P.clipEnd();
        }
        // e6: thickness-corrected curve
        const tq = seg(t, at('e6', 'thirty-eight') - 0.3, 1.0);
        if (tq > 0) {
          P.clipBegin();
          P.curve(snCurvePts(cp, 1e4, 1e12).map(([N, S]) => [N, S / W.tf]), { color: PAL.orange, width: 3, dash: [7, 6], alpha: bq * tq });
          P.clipEnd();
          d2.text('t = 38.1 mm: Δσ allowed ÷ 1.088', P.X(1e12) - 6, P.Y(snS(cp, 1e12) / W.tf) + 34, { size: 19, weight: 750, color: PAL.orange, align: 'right', alpha: bq * tq });
        }
        // e7: the two worked ranges
        W.examples.forEach((ex, k) => {
          const q = seg(t, at('e7', k === 0 ? 'becomes sixty-five' : 'one hundred megapascals') - 0.3, 0.8);
          if (q <= 0) return;
          const col = k === 0 ? PAL.cyan : PAL.amber;
          const x = P.X(ex.N);
          d2.line(P.X(1e4), P.Y(ex.ds_eff), x, P.Y(ex.ds_eff), { color: col, width: 1.6, dash: [5, 5], alpha: bq * q });
          d2.line(x, P.Y(ex.ds_eff), x, P.Y(1), { color: col, width: 1.6, dash: [5, 5], alpha: bq * q });
          d2.circle(x, P.Y(ex.ds_eff), 10, { fill: col, alpha: bq * q, glow: col });
          d2.text(`N = ${ex.N > 1e6 ? (ex.N / 1e6).toFixed(1) + ' million' : Math.round(ex.N / 1e3) + ' 000'}`, x + 14, P.Y(1) - 14 - k * 30, { size: 20, weight: 800, color: col, alpha: bq * q });
        });
      }
      // ------------------------------------------------------------ right: formulas
      d2.panel(1010, 210, 830, 800, { alpha: A });
      const R = { x: 1050, w: 760 };
      // eq. (2.8)
      const fA = A * env(t, e1 - 0.2, e3 - 0.2, 0.6, 0.5);
      if (fA > 0) {
        refChip(d2, 'C203 eq. (2.8)', 1040, 246, fA);
        formulaWalk(ctx, t, {
          id: 'f09bE', x: R.x, y: 290, size: 52, alpha: fA, tOff: e3,
          latex: `${H('N', '\\log N')} = ${H('a', '\\log \\bar a')} - ${H('m', 'm')}\\,${H('s', '\\log \\Delta\\sigma')}`.replace(/fw-f09bT-/g, 'fw-f09bE-'),
          rows: [
            { k: 'N', sym: 'N', text: 'cycles to failure', sub: 'at a constant stress range', t: at('e2', 'N is'), col: PAL.ink },
            { k: 's', sym: '\\Delta\\sigma', text: 'stress range, in MPa', t: at('e2', 'delta sigma, in'), col: PAL.cyan },
            { k: 'm', sym: 'm', text: 'negative inverse slope', sub: 'one decade in Δσ per m decades in N', t: at('e2', 'negative inverse slope'), col: PAL.green },
            { k: 'a', sym: '\\log \\bar a', text: 'intercept of the design curve with the log N axis', sub: 'log N at Δσ = 1 MPa', t: at('e2', 'log a bar is'), col: PAL.violet },
          ],
          legend: { x: R.x, y: 410, w: R.w, gap: 82, symW: 150, size: 23, symSize: 30 },
        });
      }
      // eq. (2.9)
      const gA = A * env(t, e3 - 0.2, e4 - 0.2, 0.6, 0.5);
      if (gA > 0) {
        refChip(d2, 'C203 eq. (2.9), [F.6]', 1040, 246, gA);
        formulaWalk(ctx, t, {
          id: 'f09bM', x: R.x, y: 290, size: 52, alpha: gA, tOff: e4,
          parts: [['ab', '\\log \\bar a'], [null, ' = '], ['a', '\\log a'], [null, ' - '], ['s', '2\\,s_{\\log N}']],
          rows: [
            { k: 'a', sym: '\\log a', text: 'intercept of the mean curve of the tests', t: at('e3', 'shifts the mean') - 0.6, col: PAL.ink },
            { k: 's', sym: 's_{\\log N}', text: 'standard deviation of log N: 0.200', sub: 'two of them: 0.4 in log N', t: at('e3', 'standard deviation'), col: PAL.red },
            { k: 'ab', sym: '\\log \\bar a', text: 'design curve: mean minus 2 s', sub: '97.7 % survival probability', t: at('e3', 'the design curve allows') - 0.4, col: PAL.violet },
          ],
          legend: { x: R.x, y: 410, w: R.w, gap: 90, symW: 150, size: 23, symSize: 30 },
        });
        const q = seg(t, at('e3', 'two and a half') - 0.4, 0.6);
        tex.show('f09b25', '10^{0.4} = 2.5 \\;\\Rightarrow\\; N_{design} = N_{mean} / 2.5', R.x, 720, { size: 34, alpha: gA * q, color: PAL.red });
      }
      // e4/e5: Table 2-2, D curve
      const hA = A * env(t, e4 - 0.2, e6 - 0.2, 0.6, 0.5);
      if (hA > 0) {
        refChip(d2, 'C203 Table 2-2: D curve, seawater with CP', 1040, 246, hA);
        const rows = [
          ['N ≤ 10⁶', `m₁ = 3`, `log ā₁ = ${W.la1.toFixed(3)}`, PAL.amber, e4 + 0.4],
          ['N > 10⁶', `m₂ = 5`, `log ā₂ = ${W.la2.toFixed(3)}`, PAL.cyan, at('e4', 'Beyond that') - 0.3],
        ];
        rows.forEach(([a, b, c, col, tt], k) => {
          const q = seg(t, tt, 0.6);
          const y = 330 + k * 80;
          d2.rect(R.x, y - 40, R.w, 64, { fill: rgba(col, 0.10), alpha: hA * q });
          d2.text(a, R.x + 20, y, { size: 26, weight: 750, color: col, alpha: hA * q });
          d2.text(b, R.x + 240, y, { size: 26, weight: 700, alpha: hA * q });
          d2.text(c, R.x + 440, y, { size: 26, weight: 700, alpha: hA * q });
        });
        const kq = seg(t, at('e4', 'The two branches meet') - 0.4, 0.6);
        d2.text('the bend: both branches give 10⁶ cycles', R.x, 520, { size: 23, weight: 700, color: PAL.ink, alpha: hA * kq });
        tex.show('f09bKn', `\\Delta\\sigma_{bend} = 10^{(\\log \\bar a_1 - 6)/m_1} = 10^{(${W.la1.toFixed(3)} - 6)/3} = ${W.S1.toFixed(1)}\\ \\mathrm{MPa}`, R.x, 548, { size: 30, alpha: hA * kq });
        const nq = seg(t, e5 - 0.2, 0.6);
        d2.panel(R.x - 10, 700, R.w + 20, 230, { alpha: hA * nq, accent: PAL.green, fill: 'rgba(8,24,30,0.9)' });
        d2.text('variable amplitude: no fatigue limit', R.x + 16, 748, { size: 25, weight: 750, color: PAL.green, alpha: hA * nq });
        d2.text('once large cycles have started a crack,', R.x + 16, 792, { size: 22, color: PAL.ink, alpha: hA * nq * seg(t, at('e5', 'once the big') - 0.3, 0.6) });
        d2.text('small ones help it grow', R.x + 16, 822, { size: 22, color: PAL.ink, alpha: hA * nq * seg(t, at('e5', 'once the big') - 0.3, 0.6) });
        d2.text('they count on the m = 5 branch', R.x + 16, 870, { size: 22, weight: 700, color: PAL.green, alpha: hA * nq * seg(t, at('e5', 'shallower') - 0.3, 0.6) });
        d2.text('(the fatigue limit in Table 2-1 is for screening only, [2.12])', R.x + 16, 906, { size: 17, color: PAL.ink3, alpha: hA * nq * seg(t, at('e5', 'shallower') + 0.5, 0.6) });
      }
      // e6: eq. (2.10)
      const kA = A * env(t, e6 - 0.2, e7 - 0.2, 0.6, 0.5);
      if (kA > 0) {
        refChip(d2, 'C203 eq. (2.10)', 1040, 246, kA);
        formulaWalk(ctx, t, {
          id: 'f09bT', x: R.x, y: 285, size: 44, alpha: kA, tOff: e7,
          latex: `\\log N = \\log \\bar a - m \\log\\!\\left(\\Delta\\sigma ${H('f', `\\left(\\dfrac{${H('t', 't')}}{${H('r', 't_{ref}')}}\\right)^{${H('k', 'k')}}`)}\\right)`,
          rows: [
            { k: 'f', sym: '(t/t_{ref})^k', text: 'thickness factor on the stress range', t: at('e6', 'multiplied by'), col: PAL.orange },
            { k: 'r', sym: 't_{ref}', text: 'reference thickness: 25 mm', t: at('e6', 't ref is'), col: PAL.cyan },
            { k: 't', sym: 't', text: 'thickness the crack grows through', sub: 't = t_ref for walls thinner than 25 mm', t: at('e6', 't is the thickness'), col: PAL.amber },
            { k: 'k', sym: 'k', text: 'thickness exponent: 0.20 for the D curve', sub: 'Table 2-2', t: at('e6', 'For the D curve'), col: PAL.violet },
          ],
          legend: { x: R.x, y: 420, w: R.w, gap: 82, symW: 160, size: 23, symSize: 30 },
        });
        const q = seg(t, at('e6', 'thirty-eight millimetre') - 0.4, 0.6);
        tex.show('f09bTf', `\\left(\\dfrac{38.1}{25}\\right)^{0.20} = ${W.tf.toFixed(3)}`, R.x, 780, { size: 38, alpha: kA * q, color: PAL.orange });
        d2.text('9 % more stress at the conductor', R.x + 360, 820, { size: 22, weight: 700, color: PAL.orange, alpha: kA * q });
      }
      // e7: worked example
      const wA = A * seg(t, e7 - 0.2, 0.6);
      if (wA > 0) {
        refChip(d2, 'worked example: conductor girth weld', 1040, 246, wA);
        const [x1, x2] = W.examples;
        const nf = (v) => (v > 1e6 ? `${(v / 1e6).toFixed(2)}\\times 10^6` : `${(v / 1e5).toFixed(2)}\\times 10^5`);
        d2.text('Δσ = 60 MPa', R.x, 310, { size: 26, weight: 800, color: PAL.cyan, alpha: wA });
        texSteps(ctx, t, 'f09bW1', [
          { tex: `60 \\cdot ${W.tf.toFixed(3)} = ${x1.ds_eff.toFixed(1)}\\ \\mathrm{MPa} < ${W.S1.toFixed(1)}\\;\\Rightarrow\\;\\text{branch 2}`, t: at('e7', 'becomes sixty-five') - 0.3, size: 28, dy: 0 },
          { tex: `\\log N = ${W.la2.toFixed(3)} - 5 \\log ${x1.ds_eff.toFixed(1)} = ${x1.logN.toFixed(2)}`, t: at('e7', 'log N is'), size: 28, dy: 56 },
          { tex: `N = ${nf(x1.N)}`, t: at('e7', 'About three point four'), size: 32, dy: 112, col: PAL.cyan },
        ], R.x, 330, { alpha: wA });
        const q2 = seg(t, at('e7', 'one hundred megapascals') - 0.4, 0.6);
        d2.text('Δσ = 100 MPa', R.x, 560, { size: 26, weight: 800, color: PAL.amber, alpha: wA * q2 });
        texSteps(ctx, t, 'f09bW2', [
          { tex: `100 \\cdot ${W.tf.toFixed(3)} = ${x2.ds_eff.toFixed(1)}\\ \\mathrm{MPa} > ${W.S1.toFixed(1)}\\;\\Rightarrow\\;\\text{branch 1}`, t: at('e7', 'one hundred megapascals') - 0.2, size: 28, dy: 0 },
          { tex: `\\log N = ${W.la1.toFixed(3)} - 3 \\log ${x2.ds_eff.toFixed(1)} = ${x2.logN.toFixed(2)}`, t: at('e7', 'steep branch'), size: 28, dy: 56 },
          { tex: `N = ${nf(x2.N)}`, t: at('e7', 'four hundred and fifty'), size: 32, dy: 112, col: PAL.amber },
        ], R.x, 580, { alpha: wA });
        const rq = seg(t, at('e7', 'Sixty-seven percent') - 0.3, 0.6);
        d2.panel(R.x - 10, 840, R.w + 20, 110, { alpha: wA * rq, accent: PAL.red, fill: 'rgba(30,12,20,0.9)' });
        d2.text('67 % more stress → 7.5 × fewer cycles', R.x + 16, 905, { size: 28, weight: 800, color: PAL.red, alpha: wA * rq });
      }
      chainBar(d2, 4, { alpha: A });
    },
  };
}
