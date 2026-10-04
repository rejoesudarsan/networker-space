// People, and the furniture they gather around.
// World units (1 = 8 ft). A person stands ~0.68 tall, feet at y = 0, facing +Z.
// Each person is a single skinned mesh: limbs are merged into one vertex-coloured
// geometry bound to a small skeleton, so a crowd costs one draw call per person
// while arms, knees and heads still move. Looks (and their geometry) are cached.

import * as THREE from 'three'
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js'

const rand = (a, b) => a + Math.random() * (b - a)
const pick = (arr) => arr[Math.floor(Math.random() * arr.length)]
const chance = (p) => Math.random() < p
const frac = (x) => x - Math.floor(x)
const smooth = (a, b, x) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)))
  return t * t * (3 - 2 * t)
}
const weighted = (table) => {
  let r = Math.random() * table.reduce((s, [, w]) => s + w, 0)
  for (const [v, w] of table) if ((r -= w) <= 0) return v
  return table[0][0]
}

// ---------- materials ----------
const matCache = new Map()
const mat = (color, opts = {}) => {
  const key = color + JSON.stringify(opts)
  if (!matCache.has(key)) matCache.set(key, new THREE.MeshStandardMaterial({ color, roughness: 0.85, ...opts }))
  return matCache.get(key)
}
const PERSON_MAT = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.82 })

// ---------- geometry helpers ----------
const Box = (w, h, d) => new THREE.BoxGeometry(w, h, d)
const Cyl = (rt, rb, h, seg = 10) => new THREE.CylinderGeometry(rt, rb, h, seg)
const Sph = (r, ws = 10, hs = 8, ...rest) => new THREE.SphereGeometry(r, ws, hs, ...rest)
const Cap = (r, len, cs = 3, rs = 8) => new THREE.CapsuleGeometry(r, len, cs, rs)
// Scale, then rotate, then move — in that order.
function place(g, p = [0, 0, 0], r = [0, 0, 0], s = [1, 1, 1]) {
  if (typeof s === 'number') s = [s, s, s]
  g.scale(s[0], s[1], s[2])
  if (r[0]) g.rotateX(r[0])
  if (r[1]) g.rotateY(r[1])
  if (r[2]) g.rotateZ(r[2])
  g.translate(p[0], p[1], p[2])
  return g
}
// Merge into one geometry; position + normal only (nothing here is textured).
function merge(list, indexed = false) {
  const parts = list.map((g) => {
    const n = indexed || !g.index ? g : g.toNonIndexed()
    n.clearGroups()
    for (const k of Object.keys(n.attributes)) if (!KEEP.has(k)) n.deleteAttribute(k)
    return n
  })
  const out = mergeGeometries(parts, false)
  if (!out) throw new Error('characters: merge failed')
  for (const g of new Set([...list, ...parts])) g.dispose()
  return out
}
const KEEP = new Set(['position', 'normal', 'color', 'skinIndex', 'skinWeight'])

// A kit is a cached multi-material prop: [[material, [geometries]], ...] → one mesh.
const kits = new Map()
function kit(key, build, { cast = false, receive = true } = {}) {
  let k = kits.get(key)
  if (!k) {
    const spec = build()
    const geos = spec.map(([, gs]) => merge(gs))
    const geo = geos.length === 1 ? geos[0] : mergeGeometries(geos, true)
    k = { geo, mats: spec.map(([m]) => m) }
    kits.set(key, k)
  }
  const m = new THREE.Mesh(k.geo, k.mats.length === 1 ? k.mats[0] : k.mats)
  m.castShadow = cast
  m.receiveShadow = receive
  return m
}

// ---------- proportions ----------
const THIGH = 0.155
const SHIN = 0.15
const ANKLE = 0.027 // ankle joint above the sole
const THIGH_R = 0.029
const HIP_X = 0.042
const SPINE_Y = 0.005
const SHOULDER_X = 0.079
const SHOULDER_Y = 0.195
const NECK_Y = 0.222
const HEAD_Y = 0.055
const UPPER = 0.12
const FORE = 0.11
// Height of the hip joint above the soles for a leg with thigh angle a, shin
// angle b (both forward from straight down) and outward spread z.
const legH = (a, b, z = 0) => (THIGH + SHIN * Math.cos(a - b)) * Math.cos(z) * Math.cos(a) + SHIN * Math.sin(a - b) * Math.sin(a) + ANKLE
const STAND_H = legH(0, 0)

/** Character height, for reference. */
export const HEIGHT = 0.68
/** Seat-top height of every chair, stool and pouf; the 'seated' pose rests on it. */
export const SEAT_H = 0.165

// ---------- the skeleton ----------
// [name, parent, offset(look)]
const BONES = [
  ['body', -1, () => [0, 0, 0]],
  ['pelvis', 0, () => [0, STAND_H, 0]],
  ['hipL', 1, () => [HIP_X, 0, 0]],
  ['kneeL', 2, () => [0, -THIGH, 0]],
  ['ankleL', 3, () => [0, -SHIN, 0]],
  ['hipR', 1, () => [-HIP_X, 0, 0]],
  ['kneeR', 5, () => [0, -THIGH, 0]],
  ['ankleR', 6, () => [0, -SHIN, 0]],
  ['spine', 1, () => [0, SPINE_Y, 0]],
  ['neck', 8, () => [0, NECK_Y, 0]],
  ['shoulderL', 8, (l) => [SHOULDER_X * l.width, SHOULDER_Y, 0]],
  ['elbowL', 10, () => [0, -UPPER, 0]],
  ['shoulderR', 8, (l) => [-SHOULDER_X * l.width, SHOULDER_Y, 0]],
  ['elbowR', 12, () => [0, -UPPER, 0]],
  ['hem', 1, () => [0, 0.02, 0]],
]
const BONE = Object.fromEntries(BONES.map(([n], i) => [n, i]))

