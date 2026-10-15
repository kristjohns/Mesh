// Step 1: scatter diagram -> one sea state -> spectrum -> irregular waves -> flex-joint force.
import { makeBackdrop } from '../../engine/env.js';
import { Plot } from '../../engine/draw2d.js';
import { chainBar, stepCard, heading, heat } from './fcommon.js';
import { PAL, seg, env, ease, clamp, lerp, rgba } from '../../engine/util.js';

export default async function seastates(ctx) {
  const { d2, cue, at, renderer, data, tex } = ctx;
  const F = data.fatigue;
  const back = makeBackdrop();
  const w1 = cue('w1'), w2 = cue('w2'), w3 = cue('w3'), w4 = cue('w4');
  const S = F.scatter;
  const P = S.P;
  const nh = P.length, nt = P[0].length;
  const pmax = Math.max(...P.flat());
  const hsMarg = P.map((row) => row.reduce((a, b) => a + b, 0));
  const EX = F.example;
  const sel = { i: 3, j: 7 }; // Hs 3-4 m, Tp 9-10 s
  const ex = EX;
  // sine components for the "sum of waves" picture: sample the spectrum
  const comps = [];
  const fs = [0.072, 0.088, 0.1, 0.108, 0.118, 0.135, 0.16];
  fs.forEach((f, k) => {
    const Sv = interp(ex.spec_f, ex.S_eta, f);
    comps.push({ f, a: Math.sqrt(2 * Sv * 0.012), ph: (k * 2.1) % 6.28 });
  });

  return {
    sfx: [{ t: 0.1, type: 'chapter' }],
    render(t) {
      back.render(renderer);
      const cb = seg(t, 1.6, 0.6);
      // ------------------------------------------------ scatter diagram
      const shrink = seg(t, w3 - 0.4, 1.2, ease.inOutSine);
      const hA = env(t, 1.0, w4 - 0.2, 0.6, 0.6);
      if (hA > 0) {
        const X0 = lerp(220, 150, shrink), Y0 = lerp(200, 300, shrink), W = lerp(820, 560, shrink), H = lerp(720, 520, shrink);
        const fade = 1 - 0.0 * shrink;
        const cw = W / nt, ch = H / nh;
        const Xc = (j) => X0 + j * cw, Yc = (i) => Y0 + H - (i + 1) * ch;
        d2.panel(X0 - 90, Y0 - 70, W + 130 + (1 - shrink) * 300, H + 150, { alpha: hA * fade });
        d2.text('Scatter diagram', X0 - 60, Y0 - 26, { size: 28, weight: 750, alpha: hA });
        d2.text('share of time in each sea state', X0 + 190, Y0 - 26, { size: 20, color: PAL.ink2, alpha: hA * (1 - shrink) });
        const build = seg(t, w1 + 1.0, 2.6);
        for (let i = 0; i < nh; i++) {
          for (let j = 0; j < nt; j++) {
            const p = P[i][j];
            if (p < 2e-5) continue;
            const q = clamp(build * 1.6 - (i + j) / (nh + nt));
            if (q <= 0) continue;
            const v = clamp((Math.log10(p) + 4.6) / (Math.log10(pmax) + 4.6));
            d2.rect(Xc(j) + 1, Yc(i) + 1, cw - 2, ch - 2, { fill: heat(v), alpha: hA * q * fade * 0.95 });
            if (p >= 0.004 && shrink < 0.5) d2.text((p * 100).toFixed(p >= 0.1 ? 0 : 1), Xc(j) + cw / 2, Yc(i) + ch / 2 + 6, { size: 15, weight: 650, color: v > 0.55 ? '#08131f' : PAL.ink, align: 'center', alpha: hA * q * (1 - shrink * 2) });
          }
        }
        // axes
        for (let j = 0; j <= nt; j += 2) d2.text(String(S.tp_edges[j]), Xc(j), Y0 + H + 26, { size: 17, color: PAL.ink2, align: 'center', alpha: hA });
        for (let i = 0; i <= nh; i += 2) d2.text(String(S.hs_edges[i]), X0 - 12, Y0 + H - i * ch + 6, { size: 17, color: PAL.ink2, align: 'right', alpha: hA });
        d2.text('peak period Tp [s]', X0 + W / 2, Y0 + H + 58, { size: 20, weight: 600, color: PAL.ink2, align: 'center', alpha: hA });
        const g = d2.g;
        g.save(); g.translate(X0 - 52, Y0 + H / 2); g.rotate(-Math.PI / 2);
        d2.text('significant wave height Hs [m]', 0, 0, { size: 20, weight: 600, color: PAL.ink2, align: 'center', alpha: hA });
        g.restore();
        if (shrink < 0.5) d2.text('% of time', X0 + W - 4, Y0 + 26, { size: 17, color: PAL.ink3, align: 'right', alpha: hA * (1 - shrink * 2) });
        // selected sea state
        const sp = seg(t, at('w1', 'Each cell') - 0.2, 0.6);
        if (sp > 0) {
          const pulse = 1 + 0.06 * Math.sin(t * 5);
          d2.rect(Xc(sel.j) - 2 * pulse, Yc(sel.i) - 2 * pulse, cw + 4 * pulse, ch + 4 * pulse, { stroke: PAL.ink, width: 3, alpha: hA * sp });
          const ca = hA * sp * (1 - seg(t, w2 - 0.5, 0.5));
          if (ca > 0) {
            d2.callout(Xc(sel.j) + cw, Yc(sel.i) + ch / 2, X0 + W + 60, Yc(sel.i) - 110, 'one sea state', 'Hs 3–4 m, Tp 9–10 s', { alpha: ca, progress: sp, color: PAL.ink, size: 28, elbow: [X0 + W + 20, Yc(sel.i) - 110] });
            d2.text('a few hours of irregular waves,', X0 + W + 72, Yc(sel.i) - 32, { size: 21, color: PAL.ink2, alpha: ca * seg(sp, 0.6, 0.4) });
            d2.text('with steady statistics', X0 + W + 72, Yc(sel.i) - 6, { size: 21, color: PAL.ink2, alpha: ca * seg(sp, 0.6, 0.4) });
          }
        }
        // marginal: time share per Hs band
        const mA = hA * seg(t, w2 - 0.2, 0.7) * (1 - shrink);
        if (mA > 0) {
          const xb = X0 + W + 30, bw = 230;
          d2.text('time per Hs band', xb, Y0 - 26, { size: 18, color: PAL.ink2, alpha: mA });
          hsMarg.forEach((m, i) => {
            const L = bw * Math.sqrt(m / Math.max(...hsMarg));
            d2.rect(xb, Yc(i) + 4, L * seg(t, w2 + i * 0.05, 0.5), ch - 8, { fill: rgba(PAL.cyan, 0.55), alpha: mA });
            if (m > 0.0005) d2.text(`${(m * 100).toFixed(m > 0.1 ? 0 : 1)} %`, xb + L + 8, Yc(i) + ch / 2 + 6, { size: 16, color: PAL.ink2, alpha: mA });
          });
          const b1 = seg(t, at('w2', 'below two'), 0.6);
          const b2 = seg(t, at('w2', 'above six'), 0.6);
          const bx = X0 - 8;
          const bxr = X0 + W + 330;
          const brace = (ya, yb, col, a, l1, l2) => {
            d2.path([[bxr - 12, ya + 2], [bxr, ya + 2], [bxr, yb - 2], [bxr - 12, yb - 2]], { color: col, width: 3, alpha: a });
            d2.text(l1, bxr + 20, (ya + yb) / 2 - 2, { size: 30, weight: 800, color: col, alpha: a });
            d2.text(l2, bxr + 20, (ya + yb) / 2 + 26, { size: 20, color: PAL.ink2, alpha: a });
          };
          if (b1 > 0) {
            d2.rect(X0, Yc(1), W, 2 * ch, { stroke: PAL.green, width: 3, alpha: mA * b1 });
            brace(Yc(1), Yc(0) + ch, PAL.green, mA * b1, '50 %', 'of the time Hs < 2 m');
          }
          if (b2 > 0) {
            d2.rect(X0, Yc(nh - 1), W, (nh - 6) * ch, { stroke: PAL.red, width: 3, alpha: mA * b2 });
            brace(Yc(nh - 1), Yc(6) + ch, PAL.red, mA * b2, '1.6 %', 'of the time Hs > 6 m');
          }
        }
      }
      // ------------------------------------------------ w3: spectrum + sum of sines
      const qA = env(t, w3 - 0.2, ctx.duration, 0.6, 0.5);
      if (qA > 0) {
        // spectrum (top right)
        const P1 = new Plot(d2, { x: 860, y: 200, w: 380, h: 200, xr: [0.03, 0.3], yr: [0, Math.max(...ex.S_eta) * 1.15] });
        d2.panel(800, 150, 500, 330, { alpha: qA, accent: PAL.cyan });
        d2.text('wave spectrum', 830, 186, { size: 22, weight: 700, color: PAL.cyan, alpha: qA });
        P1.axes({ alpha: qA, fs: 16, xlabel: 'frequency [Hz]', xticks: [0.1, 0.2, 0.3], yticks: [], fmtx: (v) => v.toFixed(1) });
        const sp = [];
        ex.spec_f.forEach((f, k) => { if (f <= 0.3) sp.push([f, ex.S_eta[k]]); });
        const pp = seg(t, w3, 1.2);
        P1.curve(sp, { color: PAL.cyan, width: 3, progress: pp, alpha: qA });
        // fill under
        if (pp >= 1) {
          const g = d2.g;
          g.save(); g.globalAlpha = qA * 0.18; g.fillStyle = PAL.cyan; g.beginPath();
          g.moveTo(P1.X(sp[0][0]), P1.Y(0)); sp.forEach(([x, y]) => g.lineTo(P1.X(x), P1.Y(y))); g.lineTo(P1.X(sp[sp.length - 1][0]), P1.Y(0)); g.fill(); g.restore();
        }
        // component sines
        const cA = qA * env(t, at('w3', 'sum of many') - 0.4, w4 + 1.4, 0.5, 0.6);
        if (cA > 0) {
          const xL = 1360, xR = 1800, yT = 175;
          d2.text('components', xL, yT, { size: 20, weight: 650, color: PAL.ink2, alpha: cA });
          comps.forEach((c, k) => {
            const q = seg(t, at('w3', 'sum of many') - 0.2 + k * 0.12, 0.5);
            const yc = yT + 36 + k * 40;
            const pts = [];
            for (let i = 0; i <= 120; i++) {
              const tt = (i / 120) * 40;
              pts.push([xL + (xR - xL) * i / 120, yc - c.a * 14 * Math.sin(2 * Math.PI * c.f * (tt + t * 2) + c.ph)]);
            }
            d2.path(pts, { color: rgba(PAL.cyan, 0.85), width: 1.8, alpha: cA * q });
            // marker on the spectrum
            d2.circle(P1.X(c.f), P1.Y(interp(ex.spec_f, ex.S_eta, c.f)), 5, { fill: PAL.cyan, alpha: cA * q });
          });
          d2.text('+', 1580, 470, { size: 30, weight: 700, color: PAL.ink2, align: 'center', alpha: cA });
        }
        // irregular surface (bottom)
        const eP = new Plot(d2, { x: 860, y: 560, w: 920, h: 150, xr: [0, 120], yr: [-3.2, 3.2] });
        const eA = qA * seg(t, at('w3', 'spread over') - 0.6, 0.7);
        d2.panel(800, 510, 1040, 250, { alpha: eA });
        d2.text('wave elevation η(t) [m]', 830, 545, { size: 22, weight: 700, color: PAL.cyan, alpha: eA });
        const ep = seg(t, at('w3', 'spread over') - 0.4, 2.2, ease.inOutSine);
        const pts = [];
        for (let i = 0; i < 480; i++) pts.push([i * ex.dt, ex.eta[i]]);
        eP.axes({ alpha: eA, xticks: [], yticks: [-2, 0, 2], fs: 15, fmty: (v) => String(v) });
        eP.curve(pts, { color: PAL.cyan, width: 2.2, progress: ep, alpha: eA });
        // w4: transfer function + force
        const gA = qA * seg(t, w4 + 1.0, 0.7);
        if (gA > 0) {
          const xc = 1360;
          d2.panel(xc - 40, 150, 520, 330, { alpha: gA, accent: PAL.orange, fill: 'rgba(14,30,48,0.97)' });
          d2.text('transfer function |G|', xc - 10, 186, { size: 22, weight: 700, color: PAL.orange, alpha: gA });
          const P2 = new Plot(d2, { x: xc + 30, y: 210, w: 400, h: 190, xr: [3, 20], yr: [0, F.G.G0 * 1.15] });
          P2.axes({ alpha: gA, fs: 16, xlabel: 'wave period [s]', xticks: [5, 10, 15, 20], yticks: [0, 10, 20], fmty: (v) => String(v), ylabel: 'kN per m', ylabelOff: 40 });
          const gp = [];
          F.G.T.forEach((T, k) => { if (T <= 20 && T >= 3) gp.push([T, F.G.G[k]]); });
          gp.sort((a, b) => a[0] - b[0]);
          P2.curve(gp, { color: PAL.orange, width: 3, progress: seg(t, w4 + 1.2, 1.0), alpha: gA });
          d2.text('×', 1300, 330, { size: 40, weight: 700, color: PAL.ink2, align: 'center', alpha: gA });
          const tA = gA * seg(t, at('w4', 'simple transfer') - 0.3, 0.6);
          d2.tag('assumed — stands in for a global riser analysis', xc + 220, 452, { size: 17, color: PAL.ink2, align: 'center', alpha: tA, fill: 'rgba(5,14,26,0.9)' });
        }
        const fA = qA * seg(t, at('w4', 'The result') - 0.4, 0.7);
        if (fA > 0) {
          const fP = new Plot(d2, { x: 860, y: 850, w: 920, h: 150, xr: [0, 120], yr: [-60, 60] });
          d2.panel(800, 790, 1040, 260, { alpha: fA, accent: PAL.orange });
          d2.text('flex-joint force F(t) [kN]', 830, 830, { size: 22, weight: 700, color: PAL.orange, alpha: fA });
          fP.axes({ alpha: fA, xticks: [0, 30, 60, 90, 120], yticks: [-40, 0, 40], fs: 15, fmty: (v) => String(v), fmtx: (v) => `${v} s` });
          const fp = seg(t, at('w4', 'The result') - 0.2, 2.2, ease.inOutSine);
          const pf = [];
          for (let i = 0; i < 480; i++) pf.push([i * ex.dt, ex.F[i]]);
          fP.curve(pf, { color: PAL.orange, width: 2.4, progress: fp, alpha: fA });
        }
        // left: the BOP and riser, with the force arrow
        const bA = qA * seg(t, w4 - 0.2, 0.7) * shrinkBack(t, w4);
        if (bA > 0) drawStack(d2, t, 430, 640, bA, ex);
      }
      chainBar(d2, 1, { alpha: cb });
      stepCard(d2, t, 1, 'Sea states and riser loads', 'from the scatter diagram to a force history');
    },
  };
}

