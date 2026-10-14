// Outro: back to the seabed, the chain recap, end card.
import { makeWorld, makeSite, updateWorld } from '../common.js';
import { cameraPath } from '../../engine/env.js';
import { STEPS, glyph } from './fcommon.js';
import { PAL, seg, env, ease, clamp, lerp, rgba } from '../../engine/util.js';

export default async function outro(ctx) {
  const { d2, cue, at } = ctx;
  const w = makeWorld(ctx, { water: { density: 0.02 } });
  makeSite(ctx, w, { riserTop: 200 });
  const o1 = cue('o1'), o2 = cue('o2');
  const cam = cameraPath(w.camera, [
    { t: 0, orbit: [32, 35, 13], center: [1, 3, -1], fov: 40 },
    { t: ctx.duration, orbit: [60, 80, 24], center: [0, 4, 0], fov: 40, e: ease.inOutSine },
  ]);
  const words = ['sea states', 'stress at the hot spots', 'rainflow', 'S N curve', "Miner's sum", 'design fatigue factor'];
  const labels = ['Sea states', 'Stress at the hot spots', 'Rainflow counting', 'The right S-N curve', "Miner's sum", 'Design fatigue factor'];
  const icons = ['waves', 'stress', 'rainflow', 'sn', 'sum', 'check'];
  const TW = 8.4;

  return {
    sfx: [{ t: ctx.duration - 7.5, type: 'outro' }],
    render(t) {
      cam(t);
      updateWorld(w, t);
      w.bop.rotation.set(0, 0, 0);
      w.bop.rotateZ(0.003 * Math.sin((2 * Math.PI * t) / TW));
      ctx.renderer.render(w.scene, w.camera);
      d2.vignette(0.55);
      const fadeAll = 1 - seg(t, o2 + 4.6, 1.0);
      d2.fadeRect(0.4 * env(t, o1 - 0.6, o2 + 5.6, 0.8, 1.0), '#020810');
      labels.forEach((lab, i) => {
        const tt = at('o1', words[i]);
        const q = seg(t, tt - 0.25, 0.7, ease.outExpo);
        if (q <= 0) return;
        const s = STEPS[i];
        const y = 250 + i * 98;
        const x = 600 + (1 - q) * -40;
        d2.panel(x - 30, y - 42, 760, 80, { alpha: q * fadeAll * 0.9, accent: s.col, fill: 'rgba(6,16,28,0.72)', shadow: false });
        d2.text(String(s.n), x + 4, y + 13, { size: 38, weight: 800, color: s.col, alpha: q * fadeAll });
        glyph(d2, icons[i], x + 80, y - 2, 22, s.col, q * fadeAll);
        d2.text(lab, x + 130, y + 12, { size: 36, weight: 700, alpha: q * fadeAll, shadow: true });
      });
      const tq = seg(t, o2, 1.0) * fadeAll;
      d2.text('Every wave leaves a little damage behind.', 960, 900, { size: 38, weight: 650, align: 'center', color: PAL.ink, alpha: tq, shadow: true });
      d2.text('Count it carefully, and you will know how long the steel will last.', 960, 950, { size: 30, weight: 500, align: 'center', color: PAL.ink2, alpha: seg(t, at('o2', 'Count it'), 1.0) * fadeAll, shadow: true });
      // end card
      const eA = env(t, o2 + 5.0, ctx.duration + 1, 1.0, 0.5);
      if (eA > 0) {
        d2.fadeRect(eA * 0.78, '#020810');
        d2.text('FATIGUE DESIGN WITH DNV-RP-C203', 960, 410, { size: 24, weight: 700, color: PAL.cyan, align: 'center', ls: 8, alpha: eA });
        d2.text('Every Wave Counts', 960, 510, { size: 96, weight: 800, align: 'center', alpha: eA });
        d2.text('A subsea wellhead, from sea states to fatigue life', 960, 575, { size: 30, color: PAL.ink2, align: 'center', alpha: eA });
        d2.text('Computed for this video: global beam–spring model of the well, 3D solid model of the housings (hot-spot stress),', 960, 668, { size: 21, color: PAL.ink3, align: 'center', alpha: eA });
        d2.text('rainflow counting and Miner summation over an example scatter diagram, with DNV-RP-C203 S-N curves.', 960, 700, { size: 21, color: PAL.ink3, align: 'center', alpha: eA });
        d2.text('Riser loads come from a simplified transfer function: the numbers illustrate the method, not a specific well.', 960, 744, { size: 21, color: PAL.ink3, align: 'center', alpha: eA });
      }
      d2.fadeRect(seg(t, ctx.duration - 1.4, 1.4), '#000000');
    },
  };
}