// ---------- body part templates (bone-local) ----------
const torsoGeo = () => {
  const pts = [[0, 0], [0.048, 0], [0.051, 0.03], [0.055, 0.08], [0.061, 0.14], [0.062, 0.175], [0.056, 0.205], [0.04, 0.224], [0.018, 0.232], [0, 0.234]]
  return new THREE.LatheGeometry(pts.map(([x, y]) => new THREE.Vector2(x, y)), 12)
}
const hairCap = (r, tilt, len) => place(Sph(r, 14, 8, 0, Math.PI * 2, 0, len), [0, HEAD_Y + 0.004, -0.004], [-tilt, 0, 0])
const PARTS = {
  pelvis: () => place(Sph(1, 12, 8), [0, 0, -0.004], 0, [0.056, 0.05, 0.043]),
  thigh: () => place(Cap(THIGH_R, THIGH, 3, 9), [0, -THIGH / 2, 0]),
  shin: () => place(Cap(0.024, SHIN, 3, 9), [0, -SHIN / 2, 0]),
  shoe: () => place(Cap(0.021, 0.05, 3, 8), [0, -0.013, 0.014], [Math.PI / 2, 0, 0], [1, 1, 0.62]),
  upper: () => place(Cap(0.021, UPPER, 3, 8), [0, -UPPER / 2, 0]),
  fore: () => place(Cap(0.018, FORE, 3, 8), [0, -FORE / 2, 0]),
  hand: () => place(Sph(0.02, 8, 6), [0, -FORE - 0.012, 0.003], 0, [0.9, 1.15, 0.75]),
  head: () => place(Sph(0.062, 14, 10), [0, HEAD_Y, 0.002], 0, [0.94, 1.04, 1]),
  neck: () => place(Cyl(0.021, 0.024, 0.05, 8), [0, 0.015, 0]),
  panel: () => place(Box(0.034, 0.15, 0.012), [0, 0.125, 0.04]),
  tunic: () => place(Cyl(0.057, 0.075, 0.17, 12), [0, -0.085, 0], 0, [1, 1, 0.82]),
  skirt: () => place(Cyl(0.057, 0.082, 0.14, 12), [0, -0.07, 0], 0, [1, 1, 0.85]),
  dress: () => place(Cyl(0.057, 0.085, 0.18, 12), [0, -0.09, 0], 0, [1, 1, 0.85]),
}
const HAIR = {
  none: () => [],
  short: () => [hairCap(0.066, 0.5, Math.PI * 0.5)],
  crop: () => [hairCap(0.0645, 0.35, Math.PI * 0.42)],
  long: () => [hairCap(0.067, 0.45, Math.PI * 0.55), place(Cap(0.05, 0.07, 3, 10), [0, HEAD_Y - 0.055, -0.035], 0, [1, 1, 0.55])],
  bun: () => [hairCap(0.066, 0.5, Math.PI * 0.5), place(Sph(0.027, 10, 8), [0, HEAD_Y + 0.05, -0.048])],
  pony: () => [hairCap(0.066, 0.5, Math.PI * 0.5), place(Cap(0.017, 0.07, 3, 8), [0, HEAD_Y - 0.03, -0.078], [0.35, 0, 0])],
  curly: () => [place(Sph(0.07, 12, 9), [0, HEAD_Y + 0.018, -0.02], 0, [1, 0.88, 1])],
}
// Accessories: [bone, colour key, geometries]
const ACC = {
  glasses: () => ['neck', '#1d1d1c', [
    place(new THREE.TorusGeometry(0.013, 0.0028, 4, 10), [0.021, HEAD_Y + 0.008, 0.06]),
    place(new THREE.TorusGeometry(0.013, 0.0028, 4, 10), [-0.021, HEAD_Y + 0.008, 0.06]),
    place(Box(0.014, 0.003, 0.003), [0, HEAD_Y + 0.011, 0.062]),
  ]],
  cap: (c) => ['neck', c, [
    hairCap(0.069, 0.15, Math.PI * 0.42),
    place(Cyl(0.045, 0.045, 0.005, 12), [0, HEAD_Y + 0.035, 0.058], [0.12, 0, 0], [1, 1, 0.75]),
  ]],
  sunhat: (c) => ['neck', c, [
    place(Cyl(0.105, 0.105, 0.005, 16), [0, HEAD_Y + 0.034, -0.004]),
    place(Cyl(0.05, 0.06, 0.04, 12), [0, HEAD_Y + 0.054, -0.004]),
  ]],
  scarf: (c) => ['spine', c, [
    place(new THREE.TorusGeometry(0.036, 0.014, 6, 12), [0, NECK_Y + 0.002, 0], [Math.PI / 2, 0, 0], [1, 0.8, 1]),
    place(Box(0.026, 0.09, 0.012), [0.022, NECK_Y - 0.05, 0.047], [0, 0, 0.08]),
  ]],
  backpack: (c) => ['spine', c, [place(Box(0.08, 0.1, 0.035), [0, 0.12, -0.062]), place(Cyl(0.04, 0.04, 0.035, 10), [0, 0.17, -0.062], [Math.PI / 2, 0, 0])]],
  beard: (c) => ['neck', c, [place(Sph(0.064, 12, 6, Math.PI * 0.15, Math.PI * 0.7, Math.PI * 0.55, Math.PI * 0.32), [0, HEAD_Y, 0.004])]],
}

// ---------- looks ----------
const SKIN = ['#8d5a3b', '#a8704a', '#6e4630', '#c08a62', '#7b4f35', '#5a3a28', '#d0a07a']
const HAIR_C = ['#16120f', '#1f1813', '#2b211b', '#2b211b', '#3d2c20', '#5a3d2b', '#7d7873', '#a48356']
const TOPS = ['#2f3a44', '#7a3f1f', '#b5562f', '#d9d3c7', '#3f5a2c', '#e7dcc8', '#8c6e55', '#1d1d1c', '#6b7f8e', '#a34a3a', '#c9b48f', '#f1ece2', '#c47b2b', '#3d4f6b', '#6d2f4a', '#2f5b55', '#d8b7a0']
const BOTTOMS = ['#2a2f38', '#3b4a63', '#4f6280', '#d8cfbd', '#8c7a5c', '#1d1d1c', '#5b4636', '#e9e3d6', '#4a4d4f', '#6b5a3f']
const SHOES = ['#f2efe8', '#1d1d1c', '#6b4a2e', '#8a5232', '#c9b48f', '#3a3d42']
const HATS = ['#e7dcc8', '#c9b48f', '#2f3a44', '#a34a3a', '#1d1d1c']

function randomLook() {
  const cut = weighted([['trousers', 38], ['shorts', 10], ['skirt', 12], ['dress', 10], ['kurta', 15], ['jacket', 15]])
  const skin = pick(SKIN)
  const top = pick(TOPS)
  let bottom = pick(BOTTOMS)
  if (bottom === top) bottom = BOTTOMS[0]
  const hair = weighted([['short', 28], ['crop', 14], ['long', 16], ['bun', 10], ['pony', 10], ['curly', 12], ['none', 8]])
  const acc = []
  if (chance(0.25)) acc.push('glasses')
  if (chance(0.1)) acc.push('cap')
  else if (chance(0.05)) acc.push('sunhat')
  if (chance(0.12)) acc.push('scarf')
  if (chance(0.12)) acc.push('backpack')
  if (!['long', 'bun', 'pony'].includes(hair) && chance(0.2)) acc.push('beard')
  return {
    cut,
    skin,
    hairColor: pick(HAIR_C),
    hair,
    top,
    bottom,
    jacket: cut === 'jacket' ? pick(['#2f3a44', '#1d1d1c', '#8c6e55', '#3f5a2c', '#4a4d4f', '#6b5a3f']) : null,
    legs: chance(0.3) ? pick(['#1d1d1c', '#3a3d42']) : skin,
    shoes: pick(SHOES),
    sleeves: cut === 'jacket' || (cut === 'kurta' && chance(0.6)) || chance(0.2) ? 'long' : 'short',
    accent: pick(TOPS),
    hat: pick(HATS),
    width: rand(0.93, 1.08),
    acc,
  }
}

// Geometry per look, capped so a long-running page doesn't grow without bound.
const MAX_LOOKS = 64
const looks = []
const lookByKey = new Map()
const tmpColor = new THREE.Color()

