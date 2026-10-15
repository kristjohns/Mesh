// Step 2, continued: from the moment in the beam model to the nominal stress at a hot spot,
// sigma = M / W with the section modulus of a tube, worked for the conductor girth weld.
import { makeBackdrop } from '../../engine/env.js';
import { divergingCss } from '../../models/hotspotfe.js';
import { keyLine } from '../common.js';
import { chainBar, heading, formulaWalk, texSteps, refChip } from './fcommon.js';
import { PAL, seg, env, ease, clamp, lerp, rgba } from '../../engine/util.js';

export default async function nominal(ctx) {
  const { d2, cue, at, renderer, data, tex } = ctx;
  const F = data.fatigue;
  const N = F.worked.nominal;
  const back = makeBackdrop();
  const s1 = cue('s1'), s2 = cue('s2'), s3 = cue('s3'), s4 = cue('s4');
  const f3 = (v, n = 3) => v.toFixed(n);

  return {
    render(t) {
      back.render(renderer);
      const A = env(t, 0.3, ctx.duration, 0.6, 0.5);
      heading(d2, 'From moment to nominal stress', 110, 150, A, { sub: 'beam theory for a tube in bending' });
      // ------------------------------------------------------------ left: cross-section with the bending stress
      const cx = 420, cy = 480, Ro = 180, Ri = Ro * N.Di / N.D;
      const xA = A * seg(t, s1 - 0.2, 0.8);
      if (xA > 0) {
        d2.panel(80, 210, 680, 790, { alpha: xA });
        const grow = seg(t, at('s1', 'varies linearly') - 0.3, 1.4, ease.inOutSine);
        const g = d2.g;
        g.save();
        g.globalAlpha = xA;
        for (let k = 0; k < 180; k++) {
          const a0 = (k / 180) * Math.PI * 2, a1 = ((k + 1.2) / 180) * Math.PI * 2;
          const x = Math.cos((a0 + a1) / 2);
          g.beginPath();
          g.arc(cx, cy, Ro, a0, a1);
          g.arc(cx, cy, Ri, a1, a0, true);
          g.closePath();
          g.fillStyle = grow > 0 ? divergingCss(-x * 0.95 * grow) : 'rgba(150,170,190,0.5)';
          g.fill();
        }
        g.restore();
        d2.line(cx, cy - Ro - 20, cx, cy + Ro + 20, { color: PAL.ink2, width: 1.5, dash: [8, 6], alpha: xA });
        d2.text('neutral axis', cx + 10, cy + Ro + 26, { size: 19, color: PAL.ink2, alpha: xA });
        d2.momentArrow(cx, cy, Ro + 44, -Math.PI * 0.85, -Math.PI * 0.15, { color: PAL.amber, width: 4, alpha: xA, progress: seg(t, s1 + 0.4, 1.0), glow: PAL.amber });
        d2.text('M', cx, cy - Ro - 64, { size: 32, weight: 800, color: PAL.amber, align: 'center', alpha: xA * seg(t, s1 + 0.8, 0.6) });
        const lq = xA * grow;
        d2.text('tension', cx - Ro - 14, cy - Ro + 10, { size: 22, weight: 700, color: PAL.red, align: 'right', alpha: lq });
        d2.text('compression', cx + Ro + 14, cy - Ro + 10, { size: 22, weight: 700, color: '#6f8cff', alpha: lq });
        // linear stress profile across the diameter, drawn below the section
        const py = cy + Ro + 230, ph = 70;
        const pq = seg(t, at('s1', 'varies linearly'), 1.2);
        if (pq > 0) {
          d2.line(cx - Ro, py, cx + Ro, py, { color: PAL.ink3, width: 1.5, alpha: xA });
          d2.poly([[cx - Ro, py], [cx - Ro, py - ph * pq], [cx, py], [cx + Ro, py + ph * pq], [cx + Ro, py]], { fill: rgba(PAL.amber, 0.22), alpha: xA });
          d2.line(cx - Ro, py - ph * pq, cx + Ro, py + ph * pq, { color: PAL.amber, width: 3, alpha: xA });
        }
        const oq = seg(t, at('s1', 'outer fibre') - 0.3, 0.6);
        if (oq > 0) {
          d2.circle(cx - Ro, cy, 11 + 2 * Math.sin(t * 5), { stroke: PAL.amber, width: 3, alpha: xA * oq, glow: PAL.amber });
          d2.circle(cx - Ro, py - ph, 7, { fill: PAL.amber, alpha: xA * oq });
          d2.line(cx - Ro, cy, cx - Ro, py - ph, { color: PAL.amber, width: 1.5, dash: [4, 5], alpha: xA * oq });
          d2.tag('σ_nom at the outer fibre', cx - Ro + 16, py - ph - 2, { size: 19, color: PAL.amber, alpha: xA * oq, fill: 'rgba(5,14,26,0.9)' });
          d2.text('axial stress across the section', cx, py + ph + 40, { size: 19, color: PAL.ink2, align: 'center', alpha: xA * oq });
        }
        // dimensions once the numbers come
        const dq = seg(t, at('s3', 'outer diameter') - 0.3, 0.6);
        if (dq > 0) {
          d2.dim(cx - Ro, cy + Ro + 76, cx + Ro, cy + Ro + 76, '', { alpha: xA * dq, color: PAL.cyan });
          d2.text(`D = ${(N.D * 1e3).toFixed(1)} mm`, cx, cy + Ro + 66, { size: 21, weight: 700, color: PAL.cyan, align: 'center', alpha: xA * dq });
          d2.text(`t = ${(N.t * 1e3).toFixed(1)} mm`, cx + Ro + 16, cy + 8, { size: 21, weight: 700, color: PAL.cyan, alpha: xA * dq });
        }
      }
      // ------------------------------------------------------------ right: the formulas, term by term
      const fA = A * env(t, s2 - 0.4, s4 - 0.2, 0.6, 0.6);
      const legA = 1 - seg(t, s3 - 0.4, 0.6);
      if (fA > 0) {
        d2.panel(800, 210, 1040, 790, { alpha: fA });
        refChip(d2, 'beam theory', 830, 246, fA);
        const LG = { x: 860, w: 940, gap: 76, symW: 170, size: 24, symSize: 32, alpha: legA };
        formulaWalk(ctx, t, {
          id: 'f06bF1', x: 840, y: 262, size: 54, alpha: fA, tOff: s3 - 0.3,
          parts: [['s', '\\sigma_{nom}'], [null, ' = '], ['M', '\\dfrac{M}{W}']],
          rows: [
            { k: 's', sym: '\\sigma_{nom}', text: 'nominal stress, outer fibre', sub: 'MPa, from the beam model', t: at('s1', 'nominal stress') + 0.3, col: PAL.amber },
            { k: 'M', sym: 'M', text: 'bending moment at the hot spot', sub: 'from the global beam-spring model', t: at('s2', 'bending moment'), col: PAL.orange },
          ],
          legend: { ...LG, y: 560 }, fAlpha: 1,
        });
        const q2 = seg(t, at('s2', 'section modulus, W') - 0.4, 0.6);
        formulaWalk(ctx, t, {
          id: 'f06bF2', x: 1320, y: 262, size: 54, alpha: fA * q2, tOff: s3 - 0.3,
          parts: [['W', 'W'], [null, ' = '], ['I', '\\dfrac{I}{D/2}']],
          rows: [
            { k: 'W', sym: 'W', text: 'section modulus', sub: 'm³', t: at('s2', 'section modulus, W'), col: PAL.cyan },
            { k: 'I', sym: 'I', text: 'second moment of area ÷ distance to the outer fibre', sub: 'D/2: half the outer diameter', t: at('s2', 'second moment'), col: PAL.green },
          ],
          legend: { ...LG, y: 560 + 2 * LG.gap }, fAlpha: 1,
        });
        const q3 = seg(t, at('s2', 'For a tube') - 0.4, 0.6);
        formulaWalk(ctx, t, {
          id: 'f06bF3', x: 840, y: 410, size: 46, alpha: fA * q3, tOff: s3 - 0.3,
          parts: [['I', 'I'], [null, ' = '], ['p', '\\dfrac{\\pi}{64}'], [null, '\\left('], ['D', 'D^4 - D_i^{\\,4}'], [null, '\\right)']],
          rows: [
            { k: ['p', 'D'], sym: 'I', text: 'tube: outer diameter D, inner D_i = D − 2t', sub: 'm⁴', t: at('s2', 'For a tube'), col: PAL.violet },
          ],
          legend: { ...LG, y: 560 + 4 * LG.gap }, fAlpha: 1,
        });
        // worked numbers
        const wA = fA * seg(t, s3 - 0.3, 0.6);
        if (wA > 0) {
          d2.text('conductor girth weld, 36 in pipe', 860, 560, { size: 24, weight: 750, color: PAL.amber, alpha: wA });
          texSteps(ctx, t, 'f06bW', [
            { tex: `D = ${(N.D * 1e3).toFixed(1)}\\ \\mathrm{mm},\\quad t = ${(N.t * 1e3).toFixed(1)}\\ \\mathrm{mm},\\quad D_i = ${(N.Di * 1e3).toFixed(1)}\\ \\mathrm{mm}`, t: at('s3', 'outer diameter'), size: 32, dy: 0 },
            { tex: `I = \\tfrac{\\pi}{64}\\,(0.9144^4 - 0.8382^4) = ${f3(N.I, 5)}\\ \\mathrm{m^4}`, t: at('s3', 'W is') - 1.2, size: 32, dy: 66 },
            { tex: `W = \\dfrac{${f3(N.I, 5)}}{${(N.D / 2).toFixed(4)}} = ${f3(N.W, 4)}\\ \\mathrm{m^3}`, t: at('s3', 'W is'), size: 32, dy: 132 },
            { tex: `M = ${Math.round(N.M / 1e3)}\\ \\mathrm{kNm}\\quad(\\text{flex-joint force } ${Math.round(N.H / 1e3)}\\ \\mathrm{kN})`, t: at('s3', 'the moment at'), size: 32, dy: 222 },
            { tex: `\\sigma_{nom} = \\dfrac{${(N.M / 1e6).toFixed(3)}\\ \\mathrm{MNm}}{${f3(N.W, 4)}\\ \\mathrm{m^3}} = ${N.s_nom.toFixed(1)}\\ \\mathrm{MPa}`, t: at('s3', 'Divided by'), size: 36, col: PAL.amber, dy: 292 },
          ], 860, 590, { alpha: wA, gap: 76 });
        }
      }
      // ------------------------------------------------------------ s4: ranges, and what constant loads do
      const rA = A * seg(t, s4 - 0.3, 0.7);
      if (rA > 0) {
        d2.panel(800, 210, 1040, 790, { alpha: rA });
        tex.show('f06bDs', '\\Delta\\sigma_{nom} = \\dfrac{\\Delta M}{W}', 860, 250, { size: 60, alpha: rA, color: PAL.amber });
        d2.text('linear: a range of moment is a range of stress', 860, 420, { size: 24, weight: 650, color: PAL.ink, alpha: rA });
        // two cycles with the same range and different means
        const P0x = 880, P0y = 480, Pw = 740, Ph = 360;
        const mq = seg(t, at('s4', 'Loads that stay') - 0.3, 0.8);
        const mean2 = 0.55 * mq;
        const Y = (v) => P0y + Ph / 2 - v * Ph * 0.42;
        d2.line(P0x, Y(0), P0x + Pw, Y(0), { color: PAL.ink3, width: 1.2, dash: [6, 6], alpha: rA });
        const pts1 = [], pts2 = [];
        for (let i = 0; i <= 200; i++) {
          const x = P0x + Pw * i / 200, s = 0.5 * Math.sin(i / 200 * Math.PI * 6);
          pts1.push([x, Y(s)]);
          pts2.push([x, Y(s + mean2)]);
        }
        d2.path(pts1, { color: PAL.cyan, width: 3, alpha: rA, progress: seg(t, s4 + 0.2, 1.5) });
        if (mq > 0) {
          d2.path(pts2, { color: PAL.amber, width: 3, alpha: rA * mq });
          d2.text('+ weight, preload: the mean shifts', P0x, Y(mean2 + 0.62), { size: 21, weight: 700, color: PAL.amber, alpha: rA * mq });
          d2.text('dynamic load only', P0x, Y(-0.62) + 22, { size: 21, weight: 700, color: PAL.cyan, alpha: rA * mq });
          const xr = P0x + Pw + 26;
          d2.line(P0x + Pw - 40, Y(0.5), xr + 4, Y(0.5), { color: PAL.cyan, width: 1, dash: [3, 4], alpha: rA * mq });
          d2.line(P0x + Pw - 40, Y(0.5 + mean2), xr + 40, Y(0.5 + mean2), { color: PAL.amber, width: 1, dash: [3, 4], alpha: rA * mq });
          d2.arrow(xr, Y(0.5), xr, Y(-0.5), { color: PAL.cyan, width: 2.5, head: 10, double: true, alpha: rA * mq });
          d2.arrow(xr + 36, Y(0.5 + mean2), xr + 36, Y(-0.5 + mean2), { color: PAL.amber, width: 2.5, head: 10, double: true, alpha: rA * mq });
          d2.text('same', xr + 60, Y(mean2 * 0.5) - 6, { size: 22, weight: 800, color: PAL.ink, alpha: rA * mq });
          d2.text('Δσ', xr + 60, Y(mean2 * 0.5) + 22, { size: 22, weight: 800, color: PAL.ink, alpha: rA * mq });
        }
      }
      keyLine(d2, t, at('s4', 'but they don'), ctx.duration - 0.2, 'Constant loads change the mean stress, not the stress range', { accent: PAL.amber, size: 30, y: 1030 });
      chainBar(d2, 2, { alpha: A });
    },
  };
}
