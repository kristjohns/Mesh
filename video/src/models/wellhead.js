// Wellhead stack: conductor, conductor housing (LPWH), surface casing, cement, HPWHH, lock ring.
// Units: metres. Three.js Y = elevation above mudline. Axis of the well = local Y axis.
import * as THREE from 'three';
import { latheGeometry, capGeometry, hatchTexture, capUV } from './lathe.js';

export const DIM = {
  rBore: 0.2381, rCasO: 0.254, rHpO: 0.345, rRing: 0.400, rLpLowI: 0.356, rLpBore: 0.405,
  rGroove: 0.430, rLpO: 0.480, rLpGuide: 0.530, rCondI: 0.4191, rCondO: 0.4572,
  zCondTop: 0.8, zLpTaper: 1.1, zCasTop: 1.2, zHpTaper: 1.5, zShoulder: 2.2, zRingTop: 2.45,
  zGrooveTop: 2.52, zLpTop: 2.6, zHpTop: 3.6, zToc: 0.0,
};
const D = DIM;

export function profiles(zb = -12) {
  const h4 = [];
  // H-4 mandrel profile: a series of locking grooves near the top of the HPWHH
  let z = 3.08;
  h4.push([0.345, 3.05], [0.362, z]);
  for (let i = 0; i < 6; i++) {
    h4.push([0.362, z + 0.022], [0.349, z + 0.04], [0.349, z + 0.05], [0.362, z + 0.062]);
    z += 0.062;
  }
  h4.push([0.362, 3.55], [0.336, 3.6]);
  return {
    conductor: [[D.rCondI, zb], [D.rCondO, zb], [D.rCondO, D.zCondTop], [D.rCondI, D.zCondTop]],
    casing: [[D.rBore, zb], [D.rCasO, zb], [D.rCasO, D.zCasTop], [D.rBore, D.zCasTop]],
    cement: [[D.rCasO, zb], [D.rCondI, zb], [D.rCondI, D.zToc], [D.rCasO, D.zToc]],
    lpwh: [
      [D.rCondI, 0.80], [D.rCondO, 0.80], [D.rCondO, 0.84], [D.rLpO, 1.10], [D.rLpO, 1.84], [0.495, 1.86],
      [D.rLpGuide, 1.88], [D.rLpGuide, 2.02], [0.495, 2.04], [D.rLpO, 2.06], [D.rLpO, 2.56], [0.465, 2.60],
      [0.418, 2.60], [D.rLpBore, 2.587], [D.rLpBore, D.zGrooveTop], [D.rGroove, D.zGrooveTop],
      [D.rGroove, D.zRingTop], [D.rLpBore, D.zRingTop], [D.rLpBore, D.zShoulder], [D.rLpLowI, D.zShoulder],
      [D.rLpLowI, 1.10], [D.rCondI, 0.84],
    ],
    hpwhh: [
      [D.rBore, 1.20], [D.rCasO, 1.20], [D.rCasO, 1.24], [D.rHpO, D.zHpTaper], [D.rHpO, D.zShoulder],
      [D.rRing, D.zShoulder], [D.rRing, 2.43], [0.390, D.zRingTop], [D.rHpO, D.zRingTop],
      ...h4, [0.27, 3.6], [D.rBore, 3.57],
    ],
    lockring: [[0.372, D.zRingTop], [0.428, D.zRingTop], [0.428, D.zGrooveTop - 0.003], [0.372, D.zGrooveTop - 0.003]],
  };
}

const COLORS = {
  conductor: 0x8e9aa5, casing: 0xa9b3bb, cement: 0x8f8d86, lpwh: 0x9fabb6, hpwhh: 0xd2d9df, lockring: 0x4a525a,
};
const CAPCOL = {
  conductor: ['#b3c4d2', '#55697b'], casing: ['#d2dbe2', '#6f7f8c'], cement: ['#d8ccb0', '#a39578'],
  lpwh: ['#b8d0e4', '#4a6884'], hpwhh: ['#f1f6fa', '#8aa3b8'], lockring: ['#a3d9b8', '#2f5a44'],
};

