// What if the margin is too thin? The levers C203 offers for the governing girth weld: the detail class,
// tolerances, grinding flush (C1, delta0 = 0), weld toe improvement (Table 7-1) and their limits.
import { makeBackdrop } from '../../engine/env.js';
import { keyLine } from '../common.js';
import { heading, refChip, fmtInt } from './fcommon.js';
import { PAL, seg, env, ease, clamp, lerp, rgba } from '../../engine/util.js';

export default async function improve(ctx) {
  const { d2, cue, at, renderer, data, tex } = ctx;
  const F = data.fatigue;
  const I = F.sens.improve, DFF = F.dff, PLAN = F.plan_days;
  const back = makeBackdrop();
  const i1 = cue('i1'), i2 = cue('i2'), i3 = cue('i3'), i4 = cue('i4'), i5 = cue('i5');
  const bars = [
    { lab: 'as designed', sub: 'shop weld (D), 6 mm hi-lo', v: I.base / DFF, col: PAL.amber, t: i1 + 1.0 },
    { lab: 'welded on site', sub: 'class E', v: I.site_E / DFF, col: PAL.red, t: at('i2', 'not an E') - 0.4 },
    { lab: 'tighter tolerance', sub: '4 mm hi-lo', v: I.tol4 / DFF, col: PAL.green, t: at('i2', 'tighten the tolerance') },
    { lab: 'ground flush + NDT', sub: `C1, δ0 = 0, SCF ${I.scf39_flush.toFixed(2)}`, v: I.flush_C1 / DFF, col: PAL.cyan, t: at('i3', 'curve C one') - 0.3 },
    { lab: 'toe grinding', sub: '× 3.5 on life, k = 0.15: a reserve', v: I.toe_grind / DFF, col: PAL.violet, t: at('i4', 'three and a half') - 0.4, hatch: true },
  ];
  const X0 = 400, XW = 520, VMAX = 520;
  const X = (v) => X0 + XW * v / VMAX;

  return {
    render(t) {
      back.render(renderer);
      const A = env(t, 0.3, ctx.duration, 0.6, 0.5);
      heading(d2, 'Buying back margin', 110, 150, A, { sub: 'options in DNV-RP-C203 for the conductor girth weld' });
      // ------------------------------------------------------------ left: allowable days per option
      d2.panel(80, 210, 900, 800, { alpha: A });
      d2.text('allowable days with DFF 10', 110, 256, { size: 23, weight: 750, alpha: A });
      [0, 100, 200, 300, 400, 500].forEach((v) => {
        d2.line(X(v), 290, X(v), 900, { color: 'rgba(120,160,200,0.14)', width: 1, alpha: A });
        d2.text(String(v), X(v), 932, { size: 17, color: PAL.ink2, align: 'center', alpha: A });
      });
      d2.text('days', X(250), 966, { size: 18, color: PAL.ink2, align: 'center', alpha: A });
      bars.forEach((b, k) => {
        const q = seg(t, b.t - 0.2, 0.9, ease.out);
        if (q <= 0) return;
        const y = 320 + k * 116;
        d2.text(b.lab, 110, y + 26, { size: 23, weight: 750, color: b.col, alpha: A * clamp(q * 2) });
        d2.text(b.sub, 110, y + 54, { size: 17, color: PAL.ink2, alpha: A * clamp(q * 2) });
        const w = X(b.v * q) - X0;
        d2.rect(X0, y + 8, w, 44, { fill: rgba(b.col, b.hatch ? 0.35 : 0.8), alpha: A });
        if (b.hatch) {
          const g = d2.g;
          g.save();
          g.globalAlpha = A * 0.7;
          g.beginPath(); g.rect(X0, y + 8, w, 44); g.clip();
          g.strokeStyle = b.col; g.lineWidth = 2;
          for (let x = X0 - 60; x < X0 + w + 60; x += 14) { g.beginPath(); g.moveTo(x, y + 52); g.lineTo(x + 44, y + 8); g.stroke(); }
          g.restore();
        }
        d2.text(`${Math.round(b.v)} d`, Math.max(X0 + w, b.v < PLAN ? X(PLAN) + 4 : 0) + 10, y + 40, { size: 22, weight: 800, color: b.col, alpha: A * clamp(q * 2 - 1) });
      });
      const pq = seg(t, i1 + 1.6, 0.8);
      d2.line(X(PLAN), 290, X(PLAN), 290 + 610 * pq, { color: PAL.ink, width: 2.5, dash: [9, 6], alpha: A });
      d2.tag(`planned ${PLAN} d`, X(PLAN), 286, { size: 17, color: PAL.ink, align: 'center', alpha: A * pq, fill: 'rgba(5,14,26,0.95)' });
      // ------------------------------------------------------------ right: the levers and their limits
      d2.panel(1000, 210, 840, 800, { alpha: A });
      const cards = [
        { n: '1', title: 'the detail and its tolerances', col: PAL.green, t: i2 - 0.2, lines: [
          ['shop weld, pipe rotated: D, not E', at('i2', 'Specify shop'), '[3.3.7.3], Table A-9'],
          ['hi-lo enters the SCF directly', at('i2', 'tighten the tolerance'), 'eq. (3.9)'],
        ] },
        { n: '2', title: 'grind flush on both sides', col: PAL.cyan, t: i3 - 0.2, lines: [
          ['proven free of defects: curve C1', at('i3', 'curve C one') - 0.3, 'Table A-9, [7.3.2]'],
          ['but δ0 = 0: the full misalignment counts', at('i3', 'delta nought becomes') - 0.3, 'Table 3-1'],
        ] },
        { n: '3', title: 'improve the weld toe', col: PAL.violet, t: i4 - 0.2, lines: [
          ['grinding, TIG × 3.5, hammer peening × 4', at('i4', 'three and a half') - 0.3, 'Table 7-1, fy > 350 MPa'],
          ['grinding: keep it as a reserve', at('i4', 'as a reserve') - 0.4, '[7.3.1]'],
          ['TIG: not for general design use; peening:', at('i4', 'T I G dressing is') - 0.3, '[7.4], [7.5]'],
          ['only without substantial consequences', at('i4', 'hammer peening is only') - 0.3, ''],
        ] },
        { n: '4', title: 'limits', col: PAL.red, t: i5 - 0.2, lines: [
          ['toe improvement does nothing for a root crack', at('i5', 'root of a one-sided') - 0.3, '[7.1]'],
          ['life < 15 years, severe consequences:', at('i5', 'under fifteen years') - 0.3, '[2.1.2]'],
          ['refine the analysis, or fracture mechanics', at('i5', 'fracture mechanics') - 0.3, ''],
        ] },
      ];
      let y = 250;
      cards.forEach((c) => {
        const q = seg(t, c.t, 0.6);
        const h = 58 + c.lines.length * 44;
        if (q > 0) {
          d2.rect(1024, y, 5, h - 16, { fill: c.col, alpha: A * q });
          d2.text(`${c.n} · ${c.title}`, 1046, y + 30, { size: 25, weight: 800, color: c.col, alpha: A * q });
          c.lines.forEach(([s, tt, ref], k) => {
            const lq = seg(t, tt, 0.6);
            d2.text(s, 1046, y + 72 + k * 44, { size: 21, weight: 600, alpha: A * q * lq });
            if (ref) d2.text(ref, 1814, y + 72 + k * 44, { size: 16, color: PAL.ink3, align: 'right', alpha: A * q * lq });
          });
        }
        y += h;
      });
      keyLine(d2, t, at('i5', 'Often the best') - 0.2, ctx.duration - 0.2, 'The best lever: a lower stress range, by design', { accent: PAL.green, size: 30, y: 1046 });
    },
  };
}
