// Step 2b: nominal stress, hot-spot stress from the local solid model (both housing welds) and the
// misalignment SCF of the conductor girth weld.
import * as THREE from 'three';
import { makeBackdrop, renderViewport, studioScene, envMap, cameraPath } from '../../engine/env.js';
import { Plot } from '../../engine/draw2d.js';
import { makeHotspotFE, drawProfile, divBar, divergingCss } from '../../models/hotspotfe.js';
import { keyLine } from '../common.js';
import { chainBar, heading } from './fcommon.js';
import { PAL, seg, env, ease, clamp, lerp, rgba } from '../../engine/util.js';

export default async function hotspot(ctx) {
  const { d2, cue, at, renderer, data, tex } = ctx;
  const HS = data.hotspot, F = data.fatigue;
  const back = makeBackdrop();
  const l1 = cue('l1'), l2 = cue('l2'), l3 = cue('l3'), l4 = cue('l4');
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
    { t: at('l2', 'read the surface') - 1.6, pos: [-4.0, 2.6, 5.6], tgt: [-0.5, 1.5, -0.1], fov: 26, e: ease.inOutSine },
    { t: at('l2', 'read the surface') + 0.4, pos: [-0.36, 1.21, 0.42], tgt: [-0.28, 1.2, 0.0], fov: 24 },
  ]);
  const W = HS.welds;
  const hp = W.hpwhh.levels[1], lp = W.lpwh.levels[1];
  const prof = HS.profile;
  const sec = HS.section_szz;

  return {
    sfx: [{ t: at('l2', 'read the surface') - 0.6, type: 'whoosh' }],
    render(t) {
      back.render(renderer);
      // ---------------------------------------------------------- l1: nominal stress and SCF
      const nA = env(t, 0.4, l2 - 0.1, 0.6, 0.6);
      if (nA > 0) {
        heading(d2, 'Nominal stress and stress concentration', 120, 170, nA, { sub: 'what the weld actually sees' });
        // pipe cross-section with linear bending stress
        const cx = 470, cy = 590, Ro = 230, Ri = 190;
        const g = d2.g;
        g.save();
        g.globalAlpha = nA;
        for (let k = 0; k < 180; k++) {
          const a0 = (k / 180) * Math.PI * 2, a1 = ((k + 1.2) / 180) * Math.PI * 2;
          const x = Math.cos((a0 + a1) / 2);
          g.beginPath();
          g.arc(cx, cy, Ro, a0, a1);
          g.arc(cx, cy, Ri, a1, a0, true);
          g.closePath();
          g.fillStyle = divergingCss(-x * 0.95);
          g.fill();
        }
        g.restore();
        d2.line(cx, cy - Ro - 40, cx, cy + Ro + 40, { color: PAL.ink2, width: 1.5, dash: [8, 6], alpha: nA });
        d2.text('neutral axis', cx, cy + Ro + 70, { size: 20, color: PAL.ink2, align: 'center', alpha: nA });
        d2.momentArrow(cx, cy, Ro + 50, -Math.PI * 0.85, -Math.PI * 0.15, { color: PAL.amber, width: 4, alpha: nA * seg(t, l1 + 0.5, 0.8), progress: seg(t, l1 + 0.5, 1.0), glow: PAL.amber });
        d2.text('M', cx, cy - Ro - 70, { size: 34, weight: 800, color: PAL.amber, align: 'center', alpha: nA * seg(t, l1 + 0.8, 0.6) });
        d2.text('tension', cx - Ro - 20, cy + 8, { size: 22, weight: 700, color: PAL.red, align: 'right', alpha: nA });
        d2.text('compression', cx + Ro + 20, cy + 8, { size: 22, weight: 700, color: '#6f8cff', alpha: nA });
        const fq = seg(t, at('l1', 'section modulus') - 0.4, 0.6);
        d2.panel(860, 300, 900, 170, { alpha: nA * fq, accent: PAL.cyan });
        tex.show('f07nom', '\\sigma_{nom} = \\dfrac{M}{W}, \\qquad W = \\dfrac{I}{D/2}', 900, 330, { size: 44, alpha: nA * fq });
        const sq = seg(t, at('l1', 'concentrates') - 0.6, 0.6);
        d2.panel(860, 510, 900, 330, { alpha: nA * sq, accent: PAL.red });
        d2.text('but the weld geometry raises it locally', 900, 560, { size: 26, weight: 700, color: PAL.red, alpha: nA * sq });
        tex.show('f07scf', '\\sigma_{hs} = SCF \\cdot \\sigma_{nom}', 900, 600, { size: 46, alpha: nA * sq });
        d2.text('SCF: stress concentration factor, from', 900, 740, { size: 22, color: PAL.ink2, alpha: nA * sq });
        d2.text('FE hot-spot analysis or C203 formulas', 900, 772, { size: 22, color: PAL.ink2, alpha: nA * sq });
      }
      // ---------------------------------------------------------- l2: 3D model then hot-spot read-out (HP weld)
      const zoomT = at('l2', 'read the surface');
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
          t1: at('l2', 'read the surface'), t2: at('l2', 'extrapolate'), t3: at('l2', 'that gives'),
        });
      }
      // ---------------------------------------------------------- l3: conductor housing weld, both surfaces
      const bA = env(t, l3 - 0.1, l4 - 0.1, 0.5, 0.5);
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
          t1: at('l3', 'outside is'), t2: at('l3', 'The inside') - 0.2, t3: at('l3', 'with a factor'),
        });
        keyLine(d2, t, at('l3', 'Always check'), l4 - 0.3, 'Always check both surfaces of a weld', { accent: PAL.amber, size: 30, y: 960 });
      }
      // ---------------------------------------------------------- l4: girth weld misalignment, summary
      const cA = env(t, l4 - 0.1, ctx.duration, 0.5, 0.5);
      if (cA > 0) {
        heading(d2, 'C · conductor girth weld', 100, 150, cA, { sub: 'nominal stress × SCF for misalignment' });
        const cx = 480, cy = 470, T = 120, dm = 34;
        d2.panel(80, 200, 820, 520, { alpha: cA });
        // two walls with hi-lo misalignment
        d2.poly([[cx - 360, cy - T / 2], [cx - 30, cy - T / 2], [cx - 30, cy + T / 2], [cx - 360, cy + T / 2]], { fill: 'rgba(130,160,185,0.4)', stroke: '#9fb3c4', width: 2, alpha: cA });
        d2.poly([[cx + 30, cy - T / 2 + dm], [cx + 360, cy - T / 2 + dm], [cx + 360, cy + T / 2 + dm], [cx + 30, cy + T / 2 + dm]], { fill: 'rgba(130,160,185,0.4)', stroke: '#9fb3c4', width: 2, alpha: cA });
        d2.poly([[cx - 60, cy - T / 2], [cx - 20, cy - T / 2 - 18], [cx + 30, cy - T / 2 - 10 + dm * 0.5], [cx + 60, cy - T / 2 + dm], [cx + 60, cy + T / 2 + dm], [cx + 20, cy + T / 2 + dm + 14], [cx - 30, cy + T / 2 + 10], [cx - 60, cy + T / 2]], { fill: 'rgba(176,152,108,0.6)', stroke: '#d1bd92', width: 2, alpha: cA });
        d2.line(cx - 360, cy, cx - 30, cy, { color: PAL.ink3, width: 1.5, dash: [6, 6], alpha: cA });
        d2.line(cx + 30, cy + dm, cx + 360, cy + dm, { color: PAL.ink3, width: 1.5, dash: [6, 6], alpha: cA });
        const ph = 0.5 + 0.5 * Math.sin(t * 2.2);
        for (const s of [-1, 1]) d2.arrow(cx + s * 380, cy + (s > 0 ? dm : 0), cx + s * (410 + 30 * ph), cy + (s > 0 ? dm : 0), { color: PAL.cyan, width: 4, head: 14, alpha: cA });
        const dq = seg(t, at('l4', 'six millimetres') - 0.3, 0.6);
        d2.dim(cx + 250, cy - T / 2, cx + 250, cy - T / 2 + dm, '', { color: PAL.amber, alpha: cA * dq });
        d2.text('δm = 6 mm', cx + 270, cy - T / 2 + dm / 2 + 8, { size: 24, weight: 800, color: PAL.amber, alpha: cA * dq });
        d2.dim(cx - 300, cy - T / 2, cx - 300, cy + T / 2, '', { color: PAL.ink2, alpha: cA });
        d2.text('t = 38.1 mm', cx - 290, cy + 8, { size: 22, weight: 700, color: PAL.ink2, alpha: cA });
        d2.text('hi-lo misalignment bends the wall locally', cx, cy + T / 2 + dm + 90, { size: 22, color: PAL.ink2, align: 'center', alpha: cA });
        // formula: C203 eq. (3.9), delta0 from Table 3-1
        const fq = seg(t, at('l4', 'C two-oh-three gives') - 0.5, 0.7);
        const G = F.girth;
        d2.panel(80, 750, 820, 260, { alpha: cA * fq, accent: PAL.amber });
        tex.show('f07mis', 'SCF = 1 + \\dfrac{3\\,(\\delta_m - \\delta_0)}{t}\\, e^{-\\alpha}', 110, 772, { size: 36, alpha: cA * fq });
        tex.show('f07mis3', '\\alpha = \\dfrac{0.91\\,L}{\\sqrt{D\\,t}}', 600, 772, { size: 30, alpha: cA * fq, color: PAL.ink2 });
        tex.show('f07mis2', `= 1 + \\dfrac{3\\,(6 - ${(0.05 * G.t * 1e3).toFixed(1)})}{${(G.t * 1e3).toFixed(1)}} \\cdot ${Math.exp(-G.alpha).toFixed(2)} = ${G.scf.toFixed(2)}`, 110, 880, { size: 36, alpha: cA * seg(t, at('l4', 'one point two seven') - 0.3, 0.6), color: PAL.amber });
        const lq = cA * seg(t, at('l4', 'exponential') - 0.3, 0.6);
        d2.text(`L = ${Math.round(G.L * 1e3)} mm weld width`, 625, 912, { size: 18, color: PAL.ink3, alpha: lq });
        d2.text(`D = ${(G.D * 1e3).toFixed(0)} mm outer diameter`, 625, 938, { size: 18, color: PAL.ink3, alpha: lq });
        const d0 = seg(t, at('l4', 'five percent') - 0.3, 0.6);
        d2.tag('δ0 = 0.05t is already in the S-N test data (C203 Table 3-1)', 490, 1040, { size: 19, color: PAL.ink2, align: 'center', alpha: cA * d0, fill: 'rgba(5,14,26,0.92)' });
        // summary table (right)
        const sq = seg(t, l4 + 1.0, 0.7);
        const rows = [
          ['A', 'HP housing weld', 'hot spot, FE', 'outside', F.scf.hp, PAL.violet],
          ['B', 'conductor housing weld', 'hot spot, FE', 'inside', F.scf.lp, PAL.cyan],
          ['C', 'conductor girth weld', 'nominal + C203 formula', 'outside', F.scf.cg, PAL.amber],
        ];
        d2.panel(960, 200, 880, 520, { alpha: cA * sq });
        d2.text('Stress concentration factors', 1000, 255, { size: 30, weight: 750, alpha: cA * sq });
        rows.forEach(([L, n, m, side, v, col], k) => {
          const q = seg(t, l4 + 1.4 + k * 0.5, 0.6);
          const y = 340 + k * 120;
          d2.circle(1022, y - 8, 20, { fill: rgba(col, 0.25), stroke: col, width: 2.5, alpha: cA * q });
          d2.text(L, 1022, y, { size: 22, weight: 800, color: col, align: 'center', alpha: cA * q });
          d2.text(n, 1062, y - 6, { size: 26, weight: 700, alpha: cA * q });
          d2.text(`${m} · ${side}`, 1062, y + 26, { size: 20, color: PAL.ink2, alpha: cA * q });
          const lit = k === 2 ? seg(t, at('l4', 'one point two seven'), 0.5) : 1;
          d2.text(v.toFixed(2), 1790, y + 8, { size: 44, weight: 800, color: col, align: 'right', alpha: cA * q * lit });
        });
      }
      chainBar(d2, 2, { alpha: 1 - seg(t, l2 - 0.3, 0.4) + seg(t, zoomT + 0.1, 0.5) });
    },
  };
}

