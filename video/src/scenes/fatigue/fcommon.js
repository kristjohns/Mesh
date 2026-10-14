// Shared pieces for the fatigue video: the C203 chain strip, step cards, S-N helpers, heatmaps.
import { PAL, seg, env, ease, clamp, lerp, rgba, mixHex } from '../../engine/util.js';

export const STEPS = [
  { n: 1, short: 'Sea states', col: PAL.cyan },
  { n: 2, short: 'Stress', col: PAL.amber },
  { n: 3, short: 'Count cycles', col: PAL.green },
  { n: 4, short: 'S-N curve', col: PAL.violet },
  { n: 5, short: 'Damage', col: PAL.orange },
  { n: 6, short: 'Design check', col: PAL.red },
];

// compact progress strip at the top of the screen; cur = 1..6 (0 = none highlighted)
export function chainBar(d2, cur, o = {}) {
  const a = o.alpha ?? 1;
  if (a <= 0.001) return;
  const y = o.y ?? 52;
  const gap = 14;
  const size = 19;
  const ws = STEPS.map((s) => d2.measure(`${s.n}  ${s.short}`, size, 650, 0.5) + 34);
  const total = ws.reduce((p, q) => p + q, 0) + gap * (STEPS.length - 1);
  let x = (o.x ?? 960) - total / 2;
  STEPS.forEach((s, i) => {
    const w = ws[i];
    const on = s.n === cur;
    const done = s.n < cur;
    const h = 36;
    d2.panel(x, y - h / 2, w, h, {
      r: h / 2, alpha: a * (on ? 1 : 0.85), shadow: false,
      fill: on ? rgba(s.col, 0.28) : 'rgba(8,20,34,0.82)',
      border: on ? rgba(s.col, 0.95) : done ? rgba(s.col, 0.45) : 'rgba(120,170,210,0.22)', borderWidth: on ? 2 : 1.2,
    });
    d2.text(String(s.n), x + 17, y + 7, { size, weight: 800, color: on || done ? s.col : PAL.ink3, alpha: a });
    d2.text(s.short, x + 34, y + 7, { size, weight: on ? 700 : 550, color: on ? PAL.ink : done ? PAL.ink2 : PAL.ink3, alpha: a, ls: 0.3 });
    if (i < STEPS.length - 1) d2.line(x + w + 2, y, x + w + gap - 2, y, { color: 'rgba(140,180,210,0.35)', width: 1.5, alpha: a });
    x += w + gap;
  });
}

// "STEP n" title card at the start of a step scene
export function stepCard(d2, t, step, title, sub, o = {}) {
  const t0 = o.t0 ?? 0, hold = o.hold ?? 2.3;
  const a = env(t, t0, t0 + hold, 0.35, 0.6);
  if (a <= 0.001) return 0;
  const s = STEPS[step - 1];
  d2.fadeRect(a * 0.9, '#040b14');
  const p = seg(t, t0, 1.0, ease.outExpo);
  const cx = 960, cy = 500;
  d2.text(`STEP ${step}`, cx, cy - 62, { size: 30, weight: 800, color: s.col, align: 'center', alpha: a * p, ls: 10 });
  d2.line(cx - 220 * p, cy - 30, cx + 220 * p, cy - 30, { color: s.col, width: 2, alpha: a });
  d2.text(title, cx, cy + 46, { size: 68, weight: 800, align: 'center', alpha: a * seg(t, t0 + 0.15, 0.6), ls: -0.5 });
  if (sub) d2.text(sub, cx, cy + 100, { size: 28, weight: 500, color: PAL.ink2, align: 'center', alpha: a * seg(t, t0 + 0.35, 0.6) });
  return a;
}

// heading at the top-left of a content area
export function heading(d2, str, x, y, a, o = {}) {
  if (a <= 0.001) return;
  d2.text(str, x, y, { size: o.size ?? 40, weight: 800, alpha: a, color: o.color ?? PAL.ink, ls: -0.3 });
  if (o.sub) d2.text(o.sub, x, y + (o.size ?? 40) * 0.95, { size: (o.size ?? 40) * 0.55, weight: 500, alpha: a, color: PAL.ink2 });
}

// thousands separator
export const fmtInt = (v) => Math.round(v).toLocaleString('en-US');

// logarithmic tick labels: 1e4 -> 10⁴
const SUP = { 0: '⁰', 1: '¹', 2: '²', 3: '³', 4: '⁴', 5: '⁵', 6: '⁶', 7: '⁷', 8: '⁸', 9: '⁹', '-': '⁻' };
export const pow10 = (v) => '10' + String(Math.round(Math.log10(v))).split('').map((c) => SUP[c]).join('');

// S-N curve points [N, S] -> clipped polyline within a Plot
export function snPath(P, pts, o = {}) {
  const p = clamp(o.progress ?? 1);
  P.clipBegin();
  P.curve(pts, { width: o.width ?? 3.5, color: o.color ?? PAL.cyan, alpha: o.alpha ?? 1, progress: p, dash: o.dash, glow: o.glow });
  P.clipEnd();
}

