import * as THREE from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { RGBELoader } from 'three/examples/jsm/loaders/RGBELoader.js'
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js'
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js'
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js'
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js'
import { ROOMS, PROGRAM, partAt } from './program.js'
import { createPerson as person, posePerson, poseFor, createFurnishings } from './characters.js'
import { addWorldDetails } from './details.js'
import { createVehicle, rollVehicle } from './traffic.js'
import { addWindows } from './windows.js'
import { createEnvironment } from './environment.js'

// The house at the centre of a small, quiet world that lives through one day.
// Progress (0 → 1) runs the day from dawn to late night: the house opens,
// floor by floor, to show what each room has become, then settles back
// together. People walk in and out of the gate the whole time.
// Floors come from the as-built drawing (scripts/build-house.mjs); one world
// unit is 8 ft.

// ---------- palette: the materials of the house ----------
const C = {
  plaster: '#ecebe4',
  plasterShade: '#dedad1',
  terrazzo: '#d9d3c7',
  kota: '#b9a68a',
  teak: '#7a3f1f',
  terracotta: '#b4643f',
  redOxide: '#7d2a22',
  steel: '#4a4d4f',
  granite: '#1d1d1c',
  foliage: '#4d6b35',
  foliageLight: '#6f8d47',
  gulmohar: '#e0531f',
  earth: '#a65a3a',
  asphalt: '#6a6660',
  lamp: '#ffc78a',
}

const STOREY = 1.45
const WALL = 1.3
const LEVEL = { basement: -0.72, ground: 0.73, first: 2.18, second: 3.63 }
// When the house opens, every floor lifts and parts; floors above the one in
// view rise clear out of the frame so that floor is open to the sky.
const ORDER = ['basement', 'ground', 'first', 'second']
const PART = { basement: 0, ground: 1.9, first: 2.8, second: 3.7 }
const CLEAR = 7

const smooth = (a, b, x) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)))
  return t * t * (3 - 2 * t)
}
const lerp = (a, b, k) => a + (b - a) * k
const rand = (a, b) => a + Math.random() * (b - a)
const pick = (arr) => arr[Math.floor(Math.random() * arr.length)]

// ---------- the light through the day ----------
// [hour, sky/fog, sun colour, sun intensity, hemi sky, hemi ground, hemi intensity, night]
const SKY = [
  [6, '#e9c9c0', '#ffc394', 1.6, '#e9d4d4', '#c4a78a', 0.7, 0.15],
  [8, '#efeae2', '#ffe6c8', 3.2, '#f3f1ec', '#d2bf9f', 1.45, 0],
  [12, '#f1efe9', '#fff7ea', 3.6, '#f6f6f2', '#d8c9ae', 1.55, 0],
  [16, '#efe5d6', '#ffd6a0', 3.2, '#f4eee4', '#d0b68f', 1.35, 0],
  [17.8, '#dcb592', '#ff9c5a', 1.6, '#e8c9a8', '#a67b5a', 0.8, 0.12],
  [19, '#463d46', '#ff7a45', 0.3, '#6d6276', '#4a3a33', 0.45, 0.75],
  [20.5, '#1c1f27', '#9db2d6', 0.22, '#2b3242', '#1e1a17', 0.32, 1],
  [23.5, '#121419', '#8ea3c9', 0.16, '#20263a', '#151210', 0.26, 1],
]
const cA = new THREE.Color()
const cB = new THREE.Color()
function skyAt(h) {
  let i = 0
  while (i < SKY.length - 2 && h > SKY[i + 1][0]) i++
  const a = SKY[i]
  const b = SKY[i + 1]
  const k = smooth(0, 1, (h - a[0]) / (b[0] - a[0]))
  const col = (j) => new THREE.Color(cA.set(a[j]).lerp(cB.set(b[j]), k))
  return { sky: col(1), sun: col(2), sunI: lerp(a[3], b[3], k), hemiSky: col(4), hemiGround: col(5), hemiI: lerp(a[6], b[6], k), night: lerp(a[7], b[7], k) }
}

// ---------- the routes people walk (world coordinates; tag = floor they ride with) ----------
const STREET_Z = 5.65
const FAR_Z = 9.85
const P = (x, y, z, tag = null) => ({ v: new THREE.Vector3(x, y, z), tag })
const GATE = [P(-2.75, 0, STREET_Z), P(-2.75, 0.73, 4.65, 'ground'), P(-2.6, 0.73, 2.6, 'ground'), P(-2.05, 0.73, 0.65, 'ground')]
const ROUTES = {
  in: () => [P(pick([-26, 26]), 0, STREET_Z + rand(-0.15, 0.15)), ...GATE, P(-1.05, 0.73, 0.15, 'ground')],
  up: () => [P(pick([-26, 26]), 0, STREET_Z + rand(-0.15, 0.15)), ...GATE, P(-1.9, 0.73, -0.45, 'ground'), P(-2.85, 2.18, -0.45, 'first'), P(-1.25, 2.18, 0.1, 'first')],
  office: () => [P(pick([-26, 26]), 0, STREET_Z + rand(-0.15, 0.15)), P(2.92, 0, STREET_Z), P(2.92, 0, 4.71), P(2.62, 0, 4.71, 'basement'), P(1.66, -0.72, 4.71, 'basement'), P(1.5, -0.72, 4.15, 'basement'), P(1.45, -0.72, 3.45, 'basement')],
  pass: () => {
    const z = Math.random() < 0.7 ? STREET_Z + rand(-0.2, 0.25) : FAR_Z + rand(-0.15, 0.15)
    const dir = Math.random() < 0.5 ? 1 : -1
    return [P(-26 * dir, 0, z), P(26 * dir, 0, z)]
  },
}
const reverse = (pts) => pts.slice().reverse().map((p) => ({ ...p, v: p.v.clone() }))
const END = (pts) => [...pts, P(pick([-26, 26]), 0, STREET_Z + rand(-0.15, 0.15))]

