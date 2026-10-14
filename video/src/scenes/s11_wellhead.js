// Chapter 4b: interface conductor housing <-> high-pressure housing (contact, pre-load, lift-off).
import * as THREE from 'three';
import { makeBackdrop, renderViewport, studioScene, envMap, cameraPath, toScreen } from '../engine/env.js';
import { makeLocalFE, colorBar } from '../models/femesh.js';
import { DIM } from '../models/wellhead.js';
import { cutawayScene } from './s10_template.js';
import { contactRing, drawSection } from './s06_axisym.js';
import { keyLine } from './common.js';
import { Plot } from '../engine/draw2d.js';
import { PAL, seg, env, ease, clamp, lerp, rgba } from '../engine/util.js';

export default async function wellheadScene(ctx) {
  const { d2, cue, at, renderer, data, tex } = ctx;
  const L = data.wellhead_local;
  const res = L.results;
  const back = makeBackdrop();
  const c = {};
  for (let i = 1; i <= 7; i++) c[i] = cue('c' + i);
  const C = cutawayScene(ctx, { zBottom: -2 });
  const cam = new THREE.PerspectiveCamera(30, 16 / 9, 0.05, 100);
  const camf = cameraPath(cam, [
    { t: 0, pos: [6.6, 2.5, 2.2], tgt: [0, 2.15, 0.2], fov: 30 },
    { t: c[2] - 0.3, pos: [6.2, 2.5, 2.1], tgt: [0, 2.15, 0.2], fov: 30, e: ease.inOutSine },
    { t: c[2] + 1.5, pos: [2.2, 2.4, 0.62], tgt: [0, 2.22, 0.12], fov: 30 },
    { t: c[3], pos: [2.1, 2.4, 0.6], tgt: [0, 2.23, 0.12], fov: 30, e: ease.inOutSine },
  ]);
  const fe = studioScene();
  const local = makeLocalFE(data.wellhead_surface, { vmax: 200, env: envMap(renderer) });
  local.userData.mat.toneMapped = false;
  const ycut = new THREE.Plane(new THREE.Vector3(0, 1, 0), -0.5);
  local.userData.mat.clippingPlanes = [ycut];
  local.userData.emat.clippingPlanes = [ycut];
  fe.add(local);
  const fcam = new THREE.PerspectiveCamera(19, 1, 0.01, 100);
  // moment-rotation data
  const Mr = res.map((r) => [r.rot_rel * 1e3, r.M / 1e6]);
  const k1 = Mr[1][1] / Mr[1][0];
  // state index driven by time
  const stateAt = (t) => 12 * seg(t, at('c4', 'As the moment') - 0.2, 10.5, ease.inOutSine);

  return {
    sfx: [{ t: c[3] + 0.4, type: 'click' }, { t: c[6] + 0.2, type: 'whoosh' }],
    render(t) {
      back.render(renderer);
      // ------------------------------------------------ 3D cutaway: c1, c2
      const cA = env(t, 0, c[3] + 0.3, 0.1, 0.6);
      if (cA > 0) {
        camf(t);
        renderViewport(renderer, C.S, cam, 0, 0, 1920, 1080);
        d2.fadeRect(1 - cA, '#060f19');
        // load path arrows (c1)
        const la = cA * env(t, at('c1', 'It controls') - 0.3, c[2] + 0.2, 0.5, 0.5);
        if (la > 0) {
          const [tx, ty] = toScreen([0, 3.45, 0], cam);
          d2.momentArrow(tx, ty, 80, Math.PI * 1.1, Math.PI * 1.9, { color: PAL.amber, width: 5, alpha: la, glow: PAL.amber });
          d2.text('bending moment', tx + 100, ty - 40, { size: 28, weight: 750, color: PAL.amber, alpha: la, shadow: true });
          const flow = (t * 0.6) % 1;
          const path = [[0, 3.3, 0.3], [0, 2.6, 0.3], [0, 2.32, 0.39], [0, 2.1, 0.43], [0, 1.4, 0.44]].map((p) => toScreen(p, cam));
          d2.path(path.map(([x, y]) => [x, y]), { color: PAL.amber, width: 5, alpha: la * 0.85, dash: [16, 14], dashOffset: -flow * 60, glow: PAL.amber });
          const [ex, ey] = toScreen([0, 1.4, 0.44], cam);
          d2.text('into the conductor housing', ex + 30, ey + 10, { size: 26, weight: 650, color: PAL.ink, alpha: la, shadow: true });
        }
        // contact pairs (c2)
        const pa = cA * env(t, c[2] + 0.4, c[3] + 0.3, 0.5, 0.5);
        if (pa > 0) {
          const items = [
            ['landing shoulder', [0, 2.2, 0.378], at('c2', 'landing'), PAL.amber, [-260, 120]],
            ['lock ring', [0, 2.485, 0.40], at('c2', 'lock ring'), PAL.green, [190, -110]],
            ['upper radial contact', [0, 2.33, 0.4025], at('c2', 'radial contacts'), PAL.cyan, [-330, -40]],
            ['lower radial contact', [0, 1.9, 0.35], at('c2', 'above and below'), PAL.violet, [-260, 170]],
          ];
          items.forEach(([s, p3, tt, col, off]) => {
            const q = seg(t, tt - 0.2, 0.8);
            const [px, py] = toScreen(p3, cam);
            d2.callout(px, py, px + off[0], py + off[1], s, '', { alpha: pa * clamp(q * 2), progress: q, color: col, size: 28 });
          });
          d2.tag('SURFACE-TO-SURFACE CONTACT PAIRS', 960, 100, { size: 22, alpha: pa, align: 'center', color: PAL.cyan });
        }
      }
      // ------------------------------------------------ c2 second half: slave / master densities
      const sA = env(t, at('c2', 'Make the finer') - 0.3, c[3] + 0.2, 0.5, 0.5);
      if (sA > 0) {
        const zx = 1180, zy = 420, zw = 660, zh = 560;
        d2.panel(zx, zy, zw, zh, { alpha: sA, fill: 'rgba(6,14,24,0.94)' });
        const s = 3600;
        const X0 = zx + zw / 2 - 0.378 * s, Y0 = zy + zh / 2 + 2.2 * s;
        drawSection(d2, L.profile, null, { x0: X0, y0: Y0, s, alpha: sA, clip: [zx + 2, zy + 2, zw - 4, zh - 4], fill: 'rgba(120,150,180,0.25)', edgeColor: 'rgba(170,200,225,0.55)', edgeW: 1.2 });
        const g = d2.g;
        g.save();
        g.beginPath(); g.rect(zx + 2, zy + 2, zw - 4, zh - 4); g.clip();
        for (const pp of L.pairs2d) {
          if (pp.kind !== 'shoulder') continue;
          d2.circle(X0 + pp.r * s, Y0 - pp.z * s, 9, { fill: PAL.amber, alpha: sA, glow: PAL.amber });
        }
        d2.line(X0 + 0.356 * s, Y0 - 2.2 * s + 3, X0 + 0.405 * s, Y0 - 2.2 * s + 3, { color: PAL.cyan, width: 6, alpha: sA });
        g.restore();
        d2.text('Landing shoulder, contact pair', zx + 24, zy + 40, { size: 24, weight: 700, alpha: sA });
        d2.text('● slave nodes: finer HP-housing side', zx + 24, zy + zh - 50, { size: 22, weight: 650, color: PAL.amber, alpha: sA });
        d2.text('━ master surface: conductor housing', zx + 24, zy + zh - 18, { size: 22, weight: 650, color: PAL.cyan, alpha: sA });
      }
      // ------------------------------------------------ FE model: c3 .. c5
      const fA = env(t, c[3] + 0.1, c[6] - 0.2, 0.6, 0.6);
      const ms = t < c[4] ? 0 : stateAt(t);
      if (fA > 0) {
        local.userData.set(ms, 20);
        const ang = -0.38 + 0.05 * Math.sin(t * 0.3);
        fcam.position.set(Math.sin(ang) * 9.9, 3.0, Math.cos(ang) * 9.9);
        fcam.lookAt(0, 1.95, -0.1);
        renderViewport(renderer, fe, fcam, 60, 120, 720, 880);
        colorBar(d2, 760, 640, 20, 260, 0, 200, 'MPa', { alpha: fA });
        // step timeline
        const st = [['Step 1', 'lock-ring pre-load', at('c3', 'Apply'), PAL.green], ['Step 2', 'external loads', at('c3', 'before the external'), PAL.amber]];
        st.forEach(([a, b2, tt, col], i) => {
          const q = seg(t, tt, 0.6);
          const active = i === 0 ? t < c[4] : t >= c[4];
          d2.panel(880 + i * 500, 110, 470, 92, { alpha: fA * q, accent: col, fill: active ? rgba(col, 0.16) : undefined });
          d2.text(a, 910 + i * 500, 150, { size: 26, weight: 800, color: col, alpha: fA * q });
          d2.text(b2, 910 + i * 500, 182, { size: 22, color: PAL.ink2, alpha: fA * q });
        });
        // contact ring (c3, c4) or M-theta (c5)
        const rA = fA * (1 - seg(t, c[5] - 0.2, 0.6));
        if (rA > 0) {
          d2.panel(880, 240, 970, 740, { alpha: rA });
          d2.text('Landing-shoulder contact around the circumference', 920, 290, { size: 26, weight: 700, alpha: rA });
          contactRing(d2, res, ms, 1365, 620, 240, { alpha: rA, vmax: 10e6 });
          const M = 3 * ms / 12;
          const op = res[Math.round(ms)].open_frac;
          d2.text(`M = ${M.toFixed(2)} MNm`, 1365, 615, { size: 40, weight: 800, align: 'center', color: PAL.amber, alpha: rA });
          d2.text(op > 0.001 ? `${Math.round(op * 100)} % open` : 'closed all round', 1365, 660, { size: 26, weight: 700, align: 'center', color: op > 0 ? PAL.red : PAL.green, alpha: rA });
          const pl = rA * seg(t, at('c3', 'seven point three'), 0.6);
          d2.text(`pre-load ${(L.axi.preload / 1e6).toFixed(1)} MN`, 920, 340, { size: 24, weight: 650, color: PAL.green, alpha: pl });
          const lo = rA * seg(t, at('c4', 'one point four'), 0.5);
          if (lo > 0) d2.tag('lift-off starts ≈ 1.4 MNm', 1365, 930, { size: 22, alpha: lo, align: 'center', color: PAL.red });
        }
        const mA = fA * seg(t, c[5] - 0.1, 0.6);
        if (mA > 0) {
          d2.panel(880, 240, 970, 740, { alpha: mA });
          const P = new Plot(d2, { x: 980, y: 330, w: 800, h: 480, xr: [0, 0.6], yr: [0, 3.2] });
          P.axes({ alpha: mA, xticks: [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6], yticks: [0, 1, 2, 3], xlabel: 'relative rotation HP housing / conductor housing [mrad]', ylabel: 'moment [MNm]', fs: 19, ylabelOff: 56, title: 'Moment–rotation of the interface (FE result)', fmtx: (v) => v.toFixed(1) });
          const q = seg(t, c[5] + 0.2, 2.0);
          P.curve(Mr, { color: PAL.amber, width: 4, progress: q, alpha: mA });
          P.points(Mr, { color: PAL.amber, r: 5, progress: q, alpha: mA });
          const tq = seg(t, at('c5', 'A tied'), 0.6);
          P.clipBegin();
          P.curve([[0, 0], [0.6, 0.6 * k1]], { color: PAL.red, width: 3, dash: [8, 6], alpha: mA * tq });
          P.clipEnd();
          d2.text('tied / bonded: stays linear', P.X(0.33), P.Y(3.05), { size: 22, weight: 700, color: PAL.red, alpha: mA * tq });
          const kq = seg(t, at('c5', 'knee'), 0.6);
          d2.circle(P.X(0.17), P.Y(1.38), 26, { stroke: PAL.cyan, width: 3, alpha: mA * kq });
          d2.text('knee: lift-off', P.X(0.17) + 34, P.Y(1.38) + 40, { size: 22, weight: 700, color: PAL.cyan, alpha: mA * kq });
          const k2 = (Mr[12][1] - Mr[10][1]) / (Mr[12][0] - Mr[10][0]);
          d2.text(`stiffness after lift-off: ${Math.round(100 * k2 / k1)} % of initial`, 1000, 900, { size: 26, weight: 750, color: PAL.amber, alpha: mA * seg(t, at('c5', 'halves'), 0.6) });
        }
      }
      // ------------------------------------------------ c6: global model with calibrated springs
      const gA = env(t, c[6] + 0.1, c[7] - 0.2, 0.6, 0.5);
      if (gA > 0) {
        d2.text('In the global model: calibrated interface springs', 960, 140, { size: 44, weight: 800, align: 'center', alpha: gA });
        const cx = 620, y0 = 860, sy = 210;
        const Y = (z) => y0 - (z - 0.6) * sy;
        // outer string (conductor + LPWH) and inner string (casing + HPWHH), drawn side by side
        d2.line(cx - 60, Y(0.6), cx - 60, Y(2.75), { color: '#7fa6c7', width: 12, alpha: gA });
        d2.line(cx + 60, Y(0.6), cx + 60, Y(3.6), { color: '#e3edf5', width: 10, alpha: gA });
        d2.text('conductor housing', cx - 80, Y(2.75), { size: 22, weight: 650, color: '#9fc0de', align: 'right', alpha: gA });
        d2.text('HP housing', cx + 80, Y(3.5), { size: 22, weight: 650, color: PAL.ink, alpha: gA });
        const q1 = seg(t, at('c6', 'nonlinear springs') - 0.3, 0.8);
        for (const [z, lab] of [[2.62, 'upper contact (gap)'], [1.6, 'lower contact (gap)']]) {
          d2.spring(cx - 54, Y(z), cx + 54, Y(z), { color: PAL.cyan, width: 3, coils: 4, amp: 8, alpha: gA * q1 });
          d2.text(lab, cx + 90, Y(z) + 8, { size: 22, color: PAL.cyan, alpha: gA * q1 });
        }
        d2.circle(cx, Y(2.2), 26, { stroke: PAL.amber, width: 4, alpha: gA * q1 });
        d2.momentArrow(cx, Y(2.2), 38, -0.3, Math.PI * 1.4, { color: PAL.amber, width: 3, alpha: gA * q1, head: 12 });
        d2.text('rotational spring at the shoulder', cx + 90, Y(2.2) + 8, { size: 22, color: PAL.amber, alpha: gA * q1 });
        for (const z of [0.8, 1.2, 1.6, 2.2, 2.62]) d2.circle(cx - 60, Y(z), 6, { fill: PAL.ink, alpha: gA });
        for (const z of [1.2, 1.6, 2.2, 2.62, 3.1, 3.6]) d2.circle(cx + 60, Y(z), 6, { fill: PAL.ink, alpha: gA });
        // calibration plot
        const P = new Plot(d2, { x: 1180, y: 330, w: 560, h: 380, xr: [0, 0.6], yr: [0, 3.2] });
        d2.panel(1120, 250, 700, 600, { alpha: gA * q1 });
        P.axes({ alpha: gA * q1, xticks: [0, 0.2, 0.4, 0.6], yticks: [0, 1, 2, 3], xlabel: 'rotation [mrad]', ylabel: 'M [MNm]', fs: 18, ylabelOff: 50, title: 'spring law = local FE result', fmtx: (v) => v.toFixed(1) });
        P.curve(Mr, { color: PAL.amber, width: 4, alpha: gA * q1 });
        d2.text('same stiffness in both models', 1160, 810, { size: 26, weight: 750, color: PAL.green, alpha: gA * seg(t, at('c6', 'share the same'), 0.6) });
        d2.arrow(1110, 480, 900, Y(2.2), { color: PAL.amber, width: 2.5, alpha: gA * q1, dash: [8, 6] });
      }
      // ------------------------------------------------ c7: groove corner singularity
      const wA = env(t, c[7] + 0.1, ctx.duration, 0.6, 0.5);
      if (wA > 0) {
        d2.text('Check the hottest spots', 960, 140, { size: 44, weight: 800, align: 'center', alpha: wA });
        const zx = 160, zy = 220, zw = 860, zh = 700;
        d2.panel(zx, zy, zw, zh, { alpha: wA, fill: 'rgba(6,14,24,0.94)' });
        const s = 4200;
        const X0 = zx + zw / 2 - 0.43 * s, Y0 = zy + zh / 2 + 2.47 * s;
        drawSection(d2, L.profile, L.axi.vm_nodal, { x0: X0, y0: Y0, s, alpha: wA, vmax: 120, clip: [zx + 2, zy + 2, zw - 4, zh - 4], edgeW: 1.0 });
        d2.rect(X0 + 0.372 * s, Y0 - 2.517 * s, 0.056 * s, 0.067 * s, { fill: 'rgba(120,135,145,0.9)', stroke: '#0a1622', width: 1, alpha: wA });
        const pulse = 18 + 4 * Math.sin(t * 6);
        for (const [r, z] of [[0.43, 2.52], [0.43, 2.45]]) d2.circle(X0 + r * s, Y0 - z * s, pulse, { stroke: PAL.red, width: 3.5, alpha: wA * seg(t, at('c7', 'sharp corners') - 0.2, 0.5) });
        d2.text('lock-ring groove (sharp corners)', zx + 24, zy + 42, { size: 24, weight: 700, alpha: wA });
        d2.text('lock ring', X0 + 0.40 * s, Y0 - 2.483 * s + 8, { size: 20, weight: 650, color: '#0a1622', align: 'center', alpha: wA });
        colorBar(d2, zx + zw + 30, 600, 20, 260, 0, 120, 'MPa', { alpha: wA });
        const n1 = seg(t, at('c7', 'singularities'), 0.6), n2 = seg(t, at('c7', 'fine for load transfer'), 0.6), n3 = seg(t, at('c7', 'fatigue at the groove'), 0.6);
        d2.panel(1160, 300, 680, 520, { alpha: wA * n1, accent: PAL.red });
        d2.warn(1210, 370, 16, { alpha: wA * n1 });
        d2.text('Singularities, not results', 1250, 380, { size: 32, weight: 800, color: PAL.red, alpha: wA * n1 });
        d2.check(1210, 490, 18, { progress: n2, alpha: wA });
        d2.text('model is fine for load transfer', 1250, 500, { size: 28, weight: 650, alpha: wA * n2 });
        d2.cross(1210, 600, 18, { progress: n3, alpha: wA });
        d2.text('not for fatigue at the groove', 1250, 610, { size: 28, weight: 650, alpha: wA * n3 });
        d2.text('→ model the real radius, converge the mesh', 1250, 700, { size: 26, weight: 650, color: PAL.green, alpha: wA * seg(t, at('c7', 'converged mesh'), 0.6) });
      }
    },
  };
}
