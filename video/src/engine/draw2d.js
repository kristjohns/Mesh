// 2D overlay drawing helpers (Canvas 2D at 1920x1080).
import { clamp, lerp, ease, rgba, PAL } from './util.js';

const FONT = 'Inter';

export class D2 {
  constructor(canvas) {
    this.c = canvas;
    this.g = canvas.getContext('2d');
    this.W = canvas.width;
    this.H = canvas.height;
  }

  clear() {
    this.g.setTransform(1, 0, 0, 1, 0, 0);
    this.g.globalAlpha = 1;
    this.g.clearRect(0, 0, this.W, this.H);
  }

  font(size, weight = 500, family = FONT, style = '') {
    return `${style} ${weight} ${size}px ${family}`.trim();
  }

  measure(str, size, weight = 500, ls = 0) {
    const g = this.g;
    g.font = this.font(size, weight);
    g.letterSpacing = `${ls}px`;
    const w = g.measureText(str).width;
    g.letterSpacing = '0px';
    return w;
  }

  // ------------------------------------------------------------------ text
  text(str, x, y, o = {}) {
    const g = this.g;
    const a = o.alpha ?? 1;
    if (a <= 0.001) return 0;
    g.save();
    g.globalAlpha = a;
    g.font = this.font(o.size ?? 32, o.weight ?? 500, o.family ?? FONT, o.style ?? '');
    g.letterSpacing = `${o.ls ?? 0}px`;
    g.textAlign = o.align ?? 'left';
    g.textBaseline = o.baseline ?? 'alphabetic';
    if (o.shadow) {
      g.shadowColor = o.shadow === true ? 'rgba(0,0,0,0.6)' : o.shadow;
      g.shadowBlur = o.shadowBlur ?? 12;
    }
    if (o.glow) {
      g.shadowColor = o.glow;
      g.shadowBlur = o.glowBlur ?? 18;
    }
    if (o.stroke) {
      g.strokeStyle = o.stroke;
      g.lineWidth = o.strokeWidth ?? 2;
      g.strokeText(str, x, y);
    }
    if (o.color !== null) {
      g.fillStyle = o.color ?? PAL.ink;
      g.fillText(str, x, y);
    }
    const w = g.measureText(str).width;
    g.restore();
    return w;
  }

  wrap(str, maxW, size, weight = 500) {
    const g = this.g;
    g.font = this.font(size, weight);
    const words = str.split(' ');
    const lines = [];
    let cur = '';
    for (const w of words) {
      const test = cur ? cur + ' ' + w : w;
      if (g.measureText(test).width > maxW && cur) {
        lines.push(cur);
        cur = w;
      } else cur = test;
    }
    if (cur) lines.push(cur);
    return lines;
  }

  // word-by-word reveal. p in [0,1]. Returns height used.
  reveal(str, x, y, p, o = {}) {
    const size = o.size ?? 32;
    const weight = o.weight ?? 500;
    const lh = o.lh ?? size * 1.32;
    const lines = o.maxW ? this.wrap(str, o.maxW, size, weight) : [str];
    const words = [];
    lines.forEach((ln, li) => {
      let cx = 0;
      const lw = this.measure(ln, size, weight, o.ls ?? 0);
      const ox = o.align === 'center' ? -lw / 2 : o.align === 'right' ? -lw : 0;
      for (const w of ln.split(' ')) {
        words.push({ w, x: x + ox + cx, y: y + li * lh });
        cx += this.measure(w + ' ', size, weight, o.ls ?? 0);
      }
    });
    const n = words.length;
    const spread = o.spread ?? 0.6;
    words.forEach((wd, i) => {
      const s = n > 1 ? (i / (n - 1)) * spread : 0;
      const q = ease.out(clamp((p - s) / (1 - spread + 1e-6)));
      if (q <= 0) return;
      this.text(wd.w, wd.x, wd.y + (1 - q) * (o.rise ?? 14), { ...o, align: 'left', alpha: (o.alpha ?? 1) * q });
    });
    return lines.length * lh;
  }

