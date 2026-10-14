import * as THREE from 'three';
import { makeWorld, makeSite, updateWorld } from './common.js';
import { cameraPath } from '../engine/env.js';

export default async function testScene(ctx) {
  const w = makeWorld(ctx);
  const site = makeSite(ctx, w);
  const cam = cameraPath(w.camera, [
    { t: 0, orbit: [42, 35, 18], center: [0, 3, 0], fov: 40 },
    { t: 10, orbit: [30, 75, 12], center: [5.5, 3, -4.5], fov: 40 },
  ]);
  window.__w = w;
  return {
    duration: 10,
    render(t) {
      cam(t);
      updateWorld(w, t);
      ctx.renderer.render(w.scene, w.camera);
      ctx.d2.text('test ' + t.toFixed(2), 40, 60, { size: 30 });
    },
  };
}
