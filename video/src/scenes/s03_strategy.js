// Purpose first: global questions -> beam/spring model; local questions -> solid submodel.
import * as THREE from 'three';
import { makeBackdrop, renderViewport, studioScene, envMap } from '../engine/env.js';
import { makeLocalFE, colorBar } from '../models/femesh.js';
import { drawGlobal, Z } from './globaldiag.js';
import { PAL, seg, env, ease, clamp, lerp, rgba } from '../engine/util.js';

export function qCard(d2, x, y, w, text, p, o = {}) {
  if (p <= 0) return 0;
  const c = o.color ?? PAL.cyan;
  const lines = d2.wrap(text, w - 110, o.size ?? 27, 600);
  const h = 34 + lines.length * (o.size ?? 27) * 1.3;
  const dx = (1 - ease.out(p)) * (o.from ?? -40);
  d2.panel(x + dx, y, w, h, { alpha: p * (o.alpha ?? 1), accent: c });
  d2.circle(x + dx + 44, y + h / 2, 19, { fill: rgba(c, 0.18), stroke: c, width: 2, alpha: p * (o.alpha ?? 1) });
  d2.text(o.icon ?? '?', x + dx + 44, y + h / 2 + 9, { size: 26, weight: 800, color: c, align: 'center', alpha: p * (o.alpha ?? 1) });
  lines.forEach((ln, i) => d2.text(ln, x + dx + 82, y + 44 + i * (o.size ?? 27) * 1.3, { size: o.size ?? 27, weight: 600, alpha: p * (o.alpha ?? 1) }));
  return h;
}