// Spawn rates (people per second) by hour.
const window_ = (h, a, b, ramp = 0.6) => smooth(a - ramp, a, h) * (1 - smooth(b, b + ramp, h))
const RATES = (h) => ({
  pass: 0.22 + 0.35 * window_(h, 17.5, 22) + 0.15 * window_(h, 8, 10),
  in: 0.08 + 0.35 * window_(h, 6.5, 10) + 0.08 * window_(h, 10, 17) + 0.65 * window_(h, 18, 21.5) + 0.45 * window_(h, 21.5, 24),
  out: 0.06 + 0.06 * window_(h, 10, 17) + 0.25 * window_(h, 17, 19) + 0.55 * window_(h, 22, 24),
  up: 0.02 + 0.05 * window_(h, 9, 17) + 0.28 * window_(h, 18.5, 22),
  office: 0.02 + 0.28 * window_(h, 8.3, 10) ,
  officeOut: 0.02 + 0.3 * window_(h, 17, 19.5),
  vehicle: 0.12 + 0.1 * window_(h, 8, 11) + 0.12 * window_(h, 17, 21),
})

// ---------- people ----------
const matCache = new Map()
const mat = (color, opts = {}) => {
  const key = color + JSON.stringify(opts)
  if (!matCache.has(key)) matCache.set(key, new THREE.MeshStandardMaterial({ color, roughness: 0.85, ...opts }))
  return matCache.get(key)
}
// ---------- trees ----------
const leafGeo = new THREE.IcosahedronGeometry(1, 1)
const flowerGeo = new THREE.IcosahedronGeometry(0.045, 0)
const branchGeo = new THREE.CylinderGeometry(0.025, 0.05, 1, 6)
function tree({ height = 2.4, spread = 1, flowers = 0, tone = C.foliage }) {
  const g = new THREE.Group()
  const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.05 * spread, 0.09 * spread, height * 0.6, 7), mat('#5a4636'))
  trunk.position.y = height * 0.3
  trunk.castShadow = true
  g.add(trunk)
  for (let i = 0; i < 4; i++) {
    const branch = new THREE.Mesh(branchGeo, mat('#5a4636'))
    const angle = i * Math.PI / 2 + 0.3
    const start = new THREE.Vector3(0, height * (0.36 + i * 0.035), 0)
    const end = new THREE.Vector3(Math.cos(angle) * spread * 0.45, height * 0.72, Math.sin(angle) * spread * 0.45)
    branch.position.copy(start).lerp(end, 0.5)
    branch.scale.set(spread, start.distanceTo(end), spread)
    branch.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), end.sub(start).normalize())
    branch.castShadow = true
    g.add(branch)
  }
  const crown = new THREE.Group()
  crown.position.y = height * 0.62
  const blobs = 5 + Math.round(spread * 3)
  for (let i = 0; i < blobs; i++) {
    const s = rand(0.35, 0.6) * spread
    const m = new THREE.Mesh(leafGeo, mat(i % 3 ? tone : C.foliageLight, { flatShading: true }))
    m.scale.set(s, s * 0.75, s)
    const a = (i / blobs) * Math.PI * 2
    const r = i === 0 ? 0 : rand(0.25, 0.6) * spread
    m.position.set(Math.cos(a) * r, rand(0, 0.45) * spread, Math.sin(a) * r)
    m.castShadow = true
    m.receiveShadow = true
    crown.add(m)
  }
  const blossoms = flowers ? new THREE.InstancedMesh(flowerGeo, mat(C.gulmohar, { flatShading: true }), flowers) : null
  const flowerTransform = new THREE.Object3D()
  for (let i = 0; i < flowers; i++) {
    const a = rand(0, Math.PI * 2)
    const r = rand(0.15, 0.85) * spread
    flowerTransform.position.set(Math.cos(a) * r, rand(0.3, 0.75) * spread, Math.sin(a) * r)
    flowerTransform.scale.setScalar(rand(0.7, 1.3))
    flowerTransform.updateMatrix()
    blossoms.setMatrixAt(i, flowerTransform.matrix)
    blossoms.setColorAt(i, new THREE.Color(i % 4 ? C.gulmohar : '#f08a3c'))
  }
  if (blossoms) crown.add(blossoms)
  g.add(crown)
  g.userData.crown = crown
  g.userData.phase = rand(0, 10)
  return g
}

// ---------- geometry helpers ----------
function slabGeo(w, d, depth, holes = []) {
  const outline = [[-w / 2, -d / 2], [w / 2, -d / 2], [w / 2, d / 2]]
  // Entrances cut the perimeter; treating them as closed holes leaves a
  // sliver across the mouth or produces overlapping extrusion triangles.
  const mouths = holes.filter((h) => h[3] >= d / 2).sort((a, b) => b[2] - a[2])
  for (const [x0, z0, x1] of mouths) outline.push([x1, d / 2], [x1, z0], [x0, z0], [x0, d / 2])
  outline.push([-w / 2, d / 2])
  const s = new THREE.Shape(outline.map(([x, z]) => new THREE.Vector2(x, z)))
  s.holes = holes.filter((h) => h[3] < d / 2).map(([x0, z0, x1, z1]) => new THREE.Path([new THREE.Vector2(x0, z0), new THREE.Vector2(x0, z1), new THREE.Vector2(x1, z1), new THREE.Vector2(x1, z0)]))
  const g = new THREE.ExtrudeGeometry(s, { depth, bevelEnabled: false })
  g.rotateX(Math.PI / 2) // shape (x, z) → extrude downward
  return g
}
const boxGeos = new Map()
function box(w, h, d, color, x = 0, y = 0, z = 0, o = {}) {
  const gk = `${w}|${h}|${d}`
  if (!boxGeos.has(gk)) boxGeos.set(gk, new THREE.BoxGeometry(w, h, d))
  const { cast = true, ...materialOptions } = o
  const m = new THREE.Mesh(boxGeos.get(gk), mat(color, materialOptions))
  m.position.set(x, y + h / 2, z)
  m.castShadow = cast
  m.receiveShadow = true
  return m
}
const patch = (x0, z0, x1, z1, color, y = 0.006) => {
  const m = new THREE.Mesh(new THREE.BoxGeometry(x1 - x0, 0.012, z1 - z0), mat(color))
  m.position.set((x0 + x1) / 2, y, (z0 + z1) / 2)
  m.receiveShadow = true
  return m
}