  // ------------------------------------------------------------------ shapes
  roundRectPath(x, y, w, h, r) {
    const g = this.g;
    r = Math.min(r, w / 2, h / 2);
    g.beginPath();
    g.moveTo(x + r, y);
    g.arcTo(x + w, y, x + w, y + h, r);
    g.arcTo(x + w, y + h, x, y + h, r);
    g.arcTo(x, y + h, x, y, r);
    g.arcTo(x, y, x + w, y, r);
    g.closePath();
  }

  panel(x, y, w, h, o = {}) {
    const g = this.g;
    const a = o.alpha ?? 1;
    if (a <= 0.001) return;
    g.save();
    g.globalAlpha = a;
    this.roundRectPath(x, y, w, h, o.r ?? 18);
    if (o.shadow !== false) {
      g.shadowColor = 'rgba(0,0,0,0.45)';
      g.shadowBlur = 30;
      g.shadowOffsetY = 8;
    }
    const grad = g.createLinearGradient(x, y, x, y + h);
    grad.addColorStop(0, o.fill0 ?? 'rgba(20,40,62,0.88)');
    grad.addColorStop(1, o.fill1 ?? 'rgba(10,24,40,0.88)');
    g.fillStyle = o.fill ?? grad;
    g.fill();
    g.shadowColor = 'transparent';
    g.lineWidth = o.borderWidth ?? 1.5;
    g.strokeStyle = o.border ?? 'rgba(120,180,220,0.28)';
    g.stroke();
    if (o.accent) {
      g.beginPath();
      g.moveTo(x + 1, y + (o.r ?? 18));
      g.lineTo(x + 1, y + h - (o.r ?? 18));
      g.lineWidth = 4;
      g.strokeStyle = o.accent;
      g.stroke();
    }
    g.restore();
  }

  rect(x, y, w, h, o = {}) {
    const g = this.g;
    g.save();
    g.globalAlpha = o.alpha ?? 1;
    if (o.fill) { g.fillStyle = o.fill; g.fillRect(x, y, w, h); }
    if (o.stroke) { g.strokeStyle = o.stroke; g.lineWidth = o.width ?? 1; g.strokeRect(x, y, w, h); }
    g.restore();
  }

  circle(x, y, r, o = {}) {
    const g = this.g;
    if ((o.alpha ?? 1) <= 0.001 || r <= 0) return;
    g.save();
    g.globalAlpha = o.alpha ?? 1;
    g.beginPath();
    g.arc(x, y, r, 0, Math.PI * 2);
    if (o.glow) { g.shadowColor = o.glow; g.shadowBlur = o.glowBlur ?? 16; }
    if (o.fill) { g.fillStyle = o.fill; g.fill(); }
    if (o.stroke) { g.shadowBlur = 0; g.strokeStyle = o.stroke; g.lineWidth = o.width ?? 2; g.stroke(); }
    g.restore();
  }

  line(x1, y1, x2, y2, o = {}) {
    this.path([[x1, y1], [x2, y2]], o);
  }

