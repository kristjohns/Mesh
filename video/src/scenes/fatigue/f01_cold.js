// Cold open: descent along the swaying riser with a load-cycle counter, a crack growing at a weld toe,
// the welds nobody can inspect (x-ray below the mudline), title.
import * as THREE from 'three';
import { makeWorld, makeSite, updateWorld } from '../common.js';
import { cameraPath, toScreen, makeBackdrop } from '../../engine/env.js';
import { toThree } from '../../models/template.js';
import { PAL, seg, env, ease, clamp, lerp, rgba, rng } from '../../engine/util.js';

const TW = 8.4; // wave period used for the sway and the counter

export default async function cold(ctx) {
  const { d2, cue, at, renderer } = ctx;
  const w = makeWorld(ctx, { water: { density: 0.02 }, raysOpt: { opacity: 0.11, count: 12, y: 40, height: 110 } });
  makeSite(ctx, w, { riserTop: 200 });
  const back = makeBackdrop();
  const [sx, , sz] = toThree(5.5, 4.5, 0);
  const c1 = cue('c1'), c2 = cue('c2'), c3 = cue('c3'), c4 = cue('c4');
  const tB0 = c3 - 0.6, tB1 = c4 - 0.4;   // macro shot
  const camA = cameraPath(w.camera, [
    { t: 0, pos: [sx - 9, 96, sz + 11], tgt: [sx + 5, 74, sz - 2], fov: 42 },
    { t: c2 - 0.5, pos: [sx - 12, 26, sz + 15], tgt: [sx + 2, 8, sz - 2], fov: 42, e: ease.inOutSine },
    { t: tB0 + 0.4, pos: [sx + 7.5, 17, sz - 8.5], tgt: [sx - 0.5, 6.0, sz + 0.5], fov: 40 },
  ]);
  camA.drift = 0.12;
  const camC = cameraPath(w.camera, [
    { t: tB1, orbit: [24, 58, 9], center: [sx, 1.5, sz], fov: 40 },
    { t: ctx.duration, orbit: [30, 24, 12], center: [sx - 1, 2.5, sz], fov: 40, e: ease.inOutSine },
  ]);
  camC.drift = 0.08;
  const axis = new THREE.Vector3(1, 0, 0.3).normalize();
  const sway = (t) => 0.0035 * Math.sin((2 * Math.PI * t) / TW) * (1 + 0.35 * Math.sin(t * 0.21));

  return {
    sfx: [{ t: 0.0, type: 'drone' }, { t: tB0 + 0.2, type: 'whoosh' }, { t: tB1, type: 'whoosh' }, { t: at('c4', 'D N V') + 0.3, type: 'hit' }],
    render(t) {
      const inB = t > tB0 + 0.35 && t < tB1 - 0.35;
      if (!inB) {
        (t < tB0 + 0.4 ? camA : camC)(t);
        updateWorld(w, t);
        const depthF = clamp((w.camera.position.y - 10) / 70);
        w.rays.children.forEach((m) => { m.material.opacity *= 0.25 + 0.75 * depthF; });
        w.bop.rotation.set(0, 0, 0);
        w.bop.rotateOnWorldAxis(axis, sway(t));
        ctx.renderer.render(w.scene, w.camera);
        d2.vignette(0.5);
      } else {
        back.render(renderer, { alpha: 0.6 });
      }
      // ------------------------------------------------------------ shot A: counter
      const cA = env(t, c1 + 2.0, tB0 + 0.2, 0.8, 0.4);
      if (cA > 0) {
        let n = 1 + Math.floor(t / TW);
        let label = 'LOAD CYCLES';
        const acc = seg(t, c2 - 0.2, 3.0, ease.in);
        if (acc > 0) { n = Math.round(lerp(n, 12136, acc)); }
        const x = 1820, y = 930;
        d2.panel(x - 380, y - 96, 400, 150, { alpha: cA, fill: 'rgba(4,12,22,0.72)', border: 'rgba(120,180,220,0.3)' });
        d2.text(label, x - 356, y - 56, { size: 18, weight: 700, color: PAL.ink2, ls: 3, alpha: cA });
        d2.text(n.toLocaleString('en-US'), x - 356, y + 14, { size: 58, weight: 800, color: acc > 0.98 ? PAL.amber : PAL.ink, alpha: cA });
        d2.text(acc > 0.98 ? 'per day' : 'one per wave', x - 356 + d2.measure(n.toLocaleString('en-US'), 58, 800) + 14, y + 12, { size: 22, weight: 650, color: PAL.ink2, alpha: cA });
        // pulse on each wave
        const ph = ((t % TW) / TW);
        d2.circle(x - 30, y - 60, 6 + 10 * (1 - ph), { fill: PAL.cyan, alpha: cA * (1 - ph) * (1 - acc) });
      }
      // bending moment indicator at the wellhead during shot A
      const mA = env(t, c1 + 4.0, tB0, 0.8, 0.4);
      if (mA > 0) {
        const [px, py] = toScreen([sx, 9.5, sz], w.camera);
        const s = sway(t) / 0.0035;
        d2.momentArrow(px, py, 110, -Math.PI * 0.8, -Math.PI * 0.8 + Math.PI * 0.9 * Math.sign(s) * clamp(Math.abs(s) * 1.4), { color: PAL.amber, width: 5, alpha: mA, glow: PAL.amber });
        d2.text('the stack bends with every wave', px + 130, py - 40, { size: 26, weight: 700, color: PAL.amber, alpha: mA * clamp(Math.abs(s) * 3), shadow: true });
      }
      // ------------------------------------------------------------ shot B: crack at the weld toe
      const bA = env(t, tB0, tB1, 0.5, 0.5);
      if (bA > 0) macro(d2, t, bA, tB0, tB1);
      // ------------------------------------------------------------ shot C: x-ray of the welds, no inspection
      const xA = env(t, tB1 + 0.4, at('c4', 'D N V') + 0.4, 0.8, 0.8);
      if (xA > 0 && !inB) {
        const P3 = (z) => toScreen([sx, z, sz], w.camera);
        const R = 0.4572;
        const right = new THREE.Vector3().subVectors(w.camera.position, new THREE.Vector3(sx, 0, sz)).cross(new THREE.Vector3(0, 1, 0)).normalize();
        const edge = (z, s) => toScreen([sx + right.x * R * s, z, sz + right.z * R * s], w.camera);
        const pl = [], pr = [];
        for (let z = 0; z >= -16; z -= 0.5) { pl.push(edge(z, -1)); pr.push(edge(z, 1)); }
        const xq = seg(t, tB1 + 0.6, 1.6);
        // x-ray window below the mudline
        const [wx0, wy0] = P3(0.0), [wx1, wy1] = P3(-16);
        const ww = 150;
        const gw = d2.g;
        gw.save();
        gw.globalAlpha = xA * xq;
        const gr = gw.createLinearGradient(0, wy0, 0, wy1);
        gr.addColorStop(0, 'rgba(4,14,26,0.82)');
        gr.addColorStop(1, 'rgba(4,14,26,0.0)');
        gw.fillStyle = gr;
        d2.roundRectPath(Math.min(wx0, wx1) - ww / 2, wy0, Math.abs(wx1 - wx0) + ww, wy1 - wy0, 14);
        gw.fill();
        gw.restore();
        d2.line(Math.min(wx0, wx1) - ww / 2 - 30, wy0, Math.max(wx0, wx1) + ww / 2 + 30, wy0, { color: '#b9a98a', width: 2.5, alpha: xA * xq });
        d2.text('MUDLINE', Math.max(wx0, wx1) + ww / 2 + 36, wy0 + 6, { size: 16, weight: 700, color: '#b9a98a', ls: 2, alpha: xA * xq, shadow: true });
        d2.poly([...pl.map((p) => [p[0], p[1]]), ...pr.slice().reverse().map((p) => [p[0], p[1]])], { fill: 'rgba(76,201,240,0.18)', alpha: xA * xq });
        d2.path(pl.map((p) => [p[0], p[1]]), { color: PAL.cyan, width: 2.5, alpha: xA, progress: xq, glow: PAL.cyan, glowBlur: 8 });
        d2.path(pr.map((p) => [p[0], p[1]]), { color: PAL.cyan, width: 2.5, alpha: xA, progress: xq, glow: PAL.cyan, glowBlur: 8 });
        const tagq = seg(t, tB1 + 1.6, 0.6);
        const [mx, my] = P3(-9);
        d2.text('conductor, 60 m into the seabed', mx + 90, my, { size: 22, weight: 700, color: PAL.cyan, alpha: xA * tagq, shadow: true });
        const rings = [[1.2, 'welds'], [0.8, ''], [-3.0, '']];
        rings.forEach(([z], k) => {
          const q = seg(t, at('c4', 'inspect') - 0.6 + k * 0.25, 0.6, ease.outBack);
          if (q <= 0) return;
          const [px, py] = P3(z);
          const r = 22 * clamp(q) + 3 * Math.sin(t * 5 + k);
          d2.circle(px, py, r, { stroke: PAL.amber, width: 3, alpha: xA, glow: PAL.amber });
        });
        const nq = seg(t, at('c4', 'nobody will') - 0.2, 0.6);
        if (nq > 0) {
          const [px, py] = P3(-3.0);
          d2.callout(px, py, px - 260, py + 90, 'no inspection, ever', 'cracks must be predicted, not found', { alpha: xA * nq, progress: nq, color: PAL.amber, size: 28, align: 'right' });
        }
      }
      // ------------------------------------------------------------ title
      const tA = env(t, at('c4', 'D N V') - 0.2, ctx.duration + 1, 0.9, 0.5);
      if (tA > 0) {
        d2.fadeRect(tA * 0.5, '#020810');
        const p = seg(t, at('c4', 'D N V') - 0.2, 1.6, ease.outExpo);
        d2.text('FATIGUE DESIGN WITH DNV-RP-C203', 960, 390, { size: 26, weight: 700, color: PAL.cyan, align: 'center', ls: 9, alpha: tA * p });
        d2.g.save();
        d2.g.filter = `blur(${(1 - p) * 10}px)`;
        d2.text('Every Wave Counts', 960, 500, { size: 112, weight: 800, align: 'center', alpha: tA * p, ls: -1, shadow: 'rgba(0,0,0,0.6)', shadowBlur: 30 });
        d2.g.restore();
        d2.line(960 - 380 * p, 540, 960 + 380 * p, 540, { color: PAL.cyan, width: 2, alpha: tA * 0.8 });
        d2.text('A subsea wellhead, from sea states to fatigue life', 960, 594, { size: 34, weight: 500, color: PAL.ink2, align: 'center', alpha: tA * seg(t, at('c4', 'D N V') + 0.8, 1.0) });
        const chips = [['S-N curves', PAL.violet], ['Rainflow counting', PAL.green], ["Miner's rule", PAL.orange], ['Design fatigue factor', PAL.red]];
        const ws = chips.map(([s]) => d2.measure(s, 24, 650, 1) + 24 * 1.2);
        let cx = 960 - (ws.reduce((a, b) => a + b, 0) + 3 * 28) / 2;
        chips.forEach(([s, col], i) => {
          const q = seg(t, at('c4', 'D N V') + 1.4 + i * 0.25, 0.6, ease.outBack);
          d2.tag(s, cx, 690 + (1 - q) * 20, { size: 24, alpha: tA * clamp(q), color: col });
          cx += ws[i] + 28;
        });
      }
      d2.fadeRect(1 - seg(t, 0, 2.2, ease.inOutSine), '#000000');
    },
  };
}

