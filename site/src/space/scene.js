import * as THREE from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { RGBELoader } from 'three/examples/jsm/loaders/RGBELoader.js'
import { ROOMS } from './beats.js'

// The house, baked in Blender (blender/tools/bake_site.py): each floor is one
// unlit mesh whose atlas already holds its light, so what the site shows is
// what Cycles rendered. One camera, one house, fog that carries the hour;
// every change of scene happens inside a veil of cloud.
// Units: 1 = 8 ft. Floors sit in their own frames (house.json offsets).

const FLOORS = {
  basement: { y: -0.72, x: 0.416, z: 1.387 },
  ground: { y: 0.73, x: 0, z: 0 },
  first: { y: 2.18, x: -0.208, z: -0.842 },
  second: { y: 3.63, x: 0.417, z: -0.217 },
}
const ORDER = ['basement', 'ground', 'first', 'second']
// How far each floor lifts when the house parts on the street.
const PART = { basement: 0, ground: 0.32, first: 0.66, second: 1.0 }
const WALL = 1.3
const LIME = '#e8e4da'

const smooth = (a, b, x) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)))
  return t * t * (3 - 2 * t)
}
const lerp = (a, b, k) => a + (b - a) * k
const srgb = (hex) => {
  const c = new THREE.Color(hex)
  return new THREE.Vector3(...c.clone().convertLinearToSRGB().toArray())
}

// ---------- shared shader bits ----------
const NOISE = /* glsl */ `
  float h21(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
  float vnoise(vec2 p) {
    vec2 i = floor(p), f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(mix(h21(i), h21(i + vec2(1, 0)), u.x), mix(h21(i + vec2(0, 1)), h21(i + vec2(1, 1)), u.x), u.y);
  }
  float fbm(vec2 p) {
    float v = 0.0, a = 0.5;
    for (int i = 0; i < 5; i++) { v += a * vnoise(p); p = p * 2.03 + 17.1; a *= 0.5; }
    return v;
  }
`

// Fog every material shares: distance haze, a cloud bed below the diorama
// in view, and the colour of the hour. Mixed after the colour-space
// conversion, so the fog shows its hex exactly.
const fogUniforms = {
  uFog: { value: srgb('#d1bfc2') },
  uNear: { value: 20 },
  uFar: { value: 60 },
  uBedY: { value: -100 },
  uBedDepth: { value: 1 },
  uTime: { value: 0 },
}
function fogify(material, extra = {}) {
  material.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, fogUniforms, extra.uniforms || {})
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vWorldP;')
      .replace('#include <fog_vertex>', '#include <fog_vertex>\nvWorldP = (modelMatrix * vec4(transformed, 1.0)).xyz;')
    shader.fragmentShader = shader.fragmentShader
      .replace(
        '#include <common>',
        `#include <common>
        varying vec3 vWorldP;
        uniform vec3 uFog; uniform float uNear, uFar, uBedY, uBedDepth, uTime;
        ${extra.pars || ''}
        ${NOISE}`,
      )
      .replace('#include <map_fragment>', `#include <map_fragment>\n${extra.map || ''}`)
      .replace(
        '#include <fog_fragment>',
        `{
          float d = distance(cameraPosition, vWorldP);
          float f = smoothstep(uNear, uFar, d);
          float n = fbm(vWorldP.xz * 0.9 + vec2(uTime * 0.02, uTime * 0.013));
          float bed = smoothstep(uBedY, uBedY - uBedDepth, vWorldP.y + (n - 0.5) * 0.9);
          f = max(f, bed);
          gl_FragColor.rgb = mix(gl_FragColor.rgb, uFog, clamp(f, 0.0, 1.0));
        }`,
      )
  }
  material.fog = true
  return material
}

