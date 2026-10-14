// Subsea template built from the same frame data used for the stiffness analysis (template.json).
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { latheGeometry } from './lathe.js';
import { cyl, box, tubeBetween } from './wellhead.js';
import { fatLines } from '../engine/env.js';

export const toThree = (x, y, z) => [x, z, -y];

function memberGeometry(a, b, sec) {
  const va = new THREE.Vector3(...a), vb = new THREE.Vector3(...b);
  const L = va.distanceTo(vb);
  const dir = vb.clone().sub(va).normalize();
  let g;
  if (sec.kind === 'tube') {
    g = new THREE.CylinderGeometry(sec.dims[0] / 2, sec.dims[0] / 2, L, 20, 1, false);
    const q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
    g.applyQuaternion(q);
  } else {
    const [h, w] = sec.dims;
    g = new THREE.BoxGeometry(L, h, w);
    // local x along member; keep box "height" vertical where possible
    const up = Math.abs(dir.y) > 0.95 ? new THREE.Vector3(1, 0, 0) : new THREE.Vector3(0, 1, 0);
    const zAx = new THREE.Vector3().crossVectors(dir, up).normalize();
    const yAx = new THREE.Vector3().crossVectors(zAx, dir).normalize();
    const m = new THREE.Matrix4().makeBasis(dir, yAx, zAx);
    g.applyMatrix4(m);
  }
  g.translate((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2);
  return g;
}

function gratingTexture() {
  const c = document.createElement('canvas');
  c.width = c.height = 128;
  const g = c.getContext('2d');
  g.clearRect(0, 0, 128, 128);
  g.fillStyle = '#ffffff';
  for (let i = 0; i < 128; i += 16) { g.fillRect(i, 0, 4, 128); }
  for (let j = 0; j < 128; j += 32) { g.fillRect(0, j, 128, 3); }
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  return t;
}

export function makeTemplate(data, M, env, o = {}) {
  const grp = new THREE.Group();
  const nodes = data.nodes.map(([x, y, z]) => toThree(x, y, z));
  const byGroup = {};
  for (const m of data.members) {
    const sec = data.sections[m.sec];
    const g = memberGeometry(nodes[m.a], nodes[m.b], sec);
    (byGroup[m.group] ??= []).push(g);
  }
  const frameMat = o.frameMat ?? M.yellow;
  const frame = new THREE.Group();
  for (const [k, gs] of Object.entries(byGroup)) {
    const mesh = new THREE.Mesh(mergeGeometries(gs), frameMat);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    mesh.name = k;
    frame.add(mesh);
  }
  grp.add(frame);
  grp.userData.frame = frame;
  // suction anchors
  const anchors = new THREE.Group();
  for (const a of data.anchors) {
    const [x, , z] = toThree(a.x, a.y, 0);
    const skirt = new THREE.Mesh(new THREE.CylinderGeometry(2.5, 2.5, 9.8, 48, 1, true), o.anchorMat ?? M.yellowDirty);
    skirt.position.set(x, 0.8 - 4.9, z);
    skirt.castShadow = true; skirt.receiveShadow = true;
    const lid = cyl(2.55, 0.25, M.yellow, 48); lid.position.set(x, 0.85, z);
    const hatchA = cyl(0.55, 0.2, M.grey, 24); hatchA.position.set(x + 1.1, 1.05, z - 0.6);
    const pumpI = box(0.7, 0.5, 0.7, M.orange); pumpI.position.set(x - 0.9, 1.15, z + 0.7);
    const ring = new THREE.Mesh(new THREE.TorusGeometry(2.5, 0.08, 8, 64), M.yellow); ring.rotation.x = Math.PI / 2; ring.position.set(x, 0.72, z);
    anchors.add(skirt, lid, hatchA, pumpI, ring);
    // padeye
    const pe = box(0.12, 0.6, 0.5, M.yellow); pe.position.set(x, 1.25, z + 1.6); anchors.add(pe);
  }
  grp.add(anchors);
  grp.userData.anchors = anchors;
  // well-slot receptacles with guide funnels
  const recs = [];
  for (const s of data.slots) {
    const [x, , z] = toThree(s.x, s.y, 0);
    const prof = [[0.56, 1.74], [0.78, 1.74], [0.78, 2.16], [1.25, 2.62], [1.18, 2.66], [0.62, 2.2], [0.56, 2.2]];
    const rec = new THREE.Mesh(latheGeometry(prof, { segments: 64 }), M.yellow);
    rec.position.set(x, 0, z);
    rec.castShadow = true;
    grp.add(rec);
    recs.push(rec);
  }
  grp.userData.receptacles = recs;
  // roof hatches: cells of the roof grid
  const rx = [-7.5, -3.5, 3.5, 7.5], ry = [-6.5, -2.5, 2.5, 6.5];
  const hatches = [];
  for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) {
    const x0 = rx[i], x1 = rx[i + 1], y0 = ry[j], y1 = ry[j + 1];
    const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
    const hw = x1 - x0 - 0.35, hd = y1 - y0 - 0.35;
    const pivot = new THREE.Group();
    // hinge along the outer y edge
    const side = cy >= 0 ? 1 : -1;
    const [px, py, pz] = toThree(cx, side > 0 ? y1 - 0.15 : y0 + 0.15, 7.75);
    pivot.position.set(px, py, pz);
    const panel = new THREE.Group();
    const slab = box(hw, 0.12, hd, M.hatch);
    slab.position.set(0, 0, side > 0 ? hd / 2 : -hd / 2);
    panel.add(slab);
    for (let k = -1; k <= 1; k++) {
      const rib = box(hw, 0.18, 0.12, M.yellow);
      rib.position.set(0, 0.08, (side > 0 ? hd / 2 : -hd / 2) + k * hd * 0.33);
      panel.add(rib);
    }
    pivot.add(panel);
    pivot.userData = { side, cell: [i, j] };
    grp.add(pivot);
    hatches.push(pivot);
  }
  grp.userData.hatches = hatches;
  // sloped side grating panels
  const gt = gratingTexture();
  const gmat = new THREE.MeshStandardMaterial({ color: 0xc89a1a, metalness: 0.2, roughness: 0.6, alphaMap: gt, transparent: false, alphaTest: 0.5, side: THREE.DoubleSide, envMap: env, envMapIntensity: 0.5 });
  const slopes = new THREE.Group();
  const quad = (p0, p1, p2, p3, rep) => {
    const g = new THREE.BufferGeometry();
    const pts = [p0, p1, p2, p3].flat();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3));
    g.setAttribute('uv', new THREE.Float32BufferAttribute([0, 0, rep[0], 0, rep[0], rep[1], 0, rep[1]], 2));
    g.setIndex([0, 1, 2, 0, 2, 3]);
    g.computeVertexNormals();
    const m = new THREE.Mesh(g, gmat);
    m.castShadow = true;
    slopes.add(m);
  };
  const T = (x, y, z) => toThree(x, y, z);
  // long sides (y = +-)
  for (const sy of [1, -1]) {
    for (let i = 0; i < 3; i++) {
      quad(T(rx[i], 6.5 * sy, 7.5), T(rx[i + 1], 6.5 * sy, 7.5), T(rx[i + 1], 10 * sy, 1.0), T(rx[i], 10 * sy, 1.0), [3, 3]);
    }
  }
  for (const sx of [1, -1]) {
    for (let j = 0; j < 3; j++) {
      quad(T(7.5 * sx, ry[j], 7.5), T(7.5 * sx, ry[j + 1], 7.5), T(12 * sx, ry[j + 1], 1.0), T(12 * sx, ry[j], 1.0), [3, 3]);
    }
  }
  grp.add(slopes);
  grp.userData.slopes = slopes;
  // manifold in the centre bay
  const man = new THREE.Group();
  for (const sx of [-1, 1]) {
    man.add(tubeBetween(T(sx * 1.1, -5.5, 2.6), T(sx * 1.1, 5.5, 2.6), 0.22, M.steel));
    for (let k = -2; k <= 2; k++) {
      const vb = box(0.8, 0.8, 0.8, M.grey);
      const [x, y, z] = T(sx * 1.1, k * 2.2, 2.6);
      vb.position.set(x, y, z);
      man.add(vb);
      const act = cyl(0.22, 0.9, M.yellow, 20);
      act.position.set(x, y + 0.85, z);
      man.add(act);
    }
  }
  // branches to the four trees
  for (const s of data.slots) {
    const sx = Math.sign(s.x), sy = Math.sign(s.y);
    man.add(tubeBetween(T(sx * 1.1, sy * 4.5, 2.6), T(sx * 1.1, sy * 4.5, 5.0), 0.13, M.steel));
    man.add(tubeBetween(T(sx * 1.1, sy * 4.5, 5.0), T(s.x - sx * 2.6, s.y, 5.0), 0.13, M.steel));
  }
  // manifold frame
  for (const sx of [-1, 1]) for (const sy of [-1, 1]) man.add(tubeBetween(T(sx * 2.4, sy * 6.0, 1.0), T(sx * 2.4, sy * 6.0, 5.8), 0.12, M.yellow));
  for (const zz of [1.0, 5.8]) {
    man.add(tubeBetween(T(-2.4, -6, zz), T(-2.4, 6, zz), 0.1, M.yellow));
    man.add(tubeBetween(T(2.4, -6, zz), T(2.4, 6, zz), 0.1, M.yellow));
  }
  grp.add(man);
  grp.userData.manifold = man;
  return grp;
}

