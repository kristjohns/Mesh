// Welds: the toe is a notch; hot-spot stress extrapolation; averaged vs unaveraged check.
import { makeBackdrop } from '../engine/env.js';
import { Plot } from '../engine/draw2d.js';
import { keyLine } from './common.js';
import { PAL, seg, env, ease, clamp, lerp, rgba, turboCss } from '../engine/util.js';

export default async function welds(ctx) {
  const { d2, cue, at, renderer, tex } = ctx;
  const back = makeBackdrop();
  const w1 = cue('w1'), w2 = cue('w2'), w3 = cue('w3');
  // weld geometry (girth weld conductor -> housing), screen units
  const X0 = 960, Y0 = 520, T = 110; // wall thickness in px
  // surface stress along the plate approaching the weld toe (x measured from the toe, in t)
  const sigS = (x) => 1.0 + 0.32 * Math.max(0, 1.6 - x) / 1.6 + 0.08; // structural part
  const sigN = (x) => sigS(x) + 0.9 * Math.pow(x + 0.015, -0.42) * Math.exp(-x * 3.2) * 0.35; // with notch

  return {
    render(t) {
      back.render(renderer);
      const gA = env(t, w1 - 0.4, w2 + 0.5, 0.6, 0.5);
      const hA = env(t, w2 + 0.2, w3 + 0.2, 0.6, 0.5);
      // ---------------- weld cross-section (always shown on the left during w1/w2)
      const xA = Math.max(gA, hA);
      if (xA > 0) {
        const sc = hA > 0 ? lerp(1, 0.62, seg(t, w2, 1.0)) : 1;
        const ox = lerp(0, -470, seg(t, w2 + 0.2, 1.2, ease.inOutSine));
        const g = d2.g;
        g.save();
        g.translate(X0 + ox, Y0);
        g.scale(sc, sc);
        g.translate(-X0, -Y0);
        // conductor wall (left, thinner) and housing wall (right, thicker) - horizontal section
        const Tl = T, Tr = T * 1.6;
        d2.poly([[X0 - 600, Y0 - Tl / 2], [X0 - 40, Y0 - Tl / 2], [X0 - 40, Y0 + Tl / 2], [X0 - 600, Y0 + Tl / 2]], { fill: 'rgba(120,150,175,0.35)', stroke: '#9fb3c4', width: 2, alpha: xA });
        d2.poly([[X0 + 40, Y0 - Tl / 2 - (Tr - Tl)], [X0 + 600, Y0 - Tl / 2 - (Tr - Tl)], [X0 + 600, Y0 + Tl / 2], [X0 + 40, Y0 + Tl / 2]], { fill: 'rgba(110,150,190,0.35)', stroke: '#7fa6c7', width: 2, alpha: xA });
        // weld metal with cap and root
        const cap = [[X0 - 70, Y0 - Tl / 2], [X0 - 40, Y0 - Tl / 2 - 26], [X0 + 0, Y0 - Tl / 2 - 40], [X0 + 40, Y0 - Tl / 2 - (Tr - Tl) - 6], [X0 + 70, Y0 - Tl / 2 - (Tr - Tl)]];
        d2.poly([...cap, [X0 + 40, Y0 + Tl / 2], [X0 + 30, Y0 + Tl / 2 + 14], [X0 - 30, Y0 + Tl / 2 + 14], [X0 - 40, Y0 + Tl / 2]], { fill: 'rgba(170,150,110,0.55)', stroke: '#c9b48a', width: 2, alpha: xA });
        d2.text('conductor wall', X0 - 560, Y0 + Tl / 2 + 44, { size: 24, color: PAL.ink2, alpha: xA });
        d2.text('housing', X0 + 360, Y0 + Tl / 2 + 44, { size: 24, color: PAL.ink2, alpha: xA });
        d2.text('weld', X0, Y0 + Tl / 2 + 58, { size: 24, color: '#c9b48a', align: 'center', alpha: xA });
        // weld toe marker
        const toe = [X0 - 70, Y0 - Tl / 2];
        const tp = seg(t, at('w1', 'A weld toe'), 0.6);
        d2.circle(toe[0], toe[1], 16 + 4 * Math.sin(t * 5), { stroke: PAL.red, width: 3, alpha: xA * tp });
        d2.text('weld toe: geometrically sharp', toe[0] - 20, toe[1] - 44, { size: 26, weight: 700, color: PAL.red, align: 'right', alpha: gA * tp });
        // hot-spot mesh: t x t elements along the plate surface
        const mp = seg(t, at('w2', 'Mesh the wall'), 1.2);
        if (mp > 0) {
          for (let i = 0; i < 5; i++) {
            const x1 = toe[0] - i * Tl, x2 = toe[0] - (i + 1) * Tl;
            d2.rect(x2, Y0 - Tl / 2, Tl, Tl, { stroke: PAL.cyan, width: 2, fill: rgba(PAL.cyan, 0.06), alpha: hA * clamp(mp * 5 - i) });
          }
          d2.dim(toe[0] - Tl, Y0 + Tl / 2 + 90, toe[0], Y0 + Tl / 2 + 90, 't', { color: PAL.cyan, alpha: hA * mp, size: 26 });
          d2.text('element size ≈ t × t', toe[0] - 2.5 * Tl, Y0 - Tl / 2 - 80, { size: 26, weight: 700, color: PAL.cyan, align: 'center', alpha: hA * mp });
        }
        g.restore();
      }
      // ---------------- hot-spot plot (w2)
      if (hA > 0) {
        d2.tag('DNV-RP-C203 · hot-spot method', 1420, 120, { size: 22, alpha: hA * seg(t, at('w2', 'standards'), 0.6), align: 'center', color: PAL.amber });
        const P = new Plot(d2, { x: 1060, y: 200, w: 640, h: 440, xr: [3.0, 0], yr: [0.8, 2.2] });
        P.axes({ alpha: hA, xticks: [3, 2, 1.5, 1, 0.5, 0], yticks: [1.0, 1.5, 2.0], fmtx: (v) => (v === 0 ? 'toe' : `${v}t`), fmty: (v) => v.toFixed(1), xlabel: 'distance from the weld toe', ylabel: 'surface stress', fs: 20, ylabelOff: 60 });
        const cp = seg(t, at('w2', 'read the surface') - 1.0, 1.4);
        const pts = [];
        for (let i = 0; i <= 120; i++) { const x = 3 * (1 - i / 120); pts.push([x, sigN(x)]); }
        P.clipBegin();
        P.curve(pts, { color: PAL.ink2, width: 3, alpha: hA * cp, progress: cp });
        P.clipEnd();
        if (cp > 0.5) d2.text('local notch stress (mesh dependent)', P.X(0.15), P.Y(2.12), { size: 20, color: PAL.ink2, align: 'right', alpha: hA * seg(cp, 0.6, 0.4) });
        const rp = seg(t, at('w2', 'half a thickness'), 0.6, ease.outBack);
        const r2 = seg(t, at('w2', 'one and a half'), 0.6, ease.outBack);
        const s05 = sigS(0.5), s15 = sigS(1.5);
        if (r2 > 0) {
          d2.circle(P.X(1.5), P.Y(s15), 10 * r2, { fill: PAL.cyan, alpha: hA });
          d2.text('σ(1.5t)', P.X(1.5), P.Y(s15) + 40, { size: 22, weight: 700, color: PAL.cyan, align: 'center', alpha: hA * clamp(r2) });
        }
        if (rp > 0) {
          d2.circle(P.X(0.5), P.Y(s05), 10 * rp, { fill: PAL.cyan, alpha: hA });
          d2.text('σ(0.5t)', P.X(0.5), P.Y(s05) + 40, { size: 22, weight: 700, color: PAL.cyan, align: 'center', alpha: hA * clamp(rp) });
        }
        const ep = seg(t, at('w2', 'extrapolate'), 1.2, ease.inOutSine);
        if (ep > 0) {
          const shs = 1.5 * s05 - 0.5 * s15;
          const xe = lerp(1.5, 0, ep);
          d2.line(P.X(1.5), P.Y(s15), P.X(xe), P.Y(s15 + (shs - s15) * (1.5 - xe) / 1.5), { color: PAL.amber, width: 3.5, dash: [10, 6], alpha: hA });
          if (ep >= 1) {
            d2.circle(P.X(0), P.Y(shs), 11, { fill: PAL.amber, alpha: hA, glow: PAL.amber });
            d2.text('hot-spot', P.X(0) + 18, P.Y(shs) + 2, { size: 24, weight: 800, color: PAL.amber, alpha: hA });
            d2.text('stress', P.X(0) + 18, P.Y(shs) + 30, { size: 24, weight: 800, color: PAL.amber, alpha: hA });
          }
          tex.show('s08f', '\\sigma_{hs} = 1.5\\,\\sigma_{0.5t} - 0.5\\,\\sigma_{1.5t}', 1110, 700, { size: 38, alpha: hA * seg(t, at('w2', 'extrapolate') + 0.6, 0.6), color: PAL.amber });
        }
        const cA = hA * seg(t, at('w2', 'calibrated'), 0.6);
        if (cA > 0) {
          d2.panel(1080, 790, 700, 160, { alpha: cA, accent: PAL.amber });
          d2.text('S-N curves are calibrated to this procedure:', 1110, 840, { size: 26, weight: 700, alpha: cA });
          d2.text('follow it exactly — a finer mesh is not better here', 1110, 880, { size: 24, color: PAL.ink2, alpha: cA * seg(t, at('w2', 'A finer mesh'), 0.5) });
          d2.text('(stresses read on the surface, perpendicular to the toe)', 1110, 918, { size: 20, color: PAL.ink3, alpha: cA });
        }
      }
      // ---------------- w3: averaged vs unaveraged
      const aA = env(t, w3 + 0.2, ctx.duration, 0.6, 0.5);
      if (aA > 0) {
        d2.text('Quick mesh check: averaged vs unaveraged stress', 960, 150, { size: 44, weight: 800, align: 'center', alpha: aA });
        const panels = [{ x: 140, title: 'Coarse mesh', jump: 0.32, col: PAL.red, verdict: 'jumps > 10 % → refine' }, { x: 1000, title: 'Fine mesh', jump: 0.06, col: PAL.green, verdict: 'jumps small → mesh adequate' }];
        panels.forEach((pp, k) => {
          const q = seg(t, w3 + 0.6 + k * 1.6, 0.8);
          if (q <= 0) return;
          const P = new Plot(d2, { x: pp.x + 60, y: 300, w: 680, h: 380, xr: [0, 6], yr: [0, 1.4] });
          d2.panel(pp.x, 220, 800, 640, { alpha: aA * q });
          d2.text(pp.title, pp.x + 40, 270, { size: 30, weight: 750, alpha: aA * q });
          P.axes({ alpha: aA * q, xticks: [], yticks: [], fs: 18 });
          const f = (x) => 0.25 + 0.95 * Math.exp(-0.45 * (6 - x));
          const ne = k === 0 ? 4 : 12;
          for (let e = 0; e < ne; e++) {
            const xa = (6 * e) / ne, xb = (6 * (e + 1)) / ne;
            const xm = (xa + xb) / 2;
            const slope = (f(xb) - f(xa)) / (xb - xa) * (1 - pp.jump * 2.2);
            const ya = f(xm) - slope * (xm - xa), yb = f(xm) + slope * (xb - xm);
            d2.line(P.X(xa), P.Y(ya), P.X(xb), P.Y(yb), { color: pp.col, width: 4, alpha: aA * q });
            d2.line(P.X(xb), P.y + P.h, P.X(xb), P.y + P.h - 10, { color: PAL.ink3, width: 1.5, alpha: aA * q });
          }
          const sm = [];
          for (let i = 0; i <= 80; i++) sm.push([(6 * i) / 80, f((6 * i) / 80)]);
          P.curve(sm, { color: PAL.ink, width: 2, dash: [8, 6], alpha: aA * q * 0.8 });
          d2.text('unaveraged (per element)', pp.x + 80, 740, { size: 22, color: pp.col, weight: 650, alpha: aA * q });
          d2.text('averaged at nodes', pp.x + 80, 772, { size: 22, color: PAL.ink, weight: 650, alpha: aA * q });
          const v = seg(t, at('w3', k === 0 ? 'differ by more' : 'too coarse') + 0.2, 0.6);
          if (k === 0) d2.cross(pp.x + 440, 800, 18, { progress: v, alpha: aA * q }); else d2.check(pp.x + 440, 800, 18, { progress: v, alpha: aA * q });
          d2.text(pp.verdict, pp.x + 470, 810, { size: 22, weight: 700, color: pp.col, alpha: aA * q * clamp(v) });
        });
      }
    },
  };
}
