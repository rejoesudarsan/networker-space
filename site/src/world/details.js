import * as THREE from 'three'
import { ROOMS } from './program.js'

// Quiet detail for the house and its street: the basement's ramp, stairs and
// finishes, joints in the floors, rails at the voids, planters, gates,
// windows for the neighbours, kerbs and petals. Everything repeated is
// instanced, so each floor costs a handful of draw calls, and each floor's
// detail rides with that floor when the house opens.
// Items taken from a photo carry its number (PHOTO-LABELS.md); positions come
// from the drawn plans (docs/house-understanding/plans). Anything else is
// exploratory dressing, not a claim about the house.

// ---------- palette: the house's own, a shade quieter ----------
const C = {
  plaster: '#ecebe4',
  plasterShade: '#dedad1',
  trim: '#d4cfc5',
  terrazzoJoint: '#c9c1b2',
  kota: '#b9a68a',
  kotaJoint: '#9d8c72',
  stoneJoint: '#8c7f6c',
  flag: '#bfae92',
  flagJoint: '#a39478',
  teakSeam: '#6f4026',
  teak: '#7a3f1f',
  tileJoint: '#9a5236',
  terracotta: '#b4643f',
  pot: '#a8573a',
  redOxide: '#7d2a22',
  steel: '#4a4d4f',
  gate: '#6c6f70',
  granite: '#2a2a28',
  tank: '#33332f',
  earth: '#6e4530',
  foliage: '#4d6b35',
  foliageLight: '#6f8d47',
  fern: '#5d7a3c',
  glass: '#5d6468',
  kerb: '#d6d0c4',
  kerbShade: '#b9b2a5',
  seam: '#b8af9f',
  concrete: '#b3ada2',
  concreteJoint: '#9a948a',
  ramp: '#a8a297',
  block: '#b0aba1',
  blockJoint: '#959086',
  car: '#6f7376',
  petals: ['#e0531f', '#e0531f', '#f08a3c', '#c9502c', '#d9744a'],
}

// ---------- the basement, from the drawn plan (basement floor coordinates) ----------
const PLAN = {
  // Parking 18'6" × 36'2" with the ramp up to the street at its front (#2, #3).
  parking: [[-2.2, -3.54, 0.1, -0.52], [-2.2, -0.52, -0.61, 1.0]],
  ramp: { x0: -2.2, x1: -0.61, foot: 1.2 },
  // Court 1 under the double-height void, and its stair up to the ground floor (#20).
  court: [0.2, -2.08, 2.0, -1.0],
  stair: { bottom: 1.69, landing: 2.05, z0: -0.97, z1: -0.6, risers: 20, open: 0.84 },
  // The open-to-sky court in front of the office and its stair up to the street.
  openCourt: [0.94, 1.92, 2.2],
  officeStair: { x0: 1.28, x1: 2.14, risers: 10 },
  // One of the cars the plan draws, where the photo shows one (#2).
  car: { x: -1.55, z: -2.45 },
}

// Rendered heights (world.js scales the drawn walls): walls stand 1.3 and drop
// to 0.42 when the floors part, so anything set by a wall stays below 0.4.

// ---------- shared geometry and materials ----------
// A unit wedge: foot at z −0.5 on the floor, rising to full height at z +0.5.
function wedgeGeo() {
  const A = [-0.5, 0, -0.5], B = [0.5, 0, -0.5], Cc = [0.5, 0, 0.5], D = [-0.5, 0, 0.5], E = [-0.5, 1, 0.5], F = [0.5, 1, 0.5]
  const tris = [A, E, F, A, F, B, D, Cc, F, D, F, E, A, B, Cc, A, Cc, D, A, D, E, B, F, Cc]
  const g = new THREE.BufferGeometry()
  g.setAttribute('position', new THREE.Float32BufferAttribute(tris.flat(), 3))
  g.computeVertexNormals()
  return g
}
const GEO = {
  box: new THREE.BoxGeometry(1, 1, 1),
  cyl: new THREE.CylinderGeometry(1, 1, 1, 10),
  pot: new THREE.CylinderGeometry(1, 0.72, 1, 10),
  blob: new THREE.IcosahedronGeometry(1, 0),
  ring: new THREE.TorusGeometry(1, 0.08, 6, 20),
  wedge: wedgeGeo(),
}
const MAT = {
  solid: new THREE.MeshStandardMaterial({ color: '#ffffff', roughness: 0.85 }),
  metal: new THREE.MeshStandardMaterial({ color: '#ffffff', roughness: 0.55, metalness: 0.2 }),
  leaf: new THREE.MeshStandardMaterial({ color: '#ffffff', roughness: 0.9, flatShading: true }),
  // Flat things laid on a surface: pulled towards the camera so they never shimmer.
  decal: new THREE.MeshStandardMaterial({ color: '#ffffff', roughness: 0.95, polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -2 }),
  glass: new THREE.MeshStandardMaterial({ color: '#ffffff', roughness: 0.2, metalness: 0.25 }),
  lit: new THREE.MeshStandardMaterial({ color: '#ffffff', roughness: 0.3, emissive: '#ffc78a', emissiveIntensity: 0 }),
}
const CASTS = { solid: true, metal: true, leaf: true }

const smooth = (a, b, x) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)))
  return t * t * (3 - 2 * t)
}
// The neighbours' lit windows follow the sky: warm once it is dark.
function glowAtNight(renderer, scene) {
  const bg = scene.background
  if (!bg?.isColor) return
  const lum = 0.2126 * bg.r + 0.7152 * bg.g + 0.0722 * bg.b
  MAT.lit.emissiveIntensity = 0.95 * (1 - smooth(0.05, 0.4, lum))
}