// beam-element view of the template: member centre lines and node dots
export function makeTemplateWire(data, o = {}) {
  const grp = new THREE.Group();
  const nodes = data.nodes.map(([x, y, z]) => toThree(x, y, z));
  const pos = [];
  for (const m of data.members) pos.push(...nodes[m.a], ...nodes[m.b]);
  const lines = fatLines(pos, { color: o.color ?? 0x4cc9f0, width: o.width ?? 2.2, clip: o.clip ?? [], opacity: o.opacity ?? 1 });
  const lm = lines.material;
  grp.add(lines);
  const pg = new THREE.BufferGeometry();
  pg.setAttribute('position', new THREE.Float32BufferAttribute(nodes.flat(), 3));
  const c = document.createElement('canvas');
  c.width = c.height = 32;
  const g = c.getContext('2d');
  g.fillStyle = '#fff'; g.beginPath(); g.arc(16, 16, 12, 0, Math.PI * 2); g.fill();
  const pm = new THREE.PointsMaterial({ size: o.nodeSize ?? 0.35, map: new THREE.CanvasTexture(c), transparent: true, alphaTest: 0.4, color: o.nodeColor ?? 0xeaf2f8, fog: false, clippingPlanes: o.clip ?? [] });
  grp.add(new THREE.Points(pg, pm));
  grp.userData = { lineMat: lm, pointMat: pm };
  return grp;
}