export function makeWellhead(env, o = {}) {
  const zb = o.zBottom ?? -12;
  const P = profiles(zb);
  const grp = new THREE.Group();
  grp.userData.parts = {};
  const clip = o.clipPlanes ?? [];
  for (const [name, prof] of Object.entries(P)) {
    if (o.only && !o.only.includes(name)) continue;
    const isSteel = name !== 'cement';
    const mat = new THREE.MeshStandardMaterial({
      color: COLORS[name], metalness: isSteel ? 0.85 : 0.0, roughness: isSteel ? (name === 'hpwhh' ? 0.24 : 0.34) : 0.95,
      envMap: env, envMapIntensity: o.envIntensity ?? 1.0, clippingPlanes: clip, clipShadows: true, side: THREE.DoubleSide,
    });
    const geo = latheGeometry(prof, { segments: o.segments ?? 128 });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    const part = new THREE.Group();
    part.add(mesh);
    part.name = name;
    // section cap (shown when clipping is active)
    const cg = capUV(capGeometry(prof), o.capScale ?? 3.2);
    const [fg, bgc] = CAPCOL[name];
    const capMat = new THREE.MeshStandardMaterial({
      map: hatchTexture(fg, bgc, name === 'cement' ? 22 : 14, name === 'hpwhh' || name === 'casing' ? -45 : 45), metalness: 0.05, roughness: 0.75,
      side: THREE.DoubleSide, envMap: env, envMapIntensity: 0.25, emissive: 0x0b1620, polygonOffset: true, polygonOffsetFactor: -1,
    });
    const cap = new THREE.Mesh(cg, capMat);
    cap.visible = false;
    part.add(cap);
    part.userData = { mesh, cap, mat, capMat, profile: prof };
    grp.add(part);
    grp.userData.parts[name] = part;
  }
  // weld beads (visual): conductor/LPWH at z=0.8 and casing/HPWHH at z=1.2
  if (!o.only) {
    const weldMat = new THREE.MeshStandardMaterial({ color: 0x6d6a63, metalness: 0.6, roughness: 0.6, envMap: env, clippingPlanes: clip });
    const w1 = new THREE.Mesh(new THREE.TorusGeometry(D.rCondO + 0.004, 0.012, 8, 96), weldMat);
    w1.rotation.x = Math.PI / 2; w1.position.y = 0.8;
    const w2 = new THREE.Mesh(new THREE.TorusGeometry(D.rCasO + 0.003, 0.009, 8, 96), weldMat);
    w2.rotation.x = Math.PI / 2; w2.position.y = 1.2;
    grp.add(w1, w2);
    grp.userData.welds = [w1, w2];
    // cement return ports on the LPWH (dark dots)
    const portMat = new THREE.MeshStandardMaterial({ color: 0x1b1f22, roughness: 0.8, clippingPlanes: clip });
    for (let k = 0; k < 6; k++) {
      const a = (k / 6) * Math.PI * 2 + 0.3;
      const port = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, 0.02, 20), portMat);
      port.rotation.z = Math.PI / 2;
      port.rotation.y = -a + Math.PI / 2;
      port.position.set(Math.sin(a) * (D.rLpO + 0.003), 1.45, Math.cos(a) * (D.rLpO + 0.003));
      grp.userData.parts.lpwh.add(port);
    }
  }
  grp.userData.setCut = (on) => {
    for (const p of Object.values(grp.userData.parts)) p.userData.cap.visible = on;
  };
  return grp;
}

// ----------------------------------------------------------------------------------------- BOP
function cyl(r, h, mat, seg = 32) {
  const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, h, seg), mat);
  m.castShadow = true; m.receiveShadow = true;
  return m;
}
function box(w, h, d, mat) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
  m.castShadow = true; m.receiveShadow = true;
  return m;
}
function tubeBetween(a, b, r, mat) {
  const va = new THREE.Vector3(...a), vb = new THREE.Vector3(...b);
  const L = va.distanceTo(vb);
  const m = cyl(r, L, mat, 16);
  m.position.copy(va).add(vb).multiplyScalar(0.5);
  m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), vb.clone().sub(va).normalize());
  return m;
}

