// Small math / timing helpers shared by every scene.
export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const invlerp = (a, b, x) => clamp((x - a) / (b - a));
export const smoothstep = (a, b, x) => { const t = invlerp(a, b, x); return t * t * (3 - 2 * t); };

export const ease = {
  linear: (t) => t,
  in: (t) => t * t * t,
  out: (t) => 1 - Math.pow(1 - t, 3),
  inOut: (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2),
  inOutQuad: (t) => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2),
  inOutSine: (t) => -(Math.cos(Math.PI * t) - 1) / 2,
  outExpo: (t) => (t === 1 ? 1 : 1 - Math.pow(2, -10 * t)),
  inOutExpo: (t) => (t === 0 ? 0 : t === 1 ? 1 : t < 0.5 ? Math.pow(2, 20 * t - 10) / 2 : (2 - Math.pow(2, -20 * t + 10)) / 2),
  outBack: (t) => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); },
  outQuint: (t) => 1 - Math.pow(1 - t, 5),
};

// progress of a segment starting at t0 lasting d, eased
export function seg(t, t0, d, e = ease.inOut) {
  if (d <= 0) return t >= t0 ? 1 : 0;
  return e(clamp((t - t0) / d));
}

// alpha envelope: fades in at tin over din, fades out at tout over dout
export function env(t, tin, tout = Infinity, din = 0.5, dout = 0.5) {
  const a = seg(t, tin, din, ease.inOutSine);
  const b = tout === Infinity ? 1 : 1 - seg(t, tout, dout, ease.inOutSine);
  return Math.min(a, b);
}

// seeded random numbers (mulberry32)
export function rng(seed = 1) {
  let a = seed >>> 0;
  return () => {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function hexToRgb(h) {
  const s = h.replace('#', '');
  return [parseInt(s.slice(0, 2), 16), parseInt(s.slice(2, 4), 16), parseInt(s.slice(4, 6), 16)];
}
export function rgba(h, a = 1) {
  const [r, g, b] = hexToRgb(h);
  return `rgba(${r},${g},${b},${a})`;
}
export function mixHex(h1, h2, t) {
  const a = hexToRgb(h1), b = hexToRgb(h2);
  const c = a.map((v, i) => Math.round(lerp(v, b[i], t)));
  return '#' + c.map((v) => v.toString(16).padStart(2, '0')).join('');
}

// Turbo colormap (Google), polynomial approximation, t in [0,1] -> [r,g,b] in [0,1]
export function turbo(t) {
  t = clamp(t);
  const r = 0.13572138 + t * (4.6153926 + t * (-42.66032258 + t * (132.13108234 + t * (-152.94239396 + t * 59.28637943))));
  const g = 0.09140261 + t * (2.19418839 + t * (4.84296658 + t * (-14.18503333 + t * (4.27729857 + t * 2.82956604))));
  const b = 0.1066733 + t * (12.64194608 + t * (-60.58204836 + t * (110.36276771 + t * (-89.90310912 + t * 27.34824973))));
  return [clamp(r), clamp(g), clamp(b)];
}
export function turboCss(t, a = 1) {
  const [r, g, b] = turbo(t);
  return `rgba(${Math.round(r * 255)},${Math.round(g * 255)},${Math.round(b * 255)},${a})`;
}

// keyframe interpolation of numbers/arrays with per-segment easing
export function keys(t, kf, e = ease.inOut) {
  if (t <= kf[0][0]) return kf[0][1];
  for (let i = 0; i < kf.length - 1; i++) {
    const [t0, v0] = kf[i];
    const [t1, v1] = kf[i + 1];
    if (t <= t1) {
      const u = e(clamp((t - t0) / (t1 - t0)));
      if (Array.isArray(v0)) return v0.map((x, j) => lerp(x, v1[j], u));
      return lerp(v0, v1, u);
    }
  }
  return kf[kf.length - 1][1];
}

export const PAL = {
  bg0: '#050d16', bg1: '#0a1826', bg2: '#10243a',
  ink: '#eaf2f8', ink2: '#a7bccd', ink3: '#62809a',
  cyan: '#4cc9f0', teal: '#2ec4b6', amber: '#ffb703', orange: '#fb8500',
  red: '#ef476f', green: '#3ddc97', violet: '#a78bfa', yellow: '#f2b705', steel: '#b9c3cc',
  blue: '#4895ef', pink: '#f72585',
};
