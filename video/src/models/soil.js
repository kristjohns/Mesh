// Soil cross-section face (with a slot for the well) and helpers.
import * as THREE from 'three';

// A vertical section face lying in the local XY plane (x horizontal along the cut, y up),
// spanning x in [-w/2, w/2], y in [-depth, 0], with a hole of half-width hw down to holeDepth.
export function soilSection(o = {}) {
  const w = o.width ?? 60, depth = o.depth ?? 80, hw = o.holeHalf ?? 0.46, hd = o.holeDepth ?? 60;
  const s = new THREE.Shape();
  s.moveTo(-w / 2, 0);
  s.lineTo(-hw, 0);
  s.lineTo(-hw, -hd);
  s.lineTo(hw, -hd);
  s.lineTo(hw, 0);
  s.lineTo(w / 2, 0);
  s.lineTo(w / 2, -depth);
  s.lineTo(-w / 2, -depth);
  s.closePath();
  const g = new THREE.ShapeGeometry(s, 1);
  const mat = new THREE.ShaderMaterial({
    side: THREE.DoubleSide,
    uniforms: {
      uTop: { value: new THREE.Color(o.top ?? 0x7c7160) }, uBot: { value: new THREE.Color(o.bottom ?? 0x463f33) },
      uAlpha: { value: 1 }, uHi: { value: 0 }, uHiY: { value: new THREE.Vector2(0, 0) },
      fogColor: { value: new THREE.Color(0x0d3242) }, uDepth: { value: depth }, uFade: { value: o.fade ?? 0.0 },
    },
    transparent: true,
    vertexShader: `varying vec2 vP; void main(){ vP = position.xy; gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.0); }`,
    fragmentShader: `uniform vec3 uTop; uniform vec3 uBot; uniform float uAlpha; uniform float uHi; uniform vec2 uHiY; uniform vec3 fogColor; uniform float uDepth; uniform float uFade;
      varying vec2 vP;
      float h(vec2 p){ return fract(sin(dot(p, vec2(127.1,311.7)))*43758.5453); }
      float n(vec2 p){ vec2 i=floor(p), f=fract(p); f=f*f*(3.0-2.0*f); return mix(mix(h(i),h(i+vec2(1,0)),f.x), mix(h(i+vec2(0,1)),h(i+vec2(1,1)),f.x), f.y); }
      void main(){
        float d = -vP.y;
        float t = clamp(d/60.0, 0.0, 1.0);
        vec3 c = mix(uTop, uBot, pow(t,0.7));
        // layering
        float band = n(vec2(vP.x*0.05, d*0.35)) ;
        c *= 0.88 + 0.22*band;
        float lines = smoothstep(0.96, 1.0, sin(d*0.9 + n(vec2(vP.x*0.08, d*0.1))*3.0)*0.5+0.5);
        c *= 1.0 - 0.10*lines;
        // grain
        c *= 0.92 + 0.12*h(floor(vP*28.0));
        // near-mudline softer clay: slightly greener
        c = mix(c, vec3(0.30,0.32,0.26), 0.25*(1.0 - smoothstep(0.0, 8.0, d)));
        // highlight band
        if (uHi > 0.0) { float b = step(uHiY.x, d)*step(d, uHiY.y); c = mix(c, vec3(0.3,0.75,0.95), 0.25*b*uHi); }
        // fade far edges into fog
        float ex = smoothstep(0.35, 0.5, abs(vP.x)/${(w).toFixed(1)});
        float ey = smoothstep(uDepth*0.75, uDepth, d);
        c = mix(c, fogColor*0.8, max(ex, ey));
        gl_FragColor = vec4(c, uAlpha);
        #include <colorspace_fragment>
      }`,
  });
  const m = new THREE.Mesh(g, mat);
  m.renderOrder = -1;
  return m;
}