function lookEntry(look) {
  const key = JSON.stringify(look)
  if (lookByKey.has(key)) return lookByKey.get(key)
  // Rest pose: every bone unrotated, so a bone's model position is the sum of offsets.
  const offsets = BONES.map(([, , f]) => f(look))
  const rest = offsets.map((o) => new THREE.Vector3(...o))
  BONES.forEach(([, parent], i) => parent >= 0 && rest[i].add(rest[parent]))

  const parts = []
  const add = (geo, bone, color) => parts.push({ geo, bone: BONE[bone], color })
  const sleeve = look.jacket || look.top
  const skirted = look.cut === 'skirt' || look.cut === 'dress'
  const shins = look.cut === 'shorts' || skirted ? look.legs === look.skin || look.cut === 'shorts' ? look.skin : look.legs : look.bottom
  const thighs = skirted ? look.legs : look.bottom
  add(PARTS.pelvis(), 'pelvis', look.cut === 'dress' ? look.top : look.bottom)
  for (const s of ['L', 'R']) {
    add(PARTS.thigh(), 'hip' + s, thighs)
    add(PARTS.shin(), 'knee' + s, shins)
    add(PARTS.shoe(), 'ankle' + s, look.shoes)
    add(PARTS.upper(), 'shoulder' + s, sleeve)
    add(PARTS.fore(), 'elbow' + s, look.sleeves === 'long' ? sleeve : look.skin)
    add(PARTS.hand(), 'elbow' + s, look.skin)
  }
  add(place(torsoGeo(), [0, 0, 0], 0, [look.width, 1, look.width * 0.74]), 'spine', look.jacket || look.top)
  if (look.jacket) add(PARTS.panel(), 'spine', look.top)
  add(PARTS.head(), 'neck', look.skin)
  add(PARTS.neck(), 'neck', look.skin)
  for (const g of HAIR[look.hair]()) add(g, 'neck', look.hairColor)
  if (look.cut === 'kurta') add(PARTS.tunic(), 'hem', look.top)
  if (look.cut === 'skirt') add(PARTS.skirt(), 'hem', look.bottom)
  if (look.cut === 'dress') add(PARTS.dress(), 'hem', look.top)
  for (const a of look.acc) {
    const color = a === 'beard' ? look.hairColor : a === 'cap' || a === 'sunhat' ? look.hat : look.accent
    const [bone, c, geos] = ACC[a](color)
    for (const g of geos) add(g, bone, c)
  }

  const geos = parts.map(({ geo, bone, color }) => {
    if (!geo.index) throw new Error('characters: person parts must be indexed')
    geo.translate(rest[bone].x, rest[bone].y, rest[bone].z)
    const n = geo.attributes.position.count
    tmpColor.set(color)
    const col = new Float32Array(n * 3)
    const si = new Uint16Array(n * 4)
    const sw = new Float32Array(n * 4)
    for (let i = 0; i < n; i++) {
      col[i * 3] = tmpColor.r
      col[i * 3 + 1] = tmpColor.g
      col[i * 3 + 2] = tmpColor.b
      si[i * 4] = bone
      sw[i * 4] = 1
    }
    geo.setAttribute('color', new THREE.BufferAttribute(col, 3))
    geo.setAttribute('skinIndex', new THREE.Uint16BufferAttribute(si, 4))
    geo.setAttribute('skinWeight', new THREE.BufferAttribute(sw, 4))
    return geo
  })
  const entry = { key, look, offsets, geo: merge(geos, true) }
  lookByKey.set(key, entry)
  looks.push(entry)
  return entry
}

const BOUNDS = new THREE.Sphere(new THREE.Vector3(0, 0.36, 0.05), 0.58)

/**
 * A person: a THREE.Group (the parent owns its position / rotation / scale),
 * feet at y = 0, facing +Z, ~0.68 tall. Everything under userData.body is
 * driven by posePerson().
 * opts.look: a look object to reuse (see userData.look); opts.pose: initial pose.
 */
export function createPerson(opts = {}) {
  const entry = opts.look ? lookEntry(opts.look) : looks.length < MAX_LOOKS ? lookEntry(randomLook()) : pick(looks)
  const root = new THREE.Group()
  const mesh = new THREE.SkinnedMesh(entry.geo, PERSON_MAT)
  mesh.castShadow = true
  mesh.boundingSphere = BOUNDS.clone() // poses stay inside this; skip CPU skinning
  const bones = BONES.map(([name], i) => {
    const b = new THREE.Bone()
    b.name = name
    b.position.fromArray(entry.offsets[i])
    return b
  })
  BONES.forEach(([, parent], i) => parent >= 0 && bones[parent].add(bones[i]))
  mesh.add(bones[0])
  root.add(mesh)
  mesh.bind(new THREE.Skeleton(bones))
  const rig = Object.fromEntries(BONES.map(([name], i) => [name, bones[i]]))
  rig.mesh = mesh
  rig.props = {}
  root.userData.body = bones[0]
  root.userData.rig = rig
  root.userData.look = entry.look
  root.userData.stature = opts.stature ?? rand(0.96, 1.03)
  posePerson(root, opts.pose || 'idle', 0, rand(0, 10))
  return root
}

// ---------- props held by people (made on first use) ----------
function prop(rig, name) {
  if (rig.props[name]) return rig.props[name]
  let m
  if (name === 'cup') {
    m = kit('cup', () => [[mat('#efe9df'), [place(Cyl(0.012, 0.011, 0.028, 10), [0, 0.008, 0])]]])
    m.position.set(0, -FORE - 0.012, 0.022)
    rig.elbowL.add(m)
  } else if (name === 'guitar') {
    m = kit('guitar', () => [
      [mat('#b5793f', { roughness: 0.6 }), [
        place(Cyl(0.05, 0.05, 0.026, 14), [-0.02, 0, 0], [Math.PI / 2, 0, 0]),
        place(Cyl(0.04, 0.04, 0.026, 14), [0.045, 0, 0], [Math.PI / 2, 0, 0]),
      ]],
      [mat('#2b211b'), [
        place(Box(0.14, 0.016, 0.01), [0.15, 0, 0.004]),
        place(Box(0.035, 0.024, 0.01), [0.235, 0, 0.004]),
        place(Cyl(0.015, 0.015, 0.002, 10), [0.02, 0, 0.014], [Math.PI / 2, 0, 0]),
      ]],
    ])
    m.position.set(-0.03, 0.065, 0.075)
    m.rotation.z = 0.38
    rig.spine.add(m)
  }
  m.castShadow = false
  rig.props[name] = m
  return m
}

// ---------- poses ----------
// J is a flat set of joint amounts, all zero at the rest (T-less, arms-down) pose.
// Legs: thigh forward (a), shin forward (b), spread (z). Arms: forward raise (f),
// outward raise (o), twist (t), elbow bend (e). Spine: forward (sf), side (ss),
// twist (st). Neck: nod (nf), turn (nt), tilt (ns). Body: shift (bx, bz), lift (by), turn (bt).
const FIELDS = ['la', 'lb', 'lz', 'ra', 'rb', 'rz', 'sf', 'ss', 'st', 'nf', 'nt', 'ns', 'lf', 'lo', 'lt', 'le', 'rf', 'ro', 'rt', 're', 'bx', 'bz', 'by', 'bt', 'cup', 'guitar']
const ZERO = Object.fromEntries(FIELDS.map((f) => [f, 0]))
const J = { ...ZERO }