// C203 S-N relation for one curve: (m1, loga1, m2, loga2) ; returns N for a stress range S
export function snN(c, S) {
  const [m1, la1, m2, la2] = c;
  if (m2 == null) return Math.pow(10, la1 - m1 * Math.log10(S));
  const logS1 = (la2 - la1) / (m2 - m1);
  return Math.log10(S) >= logS1 ? Math.pow(10, la1 - m1 * Math.log10(S)) : Math.pow(10, la2 - m2 * Math.log10(S));
}
export function snS(c, N) {
  const [m1, la1, m2, la2] = c;
  if (m2 == null) return Math.pow(10, (la1 - Math.log10(N)) / m1);
  const logS1 = (la2 - la1) / (m2 - m1);
  const N1 = Math.pow(10, la1 - m1 * logS1);
  return N <= N1 ? Math.pow(10, (la1 - Math.log10(N)) / m1) : Math.pow(10, (la2 - Math.log10(N)) / m2);
}
export function snCurvePts(c, N0 = 1e3, N1 = 1e9, n = 80) {
  const out = [];
  for (let i = 0; i <= n; i++) {
    const N = Math.pow(10, Math.log10(N0) + (Math.log10(N1) - Math.log10(N0)) * i / n);
    out.push([N, snS(c, N)]);
  }
  return out;
}

// heat colour for probabilities / damage shares (dark navy -> cyan -> amber -> red)
export function heat(v) {
  v = clamp(v);
  if (v < 0.33) return mixHex('#123049', '#2e8fb8', v / 0.33);
  if (v < 0.66) return mixHex('#2e8fb8', '#ffb703', (v - 0.33) / 0.33);
  return mixHex('#ffb703', '#ef476f', (v - 0.66) / 0.34);
}

// small wave icon / glyphs used on cards
export function glyph(d2, kind, x, y, s, col, a = 1) {
  const g = d2.g;
  if (kind === 'waves') {
    for (let k = 0; k < 3; k++) {
      const pts = [];
      for (let i = 0; i <= 30; i++) pts.push([x - s + (2 * s * i) / 30, y - s * 0.45 + k * s * 0.45 + Math.sin(i / 30 * Math.PI * 3 + k) * s * 0.13]);
      d2.path(pts, { color: col, width: 3, alpha: a * (1 - k * 0.25) });
    }
  } else if (kind === 'stress') {
    d2.line(x, y - s, x, y + s, { color: col, width: 6, alpha: a });
    d2.circle(x, y + s * 0.15, s * 0.32, { stroke: col, width: 3, alpha: a });
    d2.arrow(x - s * 0.95, y - s * 0.7, x - s * 0.2, y - s * 0.7, { color: col, width: 3, head: 10, alpha: a });
  } else if (kind === 'rainflow') {
    const pts = [[-1, 0.2], [-0.6, -0.8], [-0.3, 0.5], [0.0, -0.1], [0.25, 0.7], [0.6, -0.6], [1, 0.4]];
    d2.path(pts.map(([u, v]) => [x + u * s, y + v * s]), { color: col, width: 3, alpha: a });
    pts.forEach(([u, v]) => d2.circle(x + u * s, y + v * s, 3.5, { fill: col, alpha: a }));
  } else if (kind === 'sn') {
    d2.line(x - s, y - s, x - s, y + s, { color: PAL.ink3, width: 2, alpha: a });
    d2.line(x - s, y + s, x + s, y + s, { color: PAL.ink3, width: 2, alpha: a });
    d2.path([[x - s * 0.9, y - s * 0.8], [x + s * 0.2, y + s * 0.25], [x + s * 0.95, y + s * 0.45]], { color: col, width: 3.5, alpha: a });
  } else if (kind === 'sum') {
    d2.text('Σ', x - s * 0.15, y + s * 0.42, { size: s * 1.5, weight: 800, color: col, align: 'center', alpha: a });
    d2.text('n/N', x + s * 0.55, y + s * 0.3, { size: s * 0.55, weight: 700, color: col, align: 'center', alpha: a });
  } else if (kind === 'check') {
    d2.poly([[x, y - s], [x + s * 0.85, y - s * 0.6], [x + s * 0.75, y + s * 0.4], [x, y + s], [x - s * 0.75, y + s * 0.4], [x - s * 0.85, y - s * 0.6]], { stroke: col, width: 3, fill: rgba(col, 0.12), alpha: a });
    d2.path([[x - s * 0.35, y], [x - s * 0.05, y + s * 0.32], [x + s * 0.42, y - s * 0.3]], { color: col, width: 4, alpha: a });
  }
}

// value-to-x helper for a horizontal timeline in data space
export function lerpArr(arr, f) {
  const n = arr.length;
  const x = clamp(f) * (n - 1);
  const i = Math.floor(x), u = x - i;
  return i >= n - 1 ? arr[n - 1] : lerp(arr[i], arr[i + 1], u);
}
