// Chapter 1: element families — beam, shell, solid, axisymmetric — each applied to a real part.
import * as THREE from 'three';
import { makeBackdrop, renderViewport, studioScene, envMap, cameraPath, toScreen, fatLines } from '../engine/env.js';
import { makeLocalFE } from '../models/femesh.js';
import { makeWellhead, DIM } from '../models/wellhead.js';
import { chapterCard } from './common.js';
import { PAL, seg, env, ease, clamp, lerp, rgba } from '../engine/util.js';

function scanPlanes() {
  // real geometry kept above h, FE representation kept below h
  const real = new THREE.Plane(new THREE.Vector3(0, 1, 0), 100);
  const fe = new THREE.Plane(new THREE.Vector3(0, -1, 0), -100);
  return {
    real, fe, set(h) { real.constant = -h; fe.constant = h; },
  };
}

export default async function families(ctx) {
  const { d2, cue, at, renderer } = ctx;
  const env3 = envMap(renderer);
  const back = makeBackdrop();
  const scene = studioScene({ hemi: 1.3, key: 1.8 });
  const cam = new THREE.PerspectiveCamera(32, 16 / 9, 0.05, 200);
  const X = [-9.5, -3.2, 3.2, 9.5];
  const objs = [];
  const steel = (c = 0xaeb9c3) => new THREE.MeshStandardMaterial({ color: c, metalness: 0.8, roughness: 0.32, envMap: env3, side: THREE.DoubleSide });

  // 1) conductor segment -> beam
  {
    const sp = scanPlanes();
    const g = new THREE.Group();
    g.position.x = X[0];
    const m = steel(0x9fb0bf);
    m.clippingPlanes = [sp.real];
    const pipe = new THREE.Mesh(new THREE.CylinderGeometry(0.457, 0.457, 5.2, 48, 1, true), m);
    pipe.position.y = 2.6;
    const inner = new THREE.Mesh(new THREE.CylinderGeometry(0.419, 0.419, 5.2, 48, 1, true), steel(0x6f7d89));
    inner.material.clippingPlanes = [sp.real];
    inner.position.y = 2.6;
    g.add(pipe, inner);
    const line = fatLines([0, 0, 0, 0, 5.2, 0], { color: 0x4cc9f0, width: 4, clip: [sp.fe] });
    g.add(line);
    const nodeMat = new THREE.MeshBasicMaterial({ color: 0xeaf2f8, clippingPlanes: [sp.fe] });
    for (let k = 0; k <= 8; k++) {
      const s = new THREE.Mesh(new THREE.SphereGeometry(0.09, 16, 8), nodeMat);
      s.position.y = (5.2 * k) / 8;
      g.add(s);
    }
    const ringPos = [];
    for (const y of [0.65, 2.6, 4.55]) {
      for (let k = 0; k < 48; k++) {
        const a0 = (k / 48) * Math.PI * 2, a1 = ((k + 1) / 48) * Math.PI * 2;
        ringPos.push(Math.cos(a0) * 0.457, y, Math.sin(a0) * 0.457, Math.cos(a1) * 0.457, y, Math.sin(a1) * 0.457);
      }
    }
    g.add(fatLines(ringPos, { color: 0xffb703, width: 2, clip: [sp.fe] }));
    scene.add(g);
    objs.push({ g, sp, top: 5.4 });
  }
  // 2) suction anchor -> shell mid-surface mesh
  {
    const sp = scanPlanes();
    const g = new THREE.Group();
    g.position.x = X[1];
    const s = 0.55;
    const R = 2.5 * s, Hh = 9.0 * s;
    const m = new THREE.MeshStandardMaterial({ color: 0xc89a1a, metalness: 0.2, roughness: 0.55, envMap: env3, side: THREE.DoubleSide, clippingPlanes: [sp.real] });
    const skirt = new THREE.Mesh(new THREE.CylinderGeometry(R, R, Hh, 64, 1, true), m);
    skirt.position.y = Hh / 2;
    const lid = new THREE.Mesh(new THREE.CylinderGeometry(R * 1.02, R * 1.02, 0.12, 64), m);
    lid.position.y = Hh;
    g.add(skirt, lid);
    const pos = [];
    const na = 28, nz = 12;
    for (let i = 0; i < na; i++) {
      const a0 = (i / na) * Math.PI * 2, a1 = ((i + 1) / na) * Math.PI * 2;
      for (let j = 0; j <= nz; j++) {
        const y = (Hh * j) / nz;
        pos.push(Math.cos(a0) * R, y, Math.sin(a0) * R, Math.cos(a1) * R, y, Math.sin(a1) * R);
      }
      pos.push(Math.cos(a0) * R, 0, Math.sin(a0) * R, Math.cos(a0) * R, Hh, Math.sin(a0) * R);
    }
    // lid mesh: rings and spokes
    for (let k = 1; k <= 3; k++) {
      const r = (R * k) / 3;
      for (let i = 0; i < na; i++) {
        const a0 = (i / na) * Math.PI * 2, a1 = ((i + 1) / na) * Math.PI * 2;
        pos.push(Math.cos(a0) * r, Hh, Math.sin(a0) * r, Math.cos(a1) * r, Hh, Math.sin(a1) * r);
      }
    }
    for (let i = 0; i < na; i += 2) { const a = (i / na) * Math.PI * 2; pos.push(0, Hh, 0, Math.cos(a) * R, Hh, Math.sin(a) * R); }
    const shellMat = new THREE.MeshStandardMaterial({ color: 0x2a6f8f, metalness: 0, roughness: 0.8, transparent: true, opacity: 0.55, side: THREE.DoubleSide, clippingPlanes: [sp.fe], depthWrite: false });
    const surf = new THREE.Mesh(new THREE.CylinderGeometry(R, R, Hh, 64, 1, true), shellMat);
    surf.position.y = Hh / 2;
    g.add(surf);
    g.add(fatLines(pos, { color: 0x4cc9f0, width: 1.6, clip: [sp.fe] }));
    scene.add(g);
    objs.push({ g, sp, top: Hh + 0.3 });
  }
  // 3) wellhead housings -> solid hex mesh (the real local FE mesh)
  {
    const sp = scanPlanes();
    const g = new THREE.Group();
    g.position.x = X[2];
    const s = 1.45;
    const real = makeWellhead(env3, { zBottom: 0.5, segments: 96, clipPlanes: [sp.real], only: ['conductor', 'lpwh', 'casing', 'hpwhh', 'lockring'] });
    real.rotation.y = Math.PI;
    const wrap = new THREE.Group();
    wrap.add(real);
    // half-section: also cut real geometry by the symmetry plane so both look alike
    const fe = makeLocalFE(ctx.data.wellhead_surface, { env: env3, edgeColor: 0x0d2233, edgeOpacity: 0.7 });
    fe.userData.set(0, 0, 'solid', [0.62, 0.70, 0.78]);
    const y0 = new THREE.Plane(new THREE.Vector3(0, 1, 0), -0.5);
    fe.userData.mat.clippingPlanes = [sp.fe, y0];
    fe.userData.emat.clippingPlanes = [sp.fe, y0];
    fe.userData.mat.toneMapped = true;
    wrap.add(fe);
    wrap.scale.setScalar(s);
    wrap.position.y = -0.5 * s;
    g.add(wrap);
    scene.add(g);
    objs.push({ g, sp, top: 3.7 * s - 0.5 * s, scale: s, fe, real });
  }
  // 4) axisymmetric section (2D quad mesh of the same housings)
  {
    const g = new THREE.Group();
    g.position.x = X[3];
    const s = 1.45;
    const prof = ctx.data.wellhead_local.profile;
    const pts = prof.pts, Q = prof.quads, body = prof.body;
    const pos = [], col = [], idx = [];
    const bc = { casing: [0.16, 0.2, 0.25], hpwhh: [0.32, 0.38, 0.45], cement: [0.2, 0.15, 0.08], conductor: [0.06, 0.12, 0.2], lpwh: [0.08, 0.2, 0.36] };
    let vi = 0;
    const lines = [];
    Q.forEach((q, k) => {
      const ok = pts[q[0]][1] >= 0.5 - 1e-6 && pts[q[2]][1] >= 0.5 - 1e-6;
      if (!ok) return;
      const c = bc[body[k]];
      for (const n of q) { pos.push(pts[n][0], pts[n][1], 0); col.push(...c); }
      idx.push(vi, vi + 1, vi + 2, vi, vi + 2, vi + 3);
      for (let e = 0; e < 4; e++) { const a = pts[q[e]], b = pts[q[(e + 1) % 4]]; lines.push(a[0], a[1], 0.001, b[0], b[1], 0.001); }
      vi += 4;
    });
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    geo.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
    geo.setIndex(idx);
    const sec = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ vertexColors: true, side: THREE.DoubleSide, transparent: true }));
    const wrap = new THREE.Group();
    wrap.add(sec);
    const el = new THREE.LineSegments(new THREE.BufferGeometry().setAttribute('position', new THREE.Float32BufferAttribute(lines, 3)),
      new THREE.LineBasicMaterial({ color: 0x0d2233, transparent: true, opacity: 0.8 }));
    wrap.add(el);
    // axis of revolution
    const axis = fatLines([0, 0.2, 0, 0, 4.0, 0], { color: 0xffb703, width: 2.5 });
    wrap.add(axis);
    // revolve ghost
    const ghost = new THREE.Mesh(new THREE.CylinderGeometry(0.48, 0.48, 3.1, 48, 1, true, 0, Math.PI * 1.25),
      new THREE.MeshBasicMaterial({ color: 0x4cc9f0, transparent: true, opacity: 0.08, side: THREE.DoubleSide, depthWrite: false }));
    ghost.position.y = 2.05;
    wrap.add(ghost);
    wrap.scale.setScalar(s);
    wrap.position.y = -0.5 * s;
    g.add(wrap);
    scene.add(g);
    objs.push({ g, top: 3.7 * s - 0.5 * s, sec, el, ghost, axis, scale: s });
  }

  const e1 = cue('e1'), e2 = cue('e2'), e3 = cue('e3'), e4 = cue('e4'), e5 = cue('e5');
  const focus = (i) => ({ pos: [X[i] + 4.2, 3.4, 10.5], tgt: [X[i] + 3.2, 2.3, 0] });
  const camf = cameraPath(cam, [
    { t: 0, pos: [0, 5, 31], tgt: [0, 2.4, 0], fov: 32 },
    { t: e2 - 0.4, pos: [0, 4.6, 29], tgt: [0, 2.4, 0], fov: 32, e: ease.inOutSine },
    { t: e2 + 1.2, ...focus(0), fov: 32 },
    { t: e3 - 0.2, ...focus(0), fov: 32, e: ease.inOutSine },
    { t: e3 + 1.2, pos: [X[1] + 5.2, 4.4, 13.5], tgt: [X[1] + 4.0, 2.4, 0], fov: 32 },
    { t: e4 - 0.2, pos: [X[1] + 5.0, 4.6, 13.2], tgt: [X[1] + 4.0, 2.4, 0], fov: 32, e: ease.inOutSine },
    { t: e4 + 1.2, ...focus(2), fov: 32 },
    { t: e5 - 0.2, ...focus(2), fov: 32, e: ease.inOutSine },
    { t: e5 + 1.2, pos: [X[3] + 2.3, 2.75, 7.4], tgt: [X[3] + 1.55, 2.3, 0], fov: 32 },
    { t: ctx.duration - 2.6, pos: [X[3] + 2.2, 2.7, 7.0], tgt: [X[3] + 1.55, 2.3, 0], fov: 32, e: ease.inOutSine },
    { t: ctx.duration, pos: [0, 5, 31], tgt: [0, 2.4, 0], fov: 32 },
  ]);

  const names = ['Beam', 'Shell', 'Solid', 'Axisymmetric'];
  const cols = [PAL.cyan, PAL.teal, PAL.amber, PAL.violet];
  const panels = [
    { t: e2, title: 'BEAM ELEMENT', rows: [
      ['Model', 'a line with a cross-section'], ['Assumes', 'slender member, L/D ≳ 10'], ['Gives', 'section forces and deflections'], ['Not', 'local stresses'],
    ], ex: 'Conductor: L/D ≈ 65', exT: at('e2', 'The conductor') },
    { t: e3, title: 'SHELL ELEMENT', rows: [
      ['Model', 'mid-surface + thickness'], ['Assumes', 'thin wall: t ≪ R, L'], ['Gives', 'membrane + bending stress'],
    ], ex: 'Anchor skirt: R/t ≈ 100', exT: at('e3', 'like the skirt') },
    { t: e4, title: 'SOLID ELEMENT', rows: [
      ['Model', 'the full 3D volume'], ['Assumes', 'nothing about the geometry'], ['Cost', 'most general, most expensive'],
    ], ex: 'HP housing: t/R ≈ 1/3', exT: at('e4', 'like the wellhead') },
    { t: e5, title: 'AXISYMMETRIC ELEMENT', rows: [
      ['Model', 'a 2D section of a solid of revolution'], ['Requires', 'geometry, loads and supports symmetric about the axis'], ['Gives', 'the full 3D answer at 2D cost'],
    ], ex: '', exT: 1e9 },
  ];
  const sweeps = [[e2 + 2.0, 3.0], [e3 + 1.6, 2.6], [e4 + 1.8, 3.0]];

  return {
    sfx: [{ t: 0.1, type: 'chapter' }, { t: e2 + 2.0, type: 'scan' }, { t: e3 + 1.6, type: 'scan' }, { t: e4 + 1.8, type: 'scan' }],
    render(t) {
      back.render(renderer);
      // mesh sweeps
      objs.slice(0, 3).forEach((o, i) => {
        const [ts, d] = sweeps[i];
        const p = seg(t, ts, d, ease.inOutSine);
        o.sp.set(p <= 0 ? -1 : p >= 1 ? 100 : lerp(-0.2, o.top + 0.2, p));
      });
      // axisymmetric object: section appears, ghost revolve hint
      const ax = objs[3];
      const ap = seg(t, e5 + 0.6, 1.2);
      ax.sec.material.opacity = 0.6 + 0.4 * ap;
      // only the focused object (and its neighbour during camera moves) is shown
      const vis = [true, true, true, true];
      const wide = t < e2 + 0.6 || t > ctx.duration - 2.2;
      if (!wide) {
        const k = t < e3 ? 0 : t < e4 ? 1 : t < e5 ? 2 : 3;
        const kt = [e2, e3, e4, e5][k];
        for (let i = 0; i < 4; i++) vis[i] = i === k || (i === k - 1 && t < kt + 1.0);
      }
      objs.forEach((o, i) => { o.g.visible = vis[i]; });
      ax.ghost.material.opacity = 0.02 + 0.07 * seg(t, at('e5', 'symmetric about'), 1.0) * (0.6 + 0.4 * Math.sin(t * 2));
      ax.ghost.rotation.y = t * 0.6;
      objs.forEach((o, i) => { o.g.rotation.y = i === 3 ? -0.15 : Math.sin(t * 0.2 + i) * 0.25 + (i === 2 ? 0.6 : 0); });
      camf(t);
      renderViewport(renderer, scene, cam, 0, 0, 1920, 1080);

      // labels under objects in the overview
      const ov = Math.max(env(t, e1 + 0.5, e2 + 0.3, 0.6, 0.5), env(t, ctx.duration - 2.2, 1e9, 0.6, 0.5));
      if (ov > 0) {
        X.forEach((x, i) => {
          const [px, py] = toScreen([x, -0.6, 0], cam);
          d2.text(names[i], px, py + 20, { size: 34, weight: 750, color: cols[i], align: 'center', alpha: ov * seg(t, e1 + 0.5 + i * 0.35, 0.5) });
        });
      }
      // rule panels
      panels.forEach((P, i) => {
        const tEnd = i < 3 ? panels[i + 1].t - 0.2 : ctx.duration - 2.8;
        const a = env(t, P.t + 0.8, tEnd, 0.6, 0.5);
        if (a <= 0) return;
        const x = 1060, y = 230, w = 760;
        const wrapped = P.rows.map(([k, v]) => d2.wrap(v, w - 80, 30, 600));
        const rowsH = wrapped.reduce((acc, l) => acc + 58 + l.length * 36, 0);
        const h = 110 + rowsH + (P.ex ? 90 : 0);
        d2.panel(x, y, w, h, { alpha: a, accent: cols[i] });
        d2.text(P.title, x + 40, y + 64, { size: 34, weight: 800, color: cols[i], alpha: a, ls: 2 });
        let yy0 = y + 118;
        P.rows.forEach(([k, v], j) => {
          const q = seg(t, P.t + 1.2 + j * 0.7, 0.6, ease.out);
          d2.text(k.toUpperCase(), x + 40, yy0 + 14, { size: 18, weight: 700, color: PAL.ink3, ls: 2, alpha: a * q });
          wrapped[j].forEach((ln, k2) => d2.text(ln, x + 40, yy0 + 50 + k2 * 36, { size: 30, weight: 600, alpha: a * q }));
          yy0 += 58 + wrapped[j].length * 36;
        });
        if (P.ex) {
          const q = seg(t, P.exT, 0.6, ease.outBack);
          const yy = yy0 + 22;
          d2.check(x + 62, yy + 8, 22, { progress: q, alpha: a });
          d2.text(P.ex, x + 100, yy + 20, { size: 32, weight: 700, color: PAL.green, alpha: a * clamp(q) });
        }
      });
      // object-specific annotations
      const bA = env(t, at('e2', 'with a cross-section'), e3 - 0.3, 0.5, 0.5);
      if (bA > 0) {
        const [px, py] = toScreen([X[0] + 0.5, 4.55, 0], cam);
        d2.text('cross-section', px + 70, py - 10, { size: 24, weight: 650, color: PAL.amber, alpha: bA, shadow: true });
        d2.line(px + 8, py, px + 64, py - 16, { color: PAL.amber, width: 1.5, alpha: bA });
        const [nx, ny] = toScreen([X[0], 3.25, 0], cam);
        d2.text('nodes', nx + 70, ny + 8, { size: 24, weight: 650, color: PAL.ink, alpha: bA, shadow: true });
        d2.line(nx + 10, ny, nx + 64, ny, { color: PAL.ink2, width: 1.5, alpha: bA });
      }
      const sA = env(t, at('e3', 'mid-surface'), e4 - 0.3, 0.5, 0.5);
      if (sA > 0) {
        const [px, py] = toScreen([X[1] + 1.375, 2.4, 0.2], cam);
        d2.text('mid-surface mesh', px + 30, py, { size: 24, weight: 650, color: PAL.cyan, alpha: sA, shadow: true });
        d2.text('thickness t is a property', px + 30, py + 30, { size: 20, color: PAL.ink2, alpha: sA, shadow: true });
      }
      const xA = env(t, at('e5', 'axisymmetric element'), ctx.duration - 2.6, 0.5, 0.5);
      if (xA > 0) {
        const [px, py] = toScreen([X[3], 3.15 * 1.45 - 0.5 * 1.45, 0], cam);
        d2.text('axis of symmetry', px + 14, py, { size: 26, weight: 650, color: PAL.amber, alpha: xA, shadow: true });
        const [qx, qy] = toScreen([X[3] + 0.42 * 1.45, 2.0 * 1.45 - 0.5 * 1.45, 0], cam);
        d2.text('2D section', px - 30, qy - 20, { size: 28, weight: 700, color: PAL.violet, align: 'right', alpha: xA, shadow: true });
        d2.text('quadrilateral mesh', px - 30, qy + 12, { size: 22, weight: 500, color: PAL.ink2, align: 'right', alpha: xA, shadow: true });
        d2.text('r', qx + 40, qy + 40, { size: 1, alpha: 0 });
      }
      chapterCard(d2, t, 1, 'Choosing the element type', 'Beam · Shell · Solid · Axisymmetric', { t0: 0, hold: 2.2 });
    },
  };
}
