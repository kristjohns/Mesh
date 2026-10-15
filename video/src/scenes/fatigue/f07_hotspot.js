// Step 2b: nominal stress, hot-spot stress from the local solid model (both housing welds) and the
// misalignment SCF of the conductor girth weld.
import * as THREE from 'three';
import { makeBackdrop, renderViewport, studioScene, envMap, cameraPath } from '../../engine/env.js';
import { Plot } from '../../engine/draw2d.js';
import { makeHotspotFE, drawProfile, divBar, divergingCss } from '../../models/hotspotfe.js';
import { keyLine } from '../common.js';
import { chainBar, heading, formulaWalk, texSteps, refChip } from './fcommon.js';
import { PAL, seg, env, ease, clamp, lerp, rgba } from '../../engine/util.js';

export default async function hotspot(ctx) {
  const { d2, cue, at, renderer, data, tex } = ctx;
  const HS = data.hotspot, F = data.fatigue;
  const back = makeBackdrop();
  const l1 = cue('l1'), l1b = cue('l1b'), l2 = cue('l2'), l2b = cue('l2b'), l3 = cue('l3'), l3q = cue('l3q'), l3b = cue('l3b');
  const WK = F.worked.hotspot;
  const fe = studioScene({ hemi: 1.4, key: 1.5 });
  const model = makeHotspotFE(HS.surface, { vmax: 30, env: envMap(renderer) });
  const zclip = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0.3);
  model.userData.mat.clippingPlanes = [zclip];
  model.userData.emat.clippingPlanes = [zclip];
  fe.add(model);
  const cam = new THREE.PerspectiveCamera(24, 1, 0.01, 100);
  const t3d = l2 - 0.2;
  const camf = cameraPath(cam, [
    { t: t3d, pos: [-5.6, 3.4, 7.4], tgt: [-0.75, 1.75, -0.2], fov: 26 },
    { t: at('l2', 'Read the surface') - 1.6, pos: [-4.0, 2.6, 5.6], tgt: [-0.5, 1.5, -0.1], fov: 26, e: ease.inOutSine },
    { t: at('l2', 'Read the surface') + 0.4, pos: [-0.36, 1.21, 0.42], tgt: [-0.28, 1.2, 0.0], fov: 24 },
  ]);
  const W = HS.welds;
  const hp = W.hpwhh.levels[1], lp = W.lpwh.levels[1];
  const prof = HS.profile;
  const sec = HS.section_szz;

  return {
    sfx: [{ t: at('l2', 'Read the surface') - 0.6, type: 'whoosh' }],
    render(t) {
      back.render(renderer);
      // ---------------------------------------------------------- l1/l1b: what the hot-spot stress is
      const nA = env(t, 0.4, l2 - 0.1, 0.6, 0.6);
      if (nA > 0) {
        heading(d2, 'Hot-spot stress', 110, 150, nA, { sub: 'structural stress at the weld toe, DNV-RP-C203 sections 3 and 4' });
        d2.panel(80, 210, 860, 790, { alpha: nA });
        // schematic: wall with a weld at a thickness step, surface stress rising towards the toe
        const x0 = 140, xt = 600, yS = 520, T = 70;
        d2.poly([[x0, yS], [xt, yS], [xt, yS + T], [x0, yS + T]], { fill: 'rgba(130,160,185,0.40)', stroke: '#9fb3c4', width: 2, alpha: nA });
        d2.poly([[xt + 70, yS - 90], [880, yS - 90], [880, yS + T], [xt, yS + T], [xt, yS]], { fill: 'rgba(130,160,185,0.55)', stroke: '#9fb3c4', width: 2, alpha: nA });
        d2.poly([[xt - 8, yS], [xt + 70, yS - 90], [xt + 70, yS - 40], [xt + 14, yS]], { fill: 'rgba(176,152,108,0.75)', stroke: '#d1bd92', width: 1.5, alpha: nA });
        d2.text('weld', xt + 40, yS - 100, { size: 20, weight: 700, color: '#d1bd92', align: 'center', alpha: nA });
        for (const yy of [yS + 18, yS + T - 18]) d2.arrow(x0 - 10, yy, x0 - 60, yy, { color: PAL.cyan, width: 3, head: 11, alpha: nA });
        const tq = seg(t, at('l1', 'concentrates') - 0.4, 0.6);
        d2.circle(xt - 4, yS, 10 + 2 * Math.sin(t * 6), { stroke: PAL.red, width: 3, alpha: nA * tq, glow: PAL.red });
        d2.text('weld toe', xt - 20, yS + T + 34, { size: 20, weight: 750, color: PAL.red, align: 'center', alpha: nA * tq });
        // surface stress along the wall
        const pyB = 470, pyN = 420;
        const sxy = (u) => {                                   // u = distance from the toe in wall thicknesses
          const sN = 1.0, struct = sN + 0.9 * Math.exp(-u / 1.4), notch = 0.8 * Math.exp(-u / 0.12);
          return [struct, notch];
        };
        const Yp = (v) => pyB - v * 80;
        const pq = seg(t, at('l1', 'concentrates') - 0.2, 1.4, ease.inOutSine);
        const nq = seg(t, at('l1b', 'nonlinear peak') - 0.3, 1.0);
        if (pq > 0) {
          const ps = [], pn = [];
          for (let i = 0; i <= 120; i++) {
            const x = lerp(x0, xt - 4, i / 120);
            const u = (xt - 4 - x) / T;
            const [st, no] = sxy(u);
            ps.push([x, Yp(st)]);
            pn.push([x, Yp(st + no)]);
          }
          d2.line(x0, Yp(1.0), xt, Yp(1.0), { color: PAL.ink2, width: 1.6, dash: [8, 6], alpha: nA * pq });
          d2.text('nominal', x0 + 4, Yp(1.0) + 24, { size: 19, color: PAL.ink2, alpha: nA * pq });
          d2.path(ps, { color: PAL.amber, width: 3.5, alpha: nA, progress: pq });
          if (nq > 0) d2.path(pn.slice(96), { color: PAL.red, width: 3, alpha: nA * nq });
          const hq = seg(t, at('l1', 'hot spot stress') - 0.3, 0.6);
          d2.circle(xt - 4, Yp(sxy(0)[0]), 8, { fill: PAL.amber, alpha: nA * hq, glow: PAL.amber });
          d2.text('σ_hs', xt - 18, Yp(sxy(0)[0]) - 16, { size: 22, weight: 800, color: PAL.amber, align: 'right', alpha: nA * hq });
          if (nq > 0) d2.text('notch peak', xt + 10, Yp(sxy(0)[0] + 0.7), { size: 19, weight: 700, color: PAL.red, alpha: nA * nq });
          d2.text('surface stress', x0, 270, { size: 21, weight: 700, color: PAL.ink, alpha: nA * pq });
        }
        // l1b: through-thickness decomposition at the toe
        const dA = nA * seg(t, l1b - 0.2, 0.7);
        if (dA > 0) {
          const yT = 690, yB = 900, cw = 110;
          const parts = [
            ['membrane', PAL.cyan, at('l1b', 'membrane part'), (f) => 0.55],
            ['bending', PAL.green, at('l1b', 'bending part'), (f) => 0.45 * (1 - 2 * f)],
            ['notch peak', PAL.red, at('l1b', 'nonlinear peak'), (f) => 0.9 * Math.exp(-f / 0.06) - 0.06],
            ['total at the toe', PAL.amber, at('l1b', 'nonlinear peak') + 1.2, (f) => 0.55 + 0.45 * (1 - 2 * f) + 0.9 * Math.exp(-f / 0.06) - 0.06],
          ];
          parts.forEach(([lab, col, tt, fn], k) => {
            const q = seg(t, tt - 0.3, 0.7);
            if (q <= 0) return;
            const xa = 140 + k * 190;
            d2.line(xa, yT - 10, xa, yB + 10, { color: PAL.ink3, width: 2, alpha: dA * q });
            const pts = [[xa, yT]];
            for (let i = 0; i <= 40; i++) { const f = i / 40; pts.push([xa + fn(f) * cw * 0.8 * q, lerp(yT, yB, f)]); }
            pts.push([xa, yB]);
            d2.poly(pts, { fill: rgba(col, 0.28), stroke: col, width: 2.2, alpha: dA * q });
            d2.text(lab, xa + 10, yB + 42, { size: 19, weight: 700, color: col, alpha: dA * q });
            if (k < 3) d2.text(k < 2 ? '+' : '=', xa + 160, (yT + yB) / 2 + 12, { size: 38, weight: 700, color: PAL.ink2, alpha: dA * seg(t, parts[k + 1][2] - 0.3, 0.5), align: 'center' });
          });
          d2.text('through the wall at the toe', 120, 640, { size: 21, weight: 700, alpha: dA });
          const sq = seg(t, at('l1b', 'structural stress') - 0.3, 0.6);
          if (sq > 0) d2.panel(116, yT - 26, 324, yB - yT + 86, { r: 12, alpha: dA * sq, fill: 'rgba(255,183,3,0.06)', border: rgba(PAL.amber, 0.9), borderWidth: 2, shadow: false });
        }
        // right: the definition, term by term
        d2.panel(980, 210, 860, 790, { alpha: nA });
        refChip(d2, 'C203 [3.1], [4.3.1]', 1010, 246, nA);
        formulaWalk(ctx, t, {
          id: 'f07hs', x: 1030, y: 290, size: 64, alpha: nA, tOff: l1b - 0.2,
          parts: [['h', '\\sigma_{hs}'], [null, ' = '], ['k', 'SCF'], [null, '\\cdot'], ['n', '\\sigma_{nom}']],
          rows: [
            { k: 'h', sym: '\\sigma_{hs}', text: 'hot-spot stress at the weld toe', sub: 'the structural stress the weld sees', t: at('l1', 'hot spot stress'), col: PAL.amber },
            { k: 'n', sym: '\\sigma_{nom}', text: 'nominal stress', sub: 'M / W from the beam model', t: at('l1', 'the nominal stress,'), col: PAL.cyan },
            { k: 'k', sym: 'SCF', text: 'stress concentration factor', sub: 'from FE hot-spot analysis or C203 formulas', t: at('l1', 'stress concentration factor'), col: PAL.violet },
          ],
          legend: { x: 1030, y: 420, w: 770, gap: 80, symW: 140, size: 24, symSize: 32, alpha: 1 - seg(t, l1b - 0.3, 0.6) },
        });
        const bq = seg(t, l1b + 0.2, 0.6);
        if (bq > 0) {
          const items = [
            ['membrane + bending', 'structural, or hot-spot, stress', PAL.amber, at('l1b', 'structural stress')],
            ['nonlinear notch peak', 'left out: it is in the hot-spot S-N curve', PAL.red, at('l1b', 'left out on purpose')],
          ];
          items.forEach(([a, b, col, tt], k) => {
            const q = seg(t, tt - 0.3, 0.6);
            const y = 470 + k * 130;
            d2.rect(1014, y - 32, 5, 90, { fill: col, alpha: nA * bq * q });
            d2.text(a, 1036, y, { size: 28, weight: 750, color: col, alpha: nA * bq * q });
            d2.text(b, 1036, y + 40, { size: 23, color: PAL.ink2, alpha: nA * bq * q });
          });
        }
      }
      // ---------------------------------------------------------- l2: 3D model then hot-spot read-out (HP weld)
      const zoomT = at('l2', 'Read the surface');
      const mA = env(t, l2 - 0.3, zoomT + 0.6, 0.7, 0.5);
      if (mA > 0) {
        camf(t);
        model.rotation.y = 0;
        renderViewport(renderer, fe, cam, 0, 0, 1920, 1080);
        d2.fadeRect(1 - mA, '#060f19');
        const lab = mA * (1 - seg(t, zoomT - 1.4, 0.6));
        d2.tag('LOCAL SOLID MODEL · AXIAL STRESS UNDER BENDING', 960, 130, { size: 22, alpha: lab, align: 'center', color: PAL.cyan, fill: 'rgba(5,14,26,0.9)' });
        divBar(d2, 1720, 600, 22, 300, 30, 'σ axial [MPa]', { alpha: lab });
        d2.text(`${HS.n_hex.toLocaleString('en-US')} hexahedra, refined below both welds`, 120, 1010, { size: 22, color: PAL.ink2, alpha: lab });
        d2.text('half model: the cut face is the plane of bending', 120, 1040, { size: 20, color: PAL.ink3, alpha: lab });
      }
      const hA = env(t, zoomT + 0.1, l3 - 0.1, 0.5, 0.5);
      if (hA > 0) {
        heading(d2, 'A · HP housing weld', 100, 150, hA, { sub: 'hot-spot method, DNV-RP-C203 section 4' });
        // zoomed section (left)
        const box = [80, 200, 820, 800];
        d2.panel(box[0], box[1], box[2], box[3], { alpha: hA, fill: 'rgba(6,14,24,0.95)' });
        const s = 6200, rc = 0.262, zc = 1.17;
        const x0 = box[0] + box[2] / 2 - rc * s, y0 = box[1] + box[3] / 2 + zc * s;
        drawProfile(d2, prof, sec, { x0, y0, s, alpha: hA, vmax: 30, clip: [box[0] + 2, box[1] + 2, box[2] - 4, box[3] - 4], edgeW: 1.0 });
        const t_ = W.hpwhh.t;
        const X = (r) => x0 + r * s, Y = (z) => y0 - z * s;
        const toe = [X(W.hpwhh.r_out), Y(W.hpwhh.z)];
        d2.circle(toe[0], toe[1], 12 + 3 * Math.sin(t * 6), { stroke: PAL.red, width: 3, alpha: hA });
        d2.text('weld toe', toe[0] + 22, toe[1] - 14, { size: 22, weight: 750, color: PAL.red, alpha: hA });
        d2.text('HP housing', X(0.30), Y(1.36), { size: 24, weight: 700, color: PAL.ink, alpha: hA });
        d2.text('20 in casing', X(0.2), Y(1.02), { size: 22, weight: 650, color: PAL.ink, align: 'right', alpha: hA });
        d2.text(`t = ${(t_ * 1000).toFixed(1)} mm`, X(0.2), Y(1.02) + 28, { size: 20, color: PAL.ink2, align: 'right', alpha: hA });
        const rq = seg(t, at('l2', 'half a wall') - 0.3, 0.6), rq2 = seg(t, at('l2', 'one and a half') - 0.3, 0.6);
        const pts = [[0.5, rq, '0.5t'], [1.5, rq2, '1.5t']];
        pts.forEach(([k, q, lab]) => {
          if (q <= 0) return;
          const y = Y(W.hpwhh.z - k * t_);
          d2.line(toe[0] + 4, y, toe[0] + 90, y, { color: PAL.cyan, width: 2, alpha: hA * q });
          d2.circle(toe[0], y, 8, { fill: PAL.cyan, alpha: hA * q, glow: PAL.cyan });
          d2.text(lab, toe[0] + 98, y + 8, { size: 22, weight: 800, color: PAL.cyan, alpha: hA * q });
        });
        d2.rect(box[0] + 2, box[1] + 2, box[2] - 4, 50, { fill: 'rgba(6,14,24,0.9)', alpha: hA });
        d2.text('section on the tension side, axial stress [MPa]', box[0] + 20, box[1] + 34, { size: 20, weight: 650, color: PAL.ink2, alpha: hA });
        divBar(d2, box[0] + box[2] - 70, box[1] + box[3] - 250, 18, 200, 30, '', { alpha: hA });
        // surface stress vs distance (right)
        hotspotPlot(d2, tex, t, hA, {
          box: [960, 200, 880, 780], lev: hp, t_, side: 'out', id: 'hp',
          t1: at('l2', 'Read the surface'), t2: at('l2b', 'extrapolate'), t3: at('l2b', 'that gives'), wk: WK.hp,
        });
      }
      // ---------------------------------------------------------- l3: conductor housing weld, both surfaces
      const bA = env(t, l3 - 0.1, ctx.duration, 0.5, 0.5);
      if (bA > 0) {
        heading(d2, 'B · conductor housing weld', 100, 150, bA, { sub: 'the inside is the hot spot' });
        const box = [80, 200, 820, 800];
        d2.panel(box[0], box[1], box[2], box[3], { alpha: bA, fill: 'rgba(6,14,24,0.95)' });
        const s = 1750, rc = 0.415, zc = 0.9;
        const x0 = box[0] + box[2] / 2 - rc * s, y0 = box[1] + box[3] / 2 + zc * s;
        drawProfile(d2, prof, sec, { x0, y0, s, alpha: bA, vmax: 30, clip: [box[0] + 2, box[1] + 2, box[2] - 4, box[3] - 4], edgeW: 0.8 });
        const X = (r) => x0 + r * s, Y = (z) => y0 - z * s;
        const w = W.lpwh, t_ = w.t;
        const gcl = d2.g;
        gcl.save();
        gcl.beginPath(); gcl.rect(box[0] + 2, box[1] + 52, box[2] - 4, box[3] - 54); gcl.clip();
        d2.text('conductor housing', X(0.49) + 14, Y(1.0), { size: 22, weight: 700, color: PAL.ink, alpha: bA });
        d2.text('36 in conductor', X(0.4572) + 24, Y(0.7), { size: 22, weight: 700, color: PAL.ink, alpha: bA });
        d2.text(`t = ${(t_ * 1000).toFixed(1)} mm`, X(0.4572) + 24, Y(0.7) + 28, { size: 20, color: PAL.ink2, alpha: bA });
        // weld line
        d2.line(X(w.r_in) - 6, Y(w.z), X(w.r_out) + 6, Y(w.z), { color: '#d1bd92', width: 3, dash: [6, 4], alpha: bA });
        d2.text('weld', X(w.r_out) + 14, Y(w.z) + 8, { size: 20, weight: 700, color: '#d1bd92', alpha: bA });
        // mid-surface step
        const mq = seg(t, at('l3', 'mid-surface') - 0.4, 0.8);
        if (mq > 0) {
          const rm1 = (w.r_in + w.r_out) / 2, rm2 = (0.356 + 0.48) / 2;
          d2.path([[X(rm1), Y(0.62)], [X(rm1), Y(0.84)], [X(rm2), Y(1.1)], [X(rm2), Y(1.16)]], { color: PAL.amber, width: 3, dash: [10, 7], alpha: bA * mq, progress: mq });
          d2.text('mid-surface', X(rm1) - 12, Y(0.64), { size: 20, weight: 700, color: PAL.amber, align: 'right', alpha: bA * mq });
          const eq = seg(t, at('l3', 'steps inwards') - 0.1, 0.6);
          d2.line(X(rm1), Y(1.0), X(rm1), Y(1.14), { color: PAL.amber, width: 1.5, dash: [4, 4], alpha: bA * eq });
          d2.dim(X(rm2), Y(1.13), X(rm1), Y(1.13), 'e', { color: PAL.amber, alpha: bA * eq, size: 24, dy: -12 });
        }
        const lb = seg(t, at('l3', 'local bending') - 0.4, 0.8);
        if (lb > 0) {
          for (const z of [0.66, 1.12]) {
            const r = z < 0.9 ? (w.r_in + w.r_out) / 2 : (0.356 + 0.48) / 2;
            const yy = Y(z), sgn = z < 0.9 ? 1 : -1;
            d2.arrow(X(r), yy, X(r), yy + sgn * 60, { color: PAL.red, width: 4, head: 14, alpha: bA * lb });
          }
          d2.momentArrow(X(0.428), Y(0.92), 46, -Math.PI * 0.2, Math.PI * 0.75, { color: PAL.red, width: 3.5, alpha: bA * lb, progress: lb, glow: PAL.red });
          d2.text('local bending', box[0] + 30, Y(0.92) - 6, { size: 24, weight: 800, color: PAL.red, alpha: bA * lb });
          d2.text('M = N · e', box[0] + 30, Y(0.92) + 24, { size: 24, weight: 800, color: PAL.red, alpha: bA * lb });
        }
        // read-out points on both surfaces
        const io = seg(t, at('l3', 'outside is') - 0.3, 0.6), ii = seg(t, at('l3', 'The inside') - 0.3, 0.6);
        for (const [r, q, col] of [[w.r_out, io, PAL.cyan], [w.r_in, ii, PAL.amber]]) {
          if (q <= 0) continue;
          for (const k of [0.5, 1.5]) d2.circle(X(r), Y(w.z - k * t_), 7, { fill: col, alpha: bA * q, glow: col });
        }
        gcl.restore();
        d2.rect(box[0] + 2, box[1] + 2, box[2] - 4, 50, { fill: 'rgba(6,14,24,0.9)', alpha: bA });
        d2.text('section on the tension side, axial stress [MPa]', box[0] + 20, box[1] + 34, { size: 20, weight: 650, color: PAL.ink2, alpha: bA });
        hotspotPlot(d2, tex, t, bA, {
          box: [960, 200, 880, 700], lev: lp, t_, side: 'both', id: 'lp',
          t1: at('l3', 'outside is'), t2: at('l3', 'The inside') - 0.2, t3: at('l3', 'hot spot. That'),
          quad: { t: at('l3q', 'quadratic'), t2: at('l3q', 'Here it gives'), wk: WK.lp },
        });
        keyLine(d2, t, at('l3', 'Always check'), l3q - 0.3, 'Always check both surfaces of a weld', { accent: PAL.amber, size: 30, y: 1042 });
        // both-sided weld assumed: a one-sided weld would put an F3 root on the inside
        const rq = env(t, at('l3', 'That assumes') - 0.3, at('l3', 'Always check') - 0.2, 0.5, 0.5);
        if (rq > 0) {
          d2.panel(990, 912, 840, 96, { alpha: bA * rq, accent: PAL.red, fill: 'rgba(8,20,34,0.95)' });
          d2.text('assumed welded from both sides: the inside is a weld toe (D)', 1016, 950, { size: 21, weight: 700, alpha: bA * rq });
          d2.text(`one-sided weld: inside root, F3, k = 0.10 → ${Math.round(F.sens.lp_root_F3 / F.dff)} days allowed`, 1016, 984, { size: 21, weight: 650, color: PAL.red, alpha: bA * rq * seg(t, at('l3', 'Welded from the outside') - 0.3, 0.6) });
        }
        // l3q: quadratic extrapolation formula
        const qA = bA * env(t, l3q - 0.2, l3b - 0.1, 0.6, 0.5);
        if (qA > 0) {
          d2.panel(990, 912, 840, 110, { alpha: qA, accent: PAL.green, fill: 'rgba(8,20,34,0.95)' });
          tex.show('f07q49', '\\sigma_{hs} = 2.52\\,\\sigma_{0.4t} - 2.24\\,\\sigma_{0.9t} + 0.72\\,\\sigma_{1.4t}', 1016, 926, { size: 30, alpha: qA * seg(t, at('l3q', 'equation four') - 0.4, 0.6) });
          d2.text('C203 eq. (4.9), recommended for thick walls [4.3.4.2]', 1016, 1006, { size: 18, color: PAL.ink2, alpha: qA * seg(t, at('l3q', 'equation four') - 0.4, 0.6) });
        }
        // l3b: tolerances
        keyLine(d2, t, l3b + 0.2, ctx.duration - 0.2, 'Assumed: housing welds within δ0 = 0.05t (0.8 mm casing, 1.9 mm conductor)', { accent: PAL.cyan, size: 26, y: 1042 });
      }
      chainBar(d2, 2, { alpha: 1 - seg(t, l2 - 0.3, 0.4) + seg(t, zoomT + 0.1, 0.5) });
    },
  };
}