export async function createWorld(canvas) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' })
  renderer.setPixelRatio(Math.min(devicePixelRatio, 1.75))
  renderer.shadowMap.enabled = true
  renderer.shadowMap.type = THREE.PCFSoftShadowMap
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  renderer.toneMappingExposure = 1.12

  const scene = new THREE.Scene()
  scene.fog = new THREE.Fog('#ecebe4', 24, 58)
  scene.background = new THREE.Color('#ecebe4')
  const camera = new THREE.PerspectiveCamera(30, 1, 0.1, 200)

  // ---------- light ----------
  const hemi = new THREE.HemisphereLight('#ffffff', '#c9b79c', 1)
  const sun = new THREE.DirectionalLight('#ffffff', 2.5)
  sun.castShadow = true
  sun.shadow.mapSize.set(2048, 2048)
  Object.assign(sun.shadow.camera, { left: -16, right: 16, top: 16, bottom: -16, near: 1, far: 70 })
  sun.shadow.bias = -0.0004
  sun.shadow.normalBias = 0.02
  sun.shadow.radius = 4
  scene.add(hemi, sun, sun.target)
  // Image-based light: the same sunrise HDRI the Blender renders use, so
  // plaster, teak and glass pick up a real sky instead of a flat ambient.
  try {
    const hdr = await new RGBELoader().loadAsync('/world/env/sunrise_1k.hdr')
    const pmrem = new THREE.PMREMGenerator(renderer)
    scene.environment = pmrem.fromEquirectangular(hdr).texture
    scene.environmentRotation.y = Math.PI * 0.6
    hdr.dispose()
    pmrem.dispose()
  } catch (e) {
    console.warn('no HDRI', e)
  }

  const loader = new GLTFLoader()
  const [house, ...gltfs] = await Promise.all([
    fetch('/models/house.json').then((r) => r.json()),
    ...Object.keys(LEVEL).map((id) => loader.loadAsync(`/models/${id}.glb`)),
  ])
  // The Blender model's details, one GLB per floor (blender/tools/export_site.py).
  // When all four are present they replace the hand-built floor detail below.
  const maxAniso = renderer.capabilities.getMaxAnisotropy()
  const loadBlender = async (name) => {
    const g = await loader.loadAsync(`/models/blender/${name}.gltf`).catch(() => loader.loadAsync(`/models/blender/${name}.glb`)).catch(() => null)
    if (!g) return null
    // Textured export: the material's tint and roughness scale ride in its extras.
    g.scene.traverse((o) => {
      if (!o.isMesh) return
      const m = o.material
      const x = m.userData || {}
      if (x.tint) m.color.setRGB(x.tint[0], x.tint[1], x.tint[2])
      if (x.rough != null) m.roughness = x.rough
      for (const k of ['map', 'roughnessMap', 'metalnessMap', 'normalMap']) if (m[k]) m[k].anisotropy = maxAniso
      if (m.map && !m.map.wrapS) m.map.wrapS = m.map.wrapT = THREE.RepeatWrapping
    })
    return g
  }
  const blenderFloors = await Promise.all(Object.keys(LEVEL).map(loadBlender))
  const useBlender = blenderFloors.every(Boolean)
  // The roof (slab, parapets, terrace eave, skylight), in the second floor's frame.
  const blenderRoof = useBlender ? await loadBlender('roof') : null
  const roofParts = []
  // Outside the house: gulmohars, neighbour houses, office gate (street frame).
  const blenderSite = useBlender ? await loadBlender('site') : null
  // Parts hung above the floor (lanterns, fans, wall cabinets): hidden while the walls are cut away.
  const highParts = []

  // ---------- the ground: a plot of the street, with a pit where the house sits ----------
  const street = new THREE.Group()
  scene.add(street)
  const ground = new THREE.Group()
  street.add(ground)
  {
    const basementInfo = house.floors.basement
    const bx0 = basementInfo.offset[0] - basementInfo.width / 2 - 0.025
    const bx1 = basementInfo.offset[0] + basementInfo.width / 2 + 0.025
    const bz0 = basementInfo.offset[1] - basementInfo.depth / 2 - 0.025
    const bz1 = basementInfo.offset[1] + basementInfo.depth / 2 + 0.025
    const disk = new THREE.Shape()
    disk.absarc(0, 0, 60, 0, Math.PI * 2)
    // ShapeGeometry rotates -90° to face upward, so its 2D y is world -z.
    disk.holes.push(new THREE.Path([new THREE.Vector2(bx0, -bz0), new THREE.Vector2(bx0, -bz1), new THREE.Vector2(bx1, -bz1), new THREE.Vector2(bx1, -bz0)]))
    const g = new THREE.ShapeGeometry(disk, 48)
    g.rotateX(-Math.PI / 2)
    const plane = new THREE.Mesh(g, mat('#d8d0c2'))
    plane.receiveShadow = true
    ground.add(plane)
    // The street in front: red-earth verges, asphalt, a far pavement.
    ground.add(patch(-60, 5.0, 60, 6.15, '#cfc6b6', 0.004))
    ground.add(patch(-60, 6.15, 60, 6.5, C.earth, 0.004))
    ground.add(patch(-60, 6.5, 60, 9.25, C.asphalt, 0.003))
    ground.add(patch(-60, 9.25, 60, 9.55, C.earth, 0.004))
    // The pit's walls: a cut through red earth.
    const pit = (w, d, x, z) => {
      const m = new THREE.Mesh(new THREE.BoxGeometry(w, 0.9, d), mat('#9a5a3c'))
      m.position.set(x, -0.45, z)
      m.receiveShadow = true
      ground.add(m)
    }
    pit(bx1 - bx0, 0.05, (bx0 + bx1) / 2, bz0)
    // Retaining edges follow the basement footprint, not the larger plot.
    // At the front the garage ramp and office stair remain open.
    pit(1.45, 0.05, 0.525, bz1)
    pit(bx1 - 1.25, 0.05, (bx1 + 1.25) / 2, bz1)
    pit(0.05, bz1 - bz0, bx0, (bz0 + bz1) / 2)
    pit(0.05, bz1 - bz0, bx1, (bz0 + bz1) / 2)
    const floor = patch(bx0, bz0, bx1, bz1, '#7d4a33', -0.88)
    ground.add(floor)
  }

  // Neighbours: plain massing, so the house stays the subject.
  const neighbours = [
    [-10.5, 6, 9, 1.3, -0.4], [10.8, 6.4, 9.4, 1.7, -0.2], [-18, 6.4, 9, 1.1, 0], [18.4, 6.2, 9.2, 1.5, -0.3],
    [-9, 6.5, 6, 1.2, 15], [-1.6, 6.8, 6, 1.6, 15], [5.6, 6.2, 6, 1.1, 15], [12.6, 6.6, 6, 1.4, 15],
  ]
  if (blenderSite) {
    blenderSite.scene.traverse((o) => {
      if (o.isMesh) o.castShadow = o.receiveShadow = true
    })
    ground.add(blenderSite.scene)
  }
  for (const [x, w, d, h, z] of blenderSite ? [] : neighbours) {
    const b = box(w, h, d, Math.random() < 0.5 ? '#e6e3dc' : '#e1ddd5', x, 0, z)
    ground.add(b)
    // A low compound wall in front of each.
    ground.add(box(w, 0.32, 0.08, '#d4cfc5', x, 0, z + (z > 10 ? -d / 2 - 0.4 : d / 2 + 0.3)))
  }

  // ---------- the house ----------
  const SLAB = house.slab
  const wallMat = mat(C.plaster)
  const sillMat = mat(C.plasterShade)
  const detailMat = new THREE.LineBasicMaterial({ color: '#a8977c', transparent: true, opacity: 0.55 })
  const floors = {}
  const walls = []
  Object.keys(LEVEL).forEach((id, i) => {
    const info = house.floors[id]
    const g = new THREE.Group()
    g.position.set(info.offset[0], LEVEL[id], info.offset[1])
    g.userData = { id, info }
    gltfs[i].scene.traverse((o) => {
      if (o.name === 'slab') o.visible = false
      if (o.isMesh && o.name === 'walls') {
        o.material = wallMat
        o.scale.y = WALL / house.wallHeight
        walls.push({ o, full: WALL / house.wallHeight, low: 0.42 / house.wallHeight })
      } else if (o.isMesh && o.name === 'columns') {
        o.material = wallMat
        o.scale.y = WALL / (house.wallHeight + 6 / 96)
        walls.push({ o, full: o.scale.y, low: 0.5 / (house.wallHeight + 6 / 96) })
      } else if (o.isMesh && o.name === 'sills') {
        o.material = sillMat
      } else if (o.isLineSegments) {
        o.material = detailMat
        o.position.y = 0.01
      }
      if (o.isMesh) {
        o.castShadow = true
        o.receiveShadow = true
      }
    })
    g.add(gltfs[i].scene)
    walls.push(addWindows(g, gltfs[i].scene))
    if (useBlender) {
      let ownWalls = false
      blenderFloors[i].scene.traverse((o) => {
        if (!o.isMesh) return
        o.castShadow = true
        o.receiveShadow = true
        if (/_high(\.\d+)?$/.test(o.name)) highParts.push(o)
        if (/_wall(\.\d+)?$/.test(o.name)) {
          walls.push({ o, full: 1, low: 0.42 / WALL })
          if (o.name.startsWith('Lime White')) ownWalls = true
        }
      })
      g.add(blenderFloors[i].scene)
      // The export carries the plastered walls and columns; the flat CAD ones step aside.
      if (ownWalls) gltfs[i].scene.traverse((o) => { if (o.isMesh && (o.name === 'walls' || o.name === 'columns')) o.visible = false })
    }
    floors[id] = g
    scene.add(g)
  })

  // Slabs with the real voids: ground over basement Court 1 and the office's
  // sunken entry court; second over the first-floor courtyard.
  const slabs = {
    basement: [],
    ground: [[0.56, -0.65, 1.99, 0.8], [1.25, 3.27, 3.12, 5.01], [-1.85, 3.2, -0.2, 5.01]],
    first: [],
    second: [[0.18, -0.49, 1.88, 1.06]],
  }
  for (const [id, holes] of Object.entries(slabs)) {
    if (useBlender) {
      const marker = new THREE.Object3D()
      marker.userData.voids = holes
      floors[id].add(marker)
      continue
    }
    const { width, depth } = house.floors[id]
    const m = new THREE.Mesh(slabGeo(width, depth, SLAB, holes), mat(C.terrazzo))
    m.userData.voids = holes
    m.castShadow = m.receiveShadow = true
    floors[id].add(m)
  }

  const G = floors.ground
  const F = floors.first
  const S = floors.second
  if (blenderRoof) {
    blenderRoof.scene.traverse((o) => {
      if (!o.isMesh) return
      o.castShadow = true
      o.receiveShadow = true
      roofParts.push(o)
    })
    S.add(blenderRoof.scene)
  }
  if (!useBlender) {
    // Surfaces from the photos.
    G.add(patch(-0.2, 3.3, 1.2, 4.95, '#6f8a45'))       // front lawn
    G.add(patch(-2.95, -2.6, -1.85, -0.75, '#6f8a45'))   // side garden
    G.add(patch(-2.95, 0.8, -2.3, 4.95, C.kota))         // side passage
    G.add(patch(-2.3, -0.3, -1.55, 1.3, '#a99a86'))      // entrance court stone
    G.add(patch(0.56, 0.2, 2.4, 3.2, '#8a5232'))         // Living 1: the teak floor
    // A skirt from the street up to the raised ground floor, and steps at the gate.
    const skirt = (w, d, x, z) => G.add(box(w, 0.6, d, C.plasterShade, x, -0.73, z))
    skirt(1.275, 0.06, -2.4875, 4.97)
    skirt(1.45, 0.06, 0.525, 4.97)
    skirt(6.25, 0.06, 0, -4.97)
    skirt(0.06, 10, -3.1, 0)
    skirt(0.06, 9.45, 3.1, -0.275)
    for (let s = 0; s < 4; s++) G.add(box(0.8, 0.73 - s * 0.18, 0.22, C.kota, -2.75, -0.73, 5.05 + s * 0.2))
    // The outside stair to the first floor (#6), charcoal rail.
    for (let s = 0; s < 9; s++) G.add(box(0.12, 0.16 * (s + 1), 0.5, C.kota, -1.95 - s * 0.11, 0, -0.45))
    G.add(box(1.05, 0.04, 0.03, C.steel, -2.4, 1.2, -0.7))

    F.add(patch(0.75, 0.3, 2.45, 1.95, '#bfae92'))       // courtyard flagstones
    S.add(patch(-2.2, -3.4, -0.85, 3.35, C.terracotta))  // the terrace
    // Skylight over the courtyard void.
    const glass = new THREE.Mesh(new THREE.BoxGeometry(1.7, 0.02, 1.55), new THREE.MeshPhysicalMaterial({ color: '#dfe8ea', transparent: true, opacity: 0.22, roughness: 0.05 }))
    glass.position.set(1.03, WALL + 0.02, 0.28)
    S.add(glass)
    S.add(box(1.76, 0.05, 0.05, C.steel, 1.03, WALL, -0.5), box(1.76, 0.05, 0.05, C.steel, 1.03, WALL, 1.06))
  }

  // Trees: gulmohar on the street, frangipani at the entrance, the olive in
  // the first-floor courtyard, the big tree rising out of basement Court 1.
  const trees = []
  const plant = (parent, t, x, y, z) => {
    t.position.set(x, y, z)
    parent.add(t)
    trees.push(t)
  }
  if (!blenderSite) {
    plant(ground, tree({ height: 3.6, spread: 1.5, flowers: 70 }), -4.6, 0, 6.3)
    plant(ground, tree({ height: 3.3, spread: 1.35, flowers: 55 }), 5.8, 0, 6.3)
    plant(ground, tree({ height: 3.4, spread: 1.4, flowers: 40 }), -9.5, 0, 9.4)
    plant(ground, tree({ height: 3.1, spread: 1.3, flowers: 0 }), 9.8, 0, 9.4)
  }
  if (!useBlender) {
    plant(G, tree({ height: 1.7, spread: 0.75 }), -2.55, 0, 1.6)
    plant(F, tree({ height: 1.25, spread: 0.45, tone: '#57703f' }), 1.95, 0, 1.55)
    plant(floors.basement, tree({ height: 2.9, spread: 0.85 }), 0.85, 0, -1.55)
  }

  // Nest pendants in the courtyard, terrace string lights, street lamps.
  const glow = []
  const nest = (parent, x, y, z, r = 0.12) => {
    const m = new THREE.Mesh(new THREE.IcosahedronGeometry(r, 1), new THREE.MeshStandardMaterial({ color: '#6b4a2e', emissive: C.lamp, emissiveIntensity: 0, roughness: 1, flatShading: true }))
    m.position.set(x, y, z)
    parent.add(m)
    glow.push({ m, k: 2.2 })
  }
  if (!useBlender) {
    nest(F, 1.4, 1.9, 0.9)
    nest(F, 1.75, 1.6, 1.15, 0.1)
    nest(F, 1.55, 1.35, 0.7, 0.13)
    for (const [x, y, z] of [[1.4, 1.9, 0.9], [1.75, 1.6, 1.15], [1.55, 1.35, 0.7]]) {
      F.add(box(0.009, 2.6 - y, 0.009, '#514b3e', x, y, z, { cast: false }))
    }
  }
  const festoonPoints = []
  for (let i = 0; i < 16; i++) {
    const z = -3.2 + i * 0.42
    const m = new THREE.Mesh(new THREE.SphereGeometry(0.03, 8, 6), new THREE.MeshStandardMaterial({ color: '#fff3dc', emissive: C.lamp, emissiveIntensity: 0 }))
    m.position.set(-2.15, 1.05 + Math.sin(i * 0.9) * 0.04, z)
    festoonPoints.push(m.position.clone().add(new THREE.Vector3(0, 0.035, 0)))
    S.add(m)
    glow.push({ m, k: 6, evening: true })
  }
  const festoon = new THREE.Line(new THREE.BufferGeometry().setFromPoints(festoonPoints), new THREE.LineBasicMaterial({ color: '#555245' }))
  S.add(festoon)
  const streetLights = []
  for (const x of [-11, -3.6, 5.2, 13]) {
    ground.add(box(0.06, 2.6, 0.06, C.steel, x, 0, 6.3))
    const head = new THREE.Mesh(new THREE.BoxGeometry(0.34, 0.06, 0.14), new THREE.MeshStandardMaterial({ color: '#2b2b2b', emissive: C.lamp, emissiveIntensity: 0 }))
    head.position.set(x, 2.6, 6.45)
    ground.add(head)
    glow.push({ m: head, k: 8 })
    const l = new THREE.PointLight(C.lamp, 0, 7, 2)
    l.position.set(x, 2.4, 6.6)
    ground.add(l)
    streetLights.push(l)
  }
  // A warm light inside each floor, for the evening.
  const roomLights = Object.entries(floors).map(([id, g]) => {
    const l = new THREE.PointLight('#ffb46b', 0, 10, 1.2)
    l.position.set(0.2, 2.2, 0.3)
    g.add(l)
    return l
  })

  addWorldDetails({ ground, floors, house, streetOnly: useBlender, noNeighbours: !!blenderSite })

  // ---------- people inside: the programme ----------
  // A gathering is furniture plus people, built for a room and a use. When the
  // hour or the crowd changes, the old gatherings fold away and new ones grow.
  const layouts = {
    table: (n) => {
      if (n > 5) {
        const half = Math.ceil(n / 2)
        return { furniture: [[0.42, 0.3, 0.34 * half + 0.1]], at: Array.from({ length: n }, (_, i) => ({ x: i < half ? -0.36 : 0.36, z: ((i % half) - (half - 1) / 2) * 0.34, face: i < half ? Math.PI / 2 : -Math.PI / 2, seated: true })) }
      }
      return { round: true, at: Array.from({ length: n }, (_, i) => { const a = (i / n) * Math.PI * 2 + 0.4; return { x: Math.cos(a) * 0.4, z: Math.sin(a) * 0.4, face: Math.atan2(-Math.cos(a), -Math.sin(a)), seated: true } }) }
    },
    desk: (n) => ({ furniture: [[0.35, 0.3, 0.32 * n + 0.1]], at: Array.from({ length: n }, (_, i) => ({ x: -0.32, z: (i - (n - 1) / 2) * 0.32, face: Math.PI / 2, seated: true })) }),
    talk: (n) => ({ at: Array.from({ length: n }, (_, i) => { const a = (i / n) * Math.PI * 2 + rand(-0.3, 0.3); const r = 0.3 + rand(0, 0.15); return { x: Math.cos(a) * r, z: Math.sin(a) * r, face: Math.atan2(-Math.cos(a), -Math.sin(a)) } }) }),
    circle: (n) => ({ at: Array.from({ length: n }, (_, i) => { const a = (i / n) * Math.PI * 2; return { x: Math.cos(a) * 0.6, z: Math.sin(a) * 0.6, face: Math.atan2(-Math.cos(a), -Math.sin(a)), seated: i % 2 === 0, sway: true } }) }),
    dance: (n) => ({ at: Array.from({ length: n }, () => ({ x: rand(-0.6, 0.6), z: rand(-0.6, 0.6), face: rand(0, 6.3), dance: true })) }),
    row: (n) => ({ at: Array.from({ length: n }, (_, i) => ({ x: (i % 2) * 0.42 - 0.21, z: (Math.floor(i / 2) - (Math.ceil(n / 2) - 1) / 2) * 0.5, face: Math.PI / 2, stretch: true })) }),
    stage: (n) => ({ furniture: [[0.5, 0.08, 1.0, 0, -0.75]], at: Array.from({ length: n }, (_, i) => (i === 0 ? { x: 0, y: 0.08, z: -0.75, face: 0, perform: true } : { x: (((i - 1) % 4) - 1.5) * 0.3, z: Math.floor((i - 1) / 4) * 0.38 - 0.05, face: Math.PI, seated: true })) }),
  }
  let gatherings = []
  let programKey = ''
  function buildProgram(persona, part) {
    for (const g of gatherings) g.leaving = true
    PROGRAM[persona][part].forEach(([roomId, use, kind, n], gi) => {
      const room = ROOMS[roomId]
      const group = new THREE.Group()
      group.position.set(room.x, 0, room.z)
      floors[room.floor].add(group)
      const lay = layouts[kind](n)
      const items = []
      const grow = (obj, delay, extra = {}) => items.push({ obj, delay: gi * 0.12 + delay, k: 0, ...extra })
      const furnishing = createFurnishings(kind, lay, use)
      group.add(furnishing)
      grow(furnishing, 0)
      lay.at.forEach((a, i) => {
        const p = person()
        p.position.set(a.x, a.y || 0, a.z)
        p.rotation.y = a.face
        const phase = rand(0, 10)
        posePerson(p, poseFor(a, kind, use), 0, phase)
        group.add(p)
        grow(p, 0.15 + i * 0.07, { person: true, a, baseY: p.position.y, phase })
      })
      for (const it of items) it.obj.scale.setScalar(0.001)
      gatherings.push({ room, roomId, use, kind, group, items, t: 0, leaving: false })
    })
  }
  function updateProgram(dt, t) {
    for (let gi = gatherings.length - 1; gi >= 0; gi--) {
      const g = gatherings[gi]
      g.t += dt
      let alive = false
      for (const it of g.items) {
        const want = g.leaving ? 0 : g.t > it.delay ? 1 : 0
        it.k = still ? want : lerp(it.k, want, 1 - Math.pow(g.leaving ? 0.0004 : 0.002, dt))
        if (it.k > 0.01) alive = true
        it.obj.scale.setScalar(Math.max(0.001, it.k))
        if (!it.person || still) continue
        const p = it.obj
        posePerson(p, poseFor(it.a, g.kind, g.use), t, it.phase)
        // The skeleton owns the gesture and foot contact; the root remains
        // aligned with its chair, yoga mat, or microphone.
        p.position.y = it.baseY
        p.rotation.y = it.a.face
      }
      if (g.leaving && !alive) {
        g.group.removeFromParent()
        gatherings.splice(gi, 1)
      }
    }
  }

  // ---------- walkers and vehicles ----------
  const walkers = []
  const pool = []
  function spawn(points) {
    const p = pool.pop() || person()
    if (!p.parent) street.add(p)
    p.visible = true
    const segs = []
    let total = 0
    for (let i = 0; i < points.length - 1; i++) {
      const len = points[i].v.distanceTo(points[i + 1].v)
      segs.push({ a: points[i], b: points[i + 1], len, at: total })
      total += len
    }
    walkers.push({ p, segs, total, d: 0, speed: rand(0.55, 0.8), phase: rand(0, 10) })
  }
  const vehicles = []
  function vehicle() {
    const g = createVehicle(Math.random() < 0.55, person, posePerson)
    const dir = Math.random() < 0.5 ? 1 : -1
    g.rotation.y = dir > 0 ? 0 : Math.PI
    g.position.set(-28 * dir, 0, dir > 0 ? 8.55 : 7.2)
    street.add(g)
    vehicles.push({ g, dir, speed: rand(2.2, 3.4) })
  }

  // ---------- post ----------
  // Canvas antialiasing does not apply to the composer's offscreen buffers.
  // Multisample the scene before bloom so fine edges stay stable as it moves.
  const renderTarget = new THREE.WebGLRenderTarget(1, 1, {
    type: THREE.HalfFloatType,
    samples: Math.min(4, renderer.capabilities.maxSamples),
  })
  const composer = new EffectComposer(renderer, renderTarget)
  composer.addPass(new RenderPass(scene, camera))
  const bloom = new UnrealBloomPass(new THREE.Vector2(256, 256), 0, 0.6, 0.82)
  composer.addPass(bloom)
  composer.addPass(new OutputPass())

  // ---------- the day, as a path ----------
  // Progress → hour, how open the house is, and where the camera looks.
  const HOURS = [[0, 6.2], [0.1, 7.2], [0.22, 9.5], [0.38, 13], [0.54, 16.2], [0.7, 19], [0.84, 21.5], [1, 23.4]]
  // [progress, azimuth°, elevation°, distance, target x offset, height above the floor in view, target z, floor in view (0 basement … 3 second)]
  const SHOTS = [
    [0, 30, 13, 25, -1.7, 1.2, 0.6, 3.5],
    [0.1, 28, 22, 26, -1.2, 1.6, 0.6, 3.5],
    [0.22, 24, 38, 13.5, -0.4, 0.2, 0.6, 1],
    [0.38, -28, 42, 11.5, 0.4, 0.2, 1.4, 0],
    [0.54, -34, 42, 12.5, 0.2, 0.2, 0.4, 2],
    [0.7, -58, 42, 13, -0.8, 0.2, 0.0, 3],
    [0.84, 32, 38, 15.5, -0.3, 0.2, 0.4, 1.9],
    [1, 44, 14, 27, -1.2, 1.4, 0.4, 3.5],
  ]
  const key = (table, p) => {
    let i = 0
    while (i < table.length - 2 && p > table[i + 1][0]) i++
    const a = table[i]
    const b = table[i + 1]
    const k = smooth(0, 1, (p - a[0]) / (b[0] - a[0]))
    return a.map((v, j) => lerp(v, b[j], k))
  }
  // Fog thickens between stops, the way the igloo scenes pass through cloud.
  // Inside each cloud the world changes: the street is left behind as the
  // house breaks open, and every floor is seen in its own environment.
  const STOPS = [0.145, 0.3, 0.46, 0.62, 0.77, 0.91]
  const ENV_AT = [[0.145, 'cafe'], [0.3, 'studio'], [0.46, 'courtyard'], [0.62, 'terrace'], [0.77, 'night'], [0.91, null]]
  const envAt = (p) => {
    let e = null
    for (const [at, id] of ENV_AT) if (p >= at) e = id
    return e
  }
  const env = createEnvironment(scene)

  // ---------- state ----------
  const lift = { basement: 0, ground: 0, first: 0, second: 0 }
  const state = { p: 0, hour: 6, open: 0, night: 0, mx: 0, my: 0, persona: 'all' }
  const view = { az: 36, el: 17, r: 27, tx: 0.2, ty: 1.2, tz: 0.9 }
  const target = new THREE.Vector3()
  let width = 0
  let height = 0
  let still = matchMedia('(prefers-reduced-motion: reduce)').matches
  const acc = { pass: 0, in: 0, out: 0, up: 0, office: 0, officeOut: 0, vehicle: 0 }

  function resize() {
    width = canvas.clientWidth
    height = canvas.clientHeight
    renderer.setSize(width, height, false)
    composer.setSize(width, height)
    camera.aspect = width / height
    camera.updateProjectionMatrix()
  }
  resize()
  addEventListener('resize', resize)

  // Seed the street so it is never empty on arrival.
  for (let i = 0; i < 6; i++) {
    spawn(ROUTES.pass())
    walkers.at(-1).d = rand(10, 40)
  }

  const clock = new THREE.Clock()
  const tmp = new THREE.Vector3()
  function frame() {
    const dt = Math.min(clock.getDelta(), 0.05)
    const t = clock.elapsedTime
    state.hour = key(HOURS, state.p)[1]
    const h = state.hour

    // Light.
    const sky = skyAt(h)
    const cloud = Math.max(0, ...STOPS.map((b) => 1 - Math.abs(state.p - b) / 0.035))
    // The changeover happens at the thickest point of the cloud, where
    // nothing but the nearest floor can be seen.
    if (cloud > 0.9 || (cloud < 0.05 && env.id !== envAt(state.p))) env.set(envAt(state.p))
    const inside = env.cur.inside
    street.visible = inside < 0.98
    state.night = Math.max(sky.night, env.cur.dark)
    scene.background.copy(env.cur.horizon)
    scene.fog.color.copy(env.cur.horizon)
    const reach = camera.aspect < 0.8 ? 2.05 : camera.aspect < 1.2 ? 1.25 : 1
    // Settled scenes stay sharp to just past the house; only the cloud brings the fog in.
    scene.fog.near = lerp(lerp(24, 15, inside), 4, cloud) * reach
    scene.fog.far = lerp(lerp(58, 34, inside), 17, cloud) * reach
    hemi.color.copy(sky.hemiSky)
    hemi.groundColor.copy(sky.hemiGround)
    hemi.intensity = sky.hemiI * env.cur.hemi * (scene.environment ? 0.45 : 1)
    sun.color.copy(sky.sun)
    sun.intensity = sky.sunI * env.cur.sun
    renderer.toneMappingExposure = env.cur.expo
    // The sky's light on the materials: full by day, a trace at night.
    scene.environmentIntensity = lerp(0.9, 0.08, state.night) * lerp(1, 0.55, env.cur.inside)
    const day = Math.min(1, Math.max(0, (h - 5.6) / 13.4))
    const ang = day * Math.PI
    const sunPos = new THREE.Vector3(Math.cos(ang) * 22, Math.max(4, Math.sin(ang) * 24), -9)
    const moonPos = new THREE.Vector3(-10, 22, 8)
    sun.position.copy(sunPos.lerp(moonPos, smooth(18.6, 19.6, h)))
    const evening = smooth(17.6, 19.2, h)
    roomLights.forEach((l) => (l.intensity = 5 * evening + 4 * env.cur.lamps))
    streetLights.forEach((l) => (l.intensity = 7 * evening))
    for (const g of glow) g.m.material.emissiveIntensity = g.k * (g.evening ? smooth(18, 19.5, h) : evening)
    bloom.strength = 0.42 * Math.max(evening, env.cur.stars, env.cur.lamps * 0.5)
    env.update(dt, t, camera, sky.sky, sun.position, still)

    // The house opens after dawn and settles back together at night.
    state.open = smooth(0.07, 0.17, state.p) * (1 - smooth(0.87, 0.96, state.p))
    const shotNow = key(SHOTS, state.p)
    const focus = shotNow[7]
    ORDER.forEach((id, i) => {
      lift[id] = state.open * (PART[id] + CLEAR * Math.min(1, Math.max(0, i - focus)))
      floors[id].position.y = LEVEL[id] + lift[id]
    })
    // Height of the floor in view, for the camera.
    const fi = Math.min(3, Math.max(0, Math.round(focus)))
    const focusY = lerp(1.2, floors[ORDER[fi]].position.y, state.open)
    // Walls drop to a cutaway as the floors part, so the rooms show.
    const cut = smooth(0.15, 0.8, state.open)
    for (const w of walls) w.o.scale.y = lerp(w.full, w.low, cut)
    for (const o of highParts) o.visible = cut < 0.35
    for (const o of roofParts) o.visible = cut < 0.1

    const pk = state.persona + '|' + partAt(h)
    if (pk !== programKey) {
      programKey = pk
      buildProgram(state.persona, partAt(h))
    }
    updateProgram(dt, t)

    // Camera.
    const [, sAz, sEl, sR, sx, sOff, sz] = shotNow
    const sy = focusY + sOff
    const k = still ? 1 : 1 - Math.pow(0.0015, dt)
    const fit = camera.aspect < 0.8 ? 2.05 : camera.aspect < 1.2 ? 1.25 : 1
    view.az = lerp(view.az, sAz + state.mx * 5, k)
    view.el = lerp(view.el, sEl + state.my * 3, k)
    view.r = lerp(view.r, sR * fit, k)
    view.tx = lerp(view.tx, camera.aspect < 0.8 ? sx * 0.15 : sx, k)
    // On a phone the story takes the lower half, so the house sits higher.
    view.ty = lerp(view.ty, sy - (camera.aspect < 0.8 ? 3.2 : 0), k)
    view.tz = lerp(view.tz, sz, k)
    const az = THREE.MathUtils.degToRad(view.az)
    const el = THREE.MathUtils.degToRad(view.el)
    target.set(view.tx, view.ty, view.tz)
    camera.position.set(target.x + Math.sin(az) * Math.cos(el) * view.r, target.y + Math.sin(el) * view.r, target.z + Math.cos(az) * Math.cos(el) * view.r)
    camera.lookAt(target)
    sun.target.position.set(0, 0, 1)

    if (!still) {
      // Spawning.
      const r = RATES(h)
      for (const key of Object.keys(acc)) {
        acc[key] += r[key] * dt
        if (acc[key] < 1) continue
        acc[key] -= 1
        if (walkers.length > 80 && key !== 'vehicle') continue
        if (key === 'pass') spawn(ROUTES.pass())
        else if (key === 'in') spawn(state.open > 0.2 ? ROUTES.in().slice(0, 2) : ROUTES.in())
        else if (key === 'out' && state.open < 0.2) spawn(END(reverse(ROUTES.in().slice(1))))
        else if (key === 'up' && state.open < 0.2) spawn(Math.random() < 0.5 ? ROUTES.up() : END(reverse(ROUTES.up().slice(1))))
        else if (key === 'office') spawn(ROUTES.office())
        else if (key === 'officeOut') spawn(END(reverse(ROUTES.office().slice(1))))
        else if (key === 'vehicle' && vehicles.length < 6) vehicle()
      }

      // Walkers.
      for (let i = walkers.length - 1; i >= 0; i--) {
        const w = walkers[i]
        w.d += w.speed * dt
        if (w.d >= w.total) {
          w.p.visible = false
          pool.push(w.p)
          walkers.splice(i, 1)
          continue
        }
        let seg = w.segs[0]
        for (const sg of w.segs) if (w.d >= sg.at) seg = sg
        const u = (w.d - seg.at) / seg.len
        tmp.lerpVectors(seg.a.v, seg.b.v, u)
        const liftA = seg.a.tag ? lift[seg.a.tag] : 0
        const liftB = seg.b.tag ? lift[seg.b.tag] : 0
        tmp.y += lerp(liftA, liftB, u)
        posePerson(w.p, 'walk', t * w.speed, w.phase)
        w.p.position.copy(tmp)
        w.p.rotation.y = Math.atan2(seg.b.v.x - seg.a.v.x, seg.b.v.z - seg.a.v.z)
        w.p.rotation.z = Math.sin(t * 7 * w.speed + w.phase) * 0.04
        // Fade in at the start, out at a door.
        const edge = Math.min(w.d, w.total - w.d)
        w.p.scale.setScalar(Math.min(1, edge / 0.35) || 0.001)
      }

      // Vehicles.
      for (let i = vehicles.length - 1; i >= 0; i--) {
        const v = vehicles[i]
        v.g.position.x += v.dir * v.speed * dt
        rollVehicle(v.g, v.speed * dt)
        if (Math.abs(v.g.position.x) > 30) {
          street.remove(v.g)
          vehicles.splice(i, 1)
        }
      }

      for (const tr of trees) {
        tr.userData.crown.rotation.z = Math.sin(t * 0.6 + tr.userData.phase) * 0.025
        tr.userData.crown.rotation.x = Math.cos(t * 0.5 + tr.userData.phase) * 0.02
      }
    }

    composer.render()
  }
  renderer.setAnimationLoop(frame)

  const skyHex = () => '#' + scene.background.getHexString()

  return {
    state,
    skyHex,
    setReducedMotion: (v) => (still = v),
  }
}
