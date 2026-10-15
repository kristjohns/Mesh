// What moves the answer: stress level, girth-weld misalignment, environment.
import { makeBackdrop } from '../../engine/env.js';
import { Plot } from '../../engine/draw2d.js';
import { keyLine } from '../common.js';
import { heading, fmtInt } from './fcommon.js';
import { PAL, seg, env, ease, clamp, lerp, rgba } from '../../engine/util.js';

export default async function sensitivity(ctx) {
  const { d2, cue, at, renderer, data } = ctx;
  const F = data.fatigue;
  const back = makeBackdrop();
  const x1 = cue('x1'), x2 = cue('x2'), x3 = cue('x3'), x4 = cue('x4');
  const S = F.sens;
  const DFF = F.dff, PLAN = F.plan_days;
  const base = F.damage.cg.life_days;

  return {
    render(t) {
      back.render(renderer);
      const A = env(t, 0.3, ctx.duration, 0.6, 0.5);
      heading(d2, 'What moves the answer?', 110, 130, A, { sub: 'governing detail: conductor girth weld' });
      // ------------------------------------------------ 1: stress
      const a1 = A * seg(t, x1 - 0.2, 0.7);
      if (a1 > 0) {
        d2.panel(80, 190, 570, 720, { alpha: a1, accent: PAL.amber });
        d2.text('Stress level', 110, 240, { size: 28, weight: 750, alpha: a1 });
        d2.text('life ∝ 1 / Δσ³, and 1 / Δσ⁵ for small cycles', 110, 274, { size: 21, color: PAL.ink2, alpha: a1 });
        const P = new Plot(d2, { x: 190, y: 330, w: 420, h: 440, xr: [0.8, 1.3], yr: [0, 4500] });
        P.axes({ alpha: a1, xticks: [0.8, 0.9, 1.0, 1.1, 1.2, 1.3], yticks: [0, 1000, 2000, 3000, 4000], fs: 17, fmtx: (v) => `${Math.round((v - 1) * 100) > 0 ? '+' : ''}${Math.round((v - 1) * 100)} %`, fmty: (v) => fmtInt(v), xlabel: 'change in stress', ylabel: 'life [days]', ylabelOff: 62 });
        const q = seg(t, x1, 2.0);
        P.curve(S.stress, { color: PAL.amber, width: 4, progress: q, alpha: a1 });
        P.points([[1.0, base]], { color: PAL.ink, r: 8, progress: q, alpha: a1 });
        const mq = seg(t, at('x1', 'ten percent more') - 0.2, 0.8);
        if (mq > 0) {
          const l11 = S.stress.find((p) => Math.abs(p[0] - 1.1) < 1e-6)[1];
          d2.line(P.X(1.0), P.Y(base), P.X(1.1), P.Y(base), { color: PAL.ink2, width: 1.5, dash: [5, 5], alpha: a1 * mq });
          d2.arrow(P.X(1.1), P.Y(base), P.X(1.1), P.Y(l11), { color: PAL.red, width: 3, head: 12, alpha: a1 * mq });
          d2.circle(P.X(1.1), P.Y(l11), 8, { fill: PAL.red, alpha: a1 * mq });
          d2.text(`+10 % stress → ${Math.round((l11 / base - 1) * 100)} % life`, 110, 860, { size: 26, weight: 800, color: PAL.red, alpha: a1 * mq });
        }
      }
      // ------------------------------------------------ 2: misalignment
      const a2 = A * seg(t, x2 - 0.2, 0.7);
      if (a2 > 0) {
        d2.panel(675, 190, 570, 720, { alpha: a2, accent: PAL.cyan });
        d2.text('Girth weld misalignment', 705, 240, { size: 28, weight: 750, alpha: a2 });
        d2.text('allowable days with DFF 10', 705, 274, { size: 21, color: PAL.ink2, alpha: a2 });
        const P = new Plot(d2, { x: 785, y: 330, w: 420, h: 440, xr: [0, 12], yr: [0, 350] });
        P.axes({ alpha: a2, xticks: [0, 2, 4, 6, 8, 10, 12], yticks: [0, 100, 200, 300], fs: 17, fmty: (v) => String(v), xlabel: 'hi-lo misalignment δm [mm]', ylabel: 'allowable days', ylabelOff: 56 });
        const pts = S.misalign.map(([dm, scf, life]) => [dm, life / DFF]);
        const q = seg(t, x2 + 0.2, 2.0);
        P.clipBegin();
        P.curve(pts, { color: PAL.cyan, width: 4, progress: q, alpha: a2 });
        P.clipEnd();
        d2.line(P.X(0), P.Y(PLAN), P.X(12), P.Y(PLAN), { color: PAL.ink, width: 2, dash: [9, 6], alpha: a2 });
        d2.text(`planned ${PLAN} days`, P.X(0) + 6, P.Y(PLAN) - 10, { size: 18, weight: 700, color: PAL.ink, alpha: a2 });
        const p6 = pts.find((p) => p[0] === 6), p10 = pts.find((p) => p[0] === 8);
        d2.circle(P.X(6), P.Y(p6[1]), 9, { fill: PAL.green, alpha: a2 * q });
        d2.text(`6 mm: ${Math.round(p6[1])} d`, P.X(6) + 14, P.Y(p6[1]) - 12, { size: 20, weight: 800, color: PAL.green, alpha: a2 * q });
        const fq = seg(t, at('x2', 'Eight millimetres') - 0.2, 0.8);
        if (fq > 0) {
          d2.circle(P.X(8), P.Y(p10[1]), 9, { fill: PAL.red, alpha: a2 * fq, glow: PAL.red });
          d2.text(`8 mm: ${Math.round(p10[1])} d`, P.X(8) + 12, P.Y(p10[1]) - 16, { size: 20, weight: 800, color: PAL.red, alpha: a2 * fq });
          // the same joint welded on site: S-N class E instead of D
          const eq = seg(t, at('x2', 'E detail') - 0.3, 0.8);
          const lE = S.class_E / DFF;
          d2.poly([[P.X(6), P.Y(lE) - 11], [P.X(6) + 11, P.Y(lE)], [P.X(6), P.Y(lE) + 11], [P.X(6) - 11, P.Y(lE)]], { fill: PAL.orange, alpha: a2 * eq });
          d2.text(`site weld, class E: ${Math.round(lE)} d`, P.X(6) + 20, P.Y(lE) + 44, { size: 20, weight: 800, color: PAL.orange, align: 'center', alpha: a2 * eq });
          const fl = seg(t, at('x2', 'fail the check') - 0.2, 0.6);
          d2.cross(735, 856, 18, { progress: fl, alpha: a2 });
          d2.text('fails the check', 765, 866, { size: 26, weight: 800, color: PAL.red, alpha: a2 * fl });
        }
      }
      // ------------------------------------------------ 3: environment
      const a3 = A * seg(t, x3 - 0.2, 0.7);
      if (a3 > 0) {
        d2.panel(1270, 190, 570, 720, { alpha: a3, accent: PAL.red });
        d2.text('Environment', 1300, 240, { size: 28, weight: 750, alpha: a3 });
        d2.text('calculated life, days', 1300, 274, { size: 21, color: PAL.ink2, alpha: a3 });
        const E = F.env_life;
        const items = [['in air', E.air, PAL.cyan], ['seawater + CP', E.cp, PAL.amber], ['free corrosion', E.fc, PAL.red]];
        items.forEach(([lab, v, col], k) => {
          const q = seg(t, x3 + 0.2 + k * 0.4, 0.8, ease.out);
          const y = 360 + k * 170;
          d2.text(lab, 1300, y, { size: 24, weight: 700, alpha: a3 * clamp(q * 2) });
          d2.rect(1300, y + 20, 440 * v / 3300 * q, 46, { fill: rgba(col, 0.8), alpha: a3 });
          d2.text(fmtInt(v), 1310 + 440 * v / 3300 * q, y + 54, { size: 24, weight: 800, color: col, alpha: a3 * clamp(q * 2 - 1) });
        });
        const hq = seg(t, at('x3', 'half the life') - 0.3, 0.6);
        d2.text(`without CP: ${Math.round(E.fc / E.cp * 100)} % of the life`, 1300, 866, { size: 26, weight: 800, color: PAL.red, alpha: a3 * hq });
      }
      keyLine(d2, t, x4 - 0.1, ctx.duration - 0.2, 'Report the life together with the assumptions that drive it', { accent: PAL.green, size: 32, y: 1000 });
    },
  };
}