function shrinkBack() { return 1; }

function interp(xs, ys, x) {
  if (x <= xs[0]) return ys[0];
  for (let i = 0; i < xs.length - 1; i++) if (x <= xs[i + 1]) return ys[i] + (ys[i + 1] - ys[i]) * (x - xs[i]) / (xs[i + 1] - xs[i]);
  return ys[ys.length - 1];
}

// schematic BOP stack with riser, swaying with the force history
function drawStack(d2, t, cx, cy, a, ex) {
  const i = Math.floor(((t * 4) % 480 + 480) % 480);
  const f = ex.F[i] / 60;
  const g = d2.g;
  g.save();
  g.globalAlpha = a;
  g.translate(cx, cy + 260);
  g.rotate(f * 0.05);
  const grad = (x0, x1, c0, c1) => { const q = g.createLinearGradient(x0, 0, x1, 0); q.addColorStop(0, c0); q.addColorStop(0.45, c1); q.addColorStop(1, c0); return q; };
  // riser with buoyancy joints
  g.fillStyle = grad(-11, 11, '#6f7a84', '#c9d1d8');
  g.fillRect(-11, -720, 22, 360);
  g.fillStyle = grad(-26, 26, '#8a6a12', '#e0a80c');
  for (let k = 0; k < 3; k++) g.fillRect(-26, -715 + k * 100, 52, 70);
  // flex joint
  d2.circle(0, -352, 20, { fill: '#3b444c', stroke: '#6d7a86', width: 2 });
  // LMRP
  d2.roundRectPath(-62, -334, 124, 70, 8); g.fillStyle = grad(-62, 62, '#1f252b', '#4a545e'); g.fill();
  // frame
  g.strokeStyle = '#c0392b'; g.lineWidth = 6;
  g.strokeRect(-118, -262, 236, 210);
  g.beginPath(); g.moveTo(-118, -160); g.lineTo(118, -160); g.stroke();
  // accumulator bottles
  for (let k = 0; k < 5; k++) { d2.roundRectPath(-108 + k * 18, -250, 13, 78, 6); g.fillStyle = '#e0a80c'; g.fill(); }
  for (let k = 0; k < 5; k++) { d2.roundRectPath(30 + k * 18, -250, 13, 78, 6); g.fillStyle = '#e0a80c'; g.fill(); }
  // BOP body and ram blocks
  d2.roundRectPath(-48, -264, 96, 230, 10); g.fillStyle = grad(-48, 48, '#1b2026', '#56616c'); g.fill();
  for (let k = 0; k < 3; k++) {
    d2.roundRectPath(-92, -150 + k * 38, 184, 26, 6); g.fillStyle = grad(-92, 92, '#2a3138', '#79858f'); g.fill();
  }
  // connector and wellhead
  d2.roundRectPath(-44, -34, 88, 34, 6); g.fillStyle = grad(-44, 44, '#20262c', '#4f5963'); g.fill();
  g.fillStyle = grad(-26, 26, '#8d99a3', '#e3e9ee');
  g.fillRect(-26, -2, 52, 14);
  g.restore();
  d2.line(cx - 260, cy + 272, cx + 260, cy + 272, { color: '#b9a98a', width: 3, alpha: a });
  d2.text('MUDLINE', cx + 255, cy + 262, { size: 15, weight: 700, color: '#b9a98a', align: 'right', ls: 2, alpha: a });
  const ax = cx + Math.sin(f * 0.05) * 352, ay = cy + 260 - 352;
  const fa = a * (0.35 + 0.65 * clamp(Math.abs(f) * 3));
  d2.arrow(ax + Math.sign(f || 1) * 24, ay, ax + Math.sign(f || 1) * 24 + f * 200, ay, { color: PAL.orange, width: 6, head: 22, alpha: fa * clamp(Math.abs(f) * 12), glow: PAL.orange });
  d2.text('F(t)', ax + (f >= 0 ? 40 : -40), ay - 28, { size: 26, weight: 800, color: PAL.orange, align: f >= 0 ? 'left' : 'right', alpha: fa });
  d2.text('flex joint', ax - 34, ay + 8, { size: 20, color: PAL.ink2, align: 'right', alpha: a });
  d2.text('BOP', cx + 130, cy + 140, { size: 20, weight: 700, color: '#e07a70', alpha: a });
}