// A seeded random, so the dressing is the same on every visit.
function seeded(seed) {
  return () => {
    seed = (seed + 0x6d2b79f5) | 0
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

// ---------- batching: one InstancedMesh per parent, geometry and material ----------
const colours = new Map()
const colour = (hex) => {
  if (!colours.has(hex)) colours.set(hex, new THREE.Color(hex))
  return colours.get(hex)
}
function batch(parent, name, onBeforeRender = null) {
  const lists = new Map()
  return {
    parent,
    add(geo, kind, color, m) {
      const k = geo + '|' + kind
      if (!lists.has(k)) lists.set(k, { geo, kind, m: [], c: [] })
      const l = lists.get(k)
      l.m.push(m.clone())
      l.c.push(color)
    },
    flush() {
      const out = []
      for (const { geo, kind, m, c } of lists.values()) {
        const mesh = new THREE.InstancedMesh(GEO[geo], MAT[kind], m.length)
        m.forEach((mm, i) => {
          mesh.setMatrixAt(i, mm)
          mesh.setColorAt(i, colour(c[i]))
        })
        mesh.instanceMatrix.needsUpdate = true
        mesh.instanceColor.needsUpdate = true
        mesh.computeBoundingSphere()
        mesh.castShadow = !!CASTS[kind]
        mesh.receiveShadow = kind !== 'lit' && kind !== 'glass'
        mesh.name = `details:${name}:${geo}:${kind}`
        if (kind === 'lit') mesh.onBeforeRender = glowAtNight
        else if (onBeforeRender) mesh.onBeforeRender = onBeforeRender
        parent.add(mesh)
        out.push(mesh)
      }
      return out
    },
  }
}

// ---------- primitives ----------
const V = (x, y, z) => new THREE.Vector3(x, y, z)
const UP = V(0, 1, 0)
const _m = new THREE.Matrix4()
const _q = new THREE.Quaternion()
const _p = new THREE.Vector3()
const _s = new THREE.Vector3()
const _d = new THREE.Vector3()
const _e = new THREE.Euler()

// rot: a yaw, or [x, y, z] turns applied yaw first.
function put(b, geo, kind, color, x, y, z, sx, sy, sz, rot = 0, base = null) {
  if (Array.isArray(rot)) _e.set(rot[0], rot[1], rot[2], 'YXZ')
  else _e.set(0, rot, 0, 'YXZ')
  _q.setFromEuler(_e)
  _m.compose(_p.set(x, y, z), _q, _s.set(sx, sy, sz))
  if (base) _m.premultiply(base)
  b.add(geo, kind, color, _m)
}
// A box by its bottom centre, turned about y.
const cube = (b, color, x, y, z, w, h, d, { kind = 'solid', yaw = 0, base } = {}) => put(b, 'box', kind, color, x, y + h / 2, z, w, h, d, yaw, base)
// A box between two corners.
const span = (b, color, x0, y0, z0, x1, y1, z1, kind = 'solid') => cube(b, color, (x0 + x1) / 2, y0, (z0 + z1) / 2, x1 - x0, y1 - y0, z1 - z0, { kind })
const post = (b, color, x, y, z, r, h, { kind = 'solid', geo = 'cyl', base } = {}) => put(b, geo, kind, color, x, y + h / 2, z, r, h, r, 0, base)
const blob = (b, color, x, y, z, sx, sy, sz, yaw = 0) => put(b, 'blob', 'leaf', color, x, y, z, sx, sy, sz, yaw)
function rod(b, color, a, c, r, { kind = 'metal', base } = {}) {
  _d.subVectors(c, a)
  const len = _d.length()
  _q.setFromUnitVectors(UP, _d.normalize())
  _m.compose(_p.addVectors(a, c).multiplyScalar(0.5), _q, _s.set(r, len, r))
  if (base) _m.premultiply(base)
  b.add('cyl', kind, color, _m)
}
// A box laid along a line on the floor.
function beam(b, color, ax, az, bx, bz, y, h, t, kind = 'solid') {
  const dx = bx - ax
  const dz = bz - az
  cube(b, color, (ax + bx) / 2, y, (az + bz) / 2, Math.hypot(dx, dz), h, t, { kind, yaw: Math.atan2(-dz, dx) })
}

// ---------- reading the built world ----------
// The voids world.js cut in each slab (interior holes and entrance mouths).
const VOIDS = { basement: [], ground: [[0.56, -0.65, 1.99, 0.8], [1.25, 3.27, 2.39, 5.01], [-1.85, 3.2, -0.2, 5.01]], first: [], second: [[0.18, -0.49, 1.88, 1.06]] }
function voidsOf(id, floor) {
  for (const o of floor.children) {
    if (!o.isMesh || o.geometry.type !== 'ExtrudeGeometry') continue
    if (Array.isArray(o.userData.voids)) return o.userData.voids
    const s = o.geometry.parameters.shapes
    const shape = Array.isArray(s) ? s[0] : s
    if (!shape) continue
    return shape.holes.map((h) => {
      const pts = h.getPoints()
      const xs = pts.map((p) => p.x)
      const zs = pts.map((p) => p.y)
      return [Math.min(...xs), Math.min(...zs), Math.max(...xs), Math.max(...zs)]
    })
  }
  return VOIDS[id] || []
}

// Where the drawn walls, columns and sills stand, as a coarse grid in floor
// coordinates, so nothing is set down inside or against them.
const CELL = 0.04
function footprint(floor) {
  const cells = new Set()
  const key = (i, j) => (i + 4096) * 8192 + (j + 4096)
  floor.updateMatrixWorld(true)
  const inv = floor.matrixWorld.clone().invert()
  const rel = new THREE.Matrix4()
  const a = new THREE.Vector3()
  const b = new THREE.Vector3()
  const c = new THREE.Vector3()
  const side = (p, q, x, z) => (q.x - p.x) * (z - p.z) - (q.z - p.z) * (x - p.x)
  floor.traverse((o) => {
    if (!o.isMesh || !['walls', 'columns', 'sills'].includes(o.name)) return
    rel.multiplyMatrices(inv, o.matrixWorld)
    const pos = o.geometry.attributes.position
    const idx = o.geometry.index
    const n = idx ? idx.count : pos.count
    for (let t = 0; t + 2 < n; t += 3) {
      const at = (k) => (idx ? idx.getX(t + k) : t + k)
      a.fromBufferAttribute(pos, at(0)).applyMatrix4(rel)
      b.fromBufferAttribute(pos, at(1)).applyMatrix4(rel)
      c.fromBufferAttribute(pos, at(2)).applyMatrix4(rel)
      const area = side(a, b, c.x, c.z)
      if (Math.abs(area) < 1e-7) continue // a vertical face: no footprint
      const i0 = Math.floor(Math.min(a.x, b.x, c.x) / CELL)
      const i1 = Math.floor(Math.max(a.x, b.x, c.x) / CELL)
      const j0 = Math.floor(Math.min(a.z, b.z, c.z) / CELL)
      const j1 = Math.floor(Math.max(a.z, b.z, c.z) / CELL)
      for (let i = i0; i <= i1; i++) {
        for (let j = j0; j <= j1; j++) {
          for (const [u, v] of [[0.5, 0.5], [0, 0], [1, 0], [0, 1], [1, 1]]) {
            const x = (i + u) * CELL
            const z = (j + v) * CELL
            if (side(a, b, x, z) * area >= 0 && side(b, c, x, z) * area >= 0 && side(c, a, x, z) * area >= 0) {
              cells.add(key(i, j))
              break
            }
          }
        }
      }
    }
  })
  return (x, z, pad = 0) => {
    const r = Math.ceil(pad / CELL)
    const i = Math.floor(x / CELL)
    const j = Math.floor(z / CELL)
    for (let di = -r; di <= r; di++) for (let dj = -r; dj <= r; dj++) if (cells.has(key(i + di, j + dj))) return true
    return false
  }
}
// Walk from a point until a drawn wall is met; the wall's face, or `fallback`.
function faceFrom(blocked, x, z, dx, dz, max, fallback) {
  for (let t = 0; t <= max; t += 0.02) if (blocked(x + dx * t, z + dz * t)) return dx ? x + dx * t : z + dz * t
  return fallback
}

// Gatherings grow at these points; keep loose things clear of them.
const roomClear = (id, x, z, r = 0.7) => Object.values(ROOMS).every((room) => room.floor !== id || Math.hypot(room.x - x, room.z - z) > r)

// What is left of [a0, a1] once the voids crossing a line are cut out.
function spans(a0, a1, cuts) {
  let out = [[a0, a1]]
  for (const [c0, c1] of cuts) out = out.flatMap(([s0, s1]) => (c1 <= s0 || c0 >= s1 ? [[s0, s1]] : [[s0, c0], [c1, s1]].filter(([u, v]) => v - u > 0.04)))
  return out
}
// Cuts along a line at fixed z (axis 'x') or fixed x (axis 'z'), from rectangles.
const cutsAt = (rects, axis, c, pad = 0) =>
  axis === 'x'
    ? rects.filter((o) => c > o[1] - pad && c < o[3] + pad).map((o) => [o[0] - pad, o[2] + pad])
    : rects.filter((o) => c > o[0] - pad && c < o[2] + pad).map((o) => [o[1] - pad, o[3] + pad])
const inRect = (rects, x, z, pad = 0) => rects.some(([x0, z0, x1, z1]) => x > x0 - pad && x < x1 + pad && z > z0 - pad && z < z1 + pad)

// ---------- floor patterns ----------
// Divider strips over a rectangle, every `step`, never across a void.
function joints(b, color, [x0, z0, x1, z1], { step, y, holes = [], w = 0.008, dirs = 'xz', stepZ = step }) {
  const h = 0.004
  if (dirs.includes('z')) {
    for (let x = Math.ceil((x0 + 0.03) / step) * step; x < x1 - 0.03; x += step) {
      for (const [s0, s1] of spans(z0, z1, cutsAt(holes, 'z', x, w))) span(b, color, x - w / 2, y, s0, x + w / 2, y + h, s1, 'decal')
    }
  }
  if (dirs.includes('x')) {
    for (let z = Math.ceil((z0 + 0.03) / stepZ) * stepZ; z < z1 - 0.03; z += stepZ) {
      for (const [s0, s1] of spans(x0, x1, cutsAt(holes, 'x', z, w))) span(b, color, s0, y, z - w / 2, s1, y + h, z + w / 2, 'decal')
    }
  }
}
// Flagstones: courses of uneven length, joints staggered course to course.
function flags(b, color, [x0, z0, x1, z1], y, rand, { row = 0.3, holes = [] } = {}) {
  const w = 0.01
  const h = 0.004
  const rows = [z0]
  while (rows.at(-1) < z1 - row * 1.4) rows.push(rows.at(-1) + row * (0.8 + rand() * 0.4))
  rows.push(z1)
  for (let r = 1; r < rows.length - 1; r++) {
    for (const [s0, s1] of spans(x0, x1, cutsAt(holes, 'x', rows[r]))) span(b, color, s0, y, rows[r] - w / 2, s1, y + h, rows[r] + w / 2, 'decal')
  }
  for (let r = 0; r < rows.length - 1; r++) {
    for (let x = x0 + 0.08 + rand() * 0.25; x < x1 - 0.1; x += 0.26 + rand() * 0.24) {
      const za = rows[r] + w / 2
      const zb = rows[r + 1] - w / 2
      if (inRect(holes, x, (za + zb) / 2)) continue
      span(b, color, x - w / 2, y, za, x + w / 2, y + h, zb, 'decal')
    }
  }
}

// ---------- rails, pots, planters ----------
// A low rail along a line, broken wherever a wall already stands or the
// floor is cut away. `bars` gives horizontal bars, `balusters` upright ones.
function rail(b, ok, ax, az, bx, bz, { color = C.steel, h = 0.34, gap = 0.32, balusters = 0, bars = 0, kind = 'metal' } = {}) {
  const len = Math.hypot(bx - ax, bz - az)
  const n = Math.max(1, Math.round(len / 0.04))
  const runs = []
  let start = null
  for (let i = 0; i <= n; i++) {
    const free = ok(ax + ((bx - ax) * i) / n, az + ((bz - az) * i) / n)
    if (free && start === null) start = i
    if ((!free || i === n) && start !== null) {
      const end = free ? i : i - 1
      if (((end - start) / n) * len > 0.15) runs.push([start / n, end / n])
      start = null
    }
  }
  for (const [u0, u1] of runs) {
    const p0x = ax + (bx - ax) * u0
    const p0z = az + (bz - az) * u0
    const p1x = ax + (bx - ax) * u1
    const p1z = az + (bz - az) * u1
    const l = (u1 - u0) * len
    beam(b, color, p0x, p0z, p1x, p1z, h - 0.025, 0.025, 0.03, kind)
    beam(b, color, p0x, p0z, p1x, p1z, 0.04, 0.015, 0.015, kind)
    for (let k = 1; k <= bars; k++) beam(b, color, p0x, p0z, p1x, p1z, 0.04 + ((h - 0.08) * k) / (bars + 1), 0.018, 0.012, kind)
    const posts = Math.max(1, Math.round(l / gap))
    for (let k = 0; k <= posts; k++) cube(b, color, p0x + ((p1x - p0x) * k) / posts, 0, p0z + ((p1z - p0z) * k) / posts, 0.022, h - 0.025, 0.022, { kind })
    if (balusters) {
      const nb = Math.round(l / balusters)
      const every = Math.max(2, Math.round(gap / balusters))
      for (let k = 1; k < nb; k++) if (k % every) cube(b, color, p0x + ((p1x - p0x) * k) / nb, 0.055, p0z + ((p1z - p0z) * k) / nb, 0.012, h - 0.08, 0.012, { kind })
    }
  }
}
function pot(b, x, z, s = 1, y = 0, tone = C.pot) {
  post(b, tone, x, y, z, 0.065 * s, 0.11 * s, { geo: 'pot' })
  blob(b, C.fern, x, y + 0.14 * s, z, 0.095 * s, 0.07 * s, 0.095 * s, x * 3)
  blob(b, C.foliageLight, x + 0.025 * s, y + 0.18 * s, z - 0.02 * s, 0.055 * s, 0.05 * s, 0.055 * s, z * 3)
}
function planter(b, x0, z0, x1, z1, h, rand, { tone = C.plasterShade, green = C.fern } = {}) {
  span(b, tone, x0, 0, z0, x1, h, z1)
  span(b, C.earth, x0 + 0.02, h, z0 + 0.02, x1 - 0.02, h + 0.006, z1 - 0.02, 'decal')
  const along = x1 - x0 > z1 - z0
  const L = along ? x1 - x0 : z1 - z0
  const n = Math.max(2, Math.round(L / 0.16))
  for (let i = 0; i < n; i++) {
    const u = (i + 0.5) / n
    const x = along ? x0 + (x1 - x0) * u : (x0 + x1) / 2
    const z = along ? (z0 + z1) / 2 : z0 + (z1 - z0) * u
    const s = 0.06 + rand() * 0.04
    blob(b, i % 3 ? green : C.foliageLight, x, h + s * 0.6, z, s, s * 0.8, s, rand() * 6)
  }
}
// A slatted steel gate leaf between two points, standing on y.
function slatGate(b, ax, az, bx, bz, y, h = 0.38, slats = 6) {
  const yaw = Math.atan2(-(bz - az), bx - ax)
  const len = Math.hypot(bx - ax, bz - az)
  for (let i = 0; i < slats; i++) cube(b, C.gate, (ax + bx) / 2, y + 0.04 + (i * (h - 0.06)) / slats, (az + bz) / 2, len, 0.032, 0.015, { kind: 'metal', yaw })
  for (const [x, z] of [[ax, az], [bx, bz]]) cube(b, C.gate, x, y + 0.02, z, 0.024, h - 0.02, 0.024, { kind: 'metal' })
}

// A thin drip band round a slab's outer edge, broken at entrance mouths.
function slabTrim(b, info, voids) {
  const hw = info.width / 2
  const hd = info.depth / 2
  const t = 0.012
  const y0 = -0.05
  const y1 = -0.006
  for (const z of [hd, -hd]) for (const [s0, s1] of spans(-hw - t, hw + t, cutsAt(voids, 'x', z, 0.02))) span(b, C.trim, s0, y0, z - t, s1, y1, z + t)
  for (const x of [hw, -hw]) for (const [s0, s1] of spans(-hd + t, hd - t, cutsAt(voids, 'z', x, 0.02))) span(b, C.trim, x - t, y0, s0, x + t, y1, s1)
}

// ---------- the house ----------
function groundFloor(b, info, voids, blocked, rand, { arrive = 0.42 } = {}) {
  const hw = info.width / 2
  const hd = info.depth / 2
  const solid = (x, z) => Math.abs(x) < hw && Math.abs(z) < hd && !inRect(voids, x, z, 0.015)
  const free = (x, z) => solid(x, z) && !blocked(x, z, 0.04)
  const mouths = voids.filter((v) => v[3] >= hd - 0.05)
  const holes = voids.filter((v) => v[3] < hd - 0.05)
  const ramp = mouths.find((v) => v[0] + v[2] < 0)
  const office = mouths.find((v) => v[0] + v[2] > 0)

  // Terrazzo divider strips, indoors only (the gardens carry their own surfaces).
  joints(b, C.terrazzoJoint, [-hw + 0.03, -hd + 0.05, hw - 0.03, 3.3], { step: 0.5, y: 0, holes: voids })
  // Living 1's teak floor (#25, #27): plank seams.
  joints(b, C.teakSeam, [0.56, 0.2, 2.4, 3.2], { step: 0.11, y: 0.012, holes: voids, w: 0.005, dirs: 'z' })
  // Entrance court stone (#24) and the kota side passage.
  joints(b, C.stoneJoint, [-2.3, -0.3, -1.55, 1.3], { step: 0.25, y: 0.012, holes: voids })
  joints(b, C.kotaJoint, [-2.95, 0.8, -2.3, 4.95], { step: 0.325, y: 0.012, holes: voids, dirs: 'x' })
  span(b, C.kotaJoint, -2.629, 0.012, 0.8, -2.621, 0.016, 4.95, 'decal')

  // The teak balustrade round the double-height void over Court 1 (#20),
  // left open on the west where the stair from the basement arrives.
  for (const [x0, z0, x1, z1] of holes) {
    const o = 0.03
    const teak = { color: C.teak, kind: 'solid', balusters: 0.08 }
    rail(b, free, x0 - o, z0 - o, x0 - o, Math.min(z1, arrive) - 0.06, teak)
    rail(b, free, x1 + o, z0 - o, x1 + o, z1 + o, teak)
    rail(b, free, x0 - o, z0 - o, x1 + o, z0 - o, teak)
    rail(b, free, x0 - o, z1 + o, x1 + o, z1 + o, teak)
  }
  // The garage ramp cuts the front (#3): grey horizontal-bar rails on its
  // two sides and across its back, where the floor drops away.
  if (ramp) {
    const [x0, z0, x1] = ramp
    const bars = { color: C.gate, bars: 3, gap: 0.45, h: 0.36 }
    rail(b, free, x0 - 0.035, z0, x0 - 0.035, hd - 0.04, bars)
    rail(b, free, x1 + 0.035, z0, x1 + 0.035, hd - 0.04, bars)
    rail(b, free, x0, z0 - 0.035, x1, z0 - 0.035, bars)
  }
  // The office's open-to-sky court: a steel rail where the garden meets it.
  if (office) {
    const [x0, z0, x1] = office
    rail(b, free, x0 - 0.03, z0, x0 - 0.03, hd - 0.04)
    rail(b, free, x0, z0 - 0.03, x1, z0 - 0.03)
    if (x1 < hw - 0.1) rail(b, free, x1 + 0.03, z0, x1 + 0.03, 4.5)
  }

  // The street gate (#5): slatted grey steel, open inward on its pier, and a
  // low front wall with a coping between the entrances. Exploratory in line and height.
  const zf = hd - 0.1
  const gx0 = -hw + 0.05
  const gx1 = -2.38
  for (const x of [gx0, gx1]) {
    cube(b, C.plaster, x, 0, zf, 0.1, 0.44, 0.12)
    cube(b, C.trim, x, 0.44, zf, 0.13, 0.025, 0.15)
  }
  slatGate(b, gx1 - 0.08, zf - 0.03, gx1 - 0.08, zf - 0.6, 0, 0.4, 7)
  for (const [x0, x1] of spans(gx1 + 0.06, hw - 0.02, cutsAt(voids, 'x', zf, 0.06))) {
    if (x1 - x0 < 0.1) continue
    span(b, C.plaster, x0, 0, zf - 0.04, x1, 0.22, zf + 0.04)
    span(b, C.trim, x0 - 0.01, 0.22, zf - 0.055, x1 + 0.01, 0.245, zf + 0.055)
  }
  // A fern planter inside the gate (#5).
  if (free(-2.1, zf - 0.2)) planter(b, -2.24, zf - 0.32, -1.96, zf - 0.08, 0.12, rand, { tone: C.terracotta })
  // Potted plants down the side passage (#9) and in the entrance court (#24).
  for (let z = 1.0; z < 4.45; z += 0.5) if (free(-3.02, z) && roomClear('ground', -3.02, z)) pot(b, -3.03, z, 0.9 + rand() * 0.3, 0.012)
  for (const [x, z] of [[-1.6, 1.32], [-1.62, -0.22]]) if (free(x, z) && roomClear('ground', x, z)) pot(b, x, z, 1.2, 0.012)
  // A door mat at the entrance.
  cube(b, '#8a6a48', -1.62, 0.012, 0.42, 0.24, 0.006, 0.15, { kind: 'decal', yaw: 0.05 })
  // Shrubs in the side garden.
  for (let z = -2.45; z < -0.95; z += 0.24) {
    const x = -2.86 + rand() * 0.06
    if (!free(x, z)) continue
    const s = 0.08 + rand() * 0.06
    blob(b, rand() < 0.35 ? C.foliageLight : C.foliage, x, 0.012 + s * 0.6, z, s, s * 0.85, s, rand() * 6)
  }
}

function firstFloor(b, info, voids, blocked, rand) {
  const hw = info.width / 2
  const hd = info.depth / 2
  joints(b, C.terrazzoJoint, [-hw + 0.03, -hd + 0.03, hw - 0.03, hd - 0.03], { step: 0.5, y: 0, holes: voids })
  // The Double HT Court's sandstone flagstones (#11, #14).
  flags(b, C.flagJoint, [0.75, 0.3, 2.45, 1.95], 0.012, rand, { row: 0.28 })
  for (const [x, z] of [[0.86, 0.42], [2.34, 0.42], [0.86, 1.84]]) if (!blocked(x, z, 0.08) && roomClear('first', x, z, 0.75)) pot(b, x, z, 1.1, 0.012)
  // A mat at the first-floor entrance, top of the outside stair (#4).
  if (!blocked(-1.6, 0.6, 0.1)) cube(b, '#8a6a48', -1.6, 0, 0.6, 0.22, 0.006, 0.14, { kind: 'decal', yaw: -0.04 })
}

function secondFloor(b, info, voids, blocked, rand) {
  const hw = info.width / 2
  const hd = info.depth / 2
  const solid = (x, z) => !inRect(voids, x, z, 0.015) && !blocked(x, z, 0.04)
  const tx = -0.95 // the terrace runs from the slab edge to the rooms
  joints(b, C.terrazzoJoint, [tx, -hd + 0.03, hw - 0.03, hd - 0.03], { step: 0.5, y: 0, holes: voids })
  // Terracotta tiles on the terrace (#33).
  joints(b, C.tileJoint, [-2.2, -3.4, -0.85, 3.35], { step: 0.25, y: 0.012, holes: voids, w: 0.006 })
  // The white parapet (#33), on the three open sides, with a coping.
  const x0 = -hw
  const P = 0.3
  span(b, C.plaster, x0, 0, -hd + 0.08, x0 + 0.08, P, hd - 0.08)
  span(b, C.trim, x0 - 0.012, P, -hd + 0.08, x0 + 0.092, P + 0.025, hd - 0.08)
  for (const z of [-hd, hd - 0.08]) {
    let x1 = tx + 0.12
    while (x1 > x0 + 0.2 && blocked(x1, z + 0.04, 0.02)) x1 -= 0.04
    span(b, C.plaster, x0, 0, z, x1, P, z + 0.08)
    span(b, C.trim, x0 - 0.012, P, z - 0.012, x1, P + 0.025, z + 0.092)
  }
  // Two slim posts that carry the string lights over the terrace.
  for (const z of [-hd + 0.16, hd - 0.16]) post(b, C.steel, -2.15, P + 0.025, z, 0.012, 0.76, { kind: 'metal' })
  planter(b, x0 + 0.1, -hd + 0.12, x0 + 0.26, -hd + 0.95, 0.14, rand)
  planter(b, x0 + 0.1, hd - 1.1, x0 + 0.26, hd - 0.12, 0.14, rand)
  for (const [x, z] of [[-1.15, -3.25], [-1.15, 3.2]]) if (!blocked(x, z, 0.08) && roomClear('second', x, z)) pot(b, x, z, 1.25, 0.012)
  // A steel rail round the passage over the court void (#30).
  for (const [hx0, hz0, hx1, hz1] of voids) {
    const o = 0.03
    rail(b, solid, hx0 - o, hz0 - o, hx0 - o, hz1 + o)
    rail(b, solid, hx1 + o, hz0 - o, hx1 + o, hz1 + o)
    rail(b, solid, hx0 - o, hz0 - o, hx1 + o, hz0 - o)
    rail(b, solid, hx0 - o, hz1 + o, hx1 + o, hz1 + o)
  }
}

// ---------- the basement ----------
// `b` holds what stands on the floor; `walls` holds what rises with the drawn
// walls (retaining walls, block facing) and drops with them when the house opens.
function basement(b, walls, info, ctx) {
  const { groundVoids, shift, street, upstairs, blocked, trees, rand } = ctx
  const hw = info.width / 2
  const hd = info.depth / 2
  const toHere = ([x0, z0, x1, z1]) => [x0 + shift.x, z0 + shift.z, x1 + shift.x, z1 + shift.z]
  const above = groundVoids.map(toHere)
  const mouthR = above.find((v) => v[3] > hd - 0.05 && v[0] + v[2] < 0)
  const courtVoid = above.find((v) => v[3] < hd - 0.05)

  // ----- the ramp from the street down to the parking (#3) -----
  const westFace = faceFrom(blocked, -1.6, -1.0, -1, 0, 0.8, PLAN.ramp.x0)
  const rx0 = Math.max(PLAN.ramp.x0, westFace)
  const eastFace = faceFrom(blocked, (PLAN.ramp.x0 + PLAN.ramp.x1) / 2, 2.5, 1, 0, 1.2, PLAN.ramp.x1)
  const rx1 = Math.min(eastFace, mouthR ? mouthR[2] + 0.02 : PLAN.ramp.x1)
  const zf = PLAN.ramp.foot
  const H = street
  const L = hd - zf
  put(b, 'wedge', 'solid', C.ramp, (rx0 + rx1) / 2, 0, zf + L / 2, rx1 - rx0, H - 0.002, L)
  // Grooves across the slope, the way a drive is brushed for grip.
  const theta = Math.atan2(H, L)
  for (let u = 0.07; u < 0.98; u += 0.09) {
    const z = zf + L * u
    const y = H * u
    put(b, 'box', 'decal', C.concreteJoint, (rx0 + rx1) / 2, y + Math.cos(theta) * 0.002, z - Math.sin(theta) * 0.002, rx1 - rx0 - 0.06, 0.004, 0.018, [-theta, 0, 0])
  }
  // The trench drain across the ramp's foot.
  span(b, C.granite, rx0, 0, zf - 0.17, rx1, 0.006, zf - 0.02, 'decal')
  for (let x = rx0 + 0.04; x < rx1 - 0.02; x += 0.05) span(b, C.steel, x - 0.008, 0.006, zf - 0.16, x + 0.008, 0.01, zf - 0.03, 'decal')
  // Retaining wall on the open west side, up to the ground floor's level,
  // where the drawn basement wall stops short of the street.
  const westEnd = faceFrom((x, z) => !blocked(x, z), (rx0 - hw) / 2 - 0.02, -1.0, 0, 1, 4, 1.5)
  span(walls, C.plasterShade, -hw, 0, westEnd - 0.02, rx0, upstairs - 0.01, hd)
  // A coping on the store-room wall along the ramp's east side, where the
  // ground floor is cut back above it.
  if (mouthR) span(walls, C.trim, eastFace - 0.02, upstairs - 0.16, mouthR[1], eastFace + 0.14, upstairs - 0.01, hd)
  // A slatted gate at the ramp's head (#3), shut.
  slatGate(b, rx0 + 0.03, hd - 0.05, rx1 - 0.03, hd - 0.05, H, 0.4, 6)

  // ----- parking: grey concrete in saw-cut squares, block wall (#2) -----
  for (const r of PLAN.parking) {
    span(b, C.concrete, r[0], 0, r[1], r[2], 0.006, r[3], 'decal')
    joints(b, C.concreteJoint, r, { step: 0.62, y: 0.006, w: 0.01 })
  }
  // The block wall: a facing of grey concrete block on the west wall's inner face.
  const bz0 = PLAN.parking[0][1] + 0.02
  const bz1 = westEnd - 0.04
  span(walls, C.block, westFace, 0, bz0, westFace + 0.008, 1.29, bz1)
  for (let y = 0.1, k = 0; y < 1.28; y += 0.1, k++) {
    span(walls, C.blockJoint, westFace + 0.008, y - 0.004, bz0, westFace + 0.012, y + 0.004, bz1, 'decal')
    for (let z = bz0 + (k % 2 ? 0.1 : 0.2); z < bz1 - 0.02; z += 0.2) span(walls, C.blockJoint, westFace + 0.008, y - 0.096, z - 0.004, westFace + 0.012, y - 0.004, z + 0.004, 'decal')
  }
  // The car (#2): a plain massing, nose to the ramp.
  const car = PLAN.car
  cube(b, C.car, car.x, 0.07, car.z, 0.7, 0.28, 1.85)
  cube(b, C.glass, car.x, 0.35, car.z - 0.08, 0.62, 0.22, 0.98, { kind: 'glass' })
  cube(b, C.car, car.x, 0.57, car.z - 0.08, 0.6, 0.02, 0.9)
  for (const dx of [-0.33, 0.33]) for (const dz of [-0.62, 0.62]) put(b, 'cyl', 'solid', C.granite, car.x + dx, 0.11, car.z + dz, 0.11, 0.08, 0.11, [0, 0, Math.PI / 2])

  // ----- Court 1 and its stair up to the ground floor (#20) -----
  const court = PLAN.court
  span(b, C.flag, court[0], 0, court[1], court[2], 0.008, court[3], 'decal')
  flags(b, C.flagJoint, court, 0.008, rand, { row: 0.32 })
  for (const t of trees) {
    const { x, z } = t.position
    span(b, C.earth, x - 0.24, 0.008, z - 0.24, x + 0.24, 0.016, z + 0.24, 'decal')
    span(b, C.kota, x - 0.28, 0, z - 0.28, x + 0.28, 0.05, z - 0.24)
    span(b, C.kota, x - 0.28, 0, z + 0.24, x + 0.28, 0.05, z + 0.28)
    span(b, C.kota, x - 0.28, 0, z - 0.24, x - 0.24, 0.05, z + 0.24)
    span(b, C.kota, x + 0.24, 0, z - 0.24, x + 0.28, 0.05, z + 0.24)
  }
  // A straight flight from a landing by the court, west and up to arrive in
  // the void beside the foyer. Over the rooms the plan draws below, only the
  // treads are shown.
  const st = PLAN.stair
  const top = courtVoid ? courtVoid[0] : 0.144
  const sz0 = st.z0
  const sz1 = courtVoid ? Math.min(st.z1, courtVoid[3] - 0.015) : st.z1
  const rise = (upstairs - 0.004) / st.risers
  const run = (st.bottom - top) / st.risers
  span(b, C.kota, st.bottom, 0, sz0, st.landing, 0.012, sz1, 'decal')
  for (let i = 0; i < st.risers; i++) {
    const xa = st.bottom - (i + 1) * run
    const h = (i + 1) * rise
    const y0 = xa + run / 2 > st.open ? 0 : Math.max(0, h - 0.14)
    span(b, C.kota, xa, y0, sz0, xa + run, h, sz1)
  }
  // Its teak balustrade on the open, court side.
  const bz = sz0 - 0.015
  const rail0 = V(st.landing, 0.36, bz)
  const rail1 = V(top + 0.05, upstairs + 0.36 - rise, bz)
  rod(b, C.teak, V(st.bottom, 0.36, bz), rail1, 0.014, { kind: 'solid' })
  rod(b, C.teak, rail0, V(st.bottom, 0.36, bz), 0.014, { kind: 'solid' })
  for (let i = 0; i < st.risers; i += 2) {
    const x = st.bottom - (i + 0.5) * run
    const y = (i + 1) * rise
    cube(b, C.teak, x, y, bz, 0.016, 0.34, 0.016)
  }
  for (const x of [st.landing, st.bottom]) cube(b, C.teak, x, 0, bz, 0.03, 0.37, 0.03)

  // ----- the office's open-to-sky court and its stair up to the street -----
  const os = PLAN.officeStair
  const frontFace = faceFrom(blocked, (os.x0 + os.x1) / 2, hd - 0.4, 0, 1, 0.4, hd - 0.02)
  const oz1 = Math.min(frontFace, hd - 0.02)
  const oz0 = oz1 - 0.42
  const [ox0, oy0, ox1] = PLAN.openCourt
  const open = [ox0, oy0, ox1, oz0 - 0.01]
  span(b, C.flag, open[0], 0, open[1], open[2], 0.008, open[3], 'decal')
  flags(b, C.flagJoint, open, 0.008, rand, { row: 0.3 })
  const ostep = (os.x1 - os.x0) / os.risers
  for (let i = 0; i < os.risers; i++) span(b, C.kota, os.x0 + i * ostep, 0, oz0, os.x0 + (i + 1) * ostep, ((i + 1) * H) / os.risers, oz1)
  span(b, C.kota, os.x1, 0, oz0, hw, H, oz1)
  // Its steel handrail on the court side.
  const hz = oz0 - 0.015
  rod(b, C.steel, V(os.x0, 0.34, hz), V(os.x1, H + 0.34, hz), 0.01)
  for (const [x, y] of [[os.x0, 0], [(os.x0 + os.x1) / 2, H / 2], [os.x1, H]]) cube(b, C.steel, x, y, hz, 0.02, 0.34, 0.02, { kind: 'metal' })
  // A drain at the court's low point, and ferns where the stair leaves room.
  const dx = (open[0] + open[2]) / 2 + 0.1
  const dz = (open[1] + open[3]) / 2
  span(b, C.granite, dx - 0.09, 0.008, dz - 0.09, dx + 0.09, 0.014, dz + 0.09, 'decal')
  for (let i = 0; i < 4; i++) span(b, C.steel, dx - 0.07, 0.014, dz - 0.07 + i * 0.045, dx + 0.07, 0.018, dz - 0.055 + i * 0.045, 'decal')
  for (const [x, z] of [[open[2] - 0.12, open[3] - 0.14], [open[2] - 0.12, open[1] + 0.3]]) if (!blocked(x, z, 0.08) && roomClear('basement', x, z)) pot(b, x, z, 1.3, 0.008)

  // ----- everywhere else: terrazzo (#10) -----
  const finished = [...PLAN.parking, court, open, [rx0, PLAN.ramp.foot - 0.2, rx1, hd], [st.bottom - st.risers * run, sz0, st.landing, sz1], [os.x0, oz0, hw, oz1]]
  joints(b, C.terrazzoJoint, [-hw + 0.03, -hd + 0.03, hw - 0.03, hd - 0.03], { step: 0.5, y: 0, holes: finished })
}

// ---------- the street ----------
function readStreet(ground) {
  const strips = []
  const poles = []
  const trees = []
  const masses = []
  const fences = []
  for (const o of ground.children) {
    if (o.userData?.crown) trees.push(o)
    const p = o.isMesh && o.geometry.type === 'BoxGeometry' && o.geometry.parameters
    if (!p) continue
    if (p.width >= 50 && p.height < 0.05) strips.push({ z0: o.position.z - p.depth / 2, z1: o.position.z + p.depth / 2, top: o.position.y + p.height / 2 })
    else if (p.height > 2 && p.width < 0.2) poles.push(o.position)
    else if (p.height >= 0.9 && p.width >= 4 && p.depth >= 4) masses.push(o)
    else if (p.height > 0.25 && p.height < 0.4 && p.depth < 0.15 && p.width >= 3) fences.push(o)
  }
  strips.sort((a, b) => a.z0 - b.z0)
  const near = (a, b) => Math.abs(a - b) < 0.02
  const asphalt = strips.reduce((m, s) => (!m || s.z1 - s.z0 > m.z1 - m.z0 ? s : m), null) || { z0: 6.5, z1: 9.25, top: 0.009 }
  const verge = strips.find((s) => near(s.z1, asphalt.z0)) || { z0: 6.15, z1: 6.5, top: 0.01 }
  const pavement = strips.find((s) => near(s.z1, verge.z0)) || { z0: 5.0, z1: 6.15, top: 0.01 }
  const farVerge = strips.find((s) => near(s.z0, asphalt.z1)) || { z0: 9.25, z1: 9.55, top: 0.01 }
  const topAt = (z) => strips.reduce((t, s) => (z >= s.z0 && z <= s.z1 ? Math.max(t, s.top) : t), 0)
  return { asphalt, verge, pavement, farVerge, topAt, poles, trees, masses, fences }
}

// A bicycle on its stand, leaning a little. Exploratory.
function bicycle(b, x, y, z, yaw) {
  const base = new THREE.Matrix4().compose(V(x, y, z), new THREE.Quaternion().setFromEuler(new THREE.Euler(0.13, yaw, 0, 'YXZ')), V(1, 1, 1))
  const R = V(-0.26, 0.13, 0)
  const F = V(0.26, 0.13, 0)
  const B = V(-0.03, 0.11, 0)
  const S = V(-0.11, 0.33, 0)
  const H = V(0.19, 0.34, 0)
  const L = V(0.21, 0.29, 0)
  for (const w of [R, F]) {
    put(b, 'ring', 'metal', C.granite, w.x, w.y, w.z, 0.125, 0.125, 0.125, 0, base)
    put(b, 'cyl', 'metal', C.steel, w.x, w.y, w.z, 0.012, 0.03, 0.012, [Math.PI / 2, 0, 0], base)
  }
  const frame = { base }
  for (const [a, c] of [[R, B], [R, S], [B, S], [S, H], [B, L], [L, F], [H, V(0.18, 0.4, 0)]]) rod(b, C.redOxide, a, c, 0.008, frame)
  rod(b, C.steel, V(0.17, 0.4, -0.1), V(0.17, 0.4, 0.1), 0.007, frame)
  rod(b, C.steel, S, V(-0.12, 0.37, 0), 0.006, frame)
  rod(b, C.steel, B, V(-0.08, -0.005, 0.07), 0.005, frame)
  cube(b, C.granite, -0.125, 0.37, 0, 0.08, 0.016, 0.04, { kind: 'metal', base })
  cube(b, C.steel, -0.25, 0.27, 0, 0.2, 0.01, 0.08, { kind: 'metal', base })
}

function street(b, s, plot, rand) {
  const X = 28
  const { asphalt, verge, pavement, farVerge, poles, trees } = s
  const obstacles = [...poles.map((p) => [p.x, p.z]), ...trees.map((t) => [t.position.x, t.position.z])]
  const nearObstacle = (x, z, r) => obstacles.some(([ox, oz]) => Math.hypot(ox - x, oz - z) < r)
  const inPlot = (x, z) => x > plot.x0 - 0.1 && x < plot.x1 + 0.1 && z < plot.z1 + 0.06

  // Kerbs both sides of the road, laid in blocks, alternating in tone.
  for (const z of [asphalt.z0, asphalt.z1]) {
    let i = 0
    for (let x = -X; x < X; x += 0.6, i++) {
      if (trees.some((t) => Math.abs(t.position.x - (x + 0.3)) < 0.55 && Math.abs(t.position.z - z) < 0.5)) continue
      span(b, i % 2 ? C.kerb : C.kerbShade, x + 0.006, 0, z - 0.04, x + 0.594, 0.05, z + 0.04)
    }
  }
  // Pavement slabs: seams across, one down the middle, an edging at the verge.
  const pt = pavement.top
  for (let x = -X; x < X; x += 0.6) span(b, C.seam, x - 0.004, pt, pavement.z0 + 0.02, x + 0.004, pt + 0.004, pavement.z1 - 0.02, 'decal')
  const pm = (pavement.z0 + pavement.z1) / 2
  span(b, C.seam, -X, pt, pm - 0.004, X, pt + 0.004, pm + 0.004, 'decal')
  span(b, C.kerbShade, -X, 0, verge.z0 - 0.03, X, pt + 0.015, verge.z0 + 0.03)
  // Drains at the road's edge: a dark grate with steel bars.
  const at = asphalt.top
  for (let x = -X + 2.3, k = 0; x < X; x += 5.5, k++) {
    const z = k % 2 ? asphalt.z0 + 0.15 : asphalt.z1 - 0.15
    span(b, C.granite, x - 0.2, at, z - 0.08, x + 0.2, at + 0.006, z + 0.08, 'decal')
    for (let i = 0; i < 6; i++) span(b, C.gate, x - 0.17 + i * 0.065, at + 0.006, z - 0.06, x - 0.15 + i * 0.065, at + 0.01, z + 0.06, 'decal')
  }
  // Tree guards: a low brick ring round each street tree.
  for (const t of trees) {
    const { x, z } = t.position
    for (let i = 0; i < 8; i++) {
      const a = (i / 8) * Math.PI * 2
      cube(b, '#9a5a3c', x + Math.cos(a) * 0.22, s.topAt(z), z + Math.sin(a) * 0.22, 0.17, 0.07, 0.04, { yaw: -a + Math.PI / 2 })
    }
  }
  // Planting on the verges, in clumps, clear of posts and trunks.
  for (const v of [verge, farVerge]) {
    const vz = (v.z0 + v.z1) / 2
    for (let x = -X + rand(); x < X; x += 1.1 + rand() * 1.2) {
      if (nearObstacle(x, vz, 0.5) || inPlot(x, vz)) continue
      const n = 2 + Math.floor(rand() * 3)
      for (let i = 0; i < n; i++) {
        const sz = 0.05 + rand() * 0.07
        blob(b, rand() < 0.35 ? C.foliageLight : C.foliage, x + (rand() - 0.5) * 0.4, v.top + sz * 0.5, vz + (rand() - 0.5) * (v.z1 - v.z0 - 0.12), sz, sz * 0.8, sz, rand() * 6)
      }
    }
  }
  // Fallen gulmohar petals under the flowering trees.
  for (const t of trees) {
    let flowers = 0
    for (const c of t.userData.crown.children) if (c.geometry?.parameters?.radius === 0.045) flowers += c.isInstancedMesh ? c.count : 1
    if (!flowers) continue
    const trunk = t.children.find((c) => c.geometry?.type === 'CylinderGeometry')
    const spread = trunk ? trunk.geometry.parameters.radiusBottom / 0.09 : 1.3
    const R = 1.5 * spread
    for (let i = 0; i < flowers * 4; i++) {
      const a = rand() * Math.PI * 2
      const r = R * Math.pow(rand(), 0.7)
      const x = t.position.x + Math.cos(a) * r
      const z = t.position.z + Math.sin(a) * r
      if (inPlot(x, z)) continue
      if (z > asphalt.z0 && z < asphalt.z1 && rand() < 0.6) continue
      cube(b, C.petals[i % C.petals.length], x, s.topAt(z) + 0.004 + rand() * 0.008, z, 0.03, 0.003, 0.022, { kind: 'decal', yaw: rand() * Math.PI })
    }
  }
  // A bicycle on the pavement beside the gate steps.
  const bx = plot.x0 - 0.75
  if (!nearObstacle(bx, pavement.z0 + 0.24, 0.4)) bicycle(b, bx, pavement.top + 0.006, pavement.z0 + 0.24, 0)
  // The office's own gate at the street line (ground plan, front right), open.
  slatGate(b, plot.x1 - 0.12, plot.z1 - 0.03, plot.x1 - 0.12, plot.z1 - 0.45, 0, 0.4, 6)
}

// ---------- the neighbours ----------
// A wall face: place boxes by distance along it, height, and distance out.
function facade(b, ox, oz, yaw) {
  const tx = Math.cos(yaw)
  const tz = -Math.sin(yaw)
  const nx = Math.sin(yaw)
  const nz = Math.cos(yaw)
  return (color, kind, a, y, o, w, h, d) => cube(b, color, ox + a * tx + o * nx, y, oz + a * tz + o * nz, w, h, d, { kind, yaw })
}
function windowOn(f, a, y0, rand, { w = 0.38, h = 0.44 } = {}) {
  f(C.glass, rand() < 0.3 ? 'lit' : 'glass', a, y0, 0.006, w, h, 0.02)
  f(C.plasterShade, 'solid', a - w / 2 - 0.015, y0, 0.01, 0.03, h, 0.03)
  f(C.plasterShade, 'solid', a + w / 2 + 0.015, y0, 0.01, 0.03, h, 0.03)
  f(C.plasterShade, 'solid', a, y0 + h, 0.01, w + 0.06, 0.03, 0.03)
  f(C.steel, 'metal', a, y0, 0.012, 0.014, h, 0.02)
  f(C.trim, 'solid', a, y0 - 0.035, 0.03, w + 0.1, 0.035, 0.07)
  // A chajja: the thin concrete sunshade over each window.
  f(C.trim, 'solid', a, y0 + h + 0.09, 0.07, w + 0.18, 0.025, 0.14)
}
function doorOn(f, a) {
  f(C.teak, 'solid', a, 0.04, 0.008, 0.36, 0.8, 0.02)
  f(C.plasterShade, 'solid', a - 0.195, 0.04, 0.012, 0.03, 0.83, 0.028)
  f(C.plasterShade, 'solid', a + 0.195, 0.04, 0.012, 0.03, 0.83, 0.028)
  f(C.plasterShade, 'solid', a, 0.84, 0.012, 0.42, 0.03, 0.028)
  f(C.trim, 'solid', a, 0.95, 0.11, 0.56, 0.03, 0.22)
  f(C.trim, 'solid', a, 0, 0.09, 0.5, 0.04, 0.18)
}
function neighbours(b, s, rand) {
  const mid = (s.asphalt.z0 + s.asphalt.z1) / 2
  for (const m of s.masses) {
    const { width: w, height: h, depth: d } = m.geometry.parameters
    const { x, z } = m.position
    const toStreet = z < mid ? 1 : -1
    const yaw = toStreet > 0 ? 0 : Math.PI
    const front = facade(b, x, z + (toStreet * d) / 2, yaw)
    // Front: a row of windows, one bay given to the door.
    const n = Math.max(2, Math.floor((w - 0.9) / 0.9))
    const door = n < 3 ? 0 : rand() < 0.5 ? 1 : n - 2
    for (let i = 0; i < n; i++) {
      const a = (i - (n - 1) / 2) * 0.9
      if (i === door) doorOn(front, a)
      else windowOn(front, a, 0.3, rand)
    }
    // The side that faces the house gets windows too.
    const inward = x > 0 ? -1 : 1
    const side = facade(b, x + (inward * w) / 2, z, (inward * Math.PI) / 2)
    for (const a of [-d * 0.28, 0, d * 0.28]) windowOn(side, a, 0.3, rand, { w: 0.32 })
    // Roof: a parapet with a coping, a string course under it, a water tank.
    const P = 0.09
    span(b, C.plaster, x - w / 2, h, z - d / 2, x + w / 2, h + P, z - d / 2 + 0.05)
    span(b, C.plaster, x - w / 2, h, z + d / 2 - 0.05, x + w / 2, h + P, z + d / 2)
    span(b, C.plaster, x - w / 2, h, z - d / 2 + 0.05, x - w / 2 + 0.05, h + P, z + d / 2 - 0.05)
    span(b, C.plaster, x + w / 2 - 0.05, h, z - d / 2 + 0.05, x + w / 2, h + P, z + d / 2 - 0.05)
    span(b, C.trim, x - w / 2 - 0.01, h + P, z - d / 2 - 0.01, x + w / 2 + 0.01, h + P + 0.02, z - d / 2 + 0.06)
    span(b, C.trim, x - w / 2 - 0.01, h + P, z + d / 2 - 0.06, x + w / 2 + 0.01, h + P + 0.02, z + d / 2 + 0.01)
    span(b, C.trim, x - w / 2 - 0.01, h + P, z - d / 2 + 0.06, x - w / 2 + 0.06, h + P + 0.02, z + d / 2 - 0.06)
    span(b, C.trim, x + w / 2 - 0.06, h + P, z - d / 2 + 0.06, x + w / 2 + 0.01, h + P + 0.02, z + d / 2 - 0.06)
    front(C.trim, 'solid', 0, h - 0.11, 0, w + 0.03, 0.03, 0.03)
    if (rand() < 0.65) {
      const tx = x + (rand() < 0.5 ? -1 : 1) * (w / 2 - 0.45)
      const tz = z - toStreet * (d / 2 - 0.5)
      cube(b, C.plasterShade, tx, h, tz, 0.4, 0.06, 0.4)
      post(b, C.tank, tx, h + 0.06, tz, 0.16, 0.26)
    }
    // A steel gate in the compound wall, in line with the door.
    const fence = s.fences.find((f) => Math.abs(f.position.x - x) < 0.3 && Math.sign(f.position.z - z) === toStreet)
    if (fence) {
      const gx = x + (door - (n - 1) / 2) * 0.9 * Math.cos(yaw)
      const fz = fence.position.z
      cube(b, C.gate, gx, 0, fz, 0.52, 0.36, 0.1, { kind: 'metal' })
      for (const px of [gx - 0.31, gx + 0.31]) cube(b, C.plaster, px, 0, fz, 0.1, 0.42, 0.12)
      for (let i = 0; i < 3; i++) {
        const px = gx + (i + 1) * (0.6 + rand() * 0.5) * (rand() < 0.5 ? -1 : 1)
        if (Math.abs(px - x) < w / 2 - 0.2) pot(b, px, fz + toStreet * 0.16, 1.1 + rand() * 0.4)
      }
    }
  }
}

// ---------- entry ----------
// Call once, with the house closed, after the floors, slabs, surfaces, trees
// and lights are built.
export function addWorldDetails({ ground, floors, house }) {
  const rand = seeded(1172)
  const meshes = []
  const done = (b) => meshes.push(...b.flush())
  const voids = {}
  for (const [id, floor] of Object.entries(floors)) voids[id] = voidsOf(id, floor)

  const build = { ground: groundFloor, first: firstFloor, second: secondFloor }
  for (const [id, fn] of Object.entries(build)) {
    const floor = floors[id]
    const info = house.floors[id]
    if (!floor || !info) continue
    const b = batch(floor, id)
    // Where the stair up from Court 1 arrives, in ground floor coordinates.
    const arrive = floors.basement ? PLAN.stair.z0 + floors.basement.position.z - floor.position.z : undefined
    fn(b, info, voids[id], footprint(floor), rand, { arrive })
    slabTrim(b, info, voids[id])
    done(b)
  }

  const B = floors.basement
  if (B && floors.ground && house.floors.basement) {
    // What rises with the drawn walls follows their height as they drop.
    let drawn = null
    B.traverse((o) => {
      if (o.isMesh && o.name === 'walls') drawn = o
    })
    const full = drawn ? drawn.scale.y : 1
    const follow = function () {
      if (!drawn) return
      const k = drawn.scale.y / full
      if (this.scale.y !== k) {
        this.scale.y = k
        this.updateMatrixWorld()
      }
    }
    const b = batch(B, 'basement')
    const walls = batch(B, 'basement-walls', follow)
    basement(b, walls, house.floors.basement, {
      groundVoids: voids.ground || [],
      shift: { x: floors.ground.position.x - B.position.x, z: floors.ground.position.z - B.position.z },
      street: (ground ? ground.position.y : 0) - B.position.y,
      upstairs: floors.ground.position.y - B.position.y,
      blocked: footprint(B),
      trees: B.children.filter((o) => o.userData?.crown),
      rand,
    })
    done(b)
    done(walls)
  }
  // The ground floor's skirt gets a granite plinth band at the street.
  if (floors.ground) {
    const b = batch(floors.ground, 'plinth')
    for (const o of floors.ground.children) {
      const p = o.isMesh && o.geometry.type === 'BoxGeometry' && o.geometry.parameters
      if (!p || Math.abs(p.height - 0.6) > 0.01) continue
      const { x, y, z } = o.position
      cube(b, C.granite, x, y - p.height / 2, z, p.width + 0.03, 0.07, p.depth + 0.03)
    }
    done(b)
  }
  if (ground) {
    const s = readStreet(ground)
    const g = house.floors.ground
    const plot = { x0: g.offset[0] - g.width / 2, x1: g.offset[0] + g.width / 2, z1: g.offset[1] + g.depth / 2 }
    const b = batch(ground, 'street')
    street(b, s, plot, rand)
    neighbours(b, s, rand)
    done(b)
  }

  return {
    meshes,
    dispose() {
      for (const m of meshes) {
        m.removeFromParent()
        m.dispose()
      }
    },
  }
}