function relaxedArms(J) {
  J.lo = J.ro = 0.07
  J.le = J.re = 0.15
  J.lf = J.rf = 0.04
}
// Head turns and a right-hand gesture, for conversation.
function talk(J, t, ph, k = 1) {
  J.nt += Math.sin(t * 0.45 + ph * 1.7) * 0.45 * k
  J.nf += Math.sin(t * 0.8 + ph) * 0.05
  const g = Math.pow(Math.max(0, Math.sin(t * 0.9 + ph * 2.3)), 3) * k
  J.rf += 0.5 * g
  J.re += 0.9 * g + Math.sin(t * 5 + ph) * 0.15 * g
  J.rt += 0.35 * g
  J.ro += 0.1 * g
}
function sitLegs(J, b, ph) {
  const v = frac(ph * 0.37)
  J.la = J.ra = 1.45
  J.lb = b + (v - 0.5) * 0.12
  J.rb = b - (v - 0.5) * 0.12
  J.lz = J.rz = 0.07 + v * 0.06
}
// Arms forward with hands resting at table-top height (~0.3).
function tableArms(J) {
  J.sf = 0.14
  J.lf = J.rf = 0.38
  J.le = J.re = 1.4
  J.lo = J.ro = -0.15
}

const STRETCH = [
  {},
  { lo: 2.85, ro: 2.85, le: 0.2, re: 0.2, nf: -0.2 },
  { lo: 2.85, ro: 2.85, le: 0.15, re: 0.15, ss: 0.38 },
  { lo: 2.85, ro: 2.85, le: 0.15, re: 0.15, ss: -0.38 },
  { lo: 2.85, ro: 2.85, le: 0.2, re: 0.2, nf: -0.2 },
  { sf: 1.2, lf: -0.95, rf: -0.95, lo: 0.05, ro: 0.05, nf: 0.25 },
  {},
  { la: 0.55, lb: -1.35, lz: 0.85, lo: 2.8, ro: 2.8, le: 0.3, re: 0.3 },
  { la: 0.55, lb: -1.35, lz: 0.85, lo: 2.8, ro: 2.8, le: 0.3, re: 0.3 },
].map((k) => ({ ...ZERO, lo: 0.05, ro: 0.05, le: 0.1, re: 0.1, ...k }))

const POSES = {
  idle(J, t, ph) {
    relaxedArms(J)
    const w = Math.sin(t * 0.35 + ph)
    J.bx = w * 0.006
    J.ss = -w * 0.03
    J.lz = J.rz = 0.05
    J.sf = 0.02 + Math.sin(t * 1.3 + ph) * 0.01
    if (frac(ph * 0.731) < 0.55) {
      J.cup = 1
      J.lf = 0.3
      J.le = 1.75
      J.lo = -0.1
    }
    talk(J, t, ph)
  },
  seated(J, t, ph) {
    sitLegs(J, -0.2, ph)
    J.sf = -0.03
    J.lf = J.rf = 0.1
    J.le = J.re = 0.95
    J.lo = J.ro = -0.12
    talk(J, t, ph, 0.6)
  },
  'seated-table'(J, t, ph) {
    sitLegs(J, 0.1, ph)
    tableArms(J)
    talk(J, t, ph)
  },
  'seated-laptop'(J, t, ph) {
    sitLegs(J, 0.1, ph)
    J.sf = 0.12
    J.lf = J.rf = 0.45
    J.le = 1.35 + Math.sin(t * 11 + ph) * 0.05
    J.re = 1.35 + Math.sin(t * 13 + ph + 1) * 0.05
    J.lo = J.ro = -0.18
    J.nf = 0.22
    J.nt = Math.sin(t * 0.2 + ph) * 0.12
  },
  'seated-read'(J, t, ph) {
    sitLegs(J, 0.1, ph)
    tableArms(J)
    J.lo = J.ro = -0.22
    J.nf = 0.38
    J.nt = Math.sin(t * 0.15 + ph) * 0.08
    const turn = Math.pow(Math.max(0, Math.sin(t * 0.3 + ph * 2)), 8)
    J.rt += turn * 0.4
    J.ro += turn * 0.2
  },
  play(J, t, ph) {
    sitLegs(J, -0.05, ph)
    J.guitar = 1
    J.sf = 0.1
    J.rf = 0.45
    J.ro = -0.45
    J.re = 1.1 + Math.sin(t * 9 + ph) * 0.18
    J.lf = 0.7
    J.lo = 0.3
    J.le = 0.9
    J.nf = 0.28 + Math.abs(Math.sin(t * 4 + ph)) * 0.06
    J.nt = 0.15
  },
  ride(J) {
    J.la = J.ra = 1.25
    J.lb = J.rb = 0.35
    J.lz = J.rz = 0.32
    J.sf = 0.25
    J.nf = -0.2
    J.lf = J.rf = 0.9
    J.le = J.re = 0.5
    J.lo = J.ro = 0.12
  },
  walk(J, t, ph) {
    const c = t * 7 + ph
    const sw = Math.sin(c) * 0.36
    J.la = sw
    J.ra = -sw
    J.lb = sw - Math.max(0, Math.cos(c)) * 0.62
    J.rb = -sw - Math.max(0, -Math.cos(c)) * 0.62
    J.lf = -sw * 0.9
    J.rf = sw * 0.9
    J.le = 0.3 + Math.max(0, -sw) * 0.5
    J.re = 0.3 + Math.max(0, sw) * 0.5
    J.lo = J.ro = 0.08
    J.st = sw * 0.12
    J.sf = 0.05
    J.nt = -sw * 0.08
  },
  dance(J, t, ph) {
    const beat = t * 5 + ph
    const k = Math.abs(Math.sin(beat))
    J.la = J.ra = 0.32 * k
    J.lb = J.rb = -0.3 * k
    J.lz = J.rz = 0.12
    J.bt = Math.sin(t * 1.4 + ph) * 0.7
    const style = Math.floor(frac(ph * 0.618) * 3)
    if (style === 0) {
      J.lo = 2.4 + 0.35 * Math.sin(beat)
      J.ro = 2.4 - 0.35 * Math.sin(beat)
      J.le = J.re = 0.35
      J.nf = -0.15 + 0.12 * k
      J.ss = Math.sin(beat * 0.5) * 0.12
    } else if (style === 1) {
      J.lf = 0.5 + 0.35 * Math.sin(beat)
      J.rf = 0.5 - 0.35 * Math.sin(beat)
      J.le = J.re = 1.6
      J.lo = J.ro = 0.2
      J.st = Math.sin(beat * 0.5) * 0.35
      J.bx = Math.sin(beat * 0.5) * 0.02
      J.nf = 0.12 * k
    } else {
      const up = smooth(-0.3, 0.3, Math.sin(t * 1.25 + ph))
      J.ro = 0.3 + 2.2 * up
      J.rf = 0.6 - 0.3 * up
      J.re = 1.2 - 1.1 * up
      J.lo = 0.5
      J.le = 1.8
      J.lf = -0.2
      J.ss = (up - 0.5) * 0.2
      J.nt = (up - 0.5) * 0.5
    }
  },
  stretch(J, t, ph) {
    const u = t * 0.28 + ph * 0.015
    const n = STRETCH.length
    const i = ((Math.floor(u) % n) + n) % n
    const A = STRETCH[i]
    const B = STRETCH[(i + 1) % n]
    const f = smooth(0.6, 1, frac(u))
    for (const k of FIELDS) J[k] = A[k] + (B[k] - A[k]) * f
    J.sf += Math.sin(t * 1.1 + ph) * 0.01
  },
  perform(J, t, ph) {
    const k = Math.abs(Math.sin(t * 2.4))
    J.la = J.ra = 0.06 * k
    J.lb = J.rb = -0.06 * k
    J.lz = J.rz = 0.1
    // Right hand on the mic, left hand working the room.
    J.rf = 0.6
    J.re = 1.9
    J.ro = -0.35
    J.lo = 0.45 + 0.35 * Math.sin(t * 1.3 + ph)
    J.lf = 0.5 + 0.3 * Math.sin(t * 0.9)
    J.le = 0.9 + 0.5 * Math.sin(t * 1.7 + ph)
    J.st = Math.sin(t * 0.8) * 0.12
    J.nf = -0.04
    J.nt = Math.sin(t * 0.6) * 0.3
  },
  sway(J, t, ph) {
    const beat = t * 2.2 + ph
    const k = Math.abs(Math.sin(beat))
    J.la = J.ra = 0.08 * k
    J.lb = J.rb = -0.08 * k
    J.lz = J.rz = 0.06
    J.bx = Math.sin(beat) * 0.012
    J.ss = -Math.sin(beat) * 0.05
    J.nt = Math.sin(t * 0.5 + ph) * 0.25
    const cp = smooth(0.2, 0.5, Math.sin(t * 0.4 + ph))
    J.lf = J.rf = 0.15 + cp * 0.75
    J.le = J.re = 0.2 + cp * 1.2
    J.lo = J.ro = 0.07 - cp * 0.35 + cp * Math.abs(Math.sin(t * 6)) * 0.12
  },
}
/** Seat-top height under a person in the 'ride' pose (scooter/bike rider, feet on pegs at y = 0). */
export const RIDE_H = legH(1.25, 0.35, 0.32) - THIGH_R
const ALIAS = { sit: 'seated', sitting: 'seated', stand: 'idle', standing: 'idle', talk: 'idle', table: 'seated-table', type: 'seated-laptop', laptop: 'seated-laptop', desk: 'seated-laptop', read: 'seated-read', yoga: 'stretch', sing: 'perform', guitar: 'play', clap: 'sway', rider: 'ride' }
/** Every pose posePerson() understands (aliases aside). */
export const POSES_AVAILABLE = Object.keys(POSES)

