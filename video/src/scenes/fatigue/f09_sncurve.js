// Step 4: the C203 S-N curve family, detail classification, environment, thickness effect,
// variable amplitude (no fatigue limit).
import { makeBackdrop } from '../../engine/env.js';
import { Plot } from '../../engine/draw2d.js';
import { chainBar, stepCard, pow10, snCurvePts, snS } from './fcommon.js';
import { PAL, seg, env, ease, clamp, lerp, rgba, mixHex } from '../../engine/util.js';

export default async function sncurve(ctx) {
  const { d2, cue, at, renderer, data, tex } = ctx;
  const F = data.fatigue;
  const back = makeBackdrop();
  const n1 = cue('n1'), n2 = cue('n2'), n3 = cue('n3'), n4 = cue('n4'), n5 = cue('n5');
  const classes = ['B1', 'B2', 'C', 'C1', 'C2', 'D', 'E', 'F', 'F1', 'F3', 'G', 'W1', 'W2', 'W3'];
  const air = {}, cp = {}, fc = {};
  for (const c of classes) {
    const [m1, la1, m2, la2] = F.sn_table[c];
    air[c] = [m1, la1, m2, la2];
    const q = F.sn_table_cp[c];
    cp[c] = [q[0], q[1], q[2], q[3]];
    fc[c] = [3, la1 - Math.log10(3), null, null];
  }
  const colOf = (i) => mixHex(PAL.cyan, PAL.red, i / (classes.length - 1));
  const tfac = F.hotspots.find((h) => h.id === 'cg').tf;

  return {
    sfx: [{ t: 0.1, type: 'chapter' }],
    render(t) {
      back.render(renderer);
      const pA = env(t, 1.6, ctx.duration, 0.6, 0.5);
      if (pA > 0) {
        const P = new Plot(d2, { x: 210, y: 150, w: 980, h: 720, xr: [1e4, 1e9], yr: [10, 1000], xlog: true, ylog: true });
        d2.panel(110, 110, 1150, 900, { alpha: pA });
        P.axes({ alpha: pA, xticks: [1e4, 1e5, 1e6, 1e7, 1e8, 1e9], yticks: [10, 20, 50, 100, 200, 500, 1000], fmtx: pow10, fmty: (v) => String(v),
          xlabel: 'number of cycles N', ylabel: 'stress range Δσ [MPa]', fs: 21, ylabelOff: 64 });
        // ------------------------------------------------ n1: the family in air
        const famFade = 1 - 0.85 * seg(t, at('n2', 'We assume') - 0.4, 0.8);
        const famOut = 1 - seg(t, n3 - 0.2, 0.8);
        classes.forEach((c, i) => {
          const q = seg(t, n1 + 1.0 + i * 0.32, 0.7);
          if (q <= 0) return;
          const isD = c === 'D';
          const a = pA * (isD ? 1 : famFade) * (isD ? 1 : famOut) * (isD ? 1 - seg(t, n3 - 0.2, 0.6) : 1);
          if (a <= 0.001) return;
          P.clipBegin();
          P.curve(snCurvePts(air[c], 1e4, 1e9), { color: colOf(i), width: isD && famFade < 0.9 ? 5 : 2.4, progress: q, alpha: a, glow: isD && famFade < 0.9 ? PAL.cyan : null });
          P.clipEnd();
          const yEnd = P.Y(snS(air[c], 1e9));
          if (['B1', 'C', 'D', 'F', 'G', 'W3'].includes(c)) d2.text(c, P.x + P.w + 10, yEnd + 7, { size: isD ? 22 : 18, weight: isD ? 800 : 650, color: colOf(i), alpha: a * q });
        });
        const famLab = pA * seg(t, n1 + 1.5, 0.6) * famOut;
        d2.text('B1: plain steel', P.X(2e4) + 10, P.Y(snS(air.B1, 2e4)) - 14, { size: 20, weight: 650, color: PAL.cyan, alpha: famLab * famFade });
        d2.text('W3: through the weld metal', P.X(1.4e4), P.Y(snS(air.W3, 1.4e4)) + 34, { size: 20, weight: 650, color: PAL.red, alpha: famLab * famFade });
        // ------------------------------------------------ n3: environments for D
        const eA = pA * seg(t, n3 - 0.2, 0.6);
        if (eA > 0) {
          const qa = seg(t, n3 + 0.2, 1.0), qc = seg(t, at('n3', 'cathodic protection') - 0.4, 1.0), qf = seg(t, at('n3', 'free corrosion') - 0.3, 1.0);
          P.clipBegin();
          P.curve(snCurvePts(air.D, 1e4, 1e9), { color: PAL.cyan, width: 4, progress: qa, alpha: eA });
          P.curve(snCurvePts(cp.D, 1e4, 1e9), { color: PAL.amber, width: 4, progress: qc, alpha: eA, glow: PAL.amber, glowBlur: 6 });
          P.curve(snCurvePts(fc.D, 1e4, 1e9), { color: PAL.red, width: 3.5, progress: qf, alpha: eA, dash: [12, 8] });
          P.clipEnd();
          const ka = F.sn_knee.air, kc = F.sn_knee.cp;
          const kq1 = seg(t, at('n3', 'ten million') - 0.2, 0.5);
          d2.circle(P.X(ka.N), P.Y(ka.S), 9, { fill: PAL.cyan, alpha: eA * kq1, glow: PAL.cyan });
          d2.text('bend at 10⁷', P.X(ka.N) + 10, P.Y(ka.S) - 16, { size: 21, weight: 750, color: PAL.cyan, alpha: eA * kq1 });
          d2.text('m = 3', P.X(1e5) + 30, P.Y(snS(air.D, 1e5)) - 22, { size: 22, weight: 800, color: PAL.cyan, alpha: eA * kq1 });
          d2.text('m = 5', P.X(1e8) - 10, P.Y(snS(air.D, 1e8)) - 18, { size: 22, weight: 800, color: PAL.cyan, alpha: eA * seg(t, at('n3', 'slope of five') - 0.2, 0.5) * (1 - seg(t, n5, 0.5)) });
          const kq2 = seg(t, at('n3', 'one million') - 0.2, 0.5);
          d2.circle(P.X(kc.N), P.Y(kc.S), 9, { fill: PAL.amber, alpha: eA * kq2, glow: PAL.amber });
          d2.text('bend at 10⁶', P.X(kc.N) - 14, P.Y(kc.S) + 36, { size: 21, weight: 750, color: PAL.amber, align: 'right', alpha: eA * kq2 });
          // legend
          const lg = [['in air', PAL.cyan, qa], ['seawater + cathodic protection', PAL.amber, qc], ['free corrosion', PAL.red, qf]];
          lg.forEach(([s, col, q], k) => {
            const y = P.y + P.h - 120 + k * 36;
            d2.line(P.x + 30, y - 7, P.x + 74, y - 7, { color: col, width: 4, alpha: eA * q });
            d2.text(s, P.x + 88, y, { size: 21, weight: 650, color: PAL.ink, alpha: eA * q });
          });
          d2.text('D curve', P.x + 30, P.y + P.h - 156, { size: 22, weight: 800, color: PAL.ink2, alpha: eA * qa });
          const ours = seg(t, at('n3', 'Our welds') - 0.2, 0.6);
          if (ours > 0) d2.check(P.x + 88 + d2.measure('seawater + cathodic protection', 21, 650) + 26, P.y + P.h - 120 + 36 - 7, 13, { progress: ours, alpha: eA });
          // n4: thickness-corrected curve for the conductor
          const tq = seg(t, at('n4', 'thirty-eight') - 0.3, 1.0);
          if (tq > 0) {
            const shifted = snCurvePts(cp.D, 1e4, 1e9).map(([N, S]) => [N, S / tfac]);
            P.clipBegin();
            P.curve(shifted, { color: PAL.orange, width: 3, dash: [6, 6], progress: tq, alpha: eA });
            P.clipEnd();
            d2.text('D, seawater + CP, t = 38.1 mm', P.X(1e9) - 6, P.Y(snS(cp.D, 1e9) / tfac) + 30, { size: 19, weight: 750, color: PAL.orange, align: 'right', alpha: eA * tq * (1 - seg(t, n5, 0.5)) });
          }
          // n5: no fatigue limit
          const vq = seg(t, n5 + 0.2, 0.8);
          if (vq > 0) {
            const y = P.Y(kc.S);
            d2.line(P.X(kc.N), y, P.X(1e9), y, { color: PAL.ink2, width: 2.5, dash: [10, 8], alpha: eA * vq });
            d2.text('no cut-off here', P.X(3e8), y - 14, { size: 20, weight: 700, color: PAL.ink2, align: 'center', alpha: eA * vq });
            d2.cross(P.X(3e8), y + 34, 16, { progress: seg(t, at('n5', 'no fatigue limit'), 0.8), alpha: eA });
            const bq = seg(t, at('n5', 'still do damage') - 0.2, 0.8);
            P.clipBegin();
            const br = snCurvePts(cp.D, kc.N, 1e9);
            P.curve(br, { color: PAL.green, width: 6, progress: bq, alpha: eA, glow: PAL.green });
            P.clipEnd();
            d2.text('small cycles still count (m = 5)', P.X(1.2e8), P.Y(snS(cp.D, 1.2e8)) - 26, { size: 21, weight: 750, color: PAL.green, alpha: eA * bq });
          }
        }
      }
      // ------------------------------------------------------------ right column
      const X0 = 1310, W0 = 520;
      // n1: what decides the curve
      const dA = env(t, at('n1', 'Which one applies') - 0.3, n2 + 0.3, 0.6, 0.5);
      if (dA > 0) {
        d2.panel(X0, 160, W0, 520, { alpha: dA, accent: PAL.violet });
        d2.text('The curve depends on', X0 + 30, 214, { size: 28, weight: 750, alpha: dA });
        const items = [['geometry of the detail', 'its geometry'], ['how it is welded and inspected', 'welded and inspected'], ['the direction of the stress', 'which way the stress']];
        items.forEach(([s, k], i) => {
          const q = seg(t, at('n1', k) - 0.2, 0.6);
          d2.circle(X0 + 46, 290 + i * 110, 22, { fill: rgba(PAL.violet, 0.2), stroke: PAL.violet, width: 2, alpha: dA * q });
          d2.text(String(i + 1), X0 + 46, 298 + i * 110, { size: 22, weight: 800, color: PAL.violet, align: 'center', alpha: dA * q });
          d2.text(s, X0 + 86, 298 + i * 110, { size: 24, weight: 600, alpha: dA * q });
        });
        // small weld sketches with a stress arrow
        const q3 = seg(t, at('n1', 'which way the stress') - 0.2, 0.6);
        d2.arrow(X0 + 120, 560, X0 + 260, 560, { color: PAL.cyan, width: 4, head: 14, alpha: dA * q3, double: true });
        d2.rect(X0 + 280, 535, 100, 50, { fill: 'rgba(130,160,185,0.4)', stroke: '#9fb3c4', width: 2, alpha: dA * q3 });
        d2.rect(X0 + 322, 525, 16, 70, { fill: 'rgba(176,152,108,0.7)', alpha: dA * q3 });
        d2.text('stress across the weld', X0 + 120, 630, { size: 20, color: PAL.ink2, alpha: dA * q3 });
      }
      // n2: Appendix A
      const aA = env(t, n2 - 0.1, n3 + 0.2, 0.6, 0.5);
      if (aA > 0) {
        d2.panel(X0, 160, W0, 620, { alpha: aA, accent: PAL.cyan });
        d2.text('DNV-RP-C203 Appendix A', X0 + 30, 214, { size: 26, weight: 750, color: PAL.cyan, alpha: aA });
        d2.text('detail classification tables', X0 + 30, 248, { size: 21, color: PAL.ink2, alpha: aA });
        const q1 = seg(t, at('n2', 'girth weld') - 0.3, 0.6);
        // circumferential butt weld
        const gx = X0 + 40, gy = 290;
        d2.rect(gx, gy, 170, 46, { fill: 'rgba(130,160,185,0.4)', stroke: '#9fb3c4', width: 2, alpha: aA * q1 });
        d2.rect(gx + 190, gy, 170, 46, { fill: 'rgba(130,160,185,0.4)', stroke: '#9fb3c4', width: 2, alpha: aA * q1 });
        d2.poly([[gx + 160, gy], [gx + 180, gy - 12], [gx + 200, gy], [gx + 200, gy + 46], [gx + 180, gy + 58], [gx + 160, gy + 46]], { fill: 'rgba(176,152,108,0.75)', stroke: '#d1bd92', width: 1.5, alpha: aA * q1 });
        d2.text('girth weld (Table A-9, [3.3.7])', gx, gy + 100, { size: 21, weight: 700, alpha: aA * q1 });
        const gw = [
          ['both sides, in the shop,', 'pipe rotated: weld toe', 'D', PAL.cyan, at('n2', 'in the shop')],
          ['both sides, made on site', '', 'E', PAL.amber, at('n2', 'on site')],
          ['one side only, no backing:', 'weld root', 'F3', PAL.red, at('n2', 'one side only')],
        ];
        const ours = seg(t, at('n2', 'We assume') - 0.2, 0.6);
        gw.forEach(([a, b, c, col, tt], k) => {
          const q = seg(t, tt - 0.3, 0.6);
          const y = gy + 150 + k * 66;
          if (k === 0 && ours > 0) d2.rect(gx - 14, y - 30, W0 - 52, 62, { fill: rgba(PAL.cyan, 0.12), stroke: PAL.cyan, width: 2, radius: 8, alpha: aA * ours });
          d2.text(a, gx, y - 4, { size: 20, weight: 600, alpha: aA * q });
          if (b) d2.text(b, gx, y + 20, { size: 18, color: PAL.ink2, alpha: aA * q });
          d2.text(c, X0 + W0 - 50, y + 14, { size: 40, weight: 800, color: col, align: 'right', alpha: aA * q });
        });
        d2.line(X0 + 30, 600, X0 + W0 - 30, 600, { color: 'rgba(140,180,210,0.25)', width: 1, alpha: aA });
        const q2 = seg(t, at('n2', 'finite element') - 0.3, 0.6);
        const hy = 650;
        d2.text('hot-spot stress from FE ([4.3.5])', gx, hy, { size: 21, weight: 700, alpha: aA * q2 });
        d2.text('read at 0.5t and 1.5t', gx, hy + 28, { size: 18, color: PAL.ink2, alpha: aA * q2 });
        d2.text('D', X0 + W0 - 50, hy + 20, { size: 44, weight: 800, color: PAL.cyan, align: 'right', alpha: aA * q2 });
        d2.text('misalignment beyond 0.05t: add an SCF', gx, 750, { size: 18, color: PAL.ink3, alpha: aA * q2 });
      }
      // n3: environment summary
      const vA = env(t, n3 + 0.4, n4 - 0.1, 0.6, 0.5);
      if (vA > 0) {
        d2.panel(X0, 160, W0, 440, { alpha: vA, accent: PAL.amber });
        d2.text('Environment', X0 + 30, 214, { size: 28, weight: 750, alpha: vA });
        const rows = [['in air', 'D curve: bend at 10⁷ cycles', PAL.cyan, n3 + 0.4], ['seawater, cathodic protection', 'lower until 10⁶, then m = 5', PAL.amber, at('n3', 'cathodic protection') - 0.3],
          ['free corrosion', 'one slope, no bend', PAL.red, at('n3', 'free corrosion') - 0.3]];
        rows.forEach(([a, b, col, tt], i) => {
          const q = seg(t, tt, 0.6);
          d2.circle(X0 + 46, 280 + i * 100, 9, { fill: col, alpha: vA * q });
          d2.text(a, X0 + 70, 288 + i * 100, { size: 24, weight: 700, color: col, alpha: vA * q });
          d2.text(b, X0 + 70, 318 + i * 100, { size: 20, color: PAL.ink2, alpha: vA * q });
        });
      }
      // n4: thickness
      const tA = env(t, n4 - 0.2, n5 - 0.1, 0.6, 0.5);
      if (tA > 0) {
        d2.panel(X0, 160, W0, 600, { alpha: tA, accent: PAL.orange });
        d2.text('Thickness effect', X0 + 30, 214, { size: 28, weight: 750, alpha: tA });
        tex.show('f09th', '\\Delta\\sigma \\cdot \\left(\\dfrac{t}{t_{ref}}\\right)^{k}', X0 + 40, 250, { size: 44, alpha: tA * seg(t, n4 + 0.6, 0.6) });
        d2.text('t_ref = 25 mm, k = 0.20 for the D curve', X0 + 40, 400, { size: 21, color: PAL.ink2, alpha: tA * seg(t, at('n4', 'twenty-five') - 0.2, 0.6) });
        const q1 = seg(t, at('n4', 'thirty-eight') - 0.3, 0.6);
        d2.rect(X0 + 40, 450, 300 * 38.1 / 40, 46, { fill: rgba(PAL.orange, 0.35), stroke: PAL.orange, width: 2, alpha: tA * q1 });
        d2.text('conductor, 38.1 mm', X0 + 40, 530, { size: 22, weight: 700, alpha: tA * q1 });
        d2.text(`× ${tfac.toFixed(2)}`, X0 + W0 - 40, 486, { size: 36, weight: 800, color: PAL.orange, align: 'right', alpha: tA * q1 });
        const q2 = seg(t, at('n4', 'casing') - 0.3, 0.6);
        d2.rect(X0 + 40, 590, 300 * 15.9 / 40, 46, { fill: rgba(PAL.violet, 0.35), stroke: PAL.violet, width: 2, alpha: tA * q2 });
        d2.text('casing, 15.9 mm', X0 + 40, 670, { size: 22, weight: 700, alpha: tA * q2 });
        d2.text('× 1.00', X0 + W0 - 40, 626, { size: 36, weight: 800, color: PAL.violet, align: 'right', alpha: tA * q2 });
        d2.text('(no correction below 25 mm)', X0 + 40, 700, { size: 19, color: PAL.ink3, alpha: tA * q2 });
      }
      // n5: variable amplitude note
      const wA = env(t, n5 + 0.3, ctx.duration, 0.6, 0.5);
      if (wA > 0) {
        d2.panel(X0, 160, W0, 330, { alpha: wA, accent: PAL.green });
        d2.text('Variable amplitude', X0 + 30, 214, { size: 28, weight: 750, alpha: wA });
        d2.text('no fatigue limit: every cycle counts,', X0 + 30, 268, { size: 23, alpha: wA });
        d2.text('small ones on the m = 5 branch', X0 + 30, 300, { size: 23, alpha: wA });
        tex.show('f09m5', 'N = \\bar a_2 \\, \\Delta\\sigma^{-5}', X0 + 40, 340, { size: 40, alpha: wA * seg(t, at('n5', 'shallower'), 0.6), color: PAL.green });
      }
      chainBar(d2, 4, { alpha: seg(t, 1.6, 0.6) });
      stepCard(d2, t, 4, 'Choosing the S-N curve', 'detail category, environment and thickness');
    },
  };
}
