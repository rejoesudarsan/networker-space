// Builds the house as 3D models from plans/plans-AS-BUILT.dwg (needs
// libredwg's dwg2dxf) and writes public/models/<floor>.glb plus
// public/models/house.json (footprints, offsets, room labels).
//
// The DWG draws walls as pairs of parallel lines. Each pair becomes a solid
// strip, strips and columns are unioned into clean outlines, and those are
// extruded. Floors are aligned on the structural columns so they stack.
import { execFileSync } from 'node:child_process'
import { mkdtempSync, readFileSync, writeFileSync, mkdirSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import DxfParser from 'dxf-parser'
import polygonClipping from 'polygon-clipping'
import * as THREE from 'three'
import { GLTFExporter } from 'three/examples/jsm/exporters/GLTFExporter.js'
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js'

const DWG = new URL('../../plans/plans-AS-BUILT.dwg', import.meta.url).pathname
const OUT = new URL('../public/models/', import.meta.url).pathname

// Drawing units are inches. One world unit = 8 ft, so a floor is ~10 units deep.
const UNIT = 96
const WALL_H = 54 // cutaway wall height, so rooms stay visible from above
const SILL_H = 22 // window walls stop at the sill
const SLAB = 14
const COLUMN_H = WALL_H + 6

// Where each floor sits in the drawing (x0, x1); all share y 2150–3150.
const FLOORS = {
  basement: [26200, 26760],
  ground: [26880, 27600],
  first: [27700, 28420],
  second: [28500, 29010],
}
const Y_RANGE = [2150, 3160]
const DETAIL_LAYERS = ['stair', 'door', 'FURN']

// ---------- read the drawing ----------
const dir = mkdtempSync(join(process.env.TMPDIR || tmpdir(), 'house-'))
const dxfPath = join(dir, 'plans.dxf')
execFileSync('dwg2dxf', ['-y', '-o', dxfPath, DWG], { stdio: 'ignore' })
const dxf = new DxfParser().parseSync(readFileSync(dxfPath, 'utf8'))

// Every entity as line segments: [[x0, y0], [x1, y1]].
function segments(e) {
  const out = []
  if (e.type === 'LINE' || e.type === 'LWPOLYLINE' || e.type === 'POLYLINE') {
    const v = e.vertices
    for (let i = 0; i < v.length - 1; i++) out.push([[v[i].x, v[i].y], [v[i + 1].x, v[i + 1].y]])
    if (e.shape && v.length > 2) out.push([[v.at(-1).x, v.at(-1).y], [v[0].x, v[0].y]])
  } else if (e.type === 'ARC' || e.type === 'CIRCLE') {
    let a0 = e.startAngle ?? 0
    let a1 = e.endAngle ?? Math.PI * 2
    if (a1 <= a0) a1 += Math.PI * 2
    const n = Math.max(4, Math.ceil((a1 - a0) / 0.2))
    for (let i = 0; i < n; i++) {
      const p = (k) => [e.center.x + e.radius * Math.cos(a0 + ((a1 - a0) * k) / n), e.center.y + e.radius * Math.sin(a0 + ((a1 - a0) * k) / n)]
      out.push([p(i), p(i + 1)])
    }
  }
  return out
}
const inside = ([x0, x1], [x, y]) => x >= x0 && x <= x1 && y >= Y_RANGE[0] && y <= Y_RANGE[1]
const layer = (range, name) =>
  dxf.entities.filter((e) => e.layer === name).flatMap(segments).filter((s) => inside(range, s[0]) && inside(range, s[1]))

// ---------- walls: pair parallel lines into strips ----------
// Snapping to a quarter inch keeps the polygon union numerically stable.
const snap = (v) => Math.round(v * 4) / 4
function pairStrips(segs, minGap = 2.5, maxGap = 12) {
  const strips = []
  const info = segs.map(([a, b]) => {
    const dx = b[0] - a[0]
    const dy = b[1] - a[1]
    const len = Math.hypot(dx, dy)
    return { a, b, len, u: [dx / len, dy / len] }
  }).filter((s) => s.len > 1)
  for (let i = 0; i < info.length; i++) {
    for (let j = i + 1; j < info.length; j++) {
      const s = info[i]
      const t = info[j]
      if (Math.abs(s.u[0] * t.u[1] - s.u[1] * t.u[0]) > 0.02) continue // not parallel
      const n = [-s.u[1], s.u[0]]
      const gap = (t.a[0] - s.a[0]) * n[0] + (t.a[1] - s.a[1]) * n[1]
      if (Math.abs(gap) < minGap || Math.abs(gap) > maxGap) continue
      // Overlap of t's projection onto s.
      const proj = (p) => (p[0] - s.a[0]) * s.u[0] + (p[1] - s.a[1]) * s.u[1]
      const t0 = Math.min(proj(t.a), proj(t.b))
      const t1 = Math.max(proj(t.a), proj(t.b))
      const lo = Math.max(0, t0)
      const hi = Math.min(s.len, t1)
      if (hi - lo < 2) continue
      const at = (k, g) => [snap(s.a[0] + s.u[0] * k + n[0] * g), snap(s.a[1] + s.u[1] * k + n[1] * g)]
      strips.push([[at(lo, 0), at(hi, 0), at(hi, gap), at(lo, gap), at(lo, 0)]])
    }
  }
  return strips
}

const centroid = (ring) => {
  const pts = ring.slice(0, -1)
  return [pts.reduce((s, p) => s + p[0], 0) / pts.length, pts.reduce((s, p) => s + p[1], 0) / pts.length]
}

function columns(range) {
  return dxf.entities
    .filter((e) => e.layer === 'col' && e.type === 'LWPOLYLINE' && e.vertices.length >= 3)
    .map((e) => {
      const ring = e.vertices.map((v) => [snap(v.x), snap(v.y)])
      ring.push(ring[0])
      return [ring]
    })
    .filter((p) => inside(range, centroid(p[0])))
}

// ---------- align floors on the column grid ----------
function alignTo(ref, cols) {
  let best = { dx: 0, dy: 0, score: -1 }
  for (const r of ref) {
    for (const c of cols) {
      const dx = r[0] - c[0]
      const dy = r[1] - c[1]
      let score = 0
      for (const q of cols) if (ref.some((p) => Math.hypot(p[0] - q[0] - dx, p[1] - q[1] - dy) < 3)) score++
      if (score > best.score) best = { dx, dy, score }
    }
  }
  return best
}

// ---------- geometry ----------
const toShapes = (multi) =>
  multi.map(([outer, ...holes]) => {
    const shape = new THREE.Shape(outer.slice(0, -1).map(([x, y]) => new THREE.Vector2(x, y)))
    shape.holes = holes.map((h) => new THREE.Path(h.slice(0, -1).map(([x, y]) => new THREE.Vector2(x, y))))
    return shape
  })

// Extrude plan polygons (drawing x/y) up to `height`, then convert to world
// space: x → x, drawing y → -z, inches → units, centred on `origin`.
function extrude(multi, base, height, origin) {
  const geo = new THREE.ExtrudeGeometry(toShapes(multi), { depth: height, bevelEnabled: false, curveSegments: 1 })
  geo.rotateX(-Math.PI / 2) // extrude along +y; drawing y becomes -z
  geo.translate(-origin[0], base, origin[1])
  geo.scale(1 / UNIT, 1 / UNIT, 1 / UNIT)
  return geo
}

function lineGeometry(segs, y, origin) {
  const pos = []
  for (const [a, b] of segs) pos.push(a[0] - origin[0], y, -(a[1] - origin[1]), b[0] - origin[0], y, -(b[1] - origin[1]))
  const geo = new THREE.BufferGeometry()
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos.map((v) => v / UNIT), 3))
  return geo
}