/**
 * Drive a person's skeleton. The root transform stays the caller's; this resets
 * and sets every joint (and userData.body's scale) each call, so pooled people
 * can switch poses freely. Feet stay on y = 0 in every pose; seated poses rest
 * the thighs on SEAT_H. Unknown poses fall back to 'idle'.
 * Walk: pass time = t * speed so the stride matches the pace.
 */
export function posePerson(person, pose = 'idle', time = 0, phase = 0) {
  const r = person?.userData?.rig
  if (!r) return
  Object.assign(J, ZERO)
  ;(POSES[pose] || POSES[ALIAS[pose]] || POSES.idle)(J, time, phase)

  r.body.position.set(J.bx, 0, J.bz)
  r.body.rotation.set(0, J.bt, 0)
  r.body.scale.setScalar(person.userData.stature || 1)
  r.pelvis.position.y = Math.max(legH(J.la, J.lb, J.lz), legH(J.ra, J.rb, J.rz)) + J.by
  r.hipL.rotation.set(-J.la, 0, J.lz)
  r.kneeL.rotation.set(J.la - J.lb, 0, 0)
  r.ankleL.rotation.set(J.lb, 0, -J.lz)
  r.hipR.rotation.set(-J.ra, 0, -J.rz)
  r.kneeR.rotation.set(J.ra - J.rb, 0, 0)
  r.ankleR.rotation.set(J.rb, 0, J.rz)
  r.spine.rotation.set(J.sf, J.st, J.ss)
  r.neck.rotation.set(J.nf, J.nt, J.ns)
  r.shoulderL.rotation.set(-J.lf, J.lt, J.lo)
  r.shoulderR.rotation.set(-J.rf, -J.rt, -J.ro)
  r.elbowL.rotation.set(-J.le, 0, 0)
  r.elbowR.rotation.set(-J.re, 0, 0)
  r.hem.rotation.set(-Math.max(0, (J.la + J.ra) / 2) * 0.85, 0, 0)

  if (J.cup || r.props.cup) {
    const cup = prop(r, 'cup')
    cup.visible = J.cup > 0
    cup.rotation.x = J.lf + J.le - J.sf
  }
  if (J.guitar || r.props.guitar) prop(r, 'guitar').visible = J.guitar > 0
}

const MUSIC = /jam|rehears|concert|set\b|riyaz|practice room|recording/i
/** The best pose for a layout entry (`lay.at[i]`) in a gathering of `kind` / `use`. */
export function poseFor(a, kind, use = '') {
  if (a.perform) return 'perform'
  if (a.dance) return 'dance'
  if (a.stretch) return 'stretch'
  if (a.seated) {
    if (kind === 'desk') return /read|listening|zine/i.test(use) ? 'seated-read' : 'seated-laptop'
    if (kind === 'table') return 'seated-table'
    if (kind === 'circle' && MUSIC.test(use)) return 'play'
    return 'seated'
  }
  if (kind === 'circle' && MUSIC.test(use)) return 'sway'
  return 'idle'
}

// ---------- furniture ----------
const C = {
  teak: '#7a3f1f',
  darkWood: '#4a2a18',
  steel: '#4a4d4f',
  charcoal: '#2b2b2a',
  ceramic: '#efe9df',
  terracotta: '#b4643f',
  paper: '#efe8d8',
  leaf: '#4d6b35',
}
const glow = (color, emissive, emissiveIntensity) => mat(color, { emissive, emissiveIntensity, roughness: 0.6 })

const chair = (color = C.teak) => kit('chair|' + color, () => [[mat(color), [
  place(Box(0.16, 0.018, 0.16), [0, SEAT_H - 0.009, -0.02]),
  ...[-1, 1].map((s) => place(Box(0.014, SEAT_H - 0.018, 0.014), [s * 0.068, (SEAT_H - 0.018) / 2, 0.05])),
  ...[-1, 1].map((s) => place(Box(0.014, 0.35, 0.014), [s * 0.068, 0.175, -0.093])),
  place(Box(0.15, 0.05, 0.012), [0, 0.315, -0.093]),
  place(Box(0.15, 0.025, 0.012), [0, 0.24, -0.093]),
]]], { cast: true })
const taskChair = () => kit('task', () => [
  [mat('#2f3a44', { roughness: 0.95 }), [
    place(Box(0.15, 0.025, 0.15), [0, SEAT_H - 0.0125, -0.015]),
    place(Box(0.14, 0.12, 0.022), [0, 0.29, -0.095], [-0.08, 0, 0]),
  ]],
  [mat(C.steel, { roughness: 0.5 }), [
    place(Cyl(0.008, 0.008, SEAT_H - 0.04), [0, (SEAT_H - 0.04) / 2 + 0.015, -0.015]),
    place(Box(0.012, 0.11, 0.01), [0, 0.2, -0.09]),
    ...[0, 1, 2, 3, 4].map((i) => place(Box(0.1, 0.01, 0.012), [0.045, 0.012, 0], [0, 0, 0]).rotateY((i / 5) * Math.PI * 2).translate(0, 0, -0.015)),
  ]],
], { cast: true })
const pouf = (color) => kit('pouf|' + color, () => [[mat(color, { roughness: 1 }), [place(Cyl(0.068, 0.072, SEAT_H, 14), [0, SEAT_H / 2, -0.015])]]], { cast: true })

