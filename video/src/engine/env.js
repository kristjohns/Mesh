// Shared 3D environment pieces: materials, underwater ambience, seabed, particles, camera paths.
import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { rng, clamp, lerp, ease } from './util.js';

let _envTex = null;
export function envMap(renderer) {
  if (_envTex) return _envTex;
  const pm = new THREE.PMREMGenerator(renderer);
  _envTex = pm.fromScene(new RoomEnvironment(), 0.04).texture;
  pm.dispose();
  return _envTex;
}

export const uTime = { value: 0 };

export function materials(renderer) {
  const env = envMap(renderer);
  const std = (o) => new THREE.MeshStandardMaterial({ envMap: env, ...o });
  return {
    steel: std({ color: 0xb8c2ca, metalness: 0.85, roughness: 0.32, envMapIntensity: 1.0 }),
    steelDark: std({ color: 0x6f7a84, metalness: 0.8, roughness: 0.42 }),
    steelLight: std({ color: 0xd7dee4, metalness: 0.75, roughness: 0.28 }),
    housingHP: std({ color: 0xc9d1d8, metalness: 0.9, roughness: 0.26 }),
    housingLP: std({ color: 0x9aa6b1, metalness: 0.85, roughness: 0.36 }),
    yellow: std({ color: 0xe0a80c, metalness: 0.15, roughness: 0.55, envMapIntensity: 0.6 }),
    yellowDirty: std({ color: 0xb98d1d, metalness: 0.1, roughness: 0.7, envMapIntensity: 0.4 }),
    red: std({ color: 0xa8281f, metalness: 0.2, roughness: 0.5, envMapIntensity: 0.6 }),
    black: std({ color: 0x24282c, metalness: 0.5, roughness: 0.5 }),
    grey: std({ color: 0x5c656d, metalness: 0.4, roughness: 0.55 }),
    white: std({ color: 0xd9dcd8, metalness: 0.1, roughness: 0.6, envMapIntensity: 0.6 }),
    hatch: std({ color: 0x4c5a55, metalness: 0.1, roughness: 0.8, envMapIntensity: 0.4 }),
    cement: std({ color: 0x8d8c86, metalness: 0.0, roughness: 0.95, envMapIntensity: 0.3 }),
    orange: std({ color: 0xd8641c, metalness: 0.2, roughness: 0.5, envMapIntensity: 0.6 }),
  };
}

export function grimeAll(M) {
  addGrime(M.yellow, { strength: 0.32 });
  addGrime(M.yellowDirty, { strength: 0.4 });
  addGrime(M.red, { strength: 0.3 });
  addGrime(M.grey, { strength: 0.25 });
  addGrime(M.black, { strength: 0.2 });
  addGrime(M.white, { strength: 0.3 });
  addGrime(M.orange, { strength: 0.3 });
  addGrime(M.hatch, { strength: 0.3 });
  return M;
}

// ----------------------------------------------------------------------------- underwater
export function underwater(scene, o = {}) {
  const fogColor = new THREE.Color(o.fog ?? 0x0d3242);
  scene.fog = new THREE.FogExp2(fogColor, o.density ?? 0.022);
  scene.background = fogColor.clone();
  // gradient dome (unaffected by fog)
  const dome = new THREE.Mesh(
    new THREE.SphereGeometry(900, 32, 16),
    new THREE.ShaderMaterial({
      side: THREE.BackSide, depthWrite: false, fog: false,
      uniforms: { top: { value: new THREE.Color(o.top ?? 0x1f6f8b) }, bottom: { value: fogColor.clone().multiplyScalar(0.55) }, mid: { value: fogColor } },
      vertexShader: 'varying vec3 vp; void main(){ vp = normalize(position); gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.0);}',
      fragmentShader: `uniform vec3 top; uniform vec3 bottom; uniform vec3 mid; varying vec3 vp;
        void main(){ float h = vp.y; vec3 c = h>0.0 ? mix(mid, top, pow(clamp(h*1.2,0.0,1.0),0.75)) : mid;
        gl_FragColor = vec4(c,1.0);
        #include <colorspace_fragment>
        }`,
    }));
  dome.renderOrder = -10;
  scene.add(dome);
  const hemi = new THREE.HemisphereLight(o.sky ?? 0x8fd3ea, o.ground ?? 0x4a3d28, o.hemi ?? 1.15);
  scene.add(hemi);
  const sun = new THREE.DirectionalLight(o.sunColor ?? 0xd5f1ff, o.sun ?? 2.8);
  sun.position.set(20, 60, 15);
  sun.castShadow = o.shadows !== false;
  sun.shadow.mapSize.set(2048, 2048);
  const sc = sun.shadow.camera;
  sc.left = -30; sc.right = 30; sc.top = 30; sc.bottom = -30; sc.near = 1; sc.far = 150;
  sun.shadow.bias = -0.0004;
  sun.shadow.normalBias = 0.03;
  scene.add(sun);
  scene.add(sun.target);
  return { dome, hemi, sun, fogColor };
}

