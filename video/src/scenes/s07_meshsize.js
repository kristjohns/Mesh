// Chapter 2: mesh size. Fillet converges, sharp corner diverges, rules of thumb, convergence loop.
import { makeBackdrop } from '../engine/env.js';
import { chapterCard, ruleCard, keyLine } from './common.js';
import { colorBar } from '../models/femesh.js';
import { Plot } from '../engine/draw2d.js';
import { PAL, seg, env, ease, clamp, lerp, rgba, turboCss } from '../engine/util.js';

// static meshes are rasterised once into an offscreen canvas and then blitted with alpha
const _cache = new Map();
function drawFE2D(d2, mesh, o) {
  const a = o.alpha ?? 1;
  if (a <= 0 || !mesh) return;
  const key = `${mesh.hc}_${mesh.t.length}_${o.x0}_${o.y0}_${o.s}_${o.mirror}_${o.clip}_${o.edgeW}_${o.vmax}`;
  let c = _cache.get(key);
  if (!c) {
    c = document.createElement('canvas');
    c.width = 1920; c.height = 1080;
    const fake = { g: c.getContext('2d') };
    drawFE2Draw(fake, mesh, { ...o, alpha: 1 });
    _cache.set(key, c);
  }
  const g = d2.g;
  g.save();
  g.globalAlpha = a;
  g.drawImage(c, 0, 0);
  g.restore();
}
function drawFE2Draw(d2, mesh, o) {
  const a = 1;
  const { x0, y0, s } = o;
  const g = d2.g;
  g.save();
  g.globalAlpha = a;
  if (o.clip) { g.beginPath(); g.rect(...o.clip); g.clip(); }
  const P = mesh.p, T = mesh.t, S = mesh.s1;
  const vmax = o.vmax ?? 2.4;
  for (const mirror of o.mirror ? [1, -1] : [1]) {
    for (const tr of T) {
      const v = (S[tr[0]] + S[tr[1]] + S[tr[2]]) / 3;
      g.beginPath();
      for (let k = 0; k < 3; k++) {
        const [x, y] = P[tr[k]];
        const X = x0 + x * s, Y = y0 - mirror * y * s;
        if (k === 0) g.moveTo(X, Y); else g.lineTo(X, Y);
      }
      g.closePath();
      g.fillStyle = turboCss(clamp(v / vmax));
      g.fill();
      // edge length on screen: fade the wireframe out where elements become tiny
      const [xa, ya] = P[tr[0]], [xb, yb] = P[tr[1]];
      const lpx = Math.hypot(xb - xa, yb - ya) * s;
      if (o.edges !== false && lpx > 2.5) {
        g.strokeStyle = o.edgeColor ?? `rgba(5,12,20,${(0.55 * Math.min(1, (lpx - 2.5) / 6)).toFixed(3)})`;
        g.lineWidth = o.edgeW ?? 0.6;
        g.stroke();
      } else if (o.edges !== false) {
        g.strokeStyle = g.fillStyle; g.lineWidth = 0.6; g.stroke();
      }
    }
  }
  g.restore();
}