const roundTable = () => kit('round', () => [[mat(C.teak), [
  place(Cyl(0.22, 0.22, 0.022, 28), [0, 0.289, 0]),
  place(Cyl(0.022, 0.03, 0.27, 10), [0, 0.144, 0]),
  place(Cyl(0.09, 0.1, 0.018, 18), [0, 0.009, 0]),
]]], { cast: true })
function rectTable(w, h, d, desk) {
  const key = ['table', w.toFixed(3), h.toFixed(3), d.toFixed(3), desk].join('|')
  return kit(key, () => {
    const legs = []
    const lz = d > 1 ? [-1, 0, 1] : [-1, 1]
    for (const sx of [-1, 1]) for (const sz of lz) legs.push(place(Box(0.02, h - 0.022, 0.02), [sx * (w / 2 - 0.03), (h - 0.022) / 2, sz * (d / 2 - 0.03)]))
    const top = place(Box(w, 0.022, d), [0, h - 0.011, 0])
    return desk ? [[mat(C.teak), [top]], [mat(C.steel, { roughness: 0.5 }), legs]] : [[mat(C.teak), [top, ...legs]]]
  }, { cast: true })
}
function platform(w, h, d) {
  return kit(['stage', w, h, d].join('|'), () => [
    [mat(C.darkWood), [place(Box(w, h - 0.006, d), [0, (h - 0.006) / 2, 0])]],
    [mat('#8c6e55'), [place(Box(w - 0.01, 0.006, d - 0.01), [0, h - 0.003, 0])]],
  ], { cast: true })
}
const micStand = () => kit('mic', () => [
  [mat(C.steel, { roughness: 0.4, metalness: 0.4 }), [place(Cyl(0.03, 0.03, 0.006, 12), [0, 0.003, 0]), place(Cyl(0.004, 0.004, 0.52, 6), [0, 0.26, 0])]],
  [mat('#1d1d1c'), [place(Cap(0.009, 0.022, 3, 8), [0, 0.535, -0.006], [-0.5, 0, 0])]],
])
const speaker = () => kit('speaker', () => [
  [mat('#232323'), [place(Box(0.08, 0.13, 0.06), [0, 0.065, 0])]],
  [mat('#4a4d4f'), [place(Cyl(0.024, 0.024, 0.004, 12), [0, 0.072, 0.031], [Math.PI / 2, 0, 0]), place(Cyl(0.012, 0.012, 0.004, 10), [0, 0.112, 0.031], [Math.PI / 2, 0, 0])]],
], { cast: true })
const BAR_H = 0.4
const barTable = () => kit('bar', () => [
  [mat(C.steel, { roughness: 0.5 }), [place(Cyl(0.055, 0.06, 0.01, 14), [0, 0.005, 0]), place(Cyl(0.01, 0.01, BAR_H - 0.02, 8), [0, BAR_H / 2, 0])]],
  [mat(C.teak), [place(Cyl(0.075, 0.075, 0.014, 18), [0, BAR_H - 0.007, 0])]],
], { cast: true })
const LOW_H = 0.11
const lowTable = () => kit('low', () => [[mat(C.teak), [place(Cyl(0.13, 0.13, 0.018, 22), [0, LOW_H - 0.009, 0]), place(Cyl(0.1, 0.1, LOW_H - 0.018, 18), [0, (LOW_H - 0.018) / 2, 0])]]], { cast: true })
const rug = (color) => kit('rug|' + color, () => [[mat(color, { roughness: 1 }), [place(Cyl(0.74, 0.74, 0.005, 36), [0, 0.0025, 0])]]])
const yogaMat = (color) => kit('yoga|' + color, () => [[mat(color, { roughness: 1 }), [place(Box(0.2, 0.006, 0.38), [0, 0.003, 0])]]])

