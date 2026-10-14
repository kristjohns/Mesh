// Local solid model of the wellhead used for the hot-spot stresses (hotspot.json): half model with
// the axial stress change under bending, drawn with a diverging colour map.
import * as THREE from 'three';
import { clamp } from '../engine/util.js';

// blue (compression) -> light grey -> red (tension), v in [-1, 1]
export function diverging(v) {
  v = clamp(v, -1, 1);
  const c0 = [0.23, 0.30, 0.75], c1 = [0.87, 0.87, 0.87], c2 = [0.71, 0.02, 0.15];
  const [a, b, u] = v < 0 ? [c1, c0, -v] : [c1, c2, v];
  return a.map((x, i) => x + (b[i] - x) * Math.pow(u, 0.85));
}
export function divergingCss(v, a = 1) {
  const c = diverging(v);
  return `rgba(${Math.round(c[0] * 255)},${Math.round(c[1] * 255)},${Math.round(c[2] * 255)},${a})`;
}

export function makeHotspotFE(surf, o = {}) {
  const X = surf.X;
  const nv = X.length / 3;
  const q = surf.quads;
  const nq = q.length / 4;
  const idx = [];
  const edges = [];
  const seen = new Set();
  for (let k = 0; k < nq; k++) {
    const a = q[4 * k], b = q[4 * k + 1], c = q[4 * k + 2], d = q[4 * k + 3];
    idx.push(a, b, c, a, c, d);
    for (const [i, j] of [[a, b], [b, c], [c, d], [d, a]]) {
      const key = i < j ? i * 1e6 + j : j * 1e6 + i;
      if (!seen.has(key)) { seen.add(key); edges.push(i, j); }
    }
  }
  const pos = new Float32Array(nv * 3);
  for (let i = 0; i < nv; i++) {
    pos[3 * i] = X[3 * i];
    pos[3 * i + 1] = X[3 * i + 2];
    pos[3 * i + 2] = -X[3 * i + 1];
  }
  const col = new Float32Array(nv * 3);
  const vmax = o.vmax ?? 40;
  for (let i = 0; i < nv; i++) {
    const c = diverging(surf.szz[i] / vmax);
    col[3 * i] = c[0] * c[0]; col[3 * i + 1] = c[1] * c[1]; col[3 * i + 2] = c[2] * c[2];
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  g.setAttribute('color', new THREE.BufferAttribute(col, 3));
  g.setIndex(idx);
  g.computeVertexNormals();
  const mat = new THREE.MeshStandardMaterial({ vertexColors: true, metalness: 0.05, roughness: 0.62, side: THREE.DoubleSide,
    polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1, envMap: o.env ?? null, envMapIntensity: 0.25 });
  mat.toneMapped = false;
  const mesh = new THREE.Mesh(g, mat);
  const eg = new THREE.BufferGeometry();
  eg.setAttribute('position', g.attributes.position);
  eg.setIndex(edges);
  const emat = new THREE.LineBasicMaterial({ color: o.edgeColor ?? 0x0b1a26, transparent: true, opacity: o.edgeOpacity ?? 0.45 });
  const lines = new THREE.LineSegments(eg, emat);
  const grp = new THREE.Group();
  grp.add(mesh, lines);
  grp.userData = { mesh, lines, mat, emat };
  return grp;
}

// 2D section of the profile mesh (r, z) with per-quad values, drawn on the canvas
export function drawProfile(d2, prof, vals, o) {
  const { x0, y0, s } = o;
  const a = o.alpha ?? 1;
  if (a <= 0) return;
  const pts = prof.pts;
  const vmax = o.vmax ?? 40;
  const g = d2.g;
  g.save();
  g.globalAlpha = a;
  if (o.clip) { g.beginPath(); g.rect(...o.clip); g.clip(); }
  prof.quads.forEach((qd, k) => {
    const P = qd.map((n) => [x0 + (o.flip ? -1 : 1) * pts[n][0] * s, y0 - pts[n][1] * s]);
    const xs = P.map((p) => p[0]), ys = P.map((p) => p[1]);
    if (o.clip && (Math.max(...xs) < o.clip[0] || Math.min(...xs) > o.clip[0] + o.clip[2] || Math.max(...ys) < o.clip[1] || Math.min(...ys) > o.clip[1] + o.clip[3])) return;
    g.beginPath();
    g.moveTo(P[0][0], P[0][1]);
    for (let i = 1; i < 4; i++) g.lineTo(P[i][0], P[i][1]);
    g.closePath();
    const body = prof.body[k];
    g.fillStyle = vals && body !== 'cement' ? divergingCss(vals[k] / vmax) : body === 'cement' ? 'rgba(150,145,130,0.55)' : (o.fill ?? 'rgba(160,180,200,0.3)');
    g.fill();
    if (o.edges !== false) { g.strokeStyle = o.edgeColor ?? 'rgba(6,16,26,0.55)'; g.lineWidth = o.edgeW ?? 0.8; g.stroke(); }
  });
  g.restore();
}

// colour bar for the diverging map
export function divBar(d2, x, y, w, h, vmax, label, o = {}) {
  const a = o.alpha ?? 1;
  if (a <= 0.001) return;
  const g = d2.g;
  g.save();
  g.globalAlpha = a;
  const grad = g.createLinearGradient(x, y + h, x, y);
  for (let i = 0; i <= 10; i++) grad.addColorStop(i / 10, divergingCss(-1 + (2 * i) / 10));
  g.fillStyle = grad;
  g.fillRect(x, y, w, h);
  g.strokeStyle = 'rgba(200,220,235,0.6)';
  g.strokeRect(x, y, w, h);
  g.restore();
  for (let i = 0; i <= 4; i++) {
    const v = -vmax + (2 * vmax * i) / 4;
    d2.text((v > 0 ? '+' : '') + v.toFixed(0), x + w + 10, y + h - (h * i) / 4 + 7, { size: 18, color: '#a7bccd', alpha: a });
  }
  d2.text(label, x, y - 16, { size: 20, weight: 650, color: '#eaf2f8', alpha: a });
}