// procedural sand texture
function sandTexture(size = 512, seed = 3) {
  const c = document.createElement('canvas');
  c.width = c.height = size;
  const g = c.getContext('2d');
  const R = rng(seed);
  const img = g.createImageData(size, size);
  for (let i = 0; i < size * size; i++) {
    const v = 0.82 + 0.18 * R();
    img.data[4 * i] = 150 * v;
    img.data[4 * i + 1] = 138 * v;
    img.data[4 * i + 2] = 112 * v;
    img.data[4 * i + 3] = 255;
  }
  g.putImageData(img, 0, 0);
  // pebbles / blotches
  for (let i = 0; i < 900; i++) {
    const x = R() * size, y = R() * size, r = 0.6 + R() * 2.2;
    g.fillStyle = `rgba(${70 + R() * 60},${65 + R() * 50},${55 + R() * 40},${0.25 + R() * 0.4})`;
    g.beginPath(); g.arc(x, y, r, 0, Math.PI * 2); g.fill();
  }
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 4;
  return t;
}

// smooth value noise for terrain
function valueNoise2(seed) {
  const R = rng(seed);
  const N = 256;
  const tab = new Float32Array(N * N).map(() => R());
  const at = (i, j) => tab[((i % N + N) % N) * N + ((j % N + N) % N)];
  return (x, y) => {
    const i = Math.floor(x), j = Math.floor(y);
    const fx = x - i, fy = y - j;
    const sx = fx * fx * (3 - 2 * fx), sy = fy * fy * (3 - 2 * fy);
    return lerp(lerp(at(i, j), at(i + 1, j), sx), lerp(at(i, j + 1), at(i + 1, j + 1), sx), sy);
  };
}

export function seabed(scene, o = {}) {
  const size = o.size ?? 360;
  const seg = o.seg ?? 220;
  const geo = new THREE.PlaneGeometry(size, size, seg, seg);
  geo.rotateX(-Math.PI / 2);
  const n = valueNoise2(7);
  const pos = geo.attributes.position;
  const holes = o.holes ?? []; // [{x,z,r}] flatten near structures
  for (let i = 0; i < pos.count; i++) {
    const x = pos.getX(i), z = pos.getZ(i);
    let h = (n(x / 40, z / 40) - 0.5) * 1.6 + (n(x / 9 + 50, z / 9) - 0.5) * 0.35 + Math.sin(x * 0.9 + z * 0.35 + n(x / 5, z / 5) * 3) * 0.04;
    for (const hl of holes) {
      const d = Math.hypot(x - hl.x, z - hl.z);
      h *= smooth01((d - hl.r) / (hl.f ?? 8));
    }
    pos.setY(i, h);
  }
  geo.computeVertexNormals();
  const tex = sandTexture();
  tex.repeat.set(size / 6, size / 6);
  const mat = new THREE.MeshStandardMaterial({ map: tex, color: 0xb9ad92, roughness: 0.95, metalness: 0.0, envMapIntensity: 0.2 });
  mat.onBeforeCompile = (sh) => {
    sh.uniforms.uTime = uTime;
    sh.uniforms.uCaustic = { value: o.caustics ?? 0.5 };
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vWp;')
      .replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nvWp = (modelMatrix*vec4(transformed,1.0)).xyz;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', `#include <common>
      varying vec3 vWp; uniform float uTime; uniform float uCaustic;
      float caust(vec2 p, float t){
        float c = 0.0; vec2 q = p;
        for(int i=0;i<3;i++){
          q = vec2(q.x + 0.6*sin(q.y*1.3 + t*0.8 + float(i)), q.y + 0.6*cos(q.x*1.1 - t*0.6 + float(i)*1.7));
          c += 1.0/(1.0 + 18.0*abs(sin(q.x*1.7)*sin(q.y*1.7)));
        }
        return pow(c/3.0, 2.2);
      }`)
      .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
        float cs = caust(vWp.xz*0.45, uTime) * uCaustic;
        totalEmissiveRadiance += vec3(0.35,0.6,0.65) * cs * 0.55;`);
  };
  const m = new THREE.Mesh(geo, mat);
  m.receiveShadow = true;
  scene.add(m);
  return m;
}
function smooth01(x) { x = clamp(x); return x * x * (3 - 2 * x); }

