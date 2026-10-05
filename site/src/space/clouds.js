import * as THREE from 'three'

// Soft cloud banks: camera-facing puffs of fbm noise in the fog's colour,
// lit from above. They gather round whatever is in view (a floor's
// diorama, the house's base, the membership stones) so each scene sits in
// cloud, the way the Astra comps do. One instanced draw call.

const COUNT = 90

const VERT = /* glsl */ `
  attribute vec4 puff;          // xyz centre, w size
  attribute float seed;
  uniform float uTime;
  varying vec2 vUv;
  varying float vSeed;
  varying float vH;
  varying float vDepth;
  void main() {
    vUv = uv;
    vSeed = seed;
    vec3 c = puff.xyz + vec3(sin(uTime * 0.05 + seed * 6.3), 0.0, cos(uTime * 0.04 + seed * 4.1)) * puff.w * 0.05;
    vec4 mv = viewMatrix * vec4(c, 1.0);
    // Wider than tall: banks, not balls.
    mv.xy += position.xy * vec2(puff.w * 1.6, puff.w * 0.8);
    vH = position.y;
    vDepth = -mv.z;
    gl_Position = projectionMatrix * mv;
  }
`
const FRAG = /* glsl */ `
  uniform vec3 uFog;
  uniform float uOpacity, uTime, uLight;
  varying vec2 vUv;
  varying float vSeed;
  varying float vH;
  varying float vDepth;
  float h21(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
  float vnoise(vec2 p) {
    vec2 i = floor(p), f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(mix(h21(i), h21(i + vec2(1, 0)), u.x), mix(h21(i + vec2(0, 1)), h21(i + vec2(1, 1)), u.x), u.y);
  }
  float fbm(vec2 p) {
    float v = 0.0, a = 0.5;
    for (int i = 0; i < 5; i++) { v += a * vnoise(p); p = p * 2.07 + 13.3; a *= 0.5; }
    return v;
  }
  void main() {
    vec2 p = vUv - 0.5;
    float r = length(p * vec2(1.0, 1.6));
    float n = fbm(vUv * 3.2 + vSeed * 17.0 + vec2(uTime * 0.01, 0.0));
    float a = smoothstep(0.5, 0.1, r + (n - 0.5) * 0.55);
    // Lit tops, shaded undersides.
    vec3 col = uFog * mix(0.9, 1.0 + 0.1 * uLight, smoothstep(-0.5, 0.5, vH + (n - 0.5) * 0.6));
    // Fade puffs that crowd the lens.
    a *= smoothstep(0.4, 2.0, vDepth);
    gl_FragColor = vec4(col, a * uOpacity);
  }
`

export function createClouds(scene, fogColor) {
  const geo = new THREE.InstancedBufferGeometry()
  const quad = new THREE.PlaneGeometry(1, 1)
  geo.index = quad.index
  geo.setAttribute('position', quad.attributes.position)
  geo.setAttribute('uv', quad.attributes.uv)
  const puff = new Float32Array(COUNT * 4)
  const seed = new Float32Array(COUNT)
  for (let i = 0; i < COUNT; i++) seed[i] = Math.random()
  const puffAttr = new THREE.InstancedBufferAttribute(puff, 4)
  puffAttr.setUsage(THREE.DynamicDrawUsage)
  geo.setAttribute('puff', puffAttr)
  geo.setAttribute('seed', new THREE.InstancedBufferAttribute(seed, 1))
  geo.instanceCount = 0
  const uniforms = { uFog: { value: fogColor }, uOpacity: { value: 0 }, uTime: { value: 0 }, uLight: { value: 1 } }
  const mesh = new THREE.Mesh(geo, new THREE.ShaderMaterial({ vertexShader: VERT, fragmentShader: FRAG, uniforms, transparent: true, depthWrite: false }))
  mesh.frustumCulled = false
  mesh.renderOrder = 5
  scene.add(mesh)

  const rnd = (i, k) => {
    const x = Math.sin(i * 127.1 + k * 311.7) * 43758.5453
    return x - Math.floor(x)
  }
  let key = ''
  // A ring of banks round a box (cx, cz, half-sizes hx, hz) at height y,
  // plus a bed underneath it.
  function gather(id, cx, cy, cz, hx, hz, { size = 1, ring = 1, bed = 1, n = COUNT } = {}) {
    if (key === id) return
    key = id
    const span = Math.max(hx, hz)
    let k = 0
    const put = (x, y, z, s) => {
      if (k >= n) return
      puff.set([x, y, z, s], k * 4)
      k++
    }
    const nRing = Math.round(n * 0.6 * ring)
    for (let i = 0; i < nRing; i++) {
      const a = (i / nRing) * Math.PI * 2 + rnd(i, 1) * 0.4
      const rr = 1.05 + rnd(i, 2) * 0.9
      put(cx + Math.cos(a) * hx * rr, cy - span * 0.25 + rnd(i, 3) * span * 0.35, cz + Math.sin(a) * hz * rr, span * size * (0.7 + rnd(i, 4) * 0.8))
    }
    const nBed = Math.round(n * 0.4 * bed)
    for (let i = 0; i < nBed; i++) {
      put(cx + (rnd(i, 5) - 0.5) * hx * 2.6, cy - span * (0.45 + rnd(i, 6) * 0.6), cz + (rnd(i, 7) - 0.5) * hz * 2.6, span * size * (1.0 + rnd(i, 8)))
    }
    geo.instanceCount = k
    puffAttr.needsUpdate = true
  }
  function update(t, opacity, light) {
    uniforms.uTime.value = t
    uniforms.uOpacity.value = opacity
    uniforms.uLight.value = light
    mesh.visible = opacity > 0.01 && geo.instanceCount > 0
  }
  return { gather, update }
}