// surface stress approaching the toe, with the C203 read-out points and linear extrapolation
// (o.quad: also the quadratic extrapolation of eq. 4.9 on the inside surface)
function hotspotPlot(d2, tex, t, a, o) {
  const [bx, by, bw, bh] = o.box;
  const lev = o.lev, t_ = o.t_;
  const sn = lev.snom / 1e6;
  const sides = o.side === 'both' ? ['out', 'in'] : [o.side];
  const all = sides.flatMap((s) => lev[s].surf);
  const ymax = Math.ceil(Math.max(...all, sn) / 10) * 10 + 10;
  d2.panel(bx, by, bw, bh, { alpha: a });
  const single = o.side !== 'both';
  const P = new Plot(d2, { x: bx + 110, y: by + 80, w: bw - 170, h: bh - (single ? 400 : 230), xr: [4, 0], yr: [0, ymax] });
  P.axes({ alpha: a, xticks: [4, 3, 2, 1.5, 1, 0.5, 0], yticks: [0, 10, 20, 30, 40].filter((v) => v <= ymax), fs: 19, ylabelOff: 62,
    fmtx: (v) => (v === 0 ? 'toe' : `${v}t`), fmty: (v) => String(v), xlabel: 'distance from the weld toe', ylabel: 'surface stress [MPa]' });
  d2.text('surface stress, tension side (FE)', bx + 30, by + 46, { size: 22, weight: 700, alpha: a });
  // nominal
  d2.line(P.X(4), P.Y(sn), P.X(0), P.Y(sn), { color: PAL.ink2, width: 2, dash: [10, 7], alpha: a });
  d2.text(`nominal ${sn.toFixed(1)}`, P.X(4) + 8, P.Y(sn) - 10, { size: 19, color: PAL.ink2, alpha: a });
  const cols = { out: o.id === 'hp' ? PAL.violet : PAL.cyan, in: PAL.amber };
  sides.forEach((s, k) => {
    const L = lev[s];
    const q = seg(t, k === 0 ? o.t1 - 0.4 : o.t2, 1.0);
    const pts = L.d.map((d, i) => [d / t_, L.surf[i]]).filter((p) => p[0] <= 4).sort((p, q2) => p[0] - q2[0]);
    P.curve(pts.slice().reverse(), { color: cols[s], width: 3.2, progress: q, alpha: a });
    P.points(pts, { color: cols[s], r: 3.5, progress: q, alpha: a * 0.7 });
    const e = seg(t, k === 0 ? (single ? o.t2 : o.t1 + 1.2) : o.t2 + 1.0, 1.0, ease.inOutSine);
    const s05 = L.s05 / 1e6, s15 = L.s15 / 1e6, shs = L.shs / 1e6;
    if (e > 0) {
      d2.circle(P.X(1.5), P.Y(s15), 9, { fill: cols[s], stroke: '#06101a', width: 2, alpha: a });
      d2.circle(P.X(0.5), P.Y(s05), 9, { fill: cols[s], stroke: '#06101a', width: 2, alpha: a });
      const xe = lerp(1.5, 0, e);
      d2.line(P.X(1.5), P.Y(s15), P.X(xe), P.Y(s15 + (shs - s15) * (1.5 - xe) / 1.5), { color: cols[s], width: 3, dash: [9, 6], alpha: a });
      if (e >= 1) d2.circle(P.X(0), P.Y(shs), 11, { fill: cols[s], alpha: a, glow: cols[s] });
    }
  });
  // quadratic extrapolation on the inside (eq. 4.9)
  if (o.quad) {
    const W = o.quad.wk, qq = seg(t, o.quad.t - 0.3, 1.0), qe = seg(t, o.quad.t + 1.2, 1.4, ease.inOutSine);
    if (qq > 0) {
      const xs = [0.4, 0.9, 1.4], ys = [W.s04, W.s09, W.s14];
      xs.forEach((x, i) => d2.poly([[P.X(x), P.Y(ys[i]) - 10], [P.X(x) + 10, P.Y(ys[i])], [P.X(x), P.Y(ys[i]) + 10], [P.X(x) - 10, P.Y(ys[i])]], { fill: PAL.green, alpha: a * qq }));
      // Lagrange parabola through the three points
      const Lg = (x) => ys[0] * (x - xs[1]) * (x - xs[2]) / ((xs[0] - xs[1]) * (xs[0] - xs[2]))
        + ys[1] * (x - xs[0]) * (x - xs[2]) / ((xs[1] - xs[0]) * (xs[1] - xs[2]))
        + ys[2] * (x - xs[0]) * (x - xs[1]) / ((xs[2] - xs[0]) * (xs[2] - xs[1]));
      const pc = [];
      for (let i = 0; i <= 40; i++) { const x = lerp(1.6, lerp(1.6, 0, qe), i / 40); pc.push([P.X(x), P.Y(Lg(x))]); }
      if (qe > 0) d2.path(pc, { color: PAL.green, width: 3, dash: [4, 5], alpha: a });
      if (qe >= 1) d2.circle(P.X(0), P.Y(W.shs), 11, { fill: PAL.green, alpha: a, glow: PAL.green });
    }
  }
  // results
  const rq = seg(t, o.t3 - 0.3, 0.6);
  if (single) {
    const W = o.wk;
    tex.show(`f07ext${o.id}`, '\\sigma_{hs} = 1.5\\,\\sigma_{0.5t} - 0.5\\,\\sigma_{1.5t}', bx + 40, by + bh - 232, { size: 34, alpha: a * seg(t, o.t2, 0.6) });
    tex.show(`f07exn${o.id}`, `= 1.5 \\cdot ${W.s05.toFixed(1)} - 0.5 \\cdot ${W.s15.toFixed(1)} = ${W.shs_lin.toFixed(1)}\\ \\mathrm{MPa}`, bx + 40, by + bh - 172, { size: 32, alpha: a * seg(t, o.t3 - 1.2, 0.6), color: cols[o.side] });
    tex.show(`f07exs${o.id}`, `SCF = \\dfrac{${W.shs_lin.toFixed(1)}}{${W.snom.toFixed(1)}} = ${W.scf_lin.toFixed(2)}`, bx + 40, by + bh - 112, { size: 36, alpha: a * rq, color: cols[o.side] });
  } else {
    const so = lev.out.shs / lev.snom, si = lev.in.shs / lev.snom;
    d2.text(`outside: SCF ${so.toFixed(2)}`, bx + 40, by + bh - 50, { size: 28, weight: 750, color: cols.out, alpha: a * seg(t, o.t1 + 2.0, 0.6) });
    const qd = o.quad ? seg(t, o.quad.t2 - 0.3, 0.6) : 0;
    d2.text(`inside: SCF ${si.toFixed(2)}`, bx + bw - 40, by + bh - 50, { size: 30, weight: 800, color: cols.in, align: 'right', alpha: a * rq * (1 - qd) });
    if (qd > 0) d2.text(`inside, quadratic: SCF ${o.quad.wk.scf.toFixed(2)}`, bx + bw - 40, by + bh - 50, { size: 30, weight: 800, color: PAL.green, align: 'right', alpha: a * qd });
    d2.text('SCF relative to the outer-fibre nominal stress', bx + 40, by + bh - 14, { size: 16, color: PAL.ink3, alpha: a });
  }
}
