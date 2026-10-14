// Solid elements: tet vs hex, linear vs quadratic; locking, hourglassing, the rules.
import * as THREE from 'three';
import { makeBackdrop, renderViewport, studioScene, fatLines, toScreen } from '../engine/env.js';
import { ruleCard } from './common.js';
import { PAL, seg, env, ease, clamp, lerp, rgba } from '../engine/util.js';

const COL = { TET4: PAL.red, HEX8: PAL.cyan, TET10: PAL.green, HEX20: PAL.amber, HEX8I: PAL.violet };
const hex = (c) => parseInt(c.slice(1), 16);

// ------------------------------------------------------------ single element shapes
function elementShape(kind) {
  const g = new THREE.Group();
  let V, E, mids = [];
  if (kind.startsWith('TET')) {
    V = [[0, 0, 0], [1.6, 0, 0], [0.8, 0, 1.4], [0.8, 1.3, 0.47]];
    E = [[0, 1], [1, 2], [2, 0], [0, 3], [1, 3], [2, 3]];
  } else {
    V = [[0, 0, 0], [1.3, 0, 0], [1.3, 0, 1.3], [0, 0, 1.3], [0, 1.3, 0], [1.3, 1.3, 0], [1.3, 1.3, 1.3], [0, 1.3, 1.3]];
    E = [[0, 1], [1, 2], [2, 3], [3, 0], [4, 5], [5, 6], [6, 7], [7, 4], [0, 4], [1, 5], [2, 6], [3, 7]];
  }
  const quad = kind === 'TET10' || kind === 'HEX20';
  const c = kind.startsWith('TET') ? [0.8, 0.43, 0.47] : [0.65, 0.65, 0.65];
  const ctr = V.reduce((a, v) => a.map((x, i) => x + v[i] / V.length), [0, 0, 0]);
  const pos = [];
  for (const [a, b] of E) {
    pos.push(...V[a].map((x, i) => x - ctr[i]), ...V[b].map((x, i) => x - ctr[i]));
    if (quad) mids.push(V[a].map((x, i) => (x + V[b][i]) / 2 - ctr[i]));
  }
  const col = quad ? (kind === 'TET10' ? 0x3ddc97 : 0xffb703) : (kind === 'TET4' ? 0xef476f : 0x4cc9f0);
  g.add(fatLines(pos, { color: col, width: 3 }));
  // translucent faces
  const fg = new THREE.BufferGeometry();
  const fpos = [];
  const faces = kind.startsWith('TET') ? [[0, 1, 2], [0, 1, 3], [1, 2, 3], [0, 2, 3]]
    : [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]];
  for (const f of faces) {
    const tri = f.length === 3 ? [f] : [[f[0], f[1], f[2]], [f[0], f[2], f[3]]];
    for (const tr of tri) for (const k of tr) fpos.push(...V[k].map((x, i) => x - ctr[i]));
  }
  fg.setAttribute('position', new THREE.Float32BufferAttribute(fpos, 3));
  fg.computeVertexNormals();
  g.add(new THREE.Mesh(fg, new THREE.MeshStandardMaterial({ color: col, transparent: true, opacity: 0.16, side: THREE.DoubleSide, depthWrite: false })));
  const nm = new THREE.MeshBasicMaterial({ color: 0xeaf2f8 });
  for (const v of V) { const s = new THREE.Mesh(new THREE.SphereGeometry(0.075, 16, 8), nm); s.position.set(...v.map((x, i) => x - ctr[i])); g.add(s); }
  const mm = new THREE.MeshBasicMaterial({ color: 0xffb703 });
  for (const v of mids) { const s = new THREE.Mesh(new THREE.SphereGeometry(0.065, 16, 8), mm); s.position.set(...v); g.add(s); }
  return g;
}

