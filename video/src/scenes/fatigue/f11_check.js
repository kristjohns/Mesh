// Step 6: design fatigue factor, results for the three hot spots, the governing weld.
import { makeBackdrop } from '../../engine/env.js';
import { drawGlobal } from '../globaldiag.js';
import { chainBar, stepCard, heading, fmtInt } from './fcommon.js';
import { PAL, seg, env, ease, clamp, lerp, rgba } from '../../engine/util.js';

const HS_COL = { hp: PAL.violet, lp: PAL.cyan, cg: PAL.amber };

export default async function check(ctx) {
  const { d2, cue, at, renderer, data, tex } = ctx;
  const F = data.fatigue;
  const back = makeBackdrop();
  const k1 = cue('k1'), k2 = cue('k2'), k3 = cue('k3'), k4 = cue('k4');
  const DFF = F.dff, PLAN = F.plan_days;
  const rows = [
    { id: 'hp', L: 'A', name: 'HP housing weld', sub: 'hot spot SCF 1.60 · casing 15.9 mm', tt: at('k3', 'high-pressure housing') },
    { id: 'lp', L: 'B', name: 'Conductor housing weld', sub: `hot spot SCF ${F.scf.lp.toFixed(2)}, inside · 38.1 mm`, tt: at('k3', 'conductor housing weld') },
    { id: 'cg', L: 'C', name: 'Conductor girth weld', sub: `misalignment SCF ${F.scf.cg.toFixed(2)} · S-N class D · 3 m below mudline`, tt: at('k3', 'governing') },
  ].map((r) => ({ ...r, life: F.damage[r.id].life_days }));
  const gov = rows[2];
  const springZ = [];
  for (let z = -0.5; z >= -12; z -= 1.5) springZ.push(z);

  return {
    sfx: [{ t: 0.1, type: 'chapter' }, { t: at('k4', 'passes') + 0.2, type: 'hit' }],
    render(t) {
      back.render(renderer);
      // ------------------------------------------------------------ k1: why a factor
      const aA = env(t, 1.6, k3 - 0.2, 0.6, 0.6);
      if (aA > 0) {
        heading(d2, 'Why a design fatigue factor?', 110, 150, aA, { sub: 'the calculation is only as certain as its inputs' });
        const items = [['loads', 'riser analysis, sea states', at('k1', 'the loads')], ['soil', 'p-y curves, disturbance', at('k1', 'the soil')], ['fabrication', 'misalignment, weld quality', at('k1', 'fabrication')]];
        items.forEach(([a, b, tt], i) => {
          const q = seg(t, tt - 0.2, 0.6, ease.outBack);
          const x = 120 + i * 310;
          d2.panel(x, 230, 290, 170, { alpha: aA * clamp(q), accent: PAL.red });
          d2.warn(x + 50, 290, 18, { alpha: aA * clamp(q) });
          d2.text(a, x + 86, 300, { size: 28, weight: 750, alpha: aA * clamp(q) });
          d2.text(b, x + 30, 360, { size: 19, color: PAL.ink2, alpha: aA * clamp(q) });
        });
        const fq = seg(t, at('k1', 'design fatigue factor') - 0.3, 0.7);
        d2.panel(1060, 230, 760, 170, { alpha: aA * fq, accent: PAL.red });
        tex.show('f11dff', 'DFF \\cdot D \\;\\le\\; 1', 1100, 262, { size: 52, alpha: aA * fq });
        d2.text('⇔  fatigue life ≥ DFF × service time', 1100, 378, { size: 24, weight: 650, color: PAL.ink2, alpha: aA * seg(t, at('k1', 'must stay below') - 0.2, 0.6) });
        // ------------------------------------------------------ k2: the scale of DFF values
        const sA = aA * seg(t, k2 - 0.3, 0.7);
        if (sA > 0) {
          d2.panel(110, 460, 1710, 520, { alpha: sA });
          d2.text('Typical design fatigue factors', 150, 515, { size: 30, weight: 750, alpha: sA });
          d2.text('set by the governing design standard, not by C203 (e.g. DNV-OS-C101, NORSOK N-001)', 150, 552, { size: 20, color: PAL.ink2, alpha: sA });
          const X = (v) => 260 + 1380 * (Math.log10(v) / Math.log10(10));
          const y = 720;
          d2.line(X(1), y, X(10), y, { color: PAL.ink2, width: 3, alpha: sA });
          [1, 2, 3, 10].forEach((v) => {
            d2.line(X(v), y - 12, X(v), y + 12, { color: PAL.ink2, width: 3, alpha: sA });
            d2.text(String(v), X(v), y + 52, { size: 34, weight: 800, align: 'center', alpha: sA });
          });
          const g = d2.g;
          g.save();
          const grd = g.createLinearGradient(X(1), 0, X(10), 0);
          grd.addColorStop(0, 'rgba(61,220,151,0.55)');
          grd.addColorStop(0.5, 'rgba(255,183,3,0.55)');
          grd.addColorStop(1, 'rgba(239,71,111,0.65)');
          g.globalAlpha = sA;
          g.fillStyle = grd;
          g.fillRect(X(1), y - 6, X(10) - X(1), 12);
          g.restore();
          const q1 = seg(t, at('k2', 'found and repaired') - 0.4, 0.6);
          d2.text('can be inspected and repaired,', X(1) - 40, 640, { size: 22, weight: 650, color: PAL.green, alpha: sA * q1 });
          d2.text('limited consequences', X(1) - 40, 668, { size: 22, weight: 650, color: PAL.green, alpha: sA * q1 });
          const q2 = seg(t, at('k2', 'what happens') - 0.3, 0.6);
          d2.text('cannot be inspected,', X(10) + 40, 640, { size: 22, weight: 650, color: PAL.red, align: 'right', alpha: sA * q2 });
          d2.text('serious consequences', X(10) + 40, 668, { size: 22, weight: 650, color: PAL.red, align: 'right', alpha: sA * q2 });
          const mq = seg(t, at('k2', 'A conductor') - 0.2, 1.2, ease.inOutSine);
          if (mq > 0) {
            const xm = lerp(X(1), X(10), mq);
            d2.poly([[xm, y - 20], [xm - 16, y - 46], [xm + 16, y - 46]], { fill: PAL.amber, alpha: sA });
            const dq = seg(t, at('k2', 'so we use ten') - 0.3, 0.6);
            d2.panel(X(10) - 520, 810, 560, 130, { alpha: sA * dq, accent: PAL.amber });
            d2.text('conductor, 3 m below the mudline', X(10) - 490, 860, { size: 24, weight: 700, alpha: sA * dq });
            d2.text('no inspection, well integrity at stake', X(10) - 490, 894, { size: 20, color: PAL.ink2, alpha: sA * dq });
            d2.text('DFF = 10', X(10) - 490, 928, { size: 26, weight: 800, color: PAL.amber, alpha: sA * dq });
          }
        }
      }
      // ------------------------------------------------------------ k3/k4: results
      const rA = env(t, k3 - 0.3, ctx.duration, 0.6, 0.5);
      if (rA > 0) {
        heading(d2, 'Results', 110, 150, rA, { sub: 'days of riser-connected operation' });
        // left: the stack with the three hot spots
        d2.panel(90, 210, 470, 790, { alpha: rA });
        const glow = seg(t, at('k4', 'notice which weld') - 0.3, 0.6);
        const geo = drawGlobal(d2, { x: 330, y0: 520, sy: 34, syUp: 1.0, zTop: 8.5, zBot: -13, alpha: rA, soilW: 220, springs: true, springZ, springL: 60,
          bop: true, bopH: 4.6, bopW: 22, breakLabel: false, template: { gapPx: 12, inner: 14, label: '', alpha: 1 } });
        [['A', 1.2, 'hp'], ['B', 0.8, 'lp'], ['C', -3.0, 'cg']].forEach(([L, z, id]) => {
          const x = geo.X(z), y = geo.Y(z);
          const xs = id === 'hp' ? x + 30 : x - 30;
          const big = id === 'cg' ? 1 + glow * (0.35 + 0.15 * Math.sin(t * 5)) : 1;
          d2.circle(xs, y, 15 * big, { fill: rgba(HS_COL[id], 0.25 + 0.4 * (id === 'cg' ? glow : 0)), stroke: HS_COL[id], width: 2.5, alpha: rA, glow: id === 'cg' && glow > 0 ? HS_COL[id] : null });
          d2.text(L, xs, y + 7, { size: 18, weight: 800, color: id === 'cg' && glow > 0.5 ? '#08131f' : HS_COL[id], align: 'center', alpha: rA });
        });
        d2.text('out of sight,', 120, 930, { size: 22, weight: 700, color: PAL.amber, alpha: rA * glow });
        d2.text('below the seabed', 120, 958, { size: 22, weight: 700, color: PAL.amber, alpha: rA * glow });
        // right: bars on a log scale of days
        const X = (d) => 900 + 880 * (Math.log10(d) - 1) / 4;
        d2.panel(600, 210, 1230, 790, { alpha: rA });
        [10, 100, 1000, 10000, 100000].forEach((v) => {
          d2.line(X(v), 260, X(v), 880, { color: 'rgba(120,160,200,0.15)', width: 1, alpha: rA });
          d2.text(fmtInt(v), X(v), 912, { size: 18, color: PAL.ink2, align: 'center', alpha: rA });
        });
        d2.text('days (log scale)', X(1000), 948, { size: 20, weight: 600, color: PAL.ink2, align: 'center', alpha: rA });
        const div = seg(t, at('k3', 'with the design fatigue factor') - 0.4, 1.4, ease.inOutSine);
        rows.forEach((r, k) => {
          const y = 320 + k * 200;
          const q = seg(t, r.tt - 0.3, 1.0, ease.out);
          const col = HS_COL[r.id];
          d2.circle(650, y + 4, 20, { fill: rgba(col, 0.25), stroke: col, width: 2.5, alpha: rA * clamp(q * 3) });
          d2.text(r.L, 650, y + 12, { size: 20, weight: 800, color: col, align: 'center', alpha: rA * clamp(q * 3) });
          d2.text(r.name, 684, y + 2, { size: 23, weight: 750, alpha: rA * clamp(q * 3) });
          d2.text(r.sub, 684, y + 30, { size: 16, color: PAL.ink2, alpha: rA * clamp(q * 3) });
          if (q <= 0) return;
          const life = r.life;
          const allow = life / DFF;
          // calculated life (outline) and allowable (solid)
          const xl = X(Math.pow(10, 1 + (Math.log10(life) - 1) * q));
          d2.rect(X(10), y + 52, xl - X(10), 34, { stroke: col, width: 2, fill: rgba(col, 0.18), alpha: rA });
          d2.text(`${fmtInt(life)} d calculated`, xl + 10, y + 78, { size: 19, weight: 650, color: PAL.ink2, alpha: rA * clamp(q * 2 - 1) });
          if (div > 0) {
            const xa = X(Math.pow(10, lerp(Math.log10(life), Math.log10(allow), div)));
            d2.rect(X(10), y + 94, xa - X(10), 40, { fill: rgba(col, 0.85), alpha: rA });
            d2.text(`${fmtInt(allow)} d allowed`, xa + 10, y + 124, { size: 24, weight: 800, color: col, alpha: rA * seg(div, 0.7, 0.3) });
          }
        });
        if (div > 0.3) d2.text(`÷ DFF ${DFF}`, X(30), 296, { size: 26, weight: 800, color: PAL.red, align: 'center', alpha: rA * seg(div, 0.3, 0.4) });
        // planned campaign and verdict
        const pq = seg(t, at('k4', 'hundred and twenty') - 0.3, 0.8);
        if (pq > 0) {
          const xp = X(PLAN);
          d2.line(xp, 250, xp, 250 + 640 * pq, { color: PAL.ink, width: 3, dash: [10, 6], alpha: rA });
          d2.tag(`planned: ${PLAN} days`, xp, 248, { size: 20, color: PAL.ink, align: 'center', alpha: rA * pq, fill: 'rgba(5,14,26,0.95)' });
        }
        const vq = seg(t, at('k4', 'passes') - 0.1, 0.6, ease.outBack);
        if (vq > 0) {
          const u = PLAN / (gov.life / DFF);
          const px = 1530, py = 226;
          d2.panel(px, py, 280, 92, { alpha: rA * clamp(vq), accent: PAL.green, fill: 'rgba(10,40,30,0.92)' });
          d2.check(px + 46, py + 46, 24, { progress: vq, alpha: rA });
          d2.text('PASS', px + 86, py + 42, { size: 32, weight: 800, color: PAL.green, alpha: rA * clamp(vq) });
          d2.text(`utilisation ${Math.round(u * 100)} %`, px + 86, py + 74, { size: 22, weight: 700, color: u > 0.9 ? PAL.amber : PAL.ink, alpha: rA * clamp(vq) });
        }
      }
      chainBar(d2, 6, { alpha: seg(t, 1.6, 0.6) });
      stepCard(d2, t, 6, 'The design check', 'design fatigue factor and fatigue life');
    },
  };
}
