// Chapter 4c: conductor-soil springs, cement links, welds as shared nodes, load transfer to the local model.
import { makeBackdrop } from '../engine/env.js';
import { keyLine } from './common.js';
import { PAL, seg, env, ease, clamp, lerp, rgba } from '../engine/util.js';

export default async function soilbc(ctx) {
  const { d2, cue, at, renderer } = ctx;
  const back = makeBackdrop();
  const d1 = cue('d1'), d2t = cue('d2'), d3 = cue('d3'), d4 = cue('d4');
  return {
    render(t) {
      back.render(renderer);
      // ---------------------------------------------------------- d1: full spring set
      const aA = env(t, d1 - 0.4, d2t + 0.2, 0.6, 0.5);
      if (aA > 0) {
        d2.text('C · Conductor ↔ soil', 120, 130, { size: 44, weight: 800, color: PAL.teal, alpha: aA });
        const cx = 560, y0 = 300, sy = 20;
        const Y = (z) => y0 - z * sy;
        d2.rect(cx - 330, y0, 660, 31 * sy, { fill: 'rgba(110,98,78,0.35)', alpha: aA });
        const dz = env(t, at('d1', 'reduce the soil strength') - 0.3, d2t + 0.2, 0.5, 0.5);
        d2.rect(cx - 330, y0, 660, 3 * sy, { fill: rgba(PAL.amber, 0.22), alpha: aA * dz });
        d2.text('disturbed zone: reduced strength', cx - 320, y0 + 40, { size: 22, weight: 700, color: PAL.amber, alpha: aA * dz, shadow: true });
        d2.line(cx - 330, y0, cx + 330, y0, { color: '#b9a98a', width: 2.5, alpha: aA });
        d2.text('real mudline', cx - 330, y0 - 12, { size: 20, weight: 700, color: '#b9a98a', alpha: aA * seg(t, at('d1', 'real mudline'), 0.5) });
        d2.line(cx, Y(3), cx, Y(-30), { color: '#9fb3c4', width: 10, alpha: aA });
        const p1 = seg(t, at('d1', 'lateral'), 1.0), p2 = seg(t, at('d1', 'axial'), 1.0), p3 = seg(t, at('d1', 'at the tip'), 0.8), p4 = seg(t, at('d1', 'grounded'), 0.8);
        for (let z = -1; z >= -29; z -= 2) {
          const yy = Y(z);
          for (const s of [-1, 1]) {
            d2.spring(cx + s * 8, yy, cx + s * 160, yy, { color: PAL.teal, width: 2.5, coils: 4, amp: 7, alpha: aA * p1 });
            d2.line(cx + s * 160, yy - 10, cx + s * 160, yy + 10, { color: PAL.ink3, width: 3, alpha: aA * p4 });
            d2.spring(cx + s * 24, yy - 16, cx + s * 24, yy + 16, { color: PAL.violet, width: 2, coils: 3, amp: 5, alpha: aA * p2 });
          }
        }
        for (const s of [-1, 1]) {
          d2.line(cx + s * 160, Y(-0.5), cx + s * 160, Y(-29.5), { color: PAL.ink3, width: 2, alpha: aA * p4 });
          for (let yy = Y(-0.5); yy < Y(-29.5); yy += 14) d2.line(cx + s * 160, yy, cx + s * 172, yy + 9, { color: PAL.ink3, width: 1.2, alpha: aA * p4 });
        }
        d2.spring(cx, Y(-30), cx, Y(-30) + 60, { color: PAL.pink, width: 3, coils: 3, amp: 9, alpha: aA * p3 });
        d2.ground(cx, Y(-30) + 62, 70, { alpha: aA * p3 });
        const items = [
          ['p-y : lateral springs', PAL.teal, p1], ['t-z : axial skin friction', PAL.violet, p2], ['Q-z : end bearing at the tip', PAL.pink, p3], ['far ends grounded', PAL.ink2, p4],
        ];
        items.forEach(([s, c, q], i) => {
          d2.panel(1120, 280 + i * 110, 680, 86, { alpha: aA * q, accent: c });
          d2.text(s, 1160, 334 + i * 110, { size: 30, weight: 700, color: c === PAL.ink2 ? PAL.ink : c, alpha: aA * q });
        });
      }
      // ---------------------------------------------------------- d2: cement links / gaps
      const bA = env(t, d2t + 0.1, d3 + 0.2, 0.6, 0.5);
      if (bA > 0) {
        d2.text('Inside the conductor: cement and gaps', 120, 130, { size: 44, weight: 800, alpha: bA });
        const xo = 520, xi = 700, y0 = 560, sy = 60;
        const Y = (z) => y0 - z * sy;
        d2.line(xo, Y(0.8), xo, Y(-6.5), { color: '#9fb3c4', width: 12, alpha: bA });
        d2.line(xi, Y(1.2), xi, Y(-6.5), { color: '#d2dbe2', width: 8, alpha: bA });
        d2.text('conductor', xo - 20, Y(0.6), { size: 24, weight: 650, color: '#9fb3c4', align: 'right', alpha: bA });
        d2.text('surface casing', xi + 20, Y(1.0), { size: 24, weight: 650, color: PAL.ink, alpha: bA });
        const q1 = seg(t, at('d2', 'lateral links'), 1.0);
        let k = 0;
        for (let z = -0.0; z >= -6; z -= 0.75) {
          const q = clamp(q1 * 10 - k++);
          d2.line(xo + 8, Y(z), lerp(xo + 8, xi - 5, q), Y(z), { color: PAL.amber, width: 5, alpha: bA });
          d2.circle(xo, Y(z), 5, { fill: PAL.ink, alpha: bA * clamp(q * 2) });
          d2.circle(xi, Y(z), 5, { fill: PAL.ink, alpha: bA * clamp(q * 2) });
        }
        d2.line(xo - 60, Y(0), xi + 60, Y(0), { color: PAL.amber, width: 2, dash: [8, 6], alpha: bA * seg(t, at('d2', 'top of cement'), 0.5) });
        d2.text('top of cement', xi + 70, Y(0) + 8, { size: 22, weight: 700, color: PAL.amber, alpha: bA * seg(t, at('d2', 'top of cement'), 0.5) });
        const q2 = seg(t, at('d2', 'gap elements'), 0.6);
        for (const z of [0.4, 0.8]) {
          d2.line(xo + 8, Y(z), xo + 60, Y(z), { color: PAL.cyan, width: 3, alpha: bA * q2 });
          d2.line(xi - 60, Y(z), xi - 5, Y(z), { color: PAL.cyan, width: 3, alpha: bA * q2 });
          d2.line(xo + 60, Y(z) - 10, xo + 60, Y(z) + 10, { color: PAL.cyan, width: 3, alpha: bA * q2 });
          d2.line(xi - 60, Y(z) - 10, xi - 60, Y(z) + 10, { color: PAL.cyan, width: 3, alpha: bA * q2 });
        }
        d2.panel(1060, 300, 760, 120, { alpha: bA * q1, accent: PAL.amber });
        d2.text('Cemented: lateral links (tied DOFs)', 1100, 372, { size: 30, weight: 700, alpha: bA * q1 });
        d2.panel(1060, 460, 760, 120, { alpha: bA * q2, accent: PAL.cyan });
        d2.text('Above the cement: gap elements', 1100, 532, { size: 30, weight: 700, alpha: bA * q2 });
      }
      // ---------------------------------------------------------- d3: welds = shared nodes
      const cA = env(t, d3 + 0.1, d4 + 0.2, 0.6, 0.5);
      if (cA > 0) {
        d2.text('Welds: continuous steel → shared nodes', 960, 150, { size: 44, weight: 800, align: 'center', alpha: cA });
        const pairs = [['conductor', 'conductor housing', 520, at('d3', 'The conductor and its housing')], ['surface casing', 'HP housing', 1400, at('d3', 'the casing and')]];
        pairs.forEach(([a, b2, cx, tt]) => {
          const q = seg(t, tt, 1.2, ease.inOutSine);
          const gap = lerp(80, 0, q);
          d2.line(cx, 700, cx, 500 + gap / 2, { color: '#9fb3c4', width: 12, alpha: cA });
          d2.line(cx, 500 - gap / 2, cx, 300, { color: '#e3edf5', width: 16, alpha: cA });
          d2.circle(cx, 500 + gap / 2, 11, { fill: PAL.amber, alpha: cA });
          d2.circle(cx, 500 - gap / 2, 11, { fill: PAL.amber, alpha: cA });
          if (q > 0.95) d2.circle(cx, 500, 22, { stroke: PAL.amber, width: 3, alpha: cA, glow: PAL.amber });
          d2.text(a, cx + 30, 680, { size: 26, weight: 650, color: PAL.ink2, alpha: cA });
          d2.text(b2, cx + 30, 330, { size: 26, weight: 650, color: PAL.ink, alpha: cA });
          d2.text(q > 0.95 ? 'one shared node' : 'two nodes', cx + 40, 508, { size: 24, weight: 750, color: PAL.amber, alpha: cA });
        });
      }
      // ---------------------------------------------------------- d4: load transfer to the local model
      const dA = env(t, d4 + 0.1, ctx.duration, 0.6, 0.5);
      if (dA > 0) {
        d2.text('Transferring loads to the local model', 960, 130, { size: 44, weight: 800, align: 'center', alpha: dA });
        const panels = [
          { x: 120, title: 'Rigid coupling (RBE2)', col: PAL.red, rigid: true, t: at('d4', 'A rigid coupling') },
          { x: 700, title: 'Distributing coupling (RBE3)', col: PAL.green, rigid: false, t: at('d4', 'distributing coupling') },
        ];
        const bend = 0.5 + 0.5 * Math.sin(t * 1.4);
        panels.forEach((pp) => {
          const q = seg(t, pp.t - 0.3, 0.6, ease.out);
          if (q <= 0) return;
          const a = dA * q;
          d2.panel(pp.x, 210, 540, 650, { alpha: a, accent: pp.col });
          d2.text(pp.title, pp.x + 36, 268, { size: 30, weight: 750, alpha: a });
          // cut face of a tube seen edge-on (end view), deforming
          const cx = pp.x + 270, cy = 520, R = 140;
          const pts = [];
          for (let i = 0; i <= 48; i++) {
            const th = (i / 48) * Math.PI * 2;
            const ov = pp.rigid ? 0 : 0.14 * bend;
            pts.push([cx + R * (1 + ov) * Math.cos(th), cy + R * (1 - ov) * Math.sin(th)]);
          }
          d2.poly(pts, { stroke: '#dbe6ee', width: 4, fill: 'rgba(160,185,205,0.12)', alpha: a });
          // spider
          pts.filter((_, i) => i % 4 === 0).forEach(([x, y]) => d2.line(cx, cy, x, y, { color: pp.col, width: pp.rigid ? 3 : 1.6, dash: pp.rigid ? null : [6, 5], alpha: a * 0.9 }));
          d2.circle(cx, cy, 10, { fill: pp.col, alpha: a });
          d2.momentArrow(cx, cy, 52, -0.8, 0.9, { color: PAL.amber, width: 3, alpha: a, head: 12 });
          d2.text(pp.rigid ? 'cut face forced to stay rigid' : 'face free to deform (ovalise)', pp.x + 36, 760, { size: 24, weight: 650, color: pp.col, alpha: a });
          d2.text(pp.rigid ? '→ artificial stiffness' : '→ loads spread, no added stiffness', pp.x + 36, 800, { size: 22, color: PAL.ink2, alpha: a });
          if (pp.rigid) d2.cross(pp.x + 480, 262, 20, { progress: seg(t, pp.t, 0.8), alpha: a }); else d2.check(pp.x + 480, 262, 20, { progress: seg(t, pp.t, 0.8), alpha: a });
        });
        // St Venant: cut distance
        const sA = dA * seg(t, at('d4', 'place the cut') - 0.3, 0.7);
        if (sA > 0) {
          const x = 1300, w = 520;
          d2.panel(x - 20, 210, w + 40, 650, { alpha: sA, accent: PAL.cyan });
          d2.text('Where to cut', x + 16, 268, { size: 30, weight: 750, alpha: sA });
          d2.rect(x + 200, 330, 120, 420, { fill: 'rgba(160,185,205,0.18)', stroke: '#dbe6ee', width: 2, alpha: sA });
          d2.circle(x + 320, 420, 22, { stroke: PAL.red, width: 3, alpha: sA });
          d2.text('area of interest', x + 350, 428, { size: 22, weight: 650, color: PAL.red, alpha: sA });
          d2.line(x + 180, 750, x + 340, 750, { color: PAL.amber, width: 5, alpha: sA });
          d2.text('cut + coupling', x + 350, 758, { size: 22, weight: 650, color: PAL.amber, alpha: sA });
          d2.dim(x + 140, 430, x + 140, 750, '', { alpha: sA, color: PAL.cyan });
          d2.text('≥ 1–2 D', x + 126, 600, { size: 30, weight: 800, color: PAL.cyan, align: 'right', alpha: sA });
          d2.text('Saint-Venant: local load effects', x + 16, 820, { size: 22, color: PAL.ink2, alpha: sA });
          d2.text('die out within a diameter or two', x + 16, 848, { size: 22, color: PAL.ink2, alpha: sA });
        }
      }
    },
  };
}