// Things on tables: origin on the table top, user at local −Z.
const ITEMS = {
  laptop: (v = 'silver') => kit('laptop|' + v, () => {
    const hinge = (g) => g.rotateX(0.28).translate(0, 0.006, 0.0405)
    return [
      [mat(v === 'silver' ? '#b9bcbf' : '#3a3d42', { roughness: 0.45, metalness: 0.3 }), [place(Box(0.12, 0.006, 0.085), [0, 0.003, 0]), hinge(place(Box(0.12, 0.082, 0.004), [0, 0.041, 0.002]))]],
      [glow('#1b2430', '#a9c8ff', 0.35), [hinge(place(Box(0.108, 0.07, 0.001), [0, 0.043, -0.0005]))]],
    ]
  }),
  mug: (c = C.ceramic) => kit('mug|' + c, () => [
    [mat(c, { roughness: 0.5 }), [place(Cyl(0.016, 0.015, 0.036, 12), [0, 0.018, 0]), place(new THREE.TorusGeometry(0.01, 0.0035, 5, 8), [0.018, 0.019, 0])]],
    [mat('#3b2416'), [place(Cyl(0.0138, 0.0138, 0.002, 10), [0, 0.0345, 0])]],
  ]),
  notebook: (c = '#c9b48f') => kit('notebook|' + c, () => [
    [mat(c), [place(Box(0.06, 0.004, 0.084), [0, 0.002, 0])]],
    [mat(C.paper), [place(Box(0.056, 0.004, 0.08), [0.001, 0.005, 0])]],
  ]),
  plate: () => kit('plate', () => [
    [mat('#f4f1ea', { roughness: 0.4 }), [place(Cyl(0.04, 0.032, 0.006, 16), [0, 0.003, 0])]],
    [mat('#b8743a'), [place(Sph(0.02, 8, 5), [0, 0.007, 0], 0, [1, 0.35, 1])]],
  ]),
  glass: () => kit('glass', () => [[mat('#cfdcd8', { roughness: 0.1 }), [place(Cyl(0.011, 0.009, 0.032, 10), [0, 0.016, 0])]]]),
  candle: () => kit('candle', () => [
    [mat('#c9a35a', { roughness: 0.4, metalness: 0.5 }), [place(Cyl(0.016, 0.018, 0.006, 10), [0, 0.003, 0])]],
    [mat('#f3e6cc'), [place(Cyl(0.008, 0.008, 0.045, 8), [0, 0.0285, 0])]],
    [glow('#ffd08a', '#ff9a3c', 0.9), [place(Sph(0.006, 6, 5), [0, 0.057, 0], 0, [1, 1.6, 1])]],
  ]),
  bottle: () => kit('bottle', () => [[mat('#2e4a2c', { roughness: 0.3 }), [place(Cyl(0.013, 0.013, 0.05, 10), [0, 0.025, 0]), place(Cyl(0.005, 0.013, 0.02, 10), [0, 0.06, 0]), place(Cyl(0.005, 0.005, 0.016, 8), [0, 0.078, 0])]]]),
  bowl: () => kit('bowl', () => [
    [mat(C.terracotta), [place(Cyl(0.035, 0.022, 0.022, 14), [0, 0.011, 0])]],
    [mat('#d9902f'), [-1, 0, 1].map((i) => place(Sph(0.012, 8, 6), [i * 0.016, 0.026, i === 0 ? 0.01 : -0.006]))],
  ]),
  vase: () => kit('vase', () => [
    [mat(C.terracotta), [place(Cyl(0.012, 0.009, 0.045, 10), [0, 0.0225, 0])]],
    [mat(C.leaf), [place(Sph(0.016, 8, 6), [0, 0.055, 0])]],
    [mat('#e0531f'), [place(Sph(0.009, 6, 5), [0.008, 0.066, 0.004]), place(Sph(0.008, 6, 5), [-0.008, 0.062, -0.004])]],
  ]),
  books: () => kit('books', () => [
    [mat('#3d4f6b'), [place(Box(0.075, 0.012, 0.1), [0, 0.006, 0])]],
    [mat('#a34a3a'), [place(Box(0.07, 0.011, 0.095), [0, 0.0175, 0], [0, 0.2, 0])]],
    [mat('#c9b48f'), [place(Box(0.068, 0.01, 0.092), [0, 0.028, 0], [0, -0.15, 0])]],
  ]),
  openBook: () => kit('openbook', () => [
    [mat('#6d2f4a'), [place(Box(0.096, 0.003, 0.068), [0, 0.0015, 0])]],
    [mat(C.paper), [place(Box(0.046, 0.005, 0.064), [-0.023, 0.006, 0], [0, 0, 0.1]), place(Box(0.046, 0.005, 0.064), [0.023, 0.006, 0], [0, 0, -0.1])]],
  ]),
  lamp: () => kit('lamp', () => [
    [mat(C.steel, { roughness: 0.5 }), [place(Cyl(0.022, 0.025, 0.006, 12), [0, 0.003, 0]), place(Cyl(0.003, 0.003, 0.11, 6), [0, 0.058, 0])]],
    [glow('#e7dcc8', '#ffcf8a', 0.45), [place(Cyl(0.018, 0.032, 0.035, 12), [0, 0.12, 0])]],
  ]),
  plant: () => kit('plant', () => [
    [mat(C.terracotta), [place(Cyl(0.022, 0.017, 0.035, 10), [0, 0.0175, 0])]],
    [mat(C.leaf), [place(Sph(0.03, 8, 6), [0, 0.06, 0], 0, [0.9, 1.1, 0.9])]],
  ]),
  jar: () => kit('jar', () => [
    [mat('#8a8f94', { roughness: 0.3 }), [place(Cyl(0.014, 0.014, 0.03, 10), [0, 0.015, 0])]],
    [mat('#c47b2b'), [-1, 0, 1].map((i) => place(Box(0.004, 0.045, 0.004), [i * 0.005, 0.035, i * 0.003], [i * 0.12, 0, i * 0.15]))],
  ]),
  clay: () => kit('clay', () => [[mat('#a8704a', { roughness: 1 }), [place(Sph(0.024, 10, 8), [0, 0.012, 0], 0, [1, 0.75, 1]), place(Sph(0.012, 8, 6), [0.03, 0.007, 0.012])]]]),
  chess: () => kit('chess', () => {
    const light = []
    for (let i = 0; i < 8; i++) for (let j = 0; j < 8; j++) if ((i + j) % 2) light.push(place(Box(0.0155, 0.002, 0.0155), [(i - 3.5) * 0.016, 0.009, (j - 3.5) * 0.016]))
    return [[mat('#2b211b'), [place(Box(0.134, 0.008, 0.134), [0, 0.004, 0])]], [mat('#e7dcc8'), light]]
  }),
  carrom: () => kit('carrom', () => [
    [mat('#e3cc9a', { roughness: 0.5 }), [place(Box(0.19, 0.012, 0.19), [0, 0.006, 0])]],
    [mat('#5a3520'), [
      ...[-1, 1].map((s) => place(Box(0.21, 0.018, 0.012), [0, 0.009, s * 0.099])),
      ...[-1, 1].map((s) => place(Box(0.012, 0.018, 0.186), [s * 0.099, 0.009, 0])),
      ...[[-1, -1], [-1, 1], [1, -1], [1, 1]].map(([x, z]) => place(Cyl(0.008, 0.008, 0.002, 8), [x * 0.083, 0.0125, z * 0.083])),
    ]],
  ]),
  board: () => kit('board', () => [
    [mat('#c9a46a'), [place(Box(0.14, 0.006, 0.14), [0, 0.003, 0])]],
    [mat('#a34a3a'), [[-1, -1], [1, 1], [-1, 1]].map(([x, z]) => place(new THREE.ConeGeometry(0.006, 0.018, 6), [x * 0.04, 0.015, z * 0.04]))],
  ]),
  cards: () => kit('cards', () => [
    [mat('#a34a3a'), [place(Cyl(0.01, 0.01, 0.014, 10), [0.03, 0.007, 0.01]), place(Cyl(0.01, 0.01, 0.008, 10), [0.034, 0.004, -0.014])]],
    [mat('#f4f1ea'), [place(Box(0.025, 0.0015, 0.035), [-0.008, 0.001, 0], [0, 0.25, 0]), place(Box(0.025, 0.0015, 0.035), [-0.002, 0.0025, 0.004], [0, -0.15, 0])]],
  ]),
}
const MUGS = [C.ceramic, C.ceramic, C.terracotta, '#6b7f8e', '#2f3a44']
const NOTES = ['#c9b48f', '#1d1d1c', '#a34a3a', '#3d4f6b']
const MATS = ['#7d8f6a', '#b4643f', '#3d4f6b', '#6d2f4a', '#c9b48f', '#5a7a74']
const RUGS = ['#8a4a2f', '#a9875a', '#6b3a2c', '#3d4f6b']
const POUFS = ['#b4643f', '#c9b48f', '#6b7f8e', '#7a3f1f', '#3f5a2c', '#d9d3c7']

const THEMES = [
  [/dinner|supper/i, 'dinner'],
  [/chess|poker|carrom|board|game/i, 'game'],
  [/read|library|listening/i, 'read'],
  [/studio|print|clay|sketch|drawing|paint|zine/i, 'art'],
  [/café|cafe|breakfast|coffee/i, 'cafe'],
  [/laptop|work|office|heads|build|hiring|team|demo|pitch/i, 'work'],
]
const themeOf = (kind, use) => THEMES.find(([re]) => re.test(use))?.[1] || (kind === 'desk' ? 'work' : 'cafe')

// First table top in front of a seat: { t: distance to its edge, h: top height }.
function surfaceAhead(a, surfaces) {
  const fx = Math.sin(a.face)
  const fz = Math.cos(a.face)
  let best = null
  for (const s of surfaces) {
    let t
    if (s.r) {
      const ox = a.x - s.x
      const oz = a.z - s.z
      const b = ox * fx + oz * fz
      const disc = b * b - (ox * ox + oz * oz - s.r * s.r)
      if (disc < 0) continue
      t = -b - Math.sqrt(disc)
    } else {
      let t0 = -Infinity
      let t1 = Infinity
      for (const [o, f, c, half] of [[a.x, fx, s.x, s.w / 2], [a.z, fz, s.z, s.d / 2]]) {
        if (Math.abs(f) < 1e-6) {
          if (Math.abs(o - c) > half) t0 = Infinity
          continue
        }
        const ta = (c - half - o) / f
        const tb = (c + half - o) / f
        t0 = Math.max(t0, Math.min(ta, tb))
        t1 = Math.min(t1, Math.max(ta, tb))
      }
      if (t0 > t1) continue
      t = t0
    }
    if (t >= 0 && t < 0.45 && (!best || t < best.t)) best = { t, h: s.h }
  }
  return best
}

