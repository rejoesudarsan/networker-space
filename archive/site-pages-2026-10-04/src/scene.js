import * as THREE from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'

// One connected model: the four floors sit side by side at their own heights,
// joined by stairs, with a painted route running room to room. At the end the
// floors lift into a stack: the house. Each floor is a real model built from
// the as-built drawing (scripts/build-house.mjs → public/models/).
const GAP = 2.2 // stair gap between neighbouring floors
const RISE = 1.3 // height difference per storey in the connected scene
const STACK = 1.7 // storey spacing in the stacked house
const FOV = 32

const clamp01 = (v) => Math.min(1, Math.max(0, v))
const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2)
const mix = (a, b, k) => a + (b - a) * k
const hex = (h) => {
  const n = parseInt(h.slice(1), 16)
  return new THREE.Vector3(((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255)
}
const INK = 0x16130f
// "You are here": rani pink reads on every floor's paint.
const HERE = '#d2487a'

const vertex = /* glsl */ `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`
// Painted solids: one flat tone per face direction, never shaded. `vP` maps the
// model onto its floor (0–1, top-left origin) so the room being visited stays
// bright with a painted outline on the floor while the rest dims.
const solidVertex = /* glsl */ `
  uniform vec2 size;
  varying vec3 vN;
  varying vec2 vP;
  void main() {
    vN = normal;
    vP = position.xz / size + 0.5;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`
const solidFragment = /* glsl */ `
  uniform vec3 top;
  uniform vec3 side;
  uniform vec3 paint;
  uniform vec3 hi;
  uniform vec4 rect;
  uniform float dim;
  uniform float band;
  uniform vec2 size;
  varying vec3 vN;
  varying vec2 vP;
  void main() {
    vec3 col = vN.y > 0.5 ? top : side * (abs(vN.x) > 0.5 ? 0.82 : 0.66);
    vec2 inner = min(vP - rect.xy, rect.zw - vP);
    float inside = step(0.0, inner.x) * step(0.0, inner.y);
    float edge = inside * (1.0 - step(0.07 / size.x, inner.x) * step(0.07 / size.y, inner.y));
    vec3 muted = mix(col, paint, 0.6) * 0.86;
    col = mix(col, muted, dim * (1.0 - inside));
    col = mix(col, hi, edge * dim * band * step(0.5, vN.y));
    gl_FragColor = vec4(col, 1.0);
  }
`
// The route: a dashed painted ribbon that draws itself as you walk.
const routeFragment = /* glsl */ `
  uniform float progress;
  uniform float dashes;
  uniform vec3 color;
  uniform float opacity;
  varying vec2 vUv;
  void main() {
    if (vUv.x > progress) discard;
    if (fract(vUv.x * dashes) > 0.58) discard;
    gl_FragColor = vec4(color, opacity);
  }
`

function shadowTexture() {
  const c = document.createElement('canvas')
  c.width = c.height = 128
  const g = c.getContext('2d')
  const grad = g.createRadialGradient(64, 64, 8, 64, 64, 64)
  grad.addColorStop(0, 'rgba(22,19,15,0.55)')
  grad.addColorStop(1, 'rgba(22,19,15,0)')
  g.fillStyle = grad
  g.fillRect(0, 0, 128, 128)
  return new THREE.CanvasTexture(c)
}

function slab(w, h, d, color) {
  const geo = new THREE.BoxGeometry(w, h, d)
  const mesh = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ color }))
  mesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(geo), new THREE.LineBasicMaterial({ color: INK })))
  return mesh
}