const mat = (name) => new THREE.MeshBasicMaterial({ name })
const bounds = (multi) => {
  const pts = multi.flat(2)
  return [Math.min(...pts.map((p) => p[0])), Math.min(...pts.map((p) => p[1])), Math.max(...pts.map((p) => p[0])), Math.max(...pts.map((p) => p[1]))]
}

// GLTFExporter needs FileReader, which Node lacks.
globalThis.FileReader ??= class {
  readAsArrayBuffer(blob) {
    blob.arrayBuffer().then((r) => ((this.result = r), this.onloadend?.()))
  }
  readAsDataURL(blob) {
    blob.arrayBuffer().then((r) => {
      this.result = `data:${blob.type || 'application/octet-stream'};base64,${Buffer.from(r).toString('base64')}`
      this.onloadend?.()
    })
  }
}

// ---------- build ----------
mkdirSync(OUT, { recursive: true })
const ref = columns(FLOORS.ground).map((p) => centroid(p[0]))
const manifest = { unit: UNIT, slab: SLAB / UNIT, wallHeight: WALL_H / UNIT, floors: {} }

for (const [id, range] of Object.entries(FLOORS)) {
  const cols = columns(range)
  const { dx, dy, score } = id === 'ground' ? { dx: 0, dy: 0, score: cols.length } : alignTo(ref, cols.map((p) => centroid(p[0])))
  console.log(`${id}: ${cols.length} columns, ${score} on the ground grid, offset ${dx.toFixed(1)}, ${dy.toFixed(1)}`)

  const walls = polygonClipping.union(...pairStrips(layer(range, 'WALL')), ...cols)
  const sills = polygonClipping.difference(polygonClipping.union(...pairStrips(layer(range, 'window'), 2, 14)), walls)
  const site = layer(range, 'SITE')
  const [x0, y0, x1, y1] = bounds([...walls, [[...site.flat()]]])
  // The slab: the floor's extent, plus a lip under the outer walls.
  const footprint = [[[[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]]]]
  const origin = [(x0 + x1) / 2, (y0 + y1) / 2]

  const group = new THREE.Group()
  group.name = id
  const add = (name, geo, material, Type = THREE.Mesh) => {
    const m = new Type(geo, material)
    m.name = name
    group.add(m)
  }
  add('slab', extrude(footprint, -SLAB, SLAB, origin), mat('slab'))
  add('walls', extrude(walls, 0, WALL_H, origin), mat('wall'))
  if (sills.length) add('sills', extrude(sills, 0, SILL_H, origin), mat('sill'))
  add('columns', extrude(cols, 0, COLUMN_H, origin), mat('column'))
  const details = DETAIL_LAYERS.flatMap((l) => layer(range, l))
  add('details', lineGeometry(details, 0.6, origin), new THREE.LineBasicMaterial({ name: 'detail' }), THREE.LineSegments)

  const glb = await new GLTFExporter().parseAsync(group, { binary: true })
  writeFileSync(join(OUT, `${id}.glb`), Buffer.from(glb))

  // Room labels in model space (x, z), for reference when placing rooms.
  const labels = dxf.entities
    .filter((e) => e.layer === 'TEXT' && e.type === 'TEXT' && /[A-Z]{3}/.test(e.text) && inside(range, [e.startPoint.x, e.startPoint.y]))
    .map((e) => ({ text: e.text.trim(), x: +((e.startPoint.x - origin[0]) / UNIT).toFixed(2), z: +(-(e.startPoint.y - origin[1]) / UNIT).toFixed(2) }))
  manifest.floors[id] = {
    width: +((x1 - x0) / UNIT).toFixed(3),
    depth: +((y1 - y0) / UNIT).toFixed(3),
    // Centre of this floor in the shared building frame (ground floor = 0, 0).
    offset: [(origin[0] + dx) / UNIT, (origin[1] + dy) / UNIT],
    labels,
  }
  console.log(`  ${(glb.byteLength / 1024).toFixed(0)} KB, ${walls.length} wall outlines, ${details.length} detail lines`)
}

// Offsets relative to the ground floor's centre: x right, z towards the viewer.
const g = manifest.floors.ground.offset
for (const f of Object.values(manifest.floors)) f.offset = [+(f.offset[0] - g[0]).toFixed(3), +(-(f.offset[1] - g[1])).toFixed(3)]
writeFileSync(join(OUT, 'house.json'), JSON.stringify(manifest, null, 2) + '\n')