export default async function meshsize(ctx) {
  const { d2, cue, at, renderer, data } = ctx;
  const N = data.notch;
  const back = makeBackdrop();
  const m1 = cue('m1'), m2 = cue('m2'), m3 = cue('m3'), m4 = cue('m4'), m5 = cue('m5'), m6 = cue('m6');
  const F = N.series.fillet, S = N.series.sharp;
  const conv = F[F.length - 1].peak;
  const hs = F.map((q) => q.hc);
  const meshKey = (kind, h) => `${kind}_${h}`;
  const xOf = (i) => i + 1; // refinement step

  return {
    sfx: [{ t: 0.1, type: 'chapter' }, { t: m3 + 0.3, type: 'whoosh' }],
    render(t) {
      back.render(renderer);
      // ------------------------------------------------ m1: principle
      const pA = env(t, m1 + 0.5, m2 + 0.4, 0.6, 0.6);
      if (pA > 0) {
        d2.text('Fine where the stress changes quickly,', 960, 170, { size: 46, weight: 800, align: 'center', alpha: pA * seg(t, at('m1', 'The mesh has to be fine'), 0.7) });
        d2.text('coarse where it doesn’t.', 960, 230, { size: 46, weight: 800, align: 'center', color: PAL.ink2, alpha: pA * seg(t, at('m1', 'coarse'), 0.7) });
        const mesh = N.meshes['fillet_0.00625'];
        drawFE2D(d2, mesh, { x0: 960, y0: 640, s: 330, mirror: true, alpha: pA * seg(t, m1 + 1.0, 1.0), edgeW: 0.35 });
        colorBar(d2, 1720, 450, 20, 300, 0, 2.4, 'σ₁ / σ_nom', { alpha: pA, fmt: (v) => v.toFixed(1) });
        const hA = pA * seg(t, at('m1', 'changes quickly'), 0.6);
        d2.circle(960 + 0.05 * 330, 640 - 0.55 * 330, 70, { stroke: PAL.amber, width: 3, alpha: hA });
        d2.circle(960 + 0.05 * 330, 640 + 0.55 * 330, 70, { stroke: PAL.amber, width: 3, alpha: hA });
        d2.text('stress gradient → small elements', 960 + 120, 640 - 0.55 * 330 - 60, { size: 24, weight: 700, color: PAL.amber, alpha: hA });
        d2.text('uniform stress → large elements', 960 - 2 * 330 + 10, 640 - 0.75 * 330 - 24, { size: 24, weight: 700, color: PAL.ink2, alpha: pA * seg(t, at('m1', 'coarse'), 0.6) });
      }
      // ------------------------------------------------ m2/m3: convergence study
      const cA = env(t, m2 + 0.2, m4 + 0.2, 0.6, 0.6);
      if (cA > 0) {
        const sharp = t > m3 + 0.5;
        const kind = sharp ? 'sharp' : 'fillet';
        // refinement index over time
        let k;
        if (!sharp) k = Math.floor(lerp(0, 6.999, seg(t, at('m2', 'refine the mesh'), 12.0, ease.linear)));
        else k = Math.floor(lerp(0, 6.999, seg(t, at('m3', 'Each time'), 6.0, ease.linear)));
        const h = hs[k];
        const mesh = N.meshes[meshKey(kind, h)];
        d2.text(sharp ? 'Sharp corner' : 'Shoulder with a fillet radius', 520, 120, { size: 40, weight: 800, align: 'center', alpha: cA, color: sharp ? PAL.red : PAL.green });
        // full bar
        drawFE2D(d2, mesh, { x0: 520, y0: 360, s: 205, mirror: true, alpha: cA, edgeW: 0.3 });
        // zoom at the corner
        const zx = 110, zy = 560, zw = 820, zh = 420;
        d2.panel(zx, zy, zw, zh, { alpha: cA, fill: 'rgba(5,12,20,0.95)' });
        const zs = 1500;
        drawFE2D(d2, mesh, { x0: zx + zw / 2 - 0.05 * zs, y0: zy + zh / 2 + 0.58 * zs, s: zs, alpha: cA, clip: [zx + 2, zy + 2, zw - 4, zh - 4], edgeW: 0.8 });
        d2.rect(520 - 0.13 * 205, 360 - 0.72 * 205, 0.32 * 205, 0.25 * 205, { stroke: PAL.cyan, width: 2, alpha: cA });
        d2.tag(`element size at corner = r / ${Math.round(0.1 / h)}`, zx + 20, zy + 34, { size: 20, alpha: cA, color: PAL.cyan });
        if (!sharp) d2.text(`≈ ${Math.max(1, Math.round((Math.PI / 2) * 0.1 / h))} elements around the fillet`, zx + 20, zy + zh + 40, { size: 26, weight: 700, color: PAL.ink, alpha: cA });
        // plot
        const rescale = seg(t, at('m3', 'Each time') + 2.2, 1.5, ease.inOutSine);
        const P = new Plot(d2, { x: 1160, y: 200, w: 640, h: 560, xr: [0.6, 7.4], yr: [lerp(1.6, 1.0, rescale), lerp(2.45, 11.5, rescale)] });
        const yt = rescale < 0.5 ? [1.6, 1.8, 2.0, 2.2, 2.4] : [1, 3, 5, 7, 9, 11];
        P.axes({ alpha: cA, xticks: [1, 2, 3, 4, 5, 6, 7], yticks: yt, fmtx: (v) => `r/${Math.round(Math.pow(2, v - 1))}`, fmty: (v) => v.toFixed(1),
          xlabel: 'element size at the corner (halved each step)', ylabel: 'peak stress / nominal', fs: 18, ylabelOff: 62 });
        P.clipBegin();
        const fp = seg(t, at('m2', 'refine the mesh'), 12.0, ease.linear);
        const nF = Math.max(1, Math.min(7, Math.floor(fp * 7) + 1));
        const fpts = F.slice(0, nF).map((q, i) => [xOf(i), q.peak]);
        P.curve(fpts, { color: PAL.green, width: 3.5, alpha: cA });
        P.points(fpts, { color: PAL.green, r: 7, alpha: cA });
        // converged band
        const band = cA * seg(t, at('m2', 'within one percent'), 0.6);
        if (band > 0) {
          d2.rect(P.x, P.Y(conv * 1.01), P.w, P.Y(conv * 0.99) - P.Y(conv * 1.01), { fill: rgba(PAL.green, 0.15), alpha: band });
          d2.line(P.x, P.Y(conv), P.x + P.w, P.Y(conv), { color: PAL.green, width: 1.5, dash: [6, 6], alpha: band });
        }
        if (sharp) {
          const sp = seg(t, at('m3', 'Each time'), 6.0, ease.linear);
          const nS = Math.max(1, Math.min(7, Math.floor(sp * 7) + 1));
          const spts = S.slice(0, nS).map((q, i) => [xOf(i), q.peak]);
          P.curve(spts, { color: PAL.red, width: 3.5, alpha: cA });
          P.points(spts, { color: PAL.red, r: 7, alpha: cA });
        }
        P.clipEnd();
        d2.line(P.x + 30, P.y + 20, P.x + 70, P.y + 20, { color: PAL.green, width: 4, alpha: cA });
        d2.text('fillet', P.x + 80, P.y + 28, { size: 22, weight: 650, color: PAL.green, alpha: cA });
        if (sharp) {
          d2.line(P.x + 30, P.y + 54, P.x + 70, P.y + 54, { color: PAL.red, width: 4, alpha: cA });
          d2.text('sharp corner', P.x + 80, P.y + 62, { size: 22, weight: 650, color: PAL.red, alpha: cA });
        }
        // annotations
        const a1 = cA * env(t, at('m2', 'one element across'), m3 + 0.4, 0.5, 0.4);
        if (a1 > 0) {
          const e = (F[0].peak - conv) / conv;
          d2.text(`${Math.round(100 * e)} %`, P.X(1) + 16, P.Y(F[0].peak) + 8, { size: 28, weight: 800, color: PAL.amber, alpha: a1 });
        }
        const a2 = cA * env(t, at('m2', 'within one percent'), m3 + 0.4, 0.5, 0.4);
        if (a2 > 0) {
          const e = (F[3].peak - conv) / conv;
          d2.text(`${(100 * e).toFixed(1)} %`, P.X(4) - 4, P.Y(F[3].peak) + 42, { size: 26, weight: 800, color: PAL.green, alpha: a2, align: 'center' });
          d2.text('converged', P.X(7) - 10, P.Y(conv) - 18, { size: 24, weight: 800, color: PAL.green, align: 'right', alpha: cA * seg(t, at('m2', 'converged result'), 0.5) });
        }
        const a3 = cA * seg(t, at('m3', 'thirty-seven'), 0.6);
        if (a3 > 0) {
          d2.panel(1180, 835, 620, 170, { alpha: a3, accent: PAL.red });
          d2.text('+37 % every time the element size halves', 1210, 885, { size: 26, weight: 750, color: PAL.red, alpha: a3 });
          d2.text('never levels off → singularity', 1210, 925, { size: 26, weight: 650, alpha: a3 * seg(t, at('m3', 'singularity'), 0.5) });
          ctx.tex.show('s07sing', '\\sigma \\propto r^{\\lambda-1},\\;\\; \\lambda \\approx 0.54 \\;\\Rightarrow\\; \\sigma \\to \\infty', 1210, 940, { size: 30, alpha: a3 * seg(t, at('m3', 'infinite'), 0.5) });
        }
      }
      // ------------------------------------------------ m4: what to do instead
      const oA = env(t, m4 + 0.2, m5 + 0.2, 0.5, 0.5);
      if (oA > 0) {
        d2.text('Never report the peak at a singularity', 960, 200, { size: 48, weight: 800, align: 'center', alpha: oA });
        const opts = [
          ['Model the real radius', 'then converge the mesh', at('m4', 'Model the real')],
          ['Read the stress at a distance', 'hot-spot / structural stress methods', at('m4', 'read the stress')],
          ['Fracture mechanics', 'when the crack-like corner is the point', at('m4', 'fracture mechanics')],
        ];
        opts.forEach(([a, b, tt], i) => {
          const q = seg(t, tt - 0.2, 0.6, ease.out);
          const x = 190 + i * 530;
          d2.panel(x, 330 + (1 - q) * 30, 480, 300, { alpha: oA * q, accent: [PAL.green, PAL.cyan, PAL.violet][i] });
          d2.text(String(i + 1), x + 40, 420 + (1 - q) * 30, { size: 64, weight: 800, color: [PAL.green, PAL.cyan, PAL.violet][i], alpha: oA * q });
          const L = d2.wrap(a, 400, 32, 750);
          L.forEach((ln, j) => d2.text(ln, x + 40, 490 + j * 40 + (1 - q) * 30, { size: 32, weight: 750, alpha: oA * q }));
          const L2 = d2.wrap(b, 400, 24, 500);
          L2.forEach((ln, j) => d2.text(ln, x + 40, 500 + L.length * 40 + 20 + j * 30 + (1 - q) * 30, { size: 24, color: PAL.ink2, alpha: oA * q }));
        });
      }
      // ------------------------------------------------ m5: rules of thumb with mini illustrations
      const rA = env(t, m5 + 0.2, m6 + 0.2, 0.5, 0.5);
      if (rA > 0) {
        d2.text('Starting rules for mesh density', 960, 120, { size: 46, weight: 800, align: 'center', alpha: rA });
        const cells = [
          { t: at('m5', 'Put at least'), title: 'Through a wall in bending', sub: '≥ 2 quadratic or ≥ 4 linear', draw: (x, y, q) => {
            for (const [nl, col, ox] of [[2, PAL.amber, 0], [4, PAL.cyan, 200]]) {
              const w = 120, h = 150;
              for (let i = 0; i < nl; i++) for (let j = 0; j < 4; j++) d2.rect(x + ox + (w / nl) * i, y + (h / 4) * j, w / nl, h / 4, { stroke: col, width: 2, fill: rgba(col, 0.08), alpha: rA * q });
              d2.text(nl === 2 ? 'quadratic' : 'linear', x + ox + w / 2, y + h + 30, { size: 20, color: col, align: 'center', alpha: rA * q });
            }
          } },
          { t: at('m5', 'Use about ten'), title: '90° fillet', sub: '≈ 10–12 elements around it', draw: (x, y, q) => {
            const cx = x + 280, cy = y + 160, R = 140;
            for (let i = 0; i <= 12; i++) {
              const a = Math.PI + (i / 12) * (Math.PI / 2);
              d2.line(cx + R * Math.cos(a), cy + R * Math.sin(a), cx + (R + 30) * Math.cos(a), cy + (R + 30) * Math.sin(a), { color: PAL.green, width: 2, alpha: rA * q });
            }
            const arc = [];
            for (let i = 0; i <= 40; i++) { const a = Math.PI + (i / 40) * (Math.PI / 2); arc.push([cx + R * Math.cos(a), cy + R * Math.sin(a)]); }
            d2.path(arc, { color: PAL.ink, width: 3, alpha: rA * q });
            const arc2 = arc.map(([px, py]) => [cx + (px - cx) * (R + 30) / R, cy + (py - cy) * (R + 30) / R]);
            d2.path(arc2, { color: PAL.green, width: 2, alpha: rA * q });
          } },
          { t: at('m5', 'Keep the size change'), title: 'Gradual size transition', sub: 'neighbours differ by < ~30 %', draw: (x, y, q) => {
            let xx = x + 10, w = 22;
            for (let i = 0; i < 9; i++) { d2.rect(xx, y + 60, w, w, { stroke: PAL.cyan, width: 2, fill: rgba(PAL.cyan, 0.08), alpha: rA * q }); xx += w + 4; w *= 1.25; }
            d2.text('×1.25 per element', x + 10, y + 200, { size: 20, color: PAL.cyan, alpha: rA * q });
          } },
          { t: at('m5', 'well shaped'), title: 'Well-shaped elements', sub: 'low aspect ratio, little distortion', draw: (x, y, q) => {
            const shapes = [
              [[0, 0], [90, 0], [90, 90], [0, 90], PAL.green, 'good'],
              [[0, 30], [200, 30], [200, 60], [0, 60], PAL.amber, 'stretched'],
              [[0, 0], [90, 0], [150, 90], [60, 90], PAL.red, 'skewed'],
            ];
            let ox = x;
            for (const [a, b, c, dd, col, lab] of shapes) {
              d2.poly([a, b, c, dd].map(([u, v]) => [ox + u, y + 40 + v]), { stroke: col, width: 3, fill: rgba(col, 0.1), alpha: rA * q });
              d2.text(lab, ox + 45, y + 170, { size: 20, color: col, alpha: rA * q });
              ox += lab === 'stretched' ? 230 : 130;
            }
          } },
        ];
        cells.forEach((c, i) => {
          const q = seg(t, c.t - 0.2, 0.6, ease.out);
          const x = 120 + (i % 2) * 860, y = 190 + Math.floor(i / 2) * 410;
          d2.panel(x, y, 820, 370, { alpha: rA * q, accent: [PAL.amber, PAL.green, PAL.cyan, PAL.violet][i] });
          d2.text(c.title, x + 36, y + 56, { size: 32, weight: 750, alpha: rA * q });
          d2.text(c.sub, x + 36, y + 94, { size: 24, color: PAL.ink2, alpha: rA * q });
          c.draw(x + 60, y + 130, q);
        });
      }
      // ------------------------------------------------ m6: convergence loop
      const lA = env(t, m6 + 0.2, ctx.duration, 0.5, 0.5);
      if (lA > 0) {
        d2.text('The real test: a convergence study', 960, 170, { size: 46, weight: 800, align: 'center', alpha: lA });
        d2.text('on the result you care about', 960, 220, { size: 28, color: PAL.ink2, align: 'center', alpha: lA });
        const cx = 960, cy = 560, R = 230;
        const steps = [['Refine', at('m6', 'refine')], ['Rerun', at('m6', 'rerun')], ['Compare', at('m6', 'compare')]];
        steps.forEach(([s, tt], i) => {
          const a0 = -Math.PI / 2 + (i * 2 * Math.PI) / 3;
          const q = seg(t, tt - 0.2, 0.6, ease.outBack);
          const x = cx + R * Math.cos(a0), y = cy + R * Math.sin(a0);
          d2.circle(x, y, 92 * clamp(q), { fill: rgba(PAL.cyan, 0.12), stroke: PAL.cyan, width: 3, alpha: lA });
          d2.text(s, x, y + 12, { size: 34, weight: 800, align: 'center', alpha: lA * clamp(q) });
          const b0 = a0 + 0.5, b1 = a0 + (2 * Math.PI) / 3 - 0.5;
          d2.momentArrow(cx, cy, R, b0, b1, { color: PAL.cyan, width: 4, alpha: lA * seg(t, tt + 0.3, 0.6), progress: seg(t, tt + 0.3, 0.8), head: 18 });
        });
        const qA = lA * seg(t, at('m6', 'still changing'), 0.6);
        d2.text('Δ < ~2 % ?', cx, cy + 14, { size: 40, weight: 800, align: 'center', color: PAL.amber, alpha: lA * seg(t, at('m6', 'compare'), 0.6) });
        d2.text('If the result is still changing, the mesh isn’t finished.', 960, 930, { size: 32, weight: 650, align: 'center', alpha: qA, color: PAL.ink });
      }
      chapterCard(d2, t, 2, 'Choosing the mesh size', 'Gradients · singularities · convergence', { t0: 0, hold: 2.2 });
    },
  };
}
