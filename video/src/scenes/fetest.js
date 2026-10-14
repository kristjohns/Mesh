import * as THREE from 'three';
import { makeBackdrop, renderViewport, studioScene, envMap } from '../engine/env.js';
import { makeLocalFE, colorBar } from '../models/femesh.js';
export default async function fetest(ctx) {
  const back = makeBackdrop();
  const fe = studioScene();
  const o = ctx.opts;
  const local = makeLocalFE(ctx.data.wellhead_surface, { vmax: 220, env: envMap(ctx.renderer) });
  local.userData.mat.toneMapped = false;
  const clip = new THREE.Plane(new THREE.Vector3(0, 1, 0), -(o.ycut ?? 0.5));
  local.userData.mat.clippingPlanes = [clip];
  local.userData.emat.clippingPlanes = [clip];
  fe.add(local);
  const cam = new THREE.PerspectiveCamera(o.fov ?? 20, 1, 0.01, 100);
  return { duration: 5, render(t) {
    back.render(ctx.renderer);
    local.userData.set(o.state ?? 8, o.scale ?? 0);
    cam.position.set(...(o.pos ?? [-4, 2.8, 9]));
    cam.lookAt(...(o.tgt ?? [0, 2.0, 0]));
    cam.fov = o.fov ?? 20;
    renderViewport(ctx.renderer, fe, cam, o.vx ?? 1100, o.vy ?? 100, o.vw ?? 760, o.vh ?? 880);
    ctx.d2.rect(o.vx ?? 1100, o.vy ?? 100, o.vw ?? 760, o.vh ?? 880, { stroke: '#335', width: 1 });
  } };
}
