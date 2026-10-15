// Step 3: rainflow counting, animated on a stretch of the real stress history; 3-hour histogram;
// mean stress for as-welded joints.
import { makeBackdrop } from '../../engine/env.js';
import { Plot } from '../../engine/draw2d.js';
import { keyLine } from '../common.js';
import { chainBar, stepCard, heading, refChip } from './fcommon.js';
import { PAL, seg, env, ease, clamp, lerp, rgba } from '../../engine/util.js';

export default async function rainflow(ctx) {
  const { d2, cue, at, renderer, data, tex } = ctx;
  const F = data.fatigue;
  const back = makeBackdrop();
  const f1 = cue('f1'), f2 = cue('f2'), f3 = cue('f3'), f4 = cue('f4'), f5 = cue('f5'), f6 = cue('f6');
  const ex = F.example, rf = F.rf_demo;
  const rev = rf.rev, ridx = rf.rev_idx, seg_s = rf.s;
  const trace = rf.trace;
  // event schedule: pushes of reversals and extractions, in the order the algorithm meets them
  const events = simulate(rev);
  const tA = f2 + 4.2, tB = f4 + 1.6;              // algorithm runs from tA to tB
  const dtE = (tB - tA) / events.length;
  events.forEach((e, k) => { e.t = tA + k * dtE; });
  const extractions = events.filter((e) => e.kind !== 'push');
  const H = F.example.hist;

  return {
    sfx: [{ t: 0.1, type: 'chapter' }, ...extractions.filter((e) => e.kind === 'full').map((e) => ({ t: e.t + 0.1, type: 'click' }))],
    render(t) {
      back.render(renderer);
      // ---------------------------------------------------- f1: the irregular history, small cycles on big ones
      const aA = env(t, 1.4, f2 + 1.0, 0.6, 0.6);
      if (aA > 0) {
        heading(d2, 'What is a cycle?', 120, 160, aA, { sub: 'stress at the conductor girth weld, one minute of a 3-hour sea state' });
        const n0 = seg_s.length;
        const P = new Plot(d2, { x: 200, y: 260, w: 1560, h: 480, xr: [0, n0 * ex.dt], yr: [-50, 50] });
        d2.panel(130, 210, 1680, 640, { alpha: aA });
        P.axes({ alpha: aA, xticks: [0, 15, 30, 45, 60], yticks: [-40, -20, 0, 20, 40], fs: 19, fmtx: (v) => `${v} s`, fmty: (v) => String(v), ylabel: 'stress [MPa]', ylabelOff: 56 });
        const pts = [];
        for (let i = 0; i < n0; i++) pts.push([i * ex.dt, seg_s[i]]);
        P.curve(pts, { color: PAL.amber, width: 3, progress: seg(t, f1, 3.0, ease.inOutSine), alpha: aA });
        // highlight small cycles riding on larger ones (reversals 4-7 and 10-13 of the stretch)
        const hq = seg(t, at('f1', 'Small cycles') - 0.2, 0.7);
        if (hq > 0) {
          for (const [ka, kb] of [[4, 7], [10, 13]]) {
            const x0 = P.X(ridx[ka] * ex.dt) - 12, x1 = P.X(ridx[kb] * ex.dt) + 12;
            const ys = rev.slice(ka, kb + 1);
            const y0 = P.Y(Math.max(...ys)) - 14, y1 = P.Y(Math.min(...ys)) + 14;
            d2.rect(x0, y0, x1 - x0, y1 - y0, { stroke: PAL.cyan, width: 2.5, alpha: aA * hq });
          }
          d2.text('small cycles inside bigger ones', P.X(ridx[4] * ex.dt) - 12, P.Y(Math.max(...rev.slice(4, 8))) - 26, { size: 22, weight: 700, color: PAL.cyan, alpha: aA * hq });
        }
        const qq = seg(t, at('f1', 'not obvious'), 0.6);
        d2.text('?', 1740, 330, { size: 120, weight: 800, color: PAL.ink2, align: 'right', alpha: aA * qq * 0.5 });
      }
      // ---------------------------------------------------- f2-f4: rainflow on the demo stretch
      const rA = env(t, f2 - 0.3, f5 - 0.2, 0.6, 0.6);
      if (rA > 0) {
        heading(d2, 'Rainflow counting', 120, 160, rA, { sub: 'the standard cycle-counting method (ASTM E1049)' });
        const n = seg_s.length;
        const T = n * ex.dt;
        const P = new Plot(d2, { x: 180, y: 260, w: 1040, h: 560, xr: [0, T], yr: [-50, 50] });
        d2.panel(120, 210, 1150, 720, { alpha: rA });
        P.axes({ alpha: rA, xticks: [], yticks: [-40, -20, 0, 20, 40], fs: 18, fmty: (v) => String(v), ylabel: 'stress [MPa]', ylabelOff: 50 });
        const full = [];
        for (let i = 0; i < n; i++) full.push([i * ex.dt, seg_s[i]]);
        const fade = seg(t, at('f2', 'peaks and valleys') - 0.2, 1.2);
        P.curve(full, { color: PAL.amber, width: 2.2, alpha: rA * (1 - 0.75 * fade) });
        // reversal points and the connecting straight lines
        const rp = ridx.map((i, k) => [P.X(i * ex.dt), P.Y(rev[k])]);
        // points removed by extractions so far
        const gone = new Set();
        for (const e of extractions) if (t >= e.t + dtE * 0.8 && e.kind === 'full') { gone.add(e.a); gone.add(e.b); }
        const pushed = (k) => events.find((e) => e.kind === 'push' && e.i === k)?.t ?? Infinity;
        if (fade > 0) {
          const vis = rp.map((p, k) => k).filter((k) => !gone.has(k));
          d2.path(vis.map((k) => rp[k]), { color: PAL.ink, width: 2.4, alpha: rA * fade * 0.9 });
          vis.forEach((k) => {
            const lit = t >= pushed(k) ? 1 : 0.45;
            d2.circle(rp[k][0], rp[k][1], 7, { fill: lit > 0.5 ? PAL.cyan : PAL.ink3, stroke: '#06101a', width: 2, alpha: rA * fade });
          });
        }
        // the current extraction highlight
        for (const e of extractions) {
          const q = env(t, e.t, e.t + dtE * 1.6, 0.15, 0.4);
          if (q <= 0) continue;
          const [xa, ya] = rp[e.a], [xb, yb] = rp[e.b];
          const col = e.kind === 'full' ? PAL.green : PAL.violet;
          d2.line(xa, ya, xb, yb, { color: col, width: 6, alpha: rA * q, glow: col });
          d2.circle(xa, ya, 11, { stroke: col, width: 3, alpha: rA * q });
          d2.circle(xb, yb, 11, { stroke: col, width: 3, alpha: rA * q });
          // range bar
          const xr = Math.max(xa, xb) + 26;
          d2.arrow(xr, ya, xr, yb, { color: col, width: 3, head: 10, alpha: rA * q, double: true });
          d2.text(`${Math.abs(rev[e.a] - rev[e.b]).toFixed(1)} MPa${e.kind === 'full' ? '' : ' · ½'}`, xr + 12, (ya + yb) / 2 + 8, { size: 21, weight: 800, color: col, alpha: rA * q });
        }
        // stack panel (right)
        const sx = 1320, sy = 210, sw = 480, sh = 330;
        d2.panel(sx, sy, sw, sh, { alpha: rA * seg(t, tA - 0.6, 0.6), accent: PAL.cyan });
        d2.text('the rule', sx + 30, sy + 46, { size: 24, weight: 750, color: PAL.cyan, alpha: rA * seg(t, tA - 0.6, 0.6) });
        const rq = seg(t, at('f3', 'Whenever'), 0.6);
        d2.text('X = newest range', sx + 30, sy + 100, { size: 23, weight: 600, alpha: rA * rq });
        d2.text('Y = the range before it', sx + 30, sy + 134, { size: 23, weight: 600, alpha: rA * rq });
        d2.text('if X ≥ Y, count Y:', sx + 30, sy + 180, { size: 24, weight: 800, color: PAL.green, alpha: rA * seg(t, at('f3', 'at least as large'), 0.6) });
        d2.text('Y holds the start point → ½ cycle,', sx + 30, sy + 214, { size: 21, color: PAL.ink, alpha: rA * seg(t, at('f3', 'very first point') - 0.3, 0.6) });
        d2.text('drop only that point', sx + 54, sy + 240, { size: 21, color: PAL.ink2, alpha: rA * seg(t, at('f3', 'very first point') - 0.3, 0.6) });
        d2.text('otherwise → full cycle,', sx + 30, sy + 272, { size: 21, color: PAL.ink, alpha: rA * seg(t, at('f3', 'closed cycle'), 0.6) });
        d2.text('remove its two points', sx + 54, sy + 298, { size: 21, color: PAL.ink2, alpha: rA * seg(t, at('f3', 'remove its'), 0.6) });
        d2.text('left over at the end: half cycles', sx + 30, sy + 322, { size: 20, color: PAL.violet, alpha: rA * seg(t, f4 - 0.3, 0.6) });
        // counted list (right, below)
        const lx = 1320, ly = 570;
        d2.panel(lx, ly, 480, 360, { alpha: rA * seg(t, tA, 0.6) });
        d2.text('counted', lx + 30, ly + 44, { size: 24, weight: 750, alpha: rA * seg(t, tA, 0.6) });
        let row = 0;
        extractions.forEach((e) => {
          const q = seg(t, e.t + 0.15, 0.4);
          if (q <= 0) return;
          const yy = ly + 86 + row * 28;
          const col = e.kind === 'full' ? PAL.green : PAL.violet;
          const r = Math.abs(rev[e.a] - rev[e.b]);
          d2.rect(lx + 30, yy - 14, 300 * r / 90, 16, { fill: rgba(col, 0.6), alpha: rA * q });
          d2.text(`${r.toFixed(1)} MPa`, lx + 40 + 300 * r / 90, yy, { size: 18, weight: 650, color: PAL.ink2, alpha: rA * q });
          d2.text(e.kind === 'full' ? '1' : '½', lx + 450, yy, { size: 20, weight: 800, color: col, align: 'right', alpha: rA * q });
          row++;
        });
      }
      // ---------------------------------------------------- f4: the 3-hour histogram
      const hA = env(t, at('f4', 'For a three-hour') - 0.4, f5 + 0.4, 0.6, 0.6);
      if (hA > 0) {
        d2.fadeRect(hA * 0.75, '#050d16');
        const P = new Plot(d2, { x: 380, y: 260, w: 1200, h: 520, xr: [0, 100], yr: [0, 3] });
        d2.panel(260, 170, 1420, 790, { alpha: hA, accent: PAL.green });
        d2.text(`3-hour sea state: ${Math.round(H.cycles).toLocaleString('en-US')} cycles`, 300, 222, { size: 32, weight: 800, alpha: hA });
        P.axes({ alpha: hA, xticks: [0, 20, 40, 60, 80, 100], yticks: [0, 1, 2, 3], fs: 20, fmty: (v) => (v === 0 ? '1' : `10${'⁰¹²³'[v]}`), xlabel: 'stress range Δσ [MPa]', ylabel: 'cycles (log scale)', ylabelOff: 60 });
        const bp = seg(t, at('f4', 'For a three-hour') + 0.2, 2.0);
        H.n.forEach((c, k) => {
          if (c <= 0) return;
          const q = clamp(bp * H.n.length - k * 0.6);
          if (q <= 0) return;
          const x0 = P.X(H.edges[k]) + 2, x1 = P.X(H.edges[k + 1]) - 2;
          const v = Math.log10(c + 1) * q;
          d2.rect(x0, P.Y(v), x1 - x0, P.Y(0) - P.Y(v), { fill: rgba(PAL.green, 0.7), alpha: hA });
        });
        d2.text('many small cycles, a few large ones', P.X(60), P.Y(2.4), { size: 24, weight: 650, color: PAL.ink2, align: 'center', alpha: hA * bp });
      }
      // ---------------------------------------------------- f5: ranges, not means
      const mA = env(t, f5 - 0.1, ctx.duration, 0.6, 0.5);
      if (mA > 0) {
        heading(d2, 'Ranges, not means', 120, 160, mA, { sub: 'as-welded joints: the residual stress sets the real mean' });
        const P = new Plot(d2, { x: 200, y: 280, w: 760, h: 520, xr: [0, 4], yr: [-120, 420] });
        d2.panel(130, 220, 880, 680, { alpha: mA });
        P.axes({ alpha: mA, xticks: [], yticks: [-100, 0, 100, 200, 300, 400], fs: 18, fmty: (v) => String(v), xlabel: 'time', ylabel: 'stress at the weld toe [MPa]', ylabelOff: 62 });
        const dp = seg(t, f5 + 0.3, 2.0);
        const c1 = [], c2 = [];
        for (let i = 0; i <= 200; i++) {
          const u = i / 200 * 4;
          c1.push([u, 0 + 40 * Math.sin(u * Math.PI * 2)]);
          c2.push([u, 150 + 40 * Math.sin(u * Math.PI * 2)]);
        }
        P.curve(c1, { color: PAL.cyan, width: 3, progress: dp, alpha: mA });
        P.curve(c2, { color: PAL.amber, width: 3, progress: dp, alpha: mA * seg(t, at('f5', 'not mean'), 0.6) });
        const ry = seg(t, at('f5', 'residual stresses') - 0.2, 0.8);
        if (ry > 0) {
          const g = d2.g;
          g.save();
          g.globalAlpha = mA * ry * 0.22;
          g.fillStyle = PAL.red;
          g.fillRect(P.x, P.Y(400), P.w, P.Y(300) - P.Y(400));
          g.restore();
          d2.line(P.x, P.Y(355), P.x + P.w, P.Y(355), { color: PAL.red, width: 2, dash: [10, 6], alpha: mA * ry });
          d2.text('residual stress near yield: the toe sits up here, whatever the nominal mean', P.x + 14, P.Y(355) - 14, { size: 20, weight: 650, color: PAL.red, alpha: mA * ry });
        }
        const sq = seg(t, at('f5', 'full stress range') - 0.3, 0.6);
        for (const [y0, col] of [[0, PAL.cyan], [150, PAL.amber]]) {
          const x = P.X(1.25);
          d2.arrow(x, P.Y(y0 - 40), x, P.Y(y0 + 40), { color: col, width: 3, head: 11, alpha: mA * sq, double: true });
          d2.text('same Δσ', x + 20, P.Y(y0) + 8, { size: 20, weight: 800, color: col, alpha: mA * sq });
        }
        const pq = seg(t, at('f5', 'lock ring') - 0.4, 0.6);
        const f5a = mA * sq * (1 - seg(t, f6 - 0.4, 0.6));
        d2.panel(1080, 300, 720, 340, { alpha: f5a, accent: PAL.green });
        d2.text('same stress range → same damage', 1110, 352, { size: 28, weight: 750, color: PAL.green, alpha: f5a });
        d2.text('for as-welded joints C203 uses the', 1110, 400, { size: 23, color: PAL.ink, alpha: f5a });
        d2.text('full range, whatever the mean', 1110, 432, { size: 23, color: PAL.ink, alpha: f5a });
        const pa = mA * pq * (1 - seg(t, f6 - 0.4, 0.6));
        d2.text('lock-ring preload, weight of the stack:', 1110, 500, { size: 23, weight: 700, color: PAL.ink2, alpha: pa });
        d2.text('no mean-stress effect in the S-N check,', 1110, 534, { size: 23, color: PAL.ink2, alpha: pa });
        d2.text('but they set contact and load sharing', 1110, 568, { size: 23, color: PAL.ink2, alpha: pa * seg(t, at('f5', 'They still matter') - 0.3, 0.6) });
        d2.text('in the global model', 1110, 602, { size: 23, color: PAL.ink2, alpha: pa * seg(t, at('f5', 'They still matter') - 0.3, 0.6) });
        // f6: the exceptions of C203 [2.5]
        const xA = mA * seg(t, f6 - 0.2, 0.7);
        if (xA > 0) {
          d2.panel(1060, 220, 780, 680, { alpha: xA, accent: PAL.violet });
          d2.text('Exceptions', 1090, 270, { size: 30, weight: 750, alpha: xA });
          refChip(d2, 'C203 [2.5]', 1290, 262, xA);
          tex.show('f08fm0', '\\Delta\\sigma_{used} = f_m \\cdot \\Delta\\sigma', 1090, 300, { size: 40, alpha: xA * seg(t, at('f6', 'reduce the stress range') - 0.4, 0.6) });
          const rows = [
            ['base material', 'eq. (2.15)', 'f_m = \\dfrac{\\sigma_t + 0.6\\,|\\sigma_c|}{\\sigma_t + |\\sigma_c|}', '0.8 at zero mean', at('f6', 'base material'), PAL.cyan],
            ['post weld heat treated', 'eq. (2.16)', 'f_m = \\dfrac{\\sigma_t + 0.8\\,|\\sigma_c|}{\\sigma_t + |\\sigma_c|}', '0.9 at zero mean', at('f6', 'heat treated'), PAL.green],
          ];
          rows.forEach(([a, eq, f, z, tt, col], k) => {
            const q = seg(t, tt - 0.3, 0.6);
            const y = 410 + k * 175;
            d2.text(a, 1090, y, { size: 24, weight: 750, color: col, alpha: xA * q });
            d2.text(eq, 1090, y + 30, { size: 18, color: PAL.ink3, alpha: xA * q });
            tex.show(`f08fm${k + 1}`, f, 1390, y - 40, { size: 34, alpha: xA * q });
            d2.text(z, 1090, y + 62, { size: 20, weight: 650, color: PAL.ink2, alpha: xA * q * seg(t, at('f6', 'zero point nine') - 0.3, 0.6) });
          });
          d2.text('σt: max tension, σc: max compression in the cycle', 1090, 770, { size: 19, color: PAL.ink3, alpha: xA * seg(t, at('f6', 'base material'), 0.6) });
          const wq = seg(t, at('f6', 'as-welded, so') - 0.3, 0.6);
          d2.panel(1090, 800, 720, 70, { alpha: xA * wq, accent: PAL.amber, fill: 'rgba(8,20,34,0.95)' });
          d2.text('as-welded (our welds): f_m = 1, the full range', 1116, 846, { size: 24, weight: 750, color: PAL.amber, alpha: xA * wq });
        }
      }
      chainBar(d2, 3, { alpha: seg(t, 1.6, 0.6) * (1 - 0.0) });
      stepCard(d2, t, 3, 'Counting cycles', 'rainflow counting of the stress history');
    },
  };
}

