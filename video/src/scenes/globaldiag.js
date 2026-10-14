// 2D side-view drawing of the global beam / spring model of the well.
import { PAL, clamp, lerp, rgba, mixHex, seg, ease } from '../engine/util.js';

export const Z = { tip: -60, condTop: 0.8, lpTop: 2.6, hpBot: 1.2, wh: 3.6, load: 16.6, template: 2.0, shoulder: 2.2 };

// mobilisation colour: green -> amber -> red
export function mobColor(m) {
  m = clamp(m);
  return m < 0.6 ? mixHex(PAL.green, PAL.amber, m / 0.6) : mixHex(PAL.amber, PAL.red, (m - 0.6) / 0.4);
}

// o: { x, y0 (mudline), sy (px/m vertical), zTop, zBot, u(z) lateral disp [m], ux (px per m lateral),
//      springs: bool, mob(z) -> 0..1, nodes: [z...], alpha, p (draw progress), bop, template, soil, labels }
export function drawGlobal(d2, o) {
  const a = o.alpha ?? 1;
  if (a <= 0.001) return;
  const sy = o.sy ?? 14;
  const Y = (z) => o.y0 - z * sy * (z > 0 ? (o.syUp ?? 1) : 1);
  const u = o.u ?? (() => 0);
  const ux = o.ux ?? 0;
  const X = (z) => o.x + u(z) * ux;
  const zTop = o.zTop ?? 17, zBot = o.zBot ?? -30;
  const p = clamp(o.p ?? 1);
  // soil block
  if (o.soil !== false) {
    const g = d2.g;
    g.save();
    g.globalAlpha = a * (o.soilAlpha ?? 1);
    const grad = g.createLinearGradient(0, Y(0), 0, Y(zBot));
    grad.addColorStop(0, 'rgba(110,98,78,0.55)');
    grad.addColorStop(1, 'rgba(60,52,40,0.15)');
    g.fillStyle = grad;
    const sw = o.soilW ?? 380;
    g.fillRect(o.x - sw, Y(0), 2 * sw, Y(zBot) - Y(0));
    g.restore();
    d2.line(o.x - sw, Y(0), o.x + sw, Y(0), { color: '#b9a98a', width: 2.5, alpha: a });
    d2.text('MUDLINE', o.x + sw - 6, Y(0) - 10, { size: 17, weight: 700, color: '#b9a98a', align: 'right', ls: 2, alpha: a });
  }
  // springs (lateral), both sides
  if (o.springs) {
    const sp = o.springP ?? 1;
    const zs = o.springZ ?? [];
    const L = o.springL ?? 90;
    zs.forEach((z, i) => {
      if (z > 0 || z < zBot) return;
      const q = clamp(sp * zs.length - i * 0.6);
      if (q <= 0) return;
      const yy = Y(z);
      const xb = X(z);
      const m = o.mob ? o.mob(z) : 0;
      const c = o.mob ? mobColor(m) : (o.springColor ?? PAL.teal);
      const w = (o.springW ?? 2.2);
      for (const s of [-1, 1]) {
        const xg = o.x + s * (L + 26);
        d2.spring(xb + s * 6, yy, lerp(xb + s * 6, xg, q), yy, { color: c, width: w, coils: 4, amp: 6, alpha: a });
        if (q > 0.95) d2.line(xg, yy - 9, xg, yy + 9, { color: PAL.ink3, width: 2.5, alpha: a });
      }
    });
    if (o.groundHatch !== false && zs.length) {
      for (const s of [-1, 1]) {
        const xg = o.x + s * ((o.springL ?? 90) + 26);
        const y1 = Y(Math.min(0, zs[0])), y2 = Y(Math.max(zBot, zs[zs.length - 1]));
        d2.line(xg, y1 - 10, xg, y2 + 10, { color: PAL.ink3, width: 2, alpha: a * sp });
        for (let yy = y1; yy < y2; yy += 14) d2.line(xg, yy, xg + s * 10, yy + 9, { color: PAL.ink3, width: 1.2, alpha: a * sp * 0.8 });
      }
    }
  }
  // beam lines
  const beam = (z0, z1, col, wdt) => {
    const pts = [];
    const n = 60;
    for (let i = 0; i <= n; i++) {
      const z = lerp(z0, z1, i / n);
      pts.push([X(z), Y(z)]);
    }
    d2.path(pts, { color: col, width: wdt, alpha: a, progress: p });
  };
  beam(Math.max(zBot, Z.tip), Z.condTop, o.condColor ?? '#9fb3c4', o.condW ?? 7);
  beam(Z.condTop, Z.lpTop, o.lpColor ?? '#7fa6c7', (o.condW ?? 7) + 4);
  beam(Z.lpTop, Z.wh, o.hpColor ?? '#e3edf5', (o.condW ?? 7) - 1);
  if (zBot > Z.tip) {
    const yb = Y(zBot);
    d2.line(o.x - 14, yb + 4, o.x + 14, yb - 4, { color: PAL.ink2, width: 2, alpha: a });
    d2.line(o.x - 14, yb + 12, o.x + 14, yb + 4, { color: PAL.ink2, width: 2, alpha: a });
    if (o.breakLabel !== false) d2.text('continues to 60 m', o.x + 22, yb + 12, { size: 18, color: PAL.ink3, alpha: a });
  }
  // BOP (rigid)
  if (o.bop !== false && zTop > Z.wh) {
    const zb = Z.wh, zt = Math.min(zTop, Z.wh + (o.bopH ?? 5.5));
    const w2 = (o.bopW ?? 26);
    const pts = [[X(zb) - w2, Y(zb)], [X(zt) - w2, Y(zt)], [X(zt) + w2, Y(zt)], [X(zb) + w2, Y(zb)]];
    d2.poly(pts, { fill: rgba('#a8281f', 0.25), stroke: '#d0574d', width: 2, alpha: a * p });
    d2.text('BOP', X((zb + zt) / 2) + w2 + 10, Y((zb + zt) / 2) + 7, { size: 18, weight: 700, color: '#e07a70', alpha: a * p });
  }
  // nodes
  if (o.nodes) {
    const nn = o.nodes.length;
    o.nodes.forEach((z, i) => {
      if (z < zBot || z > zTop) return;
      const q = clamp((o.nodeP ?? 1) * nn - i * 0.5);
      if (q <= 0) return;
      d2.circle(X(z), Y(z), (o.nodeR ?? 4.5) * q, { fill: o.nodeColor ?? PAL.ink, alpha: a });
    });
  }
  // template receptacle (gap element)
  if (o.template) {
    const t = o.template;
    const yy = Y(Z.template);
    const gap = t.gapPx ?? 14;
    for (const s of [-1, 1]) {
      const xin = o.x + s * ((t.inner ?? 12) + gap);
      d2.rect(s > 0 ? xin : xin - 30, yy - 16, 30, 32, { fill: rgba(PAL.yellow, 0.35), stroke: PAL.yellow, width: 2, alpha: a * (t.alpha ?? 1) });
    }
    if (t.label) d2.text(t.label, o.x + gap + 56, yy + 7, { size: 18, weight: 650, color: PAL.yellow, alpha: a * (t.alpha ?? 1) });
  }
  return { X, Y };
}