// marine snow
export function particles(scene, o = {}) {
  const N = o.count ?? 2500;
  const box = o.box ?? [80, 40, 80];
  const ctr = o.center ?? [0, 10, 0];
  const R = rng(o.seed ?? 11);
  const base = new Float32Array(N * 3);
  const vel = new Float32Array(N * 3);
  for (let i = 0; i < N; i++) {
    base[3 * i] = (R() - 0.5) * box[0];
    base[3 * i + 1] = (R() - 0.5) * box[1];
    base[3 * i + 2] = (R() - 0.5) * box[2];
    vel[3 * i] = (R() - 0.5) * 0.25 + (o.drift ?? 0.15);
    vel[3 * i + 1] = -0.05 - R() * 0.12;
    vel[3 * i + 2] = (R() - 0.5) * 0.25;
  }
  const geo = new THREE.BufferGeometry();
  const pos = new Float32Array(N * 3);
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  const c = document.createElement('canvas');
  c.width = c.height = 64;
  const g = c.getContext('2d');
  const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  gr.addColorStop(0, 'rgba(255,255,255,1)');
  gr.addColorStop(0.35, 'rgba(255,255,255,0.45)');
  gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = gr;
  g.fillRect(0, 0, 64, 64);
  const mat = new THREE.PointsMaterial({ size: o.size ?? 0.09, map: new THREE.CanvasTexture(c), transparent: true, depthWrite: false,
    opacity: o.opacity ?? 0.7, color: o.color ?? 0xcfe8f0, blending: THREE.AdditiveBlending, sizeAttenuation: true });
  const pts = new THREE.Points(geo, mat);
  pts.frustumCulled = false;
  scene.add(pts);
  pts.userData.update = (t, center = ctr) => {
    for (let i = 0; i < N; i++) {
      for (let k = 0; k < 3; k++) {
        let v = base[3 * i + k] + vel[3 * i + k] * t;
        const L = box[k];
        v = ((v + L / 2) % L + L) % L - L / 2;
        pos[3 * i + k] = v + center[k];
      }
      pos[3 * i] += Math.sin(t * 0.7 + i) * 0.05;
    }
    geo.attributes.position.needsUpdate = true;
  };
  pts.userData.update(0);
  return pts;
}

// soft vertical light shafts
export function godRays(scene, o = {}) {
  const grp = new THREE.Group();
  const c = document.createElement('canvas');
  c.width = 64; c.height = 256;
  const g = c.getContext('2d');
  const gr = g.createLinearGradient(0, 0, 0, 256);
  gr.addColorStop(0, 'rgba(255,255,255,0.0)');
  gr.addColorStop(0.15, 'rgba(255,255,255,0.8)');
  gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = gr;
  g.fillRect(0, 0, 64, 256);
  const g2 = g.getImageData(0, 0, 64, 256);
  for (let y = 0; y < 256; y++) for (let x = 0; x < 64; x++) {
    const f = Math.sin((x / 63) * Math.PI);
    g2.data[4 * (y * 64 + x) + 3] *= f * f;
  }
  g.putImageData(g2, 0, 0);
  const tex = new THREE.CanvasTexture(c);
  const R = rng(o.seed ?? 5);
  const n = o.count ?? 9;
  for (let i = 0; i < n; i++) {
    const w = 3 + R() * 6, h = o.height ?? 90;
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false,
      blending: THREE.AdditiveBlending, opacity: (o.opacity ?? 0.08) * (0.5 + R()), color: o.color ?? 0x9fe3ff, fog: false, side: THREE.DoubleSide }));
    m.position.set((R() - 0.5) * (o.spread ?? 70), (o.y ?? 30) + R() * 10, (R() - 0.5) * (o.spread ?? 70));
    m.rotation.z = (R() - 0.5) * 0.35;
    m.userData.phase = R() * 6.28;
    grp.add(m);
  }
  scene.add(grp);
  grp.userData.update = (t, camera) => {
    grp.children.forEach((m) => {
      m.rotation.y = Math.atan2(camera.position.x - m.position.x, camera.position.z - m.position.z);
      m.material.opacity = m.material.userData.base ?? (m.material.userData.base = m.material.opacity);
      m.material.opacity = m.material.userData.base * (0.7 + 0.3 * Math.sin(t * 0.4 + m.userData.phase));
    });
  };
  return grp;
}