// rerun the three-point (ASTM E1049) rainflow algorithm on the reversal list, recording the order of events
function simulate(r) {
  const stack = [];
  const ev = [];
  for (let i = 0; i < r.length; i++) {
    stack.push(i);
    ev.push({ kind: 'push', i });
    while (stack.length >= 3) {
      const X = Math.abs(r[stack[stack.length - 1]] - r[stack[stack.length - 2]]);
      const Y = Math.abs(r[stack[stack.length - 2]] - r[stack[stack.length - 3]]);
      if (X < Y) break;
      if (stack.length === 3) {
        ev.push({ kind: 'half', a: stack[0], b: stack[1] });
        stack.shift();
      } else {
        const a = stack[stack.length - 3], b = stack[stack.length - 2];
        ev.push({ kind: 'full', a, b });
        const last = stack.pop();
        stack.pop(); stack.pop();
        stack.push(last);
      }
    }
  }
  for (let k = 0; k < stack.length - 1; k++) ev.push({ kind: 'residue', a: stack[k], b: stack[k + 1] });
  return ev;
}

// find a small cycle inside a larger swing in the first 120 s (for the highlight box)
function smallCycle(s, dt) {
  const n = Math.min(s.length, Math.floor(120 / dt));
  const rv = [];
  for (let i = 1; i < n - 1; i++) if ((s[i] - s[i - 1]) * (s[i + 1] - s[i]) < 0) rv.push(i);
  let best = [rv[0], rv[2]], bs = -1;
  for (let k = 1; k < rv.length - 2; k++) {
    const a = s[rv[k - 1]], b = s[rv[k]], c = s[rv[k + 1]], d = s[rv[k + 2]];
    const small = Math.abs(c - b), big = Math.abs(d - a);
    if (small < 0.35 * big && Math.min(a, d) < Math.min(b, c) && Math.max(a, d) > Math.max(b, c)) {
      const score = big - small;
      if (score > bs) { bs = score; best = [rv[k] - 2, rv[k + 1] + 2]; }
    }
  }
  return best;
}
