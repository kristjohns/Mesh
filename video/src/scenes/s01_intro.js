// Cold open: descent along the riser, template reveal, FE "scan", title.
import * as THREE from 'three';
import { makeWorld, makeSite, updateWorld } from './common.js';
import { cameraPath, toScreen, fatLines } from '../engine/env.js';
import { makeTemplateWire, toThree } from '../models/template.js';
import { PAL, seg, env, ease, clamp, lerp, rgba } from '../engine/util.js';

export default async function intro(ctx) {
  const { d2, cue, at } = ctx;
  const w = makeWorld(ctx, { water: { density: 0.02 }, raysOpt: { opacity: 0.11, count: 12, y: 40, height: 110 } });
  const site = makeSite(ctx, w, { riserTop: 200 });
  const [sx, , sz] = toThree(5.5, 4.5, 0);

  // FE "scan": solid geometry kept on one side of a moving plane, beam model on the other
  const solidPlane = new THREE.Plane(new THREE.Vector3(1, 0, 0), 100);
  const wirePlane = new THREE.Plane(new THREE.Vector3(-1, 0, 0), -100);
  w.scene.traverse((o) => {
    if (o.isMesh && o !== w.bed && o.material && !o.material.isShaderMaterial && !o.material.isMeshBasicMaterial) {
      o.material.clippingPlanes = [solidPlane];
    }
  });
  const wire = makeTemplateWire(ctx.data.template, { clip: [wirePlane] });
  w.scene.add(wire);
  // well axes in the wire model
  const wl = [];
  for (const s of ctx.data.template.slots) {
    const [x, , z] = toThree(s.x, s.y, 0);
    wl.push(x, -2, z, x, s.x === 5.5 && s.y === 4.5 ? 16 : 6.5, z);
  }
  const wg = new THREE.BufferGeometry();
  wg.setAttribute('position', new THREE.Float32BufferAttribute(wl, 3));
  const wellLines = new THREE.LineSegments(wg, new THREE.LineBasicMaterial({ color: 0xffb703, fog: false, clippingPlanes: [wirePlane] }));
  w.scene.add(wellLines);
  const scanGlow = new THREE.Mesh(new THREE.PlaneGeometry(26, 22), new THREE.MeshBasicMaterial({
    color: 0x4cc9f0, transparent: true, opacity: 0.0, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide, fog: false,
  }));
  scanGlow.rotation.y = Math.PI / 2;
  scanGlow.position.set(100, 6, 0);
  w.scene.add(scanGlow);
  const scanEdge = fatLines([0, -5, -13, 0, 17, -13, 0, 17, -13, 0, 17, 13, 0, 17, 13, 0, -5, 13, 0, -5, 13, 0, -5, -13, 0, 0.3, -13, 0, 0.3, 13],
    { color: 0x9fe8ff, width: 2.5, transparent: true });
  w.scene.add(scanEdge);

  // glowing ring at the wellhead connector
  const ring = new THREE.Mesh(new THREE.TorusGeometry(1.25, 0.05, 12, 96), new THREE.MeshBasicMaterial({ color: 0x4cc9f0, transparent: true, opacity: 0, fog: false, blending: THREE.AdditiveBlending, depthWrite: false }));
  ring.rotation.x = Math.PI / 2;
  ring.position.set(sx, 3.6, sz);
  w.scene.add(ring);

  const t1 = cue('i1'), t2 = cue('i2'), t3 = cue('i3'), t4 = cue('i4');
  const cam = cameraPath(w.camera, [
    { t: 0, pos: [sx - 9, 96, sz + 11], tgt: [sx + 5, 74, sz - 2], fov: 42 },
    { t: t2 - 1.0, pos: [sx - 12, 30, sz + 15], tgt: [sx + 2, 9, sz - 2], fov: 42, e: ease.inOutSine },
    { t: t3 - 0.5, pos: [sx + 9, 21, sz - 10], tgt: [sx - 1.5, 3.5, sz + 1.5], fov: 40 },
    { t: t4 + 2, orbit: [40, 28, 17], center: [0, 3.5, 0], fov: 40 },
    { t: ctx.duration, orbit: [44, -8, 20], center: [0, 3.5, 0], fov: 40, e: ease.inOutSine },
  ]);
  cam.drift = 0.15;

  const sfx = [
    { t: 0.0, type: 'drone' },
    { t: t3 + 1.0, type: 'scan' },
    { t: t4 + 0.4, type: 'hit' },
  ];

  return {
    sfx,
    render(t) {
      cam(t);
      updateWorld(w, t);
      // rays fade as we go deeper
      const depthF = clamp((w.camera.position.y - 10) / 70);
      w.rays.children.forEach((m) => { m.material.opacity *= 0.25 + 0.75 * depthF; });
      // scan sweep (x from +17 to -17)
      const sp = seg(t, at('i3', 'finite element model') - 0.6, 4.2, ease.inOutSine);
      const xs = lerp(17, -17, sp);
      const active = sp > 0 && sp < 1;
      solidPlane.constant = sp <= 0 ? 100 : -xs;
      wirePlane.constant = sp <= 0 ? -100 : xs;
      scanGlow.position.x = xs;
      scanGlow.material.opacity = active ? 0.045 : 0;
      scanEdge.position.set(xs, 0, 0);
      scanEdge.material.opacity = active ? 0.9 : 0;
      scanEdge.visible = active;
      ring.material.opacity = 0.9 * env(t, at('i2', 'ends up here'), at('i2', 'the soil') + 1.0, 0.4, 0.8) * (0.7 + 0.3 * Math.sin(t * 5));
      const rs = 1 + 0.08 * Math.sin(t * 3);
      ring.scale.set(rs, rs, rs);
      ctx.renderer.render(w.scene, w.camera);

      d2.vignette(0.5);
      // depth gauge
      const gA = env(t, 1.2, t3 - 0.5, 0.8, 0.8);
      if (gA > 0) {
        const depth = 350 - Math.max(0, w.camera.position.y) * 0.62 - 2;
        const gx = 1760, gy0 = 260, gy1 = 820;
        d2.line(gx, gy0, gx, gy1, { color: rgba(PAL.ink2, 0.5), width: 2, alpha: gA });
        for (let dd = 280; dd <= 360; dd += 10) {
          const y = lerp(gy0, gy1, (dd - 280) / 80);
          d2.line(gx - (dd % 50 === 0 ? 18 : 9), y, gx, y, { color: rgba(PAL.ink2, 0.6), width: 1.5, alpha: gA });
          if (dd % 50 === 0) d2.text(`${dd}`, gx - 28, y + 7, { size: 20, color: PAL.ink2, align: 'right', alpha: gA });
        }
        const my = lerp(gy0, gy1, clamp((depth - 280) / 80));
        d2.poly([[gx + 4, my], [gx + 20, my - 9], [gx + 20, my + 9]], { fill: PAL.cyan, alpha: gA });
        d2.text(`${depth.toFixed(0)} m`, gx + 30, my + 9, { size: 28, weight: 700, color: PAL.cyan, alpha: gA });
        d2.text('DEPTH', gx, gy0 - 24, { size: 18, weight: 700, color: PAL.ink2, align: 'center', ls: 3, alpha: gA });
      }
      // wellhead tag during i2
      const ta = env(t, at('i2', 'ends up here'), t3 - 0.2, 0.5, 0.5);
      if (ta > 0) {
        const [px, py] = toScreen([sx, 3.6, sz], w.camera);
        d2.callout(px, py, px + 220, py - 140, 'Wellhead', 'riser loads end up here', { alpha: ta, progress: seg(t, at('i2', 'ends up here'), 1.2, ease.out) });
      }
      // scan label
      const sa = env(t, at('i3', 'finite element model') - 0.3, t4 - 0.3, 0.4, 0.5);
      if (sa > 0) d2.tag('FINITE ELEMENT MODEL', 960, 120, { size: 22, alpha: sa, align: 'center' });

      // title
      const ta2 = env(t, t4 + 0.3, ctx.duration - 1.6, 0.8, 1.2);
      if (ta2 > 0) {
        d2.fadeRect(ta2 * 0.45, '#020810');
        const p = seg(t, t4 + 0.3, 1.6, ease.outExpo);
        d2.text('FINITE ELEMENT BEST PRACTICE', 960, 380, { size: 26, weight: 700, color: PAL.cyan, align: 'center', ls: 9, alpha: ta2 * p });
        d2.g.save();
        d2.g.filter = `blur(${(1 - p) * 10}px)`;
        d2.text('Meshing with Purpose', 960, 492, { size: 104, weight: 800, align: 'center', alpha: ta2 * p, ls: -1, shadow: 'rgba(0,0,0,0.6)', shadowBlur: 30 });
        d2.g.restore();
        d2.line(960 - 360 * p, 532, 960 + 360 * p, 532, { color: PAL.cyan, width: 2, alpha: ta2 * 0.8 });
        d2.text('A subsea wellhead & template case study', 960, 584, { size: 34, weight: 500, color: PAL.ink2, align: 'center', alpha: ta2 * seg(t, t4 + 1.0, 1.0) });
        const chips = [['Element type', at('i4', 'which element types')], ['Mesh size', at('i4', 'how fine the mesh')], ['Boundary conditions', at('i4', 'boundary conditions')]];
        let cx = 960 - 420;
        const widths = chips.map(([s]) => d2.measure(s, 26, 650, 1) + 26 * 1.2);
        const total = widths.reduce((a, b) => a + b, 0) + 2 * 34;
        cx = 960 - total / 2;
        chips.forEach(([s, tc], i) => {
          const q = seg(t, tc, 0.6, ease.outBack);
          d2.tag(s, cx, 690 + (1 - q) * 20, { size: 26, alpha: ta2 * clamp(q), color: [PAL.cyan, PAL.amber, PAL.green][i] });
          cx += widths[i] + 34;
        });
      }
      d2.fadeRect(1 - seg(t, 0, 2.2, ease.inOutSine), '#000000');
    },
  };
}