// ----------------------------------------------------------------------------- camera path
// keys: [{t, pos:[x,y,z], tgt:[x,y,z], fov}] ; segments eased in-out; optional per-key 'e'
export function cameraPath(camera, keysArr) {
  const P = new THREE.Vector3(), T = new THREE.Vector3();
  const orbitPos = (k) => {
    const c = k.center ?? [0, 0, 0];
    const [r, az, el] = k.orbit;
    const a = az * Math.PI / 180, e = el * Math.PI / 180;
    return [c[0] + r * Math.cos(e) * Math.sin(a), c[1] + r * Math.sin(e), c[2] + r * Math.cos(e) * Math.cos(a)];
  };
  for (const k of keysArr) if (k.orbit) { k.pos = orbitPos(k); k.tgt = k.center ?? [0, 0, 0]; }
  const f = (t) => {
    let k0 = keysArr[0], k1 = keysArr[keysArr.length - 1];
    if (t <= keysArr[0].t) k1 = k0;
    else if (t >= k1.t) k0 = k1;
    else {
      for (let i = 0; i < keysArr.length - 1; i++) {
        if (t >= keysArr[i].t && t <= keysArr[i + 1].t) { k0 = keysArr[i]; k1 = keysArr[i + 1]; break; }
      }
    }
    const u = k0 === k1 ? 0 : (k1.e ?? ease.inOut)(clamp((t - k0.t) / (k1.t - k0.t)));
    if (k0.orbit && k1.orbit) {
      const c0 = k0.center ?? [0, 0, 0], c1 = k1.center ?? c0;
      const cc = c0.map((v, i) => lerp(v, c1[i], u));
      const r = lerp(k0.orbit[0], k1.orbit[0], u);
      const az = lerp(k0.orbit[1], k1.orbit[1], u) * Math.PI / 180;
      const el = lerp(k0.orbit[2], k1.orbit[2], u) * Math.PI / 180;
      P.set(cc[0] + r * Math.cos(el) * Math.sin(az), cc[1] + r * Math.sin(el), cc[2] + r * Math.cos(el) * Math.cos(az));
      T.set(...cc);
    } else {
      P.set(lerp(k0.pos[0], k1.pos[0], u), lerp(k0.pos[1], k1.pos[1], u), lerp(k0.pos[2], k1.pos[2], u));
      T.set(lerp(k0.tgt[0], k1.tgt[0], u), lerp(k0.tgt[1], k1.tgt[1], u), lerp(k0.tgt[2], k1.tgt[2], u));
    }
    // optional gentle handheld drift
    const dr = f.drift ?? keysArr.drift;
    if (dr) {
      P.x += Math.sin(t * 0.37) * dr; P.y += Math.sin(t * 0.23 + 1) * dr * 0.6; P.z += Math.cos(t * 0.31) * dr;
    }
    camera.position.copy(P);
    camera.lookAt(T);
    const f0 = k0.fov ?? camera.fov, f1 = k1.fov ?? f0;
    camera.fov = lerp(f0, f1, u);
    camera.updateProjectionMatrix();
  };
  return f;
}

// project world point to screen pixels
const _v = new THREE.Vector3();
export function toScreen(p, camera, W = 1920, H = 1080) {
  _v.set(p[0] ?? p.x, p[1] ?? p.y, p[2] ?? p.z).project(camera);
  return [(_v.x * 0.5 + 0.5) * W, (-_v.y * 0.5 + 0.5) * H, _v.z];
}