// ------------------------------------------------------------ deformed cantilever from FE edges
function cantilever(vis, color) {
  const n = vis.npl, ns = vis.nsamp;
  const P = vis.p, D = vis.d;
  const segs = [];
  for (let i = 0; i < n; i++) for (let k = 0; k < ns - 1; k++) segs.push(i * ns + k, i * ns + k + 1);
  const pos = new Float32Array(segs.length * 3);
  const lines = fatLines(Array.from(pos), { color: hex(color), width: 2.2 });
  // fill surface from the 4 longitudinal corner edges
  const corner = { '00': [], '01': [], '10': [], '11': [] };
  for (let i = 0; i < n; i++) {
    const a = P[i * ns], b = P[i * ns + ns - 1];
    if (Math.abs(a[1] - b[1]) < 1e-6 && Math.abs(a[2] - b[2]) < 1e-6 && Math.abs(a[0] - b[0]) > 1e-6) {
      const key = `${Math.round(a[1])}${Math.round(a[2])}`;
      if ((a[1] === 0 || a[1] === 1) && (a[2] === 0 || a[2] === 1)) for (let k = 0; k < ns; k++) corner[key].push(i * ns + k);
    }
  }
  for (const k of Object.keys(corner)) corner[k].sort((u, v) => P[u][0] - P[v][0]);
  const m = corner['00'].length;
  const fill = new THREE.BufferGeometry();
  const fpos = new Float32Array(m * 4 * 3);
  fill.setAttribute('position', new THREE.BufferAttribute(fpos, 3));
  const idx = [];
  const ring = ['00', '10', '11', '01'];
  for (let j = 0; j < m - 1; j++) for (let r = 0; r < 4; r++) {
    const a = r * m + j, b = ((r + 1) % 4) * m + j;
    idx.push(a, b, b + 1, a, b + 1, a + 1);
  }
  fill.setIndex(idx);
  const fm = new THREE.MeshStandardMaterial({ color: hex(color), transparent: true, opacity: 0.22, side: THREE.DoubleSide, depthWrite: false, roughness: 0.6 });
  const grp = new THREE.Group();
  grp.add(new THREE.Mesh(fill, fm), lines);
  grp.userData.set = (s) => {
    const arr = [];
    for (const q of segs) arr.push(P[q][0] + s * D[q][0], P[q][2] + s * D[q][2], -(P[q][1] + s * D[q][1]));
    lines.geometry.setPositions(arr);
    ring.forEach((key, r) => corner[key].forEach((q, j) => {
      fpos[3 * (r * m + j)] = P[q][0] + s * D[q][0];
      fpos[3 * (r * m + j) + 1] = P[q][2] + s * D[q][2];
      fpos[3 * (r * m + j) + 2] = -(P[q][1] + s * D[q][1]);
    }));
    fill.attributes.position.needsUpdate = true;
    fill.computeVertexNormals();
  };
  grp.userData.set(0);
  return grp;
}

function exactGhost(L, wtip) {
  const g = new THREE.BufferGeometry();
  const nx = 60;
  const pos = new Float32Array((nx + 1) * 4 * 3);
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  const idx = [];
  for (let j = 0; j < nx; j++) for (let r = 0; r < 4; r++) { const a = r * (nx + 1) + j, b = ((r + 1) % 4) * (nx + 1) + j; idx.push(a, b, b + 1, a, b + 1, a + 1); }
  g.setIndex(idx);
  const mesh = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.07, side: THREE.DoubleSide, depthWrite: false }));
  const eg = new THREE.BufferGeometry();
  const epos = new Float32Array(nx * 2 * 3 * 4);
  eg.setAttribute('position', new THREE.BufferAttribute(epos, 3));
  const edges = new THREE.LineSegments(eg, new THREE.LineDashedMaterial({ color: 0xffffff, transparent: true, opacity: 0.55, dashSize: 0.18, gapSize: 0.12 }));
  const grp = new THREE.Group();
  grp.add(mesh, edges);
  const cs = [[0, 0], [1, 0], [1, 1], [0, 1]];
  grp.userData.set = (s) => {
    let k = 0;
    for (let r = 0; r < 4; r++) for (let j = 0; j <= nx; j++) {
      const x = (L * j) / nx;
      const w = -wtip * s * (x * x * (3 * L - x)) / (2 * L ** 3);
      pos[3 * (r * (nx + 1) + j)] = x; pos[3 * (r * (nx + 1) + j) + 1] = cs[r][1] + w; pos[3 * (r * (nx + 1) + j) + 2] = -cs[r][0];
    }
    for (let r = 0; r < 4; r++) for (let j = 0; j < nx; j++) {
      for (const jj of [j, j + 1]) {
        const x = (L * jj) / nx;
        const w = -wtip * s * (x * x * (3 * L - x)) / (2 * L ** 3);
        epos[k++] = x; epos[k++] = cs[r][1] + w; epos[k++] = -cs[r][0];
      }
    }
    g.attributes.position.needsUpdate = true;
    eg.attributes.position.needsUpdate = true;
    edges.computeLineDistances();
  };
  grp.userData.set(0);
  return grp;
}

