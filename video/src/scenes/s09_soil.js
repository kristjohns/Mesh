// Chapter 3: the soil. Continuum vs Winkler springs, p-y curves, loading, mesh, fixity, bounds, coupling.
import * as THREE from 'three';
import { makeBackdrop, renderViewport, studioScene, envMap, fatLines, cameraPath, toScreen } from '../engine/env.js';
import { makeWellhead } from '../models/wellhead.js';
import { soilSection } from '../models/soil.js';
import { chapterCard, keyLine } from './common.js';
import { drawGlobal, mobColor } from './globaldiag.js';
import { interp } from './s03_strategy.js';
import { Plot } from '../engine/draw2d.js';
import { PAL, seg, env, ease, clamp, lerp, rgba } from '../engine/util.js';

export default async function soilScene(ctx) {
  const { d2, cue, at, renderer, data, tex } = ctx;
  const G = data.global;
  const B = G.base;
  const back = makeBackdrop();
  const p = {};
  for (let i = 1; i <= 10; i++) p[i] = cue('p' + i);
  // ------------------------------------------------------------ 3D: conductor in a soil block
  const S3 = studioScene({ hemi: 1.2 });
  const env3 = envMap(renderer);
  const cut = new THREE.Plane(new THREE.Vector3(0, 0, -1), 0);
  const wh = makeWellhead(env3, { zBottom: -30, segments: 96, clipPlanes: [cut], only: ['conductor', 'lpwh', 'casing', 'cement', 'hpwhh'] });
  wh.rotation.y = Math.PI / 2;
  wh.userData.setCut(true);
  S3.add(wh);
  const face = soilSection({ width: 36, depth: 32, holeHalf: 0.459, holeDepth: 30, fade: 0 });
  face.position.z = -0.003;
  S3.add(face);
  const top = new THREE.Mesh(new THREE.PlaneGeometry(36, 18), new THREE.MeshStandardMaterial({ color: 0x6d6352, roughness: 1 }));
  top.rotation.x = -Math.PI / 2;
  top.position.set(0, 0, -9);
  S3.add(top);
  // continuum mesh lines on the section face (graded towards the pile and the mudline)
  const mpos = [];
  const xs = [0.46];
  let dx = 0.25;
  while (xs[xs.length - 1] < 17) { xs.push(xs[xs.length - 1] + dx); dx *= 1.18; }
  const ys = [0];
  let dy = 0.3;
  while (ys[ys.length - 1] > -30) { ys.push(ys[ys.length - 1] - dy); dy *= 1.12; }
  for (const sgn of [1, -1]) {
    for (const x of xs) mpos.push(sgn * x, 0, 0.01, sgn * x, -30, 0.01);
    for (const y of ys) mpos.push(sgn * 0.46, y, 0.01, sgn * 17, y, 0.01);
  }
  const cmesh = fatLines(mpos, { color: 0x4cc9f0, width: 1.2, transparent: true, opacity: 0 });
  S3.add(cmesh);
  const cam3 = new THREE.PerspectiveCamera(35, 16 / 9, 0.1, 300);
  const camf = cameraPath(cam3, [
    { t: 0, pos: [16, 9, 36], tgt: [0, -7, 0], fov: 35 },
    { t: p[2], pos: [11, 6, 42], tgt: [0, -10, 0], fov: 35, e: ease.inOutSine },
    { t: p[3] + 1, pos: [8, 4, 46], tgt: [0, -12, 0], fov: 35, e: ease.inOutSine },
  ]);

  // ------------------------------------------------------------ helpers for the 2D diagram
  const springsZ = [];
  for (let z = 0; z >= -30; z -= 1) springsZ.push(z);
  const nodes1 = [];
  for (let z = 0; z >= -30; z -= 1) nodes1.push(z);
  nodes1.push(0.8, 1.7, 2.6, 3.6);
  const sZ = B.springs.map((s) => s.z);
  const uOf = (uo, ui) => (z) => (z <= 2.6 ? interp(B.zo, uo, z) : interp(B.zi, ui, z));
  const stepAt = (s) => {
    // fractional load step -> interpolated profiles
    const n = B.steps.length;
    if (s <= 0) return { uo: B.uo.map(() => 0), ui: B.ui.map(() => 0), mob: B.springs.map(() => 0), Mtot: B.Mtot.map(() => 0), Mi: B.Mi.map(() => 0), H: 0 };
    const x = s * n - 1;
    const i0 = Math.max(0, Math.floor(x)), i1 = Math.min(n - 1, i0 + 1), f = clamp(x - i0);
    const A = s * n < 1 ? null : B.steps[i0], Bb = B.steps[i1];
    const mix = (a, b, w) => a.map((v, k) => v * (1 - w) + b[k] * w);
    if (!A) { const w = s * n; const z0 = (arr) => arr.map(() => 0); return { uo: mix(z0(Bb.uo), Bb.uo, w), ui: mix(z0(Bb.ui), Bb.ui, w), mob: mix(z0(Bb.mob), Bb.mob, w), Mtot: mix(z0(Bb.Mtot), Bb.Mtot, w), Mi: mix(z0(Bb.Mi), Bb.Mi, w), H: Bb.H * w }; }
    return { uo: mix(A.uo, Bb.uo, f), ui: mix(A.ui, Bb.ui, f), mob: mix(A.mob, Bb.mob, f), Mtot: mix(A.Mtot, Bb.Mtot, f), Mi: mix(A.Mi, Bb.Mi, f), H: A.H * (1 - f) + Bb.H * f };
  };
  // above the mudline the total moment follows from statics: M = H (z_load - z)
  const totalM = (st) => (z) => (z > 0 ? st.H * (G.z_load - z) : interp(B.zmo, st.Mtot, z));
  const DX = 420, Y0 = 262, SY = 21; // diagram geometry
  const curves = G.py_curves;
  const pyPlot = () => new Plot(d2, { x: 1120, y: 230, w: 660, h: 440, xr: [0, 230], yr: [0, 320] });

  return {
    sfx: [{ t: 0.1, type: 'chapter' }, { t: p[3] + 0.2, type: 'whoosh' }, { t: p[6] + 0.4, type: 'whoosh' }, { t: p[10] + 0.3, type: 'whoosh' }],
    render(t) {
      back.render(renderer);
      // ================= 3D intro (p1, p2)
      const a3 = env(t, 0, p[3] + 1.0, 0.1, 1.0);
      if (a3 > 0) {
        camf(t);
        cmesh.material.opacity = seg(t, at('p2', 'continuum') - 0.4, 1.5);
        cmesh.visible = cmesh.material.opacity > 0.01;
        renderViewport(renderer, S3, cam3, 0, 0, 1920, 1080);
        d2.fadeRect(1 - a3, '#060f19');
        const la = a3 * seg(t, p[1] + 2.2, 0.8);
        const [cx, cy] = toScreen([0.46, -9, 0], cam3);
        d2.callout(cx, cy, cx + 260, cy - 60, 'Conductor', 'all lateral support comes from the soil', { alpha: la * (1 - seg(t, p[2], 0.5)), progress: seg(t, p[1] + 2.2, 1.0) });
        const ca = a3 * env(t, at('p2', 'continuum'), p[3] + 0.5, 0.5, 0.5);
        if (ca > 0) {
          d2.tag('OPTION 1 · SOIL AS A SOLID CONTINUUM', 960, 110, { size: 22, alpha: ca, align: 'center', color: PAL.cyan });
          const items = [['nonlinear soil model', at('p2', 'nonlinear soil')], ['interface elements', at('p2', 'interface')], ['a lot of calibration', at('p2', 'calibration')]];
          items.forEach(([s, tt], i) => {
            const q = seg(t, tt - 0.2, 0.5, ease.out);
            d2.panel(1300, 640 + i * 90, 470, 70, { alpha: ca * q, accent: PAL.amber });
            d2.warn(1340, 676 + i * 90, 14, { alpha: ca * q });
            d2.text(s, 1376, 685 + i * 90, { size: 28, weight: 650, alpha: ca * q });
          });
          d2.text('For a pile-like conductor there is a more efficient way →', 960, 1000, { size: 28, weight: 650, align: 'center', alpha: ca * seg(t, at('p2', 'industry practice'), 0.6) });
        }
      }
      // ================= 2D part
      const dA = env(t, p[3] - 0.2, ctx.duration, 1.0, 0.5);
      if (dA <= 0) { chapterCard(d2, t, 3, 'Modelling the soil', 'Winkler springs · p-y curves · bounds', { t0: 0, hold: 2.2 }); return; }
      // load state for the diagram
      const ls = seg(t, p[6] + 0.3, 5.0, ease.inOutSine) * (1 - seg(t, p[7] - 0.2, 0.8)) + (t > p[8] - 0.5 && t < p[9] + 0.2 ? seg(t, p[8] + 0.6, 2.5, ease.inOutSine) : 0);
      const st = stepAt(ls);
      const inFix = t > p[8] - 0.5 && t < p[9] - 0.2;
      const showDiagram = t < p[10] - 0.3;
      const diaA = dA * (showDiagram ? 1 : 1 - seg(t, p[10] - 0.3, 0.6));
      if (diaA > 0) {
        const soilA = 1 - 0.7 * seg(t, at('p3', 'replace the soil'), 2.0);
        const coarse = t > p[7] + 1.0 && t < p[8] - 0.4 ? seg(t, p[7] + 1.0, 0.8) : 0;
        const zsp = coarse > 0.5 ? [0, -4, -8, -12, -16, -20, -24, -28] : springsZ;
        drawGlobal(d2, {
          x: DX, y0: Y0, sy: SY, zTop: 4.2, zBot: -30, bop: false, soilAlpha: soilA, soilW: 300,
          u: inFix ? ((z) => ls * (z <= 2.6 ? interp(G.fixed.zo, G.fixed.uo, z) : interp(G.fixed.zi, G.fixed.ui, z))) : uOf(st.uo, st.ui), ux: 600, springs: !inFix, springZ: zsp, springP: seg(t, at('p3', 'row of independent') - 0.3, 2.5), springL: 82,
          mob: (z) => interp(sZ, st.mob, z), nodes: coarse > 0.5 ? [0, -4, -8, -12, -16, -20, -24, -28, 0.8, 1.7, 2.6, 3.6] : nodes1,
          nodeP: seg(t, at('p3', 'row of independent'), 1.5), alpha: diaA, condW: 8, breakLabel: true,
        });
        d2.tag('WINKLER FOUNDATION', DX, 140, { size: 22, alpha: diaA * seg(t, at('p3', 'Winkler'), 0.6) * (1 - seg(t, p[6], 0.5)), align: 'center', color: PAL.teal });
        // load arrow at the wellhead
        const la = diaA * (ls > 0.02 ? 1 : 0);
        if (la > 0) {
          const xw = DX + interp(B.zi, st.ui, 3.6) * 600, yw = Y0 - 3.6 * SY;
          d2.arrow(xw - 130, yw, xw - 6, yw, { color: PAL.orange, width: 6, head: 20, alpha: la, glow: PAL.orange });
          d2.momentArrow(xw, yw - 4, 46, Math.PI * 1.15, Math.PI * 1.85, { color: PAL.amber, width: 4, alpha: la });
          d2.text(`H = ${Math.round(st.H / 1e3)} kN, M = ${(st.H * 13 / 1e6).toFixed(2)} MNm`, xw - 140, yw - 58, { size: 22, weight: 700, color: PAL.orange, alpha: la });
        }
        // fixed support for p8
        if (inFix) {
          const fa = diaA * seg(t, p[8] + 0.2, 0.5);
          d2.ground(DX, Y0 + 4, 120, { alpha: fa, color: PAL.red, width: 4 });
          d2.text('fixed at mudline', DX + 80, Y0 + 40, { size: 24, weight: 750, color: PAL.red, alpha: fa });
        }
      }
      // ---------------- p3: single spring explanation + p-y plot
      const pyA = dA * env(t, at('p3', 'Each spring'), p[5] - 0.3, 0.6, 0.5);
      if (pyA > 0) {
        const P = pyPlot();
        d2.panel(1060, 160, 780, 620, { alpha: pyA });
        P.axes({ alpha: pyA, xticks: [0, 50, 100, 150, 200], yticks: [0, 100, 200, 300], xlabel: 'lateral displacement  y  [mm]', ylabel: 'soil resistance  p  [kN/m]', fs: 20, ylabelOff: 64 });
        // single representative curve during p3, family during p4
        const fam = seg(t, at('p4', 'grows with depth'), 3.0);
        curves.forEach((c, i) => {
          const isRep = i === 2;
          const q = isRep ? seg(t, at('p3', 'P Y curve'), 1.5) : seg(fam, i / curves.length * 0.8, 0.3);
          if (q <= 0) return;
          const pts = c.y.map((y, k) => [y * 1000, c.p[k] / 1000]);
          const col = ['#7fe3c3', '#3ddc97', '#4cc9f0', '#4895ef', '#a78bfa'][i];
          P.clipBegin();
          P.curve(pts, { color: col, width: isRep ? 4 : 3, progress: q, alpha: pyA });
          P.clipEnd();
          if (q >= 1 && (fam > 0 || isRep)) {
            const yy = Math.min(315, c.pu / 1000);
            d2.text(`${c.X} m`, P.X(pts[pts.length - 1][0]) - 6, P.Y(yy) - 10, { size: 20, weight: 700, color: col, align: 'right', alpha: pyA * (isRep ? 1 : fam) });
          }
        });
        // table points on the representative curve
        const tp = seg(t, at('p4', 'table of points'), 0.8);
        if (tp > 0) {
          const c = curves[2];
          P.points(c.table_y.map((y, k) => [y * 1000, c.table_p[k] / 1000]).filter(([x]) => x < 230), { color: PAL.amber, r: 7, progress: tp, alpha: pyA });
          d2.text('input: table of (y, p) points', P.x + 30, P.y + 30, { size: 22, weight: 650, color: PAL.amber, alpha: pyA * tp });
        }
        if (fam > 0) d2.text('depth below mudline', P.x + P.w - 10, P.y + P.h - 20, { size: 20, color: PAL.ink2, align: 'right', alpha: pyA * fam });
        // formulas
        const fA = pyA * seg(t, at('p4', 'Matlock'), 0.8);
        tex.show('pyf1', '\\dfrac{p}{p_u} = 0.5\\left(\\dfrac{y}{y_c}\\right)^{1/3},\\quad y_c = 2.5\\,\\varepsilon_{c}\\,D', 1100, 800, { size: 30, alpha: fA, color: PAL.ink });
        tex.show('pyf2', 'p_u = \\min\\!\\left[\\left(3 + \\dfrac{\\gamma\' X}{c_u} + \\dfrac{J X}{D}\\right) c_u D,\\; 9\\,c_u D\\right]', 1100, 890, { size: 30, alpha: pyA * seg(t, at('p4', 'ultimate value'), 0.8), color: PAL.ink });
        d2.text('soft clay (Matlock / API RP 2GEO)', 1100, 790, { size: 20, weight: 650, color: PAL.ink2, alpha: fA });
        // inset: p and y on a single spring
        const iA = pyA * env(t, at('p3', 'Each spring'), p[4] - 0.2, 0.5, 0.5);
        if (iA > 0) {
          const ix = 780, iy = 360;
          d2.panel(ix - 30, iy - 110, 260, 250, { alpha: iA });
          const yy = 30 * (0.5 + 0.5 * Math.sin(t * 1.6));
          d2.rect(ix + 20 + yy, iy - 70, 26, 140, { fill: '#9fb3c4', alpha: iA });
          d2.spring(ix + 46 + yy, iy, ix + 200, iy, { color: PAL.teal, width: 3, coils: 4, amp: 9, alpha: iA });
          d2.line(ix + 200, iy - 18, ix + 200, iy + 18, { color: PAL.ink3, width: 3, alpha: iA });
          d2.arrow(ix + 20, iy + 96, ix + 20 + yy + 1, iy + 96, { color: PAL.cyan, width: 2.5, head: 10, alpha: iA });
          d2.text('y', ix + 6, iy + 104, { size: 24, weight: 800, color: PAL.cyan, alpha: iA, align: 'right' });
          d2.arrow(ix + 120, iy - 40, ix + 60 + yy, iy - 40, { color: PAL.teal, width: 3, head: 12, alpha: iA });
          d2.text('p', ix + 130, iy - 32, { size: 24, weight: 800, color: PAL.teal, alpha: iA });
        }
      }
      // ---------------- p5: tributary length + t-z / Q-z
      const tA = dA * env(t, p[5], p[6] - 0.2, 0.5, 0.5);
      if (tA > 0) {
        const zi = -5;
        const yA = Y0 - (zi + 0.5) * SY, yB = Y0 - (zi - 0.5) * SY;
        const xb = DX - 140;
        d2.line(xb, yA, xb, yB, { color: PAL.amber, width: 3, alpha: tA });
        d2.line(xb - 8, yA, xb + 8, yA, { color: PAL.amber, width: 3, alpha: tA });
        d2.line(xb - 8, yB, xb + 8, yB, { color: PAL.amber, width: 3, alpha: tA });
        d2.rect(DX - 10, yA, 20, yB - yA, { fill: rgba(PAL.amber, 0.35), alpha: tA });
        d2.text('½ L above', xb - 14, yA + 8, { size: 20, color: PAL.amber, align: 'right', alpha: tA });
        d2.text('½ L below', xb - 14, yB + 8, { size: 20, color: PAL.amber, align: 'right', alpha: tA });
        d2.panel(1060, 220, 780, 260, { alpha: tA, accent: PAL.amber });
        d2.text('Spring at node i', 1100, 275, { size: 30, weight: 750, alpha: tA });
        tex.show('trib', 'F_i(y) = p_i(y)\\,\\cdot\\,\\tfrac{1}{2}\\left(L_{i-1} + L_{i}\\right)', 1100, 300, { size: 36, alpha: tA, color: PAL.amber });
        d2.text('resistance per metre × tributary length', 1100, 440, { size: 24, color: PAL.ink2, alpha: tA });
        const vA = tA * seg(t, at('p5', 'vertical direction'), 0.6);
        if (vA > 0) {
          for (let z = -2; z >= -28; z -= 4) {
            const yy = Y0 - z * SY;
            for (const s of [-1, 1]) d2.spring(DX + s * 28, yy - 26, DX + s * 28, yy + 26, { color: PAL.violet, width: 2, coils: 3, amp: 5, alpha: vA });
          }
          const yt = Y0 + 30 * SY;
          d2.spring(DX, yt + 2, DX, yt + 60, { color: PAL.pink, width: 3, coils: 3, amp: 9, alpha: vA * seg(t, at('p5', 'Q Z'), 0.5) });
          d2.ground(DX, yt + 62, 60, { alpha: vA * seg(t, at('p5', 'Q Z'), 0.5) });
          d2.panel(1060, 520, 780, 230, { alpha: vA, accent: PAL.violet });
          d2.text('Axial springs', 1100, 575, { size: 30, weight: 750, alpha: vA });
          d2.text('t-z : skin friction along the conductor', 1100, 625, { size: 26, color: PAL.violet, weight: 650, alpha: vA * seg(t, at('p5', 'T Z'), 0.5) });
          d2.text('Q-z : end bearing at the tip', 1100, 670, { size: 26, color: PAL.pink, weight: 650, alpha: vA * seg(t, at('p5', 'Q Z'), 0.5) });
        }
      }
      // ---------------- p6: loading, moment diagram
      const mA = dA * env(t, p[6] + 0.2, p[7] - 0.3, 0.6, 0.5);
      if (mA > 0) {
        const mx0 = 820, mw = 300, msc = mw / 3.2e6;
        d2.line(mx0, Y0 - 4 * SY, mx0, Y0 + 30 * SY, { color: PAL.ink3, width: 2, alpha: mA });
        d2.text('bending moment', mx0 + 4, Y0 - 4 * SY - 40, { size: 24, weight: 700, color: PAL.amber, alpha: mA });
        d2.text('in conductor + casing', mx0 + 4, Y0 - 4 * SY - 14, { size: 20, color: PAL.ink2, alpha: mA });
        const Mf = totalM(st);
        const pts = [];
        for (let z = 3.6; z >= -30; z -= 0.25) pts.push([mx0 + Math.abs(Mf(z)) * msc, Y0 - z * SY]);
        d2.poly([[mx0, Y0 - 3.6 * SY], ...pts, [mx0, Y0 + 30 * SY]], { fill: rgba(PAL.amber, 0.18), alpha: mA });
        d2.path(pts, { color: PAL.amber, width: 3.5, alpha: mA });
        d2.line(mx0 - 20, Y0, mx0 + mw + 40, Y0, { color: '#b9a98a', width: 1.5, alpha: mA * 0.6, dash: [6, 6] });
        const pk = mA * seg(t, at('p6', 'peaks'), 0.6);
        if (pk > 0) {
          const ypk = Y0 - B.zpeak * SY, xpk = mx0 + Math.abs(B.Mpeak) * msc;
          d2.circle(xpk, ypk, 9, { fill: PAL.amber, alpha: pk, glow: PAL.amber });
          d2.line(mx0, ypk, xpk, ypk, { color: PAL.amber, width: 1.5, dash: [5, 5], alpha: pk });
          d2.panel(1260, 330, 590, 330, { alpha: pk, accent: PAL.amber });
          d2.text('Peak moment', 1300, 390, { size: 30, weight: 750, alpha: pk });
          d2.text(`${(Math.abs(B.Mpeak) / 1e6).toFixed(2)} MNm`, 1300, 450, { size: 46, weight: 800, color: PAL.amber, alpha: pk });
          d2.text(`${Math.abs(B.zpeak).toFixed(0)} m below the mudline`, 1300, 500, { size: 28, weight: 650, alpha: pk });
          const inc = Math.abs(B.Mpeak) / Math.abs(B.M_mud) - 1;
          d2.text(`+${Math.round(100 * inc)} % vs. ${(Math.abs(B.M_mud) / 1e6).toFixed(2)} MNm at the mudline`, 1300, 545, { size: 24, color: PAL.ink2, alpha: pk * seg(t, at('p6', 'nineteen'), 0.5) });
          d2.text('nonlinear analysis, load applied in steps', 1300, 620, { size: 20, color: PAL.ink3, alpha: pk });
        }
        // mobilisation legend
        const lg = mA * seg(t, at('p6', 'mobilise'), 0.6);
        if (lg > 0) {
          d2.text('spring mobilisation p/pu', 1260, 740, { size: 22, weight: 650, alpha: lg });
          for (let i = 0; i <= 20; i++) d2.rect(1260 + i * 18, 760, 18, 18, { fill: mobColor(i / 20), alpha: lg });
          d2.text('0', 1260, 805, { size: 18, color: PAL.ink2, alpha: lg });
          d2.text('1', 1260 + 21 * 18, 805, { size: 18, color: PAL.ink2, align: 'right', alpha: lg });
        }
      }
      // ---------------- p7: mesh / spring spacing convergence
      const cA = dA * env(t, p[7] + 0.2, p[8] - 0.3, 0.6, 0.5);
      if (cA > 0) {
        const P = new Plot(d2, { x: 1120, y: 260, w: 640, h: 380, xr: [0, 4.4], yr: [0, 5] });
        d2.panel(1060, 180, 780, 560, { alpha: cA });
        d2.text('Element length = spring spacing', 1100, 230, { size: 28, weight: 750, alpha: cA });
        P.axes({ alpha: cA, xticks: [0.25, 1, 2, 4], yticks: [0, 1, 2, 3, 4, 5], xlabel: 'element length near the mudline [m]', ylabel: 'error in wellhead deflection [%]', fs: 19, ylabelOff: 58, fmtx: (v) => String(v) });
        const pts = G.mesh.map((m) => [m.le, 100 * Math.abs(m.err_u)]).sort((a, b) => a[0] - b[0]);
        const q = seg(t, at('p7', 'convergence study'), 1.5);
        P.curve(pts, { color: PAL.cyan, width: 3.5, progress: q, alpha: cA });
        P.points(pts, { color: PAL.cyan, r: 7, progress: q, alpha: cA });
        if (q >= 1) d2.text(`${(100 * G.mesh[0].err_u).toFixed(1)} %`, P.X(4) - 14, P.Y(100 * G.mesh[0].err_u) - 18, { size: 26, weight: 800, color: PAL.cyan, align: 'right', alpha: cA });
        const rA = cA * seg(t, at('p7', 'half a diameter'), 0.6);
        d2.panel(1060, 770, 780, 160, { alpha: rA, accent: PAL.green });
        d2.check(1110, 830, 20, { progress: rA, alpha: rA });
        d2.text('≈ D/2 (≈ 0.5 m) near the mudline', 1150, 840, { size: 28, weight: 700, alpha: rA });
        d2.text('longer elements deeper down', 1150, 885, { size: 24, color: PAL.ink2, alpha: cA * seg(t, at('p7', 'longer elements'), 0.5) });
        const cs = seg(t, p[7] + 1.0, 0.6) * (1 - seg(t, at('p7', 'half a diameter') - 0.5, 0.6));
        if (cs > 0) d2.tag('4 m elements', DX, 140, { size: 22, alpha: cA * cs, align: 'center', color: PAL.amber });
      }
      // ---------------- p8: fixed at mudline
      const fA = dA * env(t, p[8] + 0.2, p[9] - 0.3, 0.6, 0.5);
      if (fA > 0) {
        // ghost of the spring-supported deflected shape for comparison
        const gs = seg(t, at('p8', 'deletes') - 0.3, 1.0);
        const uS = uOf(B.uo, B.ui);
        const pts = [];
        for (let z = -30; z <= 3.6; z += 0.25) pts.push([DX + uS(z) * 600, Y0 - z * SY]);
        d2.path(pts, { color: PAL.green, width: 3, dash: [8, 6], alpha: fA * gs });
        d2.text('with soil springs', DX + uS(3.6) * 600 + 16, Y0 - 3.6 * SY - 6, { size: 22, weight: 700, color: PAL.green, alpha: fA * gs });
        d2.panel(1060, 260, 780, 380, { alpha: fA, accent: PAL.red });
        d2.text('Fixed at the mudline vs. soil springs', 1100, 315, { size: 30, weight: 750, alpha: fA });
        const du = G.fixed.u_wh / B.u_wh - 1, dth = G.fixed.th_wh / B.th_wh - 1;
        d2.text('wellhead deflection', 1100, 395, { size: 26, color: PAL.ink2, alpha: fA * seg(t, at('p8', 'underestimates'), 0.5) });
        d2.text(`${Math.round(100 * du)} %`, 1780, 400, { size: 52, weight: 800, color: PAL.red, align: 'right', alpha: fA * seg(t, at('p8', 'underestimates'), 0.5) });
        d2.text(`${(G.fixed.u_wh * 1e3).toFixed(0)} mm instead of ${(B.u_wh * 1e3).toFixed(0)} mm`, 1100, 432, { size: 22, color: PAL.ink3, alpha: fA * seg(t, at('p8', 'underestimates'), 0.5) });
        d2.text('wellhead rotation', 1100, 520, { size: 26, color: PAL.ink2, alpha: fA * seg(t, at('p8', 'the rotation'), 0.5) });
        d2.text(`${Math.round(100 * dth)} %`, 1780, 525, { size: 52, weight: 800, color: PAL.red, align: 'right', alpha: fA * seg(t, at('p8', 'the rotation'), 0.5) });
        d2.cross(1110, 760, 22, { progress: seg(t, at('p8', "Don't"), 0.6), alpha: fA });
        d2.text('Don’t fix the conductor at the mudline', 1150, 770, { size: 30, weight: 750, color: PAL.red, alpha: fA * seg(t, at('p8', "Don't"), 0.6) });
      }
      // ---------------- p9: soil bounds
      const bA = dA * env(t, p[9] + 0.2, p[10] - 0.3, 0.6, 0.5);
      if (bA > 0) {
        const mx0 = 820, mw = 300, msc = mw / 3.3e6;
        d2.line(mx0, Y0 - 4 * SY, mx0, Y0 + 30 * SY, { color: PAL.ink3, width: 2, alpha: bA });
        d2.text('bending moment', mx0 + 4, Y0 - 4 * SY - 40, { size: 24, weight: 700, color: PAL.amber, alpha: bA });
        const cols = { LB: PAL.violet, BE: PAL.amber, UB: PAL.cyan };
        const names = { LB: 'lower bound soil', BE: 'best estimate', UB: 'upper bound soil' };
        ['LB', 'BE', 'UB'].forEach((k, i) => {
          const q = seg(t, at('p9', 'lower bound') + i * 0.6, 0.8);
          if (q <= 0) return;
          const bd = G.bounds[k];
          const pts = [];
          for (let z = 0.0; z >= -30; z -= 0.25) pts.push([mx0 + Math.abs(interp(bd.zmo, bd.Mtot, z)) * msc, Y0 - z * SY]);
          d2.path(pts, { color: cols[k], width: 3.5, alpha: bA, progress: q });
          const ypk = Y0 - bd.zpeak * SY, xpk = mx0 + Math.abs(bd.Mpeak) * msc;
          if (q >= 1) {
            d2.circle(xpk, ypk, 7, { fill: cols[k], alpha: bA });
            d2.text(`${Math.abs(bd.zpeak).toFixed(1)} m`, xpk + 14, ypk + 7, { size: 20, weight: 700, color: cols[k], alpha: bA });
          }
          d2.text(names[k], 1300, 330 + i * 110, { size: 28, weight: 750, color: cols[k], alpha: bA * q });
          d2.text(`peak at ${Math.abs(bd.zpeak).toFixed(1)} m · wellhead deflection ${(bd.u_wh * 1e3).toFixed(0)} mm`, 1300, 366 + i * 110, { size: 22, color: PAL.ink2, alpha: bA * q });
        });
        d2.panel(1260, 270, 590, 340, { alpha: bA * 0.0 });
        const fq = bA * seg(t, at('p9', 'For fatigue'), 0.6);
        d2.panel(1260, 680, 590, 170, { alpha: fq, accent: PAL.green });
        d2.text('For fatigue:', 1300, 735, { size: 28, weight: 750, alpha: fq });
        d2.text('cyclic soil curves at small displacements', 1300, 778, { size: 24, color: PAL.ink2, alpha: fq });
        d2.text('— that is where the damage builds up', 1300, 812, { size: 24, color: PAL.ink2, alpha: fq });
      }
      // ---------------- p10: coupled vs uncoupled springs (top view)
      const uA = dA * env(t, p[10] + 0.1, ctx.duration, 0.6, 0.5);
      if (uA > 0) {
        d2.text('One trap in 3D models: independent x and y springs', 960, 140, { size: 42, weight: 800, align: 'center', alpha: uA });
        // left: plan view with springs
        const cx = 470, cy = 520;
        d2.panel(140, 220, 660, 640, { alpha: uA });
        d2.text('plan view at one node', 180, 268, { size: 22, color: PAL.ink2, alpha: uA });
        const q1 = seg(t, at('p10', 'Two independent'), 0.6);
        const diag = seg(t, at('p10', 'diagonal'), 0.8);
        const dd = 34 * diag * (0.6 + 0.4 * Math.sin(t * 2));
        const px = cx + dd / Math.SQRT2, py = cy - dd / Math.SQRT2;
        for (const [ax, ay] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
          d2.spring(px + ax * 56, py + ay * 56, cx + ax * 220, cy + ay * 220, { color: PAL.teal, width: 3, coils: 4, amp: 9, alpha: uA * q1 });
          d2.line(cx + ax * 220 - ay * 16, cy + ay * 220 - ax * 16, cx + ax * 220 + ay * 16, cy + ay * 220 + ax * 16, { color: PAL.ink3, width: 3, alpha: uA * q1 });
        }
        d2.circle(px, py, 56, { fill: 'rgba(159,179,196,0.85)', stroke: '#dbe6ee', width: 2, alpha: uA });
        d2.text('x', cx + 236, cy + 34, { size: 24, weight: 700, color: PAL.ink2, alpha: uA * q1 });
        d2.text('y', cx + 22, cy - 230, { size: 24, weight: 700, color: PAL.ink2, alpha: uA * q1 });
        d2.arrow(cx - 60, cy + 60, cx + 120, cy - 120, { color: PAL.orange, width: 5, head: 18, alpha: uA * diag, glow: PAL.orange });
        d2.text('diagonal load', cx + 120, cy - 132, { size: 22, weight: 700, color: PAL.orange, alpha: uA * diag });
        // right: capacity envelope (square vs circle)
        const ex = 1360, ey = 505, R = 190;
        d2.panel(940, 220, 840, 640, { alpha: uA });
        d2.text('soil resistance envelope', 980, 268, { size: 22, color: PAL.ink2, alpha: uA });
        d2.line(ex - R - 40, ey, ex + R + 40, ey, { color: PAL.ink3, width: 1.5, alpha: uA });
        d2.line(ex, ey - R - 40, ex, ey + R + 40, { color: PAL.ink3, width: 1.5, alpha: uA });
        const e1 = seg(t, at('p10', 'Two independent') + 0.5, 1.0);
        d2.poly([[ex - R, ey - R], [ex + R, ey - R], [ex + R, ey + R], [ex - R, ey + R]], { stroke: PAL.red, width: 3.5, fill: rgba(PAL.red, 0.08), alpha: uA * e1 });
        d2.circle(ex, ey, R, { stroke: PAL.green, width: 3.5, fill: rgba(PAL.green, 0.08), alpha: uA * e1 });
        d2.line(ex, ey, ex + R, ey - R, { color: PAL.red, width: 2, dash: [6, 5], alpha: uA * e1 });
        d2.circle(ex + R, ey - R, 8, { fill: PAL.red, alpha: uA * e1 });
        d2.text('x–y springs', ex + R + 14, ey - R + 40, { size: 22, weight: 700, color: PAL.red, alpha: uA * e1 });
        d2.text('true (radial)', ex - R - 14, ey + R * 0.85, { size: 22, weight: 700, color: PAL.green, align: 'right', alpha: uA * e1 });
        const n1 = seg(t, at('p10', 'twenty-six'), 0.6), n2 = seg(t, at('p10', 'forty-one'), 0.6);
        d2.text(`+${Math.round(100 * (G.uncoupled.small - 1))} %  resistance on the rising part of the curve`, 980, 780, { size: 28, weight: 750, color: PAL.amber, alpha: uA * n1 });
        d2.text(`+${Math.round(100 * (G.uncoupled.ultimate - 1))} %  capacity at failure`, 980, 822, { size: 28, weight: 750, color: PAL.red, alpha: uA * n2 });
        keyLine(d2, t, at('p10', 'Use a coupled'), ctx.duration, 'Use a coupled radial spring — or line the springs up with the load', { size: 30, y: 965, accent: PAL.green });
      }
      chapterCard(d2, t, 3, 'Modelling the soil', 'Winkler springs · p-y curves · bounds', { t0: 0, hold: 2.2 });
    },
  };
}