export function makeBOP(M, o = {}) {
  const g = new THREE.Group();
  const z0 = 3.0;
  // H-4 wellhead connector over the HPWHH hub
  const con = cyl(0.82, 1.7, M.black, 48); con.position.y = z0 + 0.85; g.add(con);
  for (let k = 0; k < 10; k++) {
    const a = (k / 10) * Math.PI * 2;
    const hc = cyl(0.09, 1.2, M.steelDark, 12);
    hc.position.set(Math.sin(a) * 0.88, z0 + 0.95, Math.cos(a) * 0.88);
    g.add(hc);
  }
  let z = z0 + 1.7;
  // ram cavities
  const ramH = [0.95, 0.95, 0.95, 0.95];
  ramH.forEach((h, i) => {
    const body = box(1.7, h, 1.5, i % 2 ? M.grey : M.black);
    body.position.y = z + h / 2;
    g.add(body);
    for (const s of [-1, 1]) {
      const bon = cyl(0.42, 0.9, M.black, 32);
      bon.rotation.z = Math.PI / 2;
      bon.position.set(s * 1.3, z + h / 2, 0);
      g.add(bon);
      const op = cyl(0.3, 0.55, M.steelDark, 24);
      op.rotation.z = Math.PI / 2;
      op.position.set(s * 2.0, z + h / 2, 0);
      g.add(op);
    }
    z += h + 0.05;
  });
  // lower annular
  const ann = new THREE.Mesh(latheGeometry([[0, z], [1.05, z], [1.1, z + 0.5], [0.95, z + 1.0], [0.6, z + 1.25], [0, z + 1.25]], { segments: 48, closed: true }), M.black);
  ann.castShadow = true;
  g.add(ann);
  z += 1.25;
  // LMRP connector
  const lmrp = cyl(0.8, 1.0, M.grey, 48); lmrp.position.y = z + 0.5; g.add(lmrp);
  z += 1.0;
  const ann2 = new THREE.Mesh(latheGeometry([[0, z], [1.0, z], [1.05, z + 0.45], [0.9, z + 0.9], [0.55, z + 1.1], [0, z + 1.1]], { segments: 48 }), M.black);
  g.add(ann2);
  z += 1.1;
  // flex joint + riser adapter
  const fj = new THREE.Mesh(new THREE.SphereGeometry(0.55, 32, 16), M.steelDark); fj.position.y = z + 0.35; g.add(fj);
  const adp = cyl(0.36, 1.0, M.steel, 32); adp.position.y = z + 1.1; g.add(adp);
  g.userData.zFlex = z + 0.35;
  z += 1.6;
  // riser to the surface
  const rz = o.riserTop ?? 120;
  const riser = cyl(0.27, rz - z, M.steel, 24); riser.position.y = (rz + z) / 2; g.add(riser);
  for (let zz = z + 8; zz < rz; zz += 4.8) {
    const bm = cyl(0.62, 4.4, M.yellowDirty ?? M.yellow, 32); bm.position.y = zz + 2.2; g.add(bm);
  }
  // choke and kill lines
  for (const s of [-1, 1]) g.add(tubeBetween([s * 0.42, z, 0.0], [s * 0.42, rz, 0], 0.06, M.steelDark));
  // frame
  const fm = M.red;
  const zt = g.userData.zFlex - 0.3;
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) {
    g.add(tubeBetween([sx * 1.75, z0 + 1.0, sz * 1.75], [sx * 1.75, zt, sz * 1.75], 0.11, fm));
  }
  for (const zz of [z0 + 1.1, z0 + 3.8, zt]) {
    for (const [a, b] of [[[-1, -1], [1, -1]], [[1, -1], [1, 1]], [[1, 1], [-1, 1]], [[-1, 1], [-1, -1]]]) {
      g.add(tubeBetween([a[0] * 1.75, zz, a[1] * 1.75], [b[0] * 1.75, zz, b[1] * 1.75], 0.08, fm));
    }
  }
  // accumulator bottles
  for (let k = 0; k < 6; k++) {
    const b = cyl(0.22, 1.9, M.yellow, 20);
    b.position.set(-1.45 + k * 0.58, z0 + 6.2, 1.95);
    g.add(b);
    const b2 = cyl(0.22, 1.9, M.yellow, 20);
    b2.position.set(-1.45 + k * 0.58, z0 + 6.2, -1.95);
    g.add(b2);
  }
  // control pods
  for (const s of [-1, 1]) {
    const pod = box(0.9, 1.4, 0.9, M.orange ?? M.yellow);
    pod.position.set(s * 2.1, zt - 1.2, 0.9 * s);
    g.add(pod);
  }
  g.userData.height = zt - z0;
  return g;
}

// ----------------------------------------------------------------------------------------- XT
export function makeXT(M, o = {}) {
  const g = new THREE.Group();
  const z0 = 3.0;
  const con = cyl(0.72, 1.2, M.black, 40); con.position.y = z0 + 0.6; g.add(con);
  const body = box(1.1, 1.5, 1.1, M.white); body.position.y = z0 + 1.95; g.add(body);
  const cap = cyl(0.42, 0.6, M.yellow, 32); cap.position.y = z0 + 3.0; g.add(cap);
  // wing block and flowline towards the manifold (local -x)
  const wing = box(1.2, 0.6, 0.6, M.white); wing.position.set(-1.0, z0 + 2.0, 0); g.add(wing);
  for (let k = 0; k < 2; k++) {
    const act = cyl(0.2, 0.7, M.yellow, 20); act.position.set(-0.75 - k * 0.5, z0 + 2.65, 0); g.add(act);
  }
  const fl = tubeBetween([-1.6, z0 + 2.0, 0], [-2.6, z0 + 2.0, 0], 0.13, M.steel); g.add(fl);
  // frame
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) {
    g.add(tubeBetween([sx * 1.35, z0 + 0.3, sz * 1.35], [sx * 1.35, z0 + 3.4, sz * 1.35], 0.07, M.yellow));
  }
  for (const zz of [z0 + 0.35, z0 + 3.4]) {
    for (const [a, b] of [[[-1, -1], [1, -1]], [[1, -1], [1, 1]], [[1, 1], [-1, 1]], [[-1, 1], [-1, -1]]]) {
      g.add(tubeBetween([a[0] * 1.35, zz, a[1] * 1.35], [b[0] * 1.35, zz, b[1] * 1.35], 0.06, M.yellow));
    }
  }
  const panel = box(0.9, 0.9, 0.05, M.orange ?? M.yellow); panel.position.set(0, z0 + 1.6, 1.36); g.add(panel);
  return g;
}

export { cyl, box, tubeBetween };