  // polyline with partial-length progress
  path(pts, o = {}) {
    const g = this.g;
    const a = o.alpha ?? 1;
    if (a <= 0.001 || pts.length < 2) return;
    let p = clamp(o.progress ?? 1);
    if (p <= 0) return;
    let total = 0;
    const segs = [];
    for (let i = 0; i < pts.length - 1; i++) {
      const l = Math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]);
      segs.push(l);
      total += l;
    }
    const target = total * p;
    g.save();
    g.globalAlpha = a;
    g.beginPath();
    g.moveTo(pts[0][0], pts[0][1]);
    let acc = 0;
    for (let i = 0; i < segs.length; i++) {
      if (acc + segs[i] <= target + 1e-9) {
        g.lineTo(pts[i + 1][0], pts[i + 1][1]);
        acc += segs[i];
      } else {
        const u = (target - acc) / segs[i];
        g.lineTo(lerp(pts[i][0], pts[i + 1][0], u), lerp(pts[i][1], pts[i + 1][1], u));
        break;
      }
    }
    if (o.closed && p >= 1) g.closePath();
    if (o.fill && p >= 1) { g.fillStyle = o.fill; g.fill(); }
    g.lineWidth = o.width ?? 2;
    g.strokeStyle = o.color ?? PAL.ink;
    g.lineCap = o.cap ?? 'round';
    g.lineJoin = o.join ?? 'round';
    if (o.dash) g.setLineDash(o.dash);
    if (o.dashOffset) g.lineDashOffset = o.dashOffset;
    if (o.glow) { g.shadowColor = o.glow; g.shadowBlur = o.glowBlur ?? 14; }
    if (o.color !== null) g.stroke();
    g.restore();
  }

  poly(pts, o = {}) {
    const g = this.g;
    if ((o.alpha ?? 1) <= 0.001) return;
    g.save();
    g.globalAlpha = o.alpha ?? 1;
    g.beginPath();
    g.moveTo(pts[0][0], pts[0][1]);
    for (let i = 1; i < pts.length; i++) g.lineTo(pts[i][0], pts[i][1]);
    g.closePath();
    if (o.fill) { g.fillStyle = o.fill; g.fill(); }
    if (o.stroke) { g.lineJoin = 'round'; g.strokeStyle = o.stroke; g.lineWidth = o.width ?? 1; g.stroke(); }
    g.restore();
  }

  arrow(x1, y1, x2, y2, o = {}) {
    const p = clamp(o.progress ?? 1);
    if (p <= 0 || (o.alpha ?? 1) <= 0.001) return;
    const xe = lerp(x1, x2, p), ye = lerp(y1, y2, p);
    const ang = Math.atan2(ye - y1, xe - x1);
    const hl = o.head ?? 16;
    const w = o.width ?? 3;
    const len = Math.hypot(xe - x1, ye - y1);
    const hb = Math.min(hl, len * 0.6);
    this.line(x1, y1, xe - Math.cos(ang) * hb * 0.7, ye - Math.sin(ang) * hb * 0.7, { ...o, progress: 1, cap: 'butt' });
    const g = this.g;
    g.save();
    g.globalAlpha = o.alpha ?? 1;
    g.fillStyle = o.color ?? PAL.ink;
    if (o.glow) { g.shadowColor = o.glow; g.shadowBlur = o.glowBlur ?? 14; }
    g.beginPath();
    g.moveTo(xe, ye);
    g.lineTo(xe - Math.cos(ang - 0.42) * hb, ye - Math.sin(ang - 0.42) * hb);
    g.lineTo(xe - Math.cos(ang + 0.42) * hb, ye - Math.sin(ang + 0.42) * hb);
    g.closePath();
    g.fill();
    g.restore();
    if (o.double) this.arrow(x2, y2, x1, y1, { ...o, double: false });
  }

  // curved moment arrow (arc) centred at x,y
  momentArrow(x, y, r, a0, a1, o = {}) {
    const p = clamp(o.progress ?? 1);
    const n = 40;
    const pts = [];
    const ae = lerp(a0, a1, p);
    for (let i = 0; i <= n; i++) {
      const a = lerp(a0, ae, i / n);
      pts.push([x + r * Math.cos(a), y + r * Math.sin(a)]);
    }
    if (pts.length < 2 || p <= 0) return;
    this.path(pts.slice(0, -2), o);
    const pa = pts[pts.length - 3];
    const pb = pts[pts.length - 1];
    this.arrow(pa[0], pa[1], pb[0], pb[1], { ...o, progress: 1, head: o.head ?? 16 });
  }

  // zig-zag spring between two points
  spring(x1, y1, x2, y2, o = {}) {
    const coils = o.coils ?? 6;
    const amp = o.amp ?? 10;
    const lead = o.lead ?? 0.18;
    const L = Math.hypot(x2 - x1, y2 - y1);
    if (L < 1) return;
    const ux = (x2 - x1) / L, uy = (y2 - y1) / L;
    const nx = -uy, ny = ux;
    const pts = [[x1, y1]];
    const l0 = L * lead, l1 = L * (1 - lead);
    pts.push([x1 + ux * l0, y1 + uy * l0]);
    const nz = coils * 2;
    for (let i = 1; i < nz; i++) {
      const s = l0 + ((l1 - l0) * i) / nz;
      const side = i % 2 ? 1 : -1;
      pts.push([x1 + ux * s + nx * amp * side, y1 + uy * s + ny * amp * side]);
    }
    pts.push([x1 + ux * l1, y1 + uy * l1]);
    pts.push([x2, y2]);
    this.path(pts, { join: 'miter', ...o });
  }

  // ground hatch (fixed support) along a line centred at x,y with given width; angle: normal pointing into ground
  ground(x, y, w, o = {}) {
    const g = this.g;
    const ang = o.angle ?? Math.PI / 2; // default ground below
    const tx = Math.cos(ang + Math.PI / 2), ty = Math.sin(ang + Math.PI / 2);
    const nx = Math.cos(ang), ny = Math.sin(ang);
    const col = o.color ?? PAL.ink2;
    this.line(x - tx * w / 2, y - ty * w / 2, x + tx * w / 2, y + ty * w / 2, { color: col, width: o.width ?? 3, alpha: o.alpha });
    const n = Math.max(3, Math.round(w / 12));
    for (let i = 0; i <= n; i++) {
      const s = -w / 2 + (w * i) / n;
      const px = x + tx * s, py = y + ty * s;
      this.line(px, py, px + nx * 10 - tx * 8, py + ny * 10 - ty * 8, { color: col, width: 1.5, alpha: (o.alpha ?? 1) * 0.8 });
    }
  }

  check(x, y, s, o = {}) {
    const p = clamp(o.progress ?? 1);
    this.circle(x, y, s, { fill: rgba(o.color ?? PAL.green, 0.16), stroke: o.color ?? PAL.green, width: 2.5, alpha: (o.alpha ?? 1) * Math.min(1, p * 3) });
    this.path([[x - s * 0.45, y + s * 0.02], [x - s * 0.1, y + s * 0.36], [x + s * 0.5, y - s * 0.34]],
      { color: o.color ?? PAL.green, width: s * 0.2, progress: clamp(p * 1.4 - 0.2), alpha: o.alpha });
  }

  cross(x, y, s, o = {}) {
    const p = clamp(o.progress ?? 1);
    const c = o.color ?? PAL.red;
    this.circle(x, y, s, { fill: rgba(c, 0.16), stroke: c, width: 2.5, alpha: (o.alpha ?? 1) * Math.min(1, p * 3) });
    const q = s * 0.38;
    this.line(x - q, y - q, x + q, y + q, { color: c, width: s * 0.2, progress: clamp(p * 2 - 0.3), alpha: o.alpha });
    this.line(x + q, y - q, x - q, y + q, { color: c, width: s * 0.2, progress: clamp(p * 2 - 1), alpha: o.alpha });
  }

  warn(x, y, s, o = {}) {
    const c = o.color ?? PAL.amber;
    const a = o.alpha ?? 1;
    this.poly([[x, y - s], [x + s * 1.1, y + s * 0.85], [x - s * 1.1, y + s * 0.85]], { fill: rgba(c, 0.18), stroke: c, width: 2.5, alpha: a });
    this.text('!', x, y + s * 0.62, { size: s * 1.2, weight: 800, color: c, align: 'center', alpha: a });
  }

  // dimension line with end ticks and centred label
  dim(x1, y1, x2, y2, label, o = {}) {
    const c = o.color ?? PAL.ink2;
    const a = o.alpha ?? 1;
    this.arrow(x1, y1, x2, y2, { color: c, width: 1.5, head: 10, alpha: a, double: true });
    if (label) {
      const mx = (x1 + x2) / 2 + (o.dx ?? 0), my = (y1 + y2) / 2 + (o.dy ?? -10);
      this.text(label, mx, my, { size: o.size ?? 22, weight: 600, color: o.labelColor ?? c, align: 'center', alpha: a });
    }
  }

  // label with leader line from anchor (ax,ay) to text at (lx,ly)
  callout(ax, ay, lx, ly, title, sub, o = {}) {
    const a = o.alpha ?? 1;
    if (a <= 0.001) return;
    const p = clamp(o.progress ?? 1);
    const c = o.color ?? PAL.cyan;
    const elbow = o.elbow ?? [lx, ay];
    this.circle(ax, ay, 5, { fill: c, alpha: a * Math.min(1, p * 4), glow: c });
    this.circle(ax, ay, 11, { stroke: c, width: 1.5, alpha: a * 0.6 * Math.min(1, p * 4) });
    const pts = o.straight ? [[ax, ay], [lx, ly]] : [[ax, ay], elbow, [lx, ly]];
    this.path(pts, { color: c, width: 1.6, alpha: a * 0.9, progress: clamp(p * 1.6) });
    const tp = clamp(p * 1.6 - 0.6);
    const align = o.align ?? (lx >= ax ? 'left' : 'right');
    const off = align === 'left' ? 12 : -12;
    if (o.backing !== false && tp > 0) {
      const sz = o.size ?? 30;
      const tw = Math.max(this.measure(title, sz, 650), sub ? this.measure(sub, sz * 0.68, 500) : 0) + 28;
      const bx = align === 'left' ? lx + off - 14 : lx + off - tw + 14;
      const by = ly - (sub ? 6 : -8) - sz * 0.95;
      const bh = sub ? sz * 2.05 : sz * 1.35;
      this.panel(bx, by, tw, bh, { r: 10, alpha: a * tp * 0.85, fill: 'rgba(4,14,24,0.62)', border: 'rgba(120,180,220,0.18)', shadow: false });
    }
    this.text(title, lx + off, ly - (sub ? 6 : -8), { size: o.size ?? 30, weight: 650, color: o.titleColor ?? PAL.ink, align, alpha: a * tp, shadow: true });
    if (sub) this.text(sub, lx + off, ly + (o.size ?? 30) * 0.95, { size: (o.size ?? 30) * 0.68, weight: 500, color: PAL.ink2, align, alpha: a * tp, shadow: true });
  }

  // simple "pill" tag
  tag(str, x, y, o = {}) {
    const size = o.size ?? 22;
    const w = this.measure(str, size, o.weight ?? 650, o.ls ?? 1) + size * 1.2;
    const h = size * 1.7;
    const xx = o.align === 'center' ? x - w / 2 : o.align === 'right' ? x - w : x;
    this.panel(xx, y - h / 2, w, h, { r: h / 2, alpha: o.alpha, fill: o.fill ?? rgba(o.color ?? PAL.cyan, 0.16), border: rgba(o.color ?? PAL.cyan, 0.7), shadow: false });
    this.text(str, xx + w / 2, y + size * 0.36, { size, weight: o.weight ?? 650, color: o.textColor ?? (o.color ?? PAL.cyan), align: 'center', alpha: o.alpha, ls: o.ls ?? 1 });
    return w;
  }

  // full-screen background gradient with subtle grid and vignette
  background(o = {}) {
    const g = this.g;
    const a = o.alpha ?? 1;
    g.save();
    g.globalAlpha = a;
    const grad = g.createRadialGradient(this.W * 0.5, this.H * 0.42, 100, this.W * 0.5, this.H * 0.5, this.W * 0.75);
    grad.addColorStop(0, o.c0 ?? '#0f2236');
    grad.addColorStop(1, o.c1 ?? '#040a12');
    g.fillStyle = grad;
    g.fillRect(0, 0, this.W, this.H);
    if (o.grid !== false) {
      const step = o.step ?? 48;
      const off = o.offset ?? 0;
      g.strokeStyle = 'rgba(90,150,200,0.055)';
      g.lineWidth = 1;
      g.beginPath();
      for (let x = (off % step); x < this.W; x += step) { g.moveTo(x + 0.5, 0); g.lineTo(x + 0.5, this.H); }
      for (let y = (off % step); y < this.H; y += step) { g.moveTo(0, y + 0.5); g.lineTo(this.W, y + 0.5); }
      g.stroke();
      g.strokeStyle = 'rgba(90,150,200,0.07)';
      g.beginPath();
      for (let x = (off % (step * 4)); x < this.W; x += step * 4) { g.moveTo(x + 0.5, 0); g.lineTo(x + 0.5, this.H); }
      for (let y = (off % (step * 4)); y < this.H; y += step * 4) { g.moveTo(0, y + 0.5); g.lineTo(this.W, y + 0.5); }
      g.stroke();
    }
    g.restore();
  }

  vignette(strength = 0.55) {
    const g = this.g;
    const grad = g.createRadialGradient(this.W / 2, this.H / 2, this.H * 0.35, this.W / 2, this.H / 2, this.W * 0.72);
    grad.addColorStop(0, 'rgba(0,0,0,0)');
    grad.addColorStop(1, `rgba(0,0,0,${strength})`);
    g.save();
    g.fillStyle = grad;
    g.fillRect(0, 0, this.W, this.H);
    g.restore();
  }

  fadeRect(alpha, color = '#050d16') {
    if (alpha <= 0.001) return;
    const g = this.g;
    g.save();
    g.globalAlpha = clamp(alpha);
    g.fillStyle = color;
    g.fillRect(0, 0, this.W, this.H);
    g.restore();
  }
}

