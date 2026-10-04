import * as THREE from 'three'

// The worlds the house opens into. Outside, the house stands on its street.
// Once it breaks open, each floor is seen inside a different environment,
// the way the igloo scenes pass through cloud into a new place: a warm café
// haze, a charcoal studio, a green courtyard shade, a terrace sunset, and a
// night sky. Each is a gradient dome, a ground disc, drifting motes, and a
// lighting treatment. Nothing here is a bitmap: it is all drawn in the shader.

// zenith / horizon / nadir: the dome. floor: the disc the floors hang over.
// mote: colour of the drifting particles, with their size and count.
// hemi / sun: multipliers on the daylight. lamps: warm light inside the rooms.
// disc: a visible sun on the dome. stars: a starfield. dark: text goes light.
export const ENVS = {
  cafe: { zenith: '#ead9c0', horizon: '#f8f1e5', nadir: '#d8c6ab', floor: '#e3d5c0', mote: '#ffd9a3', size: 0.07, count: 420, hemi: 1.25, sun: 0.9, lamps: 0.6, disc: 0, stars: 0, dark: 0, expo: 1.12 },
  studio: { zenith: '#0f1013', horizon: '#23252c', nadir: '#0a0b0d', floor: '#17181c', mote: '#aab3c4', size: 0.045, count: 300, hemi: 0.4, sun: 0.55, lamps: 1.2, disc: 0, stars: 0, dark: 1, expo: 1.05 },
  courtyard: { zenith: '#86a06a', horizon: '#dbe3c4', nadir: '#4e6438', floor: '#5f7447', mote: '#f6f1b2', size: 0.06, count: 520, hemi: 1.15, sun: 1, lamps: 0, disc: 0, stars: 0, dark: 0, expo: 1.1 },
  terrace: { zenith: '#463656', horizon: '#f5a673', nadir: '#2a1d2b', floor: '#352831', mote: '#ffcf9a', size: 0.06, count: 360, hemi: 0.9, sun: 1.1, lamps: 0.8, disc: 1, stars: 0.15, dark: 1, expo: 1.08 },
  night: { zenith: '#05070e', horizon: '#1a2134', nadir: '#04050a', floor: '#0b0d14', mote: '#dfe9ff', size: 0.05, count: 260, hemi: 0.9, sun: 1, lamps: 1.3, disc: 0, stars: 1, dark: 1, expo: 1.18 },
}

const DOME_VERT = /* glsl */ `
  varying vec3 vDir;
  void main() {
    vDir = position;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`
const DOME_FRAG = /* glsl */ `
  precision highp float;
  varying vec3 vDir;
  uniform vec3 zenith, horizon, nadir, sunColor, sunDir;
  uniform float disc, stars, time;
  float hash(vec3 p) { return fract(sin(dot(p, vec3(12.9898, 78.233, 37.719))) * 43758.5453); }
  void main() {
    vec3 d = normalize(vDir);
    float y = d.y;
    vec3 col = y > 0.0 ? mix(horizon, zenith, pow(y, 0.55)) : mix(horizon, nadir, pow(-y, 0.5));
    // A soft band of haze sits on the horizon.
    col = mix(col, horizon, exp(-abs(y) * 9.0) * 0.35);
    float s = max(dot(d, sunDir), 0.0);
    col += sunColor * disc * (smoothstep(0.9985, 0.9992, s) * 1.6 + pow(s, 10.0) * 0.4);
    // Stars: a hash per cell of the sky, a few of them bright, all of them twinkling.
    vec3 cell = floor(d * 260.0);
    float h = hash(cell);
    float twinkle = 0.55 + 0.45 * sin(time * 1.7 + h * 80.0);
    float star = step(0.9965, h) * twinkle * smoothstep(0.02, 0.25, y);
    col += stars * star * (0.6 + 0.6 * hash(cell + 1.0));
    gl_FragColor = vec4(col, 1.0);
  }
`

const MOTE_VERT = /* glsl */ `
  attribute float seed;
  uniform float time, size, scale;
  varying float vA;
  void main() {
    vec3 p = position;
    p.y += sin(time * 0.35 + seed * 6.28) * 0.25;
    p.x += sin(time * 0.22 + seed * 12.0) * 0.3;
    p.z += cos(time * 0.27 + seed * 9.0) * 0.3;
    vec4 mv = modelViewMatrix * vec4(p, 1.0);
    vA = 0.35 + 0.65 * (0.5 + 0.5 * sin(time * 0.9 + seed * 40.0));
    gl_PointSize = size * scale / -mv.z;
    gl_Position = projectionMatrix * mv;
  }
`
const MOTE_FRAG = /* glsl */ `
  precision highp float;
  uniform vec3 color;
  uniform float opacity;
  varying float vA;
  void main() {
    float r = length(gl_PointCoord - 0.5);
    float a = smoothstep(0.5, 0.15, r) * vA * opacity;
    gl_FragColor = vec4(color, a);
  }
`