// Baked surfaces: the atlas as is, back faces filled with lime plaster so a
// clipped wall reads as a solid section, and a night grade.
const bakedUniforms = { uNight: { value: 0 }, uCap: { value: srgb(LIME) } }
function bakedMaterial(map) {
  map.colorSpace = THREE.SRGBColorSpace
  const m = new THREE.MeshBasicMaterial({ map, side: THREE.DoubleSide, toneMapped: false })
  return fogify(m, {
    uniforms: bakedUniforms,
    pars: 'uniform float uNight; uniform vec3 uCap;',
    map: `
      if (!gl_FrontFacing) diffuseColor.rgb = pow(uCap, vec3(2.2)) * 0.82;
      vec3 nightCol = diffuseColor.rgb * vec3(0.16, 0.19, 0.3);
      diffuseColor.rgb = mix(diffuseColor.rgb, nightCol, uNight);
    `,
  })
}

// ---------- the scene ----------
export async function createScene(canvas) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' })
  renderer.setPixelRatio(Math.min(devicePixelRatio, 1.75))
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  renderer.toneMappingExposure = 1.0
  renderer.localClippingEnabled = true
  const scene = new THREE.Scene()
  scene.fog = new THREE.Fog('#d1bfc2', 20, 60)   // enables the fog chunks; ours replace the maths
  const camera = new THREE.PerspectiveCamera(30, 1, 0.05, 400)

  // The sky: a full-screen gradient with slow cloud, in the fog's colour.
  const sky = new THREE.Mesh(
    new THREE.PlaneGeometry(2, 2),
    new THREE.ShaderMaterial({
      depthTest: false,
      depthWrite: false,
      uniforms: { uFog: fogUniforms.uFog, uGlow: { value: srgb('#e8b9a8') }, uGlowK: { value: 0.5 }, uTime: fogUniforms.uTime, uAspect: { value: 1 } },
      vertexShader: 'varying vec2 vUv; void main() { vUv = uv; gl_Position = vec4(position.xy, 0.9999, 1.0); }',
      fragmentShader: `
        varying vec2 vUv; uniform vec3 uFog, uGlow; uniform float uGlowK, uTime, uAspect;
        ${NOISE}
        void main() {
          vec2 p = vec2(vUv.x * uAspect, vUv.y);
          float streak = fbm(vec2(p.x * 1.4 + uTime * 0.006, p.y * 4.0));
          float band = smoothstep(0.35, 0.75, vUv.y) * (1.0 - smoothstep(0.75, 1.0, vUv.y));
          vec3 col = mix(uFog * 0.94, uFog * 1.04, vUv.y);
          col = mix(col, uGlow, uGlowK * band * smoothstep(0.45, 0.8, streak));
          col += (fbm(p * 3.0 + uTime * 0.01) - 0.5) * 0.035;
          gl_FragColor = vec4(col, 1.0);
        }`,
    }),
  )
  sky.frustumCulled = false
  sky.renderOrder = -10
  scene.add(sky)

  // The veil: drifting cloud that fills the frame between scenes.
  const veilMat = new THREE.ShaderMaterial({
    transparent: true,
    depthTest: false,
    depthWrite: false,
    uniforms: { uFog: fogUniforms.uFog, uVeil: { value: 0 }, uTime: fogUniforms.uTime, uAspect: { value: 1 } },
    vertexShader: 'varying vec2 vUv; void main() { vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }',
    fragmentShader: `
      varying vec2 vUv; uniform vec3 uFog; uniform float uVeil, uTime, uAspect;
      ${NOISE}
      void main() {
        vec2 p = vec2(vUv.x * uAspect, vUv.y) * 2.2;
        float n = fbm(p + vec2(uTime * 0.03, -uTime * 0.02));
        float a = smoothstep(0.0, 1.0, uVeil * 1.6 - 0.6 + n * 0.9);
        a = max(a, smoothstep(0.85, 1.0, uVeil));
        vec3 col = uFog * (0.97 + 0.08 * n);
        gl_FragColor = vec4(col, a);
      }`,
  })
  const veil = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), veilMat)
  veil.frustumCulled = false
  veil.renderOrder = 10
  scene.add(veil)

  // Light for the loose props (the baked house needs none).
  const hemi = new THREE.HemisphereLight('#fff4ea', '#6b5a4c', 0.6)
  const key = new THREE.DirectionalLight('#ffe2c4', 2.2)
  key.position.set(3, 6, 4)
  scene.add(hemi, key, key.target)
  try {
    const hdr = await new RGBELoader().loadAsync('/world/env/sunrise_1k.hdr')
    const pmrem = new THREE.PMREMGenerator(renderer)
    scene.environment = pmrem.fromEquirectangular(hdr).texture
    hdr.dispose()
    pmrem.dispose()
  } catch {
    /* props fall back to the hemisphere light */
  }

  // ---------- the baked house ----------
  const loader = new GLTFLoader()
  const glassMats = []
  const glassDay = new THREE.Color('#cfd8d6')
  const glassNight = new THREE.Color('#ffb466')
  const clip = [0, 1, 2, 3, 4].map(() => new THREE.Plane(new THREE.Vector3(0, -1, 0), 1e5))
  const load = async (name) => {
    const g = await loader.loadAsync(`/models/baked/${name}-day.gltf`).catch(() => null)
    if (!g) return null
    g.scene.traverse((o) => {
      if (!o.isMesh) return
      o.material = bakedMaterial(o.material.map)
      o.material.clippingPlanes = clip
    })
    const fx = await loader.loadAsync(`/models/baked/${name}-fixtures.gltf`).catch(() => null)
    if (fx) {
      fx.scene.traverse((o) => {
        if (!o.isMesh) return
        const x = o.material.userData || {}
        const glow = !x.glass
        const m = glow
          ? new THREE.MeshBasicMaterial({ color: o.material.emissive?.getHex() ? o.material.emissive : o.material.color, toneMapped: false })
          : new THREE.MeshBasicMaterial({ color: '#cfd8d6', transparent: true, opacity: 0.22, depthWrite: false, toneMapped: false })
        if (!glow) glassMats.push(m)
        m.clippingPlanes = clip
        o.material = fogify(m)
        o.userData.glow = glow
      })
      g.scene.add(fx.scene)
    }
    return g.scene
  }
  const house = new THREE.Group()
  scene.add(house)
  const floors = {}
  const loaded = await Promise.all([...ORDER, 'roof', 'site'].map(load))
  ORDER.forEach((id, i) => {
    const g = new THREE.Group()
    const f = FLOORS[id]
    g.position.set(f.x, f.y, f.z)
    if (loaded[i]) g.add(loaded[i])
    floors[id] = g
    house.add(g)
  })
  const roof = loaded[4]
  if (roof) floors.second.add(roof)
  const site = loaded[5] || new THREE.Group()
  house.add(site)

  // The street: asphalt that goes to fog before the frame's edge.
  const street = new THREE.Mesh(
    new THREE.PlaneGeometry(200, 200),
    fogify(new THREE.MeshBasicMaterial({ color: '#8d8790', toneMapped: false })),
  )
  street.rotation.x = -Math.PI / 2
  street.position.y = -0.002
  house.add(street)

  // ---------- the loose props (blender/tools/build_props.py) ----------
  const propsG = await loader.loadAsync('/models/props/props.gltf').catch(() => null)
  const proto = {}
  if (propsG) {
    propsG.scene.traverse((o) => {
      if (o.isMesh) {
        o.castShadow = o.receiveShadow = false
        const m = o.material
        if (m.map) m.map.anisotropy = 8
        // The CC0 teak photo is pale; pull it to the palette's teak.
        if (m.name === 'Teak') m.color.set('#c08a68')
        if (m.name === 'Sandstone') m.color.set('#d8cbb0')
        fogify(m)
      }
    })
    for (const child of [...propsG.scene.children]) {
      child.position.set(0, 0, 0)
      proto[child.name] = child
    }
  }
  const clone = (name) => (proto[name] ? proto[name].clone() : new THREE.Group())

  // Prologue: two chairs, two books and petals falling through the dawn.
  const falling = new THREE.Group()
  scene.add(falling)
  const fallers = []
  const addFaller = (name, x, z, y0, spin, s = 1) => {
    const o = clone(name)
    o.scale.setScalar(s)
    falling.add(o)
    fallers.push({ o, x, z, y0, spin, phase: Math.random() * 6 })
  }
  addFaller('chair', -0.25, 16.2, 3.4, [0.5, 0.3, 0.9])
  addFaller('chair', 0.45, 16.6, 2.6, [-0.4, 0.6, -0.3])
  addFaller('book', -0.05, 16.0, 1.9, [1.2, 0.4, 0.8], 1.6)
  addFaller('book', 0.35, 16.3, 1.25, [-0.8, 1.1, 0.2], 1.6)
  for (let i = 0; i < 9; i++) addFaller('petal', 0.05 + Math.random() * 0.35, 15.9 + Math.random() * 0.4, 1.4 + Math.random() * 0.8, [3, 2, 4], 2.2)

  // Memberships: three compositions on sandstone fragments; the call: one chair.
  const stage = new THREE.Group()
  stage.position.set(0, 0, -60)
  scene.add(stage)
  const tierAnchors = []
  const tier = (x, build) => {
    const g = new THREE.Group()
    g.position.set(x, 0, 0)
    const slab = clone('slab')
    g.add(slab)
    build(g)
    stage.add(g)
    const a = new THREE.Object3D()
    a.position.set(0, -0.2, 0.25)
    g.add(a)
    tierAnchors.push(a)
    return g
  }
  const put = (g, name, x, z, ry = 0) => {
    const o = clone(name)
    o.position.set(x, 0, z)
    o.rotation.y = ry
    g.add(o)
    return o
  }
  const members = new THREE.Group()
  stage.add(members)
  const tiers = [
    tier(-1.05, (g) => put(g, 'chair', 0, 0, 0.5)),
    tier(0, (g) => {
      put(g, 'armchair', 0, 0, -0.35)
      const b = put(g, 'book', 0.02, 0.03, 0.4)
      b.position.y = 0.2
      const p = put(g, 'petal', 0.15, 0.12, 1)
      p.scale.setScalar(2.2)
    }),
    tier(1.05, (g) => {
      put(g, 'table', 0, 0)
      put(g, 'chair', -0.17, 0.02, Math.PI / 2 + 0.3)
      put(g, 'chair', 0.17, 0.02, -Math.PI / 2 - 0.3)
    }),
  ]
  for (const t of tiers) members.add(t)
  const callG = new THREE.Group()
  stage.add(callG)
  const callSlab = clone('slab_wide')
  callG.add(callSlab)
  put(callG, 'chair', -0.05, 0, 0.45)
  const petal = put(callG, 'petal', 0.18, 0.12, 2)
  petal.scale.setScalar(2.4)
  const callAnchor = new THREE.Object3D()
  callAnchor.position.set(0.3, 0.2, 0)
  callG.add(callAnchor)

  // ---------- cameras ----------
  // The street master: Blender's Camera.Street (50 mm, level, at 1.7 m),
  // with the lens shift kept as a view offset so verticals stay level.
  const STREET = { pos: new THREE.Vector3(0, 0.697, 24.5), look: new THREE.Vector3(0, 0.697, 0), fovX: 41, shift: 0.15 }
  const shot = { pos: new THREE.Vector3(), look: new THREE.Vector3(), fovX: 41, shift: 0 }
  const fovYFor = (fovX) => THREE.MathUtils.radToDeg(2 * Math.atan(Math.tan(THREE.MathUtils.degToRad(fovX) / 2) / camera.aspect))

  function roomShot(room, p, out) {
    const r = ROOMS[room]
    const f = FLOORS[r.floor]
    const [x0, z0, x1, z1] = r.rect
    const cx = f.x + (x0 + x1) / 2
    const cz = f.z + (z0 + z1) / 2
    const span = Math.max(x1 - x0, (z1 - z0) * 0.9)
    const az = THREE.MathUtils.degToRad(r.az + (p - 0.5) * 6)
    const el = THREE.MathUtils.degToRad(r.el)
    const fovX = camera.aspect < 0.8 ? 70 : 34
    const fit = camera.aspect < 0.8 ? 1.25 : 1
    const dist = ((span * 1.45) / Math.tan(THREE.MathUtils.degToRad(fovX) / 2)) * fit * (1.04 - p * 0.06)
    out.look.set(cx, f.y + WALL * 0.18, cz)
    out.pos.set(cx + Math.sin(az) * Math.cos(el) * dist, out.look.y + Math.sin(el) * dist, cz + Math.cos(az) * Math.cos(el) * dist)
    out.fovX = fovX
    out.shift = 0
  }

  // ---------- state ----------
  const state = {
    scene: 'prologue', room: null, local: 0, open: 0, night: 0, veil: 0, fog: '#d1bfc2', glow: 0.5,
    mx: 0, my: 0, still: false, tierFocus: -1,
  }
  let width = 1
  let height = 1
  function resize() {
    width = canvas.clientWidth
    height = canvas.clientHeight
    renderer.setSize(width, height, false)
    camera.aspect = width / height
    sky.material.uniforms.uAspect.value = camera.aspect
    veilMat.uniforms.uAspect.value = camera.aspect
  }
  resize()
  addEventListener('resize', resize)

  const clock = new THREE.Clock()
  const tmp = new THREE.Vector3()
  const cur = { pos: STREET.pos.clone(), look: STREET.look.clone(), fovX: STREET.fovX, shift: STREET.shift }
  let lastScene = null

  function setClip(rect, floorId) {
    if (!rect) {
      for (const p of clip) p.set(new THREE.Vector3(0, -1, 0), 1e5)
      return
    }
    const f = FLOORS[floorId]
    const [x0, z0, x1, z1] = rect
    clip[0].set(new THREE.Vector3(1, 0, 0), -(f.x + x0))
    clip[1].set(new THREE.Vector3(-1, 0, 0), f.x + x1)
    clip[2].set(new THREE.Vector3(0, 0, 1), -(f.z + z0))
    clip[3].set(new THREE.Vector3(0, 0, -1), f.z + z1)
    clip[4].set(new THREE.Vector3(0, -1, 0), f.y + WALL * 0.84)
  }

  function frame() {
    const dt = Math.min(clock.getDelta(), 0.05)
    const t = clock.elapsedTime
    fogUniforms.uTime.value = t
    fogUniforms.uFog.value.copy(srgb(state.fog))
    sky.material.uniforms.uGlowK.value = state.glow
    veilMat.uniforms.uVeil.value = state.veil
    bakedUniforms.uNight.value = state.night
    // Until the night bake lands: lit windows are warm glass.
    for (const m of glassMats) {
      m.color.copy(glassDay).lerp(glassNight, state.night)
      m.opacity = lerp(0.22, 0.9, state.night)
    }

    const s = state.scene
    const sceneKey = s + ':' + (state.room || '')
    const changed = sceneKey !== lastScene
    const isRoom = s === 'room'
    house.visible = s === 'exterior' || isRoom || (s === 'prologue' && state.local > 0.85)
    falling.visible = s === 'prologue'
    stage.visible = s === 'members' || s === 'call'
    members.visible = s === 'members'
    callG.visible = s === 'call'
    street.visible = site.visible = s !== 'room'

    // Floors: on the street they part a little; in a room only that floor shows.
    for (const id of ORDER) {
      const g = floors[id]
      const f = FLOORS[id]
      if (isRoom) {
        g.visible = id === ROOMS[state.room].floor
        g.position.y = f.y
      } else {
        g.visible = true
        g.position.y = f.y + PART[id] * state.open
      }
    }
    if (roof) roof.visible = !isRoom
    setClip(isRoom ? ROOMS[state.room].rect : null, isRoom ? ROOMS[state.room].floor : null)

    // Fog per scene.
    if (s === 'prologue') {
      fogUniforms.uNear.value = 6
      fogUniforms.uFar.value = lerp(16, 34, smooth(0.6, 1, state.local))
      fogUniforms.uBedY.value = -100
    } else if (s === 'exterior') {
      fogUniforms.uNear.value = 18
      fogUniforms.uFar.value = 44
      fogUniforms.uBedY.value = lerp(0.25, 0.9, state.open)
      fogUniforms.uBedDepth.value = 0.9
    } else if (isRoom) {
      const f = FLOORS[ROOMS[state.room].floor]
      const d = cur.pos.distanceTo(cur.look)
      fogUniforms.uNear.value = d * 1.05
      fogUniforms.uFar.value = d * 1.9
      fogUniforms.uBedY.value = f.y + 0.02
      fogUniforms.uBedDepth.value = 0.55
    } else {
      fogUniforms.uNear.value = 3.5
      fogUniforms.uFar.value = 9
      fogUniforms.uBedY.value = 0.0
      fogUniforms.uBedDepth.value = 0.4
    }

    // Camera target for the scene.
    if (s === 'prologue' || s === 'exterior') {
      shot.pos.copy(STREET.pos)
      shot.look.copy(STREET.look)
      shot.fovX = camera.aspect < 0.8 ? 64 : STREET.fovX
      shot.shift = STREET.shift
    } else if (isRoom) {
      roomShot(state.room, state.local, shot)
    } else if (s === 'members') {
      shot.look.set(0, 0.1, -60)
      shot.pos.set(0, 0.85, -60 + 4.4 * (camera.aspect < 0.8 ? 1.8 : 1))
      shot.fovX = camera.aspect < 0.8 ? 60 : 38
      shot.shift = 0
    } else {
      shot.look.set(0.25, 0.15, -60)
      shot.pos.set(0.1, 0.75, -60 + 3.2 * (camera.aspect < 0.8 ? 1.6 : 1))
      shot.fovX = camera.aspect < 0.8 ? 60 : 36
      shot.shift = 0
    }
    // Inside a full veil the camera jumps; otherwise it eases.
    const k = state.veil > 0.97 || changed || state.still ? 1 : 1 - Math.pow(0.002, dt)
    cur.pos.lerp(shot.pos, k)
    cur.look.lerp(shot.look, k)
    cur.fovX = lerp(cur.fovX, shot.fovX, k)
    cur.shift = lerp(cur.shift, shot.shift, k)
    lastScene = sceneKey

    camera.position.copy(cur.pos)
    // A breath of parallax from the pointer.
    if (!state.still) {
      camera.position.x += state.mx * 0.06 * (isRoom ? 1 : 0.5)
      camera.position.y -= state.my * 0.04
    }
    camera.lookAt(cur.look)
    camera.fov = fovYFor(cur.fovX)
    if (Math.abs(cur.shift) > 1e-4) camera.setViewOffset(width, height, 0, -cur.shift * width, width, height)
    else camera.clearViewOffset()
    camera.updateProjectionMatrix()

    // The falling objects: down on scroll, a slow tumble in time.
    if (s === 'prologue') {
      for (const f of fallers) {
        const y = f.y0 - state.local * 2.6 + (state.still ? 0 : Math.sin(t * 0.7 + f.phase) * 0.02)
        f.o.position.set(f.x, y, f.z)
        const r = state.still ? 0 : t * 0.15
        f.o.rotation.set(f.spin[0] * (state.local + r), f.spin[1] * (state.local + r * 0.7), f.spin[2] * (state.local + r * 0.5))
        f.o.visible = y > 0.8 - 0.4
      }
    }
    // The membership in focus lifts a touch.
    tiers.forEach((g, i) => {
      g.position.y = lerp(g.position.y, state.tierFocus === i ? 0.03 : 0, 1 - Math.pow(0.001, dt))
    })

    renderer.render(scene, camera)
  }
  renderer.setAnimationLoop(frame)

  // Screen position of an anchor, for the copy that sits beside objects.
  const toScreen = (obj) => {
    obj.getWorldPosition(tmp)
    tmp.project(camera)
    return { x: (tmp.x * 0.5 + 0.5) * width, y: (-tmp.y * 0.5 + 0.5) * height, behind: tmp.z > 1 }
  }

  return {
    state,
    tierScreens: () => tierAnchors.map(toScreen),
    callScreen: () => toScreen(callAnchor),
  }
}
