// Shared scene-building helpers.
import * as THREE from 'three';
import { materials, underwater, seabed, particles, godRays, envMap, uTime, grimeAll } from '../engine/env.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { makeTemplate, toThree } from '../models/template.js';
import { makeWellhead, makeBOP, makeXT } from '../models/wellhead.js';
import { PAL, clamp, seg, ease, env as envelope } from '../engine/util.js';

export function makeWorld(ctx, o = {}) {
  const scene = new THREE.Scene();
  const M = grimeAll(materials(ctx.renderer));
  const envTex = envMap(ctx.renderer);
  const amb = underwater(scene, o.water ?? {});
  const holes = [];
  const T = ctx.data.template;
  for (const a of T.anchors) { const [x, , z] = toThree(a.x, a.y, 0); holes.push({ x, z, r: 3.2, f: 3 }); }
  const bed = o.seabed === false ? null : seabed(scene, { holes, caustics: o.caustics ?? 0.12 });
  const snow = particles(scene, o.particles ?? {});
  const rays = o.rays === false ? null : godRays(scene, o.raysOpt ?? {});
  const camera = new THREE.PerspectiveCamera(o.fov ?? 40, 1920 / 1080, 0.1, 2000);
  return { scene, M, envTex, amb, bed, snow, rays, camera };
}

// full template site: template, wells with trees, drilling slot with BOP/riser
export function makeSite(ctx, w, o = {}) {
  const T = ctx.data.template;
  const tpl = makeTemplate(T, w.M, w.envTex);
  w.scene.add(tpl);
  const wells = [];
  T.slots.forEach((s, i) => {
    const [x, , z] = toThree(s.x, s.y, 0);
    if (!(i === 0 && o.skipWell0)) {
      const wh = makeWellhead(w.envTex, { zBottom: -3, segments: 72, clipPlanes: o.clip });
      wh.position.set(x, 0, z);
      w.scene.add(wh);
      wells.push(wh);
    }
    if (i === 0 && o.bop !== false) {
      const bop = mergeByMaterial(makeBOP(o.bopMaterials ?? w.M, { riserTop: o.riserTop ?? 160 }));
      bop.position.set(x, 0, z);
      w.scene.add(bop);
      w.bop = bop;
    } else if (i !== 0 || o.bop === false) {
      if (o.trees !== false && i !== 0) {
        const xt = mergeByMaterial(makeXT(o.xtMaterials ?? w.M));
        xt.position.set(x, 0, z);
        // flowline faces the manifold
        xt.rotation.y = s.x > 0 ? 0 : Math.PI;
        w.scene.add(xt);
      }
    }
  });
  // open the hatch over the drilling slot
  for (const h of tpl.userData.hatches) {
    const [i, j] = h.userData.cell;
    if (i === 2 && j === 2) h.rotation.x = -h.userData.side * 1.95;
  }
  return { tpl, wells };
}

export function updateWorld(w, t) {
  uTime.value = t;
  w.snow?.userData.update(t, [w.camera.position.x, w.camera.position.y, w.camera.position.z]);
  w.rays?.userData.update(t, w.camera);
}

// chapter title card drawn on the 2D layer
export function chapterCard(d2, t, num, title, sub, o = {}) {
  const t0 = o.t0 ?? 0, hold = o.hold ?? 2.0;
  const a = envelope(t, t0, t0 + hold, 0.45, 0.55);
  if (a <= 0.001) return a;
  d2.fadeRect(a * 0.92, '#050d16');
  const p = seg(t, t0, 1.1, ease.outExpo);
  const cx = 960, cy = 520;
  d2.text(String(num).padStart(2, '0'), cx, cy - 40, { size: 150, weight: 800, color: null, stroke: PAL.cyan, strokeWidth: 2.5, align: 'center', alpha: a * 0.9, ls: 6 });
  d2.line(cx - 260 * p, cy + 10, cx + 260 * p, cy + 10, { color: PAL.cyan, width: 2, alpha: a });
  d2.text(title, cx, cy + 78, { size: 58, weight: 700, align: 'center', alpha: a * seg(t, t0 + 0.2, 0.6), ls: 0.5 });
  if (sub) d2.text(sub, cx, cy + 128, { size: 28, weight: 500, color: PAL.ink2, align: 'center', alpha: a * seg(t, t0 + 0.4, 0.6) });
  return a;
}

// subtitle-style key message at the bottom of the screen
export function keyLine(d2, t, tin, tout, str, o = {}) {
  const a = envelope(t, tin, tout, 0.4, 0.4);
  if (a <= 0.001) return;
  const size = o.size ?? 34;
  const w = d2.measure(str, size, 600) + 70;
  const y = o.y ?? 975;
  d2.panel(960 - w / 2, y - size * 1.25, w, size * 2.05, { alpha: a * 0.95, r: 14, accent: o.accent ?? PAL.cyan });
  d2.text(str, 960, y + size * 0.1, { size, weight: 600, align: 'center', alpha: a, color: o.color ?? PAL.ink });
}

// rule card list (best-practice summary)
export function ruleCard(d2, t, x, y, w, items, o = {}) {
  const a = o.alpha ?? 1;
  const lh = o.lh ?? 74;
  const h = (o.title ? 78 : 26) + items.length * lh + 10;
  d2.panel(x, y, w, h, { alpha: a, accent: o.accent ?? PAL.cyan });
  let yy = y + 30;
  if (o.title) {
    d2.text(o.title, x + 32, y + 52, { size: 30, weight: 700, alpha: a, color: o.accent ?? PAL.cyan, ls: 1 });
    yy = y + 86;
  }
  items.forEach((it, i) => {
    const p = seg(t, it.t ?? 0, 0.6, ease.out);
    if (p <= 0) return;
    const kind = it.kind ?? 'ok';
    const ix = x + 46, iy = yy + 18 + i * lh;
    if (kind === 'ok') d2.check(ix, iy, 17, { progress: p, alpha: a });
    else if (kind === 'no') d2.cross(ix, iy, 17, { progress: p, alpha: a });
    else d2.warn(ix, iy, 15, { alpha: a * p });
    const lines = d2.wrap(it.text, w - 110, o.size ?? 26, 550);
    lines.forEach((ln, k) => d2.text(ln, x + 82, iy + 9 + k * (o.size ?? 26) * 1.25 - (lines.length - 1) * (o.size ?? 26) * 0.6, { size: o.size ?? 26, weight: 550, alpha: a * p, color: PAL.ink }));
  });
  return h;
}

// merge all meshes of a group by material (fewer draw calls)
export function mergeByMaterial(group) {
  group.updateMatrixWorld(true);
  const buckets = new Map();
  const keep = [];
  group.traverse((o) => {
    if (o.isMesh && !o.userData.noMerge) {
      const g = o.geometry.clone().applyMatrix4(o.matrixWorld.clone().premultiply(new THREE.Matrix4().copy(group.matrixWorld).invert()));
      const nonIndexed = g.index ? g.toNonIndexed() : g;
      for (const k of Object.keys(nonIndexed.attributes)) if (!['position', 'normal'].includes(k)) nonIndexed.deleteAttribute(k);
      if (!buckets.has(o.material)) buckets.set(o.material, []);
      buckets.get(o.material).push(nonIndexed);
    }
  });
  const out = new THREE.Group();
  for (const [mat, gs] of buckets) {
    const m = new THREE.Mesh(mergeGeometries(gs), mat);
    m.castShadow = true;
    m.receiveShadow = true;
    out.add(m);
  }
  out.position.copy(group.position);
  out.rotation.copy(group.rotation);
  out.userData = group.userData;
  return out;
}
