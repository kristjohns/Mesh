// Chapter 4a: interface conductor housing <-> template (gap element, flexible template, load sharing).
import * as THREE from 'three';
import { makeBackdrop, renderViewport, studioScene, envMap, fatLines, cameraPath, toScreen } from '../engine/env.js';
import { makeWellhead, DIM } from '../models/wellhead.js';
import { latheGeometry, capGeometry, capUV, hatchTexture } from '../models/lathe.js';
import { soilSection } from '../models/soil.js';
import { makeTemplateWire, toThree } from '../models/template.js';
import { chapterCard, keyLine } from './common.js';
import { drawGlobal } from './globaldiag.js';
import { interp } from './s03_strategy.js';
import { Plot } from '../engine/draw2d.js';
import { PAL, seg, env, ease, clamp, lerp, rgba } from '../engine/util.js';

export const REC_PROFILE = [[0.56, 1.74], [0.78, 1.74], [0.78, 2.16], [1.25, 2.62], [1.18, 2.66], [0.62, 2.2], [0.56, 2.2]];

// studio cutaway of the well in its slot (shared with later scenes)
export function cutawayScene(ctx, o = {}) {
  const S = studioScene({ hemi: 1.25, key: 1.7 });
  const env3 = envMap(ctx.renderer);
  const cut = new THREE.Plane(new THREE.Vector3(-1, 0, 0), 0);
  const wh = makeWellhead(env3, { zBottom: o.zBottom ?? -7, segments: 128, clipPlanes: [cut], envIntensity: 0.6 });
  wh.userData.setCut(true);
  S.add(wh);
  const recMat = new THREE.MeshStandardMaterial({ color: 0xe0a80c, metalness: 0.15, roughness: 0.55, envMap: env3, envMapIntensity: 0.5, clippingPlanes: [cut], side: THREE.DoubleSide });
  const rec = new THREE.Mesh(latheGeometry(REC_PROFILE, { segments: 96 }), recMat);
  S.add(rec);
  const rcap = new THREE.Mesh(capUV(capGeometry(REC_PROFILE), 3.2), new THREE.MeshStandardMaterial({ map: hatchTexture('#f6d36b', '#b08214', 14, 45), side: THREE.DoubleSide, roughness: 0.7 }));
  S.add(rcap);
  // template beams attached to the receptacle (cut)
  const beamMat = recMat.clone();
  for (const zc of [-1, 1]) {
    const b = new THREE.Mesh(new THREE.BoxGeometry(0.45, 0.6, 3.0), beamMat);
    b.position.set(0, 1.95, zc * (0.78 + 1.5));
    S.add(b);
  }
  const soil = soilSection({ width: 14, depth: o.soilDepth ?? 8, holeHalf: DIM.rCondO + 0.002, holeDepth: (o.zBottom ? -o.zBottom : 7) });
  soil.rotation.y = Math.PI / 2;
  soil.position.x = -0.004;
  S.add(soil);
  return { S, wh, rec, soil, cut };
}

