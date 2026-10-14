// Step 5: Palmgren-Miner for one sea state, then the long-term sum over the scatter diagram, and the
// Weibull closed form of C203 as a check.
import { makeBackdrop } from '../../engine/env.js';
import { Plot } from '../../engine/draw2d.js';
import { chainBar, stepCard, heading, heat, pow10, snN, snS, fmtInt } from './fcommon.js';
import { PAL, seg, env, ease, clamp, lerp, rgba } from '../../engine/util.js';

export default async function miner(ctx) {
  const { d2, cue, at, renderer, data, tex } = ctx;
  const F = data.fatigue;
  const back = makeBackdrop();
  const m1 = cue('m1'), m2 = cue('m2'), m3 = cue('m3'), m4 = cue('m4');
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
      const aA = env(t, 1.6, m2 - 0.1, 0.6, 0.6);
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
      const bA = env(t, m2 - 0.2, m4 - 0.1, 0.6, 0.6);
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
      // ------------------------------------------------------------ m4: Weibull closed form
      const wA = env(t, m4 - 0.2, ctx.duration, 0.6, 0.5);
      if (wA > 0) {
        heading(d2, 'Shortcut: the Weibull closed form', 110, 150, wA, { sub: 'DNV-RP-C203, simplified fatigue analysis' });
        const E = DG.exceed;
        const WP = new Plot(d2, { x: 220, y: 260, w: 640, h: 560, xr: [0, 140], yr: [-8, 0] });
        d2.panel(110, 210, 830, 790, { alpha: wA });
        WP.axes({ alpha: wA, xticks: [0, 20, 40, 60, 80, 100, 120, 140], yticks: [0, -2, -4, -6, -8], fs: 18, fmty: (v) => (v === 0 ? '1' : `10${'⁻'}${'⁰¹²³⁴⁵⁶⁷⁸'[-v]}`), xlabel: 'stress range Δσ [MPa]', ylabel: 'probability of exceedance', ylabelOff: 64 });
        d2.text('long-term stress ranges, girth weld', 140, 248, { size: 20, weight: 700, color: PAL.ink2, alpha: wA });
        const pq = seg(t, m4 + 0.6, 1.4);
        const pts = E.Q.map((Q, k) => [E.s[k], Math.log10(Q)]).filter((p) => p[0] > 0.5 && p[0] <= 140);
        WP.points(pts, { color: PAL.orange, r: 5, progress: pq, alpha: wA });
        const fq = seg(t, at('m4', 'Weibull distribution') - 0.2, 1.0);
        const h = DG.weibull_h, q = DG.weibull_q;
        const wpts = [];
        for (let i = 0; i <= 100; i++) { const s = 140 * i / 100; wpts.push([s, Math.log10(Math.exp(-Math.pow(s / q, h)))]); }
        WP.clipBegin(); WP.curve(wpts, { color: PAL.cyan, width: 3.5, progress: fq, alpha: wA }); WP.clipEnd();
        d2.text(`Weibull fit: h = ${h.toFixed(2)}, q = ${q.toFixed(1)} MPa`, WP.x + WP.w - 10, WP.y + 34, { size: 21, weight: 750, color: PAL.cyan, align: 'right', alpha: wA * fq });
        // formula + comparison
        const kq = seg(t, at('m4', 'closed-form') - 0.4, 0.6);
        d2.panel(990, 210, 850, 260, { alpha: wA * kq, accent: PAL.cyan });
        tex.show('f10wb', 'D = \\dfrac{\\nu_0\\, T_d}{\\bar a}\\; q^{m}\\; \\Gamma\\!\\left(1 + \\dfrac{m}{h}\\right)', 1020, 245, { size: 44, alpha: wA * kq });
        d2.text('two-slope curve: incomplete gamma functions', 1020, 440, { size: 19, color: PAL.ink2, alpha: wA * kq });
        const rows = [
          ['rainflow + Miner, all sea states', DG.life_days, PAL.orange, at('m4', 'Fitted')],
          ['Weibull, two-slope S-N curve', DG.life_wb2, PAL.cyan, at('m4', 'within ten')],
          ['Weibull, one slope (no bend)', DG.life_wb1, PAL.red, at('m4', 'Ignore the bend')],
        ];
        d2.panel(990, 500, 850, 500, { alpha: wA * seg(t, at('m4', 'Fitted') - 0.3, 0.6) });
        d2.text('fatigue life, days of operation', 1020, 545, { size: 22, weight: 700, alpha: wA * seg(t, at('m4', 'Fitted') - 0.3, 0.6) });
        rows.forEach(([lab, v, col, tt], k) => {
          const qq = seg(t, tt - 0.2, 0.8, ease.out);
          const y = 610 + k * 120;
          d2.text(lab, 1020, y, { size: 22, weight: 650, alpha: wA * clamp(qq * 2) });
          d2.rect(1020, y + 18, 560 * v / 2000 * qq, 34, { fill: rgba(col, 0.75), alpha: wA });
          const rel = k === 0 ? '' : `  (${v > DG.life_days ? '+' : '−'}${Math.round(Math.abs(v / DG.life_days - 1) * 100)} %)`;
          d2.text(`${fmtInt(v)}${rel}`, 1030 + 560 * v / 2000 * qq, y + 44, { size: 22, weight: 800, color: col, alpha: wA * clamp(qq * 2) });
        });
      }
      chainBar(d2, 5, { alpha: seg(t, 1.6, 0.6) });
      stepCard(d2, t, 5, 'Adding up the damage', 'Palmgren–Miner, sea state by sea state');
    },
  };
}