export async function startScene(canvas, state, floors, rooms) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: 'high-performance' })
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2))
  // Colours are authored in sRGB, so skip output conversion.
  renderer.outputColorSpace = THREE.LinearSRGBColorSpace
  THREE.ColorManagement.enabled = false

  const scene = new THREE.Scene()
  const camera = new THREE.PerspectiveCamera(FOV, 1, 0.1, 500)
  const shadowMap = shadowTexture()
  const loader = new GLTFLoader()
  const [house, ...models] = await Promise.all([
    fetch('/models/house.json').then((r) => r.json()),
    ...floors.map((f) => loader.loadAsync(`/models/${f.plan}.glb`)),
  ])
  const SLAB = house.slab
  // The stacked house is centred on the middle of the floor footprints.
  const centre = new THREE.Vector2()
  floors.forEach((f) => centre.add(new THREE.Vector2(...house.floors[f.plan].offset)))
  centre.divideScalar(floors.length)

  // ---- lay the floors out as one connected strip ----
  const widths = floors.map((f) => house.floors[f.plan].width)
  const total = widths.reduce((s, w) => s + w, 0) + GAP * (floors.length - 1)
  let cursor = -total / 2
  const plates = floors.map((f, i) => {
    const w = widths[i]
    const { depth, offset } = house.floors[f.plan]
    const uniforms = {
      paint: { value: hex(f.paint) },
      hi: { value: hex(HERE) },
      rect: { value: new THREE.Vector4(2, 2, 2, 2) },
      dim: { value: 0 },
      size: { value: new THREE.Vector2(w, depth) },
    }
    // Floor in the paint, wall tops in the ink like poché on a plan, columns
    // in solid ink. Colours come from content.js, not the model files.
    const looks = {
      slab: { top: hex(f.paint), side: hex(f.paint).multiplyScalar(0.8), band: 1 },
      wall: { top: hex(f.ink), side: hex(f.paint), band: 0 },
      sill: { top: hex(f.ink), side: hex(f.paint), band: 0 },
      column: { top: hex('#16130f'), side: hex('#3a332a'), band: 0 },
    }
    const group = models[i].scene
    group.traverse((o) => {
      const look = o.material && looks[o.material.name]
      if (o.isLineSegments) {
        o.material = new THREE.LineBasicMaterial({ color: f.ink, transparent: true, opacity: 0.5 })
      } else if (look) {
        o.material = new THREE.ShaderMaterial({
          vertexShader: solidVertex,
          fragmentShader: solidFragment,
          uniforms: { ...uniforms, top: { value: look.top }, side: { value: look.side }, band: { value: look.band } },
        })
        o.add(new THREE.LineSegments(new THREE.EdgesGeometry(o.geometry, 30), new THREE.LineBasicMaterial({ color: INK })))
      }
    })

    const shadow = new THREE.Mesh(
      new THREE.PlaneGeometry(w * 1.4, depth * 1.4),
      new THREE.MeshBasicMaterial({ map: shadowMap, transparent: true, depthWrite: false, opacity: 0.5 }),
    )
    shadow.rotation.x = -Math.PI / 2
    shadow.position.y = -1.2
    group.add(shadow)
    scene.add(group)

    const line = new THREE.Vector3(cursor + w / 2, (f.level - 1) * RISE, 0)
    cursor += w + GAP
    // Stacked, every floor sits where the drawing's column grid puts it.
    const stack = new THREE.Vector3(offset[0] - centre.x, f.level * STACK - 1.5 * STACK, offset[1] - centre.y)
    return { f, w, depth, group, shadow, uniforms, line, stack }
  })
  const plateById = Object.fromEntries(plates.map((p) => [p.f.id, p]))

  // ---- stairs between neighbouring floors ----
  const stairs = new THREE.Group()
  const STEPS = 6
  for (let i = 0; i < plates.length - 1; i++) {
    const a = plates[i]
    const b = plates[i + 1]
    const x0 = a.line.x + a.w / 2
    const ya = a.line.y
    const yb = b.line.y
    for (let s = 0; s < STEPS; s++) {
      const k = (s + 0.5) / STEPS
      const topY = mix(ya, yb, (s + (yb > ya ? 1 : 0)) / STEPS)
      const bottom = Math.min(ya, yb) - SLAB
      const h = topY - bottom
      const step = slab(GAP / STEPS, h, 2.2, 0xf7f3e8)
      step.position.set(x0 + k * GAP, bottom + h / 2, 0)
      stairs.add(step)
    }
  }
  scene.add(stairs)

  // ---- rooms in world space ----
  const roomInfo = rooms.map((r) => {
    const p = plateById[r.floor]
    const [u0, v0, u1, v1] = r.rect
    const local = new THREE.Vector3(((u0 + u1) / 2 - 0.5) * p.w, 0, ((v0 + v1) / 2 - 0.5) * p.depth)
    return { plate: p, local, size: new THREE.Vector2((u1 - u0) * p.w, (v1 - v0) * p.depth), rect: r.rect }
  })
  const roomWorld = (info) => info.plate.line.clone().add(info.local)

  // ---- route ribbon through every room, via the stairs ----
  const pts = []
  const marks = []
  roomInfo.forEach((info, i) => {
    const prev = roomInfo[i - 1]
    if (prev && prev.plate !== info.plate) {
      const a = prev.plate
      const b = info.plate
      pts.push(new THREE.Vector3(a.line.x + a.w / 2 - 0.3, a.line.y + 0.08, 0))
      pts.push(new THREE.Vector3(b.line.x - b.w / 2 + 0.3, b.line.y + 0.08, 0))
    }
    const c = roomWorld(info)
    c.y += 0.08
    marks.push(pts.length)
    pts.push(c)
  })
  const path = new THREE.CurvePath()
  for (let i = 0; i < pts.length - 1; i++) path.add(new THREE.LineCurve3(pts[i], pts[i + 1]))
  const lengths = [0]
  for (let i = 0; i < pts.length - 1; i++) lengths.push(lengths[i] + pts[i].distanceTo(pts[i + 1]))
  const routeLen = lengths.at(-1)
  const roomProgress = marks.map((m) => lengths[m] / routeLen)
  const routeUniforms = {
    progress: { value: 0 },
    dashes: { value: routeLen / 0.45 },
    color: { value: hex(HERE) },
    opacity: { value: 1 },
  }
  const route = new THREE.Mesh(
    new THREE.TubeGeometry(path, pts.length * 40, 0.055, 6, false),
    new THREE.ShaderMaterial({ vertexShader: vertex, fragmentShader: routeFragment, uniforms: routeUniforms, transparent: true }),
  )
  scene.add(route)

  // A painted marker that stands on the room being visited.
  const marker = new THREE.Group()
  const pole = slab(0.05, 1.1, 0.05, INK)
  pole.position.y = 0.55
  const flag = slab(0.6, 0.36, 0.04, new THREE.Color(HERE))
  flag.position.set(0.32, 0.9, 0)
  const ring = new THREE.Mesh(
    new THREE.RingGeometry(0.17, 0.26, 40),
    new THREE.MeshBasicMaterial({ color: new THREE.Color(HERE), side: THREE.DoubleSide }),
  )
  ring.rotation.x = -Math.PI / 2
  ring.position.y = 0.02
  marker.add(pole, flag, ring)
  scene.add(marker)

  // ---- input + sizing ----
  const pointer = new THREE.Vector2()
  addEventListener('pointermove', (e) => pointer.set((e.clientX / innerWidth) * 2 - 1, (e.clientY / innerHeight) * 2 - 1), {
    passive: true,
  })
  const resize = () => {
    renderer.setSize(innerWidth, innerHeight, false)
    camera.aspect = innerWidth / innerHeight
    camera.updateProjectionMatrix()
  }
  addEventListener('resize', resize)
  resize()

  // ---- camera shots: look point, distance, elevation and yaw ----
  const tanHalf = Math.tan(THREE.MathUtils.degToRad(FOV / 2))
  const portrait = () => camera.aspect < 0.9
  const shot = (look, dist, elev, yaw) => ({ look, dist, elev, yaw })
  const blend = (a, b, k) =>
    shot(a.look.clone().lerp(b.look, k), mix(a.dist, b.dist, k), mix(a.elev, b.elev, k), mix(a.yaw, b.yaw, k))

  const heroShot = () => {
    // Phones: run the strip away from the viewer, above the hero board.
    if (portrait()) return shot(new THREE.Vector3(0, 0, 7), (total * 0.42) / (2 * tanHalf * 0.75), 0.85, -1.05)
    const look = new THREE.Vector3(-total * 0.17, 0.5, 0)
    return shot(look, (total * 0.62) / (2 * tanHalf * Math.min(1.6, camera.aspect)), 0.75, -0.55)
  }
  const roomShot = (i) => {
    const info = roomInfo[i]
    const look = roomWorld(info)
    // Fit the room in the middle ~55% of the screen.
    const fitH = (info.size.y * 2.3) / (2 * tanHalf)
    const fitW = (info.size.x * 2.3) / (2 * tanHalf * camera.aspect)
    const dist = Math.max(14, fitH, fitW) * (portrait() ? 1.1 : 1)
    // On phones the room sits in the upper half, above the info card.
    if (portrait()) look.z += dist * tanHalf * 0.32
    return shot(look, dist, 1.05, i % 2 ? 0.22 : -0.22)
  }
  const houseShot = (a) => {
    const fit = portrait() ? 0.95 / camera.aspect : camera.aspect < 1.3 ? 1.25 : 1
    const look = new THREE.Vector3(portrait() ? 0 : -5.4 * fit, portrait() ? -6.8 : -0.4, 0)
    return shot(look, 26 * fit, 0.42, -0.55 + a * 0.9)
  }

  const camPos = new THREE.Vector3()
  const camLook = new THREE.Vector3()
  const goalPos = new THREE.Vector3()
  const goalLook = new THREE.Vector3()
  const parallax = new THREE.Vector2()
  let first = true
  const timer = new THREE.Timer()

  function frame() {
    requestAnimationFrame(frame)
    if (state.hidden) return
    timer.update()
    const t = timer.getElapsed()
    const a = ease(clamp01(state.assemble * 1.25))
    const hero = ease(clamp01(state.hero))
    const i0 = Math.floor(state.stop)
    const i1 = Math.min(rooms.length - 1, i0 + 1)
    const k = ease(state.stop - i0)

    // Plates: connected strip → stacked house, lower floors landing first.
    plates.forEach((p, i) => {
      const kk = ease(clamp01(state.assemble * 1.6 - p.f.level * 0.12))
      p.group.position.lerpVectors(p.line, p.stack, kk)
      p.group.position.y += Math.sin(kk * Math.PI) * 2.2
      p.group.rotation.y = Math.sin(kk * Math.PI) * 0.3 * (i % 2 ? 1 : -1)
      p.shadow.material.opacity = 0.5 * (1 - kk) + (p.f.level === 0 ? 0.5 * kk : 0)
      p.shadow.position.y = -1.2 - p.f.level * STACK * kk
    })
    const strip = 1 - clamp01(state.assemble * 5)
    stairs.visible = route.visible = marker.visible = strip > 0.01
    stairs.scale.y = strip
    routeUniforms.opacity.value = strip

    // Highlight the room being visited.
    const active = roomInfo[Math.round(state.stop)]
    const focus = clamp01((state.hero - 0.5) * 2) * strip
    plates.forEach((p) => {
      p.uniforms.dim.value = focus
      p.uniforms.rect.value.set(...(p === active.plate ? active.rect : [2, 2, 2, 2]))
    })

    // Route draws up to the current position; the marker walks with it.
    const rp = mix(roomProgress[i0], roomProgress[i1], k)
    routeUniforms.progress.value = rp * clamp01(state.hero * 1.5)
    marker.position.copy(path.getPointAt(Math.min(0.9999, rp)))
    marker.position.y -= 0.08
    marker.scale.setScalar(focus * (1 + Math.sin(t * 3) * 0.04))
    flag.rotation.y = Math.sin(t * 1.4) * 0.25

    // Camera: hero overview → room by room → orbit the stacked house.
    let s = blend(roomShot(i0), roomShot(i1), k)
    s.dist *= 1 + Math.sin(k * Math.PI) * 0.35 // pull back a little between rooms
    s = blend(heroShot(), s, hero)
    s = blend(s, houseShot(a), a)
    const elev = s.elev
    goalPos.set(
      s.look.x + Math.sin(s.yaw) * Math.cos(elev) * s.dist,
      s.look.y + Math.sin(elev) * s.dist,
      s.look.z + Math.cos(s.yaw) * Math.cos(elev) * s.dist,
    )
    goalLook.copy(s.look)
    parallax.lerp(pointer, 0.05)
    goalPos.x += parallax.x * 0.6
    goalPos.y -= parallax.y * 0.4

    const lerp = first ? 1 : 0.1
    camPos.lerp(goalPos, lerp)
    camLook.lerp(goalLook, lerp)
    first = false
    camera.position.copy(camPos)
    camera.lookAt(camLook)
    renderer.render(scene, camera)
  }
  canvas.classList.add('is-ready')
  frame()
}