export default async function templateScene(ctx) {
  const { d2, cue, at, renderer, data, tex } = ctx;
  const G = data.global, T = data.template;
  const back = makeBackdrop();
  const b = {};
  for (const k of ['b0', 'b1', 'b2', 'b3', 'b4', 'b5', 'b6']) b[k] = cue(k);
  const C = cutawayScene(ctx);
  const cam = new THREE.PerspectiveCamera(30, 16 / 9, 0.05, 200);
  const camf = cameraPath(cam, [
    { t: 0, pos: [13.5, 2.2, 5.0], tgt: [0, -0.2, 0], fov: 30 },
    { t: b.b1 - 0.4, pos: [12.8, 2.3, 4.6], tgt: [0, 0.0, 0], fov: 30, e: ease.inOutSine },
    { t: b.b1 + 1.6, pos: [2.6, 2.25, 0.9], tgt: [0, 2.0, 0.55], fov: 30 },
    { t: b.b2, pos: [2.4, 2.2, 0.85], tgt: [0, 2.0, 0.55], fov: 30, e: ease.inOutSine },
  ]);
  // template frame model (beam elements) for b3
  const F = studioScene();
  const wire = makeTemplateWire(T, { width: 2.0 });
  const fixedWire = makeTemplateWire(T, { width: 1.2, color: 0x62809a, nodeSize: 0.001 });
  F.add(fixedWire, wire);
  const basePos = wire.children[0].geometry.attributes.instanceStart ? null : null;
  const nodes = T.nodes.map(([x, y, z]) => toThree(x, y, z));
  const mode = T.mode_x;
  const segPos = (scale) => {
    const arr = [];
    for (const m of T.members) {
      const A = nodes[m.a], Bn = nodes[m.b], dA = mode[m.a], dB = mode[m.b];
      arr.push(A[0] + scale * dA[0], A[1] + scale * dA[2], A[2] - scale * dA[1], Bn[0] + scale * dB[0], Bn[1] + scale * dB[2], Bn[2] - scale * dB[1]);
    }
    return arr;
  };
  const fcam = new THREE.PerspectiveCamera(34, 16 / 9, 0.1, 300);
  // anchor spring markers
  const anchorMarks = new THREE.Group();
  for (const a of T.anchors) {
    const [x, , z] = toThree(a.x, a.y, 0);
    const pos = [];
    const n = 7;
    for (let i = 0; i < n; i++) {
      const y0 = 1.0 - (i / n) * 2.4, y1 = 1.0 - ((i + 1) / n) * 2.4;
      const off = i % 2 ? 0.35 : -0.35;
      pos.push(x + (i % 2 ? -0.35 : 0.35), y0, z, x + off, y1, z);
    }
    anchorMarks.add(fatLines(pos, { color: 0x3ddc97, width: 2.5 }));
  }
  F.add(anchorMarks);
  const sw = G.template_sweep;
  const TB = G.template_base;

  return {
    sfx: [{ t: 0.1, type: 'chapter' }, { t: b.b3 + 0.2, type: 'whoosh' }, { t: at('b4', 'Then the gap closes'), type: 'thud' }],
    render(t) {
      back.render(renderer);
      // ---------------- 3D cutaway (b0, b1)
      const cA = env(t, 0, b.b2 + 0.3, 0.1, 0.6);
      if (cA > 0) {
        camf(t);
        renderViewport(renderer, C.S, cam, 0, 0, 1920, 1080);
        d2.fadeRect(1 - cA, '#060f19');
        const ia = cA * env(t, b.b0 + 3.0, b.b1 + 0.6, 0.5, 0.6);
        if (ia > 0) {
          const marks = [
            ['A', 'conductor housing ↔ template', [0, 2.0, DIM.rLpGuide + 0.015], PAL.yellow, at('b0', 'three key')],
            ['B', 'conductor housing ↔ HP housing', [0, 2.2, 0.378], PAL.cyan, at('b0', 'three key') + 0.5],
            ['C', 'conductor ↔ soil', [0, -3.0, DIM.rCondO], PAL.teal, at('b0', 'three key') + 1.0],
          ];
          marks.forEach(([L, s, p3, col, tt], i) => {
            const q = seg(t, tt, 0.6, ease.outBack);
            if (q <= 0) return;
            const [px, py] = toScreen(p3, cam);
            d2.circle(px, py, 26 * q, { fill: rgba(col, 0.25), stroke: col, width: 3, alpha: ia, glow: col });
            d2.text(L, px, py + 10, { size: 28, weight: 800, align: 'center', color: col, alpha: ia * clamp(q) });
            d2.text(s, 1260, 300 + i * 90, { size: 30, weight: 700, color: PAL.ink, alpha: ia * clamp(q) });
            d2.circle(1220, 290 + i * 90, 22, { stroke: col, width: 3, alpha: ia * clamp(q) });
            d2.text(L, 1220, 300 + i * 90, { size: 24, weight: 800, align: 'center', color: col, alpha: ia * clamp(q) });
          });
        }
        const ga = cA * env(t, at('b1', 'radial clearance') - 0.3, b.b2 + 0.3, 0.5, 0.5);
        if (ga > 0) {
          const [x1, y1] = toScreen([0, 1.95, DIM.rLpGuide], cam);
          const [x2, y2] = toScreen([0, 1.95, 0.56], cam);
          d2.arrow(x1 - 70, y1, x1, y1, { color: PAL.amber, width: 3, alpha: ga, head: 14 });
          d2.arrow(x2 + 70, y2, x2, y2, { color: PAL.amber, width: 3, alpha: ga, head: 14 });
          d2.text('30 mm radial gap', (x1 + x2) / 2, y1 - 60, { size: 34, weight: 800, color: PAL.amber, align: 'center', alpha: ga, shadow: true });
          const [hx, hy] = toScreen([0, 1.55, 0.45], cam);
          d2.callout(hx, hy, hx - 200, hy + 160, 'Conductor housing', '', { alpha: ga, align: 'right', progress: 1 });
          const [rx, ry] = toScreen([0, 1.8, 0.7], cam);
          d2.callout(rx, ry, rx + 160, ry + 200, 'Template receptacle', '', { alpha: ga, color: PAL.yellow, progress: 1 });
        }
      }
      // ---------------- b2: tie / free / gap
      const oA = env(t, b.b2 + 0.1, b.b3 - 0.2, 0.6, 0.5);
      if (oA > 0) {
        d2.text('How do we connect the housing to the template?', 960, 140, { size: 44, weight: 800, align: 'center', alpha: oA });
        const cards = [
          { x: 120, title: 'Tied', sub: 'rigid connection', kind: 'no', t: at('b2', 'Tying') },
          { x: 700, title: 'Free', sub: 'no connection', kind: 'no', t: at('b2', 'leaving them') },
          { x: 1280, title: 'Gap element', sub: 'open until the clearance closes', kind: 'ok', t: at('b2', 'gap element') },
        ];
        cards.forEach((c, i) => {
          const q = seg(t, c.t - 0.3, 0.6, ease.out);
          if (q <= 0) return;
          d2.panel(c.x, 220, 520, 640, { alpha: oA * q, accent: c.kind === 'ok' ? PAL.green : PAL.red });
          d2.text(c.title, c.x + 40, 285, { size: 36, weight: 800, alpha: oA * q });
          d2.text(c.sub, c.x + 40, 325, { size: 24, color: PAL.ink2, alpha: oA * q });
          if (c.kind === 'ok') d2.check(c.x + 460, 280, 22, { progress: seg(t, c.t, 0.8), alpha: oA * q }); else d2.cross(c.x + 460, 280, 22, { progress: seg(t, c.t + 0.4, 0.8), alpha: oA * q });
          const P = new Plot(d2, { x: c.x + 80, y: 400, w: 380, h: 330, xr: [-1, 1], yr: [-1, 1] });
          d2.line(P.x, P.Y(0), P.x + P.w, P.Y(0), { color: PAL.ink3, width: 1.5, alpha: oA * q });
          d2.line(P.X(0), P.y, P.X(0), P.y + P.h, { color: PAL.ink3, width: 1.5, alpha: oA * q });
          d2.text('u', P.x + P.w + 6, P.Y(0) + 8, { size: 22, color: PAL.ink2, alpha: oA * q });
          d2.text('F', P.X(0) + 10, P.y + 6, { size: 22, color: PAL.ink2, alpha: oA * q });
          const lp = seg(t, c.t, 1.2);
          let pts;
          if (i === 0) pts = [[-0.08, -1], [0.08, 1]];
          else if (i === 1) pts = [[-1, 0], [1, 0]];
          else pts = [[-1, -0.9], [-0.35, 0], [0.35, 0], [1, 0.9]];
          P.curve(pts, { color: c.kind === 'ok' ? PAL.green : PAL.red, width: 4, progress: lp, alpha: oA * q });
          if (i === 2 && lp > 0.5) {
            d2.dim(P.X(0), P.Y(0) + 34, P.X(0.35), P.Y(0) + 34, 'gap', { alpha: oA * q, color: PAL.amber, size: 20 });
            d2.text('slope = template stiffness', P.X(0.15), P.Y(0.75), { size: 20, weight: 650, color: PAL.green, align: 'center', alpha: oA * seg(t, at('b2', 'stiffness of the template'), 0.6) });
          }
          const notes = ['attracts all the load', 'ignores the load path', 'no force while open'];
          d2.text(notes[i], c.x + 40, 800, { size: 24, weight: 650, color: c.kind === 'ok' ? PAL.green : PAL.red, alpha: oA * seg(t, c.t + 0.6, 0.6) });
        });
      }
      // ---------------- b3: template frame model, fixed vs foundation
      const fA = env(t, b.b3 + 0.1, b.b4 - 0.2, 0.6, 0.5);
      if (fA > 0) {
        const sc = 1.4 * (0.5 + 0.5 * Math.sin(t * 2.0)) * seg(t, b.b3 + 1.0, 1.0);
        wire.children[0].geometry.setPositions(segPos(sc));
        const ang = 0.7 + t * 0.05;
        fcam.position.set(Math.sin(ang) * 36, 17, Math.cos(ang) * 36);
        fcam.lookAt(0, 2, 0);
        renderViewport(renderer, F, fcam, 0, 120, 1150, 860);
        d2.text('Template frame model (beam elements)', 90, 120, { size: 30, weight: 750, alpha: fA });
        d2.text('unit load at the slot receptacle · deflection exaggerated', 90, 156, { size: 22, color: PAL.ink2, alpha: fA });
        const k1 = T.k_slot.fixed_k_x / 1e6, k2 = T.k_slot.foundation_k_x / 1e6;
        const q1 = seg(t, at('b3', 'If we fix'), 0.6), q2 = seg(t, at('b3', 'its foundation'), 0.6);
        d2.panel(1200, 280, 640, 470, { alpha: fA });
        d2.text('slot stiffness', 1240, 335, { size: 26, color: PAL.ink2, alpha: fA });
        d2.text('with anchor foundation springs', 1240, 410, { size: 26, weight: 700, color: PAL.green, alpha: fA * q2 });
        d2.text(`${Math.round(k2)} MN/m`, 1240, 470, { size: 52, weight: 800, color: PAL.green, alpha: fA * q2 });
        d2.text('anchors fixed', 1240, 560, { size: 26, weight: 700, color: PAL.red, alpha: fA * q1 });
        d2.text(`${Math.round(k1).toLocaleString('en-US')} MN/m`, 1240, 620, { size: 52, weight: 800, color: PAL.red, alpha: fA * q1 });
        d2.text(`${(k1 / k2).toFixed(1)}× too stiff`, 1240, 700, { size: 32, weight: 800, color: PAL.amber, alpha: fA * seg(t, at('b3', 'eight times'), 0.5) });
      }
      // ---------------- b4: load sharing
      const lA = env(t, b.b4 + 0.1, b.b5 + 0.3, 0.6, 0.5);
      if (lA > 0) {
        const hp = seg(t, at('b4', 'Now increase') + 0.3, 13.0, ease.linear);
        const Hn = 250 * hp; // kN on the plots
        const sstep = clamp(Hn / 150);
        // diagram
        const n = TB.steps.length;
        const xs = sstep * n - 1, i0 = Math.max(0, Math.floor(xs)), i1 = Math.min(n - 1, i0 + 1), f = clamp(xs - i0);
        const mix = (k) => (sstep * n < 1 ? TB.steps[0][k].map((v) => v * sstep * n) : TB.steps[i0][k].map((v, j) => v * (1 - f) + TB.steps[i1][k][j] * f));
        const uo = mix('uo'), ui = mix('ui');
        const u = (z) => (z <= 2.6 ? interp(TB.zo, uo, z) : interp(TB.zi, ui, z));
        const DX = 330, Y0 = 380, SY = 26;
        drawGlobal(d2, { x: DX, y0: Y0, sy: SY, zTop: 4.0, zBot: -18, bop: false, u, ux: 600, springs: true, springZ: [0, -1, -2, -3, -4, -5, -6, -7, -8, -9, -10, -11, -12, -13, -14, -15, -16, -17], springL: 70, alpha: lA, soilW: 240, breakLabel: false,
          template: { gapPx: 18, inner: 6, alpha: 1 } });
        const Rn = interp(sw.H.map((h) => h / 1e3), sw.gap.map((q) => q.R / 1e3), Math.max(10, Math.min(Hn, 150)));
        if (Rn > 1 && Hn > 10) {
          const yy = Y0 - 2.0 * SY;
          const xr = DX + 6 + 18 + 30;
          d2.arrow(xr + 60, yy, xr + 4, yy, { color: PAL.yellow, width: 5, head: 16, alpha: lA, glow: PAL.yellow });
          d2.text(`R = ${Math.round(Rn)} kN`, xr + 70, yy + 8, { size: 24, weight: 800, color: PAL.yellow, alpha: lA });
        }
        const xw = DX + u(3.6) * 600, yw = Y0 - 3.6 * SY;
        d2.arrow(xw - 120, yw, xw - 6, yw, { color: PAL.orange, width: 5, head: 18, alpha: lA });
        d2.text(`H = ${Math.round(Math.min(Hn, 150))} kN`, xw - 130, yw - 22, { size: 22, weight: 700, color: PAL.orange, alpha: lA });
        // plots
        const P1 = new Plot(d2, { x: 860, y: 170, w: 900, h: 300, xr: [0, 250], yr: [0, 560] });
        P1.axes({ alpha: lA, xticks: [0, 50, 100, 150, 200, 250], yticks: [0, 200, 400], xlabel: '', ylabel: 'template contact [kN]', fs: 18, ylabelOff: 60, title: 'Load sharing with the template' });
        const P2 = new Plot(d2, { x: 860, y: 590, w: 900, h: 300, xr: [0, 250], yr: [0, 4.3] });
        P2.axes({ alpha: lA, xticks: [0, 50, 100, 150, 200, 250], yticks: [0, 1, 2, 3, 4], xlabel: 'riser load H at the flex joint [kN]', ylabel: 'moment at mudline [MNm]', fs: 18, ylabelOff: 60 });
        const H = [0, ...sw.H.map((h) => h / 1e3)];
        const ser = (key, fld, sc) => [[0, 0], ...sw[key].map((q, j) => [sw.H[j] / 1e3, q[fld] / sc])].filter(([x]) => x <= Hn + 1e-6);
        P1.clipBegin(); P1.curve(ser('gap', 'R', 1e3), { color: PAL.yellow, width: 4, alpha: lA }); P1.clipEnd();
        P2.clipBegin();
        P2.curve(ser('free', 'M_mud', 1e6), { color: PAL.red, width: 3, alpha: lA, dash: [8, 6] });
        P2.curve(ser('tied', 'M_mud', 1e6), { color: PAL.ink3, width: 3, alpha: lA, dash: [3, 5] });
        P2.curve(ser('gap', 'M_mud', 1e6), { color: PAL.green, width: 4, alpha: lA });
        P2.clipEnd();
        d2.text('no template contact', P2.X(250) - 10, P2.Y(4.15) - 12, { size: 20, weight: 650, color: PAL.red, align: 'right', alpha: lA * clamp((Hn - 200) / 30) });
        d2.text('gap element', P2.X(250) + 8, P2.Y(3.07) + 7, { size: 20, weight: 650, color: PAL.green, alpha: lA * clamp((Hn - 220) / 20) });
        d2.text('tied', P2.X(250) + 8, P2.Y(2.83) + 22, { size: 20, weight: 650, color: PAL.ink3, alpha: lA * clamp((Hn - 220) / 20) });
        // marker
        d2.line(P1.X(Hn), P1.y, P1.X(Hn), P2.y + P2.h, { color: 'rgba(255,255,255,0.25)', width: 1.5, alpha: lA });
        const gc = lA * seg(t, at('b4', 'Then the gap closes'), 0.6);
        d2.text('gap closes ≈ 50 kN', P1.X(50) + 10, P1.Y(40) - 6, { size: 22, weight: 750, color: PAL.amber, alpha: gc });
        const fq = lA * seg(t, at('b4', 'At full load'), 0.6);
        if (fq > 0) {
          const R150 = TB.R / 1e3;
          d2.circle(P1.X(150), P1.Y(R150), 8, { fill: PAL.yellow, alpha: fq });
          d2.text(`${Math.round(R150)} kN ≈ ${(R150 / 150).toFixed(1)} × H`, P1.X(150) - 16, P1.Y(R150) - 16, { size: 24, weight: 800, color: PAL.yellow, align: 'right', alpha: fq });
          const Mf = sw.free[14].M_mud / 1e6, Mg = sw.gap[14].M_mud / 1e6;
          d2.circle(P2.X(150), P2.Y(Mg), 8, { fill: PAL.green, alpha: fq });
          d2.text(`−${Math.round(100 * (1 - Mg / Mf))} % at the mudline`, P2.X(150) + 16, P2.Y(Mg) + 34, { size: 24, weight: 800, color: PAL.green, alpha: fq * seg(t, at('b4', 'twenty-one'), 0.5) });
        }
        d2.text('fulcrum', DX + 70, Y0 - 2.0 * SY + 46, { size: 20, weight: 650, color: PAL.yellow, alpha: lA * seg(t, at('b4', 'fulcrum'), 0.5) });
      }
      keyLine(d2, t, b.b5 + 0.1, b.b6 - 0.2, 'The template can relieve the wellhead — if it is designed to carry that load', { size: 30, y: 975, accent: PAL.amber });
      // ---------------- b6: contact geometry
      const gA = env(t, b.b6 + 0.1, ctx.duration, 0.6, 0.5);
      if (gA > 0) {
        d2.text('Contact geometry decides what is transferred', 960, 140, { size: 44, weight: 800, align: 'center', alpha: gA });
        const panels = [
          { x: 120, title: 'One short contact ring', sub: 'lateral force only', t: at('b6', 'A single') },
          { x: 700, title: 'Two rings, some distance apart', sub: 'force couple → moment', t: at('b6', 'Two rings') },
          { x: 1280, title: 'Vertical landing face', sub: 'compression-only + friction', t: at('b6', 'vertically') },
        ];
        panels.forEach((pp, i) => {
          const q = seg(t, pp.t - 0.3, 0.6, ease.out);
          if (q <= 0) return;
          const a = gA * q;
          d2.panel(pp.x, 220, 520, 660, { alpha: a, accent: [PAL.cyan, PAL.green, PAL.violet][i] });
          d2.text(pp.title, pp.x + 36, 280, { size: 30, weight: 750, alpha: a });
          d2.text(pp.sub, pp.x + 36, 318, { size: 24, color: PAL.ink2, alpha: a });
          const cx = pp.x + 260;
          const sway = Math.sin(t * 1.6) * 0.12;
          // inner housing (rotating slightly)
          const g = d2.g;
          g.save();
          g.translate(cx, 640);
          g.rotate(i < 2 ? sway : 0);
          d2.rect(-34, -240, 68, 360, { fill: 'rgba(170,190,210,0.5)', stroke: '#dbe6ee', width: 2, alpha: a });
          g.restore();
          if (i === 0) {
            for (const s of [-1, 1]) d2.rect(cx + s * 52 - 10, 600, 20, 40, { fill: rgba(PAL.yellow, 0.6), alpha: a });
            d2.arrow(cx + 140, 620, cx + 64, 620, { color: PAL.yellow, width: 4, alpha: a });
            d2.text('F', cx + 150, 628, { size: 24, weight: 800, color: PAL.yellow, alpha: a });
            d2.text('rotation free (like a pin)', pp.x + 36, 840, { size: 24, weight: 650, color: PAL.cyan, alpha: a });
          } else if (i === 1) {
            for (const yy of [440, 720]) for (const s of [-1, 1]) d2.rect(cx + s * 52 - 10, yy - 20, 20, 40, { fill: rgba(PAL.yellow, 0.6), alpha: a });
            const f = Math.sign(sway) || 1;
            d2.arrow(cx + 150 * f, 440, cx + 64 * f, 440, { color: PAL.yellow, width: 4, alpha: a });
            d2.arrow(cx - 150 * f, 720, cx - 64 * f, 720, { color: PAL.yellow, width: 4, alpha: a });
            d2.momentArrow(cx, 580, 110, -0.6, 0.6, { color: PAL.green, width: 4, alpha: a });
            d2.text('M = F · a', cx + 90, 590, { size: 26, weight: 800, color: PAL.green, alpha: a });
            d2.text('transfers a moment', pp.x + 36, 840, { size: 24, weight: 650, color: PAL.green, alpha: a });
          } else {
            const lift = Math.max(0, Math.sin(t * 1.3)) * 14;
            d2.rect(cx - 140, 700, 280, 30, { fill: rgba(PAL.yellow, 0.5), stroke: PAL.yellow, width: 2, alpha: a });
            d2.rect(cx - 90, 470 - lift, 180, 230, { fill: 'rgba(170,190,210,0.5)', stroke: '#dbe6ee', width: 2, alpha: a });
            d2.arrow(cx, 760, cx, 706, { color: PAL.violet, width: 4, alpha: a * (lift < 2 ? 1 : 0.2) });
            d2.text(lift < 2 ? 'bears' : 'lifts off', cx + 110, 650, { size: 24, weight: 800, color: lift < 2 ? PAL.violet : PAL.ink2, alpha: a });
            d2.arrow(cx - 150, 696, cx - 100, 696, { color: PAL.amber, width: 3, alpha: a, double: true, head: 10 });
            d2.text('μ', cx - 166, 690, { size: 26, weight: 800, color: PAL.amber, alpha: a, align: 'right' });
            d2.text('no tension across the face', pp.x + 36, 840, { size: 24, weight: 650, color: PAL.violet, alpha: a });
          }
        });
      }
      chapterCard(d2, t, 4, 'Boundary conditions at the interfaces', 'Template · HP housing · soil', { t0: 0, hold: 2.2 });
    },
  };
}