export default async function solids(ctx) {
  const { d2, cue, at, renderer, data } = ctx;
  const C = data.cantilever;
  const back = makeBackdrop();
  const t1 = cue('t1'), t2 = cue('t2'), t3 = cue('t3'), t4 = cue('t4'), t5 = cue('t5'), t6 = cue('t6'), t7 = cue('t7');
  // element zoo scene
  const zoo = studioScene();
  const shapes = {};
  const zpos = { TET4: [-2.2, 1.3], HEX8: [2.2, 1.3], TET10: [-2.2, -1.5], HEX20: [2.2, -1.5] };
  for (const k of ['TET4', 'HEX8', 'TET10', 'HEX20']) {
    const s = elementShape(k);
    s.position.set(zpos[k][0], zpos[k][1], 0);
    zoo.add(s);
    shapes[k] = s;
  }
  const zcam = new THREE.PerspectiveCamera(30, 16 / 9, 0.1, 100);
  zcam.position.set(0, 0.8, 12.5);
  zcam.lookAt(0, -0.1, 0);
  // cantilever scene
  const cs = studioScene({ hemi: 1.4 });
  const rows = ['HEX8', 'TET4', 'HEX20', 'TET10'];
  const beams = {};
  const ghosts = {};
  rows.forEach((k, i) => {
    const b = cantilever(C.vis[k], COL[k]);
    b.position.y = 7.2 - i * 4.0;
    cs.add(b);
    beams[k] = b;
    const gh = exactGhost(10, C.w_ref);
    gh.position.y = b.position.y;
    cs.add(gh);
    ghosts[k] = gh;
  });
  const wall = new THREE.Mesh(new THREE.BoxGeometry(0.3, 17, 2.2), new THREE.MeshStandardMaterial({ color: 0x33475a, roughness: 0.9 }));
  wall.position.set(-0.15, 2.8, -0.5);
  cs.add(wall);
  const ccam = new THREE.PerspectiveCamera(24, 16 / 9, 0.1, 200);
  const SCALE = 0.45; // deflection magnification for display
  const hg = data.hourglass;

  const bars = [
    { k: 'HEX8', name: 'Linear hex', sub: 'HEX8', v: C.convergence.HEX8[0].ratio, t: at('t3', 'linear hexahedron') },
    { k: 'TET4', name: 'Linear tet', sub: 'TET4', v: C.convergence.TET4[0].ratio, t: at('t3', 'linear tetrahedron') },
    { k: 'HEX20', name: 'Quadratic hex', sub: 'HEX20', v: C.convergence.HEX20[0].ratio, t: at('t6', 'twenty-node') },
    { k: 'TET10', name: 'Quadratic tet', sub: 'TET10', v: C.convergence.TET10[0].ratio, t: at('t6', 'ten-node') },
    { k: 'HEX8I', name: 'Linear hex, enhanced', sub: 'HEX8I · incompatible modes', v: C.convergence.HEX8I[0].ratio, t: at('t6', 'incompatible modes') },
  ];

  const drawBars = (a, x, y, w) => {
    d2.panel(x - 30, y - 70, w + 60, 520, { alpha: a });
    d2.text('Tip deflection, one element through the thickness', x, y - 26, { size: 24, weight: 650, alpha: a });
    const bw = w - 230;
    const ex = x + 230 + bw;
    bars.forEach((b, i) => {
      const p = seg(ctx._t, b.t, 1.0, ease.outQuint);
      if (p <= 0) return;
      const yy = y + 30 + i * 82;
      d2.text(b.name, x, yy + 6, { size: 22, weight: 650, alpha: a * clamp(p * 3), color: COL[b.k] });
      d2.text(b.sub, x, yy + 32, { size: 17, weight: 600, alpha: a * clamp(p * 3), color: PAL.ink3, ls: 1 });
      d2.rect(x + 230, yy - 12, bw, 30, { fill: 'rgba(255,255,255,0.05)', alpha: a });
      d2.rect(x + 230, yy - 12, bw * b.v * p, 30, { fill: COL[b.k], alpha: a * 0.85 });
      const inside = b.v * p > 0.8;
      d2.text(`${Math.round(100 * b.v * p)}%`, inside ? x + 222 + bw * b.v * p : x + 240 + bw * b.v * p, yy + 12, { size: 24, weight: 800, alpha: a * clamp(p * 2), color: inside ? '#06101a' : PAL.ink, align: inside ? 'right' : 'left' });
    });
    d2.line(ex, y + 4, ex, y + 30 + 5 * 82 - 30, { color: PAL.ink, width: 2, alpha: a * 0.8, dash: [6, 6] });
    d2.text('exact', ex, y + 0, { size: 18, weight: 700, color: PAL.ink2, align: 'center', alpha: a });
  };

  return {
    sfx: [{ t: t3 + 0.3, type: 'whoosh' }, { t: t6 + 0.4, type: 'whoosh' }],
    render(t) {
      ctx._t = t;
      back.render(renderer);
      // ---------------- t1: element zoo
      const hA0 = env(t, 0.2, t2 - 0.2, 0.6, 0.5);
      d2.text('Inside the solid family', 960, 1000, { size: 30, weight: 700, color: PAL.ink2, align: 'center', ls: 2, alpha: hA0 });
      const zA = env(t, 0.2, t2 - 0.2, 0.6, 0.5);
      if (zA > 0) {
        for (const [k, s] of Object.entries(shapes)) {
          s.rotation.y = t * 0.35 + (k.includes('HEX') ? 0.5 : 0);
          s.rotation.x = 0.35;
          const q = seg(t, at('t1', k.startsWith('TET') ? 'tetrahedra' : 'hexahedra') + (k.endsWith('0') ? 0.8 : 0), 0.6, ease.outBack);
          s.scale.setScalar(Math.max(0.001, q));
        }
        renderViewport(renderer, zoo, zcam, 0, 0, 1920, 1080);
        d2.fadeRect(1 - zA, '#060f19');
        const h1 = seg(t, at('t1', 'tetrahedra'), 0.6), h2 = seg(t, at('t1', 'hexahedra'), 0.6);
        d2.text('TETRAHEDRA', 960 - 520, 150, { size: 30, weight: 800, color: PAL.ink, align: 'center', ls: 5, alpha: zA * h1 });
        d2.text('HEXAHEDRA', 960 + 520, 150, { size: 30, weight: 800, color: PAL.ink, align: 'center', ls: 5, alpha: zA * h2 });
        const lin = seg(t, at('t1', 'linear'), 0.6), qd = seg(t, at('t1', 'quadratic'), 0.6);
        d2.text('LINEAR', 960, 370, { size: 26, weight: 800, color: PAL.ink2, align: 'center', ls: 5, alpha: zA * lin });
        d2.text('QUADRATIC', 960, 750, { size: 26, weight: 800, color: PAL.ink2, align: 'center', ls: 5, alpha: zA * qd });
        const lab = (k, x, y, s1, s2) => {
          const a2 = zA * seg(t, at('t1', 'orders') + (k.endsWith('0') ? 0.6 : 0), 0.6);
          d2.text(s1, x, y, { size: 30, weight: 750, color: COL[k], align: 'center', alpha: a2 });
          d2.text(s2, x, y + 34, { size: 22, color: PAL.ink2, align: 'center', alpha: a2 });
        };
        lab('TET4', 520, 520, 'TET4', '4 corner nodes');
        lab('HEX8', 1400, 520, 'HEX8', '8 corner nodes');
        lab('TET10', 520, 985, 'TET10', '+ mid-side nodes');
        lab('HEX20', 1400, 985, 'HEX20', '+ mid-side nodes');
      }
      // ---------------- cantilever views: t2..t4 and t6..end
      const cA = Math.max(env(t, t2 - 0.1, t4 + 0.4, 0.6, 0.6), env(t, t6 + 0.2, ctx.duration, 0.6, 0.6));
      if (cA > 0) {
        const showQ = t > t6;
        const vis = { HEX8: seg(t, t2 + 0.4, 1.0), TET4: seg(t, t3 + 1.6, 0.8), HEX20: showQ ? seg(t, at('t6', 'twenty-node') - 0.5, 0.8) : 0, TET10: showQ ? seg(t, at('t6', 'ten-node') - 0.5, 0.8) : 0 };
        const dp = { HEX8: seg(t, t3, 2.5, ease.inOutSine), TET4: seg(t, at('t3', 'linear tetrahedron'), 2.2, ease.inOutSine),
          HEX20: seg(t, at('t6', 'twenty-node'), 2.2, ease.inOutSine), TET10: seg(t, at('t6', 'ten-node'), 2.2, ease.inOutSine) };
        for (const k of rows) {
          beams[k].visible = vis[k] > 0.01;
          beams[k].scale.setScalar(1);
          beams[k].children[0].material.opacity = 0.22 * vis[k];
          beams[k].children[1].material.opacity = vis[k];
          beams[k].children[1].material.transparent = true;
          beams[k].userData.set(SCALE * dp[k]);
          ghosts[k].visible = vis[k] > 0.01;
          ghosts[k].userData.set(SCALE * Math.max(dp[k], seg(t, at('t2', 'beam theory') - 0.3, 1.5)) * (k === 'HEX8' || t > t3 ? 1 : 0));
        }
        const tcam = t > t7 ? seg(t, t7 + 0.5, 2.0) : 0;
        ccam.position.set(lerp(5.4, 4.8, tcam), 3.6, 36);
        ccam.lookAt(lerp(5.4, 4.8, tcam), 1.75, 0);
        const fo = env(t, t2 - 0.1, t4 + 0.4, 0.6, 0.6) + env(t, t6 + 0.2, ctx.duration, 0.6, 0.6);
        renderViewport(renderer, cs, ccam, 0, 60, 1180, 980);
        // row labels and per-beam results
        rows.forEach((k, i) => {
          if (vis[k] <= 0.01) return;
          const [lx, ly] = toScreen([-0.6, 7.2 - i * 4.0 + 0.5, 0], ccam, 1180, 980);
          d2.text(k, lx - 6, ly + 60 + 10, { size: 26, weight: 800, color: COL[k], align: 'right', alpha: cA * vis[k] });
          const r = C.vis[k].ratio;
          const [tx, ty] = toScreen([10.2, 7.2 - i * 4.0 - SCALE * C.w_ref * r * dp[k] + 0.5, 0], ccam, 1180, 980);
          if (dp[k] > 0.6) d2.text(`${Math.round(100 * r)}%`, tx + 10, ty + 60 + 9, { size: 30, weight: 800, color: COL[k], alpha: cA * seg(dp[k], 0.6, 0.3) });
        });
        // load arrow on the top beam(s)
        const la = cA * seg(t, at('t2', 'a load') - 0.3, 0.6);
        rows.forEach((k, i) => {
          if (vis[k] <= 0.01) return;
          const yb = 7.2 - i * 4.0 + 1 - SCALE * C.w_ref * C.vis[k].ratio * dp[k];
          const [ax, ay] = toScreen([10, yb + 1.6, 0], ccam, 1180, 980);
          const [bx, by] = toScreen([10, yb + 0.05, 0], ccam, 1180, 980);
          d2.arrow(ax, ay + 60, bx, by + 60, { color: PAL.ink, width: 4, head: 16, alpha: la * vis[k] });
        });
        const ga = cA * seg(t, at('t2', 'beam theory') - 0.3, 0.8);
        d2.text('dashed: exact (beam theory)', 1240, 190, { size: 22, color: PAL.ink2, alpha: ga });
        d2.text(`deflections ×${SCALE * 10 / 1}`.replace('4.5', '4.5'), 70, 1010, { size: 20, color: PAL.ink3, alpha: ga * 0 });
        d2.text('Cantilever test: 1 element through the thickness', 1240, 150, { size: 26, weight: 700, color: PAL.ink, alpha: cA * seg(t, at('t2', 'only one element'), 0.6) });
        // bar chart
        const bA = cA * seg(t, t3 + 0.2, 0.8);
        if (bA > 0 && t < t7 + 0.8) drawBars(bA * (1 - seg(t, t7, 0.8)), 1240, 330, 600);
        const lk = env(t, at('t3', 'This is called locking'), t4 + 0.4, 0.4, 0.5);
        if (lk > 0) {
          d2.panel(1210, 880, 660, 90, { alpha: lk, accent: PAL.red });
          d2.text('Far too stiff: locking', 1540, 938, { size: 36, weight: 800, align: 'center', color: PAL.red, alpha: lk });
        }
      }
      // ---------------- t4: shear locking diagrams
      const sA = env(t, t4 + 0.2, t5 - 0.2, 0.6, 0.5);
      if (sA > 0) {
        const k = seg(t, at('t4', 'In bending') - 0.2, 2.0, ease.inOutSine) * (0.8 + 0.2 * Math.sin(t * 1.4));
        d2.text('Why linear elements lock', 960, 140, { size: 50, weight: 800, align: 'center', alpha: sA });
        // left: real material
        drawBendingTrue(d2, 520, 520, 520, 300, k, sA * seg(t, at('t4', 'the material'), 0.6));
        d2.text('Real material', 520, 300, { size: 34, weight: 750, align: 'center', alpha: sA * seg(t, at('t4', 'the material'), 0.6) });
        d2.text('sections stay square to the curved axis', 520, 340, { size: 22, color: PAL.ink2, align: 'center', alpha: sA * seg(t, at('t4', 'curves'), 0.6) });
        const rA = sA * seg(t, at('t4', 'A linear element'), 0.6);
        drawBendingQ4(d2, 1400, 520, 520, 300, k, rA, seg(t, at('t4', 'to shear'), 0.8));
        d2.text('Linear element', 1400, 300, { size: 34, weight: 750, align: 'center', alpha: rA, color: PAL.cyan });
        d2.text('straight edges cannot curve', 1400, 340, { size: 22, color: PAL.ink2, align: 'center', alpha: rA });
        const eA = sA * seg(t, at('t4', 'stores strain energy'), 0.7);
        d2.panel(460, 820, 1000, 120, { alpha: eA, accent: PAL.red });
        d2.text('Fake shear strain stores real strain energy', 960, 870, { size: 32, weight: 700, align: 'center', alpha: eA });
        d2.text('→ the element is far too stiff: shear locking', 960, 912, { size: 28, weight: 600, align: 'center', color: PAL.red, alpha: eA * seg(t, at('t4', 'This is shear locking'), 0.6) });
      }
      // ---------------- t5: reduced integration, hourglassing
      const hA = env(t, t5 + 0.2, t6 + 0.2, 0.6, 0.5);
      if (hA > 0) {
        d2.text('Reduced integration and hourglassing', 960, 140, { size: 50, weight: 800, align: 'center', alpha: hA });
        const mode = seg(t, at('t5', 'this hourglass') - 0.3, 0.8) * Math.sin(t * 3.2);
        drawHourglassElement(d2, 420, 470, 300, mode, hA, seg(t, at('t5', 'single point'), 0.6));
        d2.text('one integration point', 420, 690, { size: 24, weight: 650, color: PAL.red, align: 'center', alpha: hA * seg(t, at('t5', 'single point'), 0.6) });
        d2.text('zero strain at that point → no stiffness', 420, 726, { size: 22, color: PAL.ink2, align: 'center', alpha: hA * seg(t, at('t5', 'produces no strain'), 0.6) });
        // real mesh result: full vs one-point integration
        const mA = hA * seg(t, at('t5', 'nothing resists') - 0.6, 0.8);
        const ps = seg(t, at('t5', 'nothing resists') - 0.4, 1.6, ease.inOutSine);
        drawMesh2D(d2, hg, hg.u_full, 1000, 300, 820, ps, mA * 0.9, PAL.cyan, 'full integration (2×2)');
        drawMesh2D(d2, hg, hg.u_hg, 1000, 600, 820, ps, mA, PAL.red, 'one-point integration, weak hourglass control');
        const nA = hA * seg(t, at('t5', 'Without hourglass control'), 0.6);
        d2.panel(330, 830, 1260, 140, { alpha: nA, accent: PAL.red });
        d2.text('Our cantilever, no hourglass control:', 380, 885, { size: 28, weight: 700, alpha: nA });
        d2.text('1 element through the thickness → singular (no solution)', 380, 925, { size: 26, color: PAL.ink2, alpha: nA * seg(t, at('t5', 'is singular'), 0.5) });
        d2.text(`2 elements → ${Math.round(100 * C.convergence.HEX8R[1].ratio)}% of the correct deflection`, 380, 958, { size: 26, color: PAL.ink2, alpha: nA * seg(t, at('t5', 'twice too large'), 0.5) });
      }
      // ---------------- t6: quadratic element bends (small inset) shown over the cantilevers
      // ---------------- t7: rules
      const rA = env(t, t7 + 0.4, ctx.duration, 0.6, 0.5);
      if (rA > 0) {
        ruleCard(d2, t, 1180, 250, 700, [
          { t: at('t7', 'quadratic tetrahedra'), kind: 'ok', text: 'Quadratic tets (TET10) when the geometry is too complex to sweep' },
          { t: at('t7', 'Use hexahedra'), kind: 'ok', text: 'Hexahedra where you can sweep or map: most accuracy per DOF' },
          { t: at('t7', "Don't use linear"), kind: 'no', text: 'No linear tets (TET4) for stress' },
          { t: at('t7', 'And with linear'), kind: 'warn', text: 'Linear hexes: enhanced formulation or ≥ 4 through the thickness; check hourglass energy' },
        ], { title: 'SOLID ELEMENT RULES', alpha: rA, lh: 118, size: 27 });
      }
    },
  };
}