// surface stress approaching the toe, with the C203 read-out points and linear extrapolation
function hotspotPlot(d2, tex, t, a, o) {
  const [bx, by, bw, bh] = o.box;
  const lev = o.lev, t_ = o.t_;
  const sn = lev.snom / 1e6;
  const sides = o.side === 'both' ? ['out', 'in'] : [o.side];
  const all = sides.flatMap((s) => lev[s].surf);
  const ymax = Math.ceil(Math.max(...all, sn) / 10) * 10 + 10;
  d2.panel(bx, by, bw, bh, { alpha: a });
  const P = new Plot(d2, { x: bx + 110, y: by + 80, w: bw - 170, h: bh - (o.side === 'both' ? 230 : 300), xr: [4, 0], yr: [0, ymax] });
  P.axes({ alpha: a, xticks: [4, 3, 2, 1.5, 1, 0.5, 0], yticks: [0, 10, 20, 30, 40].filter((v) => v <= ymax), fs: 19, ylabelOff: 62,
    fmtx: (v) => (v === 0 ? 'toe' : `${v}t`), fmty: (v) => String(v), xlabel: 'distance from the weld toe', ylabel: 'surface stress [MPa]' });
  d2.text('surface stress, tension side (FE)', bx + 30, by + 46, { size: 22, weight: 700, alpha: a });
  // nominal
  d2.line(P.X(4), P.Y(sn), P.X(0), P.Y(sn), { color: PAL.ink2, width: 2, dash: [10, 7], alpha: a });
  d2.text(`nominal ${sn.toFixed(1)}`, P.X(4) + 8, P.Y(sn) - 10, { size: 19, color: PAL.ink2, alpha: a });
  const cols = { out: o.id === 'hp' ? PAL.violet : PAL.cyan, in: PAL.amber };
  const res = [];
  sides.forEach((s, k) => {
    const L = lev[s];
    const q = seg(t, k === 0 ? o.t1 - 0.4 : o.t2, 1.0);
    const pts = L.d.map((d, i) => [d / t_, L.surf[i]]).filter((p) => p[0] <= 4).sort((p, q2) => p[0] - q2[0]);
    P.curve(pts.slice().reverse(), { color: cols[s], width: 3.2, progress: q, alpha: a });
    P.points(pts.filter((_, i) => i % 1 === 0).map((p) => p), { color: cols[s], r: 3.5, progress: q, alpha: a * 0.7 });
    const e = seg(t, k === 0 ? (o.side === 'both' ? o.t1 + 1.2 : o.t2) : o.t2 + 1.0, 1.0, ease.inOutSine);
    const s05 = L.s05 / 1e6, s15 = L.s15 / 1e6, shs = L.shs / 1e6;
    if (e > 0) {
      d2.circle(P.X(1.5), P.Y(s15), 9, { fill: cols[s], stroke: '#06101a', width: 2, alpha: a });
      d2.circle(P.X(0.5), P.Y(s05), 9, { fill: cols[s], stroke: '#06101a', width: 2, alpha: a });
      const xe = lerp(1.5, 0, e);
      d2.line(P.X(1.5), P.Y(s15), P.X(xe), P.Y(s15 + (shs - s15) * (1.5 - xe) / 1.5), { color: cols[s], width: 3, dash: [9, 6], alpha: a });
      if (e >= 1) d2.circle(P.X(0), P.Y(shs), 11, { fill: cols[s], alpha: a, glow: cols[s] });
    }
    res.push([s, shs, e, cols[s]]);
  });
  // results
  const rq = seg(t, o.t3 - 0.3, 0.6);
  if (o.side !== 'both') {
    tex.show(`f07ext${o.id}`, '\\sigma_{hs} = 1.5\\,\\sigma_{0.5t} - 0.5\\,\\sigma_{1.5t}', bx + 40, by + bh - 120, { size: 34, alpha: a * seg(t, o.t2, 0.6) });
    d2.text(`SCF = ${(lev[o.side].shs / lev.snom).toFixed(2)}`, bx + bw - 40, by + bh - 50, { size: 40, weight: 800, color: cols[o.side], align: 'right', alpha: a * rq });
  } else {
    const so = lev.out.shs / lev.snom, si = lev.in.shs / lev.snom;
    d2.text(`outside: SCF ${so.toFixed(2)}`, bx + 40, by + bh - 50, { size: 30, weight: 750, color: cols.out, alpha: a * seg(t, o.t1 + 2.0, 0.6) });
    d2.text(`inside: SCF ${si.toFixed(2)}`, bx + bw - 40, by + bh - 50, { size: 36, weight: 800, color: cols.in, align: 'right', alpha: a * rq });
  }
}
