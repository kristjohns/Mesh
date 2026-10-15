// Real loading is irregular -> the C203 chain of six steps.
import { makeBackdrop } from '../../engine/env.js';
import { Plot } from '../../engine/draw2d.js';
import { STEPS, chainBar, glyph } from './fcommon.js';
import { PAL, seg, env, ease, clamp, lerp, rgba } from '../../engine/util.js';

export default async function roadmap(ctx) {
  const { d2, cue, at, renderer, data } = ctx;
  const F = data.fatigue;
  const back = makeBackdrop();
  const r1 = cue('r1'), r2 = cue('r2'), r3 = cue('r3');
  const sig = F.example.s;
  const CARDS = [
    ['Sea states', 'scatter diagram,', 'wave spectra', 'waves', at('r2', 'sea states')],
    ['Stress', 'global + local FE,', 'hot spots, SCFs', 'stress', at('r2', 'stress history')],
    ['Count cycles', 'rainflow', 'counting', 'rainflow', at('r2', 'Count the')],
    ['S-N curve', 'detail, environment,', 'thickness', 'sn', at('r2', 'Pick the')],
    ['Damage', 'Palmgren–Miner', 'sum', 'sum', at('r2', 'Add up')],
    ['Design check', 'design fatigue', 'factor', 'check', at('r2', 'design fatigue factor')],
  ];
  const CW = 268, CH = 300, GAP = 32;
  const x0 = 960 - (6 * CW + 5 * GAP) / 2, y0 = 420;
  // pill centres of the chain strip (same layout as chainBar)
  const pw = STEPS.map((s) => d2.measure(`${s.n}  ${s.short}`, 19, 650, 0.5) + 34);
  const ptot = pw.reduce((p, q) => p + q, 0) + 14 * 5;
  const pc = [];
  { let x = 960 - ptot / 2; pw.forEach((w) => { pc.push([x + w / 2, 52, w]); x += w + 14; }); }

  return {
    sfx: CARDS.map((c) => ({ t: c[4] - 0.1, type: 'click' })),
    render(t) {
      back.render(renderer);
      // ---------------------------------------------- r1: test vs sea
      const aA = env(t, 0.2, r2 + 0.3, 0.6, 0.6);
      if (aA > 0) {
        d2.text('Real loading is irregular', 960, 190, { size: 50, weight: 800, align: 'center', alpha: aA });
        const P1 = new Plot(d2, { x: 190, y: 380, w: 560, h: 300, xr: [0, 1], yr: [-1.3, 1.3] });
        const P2 = new Plot(d2, { x: 1110, y: 380, w: 620, h: 300, xr: [0, 60], yr: [-60, 60] });
        d2.panel(140, 300, 660, 470, { alpha: aA });
        d2.panel(1060, 300, 720, 470, { alpha: aA * seg(t, at('r1', 'nothing like') - 0.3, 0.6) });
        d2.text('laboratory test', 180, 350, { size: 26, weight: 700, color: PAL.cyan, alpha: aA });
        d2.text('constant amplitude', 180, 740, { size: 21, color: PAL.ink2, alpha: aA });
        const p1 = seg(t, 0.5, 2.6, ease.inOutSine);
        const pts1 = [];
        for (let i = 0; i <= 200; i++) pts1.push([i / 200, Math.sin(i / 200 * Math.PI * 8)]);
        P1.curve(pts1, { color: PAL.cyan, width: 3, progress: p1, alpha: aA });
        const qa = aA * seg(t, at('r1', 'nothing like') - 0.3, 0.6);
        d2.text('conductor girth weld, 3-hour sea state', 1100, 350, { size: 26, weight: 700, color: PAL.amber, alpha: qa });
        d2.text('irregular amplitude and period [MPa]', 1100, 740, { size: 21, color: PAL.ink2, alpha: qa });
        const p2 = seg(t, at('r1', 'nothing like') - 0.2, 3.0, ease.inOutSine);
        const pts2 = [];
        for (let i = 0; i < 240; i++) pts2.push([i * 0.25, sig[i]]);
        P2.curve(pts2, { color: PAL.amber, width: 2.6, progress: p2, alpha: qa });
        d2.text('≠', 930, 560, { size: 90, weight: 300, align: 'center', color: PAL.ink2, alpha: qa });
      }
      // ---------------------------------------------- r2: six steps
      const cA = env(t, r2 - 0.4, ctx.duration + 1, 0.5, 0.5);
      const morph = seg(t, r3 + 1.2, 1.4, ease.inOutSine);
      if (cA > 0 && morph < 1) {
        const tf = 1 - seg(t, r3 + 0.6, 0.6);
        d2.text('The fatigue analysis chain', 960, 190, { size: 50, weight: 800, align: 'center', alpha: cA * seg(t, r2 - 0.2, 0.6) * tf });
        d2.text('global analysis + the DNV-RP-C203 fatigue method', 960, 240, { size: 26, weight: 500, color: PAL.ink2, align: 'center', alpha: cA * seg(t, r2, 0.6) * tf });
        const g = d2.g;
        CARDS.forEach(([title, l1, l2, icon, tc], i) => {
          const q = seg(t, tc - 0.3, 0.7, ease.outBack);
          if (q <= 0) return;
          const s = STEPS[i];
          const x = x0 + i * (CW + GAP);
          g.save();
          // fly up and shrink into the chain strip
          const mi = seg(morph, i * 0.06, 0.7, ease.inOutSine);
          const cx = lerp(x + CW / 2, pc[i][0], mi), cy = lerp(y0 + CH / 2, pc[i][1], mi);
          g.translate(cx, cy + (1 - clamp(q)) * 40);
          const sc = lerp(1, pc[i][2] / CW, mi);
          g.scale(sc, lerp(1, 36 / CH, mi));
          g.translate(-(x + CW / 2), -(y0 + CH / 2));
          const a = cA * clamp(q) * (1 - seg(mi, 0.55, 0.45));
          const lit = t > tc && t < tc + 1.6 ? 1 - seg(t, tc + 0.8, 0.8) : 0;
          d2.panel(x, y0, CW, CH, { alpha: a, accent: s.col, fill: lit > 0 ? rgba(s.col, 0.10 + 0.12 * lit) : undefined, border: rgba(s.col, 0.35 + 0.5 * lit) });
          d2.text(String(s.n), x + 28, y0 + 64, { size: 52, weight: 800, color: s.col, alpha: a });
          glyph(d2, icon, x + CW - 70, y0 + 66, 34, s.col, a);
          d2.text(title, x + 28, y0 + 170, { size: 31, weight: 750, alpha: a });
          d2.text(l1, x + 28, y0 + 214, { size: 21, weight: 500, color: PAL.ink2, alpha: a });
          d2.text(l2, x + 28, y0 + 244, { size: 21, weight: 500, color: PAL.ink2, alpha: a });
          g.restore();
          if (i < 5 && morph <= 0) {
            const xa = x + CW + 4, xb = x + CW + GAP - 4, y = y0 + CH / 2;
            const p2 = seg(t, CARDS[i + 1][4] - 0.5, 0.4);
            d2.arrow(xa, y, xb, y, { color: rgba(PAL.ink2, 0.8), width: 2.5, head: 10, alpha: cA * p2 });
          }
        });
        // r2b: where each step lives in the standard
        const CHIPS = [
          [4, '§2.2 Miner sum', 'Section two'], [3, '§2.4 S-N curves', 'S N curves'], [3, '§2.4, §2.5 thickness, mean', 'thickness and mean'],
          [1, '§3 SCFs', 'Section three'], [1, '§4 FE hot spot', 'section four'], [4, '§5 fatigue analysis', 'Section five'],
          [3, 'App. A detail classes', 'Appendix A'], [0, 'global analysis: RP-E104', 'global analysis'], [5, 'DFF: DNV-OS-C101', 'O S, C'],
        ];
        const used = [0, 0, 0, 0, 0, 0];
        const chipA = cA * (1 - seg(t, r3 - 0.2, 0.6));
        if (chipA > 0) {
          CHIPS.forEach(([ci, str, cueW]) => {
            const row = used[ci]++;
            const q = seg(t, at('r2b', cueW) - 0.3, 0.5);
            if (q <= 0) return;
            const cxp = x0 + ci * (CW + GAP) + CW / 2;
            d2.tag(str, cxp, y0 + CH + 40 + row * 44 + (1 - q) * 10, { size: 16, color: STEPS[ci].col, align: 'center', alpha: chipA * q, fill: 'rgba(5,14,26,0.92)', ls: 0.4 });
          });
        }
        // a pulse running along the chain during r3
        const pr = seg(t, r3 - 0.3, 1.5, ease.inOutSine);
        if (pr > 0 && pr < 1 && morph <= 0) {
          const xp = lerp(x0, x0 + 6 * CW + 5 * GAP, pr);
          const g2 = d2.g;
          g2.save();
          const grd = g2.createLinearGradient(xp - 160, 0, xp + 20, 0);
          grd.addColorStop(0, 'rgba(76,201,240,0)');
          grd.addColorStop(1, 'rgba(76,201,240,0.35)');
          g2.fillStyle = grd;
          g2.fillRect(xp - 160, y0 - 6, 180, CH + 12);
          g2.restore();
        }
      }
      if (morph > 0) chainBar(d2, 0, { alpha: seg(morph, 0.6, 0.4) * cA });
      const wa = seg(t, at('r3', 'real wellhead'), 0.8) * (1 - seg(t, ctx.duration - 0.6, 0.6));
      d2.text('…on a real wellhead', 960, 560, { size: 46, weight: 700, align: 'center', color: PAL.ink, alpha: wa * morph });
    },
  };
}