// --------------------------------------------------------------------------- 2D helpers
function drawBendingTrue(d2, cx, cy, w, h, k, a) {
  if (a <= 0) return;
  const R = k > 0.01 ? 900 / k : 1e6; // radius of curvature of the axis
  const n = 6;
  const pts = (yo) => {
    const out = [];
    for (let i = 0; i <= 40; i++) {
      const s = (i / 40 - 0.5) * w;
      const th = s / R;
      const r = R - yo;
      out.push([cx + r * Math.sin(th), cy - (R - r * Math.cos(th)) + R - R]);
    }
    return out.map(([x, y]) => [x, y + 0]);
  };
  const map = (s, yo) => { const th = s / R; const r = R + yo; return [cx + r * Math.sin(th), cy + R - r * Math.cos(th) - yo + yo]; };
  // centre the arc: axis y0 = cy
  const P = (s, yo) => { const th = s / R; const r = R - yo; return [cx + r * Math.sin(th), cy + (R - r * Math.cos(th)) - yo * 0]; };
  const top = [], bot = [], mid = [];
  for (let i = 0; i <= 40; i++) {
    const s = (i / 40 - 0.5) * w;
    top.push(Pc(cx, cy, R, s, h / 2));
    bot.push(Pc(cx, cy, R, s, -h / 2));
    mid.push(Pc(cx, cy, R, s, 0));
  }
  d2.poly([...top, ...bot.slice().reverse()], { fill: rgba(PAL.steel, 0.12), alpha: a });
  d2.path(top, { color: PAL.ink, width: 3, alpha: a });
  d2.path(bot, { color: PAL.ink, width: 3, alpha: a });
  d2.path(mid, { color: PAL.ink3, width: 1.5, alpha: a, dash: [8, 6] });
  for (let j = 0; j <= n; j++) {
    const s = (j / n - 0.5) * w;
    const p1 = Pc(cx, cy, R, s, h / 2), p2 = Pc(cx, cy, R, s, -h / 2);
    d2.line(p1[0], p1[1], p2[0], p2[1], { color: j === 0 || j === n ? PAL.ink : rgba(PAL.ink2, 0.8), width: j === 0 || j === n ? 3 : 1.5, alpha: a });
  }
  // right-angle markers at a corner
  const s0 = 0.5 * w - w / n;
  const c = Pc(cx, cy, R, s0, h / 2);
  angMark(d2, c, Pc(cx, cy, R, s0 - 30, h / 2), Pc(cx, cy, R, s0, h / 2 - 30), PAL.green, a, '90°');
}
function Pc(cx, cy, R, s, yo) {
  // point at arc-length s along the axis, offset yo towards the centre of curvature (above)
  const th = s / R;
  const r = R - yo;
  return [cx + r * Math.sin(th), cy - R + r * Math.cos(th) + 0];
}
function angMark(d2, c, pa, pb, col, a, label) {
  const ua = [pa[0] - c[0], pa[1] - c[1]], ub = [pb[0] - c[0], pb[1] - c[1]];
  const la = Math.hypot(...ua), lb = Math.hypot(...ub);
  const a0 = Math.atan2(ua[1], ua[0]), a1 = Math.atan2(ub[1], ub[0]);
  let da = a1 - a0;
  while (da > Math.PI) da -= 2 * Math.PI;
  while (da < -Math.PI) da += 2 * Math.PI;
  const pts = [];
  for (let i = 0; i <= 20; i++) { const aa = a0 + (da * i) / 20; pts.push([c[0] + 26 * Math.cos(aa), c[1] + 26 * Math.sin(aa)]); }
  d2.path(pts, { color: col, width: 3, alpha: a });
  const am = a0 + da / 2;
  d2.text(label, c[0] + 52 * Math.cos(am), c[1] + 52 * Math.sin(am) + 8, { size: 24, weight: 800, color: col, align: 'center', alpha: a });
}
function drawBendingQ4(d2, cx, cy, w, h, k, a, gp) {
  if (a <= 0) return;
  const th = 0.28 * k; // rotation of the end faces
  const dx = (h / 2) * Math.tan(th);
  const c = [
    [cx - w / 2 + dx, cy - h / 2], [cx + w / 2 - dx, cy - h / 2], [cx + w / 2 + dx, cy + h / 2], [cx - w / 2 - dx, cy + h / 2],
  ];
  d2.poly(c, { fill: rgba(PAL.cyan, 0.12), stroke: PAL.cyan, width: 3, alpha: a });
  d2.line(cx - w / 2, cy, cx + w / 2, cy, { color: PAL.ink3, width: 1.5, dash: [8, 6], alpha: a });
  for (const p of c) d2.circle(p[0], p[1], 9, { fill: PAL.ink, alpha: a });
  if (gp > 0 && k > 0.2) {
    angMark(d2, c[1], [c[1][0] - 40, c[1][1]], [c[2][0], c[2][1]], PAL.red, a * gp, '≠ 90°');
    d2.text('γ ≠ 0 : spurious shear', cx, cy + h / 2 + 70, { size: 30, weight: 750, color: PAL.red, align: 'center', alpha: a * gp });
  }
}
function drawHourglassElement(d2, cx, cy, s, mode, a, gp) {
  if (a <= 0) return;
  const amp = 0.22 * s * mode;
  const base = [[-1, -1], [1, -1], [1, 1], [-1, 1]];
  const pts = base.map(([x, y]) => [cx + (x * s) / 2 + amp * x * y * 0.5 * -1 * 0 + amp * (x * y), cy - (y * s) / 2]);
  d2.poly(base.map(([x, y]) => [cx + (x * s) / 2, cy - (y * s) / 2]), { stroke: rgba(PAL.ink3, 0.6), width: 1.5, alpha: a });
  d2.poly(pts, { fill: rgba(PAL.amber, 0.14), stroke: PAL.amber, width: 3.5, alpha: a });
  for (const p of pts) d2.circle(p[0], p[1], 10, { fill: PAL.ink, alpha: a });
  d2.circle(cx, cy, 12, { fill: PAL.red, alpha: a * gp, glow: PAL.red });
  // the centre lines stay unstrained
  d2.line(cx - s / 2, cy, cx + s / 2, cy, { color: rgba(PAL.red, 0.6), width: 1.5, dash: [6, 6], alpha: a * gp });
  d2.line(cx, cy - s / 2, cx, cy + s / 2, { color: rgba(PAL.red, 0.6), width: 1.5, dash: [6, 6], alpha: a * gp });
}
function drawMesh2D(d2, hg, U, x0, y0, w, p, a, col, label) {
  if (a <= 0) return;
  const sc = w / hg.LX;
  let umax = 0;
  for (const u of U) umax = Math.max(umax, Math.abs(u[0]), Math.abs(u[1]));
  const ds = (0.22 * hg.LY / umax) * p;
  const P = hg.p.map(([x, y], i) => [x0 + (x + ds * U[i][0]) * sc, y0 + 160 - (y + ds * U[i][1]) * sc]);
  for (const q of hg.quads) d2.poly(q.map((n) => P[n]), { fill: rgba(col, 0.1), stroke: col, width: 1.6, alpha: a });
  d2.text(label, x0, y0 - 14, { size: 22, weight: 650, color: col, alpha: a });
}