// microscope-style macro of a weld toe with a crack growing cycle by cycle
function macro(d2, t, a, t0, t1) {
  const g = d2.g;
  const cx = 960, cy = 560, R = 430;
  g.save();
  g.globalAlpha = a;
  g.beginPath();
  g.arc(cx, cy, R, 0, Math.PI * 2);
  g.clip();
  // steel background with grains
  const grd = g.createRadialGradient(cx - 120, cy - 160, 40, cx, cy, R);
  grd.addColorStop(0, '#5b6b78');
  grd.addColorStop(1, '#1d262e');
  g.fillStyle = grd;
  g.fillRect(cx - R, cy - R, 2 * R, 2 * R);
  const RR = rng(21);
  for (let i = 0; i < 260; i++) {
    const x = cx - R + RR() * 2 * R, y = cy - R + RR() * 2 * R, r = 8 + RR() * 26;
    g.strokeStyle = `rgba(200,215,225,${0.04 + RR() * 0.05})`;
    g.lineWidth = 1;
    g.beginPath();
    for (let k = 0; k <= 6; k++) {
      const an = (k / 6) * Math.PI * 2 + RR() * 0.3;
      const px = x + Math.cos(an) * r * (0.8 + RR() * 0.4), py = y + Math.sin(an) * r * (0.8 + RR() * 0.4);
      if (k === 0) g.moveTo(px, py); else g.lineTo(px, py);
    }
    g.stroke();
  }
  // weld cap (upper right) over the plate surface (horizontal line)
  const ys = cy - 60;
  g.fillStyle = 'rgba(10,16,24,0.92)';
  g.beginPath();
  g.moveTo(cx - R, ys);
  g.lineTo(cx - 40, ys);
  g.quadraticCurveTo(cx + 40, ys - 10, cx + 120, ys - 140);
  g.lineTo(cx + R, ys - 260);
  g.lineTo(cx + R, cy - R);
  g.lineTo(cx - R, cy - R);
  g.closePath();
  g.fill();
  // weld metal tint
  g.fillStyle = 'rgba(176,152,108,0.22)';
  g.beginPath();
  g.moveTo(cx - 40, ys);
  g.quadraticCurveTo(cx + 40, ys - 10, cx + 120, ys - 140);
  g.lineTo(cx + R, ys - 260);
  g.lineTo(cx + R, cy + R);
  g.lineTo(cx + 60, cy + R);
  g.quadraticCurveTo(cx + 10, cy + 100, cx - 40, ys);
  g.fill();
  // stress flicker at the toe
  const s = 0.5 + 0.5 * Math.sin(t * 9);
  const hg = g.createRadialGradient(cx - 40, ys, 4, cx - 40, ys, 220);
  hg.addColorStop(0, `rgba(239,71,111,${0.35 + 0.3 * s})`);
  hg.addColorStop(1, 'rgba(239,71,111,0)');
  g.fillStyle = hg;
  g.fillRect(cx - 300, ys - 200, 600, 460);
  // crack, growing in steps (one per cycle burst)
  const u = clamp((t - t0 - 0.6) / (t1 - t0 - 1.4));
  const depth = Math.pow(u, 1.8) * 360;
  const RC = rng(5);
  const pts = [[cx - 40, ys]];
  let y = ys, x = cx - 40;
  while (y < ys + depth) {
    y += 10 + RC() * 8;
    x += (RC() - 0.45) * 14;
    pts.push([x, Math.min(y, ys + depth)]);
  }
  g.restore();
  g.save();
  g.globalAlpha = a;
  g.beginPath();
  g.arc(cx, cy, R, 0, Math.PI * 2);
  g.clip();
  d2.path(pts, { color: '#ffe8b0', width: 3.5, glow: PAL.amber, glowBlur: 18, alpha: a });
  g.restore();
  // lens ring
  d2.circle(cx, cy, R, { stroke: 'rgba(160,200,230,0.5)', width: 3, alpha: a });
  d2.circle(cx, cy, R + 12, { stroke: 'rgba(160,200,230,0.15)', width: 10, alpha: a });
  // labels
  d2.text('WELD TOE', cx - 60, ys - 30, { size: 22, weight: 800, color: PAL.ink, align: 'right', ls: 3, alpha: a, shadow: true });
  const N = Math.round(Math.pow(10, lerp(0, 6.3, Math.pow(u, 0.8))));
  d2.text('cycles', cx + R + 40, cy - 30, { size: 22, weight: 700, color: PAL.ink2, ls: 2, alpha: a });
  d2.text(N.toLocaleString('en-US'), cx + R + 40, cy + 30, { size: 52, weight: 800, color: PAL.amber, alpha: a });
  d2.text('crack depth', cx - R - 40, cy - 30, { size: 22, weight: 700, color: PAL.ink2, align: 'right', ls: 2, alpha: a });
  d2.text(`${(depth / 360 * 30).toFixed(1)} mm`, cx - R - 40, cy + 30, { size: 52, weight: 800, color: PAL.ink, align: 'right', alpha: a });
}
