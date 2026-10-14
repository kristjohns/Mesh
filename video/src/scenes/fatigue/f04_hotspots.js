// Where will it crack? Section through the well and soil, moment diagram from the global model,
// the three candidate hot spots.
import * as THREE from 'three';
import { makeWorld, makeSite, updateWorld } from '../common.js';
import { cameraPath, toScreen, materials, grimeAll } from '../../engine/env.js';
import { toThree } from '../../models/template.js';
import { makeWellhead, DIM } from '../../models/wellhead.js';
import { soilSection } from '../../models/soil.js';
import { PAL, seg, env, ease, clamp, lerp, rgba } from '../../engine/util.js';

const HS_COL = { hp: PAL.violet, lp: PAL.cyan, cg: PAL.amber };

export default async function hotspots(ctx) {
  const { d2, cue, at, data } = ctx;
  const F = data.fatigue;
  const [sx, , sz] = toThree(5.5, 4.5, 0);
  const phi = (32 * Math.PI) / 180;
  const n = new THREE.Vector3(Math.cos(phi), 0, Math.sin(phi));
  const u = new THREE.Vector3(-Math.sin(phi), 0, Math.cos(phi));
  const p0 = new THREE.Vector3(sx, 0, sz);
  const cut = new THREE.Plane(n.clone().negate(), n.dot(p0));
  const w = makeWorld(ctx, { water: { density: 0.016 } });
  const bopM = grimeAll(materials(ctx.renderer));
  makeSite(ctx, w, { skipWell0: true, clip: [cut], riserTop: 140, bopMaterials: bopM });
  const bopMats = new Set(Object.values(bopM));
  w.scene.traverse((o) => {
    const m = o.material;
    if (!o.isMesh || !m || bopMats.has(m) || m.isShaderMaterial || m.isMeshBasicMaterial) return;
    m.clippingPlanes = [cut];
    if (o !== w.bed) m.side = THREE.DoubleSide;
  });
  const wh = makeWellhead(w.envTex, { zBottom: -24, segments: 128, clipPlanes: [cut], envIntensity: 0.55 });
  wh.position.copy(p0);
  wh.rotation.y = -phi;
  wh.userData.setCut(true);
  w.scene.add(wh);
  // girth weld bead 3 m below the mudline
  const bead = new THREE.Mesh(new THREE.TorusGeometry(DIM.rCondO + 0.004, 0.014, 8, 96),
    new THREE.MeshStandardMaterial({ color: 0x6d6a63, metalness: 0.6, roughness: 0.6, envMap: w.envTex, clippingPlanes: [cut] }));
  bead.rotation.x = Math.PI / 2;
  bead.position.set(sx, -3.0, sz);
  w.scene.add(bead);
  const soil = soilSection({ width: 60, depth: 40, holeHalf: DIM.rCondO + 0.002, holeDepth: 24 });
  soil.position.copy(p0).addScaledVector(n, -0.004);
  soil.rotation.y = -phi + Math.PI / 2;
  w.scene.add(soil);
  const h1 = cue('h1'), h2 = cue('h2'), h3 = cue('h3');
  const C = (dn, du, y, ty, tu = 0) => {
    const pos = p0.clone().addScaledVector(n, dn).addScaledVector(u, du);
    pos.y = y;
    const tgt = p0.clone().addScaledVector(u, tu);
    tgt.y = ty;
    return { pos: pos.toArray(), tgt: tgt.toArray() };
  };
  const cam = cameraPath(w.camera, [
    { t: 0, ...C(62, 30, 9, -1, 4), fov: 40 },
    { t: h2 - 1.0, ...C(52, 22, 4, -1.5, 3), fov: 40, e: ease.inOutSine },
    { t: h3 + 0.4, ...C(50, 20, 3, -2, 3), fov: 40, e: ease.inOutSine },
    { t: h3 + 3.4, ...C(11.5, 5.0, 1.2, -0.7, 0.6), fov: 40 },
    { t: ctx.duration, ...C(10.5, 4.0, 1.0, -0.8, 0.6), fov: 40, e: ease.inOutSine },
  ]);
  cam.drift = 0.06;
  const axis = u.clone();
  const TW = 8.4;
  const sway = (t) => Math.sin((2 * Math.PI * t) / TW);
  const dg = F.diagram;
  const Mat = (zs, Ms, z) => {
    for (let i = 0; i < zs.length - 1; i++) if (z >= zs[i] && z <= zs[i + 1]) return Ms[i] + (Ms[i + 1] - Ms[i]) * (z - zs[i]) / (zs[i + 1] - zs[i]);
    return 0;
  };
  const Mmax = Math.max(...dg.Mo.map(Math.abs), ...dg.Mi.map(Math.abs));

  return {
    sfx: [{ t: h3 + 0.6, type: 'whoosh' }],
    render(t) {
      cam(t);
      updateWorld(w, t);
      w.bop.rotation.set(0, 0, 0);
      w.bop.rotateOnWorldAxis(axis, 0.003 * sway(t) * env(t, 0.5, h3 + 1, 1.0, 1.0));
      ctx.renderer.render(w.scene, w.camera);
      d2.vignette(0.5);
      const S = (z, off = 0) => toScreen(p0.clone().addScaledVector(u, off).setY(z).toArray(), w.camera);
      // ------------------------------------------------ h1: the riser load
      const fA = env(t, h1 + 1.0, h3 + 0.6, 0.6, 0.6);
      if (fA > 0) {
        const [fx, fy] = S(16.6);
        const s = sway(t);
        d2.arrow(fx, fy, fx + 160 * s, fy, { color: PAL.orange, width: 6, head: 22, alpha: fA * clamp(Math.abs(s) * 4), glow: PAL.orange });
        d2.text('riser force at the flex joint', fx + 30, fy - 30, { size: 24, weight: 700, color: PAL.orange, alpha: fA, shadow: true });
        const lq = seg(t, at('h1', 'last video') - 0.4, 0.6) * (1 - seg(t, h2 - 0.4, 0.5));
        const [mx, my] = S(-12, 6);
        d2.text('conductor, cemented casing, soil', mx, my, { size: 22, weight: 650, color: PAL.ink, alpha: fA * lq, shadow: true });
      }
      // ------------------------------------------------ h2: moment diagram
      const mA = env(t, h2 - 0.4, h3 + 2.6, 0.7, 0.7);
      if (mA > 0) {
        const grow = seg(t, h2, 2.4, ease.inOutSine);
        const [ax0, ay0] = S(0), [ax1, ay1] = S(-10);
        const pxPerM = Math.hypot(ax1 - ax0, ay1 - ay0) / 10;
        const scale = 6.0 * pxPerM / Mmax;  // the peak moment is drawn 6 m wide
        const zs = [];
        for (let z = 16.6; z >= -22; z -= 0.25) zs.push(z);
        const zTop = lerp(16.6, -22, 0);
        const zEnd = lerp(16.6, -22, grow);
        const outer = [], inner = [];
        for (const z of zs) {
          if (z < zEnd) break;
          const mo = z <= 2.6 ? Mat(dg.zo, dg.Mo, z) : 0;
          const mi = Mat(dg.zi, dg.Mi, z) * (z > 2.6 ? 1 : 1);
          const [x0, y0] = S(z, -0.5);
          const xin = x0 - Math.abs(mi) * scale, xout = xin - Math.abs(mo) * scale;
          inner.push([x0, y0, xin]);
          outer.push([xin, y0, xout]);
        }
        if (inner.length > 1) {
          const g = d2.g;
          g.save();
          g.globalAlpha = mA * 0.55;
          g.fillStyle = PAL.violet;
          g.beginPath();
          inner.forEach(([x0, y0], k) => (k ? g.lineTo(x0, y0) : g.moveTo(x0, y0)));
          for (let k = inner.length - 1; k >= 0; k--) g.lineTo(inner[k][2], inner[k][1]);
          g.fill();
          g.fillStyle = PAL.cyan;
          g.beginPath();
          outer.forEach(([x0, y0], k) => (k ? g.lineTo(x0, y0) : g.moveTo(x0, y0)));
          for (let k = outer.length - 1; k >= 0; k--) g.lineTo(outer[k][2], outer[k][1]);
          g.fill();
          g.restore();
          d2.path(outer.map((p) => [p[2], p[1]]), { color: PAL.ink, width: 2.5, alpha: mA });
        }
        const lA = mA * seg(t, h2 + 1.0, 0.8);
        const [lx, ly] = S(10, -4);
        d2.text('bending moment', lx - 30, ly, { size: 28, weight: 800, color: PAL.ink, align: 'right', alpha: lA, shadow: true });
        d2.text('global model, 20 kN at the flex joint', lx - 30, ly + 30, { size: 19, color: PAL.ink2, align: 'right', alpha: lA, shadow: true });
        const cq = seg(t, at('h2', 'into the conductor') - 0.3, 0.6);
        const [cx2, cy2] = S(-7, -4.5);
        d2.tag('conductor', cx2 - 20, cy2, { size: 20, color: PAL.cyan, align: 'right', alpha: mA * cq, fill: 'rgba(5,14,26,0.85)' });
        const [ix, iy] = S(8, -1.2);
        d2.tag('HP housing + BOP', ix - 10, iy, { size: 20, color: PAL.violet, align: 'right', alpha: mA * cq, fill: 'rgba(5,14,26,0.85)' });
        const pq = seg(t, at('h2', 'to a peak') - 0.3, 0.6);
        if (pq > 0) {
          const zp = dg.zpeak;
          const mo = Mat(dg.zo, dg.Mo, zp), mi = Mat(dg.zi, dg.Mi, zp);
          const [x0, y0] = S(zp, -0.5);
          const xp = x0 - (Math.abs(mo) + Math.abs(mi)) * scale;
          d2.circle(xp, y0, 9, { fill: PAL.amber, alpha: mA * pq, glow: PAL.amber });
          d2.callout(xp, y0, xp - 60, y0 + 90, `peak ≈ ${Math.abs(zp).toFixed(1)} m below the mudline`, `${Math.round(Math.abs(mo))} kNm in the conductor`, { alpha: mA * pq, progress: pq, color: PAL.amber, size: 26, align: 'right' });
        }
      }
      // ------------------------------------------------ h3: the three candidate hot spots
      const hA = env(t, h3 + 2.2, ctx.duration, 0.6, 0.5);
      if (hA > 0) {
        const spots = [
          ['A', 'hp', 1.2, DIM.rCasO, 'HP housing weld', 'HP housing to 20 in surface casing', at('h3', 'high-pressure housing'), [-330, -150]],
          ['B', 'lp', 0.8, DIM.rCondO, 'Conductor housing weld', 'conductor housing to 36 in conductor', at('h3', 'conductor housing and'), [260, -110]],
          ['C', 'cg', -3.0, DIM.rCondO, 'Conductor girth weld', '3 m below the mudline', at('h3', 'girth weld'), [260, 40]],
        ];
        spots.forEach(([L, id, z, r, title, sub, tt, off]) => {
          const q = seg(t, tt - 0.3, 0.8);
          if (q <= 0) return;
          const side = off[0] > 0 ? 1 : -1;
          const [px, py] = S(z, -side * r);   // +u points to screen-left in this view
          const col = HS_COL[id];
          d2.circle(px, py, 15 + 3 * Math.sin(t * 5), { stroke: col, width: 3, alpha: hA * clamp(q * 2), glow: col });
          d2.callout(px, py, px + off[0], py + off[1], `${L} · ${title}`, sub, { alpha: hA, progress: q, color: col, size: 26, align: side > 0 ? 'left' : 'right' });
        });
        const kq = seg(t, at('h3', 'weak detail') - 0.4, 0.6) * (1 - seg(t, at('h3', 'high-pressure housing') - 0.4, 0.5));
        d2.tag('high stress range  ×  weak detail  =  hot spot', 960, 120, { size: 24, color: PAL.amber, align: 'center', alpha: hA * kq, fill: 'rgba(5,14,26,0.9)' });
        const [mx, my] = S(0, 4.2);
        d2.text('MUDLINE', mx, my - 10, { size: 18, weight: 700, color: '#d8ccb0', ls: 3, alpha: hA, shadow: true });
      }
    },
  };
}