// darken paint with world-space noise and silt towards the seabed (cheap, procedural)
export function addGrime(mat, o = {}) {
  const strength = o.strength ?? 0.35;
  mat.onBeforeCompile = (sh) => {
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vWpG;')
      .replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nvWpG = (modelMatrix*vec4(transformed,1.0)).xyz;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', `#include <common>
      varying vec3 vWpG;
      float hashG(vec3 p){ p = fract(p*0.3183099+0.1); p *= 17.0; return fract(p.x*p.y*p.z*(p.x+p.y+p.z)); }
      float noiseG(vec3 x){ vec3 i = floor(x); vec3 f = fract(x); f = f*f*(3.0-2.0*f);
        return mix(mix(mix(hashG(i+vec3(0,0,0)),hashG(i+vec3(1,0,0)),f.x), mix(hashG(i+vec3(0,1,0)),hashG(i+vec3(1,1,0)),f.x),f.y),
                   mix(mix(hashG(i+vec3(0,0,1)),hashG(i+vec3(1,0,1)),f.x), mix(hashG(i+vec3(0,1,1)),hashG(i+vec3(1,1,1)),f.x),f.y), f.z); }`)
      .replace('#include <color_fragment>', `#include <color_fragment>
        float gn = noiseG(vWpG*1.3)*0.6 + noiseG(vWpG*5.0)*0.4;
        float silt = 1.0 - smoothstep(0.0, 2.5, vWpG.y);
        diffuseColor.rgb *= 1.0 - ${strength.toFixed(3)} * (gn*0.7 + silt*0.6);
        diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.32,0.30,0.25), silt*0.25);`);
  };
  mat.customProgramCacheKey = () => 'grime' + strength;
  return mat;
}

// screen-space thick line segments (positions: flat array of segment endpoints)
import { LineSegments2 } from 'three/addons/lines/LineSegments2.js';
import { LineSegmentsGeometry } from 'three/addons/lines/LineSegmentsGeometry.js';
import { LineMaterial } from 'three/addons/lines/LineMaterial.js';
export function fatLines(positions, o = {}) {
  const g = new LineSegmentsGeometry();
  g.setPositions(positions);
  if (o.colors) g.setColors(o.colors);
  const m = new LineMaterial({
    color: o.colors ? 0xffffff : (o.color ?? 0x4cc9f0), linewidth: o.width ?? 2, vertexColors: !!o.colors,
    transparent: (o.opacity ?? 1) < 1 || !!o.transparent, opacity: o.opacity ?? 1, depthTest: o.depthTest ?? true,
    worldUnits: false, fog: false, dashed: false,
  });
  m.resolution.set(1920, 1080);
  if (o.clip) m.clippingPlanes = o.clip;
  const l = new LineSegments2(g, m);
  l.computeLineDistances();
  l.frustumCulled = false;
  return l;
}

// full-screen blueprint backdrop rendered in WebGL (so 3D viewports can sit on top of it)
export function makeBackdrop() {
  const scene = new THREE.Scene();
  const cam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  const mat = new THREE.ShaderMaterial({
    depthTest: false, depthWrite: false,
    uniforms: { uOff: { value: 0 }, uA: { value: 1 }, c0: { value: new THREE.Color(0x0f2236) }, c1: { value: new THREE.Color(0x040a12) }, uGrid: { value: 1 } },
    vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }',
    fragmentShader: `uniform float uOff; uniform float uA; uniform vec3 c0; uniform vec3 c1; uniform float uGrid; varying vec2 vUv;
      void main(){
        vec2 px = vec2(vUv.x*1920.0, (1.0-vUv.y)*1080.0);
        float d = length((px - vec2(960.0, 454.0)) / vec2(1440.0, 1440.0));
        vec3 c = mix(c0, c1, smoothstep(0.05, 0.75, d));
        vec2 g = mod(px - uOff, 48.0);
        float l = (step(g.x, 1.0) + step(g.y, 1.0)) * 0.055;
        vec2 g4 = mod(px - uOff, 192.0);
        l += (step(g4.x, 1.0) + step(g4.y, 1.0)) * 0.03;
        c += vec3(0.35, 0.59, 0.78) * l * 0.35 * uGrid;
        gl_FragColor = vec4(c * uA, 1.0);
        #include <colorspace_fragment>
      }`,
  });
  const q = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), mat);
  scene.add(q);
  return {
    mat,
    render(renderer, o = {}) {
      mat.uniforms.uOff.value = o.offset ?? 0;
      mat.uniforms.uA.value = o.alpha ?? 1;
      mat.uniforms.uGrid.value = o.grid ?? 1;
      renderer.setScissorTest(false);
      renderer.setViewport(0, 0, 1920, 1080);
      renderer.autoClear = true;
      renderer.render(scene, cam);
    },
  };
}

// render a scene into a screen-space rectangle (x,y = top-left in pixels)
export function renderViewport(renderer, scene, camera, x, y, w, h) {
  renderer.autoClear = false;
  renderer.clearDepth();
  renderer.setScissorTest(true);
  renderer.setScissor(x, 1080 - y - h, w, h);
  renderer.setViewport(x, 1080 - y - h, w, h);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  renderer.render(scene, camera);
  renderer.setScissorTest(false);
  renderer.setViewport(0, 0, 1920, 1080);
  renderer.autoClear = true;
}

// studio lighting scene for FE / object views
export function studioScene(o = {}) {
  const scene = new THREE.Scene();
  scene.add(new THREE.HemisphereLight(0xdfefff, 0x1a2430, o.hemi ?? 1.6));
  const d = new THREE.DirectionalLight(0xffffff, o.key ?? 1.6);
  d.position.set(3, 5, 4);
  scene.add(d);
  const r = new THREE.DirectionalLight(0x9fd8ff, o.rim ?? 0.8);
  r.position.set(-4, 2, -3);
  scene.add(r);
  return scene;
}