function setting(theme, use, a, hit, i) {
  const g = new THREE.Group()
  const inset = theme === 'game' ? 0.03 : 0.06
  const d = hit.t + inset
  g.position.set(a.x + Math.sin(a.face) * d, (a.y || 0) + hit.h, a.z + Math.cos(a.face) * d)
  g.rotation.y = a.face
  const put = (m, x = 0, z = 0, ry = 0) => {
    m.position.set(x, 0, z)
    m.rotation.y = ry
    g.add(m)
    return m
  }
  const side = i % 2 ? 1 : -1
  if (theme === 'work') {
    put(ITEMS.laptop(i % 3 === 1 ? 'dark' : 'silver'), 0, 0.004, rand(-0.08, 0.08))
    put(ITEMS.mug(pick(MUGS)), side * 0.085, -0.015, rand(0, 6))
  } else if (theme === 'dinner') {
    put(ITEMS.plate(), 0, -0.01)
    put(ITEMS.glass(), 0.05, 0.035)
  } else if (theme === 'game') {
    if (/poker/i.test(use)) put(ITEMS.cards(), 0, 0, rand(-0.3, 0.3))
    put(chance(0.5) ? ITEMS.glass() : ITEMS.mug(pick(MUGS)), side * 0.07, -0.02, rand(0, 6))
  } else if (theme === 'art') {
    if (/clay/i.test(use)) put(ITEMS.clay(), 0, 0, rand(0, 6))
    else put(ITEMS.notebook(C.paper), 0, 0, rand(-0.25, 0.25))
    if (i % 2 === 0) put(ITEMS.jar(), 0.07, 0.02)
  } else if (theme === 'read') {
    put(ITEMS.openBook(), 0, -0.005, rand(-0.15, 0.15))
    if (i % 2) put(ITEMS.mug(pick(MUGS)), side * 0.08, -0.01, rand(0, 6))
  } else {
    put(ITEMS.mug(pick(MUGS)), 0.02, -0.012, rand(0, 6))
    if (i % 3 === 0) put(ITEMS.notebook(pick(NOTES)), -0.055, 0.005, rand(-0.3, 0.3))
    else if (i % 3 === 1) put(ITEMS.plate(), -0.05, 0.01).scale.setScalar(0.7)
  }
  return g
}

// Things down the middle of a table top.
function centre(theme, use, s, i) {
  const g = new THREE.Group()
  g.position.set(s.x, s.h, s.z)
  const put = (m, x = 0, z = 0) => (m.position.set(x, 0, z), g.add(m), m)
  if (theme === 'dinner') {
    put(i % 2 ? ITEMS.bottle() : ITEMS.candle(), 0.03, 0)
    put(i % 2 ? ITEMS.candle() : ITEMS.bowl(), -0.03, 0.01)
  } else if (theme === 'game') {
    const m = put(/chess/i.test(use) ? ITEMS.chess() : /carrom/i.test(use) ? ITEMS.carrom() : /poker/i.test(use) ? ITEMS.cards() : ITEMS.board())
    m.rotation.y = rand(-0.3, 0.3)
  } else if (theme === 'read') put(ITEMS.books())
  else if (theme === 'art') put(ITEMS.jar())
  else if (theme === 'work') put(ITEMS.plant())
  else put(ITEMS.vase())
  return g
}

/**
 * Furniture for a gathering, built from the world's layout object
 * ({ round?, furniture?: [[w, h, d, x?, z?]], at: [{ x, y?, z, face, seated?, ... }] }).
 * Returns a THREE.Group at the gathering's origin; group.userData.pieces lists
 * its top-level pieces (each grounded at its own origin) for staggered growth.
 * `use` (optional, e.g. 'Long dinner') picks what goes on the tables.
 */
export function createFurnishings(kind, layout = {}, use = '') {
  const group = new THREE.Group()
  const pieces = []
  const add = (o, x = 0, y = 0, z = 0, ry = 0) => {
    o.position.set(x, y, z)
    o.rotation.y = ry
    group.add(o)
    pieces.push(o)
    return o
  }
  const at = layout.at || []
  const theme = themeOf(kind, use)
  const surfaces = []
  if (layout.round) {
    surfaces.push({ x: 0, z: 0, r: 0.22, h: 0.3 })
    add(roundTable())
  }
  for (const [w, h, d, x = 0, z = 0] of layout.furniture || []) {
    if (h < 0.15) {
      add(platform(w, h, d), x, 0, z)
      continue
    }
    surfaces.push({ x, z, w, d, h })
    add(rectTable(w, h, d, kind === 'desk'), x, 0, z)
  }

  if (kind === 'talk' && at.length >= 3 && !/arriv/i.test(use)) {
    surfaces.push({ x: 0, z: 0, r: 0.075, h: BAR_H })
    add(barTable())
    for (const [x, z] of [[0.025, 0.02], [-0.03, -0.01]]) add(ITEMS.glass(), x, BAR_H, z)
  }
  if (kind === 'circle') {
    add(rug(pick(RUGS)))
    add(lowTable())
    const top = new THREE.Group()
    top.add(ITEMS.candle())
    const mug = ITEMS.mug(pick(MUGS))
    mug.position.set(0.06, 0, 0.03)
    top.add(mug)
    if (!MUSIC.test(use)) {
      const nb = ITEMS.notebook(pick(NOTES))
      nb.position.set(-0.06, 0, -0.02)
      nb.rotation.y = 0.4
      top.add(nb)
    }
    add(top, 0, LOW_H)
  }
  if (kind === 'row') for (const a of at) add(yogaMat(pick(MATS)), a.x, a.y || 0, a.z, a.face)
  if (kind === 'stage') {
    const p = at.find((a) => a.perform)
    const [w = 0.5, h = 0.08, d = 1, x = 0, z = -0.75] = layout.furniture?.[0] || []
    if (p) {
      const fx = Math.sin(p.face)
      const fz = Math.cos(p.face)
      add(micStand(), p.x + fx * 0.12, p.y ?? h, p.z + fz * 0.12, p.face)
      const bz = z - Math.sign(fz || 1) * (d / 2 - 0.05)
      for (const s of [-1, 1]) add(speaker(), x + s * (w / 2 - 0.06), h, bz, p.face + s * 0.25)
    }
  }

  // Seats, then what's in front of each.
  const seat = kind === 'circle' ? () => pouf(pick(POUFS)) : kind === 'desk' ? () => taskChair() : kind === 'stage' ? () => chair(C.charcoal) : () => chair()
  at.forEach((a, i) => {
    if (!a.seated) return
    add(seat(), a.x, a.y || 0, a.z, a.face)
    const hit = surfaceAhead(a, surfaces)
    if (hit && hit.h < BAR_H) add(setting(theme, use, a, hit, i))
  })

  // Down the middle of tables.
  surfaces.forEach((s, si) => {
    if (s.h >= BAR_H) return
    if (s.r) return add(centre(theme, use, s, si))
    if (kind === 'desk') {
      // Lamps or plants along the far edge.
      const n = Math.max(1, Math.round(s.d / 0.64))
      for (let k = 0; k < n; k++) {
        const m = theme === 'read' ? ITEMS.lamp() : ITEMS.plant()
        add(m, s.x + s.w / 2 - 0.05, s.h, s.z + (k - (n - 1) / 2) * (s.d / n))
      }
      return
    }
    const long = s.d >= s.w
    const len = long ? s.d : s.w
    const n = Math.max(1, Math.round(len / (theme === 'game' ? 0.68 : 0.4)))
    for (let k = 0; k < n; k++) {
      const off = (k - (n - 1) / 2) * (len / n)
      add(centre(theme, use, { ...s, x: s.x + (long ? 0 : off), z: s.z + (long ? off : 0) }, k))
    }
  })

  group.userData.pieces = pieces
  return group
}
