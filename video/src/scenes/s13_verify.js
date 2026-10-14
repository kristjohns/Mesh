// Chapter 5: verification checklist with real numbers.
import { makeBackdrop } from '../engine/env.js';
import { chapterCard } from './common.js';
import { Plot } from '../engine/draw2d.js';
import { PAL, seg, env, ease, clamp, lerp, rgba } from '../engine/util.js';

export default async function verify(ctx) {
  const { d2, cue, at, renderer, data, tex } = ctx;
  const G = data.global;
  const back = makeBackdrop();
  const v1 = cue('v1'), v2 = cue('v2'), v3 = cue('v3'), v4 = cue('v4');
  const sw = G.template_sweep;
  return {
    render(t) {
      back.render(renderer);
      const A = env(t, v1 - 0.3, ctx.duration, 0.6, 0.5);
      if (A > 0) {
        d2.text('Before you believe a result, check it', 960, 120, { size: 48, weight: 800, align: 'center', alpha: A * seg(t, v1 - 0.3, 0.8) });
        const items = [
          ['Reactions balance the applied loads', 'ΣF = 0, ΣM = 0', at('v2', 'reactions')],
          ['Deformed shape makes sense', 'exaggerate it and look', at('v2', 'deformed shape')],
          ['Result of interest has converged', 'refine · rerun · compare', at('v2', 'converged')],
          ['Contacts open / closed as expected', 'check the contact status', at('v2', 'contacts open')],
        ];
        items.forEach(([a, b, tt], i) => {
          const q = seg(t, tt - 0.2, 0.6, ease.out);
          if (q <= 0) return;
          const y = 200 + i * 120;
          d2.panel(120, y, 820, 100, { alpha: A * q, accent: PAL.green });
          d2.check(175, y + 50, 22, { progress: seg(t, tt + 0.2, 0.8), alpha: A * q });
          d2.text(a, 220, y + 46, { size: 30, weight: 700, alpha: A * q });
          d2.text(b, 220, y + 80, { size: 22, color: PAL.ink2, alpha: A * q });
        });
        // hand calculation
        const hq = seg(t, v3 - 0.1, 0.7, ease.out);
        if (hq > 0) {
          const H = G.handcalc;
          d2.panel(1000, 200, 820, 380, { alpha: A * hq, accent: PAL.cyan });
          d2.text('Hand calculation', 1040, 255, { size: 32, weight: 750, alpha: A * hq });
          d2.text('Hetényi: semi-infinite beam on an elastic foundation', 1040, 292, { size: 22, color: PAL.ink2, alpha: A * hq });
          tex.show('het', 'y_0 = \\dfrac{2H\\lambda}{k} + \\dfrac{2M\\lambda^2}{k},\\qquad \\lambda = \\sqrt[4]{\\dfrac{k}{4EI}}', 1040, 320, { size: 32, alpha: A * hq });
          const nq = seg(t, at('v3', 'matches'), 0.6);
          d2.text('hand calc', 1040, 490, { size: 24, color: PAL.ink2, alpha: A * nq });
          d2.text(`${(H.y0_hetenyi * 1e3).toFixed(2)} mm`, 1040, 532, { size: 36, weight: 800, color: PAL.cyan, alpha: A * nq });
          d2.text('FE, linear springs', 1330, 490, { size: 24, color: PAL.ink2, alpha: A * nq });
          d2.text(`${(H.y0_fe * 1e3).toFixed(2)} mm`, 1330, 532, { size: 36, weight: 800, color: PAL.cyan, alpha: A * nq });
          d2.tag(`Δ = ${(100 * H.diff).toFixed(2)} %`, 1630, 520, { size: 24, alpha: A * seg(t, at('v3', 'tenth of a percent'), 0.5), color: PAL.green });
        }
        // sensitivity
        const sq = seg(t, v4 - 0.1, 0.7, ease.out);
        if (sq > 0) {
          d2.panel(120, 690, 1700, 320, { alpha: A * sq, accent: PAL.amber });
          d2.text('Sensitivity: wellhead deflection at the extreme load', 160, 745, { size: 30, weight: 750, alpha: A * sq });
          const P = new Plot(d2, { x: 600, y: 780, w: 1100, h: 180, xr: [0, 280], yr: [0, 1] });
          const ax = (v) => P.X(v);
          d2.line(ax(0), 960, ax(280), 960, { color: PAL.ink3, width: 1.5, alpha: A * sq });
          for (const v of [0, 50, 100, 150, 200, 250]) d2.text(`${v}`, ax(v), 990, { size: 18, color: PAL.ink2, align: 'center', alpha: A * sq });
          d2.text('mm', ax(280) + 10, 990, { size: 18, color: PAL.ink2, alpha: A * sq });
          const B = G.bounds;
          const rows = [
            ['soil strength (lower – upper bound)', B.UB.u_wh * 1e3, B.LB.u_wh * 1e3, B.BE.u_wh * 1e3, PAL.violet, at('v4', 'soil strength')],
            ['template gap (tied – no contact)', sw.tied[14].u_wh * 1e3, sw.free[14].u_wh * 1e3, sw.gap[14].u_wh * 1e3, PAL.yellow, at('v4', 'gaps')],
          ];
          rows.forEach(([lab, lo, hi, mid, col, tt], i) => {
            const q = seg(t, tt, 0.8, ease.outQuint);
            const y = 820 + i * 70;
            d2.text(lab, 160, y + 10, { size: 24, weight: 650, alpha: A * sq });
            d2.rect(ax(mid) - (ax(mid) - ax(lo)) * q, y - 14, (ax(hi) - ax(lo)) * q, 30, { fill: rgba(col, 0.75), alpha: A * sq });
            d2.line(ax(mid), y - 22, ax(mid), y + 24, { color: PAL.ink, width: 2.5, alpha: A * sq * clamp(q * 3) });
            if (q > 0.9) {
              d2.text(`${Math.round(lo)}`, ax(lo) - 8, y + 9, { size: 20, weight: 700, color: col, align: 'right', alpha: A * sq });
              d2.text(`${Math.round(hi)}`, ax(hi) + 8, y + 9, { size: 20, weight: 700, color: col, alpha: A * sq });
            }
          });
          d2.text('+ pre-load, friction, …', 160, 975, { size: 22, color: PAL.ink2, alpha: A * sq * seg(t, at('v4', 'pre-load'), 0.5) });
          const rq = seg(t, at('v4', 'report a range'), 0.6);
          d2.tag('large spread → report a range, not a single number', 1490, 745, { size: 22, alpha: A * rq, color: PAL.amber, align: 'center' });
        }
      }
      chapterCard(d2, t, 5, 'Verification', 'Check before you believe', { t0: 0, hold: 2.2 });
    },
  };
}
