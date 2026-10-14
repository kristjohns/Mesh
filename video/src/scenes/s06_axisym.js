// Axisymmetric shortcut, when it fails (bending + lift-off), and the half model with symmetry.
import * as THREE from 'three';
import { makeBackdrop, renderViewport, studioScene, envMap, fatLines, toScreen } from '../engine/env.js';
import { makeLocalFE, colorBar } from '../models/femesh.js';
import { keyLine } from './common.js';
import { PAL, seg, env, ease, clamp, lerp, rgba, turboCss, turbo } from '../engine/util.js';

// draw the 2D axisymmetric mesh (r,z) with nodal values
export function drawSection(d2, prof, vals, o) {
  const { x0, y0, s } = o; // screen = (x0 + r*s, y0 - z*s)
  const a = o.alpha ?? 1;
  if (a <= 0) return;
  const pts = prof.pts;
  const vmax = o.vmax ?? 120;
  const g = d2.g;
  g.save();
  g.globalAlpha = a;
  if (o.clip) { g.beginPath(); g.rect(...o.clip); g.clip(); }
  prof.quads.forEach((q, k) => {
    const zc = (pts[q[0]][1] + pts[q[2]][1]) / 2;
    if (o.zmin !== undefined && zc < o.zmin) return;
    const P = q.map((n) => [x0 + pts[n][0] * s, y0 - pts[n][1] * s]);
    let fill;
    if (vals) {
      const v = (vals[q[0]] + vals[q[1]] + vals[q[2]] + vals[q[3]]) / 4;
      fill = turboCss(v / vmax);
    } else fill = o.fill ?? 'rgba(160,180,200,0.25)';
    g.beginPath();
    g.moveTo(P[0][0], P[0][1]);
    for (let i = 1; i < 4; i++) g.lineTo(P[i][0], P[i][1]);
    g.closePath();
    g.fillStyle = fill;
    g.fill();
    if (o.edges !== false) { g.strokeStyle = o.edgeColor ?? 'rgba(6,16,26,0.55)'; g.lineWidth = o.edgeW ?? 0.7; g.stroke(); }
  });
  g.restore();
}

// contact line force around the shoulder (top view ring)
export function contactRing(d2, res, s, cx, cy, R, o = {}) {
  const a = o.alpha ?? 1;
  if (a <= 0) return;
  const n = res.length;
  s = clamp(s, 0, n - 1);
  const i0 = Math.floor(s), i1 = Math.min(n - 1, i0 + 1), f = s - i0;
  const A = res[i0].shoulder_theta, B = res[i1].shoulder_theta;
  const line = A.map((p, k) => p.line * (1 - f) + B[k].line * f);
  const th = A.map((p) => p.theta);
  const full = [];
  for (let k = 0; k < th.length; k++) full.push([th[k], line[k]]);
  for (let k = th.length - 2; k > 0; k--) full.push([2 * Math.PI - th[k], line[k]]);
  full.sort((p, q) => p[0] - q[0]);
  full.push([2 * Math.PI, full[0][1]]);
  const vmax = o.vmax ?? 10e6;
  const W = o.width ?? 46;
  // base ring
  d2.circle(cx, cy, R, { stroke: 'rgba(160,190,210,0.25)', width: 2, alpha: a });
  for (let k = 0; k < full.length - 1; k++) {
    const [t0, v0] = full[k], [t1, v1] = full[k + 1];
    const v = (v0 + v1) / 2;
    const g = d2.g;
    // screen angle: theta=0 -> +x (right), theta increases counter-clockwise (screen up)
    const a0 = -t0, a1 = -t1;
    if (v < 1e3) {
      g.save();
      g.globalAlpha = a;
      g.setLineDash([6, 6]);
      g.strokeStyle = 'rgba(200,210,220,0.6)';
      g.lineWidth = 3;
      g.beginPath();
      g.arc(cx, cy, R, a0, a1, true);
      g.stroke();
      g.restore();
      continue;
    }
    const w = 6 + W * clamp(v / vmax);
    g.save();
    g.globalAlpha = a;
    g.strokeStyle = turboCss(clamp(v / vmax));
    g.lineWidth = w;
    g.beginPath();
    g.arc(cx, cy, R, a0, a1 - 0.002, true);
    g.stroke();
    g.restore();
  }
  if (o.labels !== false) {
    d2.text('compression side', cx + R + 40, cy + 8, { size: 22, weight: 650, color: PAL.ink2, alpha: a });
    d2.text('tension side', cx - R - 40, cy + 8, { size: 22, weight: 650, color: PAL.ink2, align: 'right', alpha: a });
  }
  return line;
}

