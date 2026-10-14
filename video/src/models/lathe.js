// Lathe geometry with sharp profile corners and matching section caps.
import * as THREE from 'three';

// profile: array of [r, z] (closed polygon, CCW in r-z plane). Returns BufferGeometry revolved
// around the Y axis (three.js up). Sharp corners where the turn angle exceeds `sharpDeg`.
export function latheGeometry(profile, o = {}) {
  const segs = o.segments ?? 96;
  const phi0 = o.phiStart ?? 0, phiL = o.phiLength ?? Math.PI * 2;
  const sharp = Math.cos(((o.sharpDeg ?? 28) * Math.PI) / 180);
  const n = profile.length;
  const closed = o.closed ?? true;
  const pos = [], nor = [], idx = [];
  const segN = (i) => {
    const a = profile[i], b = profile[(i + 1) % n];
    const dr = b[0] - a[0], dz = b[1] - a[1];
    const L = Math.hypot(dr, dz) || 1;
    // outward normal for CCW polygon in (r,z): rotate tangent by -90deg -> (dz, -dr)
    return [dz / L, -dr / L];
  };
  const nseg = closed ? n : n - 1;
  for (let s = 0; s < nseg; s++) {
    const a = profile[s], b = profile[(s + 1) % n];
    if (Math.hypot(b[0] - a[0], b[1] - a[1]) < 1e-9) continue;
    const ns = segN(s);
    const prev = segN((s - 1 + n) % n), next = segN((s + 1) % n);
    const avg = (p, q) => { const x = p[0] + q[0], y = p[1] + q[1]; const L = Math.hypot(x, y) || 1; return [x / L, y / L]; };
    const dot = (p, q) => p[0] * q[0] + p[1] * q[1];
    const na = (s > 0 || closed) && dot(prev, ns) > sharp ? avg(prev, ns) : ns;
    const nb = ((s + 1) % n !== 0 || closed) && dot(next, ns) > sharp ? avg(next, ns) : ns;
    const base = pos.length / 3;
    for (let k = 0; k <= segs; k++) {
      const phi = phi0 + (phiL * k) / segs;
      const c = Math.cos(phi), si = Math.sin(phi);
      pos.push(a[0] * si, a[1], a[0] * c, b[0] * si, b[1], b[0] * c);
      nor.push(na[0] * si, na[1], na[0] * c, nb[0] * si, nb[1], nb[0] * c);
    }
    for (let k = 0; k < segs; k++) {
      const i0 = base + 2 * k, i1 = i0 + 1, i2 = i0 + 2, i3 = i0 + 3;
      idx.push(i0, i2, i1, i1, i2, i3);
    }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('normal', new THREE.Float32BufferAttribute(nor, 3));
  g.setIndex(idx);
  return g;
}

// Section cap: the profile polygon on both sides of the axis, lying in the plane x=0 (three.js),
// i.e. the plane containing the axis and the z (three) direction. Returns geometry in that plane.
export function capGeometry(profile) {
  const shape = new THREE.Shape(profile.map(([r, z]) => new THREE.Vector2(r, z)));
  const g1 = new THREE.ShapeGeometry(shape);
  const g2 = g1.clone();
  g2.scale(-1, 1, 1);
  // ShapeGeometry lies in XY plane; we want the section in the plane spanned by three-Z (radial) and Y.
  const merged = mergeTwo(g1, g2);
  merged.rotateY(-Math.PI / 2); // map shape x -> three z (towards +z)
  return merged;
}

function mergeTwo(a, b) {
  const pa = a.attributes.position.array, pb = b.attributes.position.array;
  const pos = new Float32Array(pa.length + pb.length);
  pos.set(pa, 0);
  pos.set(pb, pa.length);
  const ia = a.index.array, ib = b.index.array;
  const off = pa.length / 3;
  const idx = [];
  for (let i = 0; i < ia.length; i++) idx.push(ia[i]);
  // mirrored copy has reversed winding: flip
  for (let i = 0; i < ib.length; i += 3) idx.push(ib[i] + off, ib[i + 2] + off, ib[i + 1] + off);
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  g.setIndex(idx);
  g.computeVertexNormals();
  return g;
}

// hatch texture for section caps (engineering drawing style)
const _hatch = {};
export function hatchTexture(color = '#cfd8df', bg = '#8d99a3', spacing = 10, angle = 45) {
  const key = color + bg + spacing + angle;
  if (_hatch[key]) return _hatch[key];
  const c = document.createElement('canvas');
  c.width = c.height = 128;
  const g = c.getContext('2d');
  g.fillStyle = bg;
  g.fillRect(0, 0, 128, 128);
  g.strokeStyle = color;
  g.lineWidth = 2;
  g.save();
  g.translate(64, 64);
  g.rotate((angle * Math.PI) / 180);
  for (let x = -200; x < 200; x += spacing) { g.beginPath(); g.moveTo(x, -200); g.lineTo(x, 200); g.stroke(); }
  g.restore();
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.colorSpace = THREE.SRGBColorSpace;
  _hatch[key] = t;
  return t;
}

// planar UVs for a cap geometry (in the plane x=0 -> use z,y)
export function capUV(g, scale = 8) {
  const p = g.attributes.position;
  const uv = new Float32Array(p.count * 2);
  for (let i = 0; i < p.count; i++) { uv[2 * i] = p.getZ(i) * scale; uv[2 * i + 1] = p.getY(i) * scale; }
  g.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
  return g;
}
