// Fatigue in a nutshell: stress range, cracks at weld toes, S-N testing, design curve, power law.
import { makeBackdrop } from '../../engine/env.js';
import { Plot } from '../../engine/draw2d.js';
import { keyLine } from '../common.js';
import { heading, pow10 } from './fcommon.js';
import { PAL, seg, env, ease, clamp, lerp, rgba, rng } from '../../engine/util.js';

export default async function basics(ctx) {
  const { d2, cue, at, renderer, tex } = ctx;
  const back = makeBackdrop();
  const b1 = cue('b1'), b2 = cue('b2'), b3 = cue('b3'), b4 = cue('b4'), b5 = cue('b5');
  // synthetic constant-amplitude test results around a mean curve (std of log N = 0.2)
  const R = rng(17);
  const gauss = () => { let s = 0; for (let i = 0; i < 6; i++) s += R(); return (s - 3) / Math.sqrt(0.5); };
  const LA_MEAN = 12.564, SD = 0.2;
  const levels = [250, 200, 160, 125, 100, 80, 63];
  const tests = [];
  levels.forEach((S, i) => { for (let k = 0; k < 4; k++) tests.push({ S: S * (1 + 0.025 * (R() - 0.5)), N: Math.pow(10, LA_MEAN - 3 * Math.log10(S) + SD * gauss()), i, k }); });
  // the first specimen tested on the machine
  const first = { S: 125, N: Math.pow(10, LA_MEAN - 3 * Math.log10(125) + 0.12) };
  const meanN = (S) => Math.pow(10, LA_MEAN - 3 * Math.log10(S));
  const desN = (S) => Math.pow(10, LA_MEAN - 2 * SD - 3 * Math.log10(S));

  return {
    sfx: [{ t: at('b3', 'count the cycles') + 3.2, type: 'thud' }],
    render(t) {
      back.render(renderer);
      // ------------------------------------------------------------ b1: stress range
      const aA = env(t, 0.3, b2 - 0.2, 0.6, 0.5);
      if (aA > 0) {
        heading(d2, 'Fatigue in a nutshell', 120, 140, aA, { sub: 'what drives it, and how we measure it' });
        const P = new Plot(d2, { x: 210, y: 300, w: 1000, h: 440, xr: [0, 1], yr: [-1.5, 1.5] });
        d2.panel(140, 240, 1120, 580, { alpha: aA });
        P.axes({ alpha: aA, xlabel: 'time', ylabel: 'stress', fs: 22, ylabelOff: 40 });
        const sm = 0.25, sa = 0.85;
        const sig = (u) => sm + sa * Math.sin(u * Math.PI * 2 * 3.25 - 0.4);
        const dp = seg(t, b1 - 0.2, 3.2, ease.inOutSine);
        const pts = [];
        for (let i = 0; i <= 300; i++) pts.push([i / 300, sig(i / 300)]);
        P.curve(pts, { color: PAL.cyan, width: 4, progress: dp, alpha: aA, glow: PAL.cyan, glowBlur: 8 });
        const rp = seg(t, at('b1', 'stress range') - 0.3, 0.8);
        if (rp > 0) {
          const ymax = P.Y(sm + sa), ymin = P.Y(sm - sa), ym = P.Y(sm);
          d2.line(P.x, ymax, P.x + P.w, ymax, { color: PAL.ink2, width: 1.5, dash: [8, 7], alpha: aA * rp });
          d2.line(P.x, ymin, P.x + P.w, ymin, { color: PAL.ink2, width: 1.5, dash: [8, 7], alpha: aA * rp });
          d2.line(P.x, ym, P.x + P.w, ym, { color: PAL.ink3, width: 1.2, dash: [3, 6], alpha: aA * rp });
          d2.text('σ max', P.x + P.w - 8, ymax - 12, { size: 22, weight: 650, color: PAL.ink2, align: 'right', alpha: aA * rp });
          d2.text('σ min', P.x + P.w - 8, ymin + 30, { size: 22, weight: 650, color: PAL.ink2, align: 'right', alpha: aA * rp });
          d2.text('mean', P.x + P.w - 8, ym - 10, { size: 20, color: PAL.ink3, align: 'right', alpha: aA * rp });
          const q = seg(t, at('b1', 'the difference') - 0.2, 0.7, ease.outBack);
          const xr = P.X(0.12);
          d2.arrow(xr, ymin, xr, ymax, { color: PAL.amber, width: 4, head: 16, alpha: aA * clamp(q), double: true, glow: PAL.amber });
          tex.show('f02ds', '\\Delta\\sigma', xr + 18, (ymax + ymin) / 2 - 34, { size: 52, alpha: aA * clamp(q), color: PAL.amber });
        }
        // inset: a pipe bending back and forth; its outer-fibre stress is the signal on the plot
        const pa = aA * env(t, b1 + 0.6, at('b1', 'written delta') - 0.3, 0.6, 0.4);
        if (pa > 0) {
          d2.panel(1320, 240, 480, 580, { alpha: pa });
          d2.text('a pipe bending in the waves', 1350, 285, { size: 22, weight: 650, color: PAL.ink2, alpha: pa });
          const u = clamp((t - (b1 - 0.2)) / 3.2) ;
          const ph = u * Math.PI * 2 * 3.25 - 0.4 + Math.max(0, t - (b1 + 3.0)) * Math.PI * 2 * 0.33;
          const sv = sm + sa * Math.sin(ph);
          const bx = 1560, by0 = 760, by1 = 330;
          const bend = (sv - sm) * 70;
          const N = 30;
          const L = [], Rr = [];
          for (let i = 0; i <= N; i++) {
            const v = i / N;
            const x = bx + bend * v * v;
            const y = lerp(by0, by1, v);
            L.push([x - 26, y]); Rr.push([x + 26, y]);
          }
          d2.poly([...L, ...Rr.reverse()], { fill: 'rgba(150,175,195,0.45)', stroke: '#b9c9d6', width: 2, alpha: pa });
          d2.ground(bx, by0 + 2, 200, { alpha: pa });
          d2.arrow(bx + bend - 90 * Math.sign(bend || 1), by1 - 16, bx + bend, by1 - 16, { color: PAL.orange, width: 4, head: 14, alpha: pa * clamp(Math.abs(bend) / 30) });
          // hot spot at the base, coloured by its stress
          const hot = sv > sm;
          d2.circle(bx - 26, by0 - 40, 11, { fill: hot ? PAL.red : PAL.cyan, alpha: pa, glow: hot ? PAL.red : PAL.cyan });
          d2.text(hot ? 'tension' : 'compression', bx - 46, by0 - 34, { size: 20, weight: 700, color: hot ? PAL.red : PAL.cyan, align: 'right', alpha: pa });
        }
        const fa = aA * seg(t, at('b1', 'written delta') - 0.2, 0.7);
        if (fa > 0) {
          d2.panel(1320, 380, 480, 300, { alpha: fa, accent: PAL.amber });
          d2.text('stress range', 1350, 430, { size: 26, weight: 700, color: PAL.amber, alpha: fa });
          tex.show('f02dsf', '\\Delta\\sigma = \\sigma_{\\max} - \\sigma_{\\min}', 1350, 470, { size: 40, alpha: fa });
          d2.text('the main driver of fatigue', 1350, 600, { size: 22, color: PAL.ink2, alpha: fa });
          d2.text('in welded steel', 1350, 630, { size: 22, color: PAL.ink2, alpha: fa });
        }
      }
      // ------------------------------------------------------------ b2: crack at the weld toe
      const wA = env(t, b2 - 0.1, b3 - 0.2, 0.6, 0.5);
      if (wA > 0) {
        heading(d2, 'Cracks start at welds', 120, 140, wA, { sub: 'a notch, small flaws and residual stress' });
        const X0 = 640, Y0 = 540, T = 150;
        const g = d2.g;
        // plates
        const plate = (x0, x1) => d2.poly([[x0, Y0 - T / 2], [x1, Y0 - T / 2], [x1, Y0 + T / 2], [x0, Y0 + T / 2]], { fill: 'rgba(120,150,175,0.32)', stroke: '#9fb3c4', width: 2, alpha: wA });
        plate(X0 - 520, X0 - 46);
        plate(X0 + 46, X0 + 520);
        const cap = [[X0 - 86, Y0 - T / 2], [X0 - 50, Y0 - T / 2 - 22], [X0, Y0 - T / 2 - 34], [X0 + 50, Y0 - T / 2 - 22], [X0 + 86, Y0 - T / 2]];
        const root = [[X0 + 70, Y0 + T / 2], [X0 + 40, Y0 + T / 2 + 18], [X0 - 40, Y0 + T / 2 + 18], [X0 - 70, Y0 + T / 2]];
        d2.poly([...cap, ...root], { fill: 'rgba(176,152,108,0.55)', stroke: '#d1bd92', width: 2, alpha: wA });
        // weld ripples
        for (let k = 0; k < 5; k++) {
          const u = (k + 1) / 6;
          d2.path([[X0 - 80 + 160 * u - 30, Y0 - T / 2 - 4], [X0 - 80 + 160 * u, Y0 - T / 2 - 26 + Math.abs(u - 0.5) * 30], [X0 - 80 + 160 * u + 30, Y0 - T / 2 - 4]], { color: 'rgba(230,210,170,0.35)', width: 1.5, alpha: wA });
        }
        // stress arrows (cyclic)
        const ph = Math.sin(t * 2.4);
        for (const s of [-1, 1]) {
          for (const dy of [-50, 0, 50]) {
            const xb = X0 + s * 560;
            d2.arrow(xb, Y0 + dy, xb + s * (30 + 26 * ph), Y0 + dy, { color: PAL.cyan, width: 3, head: 11, alpha: wA * 0.85 });
          }
        }
        const toe = [X0 - 86, Y0 - T / 2];
        const tp = seg(t, at('b2', 'weld toe') - 0.2, 0.6);
        d2.circle(toe[0], toe[1], 20 + 4 * Math.sin(t * 5), { stroke: PAL.red, width: 3, alpha: wA * tp });
        d2.callout(toe[0], toe[1], toe[0] - 120, toe[1] - 120, 'weld toe', 'a sharp notch', { alpha: wA * tp, progress: tp, color: PAL.red, size: 28 });
        // flaws
        const fp = seg(t, at('b2', 'tiny flaws') - 0.2, 0.6);
        const RR = rng(3);
        for (let k = 0; k < 14; k++) {
          const u = RR();
          const px = lerp(X0 - 78, X0 - 40, u) + (RR() - 0.5) * 8, py = lerp(Y0 - T / 2 + 6, Y0 + T / 2 - 6, RR());
          d2.circle(px + (k % 2 ? 76 : 0), py, 2 + RR() * 2.5, { fill: '#1b2530', stroke: '#e9d7b0', width: 0.8, alpha: wA * fp });
        }
        d2.text('small welding flaws', X0 + 100, Y0 + T / 2 + 62, { size: 22, color: '#d1bd92', weight: 600, alpha: wA * fp });
        // residual stress halo
        const rs = seg(t, at('b2', 'residual stresses') - 0.2, 0.8);
        if (rs > 0) {
          g.save();
          g.globalAlpha = wA * rs * 0.55;
          const grd = g.createRadialGradient(X0, Y0 - 20, 20, X0, Y0, 230);
          grd.addColorStop(0, 'rgba(239,71,111,0.65)');
          grd.addColorStop(1, 'rgba(239,71,111,0)');
          g.fillStyle = grd;
          g.fillRect(X0 - 260, Y0 - T / 2 - 60, 520, T + 120);
          g.restore();
          d2.tag('residual stress ≈ yield', X0 + 150, Y0 - T / 2 - 70, { size: 21, color: PAL.red, alpha: wA * rs });
        }
        // crack growth from the toe through the wall
        const cs = at('b2', 'So a crack');
        const cg = seg(t, cs, b3 - 0.8 - cs, (x) => Math.pow(x, 2.2));
        if (cg > 0) {
          const pts = [toe];
          const n = 24;
          const RC = rng(9);
          for (let i = 1; i <= n; i++) {
            const u = i / n;
            if (u > cg) break;
            pts.push([toe[0] + 10 * u + (RC() - 0.5) * 7, toe[1] + u * T * 0.94]);
          }
          d2.path(pts, { color: '#ffe8b0', width: 3.2, alpha: wA, glow: PAL.amber, glowBlur: 16 });
        }
        // crack depth vs cycles
        const gp = seg(t, at('b2', 'crack starts early') - 0.6, 0.8);
        if (gp > 0) {
          d2.panel(1260, 280, 540, 470, { alpha: wA * gp, accent: PAL.amber });
          const P = new Plot(d2, { x: 1330, y: 360, w: 420, h: 260, xr: [0, 1], yr: [0, 1] });
          P.axes({ alpha: wA * gp, xlabel: 'cycles', ylabel: 'crack depth', fs: 20, ylabelOff: 30 });
          d2.text('Crack growth', 1290, 330, { size: 26, weight: 750, alpha: wA * gp });
          const a = (u) => 0.03 + 0.97 * Math.pow(u, 3.4);
          const cp = clamp(cg * 1.0 + 0.08 * (cg > 0));
          const pts = [];
          for (let i = 0; i <= 100; i++) pts.push([i / 100, a(i / 100)]);
          P.curve(pts, { color: PAL.amber, width: 3.5, progress: Math.max(cp, gp * 0.08), alpha: wA * gp });
          d2.line(P.X(0.1), P.y + P.h, P.X(0.1), P.y, { color: PAL.ink3, width: 1.2, dash: [5, 6], alpha: wA * gp });
          d2.text('start', P.X(0.05), P.y + 22, { size: 17, color: PAL.ink2, align: 'center', alpha: wA * gp });
          d2.text('growth: most of the life', P.X(0.55), P.y + 22, { size: 18, color: PAL.amber, weight: 650, align: 'center', alpha: wA * seg(t, at('b2', 'most of the life'), 0.6) });
        }
      }
      // ------------------------------------------------------------ b3..b5: S-N testing and the curve
      const sA = env(t, b3 - 0.2, ctx.duration, 0.6, 0.5);
      if (sA > 0) {
        heading(d2, 'Measuring fatigue strength', 120, 140, sA * (1 - seg(t, b4 - 0.4, 0.4)), { sub: 'constant-amplitude tests on welded specimens' });
        heading(d2, 'The design S-N curve', 120, 140, sA * seg(t, b4 - 0.2, 0.5), { sub: 'DNV-RP-C203' });
        const P = new Plot(d2, { x: 1040, y: 230, w: 740, h: 520, xr: [1e4, 1e8], yr: [40, 400], xlog: true, ylog: true });
        const pA = sA * seg(t, b3 + 0.4, 0.8);
        d2.panel(940, 180, 900, 710, { alpha: pA });
        P.axes({ alpha: pA, xticks: [1e4, 1e5, 1e6, 1e7, 1e8], yticks: [50, 100, 200, 400], fmtx: pow10, fmty: (v) => String(v),
          xlabel: 'cycles to failure, N', ylabel: 'stress range Δσ [MPa]', fs: 21, ylabelOff: 62 });
        // test machine (b3)
        const mA = sA * env(t, b3 + 0.2, b4 + 0.2, 0.5, 0.6);
        const tb0 = at('b3', 'we test') - 0.2, tbreak = at('b3', 'count the cycles') + 3.2;
        if (mA > 0) {
          const cx = 480, top = 300, bot = 840;
          const run = t < tbreak;
          const osc = run ? Math.sin((t - tb0) * 18) * 6 * seg(t, tb0, 0.6) : 0;
          // frame
          d2.rect(cx - 230, top - 30, 460, 30, { fill: '#2a3a4a', alpha: mA });
          d2.rect(cx - 230, bot, 460, 34, { fill: '#2a3a4a', alpha: mA });
          for (const s of [-1, 1]) d2.rect(cx + s * 210 - 14, top - 30, 28, bot - top + 64, { fill: '#33475a', alpha: mA });
          d2.rect(cx - 70, top, 140, 110, { fill: '#46596c', stroke: '#6d8296', width: 2, alpha: mA });
          d2.rect(cx - 50, top + 110 + osc, 100, 40, { fill: '#56697c', alpha: mA });
          // specimen with transverse weld
          const sy0 = top + 150 + osc, sy1 = bot - 150;
          const ym = (sy0 + sy1) / 2;
          const brk = clamp((t - tbreak) * 3);
          const gapY = brk * 26;
          d2.rect(cx - 34, sy0, 68, ym - sy0 - gapY / 2, { fill: '#9fb3c4', alpha: mA });
          d2.rect(cx - 34, ym + gapY / 2, 68, sy1 - ym - gapY / 2, { fill: '#9fb3c4', alpha: mA });
          d2.rect(cx - 40, ym - 9 - gapY / 2, 80, 18, { fill: '#c9b48a', alpha: mA * (1 - brk) });
          d2.rect(cx - 50, sy1, 100, 40, { fill: '#56697c', alpha: mA });
          d2.rect(cx - 70, bot - 110, 140, 110, { fill: '#46596c', stroke: '#6d8296', width: 2, alpha: mA });
          if (brk > 0 && brk < 1) d2.circle(cx, ym, 30 + 90 * brk, { stroke: PAL.amber, width: 3, alpha: mA * (1 - brk) });
          const Ncount = run ? first.N * clamp((t - tb0) / (tbreak - tb0)) ** 1.6 : first.N;
          d2.panel(cx - 170, bot + 60, 340, 70, { alpha: mA, fill: 'rgba(4,12,22,0.9)' });
          d2.text(`N = ${Math.round(Ncount).toLocaleString('en-US')}`, cx, bot + 106, { size: 30, weight: 800, align: 'center', color: run ? PAL.ink : PAL.amber, alpha: mA });
          d2.text(`Δσ = ${first.S} MPa, constant`, cx, top - 46, { size: 24, weight: 650, align: 'center', color: PAL.cyan, alpha: mA });
          // breaking point flies to the plot
          const fly = seg(t, tbreak + 0.2, 0.9, ease.inOutSine);
          if (fly > 0) {
            const x = lerp(cx, P.X(first.N), fly), y = lerp(ym, P.Y(first.S), fly) - Math.sin(fly * Math.PI) * 120;
            d2.circle(x, y, 9, { fill: PAL.amber, alpha: mA, glow: PAL.amber });
          }
        }
        // the first point stays
        const dim = 1 - 0.65 * seg(t, b5 - 0.3, 0.8);
        if (t > tbreak + 1.1) d2.circle(P.X(first.N), P.Y(first.S), 8, { fill: PAL.amber, stroke: '#06101a', width: 2, alpha: sA * dim });
        const rep = at('b3', 'Repeat that');
        tests.forEach((p, k) => {
          const q = seg(t, rep + 0.1 * k, 0.45, ease.outBack);
          if (q <= 0) return;
          d2.circle(P.X(p.N), P.Y(p.S), 7 * q, { fill: PAL.cyan, stroke: '#06101a', width: 2, alpha: sA * clamp(q) * dim });
        });
        // mean line + scatter band
        const lp = seg(t, at('b3', 'straight line') - 0.2, 1.0);
        P.clipBegin();
        P.curve([[meanN(400), 400], [meanN(40), 40]], { color: PAL.ink, width: 3, progress: lp, alpha: sA * 0.9 });
        P.clipEnd();
        if (lp > 0.5) d2.text('mean', P.X(meanN(46)) + 12, P.Y(46) - 4, { size: 22, weight: 700, color: PAL.ink, alpha: sA * seg(lp, 0.5, 0.5) });
        const bp = seg(t, at('b3', 'scatter') - 0.2, 0.8);
        if (bp > 0) {
          const g = d2.g;
          g.save();
          P.clipBegin();
          g.globalAlpha = sA * bp * 0.16;
          g.fillStyle = PAL.cyan;
          g.beginPath();
          g.moveTo(P.X(meanN(400) * Math.pow(10, 2 * SD)), P.Y(400));
          g.lineTo(P.X(meanN(40) * Math.pow(10, 2 * SD)), P.Y(40));
          g.lineTo(P.X(meanN(40) / Math.pow(10, 2 * SD)), P.Y(40));
          g.lineTo(P.X(meanN(400) / Math.pow(10, 2 * SD)), P.Y(400));
          g.closePath();
          g.fill();
          P.clipEnd();
          g.restore();
        }
        // b4: bell curve and the design curve
        const bA = sA * seg(t, b4 + 0.3, 0.8) * (1 - seg(t, b5 - 0.3, 0.8));
        if (bA > 0) {
          const S0 = 125;
          const yb = P.Y(S0);
          const g = d2.g;
          const pts = [];
          for (let i = -40; i <= 40; i++) {
            const z = i / 10;
            const x = P.X(meanN(S0) * Math.pow(10, z * SD));
            pts.push([x, yb - 110 * Math.exp(-0.5 * z * z) * bA]);
          }
          d2.path(pts, { color: PAL.ink2, width: 2.5, alpha: bA });
          // shaded lower tail beyond 2 SD
          const tail = pts.filter((_, i) => i <= 20);
          g.save();
          g.globalAlpha = bA * 0.5;
          g.fillStyle = PAL.red;
          g.beginPath();
          g.moveTo(tail[0][0], yb);
          tail.forEach(([x, y]) => g.lineTo(x, y));
          g.lineTo(tail[tail.length - 1][0], yb);
          g.closePath();
          g.fill();
          g.restore();
          const x2 = P.X(desN(S0));
          d2.line(x2, yb - 130, x2, yb + 10, { color: PAL.cyan, width: 2, dash: [6, 5], alpha: bA });
          d2.text('2 SD', (x2 + P.X(meanN(S0))) / 2, yb - 128, { size: 20, weight: 700, color: PAL.ink2, align: 'center', alpha: bA });
          d2.arrow(P.X(meanN(S0)), yb - 116, x2, yb - 116, { color: PAL.ink2, width: 1.8, head: 10, alpha: bA });
        }
        const dp = seg(t, at('b4', 'two standard') - 0.1, 1.2);
        P.clipBegin();
        P.curve([[desN(400), 400], [desN(40), 40]], { color: PAL.cyan, width: 4.5, progress: dp, alpha: sA, glow: PAL.cyan, glowBlur: 10 });
        P.clipEnd();
        const dl = sA * seg(t, at('b4', 'survival') - 0.3, 0.6);
        if (dl > 0) {
          d2.tag('design curve = mean − 2 SD', P.X(desN(64)) - 14, P.Y(64) + 34, { size: 21, color: PAL.cyan, alpha: dl, align: 'right' });
          d2.tag('97.7 % survival probability', P.x + 18, P.y + P.h - 30, { size: 21, color: PAL.green, alpha: dl });
        }
        // b5: the power law
        const eA = sA * seg(t, b5 - 0.2, 0.7);
        if (eA > 0) {
          d2.panel(120, 250, 760, 330, { alpha: eA, accent: PAL.cyan });
          d2.text('The S-N curve is a power law', 160, 305, { size: 28, weight: 750, alpha: eA });
          tex.show('f02pl', 'N = \\bar a \\; \\Delta\\sigma^{-m}', 160, 335, { size: 54, alpha: eA * seg(t, at('b5', 'power law'), 0.6) });
          tex.show('f02lg', '\\log N = \\log \\bar a - m \\log \\Delta\\sigma', 160, 440, { size: 38, alpha: eA * seg(t, at('b5', 'divided by'), 0.6), color: PAL.ink2 });
          const mq = seg(t, at('b5', 'm is three'), 0.6);
          d2.text('most welds:', 160, 540, { size: 26, color: PAL.ink2, alpha: eA * mq });
          tex.show('f02m3', 'm = 3', 320, 506, { size: 40, alpha: eA * mq, color: PAL.amber });
          // slope triangle
          const S1 = 330, S2 = 165;
          const xa = P.X(desN(S1)), xb = P.X(desN(S2));
          d2.path([[xa, P.Y(S1)], [xb, P.Y(S1)], [xb, P.Y(S2)]], { color: PAL.amber, width: 2.5, alpha: sA * mq });
          d2.text('m = 3', xb + 12, (P.Y(S1) + P.Y(S2)) / 2 + 8, { size: 22, weight: 800, color: PAL.amber, alpha: sA * mq });
          // double the stress -> 1/8 the life
          const dq = seg(t, at('b5', 'double') - 0.2, 1.2, ease.inOutSine);
          if (dq > 0) {
            const Sa = 55, Sb = 110;
            const pa = [P.X(desN(Sa)), P.Y(Sa)], pb = [P.X(desN(Sb)), P.Y(Sb)];
            d2.circle(pa[0], pa[1], 9, { fill: PAL.green, alpha: sA * dq });
            const cur = [lerp(pa[0], pb[0], dq), lerp(pa[1], pb[1], dq)];
            d2.arrow(pa[0], pa[1], pa[0], pb[1], { color: PAL.green, width: 3, head: 12, alpha: sA * dq, progress: clamp(dq * 2) });
            d2.arrow(pa[0], pb[1], pb[0], pb[1], { color: PAL.red, width: 3, head: 12, alpha: sA * dq, progress: clamp(dq * 2 - 1) });
            d2.circle(cur[0], cur[1], 9, { fill: PAL.red, alpha: sA * dq * (dq >= 1 ? 1 : 0.6) });
            d2.text('× 2 stress', pa[0] + 14, (pa[1] + pb[1]) / 2 + 8, { size: 22, weight: 800, color: PAL.green, alpha: sA * clamp(dq * 2) });
            d2.text('÷ 8 life', (pa[0] + pb[0]) / 2, pb[1] - 16, { size: 22, weight: 800, color: PAL.red, align: 'center', alpha: sA * clamp(dq * 2 - 1) });
            const big = seg(t, at('b5', 'factor of eight'), 0.6);
            d2.panel(120, 620, 760, 150, { alpha: eA * big, accent: PAL.red });
            tex.show('f02x2', '2\\,\\Delta\\sigma \\;\\Rightarrow\\; N / 2^3 = N/8', 160, 650, { size: 44, alpha: eA * big, color: PAL.ink });
          }
        }
        keyLine(d2, t, at('b5', 'Small errors') - 0.2, ctx.duration - 0.2, 'Small errors in stress become big errors in life', { accent: PAL.red, size: 32 });
      }
    },
  };
}
