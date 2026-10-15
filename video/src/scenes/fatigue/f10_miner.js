// Step 5: Palmgren-Miner for one sea state, then the long-term sum over the scatter diagram, and the
// Weibull closed form of C203 as a check.
import { makeBackdrop } from '../../engine/env.js';
import { Plot } from '../../engine/draw2d.js';
import { chainBar, stepCard, heading, heat, pow10, snN, snS, snCurvePts, fmtInt, formulaWalk, texSteps, refChip } from './fcommon.js';
import { PAL, seg, env, ease, clamp, lerp, rgba } from '../../engine/util.js';

export default async function miner(ctx) {
  const { d2, cue, at, renderer, data, tex } = ctx;
  const F = data.fatigue;
  const back = makeBackdrop();
  const m1 = cue('m1'), m1b = cue('m1b'), m1c = cue('m1c'), m2 = cue('m2'), m3 = cue('m3');
  const WM = F.worked.miner, WS = F.worked.sn;
  const Hh = F.example.hist;
  const hsC = F.hotspots.find((h) => h.id === 'cg');
  const cpD = F.sn_table_cp.D;
  const curve = [cpD[0], cpD[1], cpD[2], cpD[3]];
  const tf = hsC.tf;
  const Ncurve = (s) => snN(curve, s * tf);
  const bins = Hh.n.map((n, k) => ({ n, s: 0.5 * (Hh.edges[k] + Hh.edges[k + 1]), d: Hh.dmg[k] })).filter((b) => b.n > 0);
  const dmax = Math.max(...bins.map((b) => b.d));
  const DG = F.damage.cg;
  const P = F.scatter.P;
  const C = DG.contrib;
  const nh = P.length, nt = P[0].length;
  const pmax = Math.max(...P.flat()), cmax = Math.max(...C.flat());
  const tBand = P.map((r) => r.reduce((a, b) => a + b, 0));
  const dBand = C.map((r) => r.reduce((a, b) => a + b, 0));
  const sumR = (arr, a, b) => arr.slice(a, b).reduce((p, q) => p + q, 0);

  return {
    sfx: [{ t: 0.1, type: 'chapter' }],
    render(t) {
      back.render(renderer);
      // ------------------------------------------------------------ m1: Miner for one sea state
      const aA = env(t, 1.6, m1b - 0.1, 0.6, 0.6);
      if (aA > 0) {
        heading(d2, 'Palmgren–Miner rule', 110, 150, aA, { sub: 'one sea state: Hs 3–4 m, Tp 9–10 s, 3 hours' });
        tex.show('f10miner', 'D = \\sum_i \\dfrac{n_i}{N_i} \\;\\le\\; 1', 1180, 92, { size: 46, alpha: aA * seg(t, at('m1', 'The damage is') - 0.3, 0.6) });
        const yr = [2, 120];
        const Y = (s) => 260 + 640 * (1 - (Math.log10(s) - Math.log10(yr[0])) / (Math.log10(yr[1]) - Math.log10(yr[0])));
        // histogram, bars to the left
        const hx = 560;
        d2.panel(90, 220, 500, 760, { alpha: aA });
        d2.text('counted cycles n', 110, 255, { size: 22, weight: 700, color: PAL.green, alpha: aA });
        const nmax = Math.max(...bins.map((b) => b.n));
        bins.forEach((b) => {
          const L = 400 * Math.log10(1 + b.n) / Math.log10(1 + nmax);
          const y = Y(b.s);
          d2.rect(hx - L, y - 6, L, 12, { fill: rgba(PAL.green, 0.65), alpha: aA * seg(t, m1, 0.8) });
        });
        // S-N curve
        const SP = new Plot(d2, { x: 680, y: 260, w: 560, h: 640, xr: [1e5, 1e12], yr, xlog: true, ylog: true });
        d2.panel(610, 220, 660, 760, { alpha: aA });
        SP.axes({ alpha: aA, xticks: [1e6, 1e8, 1e10, 1e12], yticks: [5, 10, 20, 50, 100], fmtx: pow10, fmty: (v) => String(v), xlabel: 'cycles to failure N', fs: 18 });
        d2.text('D curve, seawater + CP, t = 38.1 mm', 630, 255, { size: 20, weight: 700, color: PAL.amber, alpha: aA });
        const crv = [];
        for (let i = 0; i <= 120; i++) { const s = Math.pow(10, Math.log10(yr[0]) + (Math.log10(yr[1]) - Math.log10(yr[0])) * i / 120); crv.push([Ncurve(s), s]); }
        SP.clipBegin(); SP.curve(crv, { color: PAL.amber, width: 4, alpha: aA }); SP.clipEnd();
        // sweep through the bins: n -> N -> n/N
        const sw0 = at('m1', 'uses up') - 0.3, sw1 = at('m1', 'The damage is');
        const dx = 1300;
        d2.panel(1290, 220, 540, 760, { alpha: aA * seg(t, sw0, 0.6) });
        d2.text('damage n / N per range', 1310, 255, { size: 22, weight: 700, color: PAL.orange, alpha: aA * seg(t, sw0, 0.6) });
        let Dsum = 0;
        bins.forEach((b, k) => {
          const tb = lerp(sw0, sw1, k / bins.length);
          const q = seg(t, tb, 0.5);
          if (q <= 0) return;
          const y = Y(b.s);
          const xN = SP.X(Ncurve(b.s));
          const active = env(t, tb, tb + 0.9, 0.1, 0.4);
          if (active > 0) {
            d2.line(hx, y, xN, y, { color: PAL.ink, width: 1.6, dash: [5, 5], alpha: aA * active });
            d2.circle(xN, y, 7, { fill: PAL.amber, alpha: aA * active, glow: PAL.amber });
          }
          const L = 470 * b.d / dmax;
          d2.rect(dx + 20, y - 6, L * q, 12, { fill: rgba(PAL.orange, 0.8), alpha: aA });
          Dsum += b.d * q;
        });
        // where the damage sits
        const pk = bins.reduce((a, b) => (b.d > a.d ? b : a), bins[0]);
        const wq = seg(t, sw1 - 0.2, 0.6);
        d2.text('a few large ranges do most of the damage:', dx + 20, 800, { size: 20, weight: 700, color: PAL.orange, alpha: aA * wq });
        d2.text('each counts with Δσ³', dx + 20, 828, { size: 20, weight: 700, color: PAL.orange, alpha: aA * wq });
        const totA = aA * seg(t, sw1, 0.6);
        d2.panel(1310, 880, 500, 80, { alpha: totA, accent: PAL.orange, fill: 'rgba(8,20,34,0.95)' });
        d2.text(`D = ${(Hh.D_3h * 1e5).toFixed(2)} × 10⁻⁵ in 3 hours`, 1340, 930, { size: 28, weight: 800, color: PAL.orange, alpha: totA });
        const fq = seg(t, at('m1', 'failure is predicted') - 0.2, 0.6);
        d2.tag(`this sea state alone, nonstop: failure after ≈ ${fmtInt(3 / Hh.D_3h / 24)} days`, 960, 1020, { size: 20, color: PAL.ink2, align: 'center', alpha: aA * fq, fill: 'rgba(5,14,26,0.92)' });
      }
      // ------------------------------------------------------------ m2/m3: long term
      const bA = env(t, m2 - 0.2, ctx.duration, 0.6, 0.6);
      if (bA > 0) {
        heading(d2, 'Long-term damage', 110, 150, bA, { sub: 'every sea state, weighted by how often it occurs' });
        tex.show('f10lt', 'D_{day} = 24\\,\\mathrm{h} \\sum_{j} p_j \\, d_j', 1220, 92, { size: 38, alpha: bA * seg(t, m2 + 0.6, 0.6) });
        const morph = seg(t, at('m2', 'This map') - 0.6, 1.4, ease.inOutSine);
        const X0 = 210, Y0 = 250, W = 620, H = 640, cw = W / nt, ch = H / nh;
        const Xc = (j) => X0 + j * cw, Yc = (i) => Y0 + H - (i + 1) * ch;
        d2.panel(110, 210, 800, 800, { alpha: bA });
        d2.text(morph < 0.5 ? 'share of time' : 'share of damage, % (girth weld)', 880, 248, { size: 22, weight: 700, color: morph < 0.5 ? PAL.cyan : PAL.orange, align: 'right', alpha: bA });
        for (let i = 0; i < nh; i++) for (let j = 0; j < nt; j++) {
          const p = P[i][j], c = C[i][j];
          const vp = p < 2e-5 ? -1 : clamp((Math.log10(p) + 4.6) / (Math.log10(pmax) + 4.6));
          const vc = c < 1e-5 ? -1 : clamp(Math.pow(c / cmax, 0.5));
          const v = lerp(vp, vc, morph);
          if (v < 0) continue;
          d2.rect(Xc(j) + 1, Yc(i) + 1, cw - 2, ch - 2, { fill: heat(v), alpha: bA * 0.95 });
          if (morph > 0.9 && c > 0.02) d2.text((c * 100).toFixed(0), Xc(j) + cw / 2, Yc(i) + ch / 2 + 6, { size: 15, weight: 750, color: v > 0.55 ? '#08131f' : PAL.ink, align: 'center', alpha: bA * seg(morph, 0.9, 0.1) });
        }
        for (let j = 0; j <= nt; j += 2) d2.text(String(F.scatter.tp_edges[j]), Xc(j), Y0 + H + 26, { size: 17, color: PAL.ink2, align: 'center', alpha: bA });
        for (let i = 0; i <= nh; i += 2) d2.text(String(F.scatter.hs_edges[i]), X0 - 12, Y0 + H - i * ch + 6, { size: 17, color: PAL.ink2, align: 'right', alpha: bA });
        d2.text('Tp [s]', X0 + W / 2, Y0 + H + 56, { size: 19, color: PAL.ink2, align: 'center', alpha: bA });
        d2.text('Hs [m]', X0 - 54, Y0 - 16, { size: 19, color: PAL.ink2, alpha: bA });
        // bars per Hs band: time vs damage
        const bq = seg(t, m3 - 0.6, 0.8);
        if (bq > 0) {
          const bx = 1100, bw = 480;
          d2.panel(960, 210, 880, 800, { alpha: bA * bq });
          d2.text('per Hs band', 990, 248, { size: 22, weight: 700, alpha: bA * bq });
          d2.rect(1340, 232, 18, 14, { fill: rgba(PAL.cyan, 0.75), alpha: bA * bq });
          d2.text('time', 1366, 246, { size: 19, color: PAL.ink2, alpha: bA * bq });
          d2.rect(1440, 232, 18, 14, { fill: rgba(PAL.orange, 0.85), alpha: bA * bq });
          d2.text('damage', 1466, 246, { size: 19, color: PAL.ink2, alpha: bA * bq });
          for (let i = 0; i < 10; i++) {
            const y = Yc(i);
            const g = seg(t, m3 - 0.4 + i * 0.06, 0.6);
            d2.text(`${i}–${i + 1} m`, bx - 16, y + ch / 2 + 6, { size: 18, color: PAL.ink2, align: 'right', alpha: bA * bq });
            d2.rect(bx, y + 6, bw * tBand[i] / 0.45 * g, ch / 2 - 6, { fill: rgba(PAL.cyan, 0.75), alpha: bA * bq });
            d2.rect(bx, y + ch / 2, bw * dBand[i] / 0.45 * g, ch / 2 - 6, { fill: rgba(PAL.orange, 0.85), alpha: bA * bq });
          }
          const call = (i0, i1, col, l1, l2, tt) => {
            const q = seg(t, tt - 0.2, 0.6);
            if (q <= 0) return;
            const ya = Yc(i1 - 1), yb = Yc(i0) + ch;
            const xr = 1810;
            d2.path([[xr - 12, ya + 2], [xr, ya + 2], [xr, yb - 2], [xr - 12, yb - 2]], { color: col, width: 3, alpha: bA * q });
            d2.text(l1, xr - 24, (ya + yb) / 2 - 4, { size: 24, weight: 800, color: col, align: 'right', alpha: bA * q });
            d2.text(l2, xr - 24, (ya + yb) / 2 + 22, { size: 18, color: PAL.ink2, align: 'right', alpha: bA * q });
          };
          call(0, 2, PAL.green, `${(sumR(dBand, 0, 2) * 100).toFixed(1)} % of damage`, `${Math.round(sumR(tBand, 0, 2) * 100)} % of time`, at('m3', 'calm days'));
          call(3, 6, PAL.orange, `${Math.round(sumR(dBand, 3, 6) * 100)} % of damage`, `${Math.round(sumR(tBand, 3, 6) * 100)} % of time`, at('m3', 'Three quarters'));
          call(6, 10, PAL.red, `${Math.round(sumR(dBand, 6, 12) * 100)} % of damage`, `${(sumR(tBand, 6, 12) * 100).toFixed(1)} % of time`, at('m3', 'storms'));
          const tq = seg(t, at('m3', 'template takes') - 0.3, 0.6);
          d2.tag('above 50 kN the template carries part of the load', 1400, 960, { size: 19, color: PAL.yellow, align: 'center', alpha: bA * tq, fill: 'rgba(5,14,26,0.92)' });
        }
      }
      // ------------------------------------------------------------ m1b/m1c: eq. (2.3) term by term, two slopes, worked bins
      const fA = env(t, m1b - 0.2, m2 - 0.1, 0.6, 0.6);
      if (fA > 0) {
        heading(d2, 'Palmgren–Miner, written out', 110, 150, fA, { sub: 'DNV-RP-C203 [2.2], eq. (2.3)' });
        d2.panel(80, 210, 1760, 250, { alpha: fA });
        const H = (k, x) => `\\htmlClass{fw-f10E-${k}}{${x}}`;
        formulaWalk(ctx, t, {
          id: 'f10E', x: 130, y: 250, size: 56, alpha: fA, tOff: m1c - 0.2,
          latex: `D = ${H('s', '\\sum_{i=1}^{k} \\dfrac{n_i}{N_i}')} = ${H('a', '\\dfrac{1}{\\bar a}')} \\sum_{i=1}^{k} n_i\\, ${H('m', '(\\Delta\\sigma_i)^{m}')} \\;\\le\\; ${H('e', '\\eta')}`,
          rows: [
            { k: 's', sym: '\\tfrac{n_i}{N_i}', text: 'cycles counted in block i ÷ cycles to failure at Δσᵢ', t: at('m1b', 'D is the sum'), col: PAL.orange },
            { k: 'a', sym: 'N_i = \\bar a\\, \\Delta\\sigma_i^{-m}', text: 'the S-N curve put in for Nᵢ', t: at('m1b', 'From the S N curve'), col: PAL.violet },
            { k: 'm', sym: '\\Delta\\sigma_i^{\\,m}', text: 'each cycle counts with its range to the power m', sub: 'm = 3: twice the range, eight times the damage', t: at('m1b', "That's why"), col: PAL.amber },
          ],
          legend: { x: 130, y: 500, w: 820, gap: 100, symW: 250, size: 23, symSize: 32, alpha: 1 - seg(t, m1c - 0.4, 0.6) },
        });
        const eq = seg(t, at('m1b', 'D is the sum') - 0.4, 0.6);
        d2.text('η: usage factor = 1 / DFF (see the design check)', 1240, 420, { size: 20, color: PAL.ink2, alpha: fA * eq });
        d2.text('k: number of stress blocks (≥ 20)', 1240, 392, { size: 20, color: PAL.ink2, alpha: fA * eq });
        // two slopes
        const tq = seg(t, m1c - 0.3, 0.6);
        d2.panel(1000, 480, 840, 520, { alpha: fA * seg(t, m1c - 0.3, 0.6) });
        if (tq > 0) {
          d2.text('two-slope curve: each range to its own branch', 1030, 530, { size: 23, weight: 750, alpha: fA * tq });
          tex.show('f10two', `D = \\dfrac{1}{\\bar a_1}\\!\\sum_{\\Delta\\sigma_i > S_1}\\! n_i\\,\\Delta\\sigma_i^{\\,m_1} + \\dfrac{1}{\\bar a_2}\\!\\sum_{\\Delta\\sigma_i \\le S_1}\\! n_i\\,\\Delta\\sigma_i^{\\,m_2}`, 1030, 560, { size: 32, alpha: fA * tq });
          d2.text(`S₁ = ${WS.S1.toFixed(1)} MPa after the thickness correction, m₁ = 3, m₂ = 5`, 1030, 690, { size: 19, color: PAL.ink2, alpha: fA * tq });
          const b2 = { s: 86.25 };
          b2.se = b2.s * WS.tf; b2.N = Math.pow(10, WS.la1 - 3 * Math.log10(b2.se));
          texSteps(ctx, t, 'f10W', [
            { tex: `${WM.s.toFixed(2)} \\cdot ${WS.tf.toFixed(3)} = ${WM.s_eff.toFixed(1)} < ${WS.S1.toFixed(1)}:\\; N = 10^{${WS.la2.toFixed(3)} - 5\\log ${WM.s_eff.toFixed(1)}} = ${(WM.N / 1e6).toFixed(2)}\\times 10^6`, t: at('m1c', 'A sixty-nine') + 0.5, size: 24, dy: 0, col: PAL.cyan },
            { tex: `n/N = ${WM.n} / ${(WM.N / 1e6).toFixed(2)}\\times 10^6 = ${(WM.d * 1e5).toFixed(1)}\\times 10^{-5}`, t: at('m1c', 'Twenty-five of them'), size: 26, dy: 52, col: PAL.cyan },
            { tex: `${b2.s.toFixed(2)} \\cdot ${WS.tf.toFixed(3)} = ${b2.se.toFixed(1)} > ${WS.S1.toFixed(1)}:\\; N = 10^{${WS.la1.toFixed(3)} - 3\\log ${b2.se.toFixed(1)}} = ${(b2.N / 1e5).toFixed(1)}\\times 10^5`, t: at('m1c', 'eighty-six'), size: 24, dy: 120, col: PAL.amber },
            { tex: `k = ${WM.nbins}\\ \\text{blocks}, \\quad D_{3\\,h} = \\sum_i n_i/N_i = ${(WM.D_3h * 1e4).toFixed(1)}\\times 10^{-4}`, t: at('m1c', 'We have forty-two'), size: 28, dy: 200, col: PAL.orange },
          ], 1030, 720, { alpha: fA * tq });
          // mini S-N plot with the two blocks
          const SP = new Plot(d2, { x: 200, y: 540, w: 700, h: 380, xr: [1e5, 1e8], yr: [40, 160], xlog: true, ylog: true });
          const pa = fA * tq;
          d2.panel(80, 480, 900, 520, { alpha: pa });
          SP.axes({ alpha: pa, xticks: [1e5, 1e6, 1e7, 1e8], yticks: [40, 60, 80, 100, 150], fmtx: pow10, fmty: (v) => String(v), xlabel: 'N', ylabel: 'Δσ after thickness correction [MPa]', fs: 18, ylabelOff: 62 });
          const cp = [WS.m1, WS.la1, WS.m2, WS.la2];
          SP.clipBegin(); SP.curve(snCurvePts(cp, 1e5, 1e8), { color: PAL.ink2, width: 3, alpha: pa }); SP.clipEnd();
          d2.circle(SP.X(WS.N1), SP.Y(WS.S1), 7, { fill: PAL.ink, alpha: pa });
          d2.text('bend', SP.X(WS.N1) + 10, SP.Y(WS.S1) - 10, { size: 18, color: PAL.ink2, alpha: pa });
          const p1 = seg(t, at('m1c', 'A sixty-nine') + 0.3, 0.6), p2 = seg(t, at('m1c', 'eighty-six') - 0.2, 0.6);
          d2.circle(SP.X(WM.N), SP.Y(WM.s_eff), 10, { fill: PAL.cyan, alpha: pa * p1, glow: PAL.cyan });
          d2.text('branch 2 (m = 5)', SP.X(WM.N) + 14, SP.Y(WM.s_eff) + 26, { size: 19, weight: 750, color: PAL.cyan, alpha: pa * p1 });
          d2.circle(SP.X(b2.N), SP.Y(b2.se), 10, { fill: PAL.amber, alpha: pa * p2, glow: PAL.amber });
          d2.text('branch 1 (m = 3)', SP.X(b2.N) + 14, SP.Y(b2.se) - 14, { size: 19, weight: 750, color: PAL.amber, alpha: pa * p2 });
        }
      }
      chainBar(d2, 5, { alpha: seg(t, 1.6, 0.6) });
      stepCard(d2, t, 5, 'Adding up the damage', 'Palmgren–Miner, sea state by sea state');
    },
  };
}
