// Outro: back to the seabed, three takeaways, end card.
import * as THREE from 'three';
import { makeWorld, makeSite, updateWorld } from './common.js';
import { cameraPath } from '../engine/env.js';
import { PAL, seg, env, ease, clamp, lerp } from '../engine/util.js';

export default async function outro(ctx) {
  const { d2, cue, at } = ctx;
  const w = makeWorld(ctx, { water: { density: 0.02 } });
  makeSite(ctx, w, { riserTop: 200 });
  const o1 = cue('o1'), o2 = cue('o2');
  const cam = cameraPath(w.camera, [
    { t: 0, orbit: [30, 40, 14], center: [1, 3, -1], fov: 40 },
    { t: ctx.duration, orbit: [58, 75, 24], center: [0, 4, 0], fov: 40, e: ease.inOutSine },
  ]);
  return {
    sfx: [{ t: ctx.duration - 6.0, type: 'outro' }],
    render(t) {
      cam(t);
      updateWorld(w, t);
      ctx.renderer.render(w.scene, w.camera);
      d2.vignette(0.55);
      const lines = [
        ['Choose the element', 'by the physics', at('o1', 'choose the element'), PAL.cyan],
        ['Size the mesh', 'by the stress gradients', at('o1', 'size the mesh'), PAL.amber],
        ['Set boundary conditions', 'by the real load paths', at('o1', 'set boundary'), PAL.green],
      ];
      const fadeAll = 1 - seg(t, o2 + 3.6, 1.0);
      d2.fadeRect(0.35 * env(t, o1 - 0.5, o2 + 4.6, 0.8, 1.0), '#020810');
      lines.forEach(([a, b, tt, col], i) => {
        const q = seg(t, tt - 0.2, 0.8, ease.outExpo);
        if (q <= 0) return;
        const y = 330 + i * 150;
        d2.text(a, 940, y + (1 - q) * 20, { size: 64, weight: 800, align: 'right', alpha: q * fadeAll, shadow: true });
        d2.text(b, 980, y + (1 - q) * 20, { size: 64, weight: 500, color: col, alpha: q * fadeAll, shadow: true });
      });
      const qA = seg(t, o2, 1.0) * fadeAll;
      d2.text('…and your model answers the question you actually asked.', 960, 820, { size: 34, weight: 600, align: 'center', color: PAL.ink2, alpha: qA, shadow: true });
      // end card
      const eA = env(t, o2 + 4.2, ctx.duration + 1, 1.0, 0.5);
      if (eA > 0) {
        d2.fadeRect(eA * 0.75, '#020810');
        d2.text('Meshing with Purpose', 960, 500, { size: 88, weight: 800, align: 'center', alpha: eA });
        d2.text('Finite element best practice · a subsea wellhead & template case study', 960, 570, { size: 28, color: PAL.ink2, align: 'center', alpha: eA });
        d2.text('All results shown were computed for this video: 3D solid, axisymmetric, beam-spring and frame FE models', 960, 660, { size: 22, color: PAL.ink3, align: 'center', alpha: eA });
      }
      d2.fadeRect(seg(t, ctx.duration - 1.4, 1.4), '#000000');
    },
  };
}
