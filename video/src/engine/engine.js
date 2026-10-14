// Core engine: renderer, data loading, KaTeX overlay, deterministic frame rendering.
import * as THREE from 'three';
import katex from 'katex';
import { D2 } from './draw2d.js';
import { PAL } from './util.js';

export const W = 1920, H = 1080;

class TexLayer {
  constructor(div) {
    this.div = div;
    this.items = new Map();
    this.used = new Set();
  }
  _get(id, latex, size, color) {
    let it = this.items.get(id);
    if (!it || it.latex !== latex) {
      if (it) it.el.remove();
      const el = document.createElement('div');
      el.className = 'tex';
      el.style.fontSize = size + 'px';
      el.style.color = color;
      katex.render(latex, el, { throwOnError: false, displayMode: false });
      this.div.appendChild(el);
      it = { el, latex, w: 0, h: 0 };
      it.w = el.offsetWidth;
      it.h = el.offsetHeight;
      this.items.set(id, it);
    }
    return it;
  }
  // draw latex at (x,y) (top-left by default, or centred with align:'center')
  show(id, latex, x, y, o = {}) {
    const a = o.alpha ?? 1;
    if (a <= 0.001) return null;
    const it = this._get(id, latex, o.size ?? 40, o.color ?? PAL.ink);
    const s = o.scale ?? 1;
    let ox = 0, oy = 0;
    if (o.align === 'center') ox = -it.w * s / 2;
    if (o.align === 'right') ox = -it.w * s;
    if (o.valign === 'middle') oy = -it.h * s / 2;
    it.el.style.transform = `translate(${x + ox}px, ${y + oy + (o.dy ?? 0)}px) scale(${s})`;
    it.el.style.opacity = a;
    it.el.style.visibility = 'visible';
    if (o.glow) it.el.style.textShadow = `0 0 18px ${o.glow}`;
    this.used.add(id);
    return it;
  }
  begin() { this.used.clear(); }
  end() {
    for (const [id, it] of this.items) if (!this.used.has(id)) it.el.style.visibility = 'hidden';
  }
}

export class Engine {
  constructor(glCanvas, c2d, dom) {
    this.glCanvas = glCanvas;
    this.d2 = new D2(c2d);
    this.tex = new TexLayer(dom);
    this.data = {};
  }

  async init() {
    const weights = [300, 400, 500, 600, 650, 700, 800, 900];
    await Promise.all(weights.map((w) => document.fonts.load(`${w} 40px Inter`)));
    await document.fonts.load(`700 40px "Inter Display"`).catch(() => {});
    const q = new URLSearchParams(location.search);
    this.q = q;
    this.video = q.get('video') ?? 'fea';
    // data files per video: [key, file]
    const files = this.video === 'fatigue'
      ? [['timing', 'fatigue_timing'], ['global', 'global'], ['template', 'template'], ['wellhead_local', 'wellhead_local'],
        ['wellhead_surface', 'wellhead_surface'], ['fatigue', 'fatigue'], ['hotspot', 'hotspot']]
      : ['timing', 'cantilever', 'hourglass', 'notch', 'global', 'template', 'wellhead_local', 'wellhead_surface'].map((f) => [f, f]);
    await Promise.all(files.map(async ([k, f]) => {
      const r = await fetch(`/data/${f}.json`);
      this.data[k] = await r.json();
    }));
    const renderer = new THREE.WebGLRenderer({ canvas: this.glCanvas, antialias: q.get('aa') !== '0', alpha: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
    renderer.setPixelRatio(1);
    renderer.setSize(W, H, false);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.0;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.localClippingEnabled = true;
    this.renderer = renderer;
    // await KaTeX fonts
    this.tex.show('__warm', 'x^2\\,\\sigma', -500, -500, { alpha: 0.01 });
    await document.fonts.ready;
    return true;
  }

  timingFor(id) {
    return this.data.timing.scenes.find((s) => s.id === id);
  }

  async setup(factory, id, opts = {}) {
    const tm = this.timingFor(id) ?? { id, duration: opts.duration ?? 10, lines: [] };
    const cues = {};
    for (const ln of tm.lines) cues[ln.id] = ln;
    const ctx = {
      engine: this, THREE, renderer: this.renderer, d2: this.d2, tex: this.tex, data: this.data,
      W, H, duration: tm.duration, lines: tm.lines, opts,
      cue: (k) => { if (!cues[k]) throw new Error('missing cue ' + k); return cues[k].start; },
      cueEnd: (k) => cues[k].start + cues[k].dur,
      cueDur: (k) => cues[k].dur,
      // approximate time at which `sub` is spoken inside line k (proportional to character position)
      at: (k, sub, frac = 0) => {
        const c = cues[k];
        if (!c) throw new Error('missing cue ' + k);
        const i = c.text.indexOf(sub);
        if (i < 0) throw new Error(`'${sub}' not in ${k}`);
        const pos = (i + frac * sub.length) / c.text.length;
        return c.start + c.dur * (0.03 + 0.95 * pos);
      },
    };
    this.ctx = ctx;
    this.scene = await factory(ctx);
    this.scene.duration = this.scene.duration ?? tm.duration;
    return { duration: this.scene.duration, sfx: this.scene.sfx ?? [] };
  }

  frame(t) {
    this.d2.clear();
    this.tex.begin();
    this.renderer.setScissorTest(false);
    this.renderer.setViewport(0, 0, W, H);
    this.scene.render(t);
    this.tex.end();
    return true;
  }
}