export default async function axisym(ctx) {
  const { d2, cue, at, renderer, data } = ctx;
  const L = data.wellhead_local;
  const prof = L.profile;
  const back = makeBackdrop();
  const fe = studioScene();
  const local = makeLocalFE(data.wellhead_surface, { vmax: 160, env: envMap(renderer) });
  local.userData.mat.toneMapped = false;
  const ycut = new THREE.Plane(new THREE.Vector3(0, 1, 0), -0.5);
  const sweep = new THREE.Plane(new THREE.Vector3(0, 0, 1), 0);
  local.userData.mat.clippingPlanes = [ycut, sweep];
  local.userData.emat.clippingPlanes = [ycut, sweep];
  fe.add(local);
  // moving 2D section on the sweep plane
  const secGeo = new THREE.BufferGeometry();
  {
    const pos = [], idx = [];
    let v = 0;
    prof.quads.forEach((q) => {
      if (prof.pts[q[0]][1] < 0.5 - 1e-6) return;
      for (const n of q) pos.push(prof.pts[n][0], prof.pts[n][1], 0);
      idx.push(v, v + 1, v + 2, v, v + 2, v + 3);
      v += 4;
    });
    secGeo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    secGeo.setIndex(idx);
  }
  const secMesh = new THREE.Mesh(secGeo, new THREE.MeshBasicMaterial({ color: 0xa78bfa, transparent: true, opacity: 0.85, side: THREE.DoubleSide, depthWrite: false }));
  const secPivot = new THREE.Group();
  secPivot.add(secMesh);
  fe.add(secPivot);
  // symmetry plane
  const symPlane = new THREE.Mesh(new THREE.PlaneGeometry(1.5, 3.6), new THREE.MeshBasicMaterial({ color: 0x4cc9f0, transparent: true, opacity: 0, side: THREE.DoubleSide, depthWrite: false }));
  symPlane.position.set(0, 2.1, 0.002);
  fe.add(symPlane);
  const symEdge = fatLines([-0.75, 0.3, 0, 0.75, 0.3, 0, 0.75, 0.3, 0, 0.75, 3.9, 0, 0.75, 3.9, 0, -0.75, 3.9, 0, -0.75, 3.9, 0, -0.75, 0.3, 0], { color: 0x4cc9f0, width: 2, transparent: true });
  fe.add(symEdge);
  const cam = new THREE.PerspectiveCamera(19, 1, 0.01, 100);
  const a1 = cue('a1'), a2 = cue('a2'), a3 = cue('a3'), a4 = cue('a4'), a5 = cue('a5');
  const res = L.results;

  return {
    sfx: [{ t: a2 + 0.5, type: 'whoosh' }],
    render(t) {
      back.render(renderer);
      // ------------- 3D part (a2 .. end)
      const tA = env(t, a2 + 0.2, ctx.duration, 0.7, 0.5);
      let ms = 0;
      if (tA > 0) {
        const sw = seg(t, a2 + 0.4, 4.5, ease.inOutSine);
        const th = Math.PI * sw;
        // keep points with azimuth <= th (see derivation in notes)
        sweep.normal.set(-Math.sin(th) * -1, 0, 0).set(Math.sin(th), 0, Math.cos(th));
        sweep.normal.set(Math.sin(th), 0, Math.cos(th));
        // points kept: n.p >= 0 ; with p = (r cos phi, ., -r sin phi): r sin(th) cos(phi) - r cos(th) sin(phi) = r sin(th - phi)
        sweep.constant = sw >= 1 ? 10 : 0;
        secPivot.rotation.y = th;
        secMesh.visible = sw > 0 && sw < 1;
        ms = 12 * seg(t, at('a3', 'squeezes') - 0.5, 6.0, ease.inOutSine) * (1 - seg(t, a5 + 0.5, 1.5));
        local.userData.set(ms, 20 * seg(t, a3, 1.0));
        const ang = lerp(-0.33, -1.0, seg(t, a4, 2.0, ease.inOutSine));
        const r = lerp(9.9, 9.0, seg(t, a4, 2.0));
        cam.position.set(Math.sin(ang) * r, lerp(3.0, 4.2, seg(t, a4, 2.0)), Math.cos(ang) * r);
        cam.lookAt(0, 1.95, -0.1);
        const sp = env(t, at('a4', 'symmetric about that plane') - 0.4, ctx.duration, 0.6, 0.5);
        symPlane.material.opacity = 0.18 * sp;
        symEdge.material.opacity = sp;
        symEdge.visible = sp > 0.01;
        local.position.y = (1 - ease.out(clamp(tA * 1.4))) * -0.4;
        renderViewport(renderer, fe, cam, 1080, 120, 760, 880);
        colorBar(d2, 1820, 640, 20, 260, 0, 160, 'MPa', { alpha: tA * seg(t, a3, 1) });
      }
      // ------------- a1: axisymmetric section + preload contour
      const sA = env(t, a1 - 0.3, a3 + 0.6, 0.6, 0.6);
      if (sA > 0) {
        const p = seg(t, a1, 1.6, ease.inOutSine);
        // full section (left)
        d2.line(170, 130, 170, 1010, { color: PAL.amber, width: 2, dash: [10, 8], alpha: sA });
        d2.text('axis', 170, 118, { size: 20, weight: 700, color: PAL.amber, align: 'center', alpha: sA });
        drawSection(d2, prof, seg(t, at('a1', 'solves') - 0.3, 0.8) > 0 ? L.axi.vm_nodal : null, { x0: 170, y0: 1060, s: 280, alpha: sA * p, vmax: 120, zmin: 0.3, edgeW: 0.5 });
        // zoom on the shoulder
        const zx = 320, zy = 160, zw = 640, zh = 760;
        const zp = seg(t, at('a1', 'quadrilateral') - 0.5, 1.0, ease.inOutSine);
        if (zp > 0) {
          d2.panel(zx, zy, zw, zh, { alpha: sA * zp, fill: 'rgba(6,14,24,0.9)' });
          const s = 1250;
          drawSection(d2, prof, seg(t, at('a1', 'solves') - 0.3, 0.8) > 0 ? L.axi.vm_nodal : null,
            { x0: zx + zw / 2 - 0.40 * s, y0: zy + zh / 2 + 2.3 * s, s, alpha: sA * zp, vmax: 120, clip: [zx + 2, zy + 2, zw - 4, zh - 4], edgeW: 0.8 });
          // zoom frame on the full section
          const fx = 170 + 0.29 * 280, fy = 1060 - 2.6 * 280;
          d2.rect(fx, fy, 0.22 * 280, 0.6 * 280, { stroke: PAL.cyan, width: 2, alpha: sA * zp });
          d2.line(fx + 0.22 * 280, fy, zx, zy, { color: PAL.cyan, width: 1.2, alpha: sA * zp * 0.6 });
          d2.line(fx + 0.22 * 280, fy + 0.6 * 280, zx, zy + zh, { color: PAL.cyan, width: 1.2, alpha: sA * zp * 0.6 });
          const X0 = zx + zw / 2 - 0.40 * s, Y0 = zy + zh / 2 + 2.3 * s;
          d2.rect(X0 + 0.372 * s, Y0 - 2.517 * s, 0.056 * s, 0.067 * s, { fill: 'rgba(120,135,145,0.9)', stroke: '#0a1622', width: 1, alpha: sA * zp });
          const lx = X0 + 0.47 * s + 26;
          d2.line(X0 + 0.428 * s, Y0 - 2.483 * s, lx, Y0 - 2.483 * s, { color: PAL.ink2, width: 1.5, alpha: sA * zp });
          d2.tag('lock ring', lx, Y0 - 2.483 * s, { size: 20, alpha: sA * zp, color: PAL.ink2, textColor: PAL.ink, fill: 'rgba(6,14,24,0.92)' });
          d2.line(X0 + 0.405 * s, Y0 - 2.2 * s, lx, Y0 - 2.2 * s, { color: PAL.ink2, width: 1.5, alpha: sA * zp });
          d2.tag('shoulder', lx, Y0 - 2.2 * s, { size: 20, alpha: sA * zp, color: PAL.ink2, textColor: PAL.ink, fill: 'rgba(6,14,24,0.92)' });
          d2.rect(zx + 2, zy + 2, zw - 4, 60, { fill: 'rgba(6,14,24,0.92)', alpha: sA * zp });
          d2.text('landing shoulder & lock ring', zx + 20, zy + 40, { size: 24, weight: 650, alpha: sA * zp });
        }
        const tagHide = 1 - seg(t, at('a2', 'agree') - 0.6, 0.5);
        const cA = sA * seg(t, at('a1', 'about a thousand') - 0.2, 0.6) * tagHide;
        d2.tag(`${L.n2d_quad.toLocaleString('en-US')} quadrilaterals`, 330, 980, { size: 22, alpha: cA, color: PAL.violet });
        d2.tag('solves in 0.1 s', 700, 980, { size: 22, alpha: sA * seg(t, at('a1', 'solves'), 0.6) * tagHide, color: PAL.green });
        if (seg(t, at('a1', 'solves'), 0.6) > 0) colorBar(d2, 990, 640, 18, 260, 0, 120, 'MPa', { alpha: sA * seg(t, at('a1', 'solves'), 0.6) });
      }
      // ------------- a2 counters + agreement
      const nA = env(t, a2 + 1.0, a3 + 0.3, 0.6, 0.5);
      if (nA > 0) {
        d2.text('Revolve the section →', 1460, 95, { size: 28, weight: 700, align: 'center', alpha: nA });
        const q = seg(t, at('a2', 'thirty-seven'), 1.4, ease.out);
        d2.panel(1000, 960, 860, 90, { alpha: nA * clamp(q * 3) });
        d2.text(`${Math.round(L.n3d_hex * q).toLocaleString('en-US')} hexahedra`, 1040, 1015, { size: 30, weight: 750, alpha: nA * clamp(q * 3), color: PAL.cyan });
        d2.text(`${Math.round(L.n3d_dof * seg(t, at('a2', 'a hundred and forty'), 1.2, ease.out)).toLocaleString('en-US')} degrees of freedom`, 1400, 1015, { size: 30, weight: 750, alpha: nA * seg(t, at('a2', 'a hundred and forty'), 0.5) });
        const gA = nA * seg(t, at('a2', 'agree'), 0.6);
        if (gA > 0) {
          d2.panel(330, 880, 660, 120, { alpha: gA, accent: PAL.green });
          d2.check(380, 940, 22, { progress: seg(t, at('a2', 'agree'), 0.8), alpha: gA });
          d2.text('Pre-load only: 2D vs 3D', 420, 928, { size: 28, weight: 700, alpha: gA });
          d2.text('peak stress differs by < 0.1 %', 420, 966, { size: 26, weight: 600, color: PAL.green, alpha: gA });
        }
      }
      // ------------- a3: bending breaks axisymmetry -> contact ring
      const bA = env(t, a3 + 0.3, a4 + 0.4, 0.6, 0.6);
      if (bA > 0) {
        d2.text('Bending is not axisymmetric', 520, 150, { size: 44, weight: 800, align: 'center', alpha: bA });
        const R = 230;
        d2.panel(140, 220, 760, 640, { alpha: bA });
        d2.text('Landing-shoulder contact, top view', 180, 270, { size: 26, weight: 700, alpha: bA });
        d2.text('line force around the circumference (FE result)', 180, 304, { size: 20, color: PAL.ink2, alpha: bA });
        contactRing(d2, res, ms, 520, 570, R, { alpha: bA, vmax: 10e6 });
        const M = lerp(0, 3, ms / 12);
        d2.text(`M = ${M.toFixed(2)} MNm`, 520, 580, { size: 34, weight: 800, align: 'center', color: PAL.amber, alpha: bA });
        const op = res[Math.round(ms)].open_frac;
        d2.text(op > 0.001 ? `${Math.round(op * 100)} % of the shoulder open` : 'fully in contact', 520, 622, { size: 22, weight: 600, align: 'center', color: op > 0 ? PAL.red : PAL.green, alpha: bA });
        const xA = bA * seg(t, at('a3', 'cannot represent'), 0.6);
        if (xA > 0) {
          d2.panel(140, 880, 760, 100, { alpha: xA, accent: PAL.red });
          d2.cross(190, 930, 20, { progress: seg(t, at('a3', 'cannot represent'), 0.8), alpha: xA });
          d2.text('an axisymmetric section cannot show this', 230, 940, { size: 28, weight: 700, color: PAL.red, alpha: xA });
        }
        // moment arrow over the 3D model
        const [px, py] = [1460, 165];
        d2.momentArrow(px, py, 60, Math.PI * 0.95, Math.PI * 0.05 + Math.PI * 0.9 * 0, { color: PAL.amber, width: 5, alpha: bA * seg(t, at('a3', 'squeezes') - 0.6, 0.6), progress: seg(t, at('a3', 'squeezes') - 0.6, 1.0) });
      }
      // ------------- a4: half model + symmetry
      const hA = env(t, a4 + 0.4, ctx.duration, 0.6, 0.5);
      if (hA > 0) {
        d2.text('Go 3D, but model only half', 520, 150, { size: 44, weight: 800, align: 'center', alpha: hA });
        // schematic: full circle -> half with symmetry plane
        const cx = 520, cy = 470;
        const p1 = seg(t, at('a4', 'Bending in one plane') - 0.3, 1.0);
        d2.circle(cx, cy, 170, { stroke: rgba(PAL.ink2, 0.4), width: 3, alpha: hA });
        d2.g.save();
        d2.g.globalAlpha = hA;
        d2.g.beginPath();
        d2.g.arc(cx, cy, 170, Math.PI, 2 * Math.PI);
        d2.g.lineWidth = 34;
        d2.g.strokeStyle = rgba(PAL.cyan, 0.35);
        d2.g.stroke();
        d2.g.restore();
        d2.line(cx - 240, cy, cx + 240, cy, { color: PAL.cyan, width: 3, alpha: hA * p1, progress: p1 });
        d2.text('plane of bending = symmetry plane', cx, cy + 76, { size: 24, weight: 650, color: PAL.cyan, align: 'center', alpha: hA * p1 });
        d2.arrow(cx - 120, cy - 260, cx + 120, cy - 260, { color: PAL.amber, width: 4, alpha: hA * p1 });
        d2.text('bending direction', cx, cy - 280, { size: 22, color: PAL.amber, align: 'center', alpha: hA * p1 });
        // roller symbols on the plane
        const p2 = seg(t, at('a4', 'symmetry condition'), 0.8);
        for (let k = -3; k <= 3; k++) {
          if (k === 0) continue;
          const x = cx + k * 52;
          d2.poly([[x, cy + 4], [x - 12, cy + 26], [x + 12, cy + 26]], { stroke: PAL.cyan, width: 2, alpha: hA * p2 });
          d2.circle(x - 6, cy + 32, 4, { stroke: PAL.cyan, width: 1.5, alpha: hA * p2 });
          d2.circle(x + 6, cy + 32, 4, { stroke: PAL.cyan, width: 1.5, alpha: hA * p2 });
        }
        if (p2 > 0) {
          d2.panel(170, 640, 700, 150, { alpha: hA * p2, accent: PAL.cyan });
          d2.text('Symmetry condition on the cut face:', 210, 695, { size: 28, weight: 700, alpha: hA * p2 });
          ctx.tex.show('s06un', 'u_n = 0', 210, 720, { size: 44, alpha: hA * p2, color: PAL.cyan });
          d2.text('(no displacement normal to the plane)', 400, 762, { size: 22, color: PAL.ink2, alpha: hA * p2 });
        }
      }
      keyLine(d2, t, a5 + 0.1, ctx.duration - 0.3, 'Cheapest element that captures the physics — and know what rules it out', { size: 32, y: 960, accent: PAL.green });
    },
  };
}
