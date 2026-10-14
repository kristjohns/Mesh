// Step 2a: global model -> load-to-moment (stress) transfer curves, and running a force history through one.
import { makeBackdrop } from '../../engine/env.js';
import { Plot } from '../../engine/draw2d.js';
import { drawGlobal, Z } from '../globaldiag.js';
import { chainBar, stepCard } from './fcommon.js';
import { PAL, seg, env, ease, clamp, lerp, rgba } from '../../engine/util.js';

const HS_COL = { hp: PAL.violet, lp: PAL.cyan, cg: PAL.amber };
const HS_LAB = { hp: 'A  HP housing weld', lp: 'B  conductor housing weld', cg: 'C  conductor girth weld' };

export default async function transfer(ctx) {
  const { d2, cue, at, renderer, data } = ctx;
  const F = data.fatigue;
  const back = makeBackdrop();
  const g1 = cue('g1'), g2 = cue('g2'), g3 = cue('g3');
  const Hs = F.H;
  const curves = {};
  for (const h of F.hotspots) curves[h.id] = h.M.map((m, i) => [Hs[i], m / h.W / 1e6]);
  const interp = (pts, x) => {
    const s = Math.sign(x) || 1, a = Math.abs(x);
    for (let i = 0; i < pts.length - 1; i++) if (a <= pts[i + 1][0]) return s * (pts[i][1] + (pts[i + 1][1] - pts[i][1]) * (a - pts[i][0]) / (pts[i + 1][0] - pts[i][0]));
    return s * pts[pts.length - 1][1];
  };
  const dg = F.diagram;
  const umax = Math.max(...dg.uo.map(Math.abs), ...dg.ui.map(Math.abs));
  const uAt = (zs, us, z) => {
    for (let i = 0; i < zs.length - 1; i++) if (z >= zs[i] && z <= zs[i + 1]) return us[i] + (us[i + 1] - us[i]) * (z - zs[i]) / (zs[i + 1] - zs[i]);
    return z < zs[0] ? us[0] : us[us.length - 1];
  };
  const springZ = [];
  for (let z = -0.5; z >= -21; z -= 1.5) springZ.push(z);
  const ex = F.example;
  const Hsweep = (t) => 250 * seg(t, at('g1', 'increasing') - 0.3, 7.0, ease.inOutSine);

  return {
    sfx: [{ t: 0.1, type: 'chapter' }],
    render(t) {
      back.render(renderer);
      const H = Hsweep(t);
      const lA = env(t, 1.6, g3 - 0.3, 0.6, 0.7);
      if (lA > 0) {
        // ---------------------------------------------- left: global beam-spring model
        d2.panel(90, 120, 640, 900, { alpha: lA });
        d2.text('Global model', 120, 165, { size: 28, weight: 750, alpha: lA });
        d2.text('beams, p-y springs, interface springs, template gap', 120, 196, { size: 18, color: PAL.ink2, alpha: lA });
        const gapClosed = H >= 50;
        const sc = H * 0.32 / umax;   // px per mm of the 20 kN profile, scaled with the load
        const mob = (z) => clamp((H / 250) * 1.15 * Math.exp(z / 5));
        const geo = drawGlobal(d2, {
          x: 410, y0: 690, sy: 14.5, syUp: 1.75, zTop: 17.2, zBot: -21.5, alpha: lA, soilW: 290,
          u: (z) => (z > 2.6 ? uAt(dg.ui_z, dg.ui, z) : uAt(dg.uo_z, dg.uo, z)), ux: sc,
          springs: true, springZ, springL: 70, mob: seg(t, at('g2', 'soil springs') - 0.3, 0.6) > 0 ? mob : null,
          bopH: 13.2, bopW: 24, breakLabel: true,
          template: { gapPx: gapClosed ? 0 : lerp(14, 2, clamp(H / 50)), inner: 14, label: H > 1 ? (gapClosed ? 'template gap: closed' : 'template gap: open') : 'template gap', alpha: 1 },
        });
        // load arrow at the flex joint
        const yF = geo.Y(16.6), xF = geo.X(16.6);
        if (H > 0.5) {
          d2.arrow(xF, yF, xF + 24 + H * 0.5, yF, { color: PAL.orange, width: 6, head: 20, alpha: lA, glow: PAL.orange });
          d2.text(`${Math.round(H)} kN`, xF + 34 + H * 0.5, yF + 9, { size: 26, weight: 800, color: PAL.orange, alpha: lA });
        }
        d2.text('flex joint', xF - 32, yF + 7, { size: 18, color: PAL.ink2, align: 'right', alpha: lA });
        // hot spot markers
        const hq = seg(t, g1 + 1.4, 0.8);
        [['A', 1.2, 'hp'], ['B', 0.8, 'lp'], ['C', -3.0, 'cg']].forEach(([L, z, id], k) => {
          const x = geo.X(z), y = geo.Y(z);
          const xs = id === 'hp' ? x + 26 : x - 26;
          d2.circle(xs, y, 13, { fill: rgba(HS_COL[id], 0.25), stroke: HS_COL[id], width: 2.5, alpha: lA * hq });
          d2.text(L, xs, y + 7, { size: 17, weight: 800, color: HS_COL[id], align: 'center', alpha: lA * hq });
        });
        // ---------------------------------------------- right: transfer curves
        const P = new Plot(d2, { x: 900, y: 250, w: 860, h: 560, xr: [0, 250], yr: [0, 180] });
        d2.panel(800, 120, 1030, 900, { alpha: lA });
        d2.text('Transfer functions', 830, 165, { size: 28, weight: 750, alpha: lA });
        d2.text('nominal stress at each hot spot = moment ÷ section modulus', 830, 196, { size: 18, color: PAL.ink2, alpha: lA });
        P.axes({ alpha: lA, xticks: [0, 50, 100, 150, 200, 250], yticks: [0, 50, 100, 150], xlabel: 'flex-joint force [kN]', ylabel: 'nominal stress [MPa]', fs: 20, ylabelOff: 56 });
        for (const id of ['cg', 'lp', 'hp']) {
          const pts = curves[id].filter((p) => p[0] <= H);
          if (H > 0) pts.push([H, interp(curves[id], H)]);
          if (pts.length > 1) P.curve(pts, { color: HS_COL[id], width: 4, alpha: lA });
          if (H > 0) d2.circle(P.X(H), P.Y(interp(curves[id], H)), 7, { fill: HS_COL[id], alpha: lA, glow: HS_COL[id] });
        }
        // legend
        ['hp', 'lp', 'cg'].forEach((id, k) => {
          const y = P.y + 30 + k * 36;
          d2.line(P.x + 30, y - 7, P.x + 70, y - 7, { color: HS_COL[id], width: 4, alpha: lA * hq });
          d2.text(HS_LAB[id], P.x + 84, y, { size: 21, weight: 650, color: PAL.ink, alpha: lA * hq });
        });
        // g2 annotations
        const a1 = lA * seg(t, at('g2', 'radial clearance') - 0.2, 0.6);
        if (a1 > 0) {
          const x = P.X(65), y = P.Y(interp(curves.hp, 65));
          d2.circle(x, y, 20, { stroke: PAL.violet, width: 3, alpha: a1 });
          d2.callout(x, y, P.X(120), P.Y(18), 'housings touch', 'radial clearance closes ≈ 65 kN', { alpha: a1, progress: seg(t, at('g2', 'radial clearance') - 0.2, 1.0), color: PAL.violet, size: 24, straight: true });
        }
        const a2 = lA * seg(t, at('g2', 'fifty kilonewtons') - 0.3, 0.6);
        if (a2 > 0) {
          d2.line(P.X(50), P.y, P.X(50), P.y + P.h, { color: PAL.yellow, width: 2, dash: [8, 6], alpha: a2 });
          d2.tag('template gap closes ≈ 50 kN', P.X(50) + 12, P.y + P.h - 26, { size: 20, color: PAL.yellow, alpha: a2 });
          d2.text('the template takes', P.X(205), P.Y(interp(curves.cg, 205)) + 40, { size: 20, color: PAL.amber, align: 'center', alpha: a2 });
          d2.text('part of the load', P.X(205), P.Y(interp(curves.cg, 205)) + 64, { size: 20, color: PAL.amber, align: 'center', alpha: a2 });
        }
        const a3 = lA * seg(t, at('g2', 'soil springs soften') - 0.2, 0.6) * (1 - seg(t, at('g2', 'radial clearance'), 0.5));
        d2.tag('soil springs soften (p-y)', 410, 1000, { size: 20, color: PAL.amber, align: 'center', alpha: a3, fill: 'rgba(5,14,26,0.9)' });
      }
      // ---------------------------------------------- g3: run a force history through the curve
      const mA = env(t, g3 - 0.5, ctx.duration + 1, 0.7, 0.5);
      if (mA > 0) {
        d2.text('Force history in, stress history out', 960, 150, { size: 44, weight: 800, align: 'center', alpha: mA });
        d2.text('conductor girth weld (C), the same 3-hour sea state', 960, 192, { size: 22, color: PAL.ink2, align: 'center', alpha: mA });
        const Fm = 80;
        const P = new Plot(d2, { x: 300, y: 250, w: 560, h: 380, xr: [-Fm, Fm], yr: [-60, 60] });
        d2.panel(220, 220, 680, 450, { alpha: mA });
        P.axes({ alpha: mA, xticks: [-80, -40, 0, 40, 80], yticks: [-50, 0, 50], fs: 17, fmty: (v) => String(v), xlabel: '', ylabel: 'stress [MPa]', ylabelOff: 46 });
        const pts = [];
        for (let i = 0; i <= 120; i++) { const x = -Fm + 2 * Fm * i / 120; pts.push([x, interp(curves.cg, x)]); }
        P.curve(pts, { color: PAL.amber, width: 4, alpha: mA });
        d2.line(P.X(0), P.y, P.X(0), P.y + P.h, { color: 'rgba(160,190,210,0.25)', width: 1, alpha: mA });
        d2.line(P.x, P.Y(0), P.x + P.w, P.Y(0), { color: 'rgba(160,190,210,0.25)', width: 1, alpha: mA });
        // input below (time downwards), output to the right (time to the right)
        const T = 36, t0s = 20;
        const prog = seg(t, g3 - 0.2, ctx.duration - g3, ease.linear);
        const tn = prog * T;
        const yIn0 = 700, yIn1 = 1040, xOut0 = 960, xOut1 = 1820;
        d2.panel(220, 680, 680, 380, { alpha: mA * 0.9 });
        d2.text('force F(t) [kN]', 240, 716, { size: 20, weight: 700, color: PAL.orange, alpha: mA });
        d2.panel(940, 220, 900, 450, { alpha: mA * 0.9 });
        d2.text('stress σ(t) [MPa]', 960, 256, { size: 20, weight: 700, color: PAL.amber, alpha: mA });
        const inPts = [], outPts = [];
        const n = Math.floor(tn / ex.dt);
        for (let k = 0; k <= n; k++) {
          const i = Math.floor(t0s / ex.dt) + k;
          const f = ex.F[i];
          const tt = k * ex.dt;
          inPts.push([P.X(f), yIn0 + 30 + (yIn1 - yIn0 - 40) * tt / T]);
          outPts.push([xOut0 + 20 + (xOut1 - xOut0 - 40) * tt / T, P.Y(interp(curves.cg, f))]);
        }
        if (inPts.length > 1) {
          d2.path(inPts, { color: PAL.orange, width: 2.4, alpha: mA });
          d2.path(outPts, { color: PAL.amber, width: 2.4, alpha: mA });
          const pi = inPts[inPts.length - 1], po = outPts[outPts.length - 1];
          const cx = pi[0], cy = po[1];
          d2.line(pi[0], pi[1], cx, cy, { color: PAL.ink2, width: 1.4, dash: [5, 5], alpha: mA });
          d2.line(cx, cy, po[0], po[1], { color: PAL.ink2, width: 1.4, dash: [5, 5], alpha: mA });
          d2.circle(cx, cy, 8, { fill: PAL.amber, alpha: mA, glow: PAL.amber });
          d2.circle(pi[0], pi[1], 6, { fill: PAL.orange, alpha: mA });
          d2.circle(po[0], po[1], 6, { fill: PAL.amber, alpha: mA });
        }
        d2.arrow(240, yIn0 + 40, 240, yIn1 - 20, { color: PAL.ink3, width: 1.5, head: 9, alpha: mA });
        d2.text('time', 252, yIn1 - 24, { size: 17, color: PAL.ink3, alpha: mA });
        d2.arrow(xOut0 + 20, 640, xOut1 - 10, 640, { color: PAL.ink3, width: 1.5, head: 9, alpha: mA });
        d2.text('time', xOut1 - 10, 630, { size: 17, color: PAL.ink3, align: 'right', alpha: mA });
      }
      chainBar(d2, 2, { alpha: seg(t, 1.6, 0.6) });
      stepCard(d2, t, 2, 'From force to stress', 'transfer functions from the global model');
    },
  };
}