// --------------------------------------------------------------------- plots
export class Plot {
  constructor(d2, o) {
    this.d = d2;
    Object.assign(this, { x: 0, y: 0, w: 600, h: 400, xr: [0, 1], yr: [0, 1], xlog: false, ylog: false }, o);
  }
  X(v) {
    const [a, b] = this.xr;
    const t = this.xlog ? (Math.log10(v) - Math.log10(a)) / (Math.log10(b) - Math.log10(a)) : (v - a) / (b - a);
    return this.x + t * this.w;
  }
  Y(v) {
    const [a, b] = this.yr;
    const t = this.ylog ? (Math.log10(v) - Math.log10(a)) / (Math.log10(b) - Math.log10(a)) : (v - a) / (b - a);
    return this.y + this.h - t * this.h;
  }
  axes(o = {}) {
    const d = this.d;
    const a = o.alpha ?? 1;
    const p = clamp(o.progress ?? 1);
    if (a <= 0.001) return;
    const c = 'rgba(167,188,205,0.85)';
    // grid
    const gx = o.xticks ?? [];
    const gy = o.yticks ?? [];
    for (const v of gx) d.line(this.X(v), this.y + this.h, this.X(v), this.y + this.h - this.h * p, { color: 'rgba(120,160,200,0.13)', width: 1, alpha: a });
    for (const v of gy) d.line(this.x, this.Y(v), this.x + this.w * p, this.Y(v), { color: 'rgba(120,160,200,0.13)', width: 1, alpha: a });
    d.line(this.x, this.y + this.h, this.x + this.w * p, this.y + this.h, { color: c, width: 2, alpha: a });
    d.line(this.x, this.y + this.h, this.x, this.y + this.h - this.h * p, { color: c, width: 2, alpha: a });
    const fs = o.fs ?? 20;
    const fmtx = o.fmtx ?? ((v) => String(v));
    const fmty = o.fmty ?? ((v) => String(v));
    for (const v of gx) d.text(fmtx(v), this.X(v), this.y + this.h + fs * 1.35, { size: fs, color: PAL.ink2, align: 'center', alpha: a * p });
    for (const v of gy) d.text(fmty(v), this.x - 12, this.Y(v) + fs * 0.35, { size: fs, color: PAL.ink2, align: 'right', alpha: a * p });
    if (o.xlabel) d.text(o.xlabel, this.x + this.w / 2, this.y + this.h + fs * 2.9, { size: fs * 1.05, weight: 600, color: PAL.ink2, align: 'center', alpha: a * p });
    if (o.ylabel) {
      const g = d.g;
      g.save();
      g.translate(this.x - (o.ylabelOff ?? 70), this.y + this.h / 2);
      g.rotate(-Math.PI / 2);
      d.text(o.ylabel, 0, 0, { size: fs * 1.05, weight: 600, color: PAL.ink2, align: 'center', alpha: a * p });
      g.restore();
    }
    if (o.title) d.text(o.title, this.x, this.y - 22, { size: fs * 1.25, weight: 650, color: PAL.ink, alpha: a * p });
  }
  curve(pts, o = {}) {
    const sp = pts.map(([u, v]) => [this.X(u), this.Y(v)]);
    this.d.path(sp, { width: 3.5, ...o });
    return sp;
  }
  points(pts, o = {}) {
    const p = clamp(o.progress ?? 1);
    const n = pts.length;
    pts.forEach(([u, v], i) => {
      const q = clamp(p * n - i);
      if (q <= 0) return;
      this.d.circle(this.X(u), this.Y(v), (o.r ?? 7) * ease.outBack(q), { fill: o.fill ?? o.color ?? PAL.cyan, stroke: o.stroke ?? '#06101a', width: 2, alpha: o.alpha ?? 1 });
    });
  }
  clipBegin() {
    const g = this.d.g;
    g.save();
    g.beginPath();
    g.rect(this.x, this.y - 2, this.w + 2, this.h + 4);
    g.clip();
  }
  clipEnd() { this.d.g.restore(); }
}