export default async function strategy(ctx) {
  const { d2, cue, at, renderer } = ctx;
  const back = makeBackdrop();
  const fe = studioScene();
  const local = makeLocalFE(ctx.data.wellhead_surface, { vmax: 160, env: envMap(renderer) });
  local.userData.mat.toneMapped = false;
  const ycut = new THREE.Plane(new THREE.Vector3(0, 1, 0), -0.5);
  local.userData.mat.clippingPlanes = [ycut];
  local.userData.emat.clippingPlanes = [ycut];
  fe.add(local);
  const cam = new THREE.PerspectiveCamera(30, 1, 0.01, 50);
  const g1 = cue('g1'), g2 = cue('g2'), g3 = cue('g3'), g4 = cue('g4'), g5 = cue('g5');
  const nodes = [];
  for (let z = 0; z >= -30; z -= 1.5) nodes.push(z);
  nodes.push(0.8, 1.7, 2.6, 3.6);
  const springZ = nodes.filter((z) => z <= 0).sort((a, b) => b - a);
  const base = ctx.data.global.base;
  const uo = (z) => {
    // interpolate the real deflected shape (outer string below 2.6 m, inner above)
    const zz = base.zo, uu = base.uo;
    if (z <= 2.6) return interp(zz, uu, z);
    return interp(base.zi, base.ui, z);
  };

  return {
    sfx: [{ t: g3 + 0.3, type: 'whoosh' }, { t: g5 + 0.3, type: 'whoosh' }],
    render(t) {
      back.render(renderer);
      // ---- 3D local model (phase D)
      const la = env(t, g5 + 0.4, ctx.duration - 0.3, 0.8, 0.5);
      if (la > 0) {
        const s = 8 * seg(t, g5 + 1.0, 6, ease.inOutSine);
        local.userData.set(s, 25 * la);
        const ang = -0.33 + 0.12 * Math.sin(t * 0.3);
        const r = 9.9;
        cam.position.set(Math.sin(ang) * r, 3.0, Math.cos(ang) * r);
        cam.lookAt(0, 1.95, -0.1);
        cam.fov = 19;
        const vx = 1180, vy = 150, vw = 700, vh = 850;
        local.position.y = (1 - ease.out(clamp(la * 1.5))) * -0.6;
        renderViewport(renderer, fe, cam, vx, vy, vw, vh);
      }
      // ---- phase A: statement
      const aA = env(t, g1 - 0.4, g2 - 0.3, 0.6, 0.5);
      if (aA > 0) {
        const p = seg(t, g1 - 0.4, 1.2, ease.outExpo);
        d2.text('Questions first', 960, 470, { size: 92, weight: 800, align: 'center', alpha: aA * p });
        d2.text('The questions decide the model.', 960, 545, { size: 36, weight: 500, color: PAL.ink2, align: 'center', alpha: aA * seg(t, at('g1', 'The questions'), 0.8) });
        for (let i = 0; i < 5; i++) {
          const q = seg(t, g1 + 0.6 + i * 0.25, 0.6, ease.outBack);
          const ang = -0.9 + i * 0.45;
          d2.circle(960 + Math.cos(ang - Math.PI / 2) * 330, 500 + Math.sin(ang - Math.PI / 2) * 250, 24 * q, { stroke: rgba(PAL.cyan, 0.6), width: 2, alpha: aA * 0.7 });
          d2.text('?', 960 + Math.cos(ang - Math.PI / 2) * 330, 500 + Math.sin(ang - Math.PI / 2) * 250 + 10, { size: 28 * q, weight: 800, color: PAL.cyan, align: 'center', alpha: aA * 0.7 });
        }
      }
      // ---- phase B/C/D: global column; slides left and shrinks during g4
      const shrink = seg(t, g4 - 0.2, 1.4, ease.inOutSine);
      const gA = env(t, g2 - 0.1, ctx.duration - 0.3, 0.5, 0.5);
      if (gA > 0) {
        const g = d2.g;
        g.save();
        const sc = lerp(1, 0.62, shrink);
        g.translate(lerp(0, 30, shrink), lerp(0, 120, shrink));
        g.scale(sc, sc);
        d2.text('GLOBAL', 120, 150, { size: 26, weight: 800, color: PAL.cyan, ls: 6, alpha: gA });
        d2.text('questions', 262, 150, { size: 26, weight: 500, color: PAL.ink2, alpha: gA });
        let y = 200;
        y += 22 + qCard(d2, 120, y, 640, 'How is the load shared between the conductor, the casing and the template?', seg(t, at('g2', 'How is the load'), 0.7), {});
        qCard(d2, 120, y, 640, 'How far down into the soil does the bending go?', seg(t, at('g2', 'How far down'), 0.7), {});
        // global model diagram
        const dp = seg(t, g3 + 0.1, 2.4, ease.inOutSine);
        if (dp > 0) {
          const defl = seg(t, at('g3', 'runs in seconds') - 0.5, 2.0, ease.inOutSine);
          drawGlobal(d2, {
            x: 1180, y0: 700, sy: 13, syUp: 1.0, zTop: 17, zBot: -26, p: dp, alpha: gA,
            u: uo, ux: 520 * defl, springs: true, springZ, springP: seg(t, g3 + 1.0, 2.0), springL: 70,
            nodes, nodeP: seg(t, g3 + 0.6, 1.5), soilW: 300,
            mob: (z) => defl * interp(base.springs.map((s) => s.z), base.springs.map((s) => s.mob), z),
          });
          const ta = seg(t, g3 + 0.8, 0.8);
          d2.tag('GLOBAL MODEL', 1180, 360, { size: 22, alpha: gA * ta, align: 'center' });
          const lp = seg(t, at('g3', 'with beams'), 0.8);
          d2.text('Beams for the pipes', 120, 640, { size: 30, weight: 650, alpha: gA * lp });
          d2.text('Springs for the soil', 120, 690, { size: 30, weight: 650, color: PAL.teal, alpha: gA * seg(t, at('g3', 'springs for'), 0.8) });
          d2.text('Runs in seconds → easy sensitivity studies', 120, 750, { size: 26, weight: 500, color: PAL.ink2, alpha: gA * seg(t, at('g3', 'runs in seconds'), 0.8) });
          if (defl > 0.05) d2.text(`lateral deflection ×${Math.round(520 / 13)}`, 1180 + 40, 700 - 18 * 13, { size: 18, color: PAL.ink3, alpha: gA * defl });
        }
        g.restore();
      }
      // ---- local questions (g4) and the local model (g5)
      const lA = env(t, g4 + 0.6, ctx.duration - 0.3, 0.5, 0.5);
      if (lA > 0) {
        const mv = seg(t, g5 + 0.2, 1.2, ease.inOutSine);
        const x0 = lerp(980, 820, mv), wq = lerp(800, 560, mv);
        const y0 = lerp(220, 150, mv);
        d2.text('LOCAL', x0, y0 - 50, { size: 26, weight: 800, color: PAL.amber, ls: 6, alpha: lA });
        d2.text('questions', x0 + 128, y0 - 50, { size: 26, weight: 500, color: PAL.ink2, alpha: lA });
        let y = y0;
        y += 22 + qCard(d2, x0, y, wq, 'What is the stress at a weld toe?', seg(t, at('g4', 'What is the stress'), 0.7), { color: PAL.amber, size: lerp(27, 23, mv) });
        y += 22 + qCard(d2, x0, y, wq, 'How is the contact pressure distributed on the landing shoulder?', seg(t, at('g4', 'How is the contact'), 0.7), { color: PAL.amber, size: lerp(27, 23, mv) });
        const np = seg(t, at('g4', 'A beam model'), 0.6);
        if (np > 0) {
          d2.cross(x0 + 30, y + 30, 18, { progress: np, alpha: lA });
          d2.text('A beam model has no information about either', x0 + 64, y + 40, { size: lerp(25, 21, mv), weight: 600, color: PAL.red, alpha: lA * np });
        }
      }
      // phase D labels
      const dA = env(t, g5 + 0.5, ctx.duration - 0.3, 0.6, 0.5);
      if (dA > 0) {
        d2.tag('LOCAL SOLID MODEL', 1510, 130, { size: 22, alpha: dA, align: 'center', color: PAL.amber });
        colorBar(d2, 1748, 640, 22, 260, 0, 160, 'von Mises, MPa', { alpha: dA });
        // zoom link from the global wellhead region to the local model
        const lp = seg(t, at('g5', 'drive its boundaries') - 0.3, 1.0, ease.inOutSine);
        if (lp > 0) {
          const sc = 0.62, ox = 30, oy = 120;
          const gx = ox + 1180 * sc, gy = oy + (700 - 2.5 * 13) * sc;
          d2.rect(gx - 34, gy - 44, 68, 80, { stroke: PAL.amber, width: 2, alpha: dA * lp });
          d2.path([[gx + 34, gy - 4], [gx + 120, gy - 4], [gx + 120, 640], [1380, 640]], { color: PAL.amber, width: 2.5, alpha: dA * lp, progress: lp, dash: [8, 6] });
          d2.arrow(1340, 640, 1425, 640, { color: PAL.amber, width: 3, alpha: dA * seg(t, at('g5', 'drive its boundaries') + 0.6, 0.5) });
          d2.text('boundary loads', gx + 135, 690, { size: 22, weight: 650, color: PAL.amber, alpha: dA * seg(t, at('g5', 'drive its boundaries') + 0.6, 0.5) });
          d2.text('from the global model', gx + 135, 718, { size: 20, weight: 500, color: PAL.ink2, alpha: dA * seg(t, at('g5', 'drive its boundaries') + 0.6, 0.5) });
        }
        const sp = seg(t, at('g5', 'global-local'), 0.8);
        if (sp > 0) {
          d2.panel(560, 930, 800, 82, { alpha: dA * sp, accent: PAL.amber });
          d2.text('Global–local analysis  ·  submodelling', 960, 982, { size: 32, weight: 700, align: 'center', alpha: dA * sp });
        }
      }
    },
  };
}

function interp(xs, ys, x) {
  // xs ascending
  if (x <= xs[0]) return ys[0];
  if (x >= xs[xs.length - 1]) return ys[ys.length - 1];
  let lo = 0, hi = xs.length - 1;
  while (hi - lo > 1) { const m = (lo + hi) >> 1; if (xs[m] <= x) lo = m; else hi = m; }
  const f = (x - xs[lo]) / (xs[hi] - xs[lo]);
  return ys[lo] + f * (ys[hi] - ys[lo]);
}
export { interp };