export function createEnvironment(scene) {
  const cur = {
    zenith: new THREE.Color(), horizon: new THREE.Color(), nadir: new THREE.Color(), floor: new THREE.Color(), mote: new THREE.Color(),
    size: 0, hemi: 1, sun: 1, lamps: 0, disc: 0, stars: 0, dark: 0, expo: 1.12, inside: 0,
  }
  const want = { ...cur, zenith: new THREE.Color(), horizon: new THREE.Color(), nadir: new THREE.Color(), floor: new THREE.Color(), mote: new THREE.Color() }

  const dome = new THREE.Mesh(
    new THREE.SphereGeometry(140, 48, 24),
    new THREE.ShaderMaterial({
      vertexShader: DOME_VERT,
      fragmentShader: DOME_FRAG,
      side: THREE.BackSide,
      depthWrite: false,
      uniforms: {
        zenith: { value: cur.zenith }, horizon: { value: cur.horizon }, nadir: { value: cur.nadir },
        sunColor: { value: new THREE.Color('#ffd2a0') }, sunDir: { value: new THREE.Vector3(0, 1, 0) },
        disc: { value: 0 }, stars: { value: 0 }, time: { value: 0 },
      },
    }),
  )
  dome.renderOrder = -10
  dome.frustumCulled = false
  dome.visible = false
  scene.add(dome)

  // The disc every floor hangs over once the house is open.
  const floor = new THREE.Mesh(new THREE.CircleGeometry(80, 64), new THREE.MeshStandardMaterial({ color: cur.floor, roughness: 1 }))
  floor.rotation.x = -Math.PI / 2
  floor.position.y = -1.75
  // No shadows here: the floors lifted clear of the frame would throw huge
  // dark shapes across the disc.
  floor.receiveShadow = false
  floor.visible = false
  scene.add(floor)

  // Motes in the air: dust in the café, pollen in the courtyard, embers at
  // the terrace, the faint cold sparks of a night sky.
  const COUNT = 520
  const pos = new Float32Array(COUNT * 3)
  const seed = new Float32Array(COUNT)
  for (let i = 0; i < COUNT; i++) {
    pos[i * 3] = (Math.random() - 0.5) * 22
    pos[i * 3 + 1] = -1 + Math.random() * 11
    pos[i * 3 + 2] = (Math.random() - 0.5) * 22
    seed[i] = Math.random()
  }
  const moteGeo = new THREE.BufferGeometry()
  moteGeo.setAttribute('position', new THREE.BufferAttribute(pos, 3))
  moteGeo.setAttribute('seed', new THREE.BufferAttribute(seed, 1))
  const moteMat = new THREE.ShaderMaterial({
    vertexShader: MOTE_VERT,
    fragmentShader: MOTE_FRAG,
    transparent: true,
    depthWrite: false,
    uniforms: { time: { value: 0 }, size: { value: 0.06 }, scale: { value: 600 }, color: { value: cur.mote }, opacity: { value: 0 } },
  })
  const motes = new THREE.Points(moteGeo, moteMat)
  motes.frustumCulled = false
  motes.visible = false
  scene.add(motes)

  let id = null
  function set(next) {
    if (next === id) return
    id = next
    const e = ENVS[next]
    want.inside = e ? 1 : 0
    if (!e) return
    want.zenith.set(e.zenith)
    want.horizon.set(e.horizon)
    want.nadir.set(e.nadir)
    want.floor.set(e.floor)
    want.mote.set(e.mote)
    for (const k of ['size', 'hemi', 'sun', 'lamps', 'disc', 'stars', 'dark', 'expo']) want[k] = e[k]
    moteGeo.setDrawRange(0, e.count)
  }

  // Outside, the dome and disc take the sky colour so the changeover is
  // hidden inside the cloud; the daylight stays untouched.
  function update(dt, t, camera, sky, sunPos, still) {
    const k = still ? 1 : 1 - Math.pow(0.004, dt)
    if (!want.inside) {
      want.zenith.copy(sky)
      want.horizon.copy(sky)
      want.nadir.copy(sky)
      want.floor.copy(sky)
      want.hemi = 1
      want.sun = 1
      want.lamps = 0
      want.disc = 0
      want.stars = 0
      want.dark = 0
      want.expo = 1.12
    }
    for (const c of ['zenith', 'horizon', 'nadir', 'floor', 'mote']) cur[c].lerp(want[c], k)
    for (const n of ['size', 'hemi', 'sun', 'lamps', 'disc', 'stars', 'dark', 'expo', 'inside']) cur[n] = cur[n] + (want[n] - cur[n]) * k

    const on = cur.inside > 0.02
    dome.visible = floor.visible = motes.visible = on
    dome.position.copy(camera.position)
    const u = dome.material.uniforms
    u.disc.value = cur.disc
    u.stars.value = cur.stars
    u.time.value = t
    u.sunDir.value.copy(sunPos).normalize()
    floor.material.color.copy(cur.floor)
    motes.position.set(camera.position.x * 0.2, 0, camera.position.z * 0.2)
    moteMat.uniforms.time.value = t
    moteMat.uniforms.size.value = cur.size
    moteMat.uniforms.scale.value = innerHeight * 0.9
    moteMat.uniforms.opacity.value = cur.inside * 0.85
  }

  return { set, update, cur, get id() { return id } }
}
