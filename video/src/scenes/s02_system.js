// The structure: template, then the wellhead stack assembled in a section cutaway.
import * as THREE from 'three';
import { makeWorld, makeSite, updateWorld, mergeByMaterial } from './common.js';
import { cameraPath, toScreen, materials, grimeAll } from '../engine/env.js';
import { toThree } from '../models/template.js';
import { makeWellhead, makeBOP, DIM } from '../models/wellhead.js';
import { soilSection } from '../models/soil.js';
import { PAL, seg, env, ease, clamp, lerp, rgba } from '../engine/util.js';

export default async function system(ctx) {
  const { d2, cue, cueEnd, at } = ctx;
  const [sx, , sz] = toThree(5.5, 4.5, 0);
  const phi = (32 * Math.PI) / 180;
  const n = new THREE.Vector3(Math.cos(phi), 0, Math.sin(phi));
  const p0 = new THREE.Vector3(sx, 0, sz);
  const cut = new THREE.Plane(n.clone().negate(), n.dot(p0) + 400);
  const w = makeWorld(ctx, { water: { density: 0.018 } });
  const bopM = grimeAll(materials(ctx.renderer));
  const site = makeSite(ctx, w, { skipWell0: true, bopMaterials: bopM, clip: [cut], riserTop: 140 });
  const bopMats = new Set(Object.values(bopM));
  // keep the slot-0 receptacle opaque while the rest of the template fades for close-ups
  const rec0 = site.tpl.userData.receptacles[0];
  rec0.material = w.M.yellow.clone();
  const fadeMats = new Set();
  w.scene.traverse((o) => {
    const m = o.material;
    if (!o.isMesh || !m || bopMats.has(m) || m.isShaderMaterial || m.isMeshBasicMaterial) return;
    m.clippingPlanes = [cut];
    if (o !== w.bed) m.side = THREE.DoubleSide;
    if (o !== w.bed && o !== rec0 && !o.parent?.parent?.userData?.parts && Object.values(w.M).includes(m) || m.alphaMap) fadeMats.add(m);
  });
  for (const m of fadeMats) { m.transparent = true; m.needsUpdate = true; }

  // the drilling-slot wellhead, full length, with installation offsets
  const cementLevel = new THREE.Plane(new THREE.Vector3(0, -1, 0), -60);
  const wh = makeWellhead(w.envTex, { zBottom: -60, segments: 128, clipPlanes: [cut], envIntensity: 0.55 });
  wh.position.copy(p0);
  wh.rotation.y = -phi;
  w.scene.add(wh);
  const P = wh.userData.parts;
  P.cement.userData.mat.clippingPlanes = [cut, cementLevel];
  const capClipCement = new THREE.Plane(new THREE.Vector3(0, -1, 0), -60);
  P.cement.userData.capMat.clippingPlanes = [capClipCement];
  wh.userData.welds.forEach((m) => { m.visible = false; });
  // soil section face
  const soil = soilSection({ width: 70, depth: 85, holeHalf: DIM.rCondO + 0.002, holeDepth: 60 });
  soil.position.copy(p0).addScaledVector(n, -0.004);
  soil.rotation.y = -phi + Math.PI / 2;
  w.scene.add(soil);
  soil.visible = false;

  const bop = site.wells && w.bop;
  const tS1 = cue('s1'), tS2 = cue('s2'), tS3 = cue('s3'), tS4 = cue('s4'), tS5 = cue('s5'), tS6 = cue('s6'), tS7 = cue('s7');
  const tCut = tS2 - 0.9;

  // camera: n points towards the camera side of the cut
  const C = (dn, du, y, ty = y, tu = 0) => {
    const u = new THREE.Vector3(-Math.sin(phi), 0, Math.cos(phi));
    const pos = p0.clone().addScaledVector(n, dn).addScaledVector(u, du);
    pos.y = y;
    const tgt = p0.clone().addScaledVector(u, tu);
    tgt.y = ty;
    return { pos: pos.toArray(), tgt: tgt.toArray() };
  };
  const cam = cameraPath(w.camera, [
    { t: 0, orbit: [46, -12, 21], center: [0, 3.5, 0], fov: 40 },
    { t: tS1 + 9.5, orbit: [40, 48, 19], center: [0, 3.0, 0], fov: 40, e: ease.inOutSine },
    { t: tS2 + 3.2, ...C(80, 30, -9, -24, 3), fov: 42 },
    { t: tS3 - 0.4, ...C(84, 33, -10, -24, 3), fov: 42, e: ease.inOutSine },
    { t: tS3 + 2.0, ...C(7.2, 3.0, 2.4, 1.6, 0), fov: 40 },
    { t: tS4 - 0.2, ...C(6.6, 3.4, 2.3, 1.6, 0), fov: 40, e: ease.inOutSine },
    { t: tS4 + 1.4, ...C(10, 4, 0.9, -0.9, 0), fov: 40 },
    { t: tS5 + 0.4, ...C(9.5, 4.5, 1.2, -0.6, 0), fov: 40, e: ease.inOutSine },
    { t: tS5 + 2.4, ...C(4.0, 1.7, 2.75, 2.25, 0), fov: 38 },
    { t: tS6 - 0.3, ...C(3.7, 1.9, 2.7, 2.3, 0), fov: 38, e: ease.inOutSine },
    { t: tS6 + 2.6, ...C(25, 11, 5, 8.0, 0), fov: 42 },
    { t: ctx.duration, ...C(27, 13, 4.5, 8.5, 0), fov: 42, e: ease.inOutSine },
  ]);
  cam.drift = 0.08;

  // load arrows / moment time series
  const series = (tt) => Math.sin(tt * 0.63) * 0.55 + Math.sin(tt * 1.37 + 1.1) * 0.3 + Math.sin(tt * 2.9 + 0.4) * 0.15;
  const glow = (part, amt) => {
    const m = part.userData.mat;
    m.emissive = m.emissive ?? new THREE.Color();
    m.emissive.setRGB(0.15 * amt, 0.55 * amt, 0.75 * amt);
  };

  const sfx = [
    { t: tCut, type: 'whoosh' }, { t: tS2 + 2.6, type: 'thud' }, { t: tS4 + 3.6, type: 'thud' },
    { t: at('s5', 'pre-loads') + 0.2, type: 'click' }, { t: tS6 + 2.5, type: 'thud' },
  ];

  return {
    sfx,
    render(t) {
      // cut plane slides in from in front of the slot to the well axis
      const cp = seg(t, tCut, 1.6, ease.inOutSine);
      cut.constant = n.dot(p0) + (cp <= 0 ? 400 : lerp(40, 0, cp));
      const cutOn = cp > 0;
      wh.userData.setCut(cp >= 1);
      soil.visible = cp > 0.6;
      soil.material.uniforms.uAlpha.value = seg(t, tCut + 1.0, 0.8);
      // installation: conductor (+LPWH) slides in during s2
      const yc = lerp(64, 0, seg(t, tS2 + 0.3, 2.3, ease.inOutSine));
      P.conductor.position.y = yc;
      P.lpwh.position.y = yc;
      // casing + HPWHH run during s4
      const yh = lerp(66, 0, seg(t, tS4 + 0.1, 3.5, (x) => ease.inOutSine(x)));
      P.casing.position.y = yh;
      P.hpwhh.position.y = yh;
      for (const k of ['casing', 'hpwhh']) P[k].visible = yh < 65.9;
      // cement fills the annulus from the shoe to the mudline
      const lev = lerp(-60, 0, seg(t, tS4 + 3.7, 1.6, ease.inOutSine));
      cementLevel.constant = lev;
      capClipCement.constant = lev;
      P.cement.visible = lev > -59.9;
      // lock ring engages
      const lk = seg(t, at('s5', 'pre-loads') - 0.4, 0.8, ease.outBack);
      P.lockring.visible = lk > 0;
      const rs = lerp(0.9, 1.0, lk);
      P.lockring.scale.set(rs, 1, rs);
      // BOP lands during s6 and sways during s7
      bop.position.y = lerp(30, 0, seg(t, tS6 - 0.6, 3.0, ease.inOutSine));
      bop.visible = t < tCut + 0.2 || t > tS6 - 0.7;
      const sway = t > tS7 ? series(t) * 0.005 * seg(t, tS7, 1.5) : 0;
      bop.rotation.set(0, 0, 0);
      bop.rotateOnWorldAxis(new THREE.Vector3(-Math.sin(phi), 0, Math.cos(phi)), sway);
      // other trees fade (hide) when the section is shown
      // highlights
      glow(P.conductor, env(t, tS2 + 2.2, tS3 - 0.3, 0.4, 0.6) * 0.8);
      glow(P.lpwh, env(t, tS3 + 0.2, tS4 - 0.2, 0.4, 0.6) * (0.6 + 0.4 * Math.sin(t * 4)));
      glow(P.casing, env(t, tS4 + 0.3, tS5 - 0.2, 0.4, 0.6) * 0.8);
      glow(P.hpwhh, env(t, tS5 + 0.2, tS6 - 0.3, 0.4, 0.6) * (0.55 + 0.35 * Math.sin(t * 4)));
      glow(P.lockring, env(t, at('s5', 'pre-loads'), tS6, 0.3, 0.6) * 1.4);
      const fo = 1 - 0.72 * env(t, tS3 - 0.2, tS6 + 0.4, 1.2, 1.4);
      for (const m of fadeMats) { m.opacity = fo; m.depthWrite = fo > 0.99; }

      cam(t);
      updateWorld(w, t);
      ctx.renderer.render(w.scene, w.camera);
      d2.vignette(0.5);

      const S = (p) => toScreen(p, w.camera);
      const call = (p3, dx, dy, title, sub, tin, tout, o = {}) => {
        const a = env(t, tin, tout, 0.4, 0.5);
        if (a <= 0) return;
        const [px, py] = S(p3);
        d2.callout(px, py, px + dx, py + dy, title, sub, { alpha: a, progress: seg(t, tin, 1.0, ease.out), ...o });
      };
      // s1: template parts
      const T = ctx.data.template;
      const [axp, , azp] = toThree(-10, -8, 0);
      call([axp, 1.0, azp], -160, 120, 'Suction anchors ×4', 'hold the template down', at('s1', 'four suction'), tCut);
      call([0, 7.6, 0], 120, -170, 'Protective roof', 'over-trawlable hatches', at('s1', 'protective roof'), tCut, { align: 'left' });
      const slotA = env(t, at('s1', 'four-slot'), tCut, 0.4, 0.5);
      if (slotA > 0) {
        T.slots.forEach((s, i) => {
          const [x, , z] = toThree(s.x, s.y, 0);
          const [px, py] = S([x, 2.4, z]);
          const q = seg(t, at('s1', 'four-slot') + i * 0.15, 0.5, ease.outBack);
          d2.circle(px, py, 22 * q, { stroke: PAL.cyan, width: 3, alpha: slotA, glow: PAL.cyan });
          d2.text(String(i + 1), px, py - 34, { size: 24, weight: 800, color: PAL.cyan, align: 'center', alpha: slotA * q, shadow: true });
        });
        d2.tag('4 WELL SLOTS', 960, 110, { size: 22, alpha: slotA, align: 'center' });
      }
      // s2: conductor
      const u = new THREE.Vector3(-Math.sin(phi), 0, Math.cos(phi));
      const condPt = (y) => p0.clone().addScaledVector(u, DIM.rCondO).setY(y).toArray();
      call(condPt(-18), 120, -60, 'Conductor', '36 in × 1.5 in steel pipe', tS2 + 2.4, tS3 - 0.2, { align: 'left' });
      const dimA = env(t, tS2 + 3.4, tS3 - 0.2, 0.5, 0.5);
      if (dimA > 0) {
        const a3 = p0.clone().addScaledVector(u, -2.2).setY(0).toArray();
        const b3 = p0.clone().addScaledVector(u, -2.2).setY(-60).toArray();
        const [ax2, ay2] = S(a3), [bx2, by2] = S(b3);
        d2.dim(ax2, ay2, bx2, by2, '', { alpha: dimA, color: PAL.amber });
        d2.text('≈ 60 m', ax2 + 18, (ay2 + by2) / 2, { size: 30, weight: 700, color: PAL.amber, align: 'left', alpha: dimA, shadow: true });
        d2.text('penetration', ax2 + 18, (ay2 + by2) / 2 + 30, { size: 22, color: PAL.ink2, align: 'left', alpha: dimA, shadow: true });
        const [sx2, sy2] = S(p0.clone().addScaledVector(u, 16).setY(-30).toArray());
        d2.text('Seabed soil', sx2, sy2, { size: 30, weight: 700, color: PAL.ink, alpha: dimA * 0.9, shadow: true });
        d2.text('soft clay', sx2, sy2 + 32, { size: 22, color: PAL.ink2, alpha: dimA * 0.9, shadow: true });
        const [mx, my] = S(p0.clone().addScaledVector(u, 12).setY(0).toArray());
        d2.text('MUDLINE', mx, my - 10, { size: 18, weight: 700, color: PAL.ink2, ls: 3, alpha: dimA, shadow: true });
      }
      // s3: conductor housing + receptacle
      call(p0.clone().addScaledVector(u, DIM.rLpO).setY(1.5).toArray(), 150, 90, 'Conductor housing', 'low-pressure wellhead, welded to the conductor', at('s3', 'conductor housing'), tS4 - 0.1, { align: 'left' });
      call(p0.clone().addScaledVector(u, -0.85).setY(2.0).toArray(), -150, -110, 'Well-slot receptacle', 'part of the template', at('s3', 'receptacle') - 0.3, tS4 - 0.1, { align: 'right', color: PAL.amber });
      // weld marker
      const wa = env(t, at('s3', 'welded'), tS4 - 0.1, 0.3, 0.4);
      if (wa > 0) {
        const [px, py] = S(p0.clone().addScaledVector(u, DIM.rCondO).setY(0.8).toArray());
        d2.circle(px, py, 10 + 3 * Math.sin(t * 6), { stroke: PAL.amber, width: 2.5, alpha: wa });
        d2.text('weld', px + 18, py + 8, { size: 20, weight: 700, color: PAL.amber, alpha: wa, shadow: true });
      }
      // s4: casing + cement
      call(p0.clone().addScaledVector(u, DIM.rCasO).setY(-3).toArray(), 160, 60, 'Surface casing', '20 in, runs inside the conductor', tS4 + 1.0, tS5 - 0.1, { align: 'left' });
      call(p0.clone().addScaledVector(u, -0.33).setY(-6).toArray(), -170, 70, 'Cement', 'fills the annulus', at('s4', 'cemented') + 0.2, tS5 - 0.1, { align: 'right', color: PAL.ink2 });
      // s5: HPWHH, shoulder, lock ring
      call(p0.clone().addScaledVector(u, DIM.rHpO).setY(3.0).toArray(), 190, -80, 'High-pressure wellhead housing', '18¾ in, welded to the surface casing', tS5 + 0.2, tS6 - 0.2, { align: 'left' });
      call(p0.clone().addScaledVector(u, 0.378).setY(2.2).toArray(), -180, 110, 'Landing shoulder', '', at('s5', 'lands on a shoulder'), tS6 - 0.2, { align: 'right', color: PAL.amber });
      call(p0.clone().addScaledVector(u, 0.40).setY(2.49).toArray(), 200, 90, 'Lock ring', 'pre-loads the housing down', at('s5', 'lock ring') - 0.1, tS6 - 0.2, { align: 'left', color: PAL.green });
      const pa = env(t, at('s5', 'pre-loads') + 0.3, tS6 - 0.2, 0.3, 0.4);
      if (pa > 0) {
        for (const side of [1, -1]) {
          const [px, py] = S(p0.clone().addScaledVector(u, side * 0.38).setY(2.75).toArray());
          const [qx, qy] = S(p0.clone().addScaledVector(u, side * 0.38).setY(2.47).toArray());
          d2.arrow(px, py, qx, qy, { color: PAL.green, width: 4, head: 16, alpha: pa, progress: seg(t, at('s5', 'pre-loads') + 0.3, 0.5), glow: PAL.green });
        }
      }
      // s6: BOP
      call([sx, 8.5, sz], 200, -120, 'Blowout preventer', 'lands on the HP housing', tS6 + 0.8, tS7 + 0.5, { align: 'left' });
      call([sx, 30, sz], 140, 40, 'Drilling riser', 'to the rig', tS6 + 1.4, tS7 + 0.5, { align: 'left' });
      // s7: loads
      const la = env(t, tS7 + 0.2, ctx.duration - 0.6, 0.5, 0.6);
      if (la > 0) {
        const s = series(t);
        const zf = w.bop.userData.zFlex ?? 12;
        const [fx, fy] = S([sx, zf, sz]);
        const [wx, wy] = S([sx, 3.6, sz]);
        const [tx, ty] = S([sx, zf + 6, sz]);
        // riser tension (up)
        d2.arrow(tx, ty + 70, tx, ty - 50, { color: PAL.cyan, width: 5, head: 20, alpha: la * seg(t, at('s7', 'riser tension'), 0.5), glow: PAL.cyan });
        d2.text('riser tension', tx + 18, ty - 20, { size: 24, weight: 650, color: PAL.cyan, alpha: la * seg(t, at('s7', 'riser tension'), 0.5), shadow: true });
        // weight (down)
        const [gx, gy] = S([sx - 2.6, 9, sz]);
        d2.arrow(gx, gy - 40, gx, gy + 70, { color: PAL.ink2, width: 5, head: 20, alpha: la * seg(t, at('s7', 'weight'), 0.5) });
        d2.text('weight', gx - 14, gy + 30, { size: 24, weight: 650, color: PAL.ink2, align: 'right', alpha: la * seg(t, at('s7', 'weight'), 0.5), shadow: true });
        // cyclic lateral force at the flex joint
        const fa = la * seg(t, at('s7', 'bending moment'), 0.5);
        d2.arrow(fx, fy, fx + 210 * s, fy, { color: PAL.orange, width: 6, head: 22, alpha: fa * clamp(Math.abs(s) * 4), glow: PAL.orange });
        d2.text('riser load', fx + 210 * s + (s > 0 ? 16 : -16), fy - 14, { size: 24, weight: 650, color: PAL.orange, align: s > 0 ? 'left' : 'right', alpha: fa * clamp(Math.abs(s) * 4), shadow: true });
        // bending moment at the wellhead
        const mr = 90;
        d2.momentArrow(wx, wy, mr, -Math.PI * 0.75, -Math.PI * 0.75 + Math.PI * 0.9 * Math.sign(s) * clamp(Math.abs(s) * 1.5), { color: PAL.amber, width: 5, alpha: fa, glow: PAL.amber });
        d2.text('bending moment', wx + mr + 16, wy + 8, { size: 26, weight: 700, color: PAL.amber, alpha: fa, shadow: true });
        // time series inset
        const ia = la * seg(t, at('s7', 'cycles') - 0.2, 0.6);
        if (ia > 0) {
          const X = 120, Y = 700, Wd = 560, Hh = 230;
          d2.panel(X, Y, Wd, Hh, { alpha: ia, accent: PAL.amber });
          d2.text('Wellhead bending moment', X + 26, Y + 40, { size: 24, weight: 650, alpha: ia });
          d2.text('cycles with every wave → fatigue', X + 26, Y + 70, { size: 20, color: PAL.ink2, alpha: ia });
          const pts = [];
          for (let k = 0; k <= 200; k++) {
            const tt = t - 12 + (12 * k) / 200;
            pts.push([X + 30 + (Wd - 60) * k / 200, Y + 150 - series(tt) * 55]);
          }
          d2.line(X + 30, Y + 150, X + Wd - 30, Y + 150, { color: 'rgba(160,190,210,0.25)', width: 1, alpha: ia });
          d2.path(pts, { color: PAL.amber, width: 3, alpha: ia, glow: PAL.amber, glowBlur: 6 });
          d2.circle(pts[pts.length - 1][0], pts[pts.length - 1][1], 6, { fill: PAL.amber, alpha: ia });
        }
      }
    },
  };
}
