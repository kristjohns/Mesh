// Local solid FE model of the wellhead (half model) from wellhead_surface.json.
import * as THREE from 'three';
import { turbo } from '../engine/util.js';

export function makeLocalFE(surf, o = {}) {
  const X = surf.X;
  const nv = X.length / 3;
  const q = surf.quads;
  const nq = q.length / 4;
  const body = surf.quad_body;
  const keep = o.bodies ?? null; // optional list of bodies to include
  const idx = [];
  const edgeSet = new Set();
  const edges = [];
  for (let k = 0; k < nq; k++) {
    if (keep && !keep.includes(body[k])) continue;
    const a = q[4 * k], b = q[4 * k + 1], c = q[4 * k + 2], d = q[4 * k + 3];
    idx.push(a, b, c, a, c, d);
    for (const [i, j] of [[a, b], [b, c], [c, d], [d, a]]) {
      const key = i < j ? i * 1e6 + j : j * 1e6 + i;
      if (!edgeSet.has(key)) { edgeSet.add(key); edges.push(i, j); }
    }
  }
  // three.js coordinates: x -> x, z(up) -> y, y -> -z
  const base = new Float32Array(nv * 3);
  for (let i = 0; i < nv; i++) {
    base[3 * i] = X[3 * i];
    base[3 * i + 1] = X[3 * i + 2];
    base[3 * i + 2] = -X[3 * i + 1];
  }
  const pos = new Float32Array(base);
  const col = new Float32Array(nv * 3);
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  g.setAttribute('color', new THREE.BufferAttribute(col, 3));
  g.setIndex(idx);
  g.computeVertexNormals();
  const mat = new THREE.MeshStandardMaterial({ vertexColors: true, metalness: 0.05, roughness: 0.6, side: THREE.DoubleSide,
    polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1, envMap: o.env ?? null, envMapIntensity: 0.25 });
  const mesh = new THREE.Mesh(g, mat);
  const eg = new THREE.BufferGeometry();
  eg.setAttribute('position', g.attributes.position);
  eg.setIndex(edges);
  const emat = new THREE.LineBasicMaterial({ color: o.edgeColor ?? 0x0b1a26, transparent: true, opacity: o.edgeOpacity ?? 0.55 });
  const lines = new THREE.LineSegments(eg, emat);
  const grp = new THREE.Group();
  grp.add(mesh, lines);
  const states = surf.states;
  const vmax = o.vmax ?? 250, vmin = o.vmin ?? 0;
  grp.userData = {
    mesh, lines, mat, emat, states, M: surf.M,
    // s: fractional state index; scale: displacement magnification; colorMode: 'vm' | 'solid'
    set(s, scale = 0, colorMode = 'vm', solid = [0.72, 0.78, 0.83]) {
      const n = states.length;
      s = Math.max(0, Math.min(n - 1, s));
      const i0 = Math.floor(s), i1 = Math.min(n - 1, i0 + 1), f = s - i0;
      const A = states[i0], B = states[i1];
      for (let i = 0; i < nv; i++) {
        const ux = A.u[3 * i] * (1 - f) + B.u[3 * i] * f;
        const uy = A.u[3 * i + 1] * (1 - f) + B.u[3 * i + 1] * f;
        const uz = A.u[3 * i + 2] * (1 - f) + B.u[3 * i + 2] * f;
        pos[3 * i] = base[3 * i] + scale * ux;
        pos[3 * i + 1] = base[3 * i + 1] + scale * uz;
        pos[3 * i + 2] = base[3 * i + 2] - scale * uy;
        if (colorMode === 'vm') {
          const v = A.vm[i] * (1 - f) + B.vm[i] * f;
          const c = turbo((v - vmin) / (vmax - vmin));
          col[3 * i] = c[0] * c[0]; col[3 * i + 1] = c[1] * c[1]; col[3 * i + 2] = c[2] * c[2];
        } else {
          col[3 * i] = solid[0]; col[3 * i + 1] = solid[1]; col[3 * i + 2] = solid[2];
        }
      }
      g.attributes.position.needsUpdate = true;
      g.attributes.color.needsUpdate = true;
      if (scale > 0) g.computeVertexNormals();
    },
  };
  grp.userData.set(0, 0);
  return grp;
}

// colour bar drawn on the 2D layer
export function colorBar(d2, x, y, w, h, vmin, vmax, label, o = {}) {
  const a = o.alpha ?? 1;
  if (a <= 0.001) return;
  const g = d2.g;
  g.save();
  g.globalAlpha = a;
  const grad = g.createLinearGradient(x, y + h, x, y);
  for (let i = 0; i <= 10; i++) {
    const c = turbo(i / 10);
    grad.addColorStop(i / 10, `rgb(${Math.round(c[0] * 255)},${Math.round(c[1] * 255)},${Math.round(c[2] * 255)})`);
  }
  g.fillStyle = grad;
  g.fillRect(x, y, w, h);
  g.strokeStyle = 'rgba(200,220,235,0.6)';
  g.strokeRect(x, y, w, h);
  g.restore();
  const ticks = o.ticks ?? 5;
  for (let i = 0; i <= ticks; i++) {
    const v = vmin + ((vmax - vmin) * i) / ticks;
    const yy = y + h - (h * i) / ticks;
    d2.text(o.fmt ? o.fmt(v) : v.toFixed(0), x + w + 10, yy + 7, { size: 18, color: '#a7bccd', alpha: a });
  }
  d2.text(label, x, y - 16, { size: 20, weight: 650, color: '#eaf2f8', alpha: a });
}
