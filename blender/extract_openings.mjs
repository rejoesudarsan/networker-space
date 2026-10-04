// Extracts door and window openings from plans/plans-AS-BUILT.dwg into
// blender/data/openings.json, in the same floor-local units and origin as
// site/public/models/<floor>.glb (see site/scripts/build-house.mjs, whose
// DXF reading, wall pairing and origin logic are copied here unchanged).
//
// Run from anywhere (needs libredwg's dwg2dxf and site/node_modules):
//   node /Users/rejoesudarsan/Dev/networker-space/blender/extract_openings.mjs
//
// Output per floor, floor-local Three.js units (x right, z toward the street):
//   doors:   [{ x0, z0, x1, z1, width_ft, source }]  wall-thickness rectangles over each door gap
//   gaps:    [{ x0, z0, x1, z1, width_ft, perimeter }] wall gaps 1-8 ft with no door symbol (archways, passages)
//   slivers: [{ ... }]                             gaps under 1 ft between wall strips (drafting artefacts)
//   windows: [{ x0, z0, x1, z1, length }]           sill islands (for reference; Blender uses the GLB sills)
import { execFileSync } from 'node:child_process'
import { mkdtempSync, readFileSync, writeFileSync, mkdirSync } from 'node:fs'
import { createRequire } from 'node:module'
import { tmpdir } from 'node:os'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
const REPO = join(HERE, '..')
const require = createRequire(join(REPO, 'site', 'package.json'))
const DxfParser = require('dxf-parser')
const polygonClipping = require('polygon-clipping')

const DWG = join(REPO, 'plans', 'plans-AS-BUILT.dwg')
const OUT = join(HERE, 'data', 'openings.json')
const DWG2DXF = process.env.DWG2DXF || '/opt/homebrew/bin/dwg2dxf'

// ---- copied from site/scripts/build-house.mjs ----
const UNIT = 96
const FLOORS = {
  basement: [26200, 26760],
  ground: [26880, 27600],
  first: [27700, 28420],
  second: [28500, 29010],
}
const Y_RANGE = [2150, 3160]

const dir = mkdtempSync(join(process.env.TMPDIR || tmpdir(), 'openings-'))
const dxfPath = join(dir, 'plans.dxf')
execFileSync(DWG2DXF, ['-y', '-o', dxfPath, DWG], { stdio: 'ignore' })
const dxf = new DxfParser().parseSync(readFileSync(dxfPath, 'utf8'))

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
      if (Math.abs(s.u[0] * t.u[1] - s.u[1] * t.u[0]) > 0.02) continue
      const n = [-s.u[1], s.u[0]]
      const gap = (t.a[0] - s.a[0]) * n[0] + (t.a[1] - s.a[1]) * n[1]
      if (Math.abs(gap) < minGap || Math.abs(gap) > maxGap) continue
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
const bounds = (multi) => {
  const pts = multi.flat(2)
  return [Math.min(...pts.map((p) => p[0])), Math.min(...pts.map((p) => p[1])), Math.max(...pts.map((p) => p[0])), Math.max(...pts.map((p) => p[1]))]
}
// ---- end of copied code ----

// Even-odd point-in-multipolygon.
function inWalls(walls, [x, y]) {
  let c = false
  for (const poly of walls) for (const ring of poly) {
    for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
      const [xi, yi] = ring[i]
      const [xj, yj] = ring[j]
      if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) c = !c
    }
  }
  return c
}

// Runs of "inside wall" along n through p, within +-reach; returns the run
// nearest p, or null.
function section(walls, p, n, reach = 16, step = 0.25) {
  const runs = []
  let cur = null
  for (let t = -reach; t <= reach + 1e-9; t += step) {
    if (inWalls(walls, [p[0] + n[0] * t, p[1] + n[1] * t])) {
      if (cur && t - cur[1] <= step * 1.5) cur[1] = t
      else runs.push((cur = [t, t]))
    }
  }
  if (!runs.length) return null
  const dist = (r) => (r[0] <= 0 && r[1] >= 0 ? 0 : Math.min(Math.abs(r[0]), Math.abs(r[1])))
  runs.sort((x, y) => dist(x) - dist(y))
  return runs[0]
}

// Jamb beyond an end point P, walking outward along dir up to `look` inches:
// the first wall cross-section thinner than MAX_WALL (an along-wall run is
// longer and is skipped). Returns { k, run } with k the distance to the jamb face.
const MAX_WALL = 14
function jamb(walls, P, dir, n, look = 10) {
  for (let k = 0.5; k <= look; k += 0.5) {
    const q = [P[0] + dir[0] * k, P[1] + dir[1] * k]
    const run = section(walls, q, n)
    if (!run) continue
    if (run[1] - run[0] > MAX_WALL || run[0] === -16 || run[1] >= 16) return null
    if (run[0] > 6 || run[1] < -6) continue // a different wall alongside, not this jamb
    return { k, run }
  }
  return null
}

// Try A->B as a door gap: a wall jamb beyond at least one end, open in the middle.
function gapRect(walls, A, B) {
  const len = Math.hypot(B[0] - A[0], B[1] - A[1])
  if (len < 12) return null
  const u = [(B[0] - A[0]) / len, (B[1] - A[1]) / len]
  const n = [-u[1], u[0]]
  const jA = jamb(walls, A, [-u[0], -u[1]], n)
  const jB = jamb(walls, B, u, n)
  if (!jA && !jB) return null
  const run = jA && jB ? [Math.min(jA.run[0], jB.run[0]), Math.max(jA.run[1], jB.run[1])] : (jA || jB).run
  if (run[1] - run[0] > MAX_WALL) return null
  const c = (run[0] + run[1]) / 2
  for (const f of [0.25, 0.5, 0.75]) {
    const m = [A[0] + u[0] * len * f + n[0] * c, A[1] + u[1] * len * f + n[1] * c]
    if (inWalls(walls, m)) return null
  }
  const s0 = -(jA ? jA.k : 0) - 1
  const s1 = len + (jB ? jB.k : 0) + 1
  const pts = []
  for (const sAlong of [s0, s1]) for (const t of [run[0] - 0.25, run[1] + 0.25]) {
    pts.push([A[0] + u[0] * sAlong + n[0] * t, A[1] + u[1] * sAlong + n[1] * t])
  }
  return { pts, width: s1 - s0 - 2, both: !!(jA && jB) }
}

// Block door: closed leaf runs from the hinge (arc centre) along the block's
// arc start/end; transform block points into drawing space.
function blockXform(ins) {
  const sx = ins.xScale ?? 1
  const sy = ins.yScale ?? 1
  const r = ((ins.rotation ?? 0) * Math.PI) / 180
  const c = Math.cos(r)
  const s = Math.sin(r)
  return ([x, y]) => {
    const X = x * sx
    const Y = y * sy
    return [ins.position.x + X * c - Y * s, ins.position.y + X * s + Y * c]
  }
}
const arcEnds = (a, f = (p) => p) => {
  const P = (ang) => f([a.center.x + a.radius * Math.cos(ang), a.center.y + a.radius * Math.sin(ang)])
  return [f([a.center.x, a.center.y]), P(a.startAngle), P(a.endAngle)]
}

function doorCandidates(range) {
  const cands = []
  for (const e of dxf.entities.filter((e) => e.layer === 'door')) {
    if (e.type === 'INSERT' && dxf.blocks[e.name]) {
      if (!inside(range, [e.position.x, e.position.y])) continue
      const f = blockXform(e)
      for (const a of dxf.blocks[e.name].entities.filter((b) => b.type === 'ARC')) {
        const [H, E1, E2] = arcEnds(a, f)
        // In the DOOR/DOOR1 blocks the leaf is drawn open along the arc's start
        // angle; the closed leaf (the wall gap) is along its end angle.
        cands.push({ source: `${e.name}`, H, ends: [E1, E2], closed: E2 })
      }
    } else if (e.type === 'ARC') {
      if (!inside(range, [e.center.x, e.center.y])) continue
      const [H, E1, E2] = arcEnds(e)
      cands.push({ source: 'arc', H, ends: [E1, E2] })
    }
  }
  // Double doors: two leaves whose closed ends meet become one opening hinge to hinge.
  const d = (p, q) => Math.hypot(p[0] - q[0], p[1] - q[1])
  const merged = []
  const used = new Set()
  for (let i = 0; i < cands.length; i++) for (let j = i + 1; j < cands.length; j++) {
    if (used.has(i) || used.has(j)) continue
    const a = cands[i]
    const b = cands[j]
    const span = d(a.H, b.H)
    const meet = a.ends.some((ea) => b.ends.some((eb) => d(ea, eb) < 4 && Math.abs(d(a.H, ea) + d(b.H, eb) - span) < 4))
    if (!meet) continue
    used.add(i)
    used.add(j)
    merged.push({ source: `double ${a.source}+${b.source}`, H: a.H, ends: [b.H] })
  }
  return [...cands.filter((_, i) => !used.has(i)), ...merged]
}

// Sliding / double-line doors drawn directly as close parallel LINE pairs on the door layer.
function linePairs(range, hinges) {
  const lines = dxf.entities.filter((e) => e.layer === 'door' && e.type === 'LINE')
    .map((e) => [[e.vertices[0].x, e.vertices[0].y], [e.vertices[1].x, e.vertices[1].y]])
    .filter((s) => inside(range, s[0]) && inside(range, s[1]))
    .filter(([a, b]) => Math.hypot(b[0] - a[0], b[1] - a[1]) >= 18)
    .filter(([a, b]) => !hinges.some((h) => Math.hypot(a[0] - h[0], a[1] - h[1]) < 8 || Math.hypot(b[0] - h[0], b[1] - h[1]) < 8))
  const out = []
  const used = new Set()
  for (let i = 0; i < lines.length; i++) for (let j = i + 1; j < lines.length; j++) {
    if (used.has(i) || used.has(j)) continue
    const [a, b] = lines[i]
    const [c, d] = lines[j]
    const len = Math.hypot(b[0] - a[0], b[1] - a[1])
    const u = [(b[0] - a[0]) / len, (b[1] - a[1]) / len]
    const v = [d[0] - c[0], d[1] - c[1]]
    const lv = Math.hypot(...v)
    if (Math.abs(u[0] * v[1] - u[1] * v[0]) / lv > 0.02) continue
    const gap = Math.abs((c[0] - a[0]) * -u[1] + (c[1] - a[1]) * u[0])
    if (gap > 3) continue
    const proj = (p) => (p[0] - a[0]) * u[0] + (p[1] - a[1]) * u[1]
    if (Math.min(proj(c), proj(d)) > len - 6 || Math.max(proj(c), proj(d)) < 6) continue
    used.add(i)
    used.add(j)
    const lo = Math.min(0, proj(c), proj(d))
    const hi = Math.max(len, proj(c), proj(d))
    const m = [(a[0] + c[0]) / 2 - u[0] * proj([(a[0] + c[0]) / 2, (a[1] + c[1]) / 2]), (a[1] + c[1]) / 2 - u[1] * proj([(a[0] + c[0]) / 2, (a[1] + c[1]) / 2])]
    out.push([[m[0] + u[0] * lo, m[1] + u[1] * lo], [m[0] + u[0] * hi, m[1] + u[1] * hi]])
  }
  return out
}

// Wall gaps with no door symbol: from each short ring edge (a wall end face),
// march outward to the next wall; keep gaps whose far side is a matching end.
function wallGaps(walls, skip) {
  const out = []
  const seen = new Set()
  for (const poly of walls) for (const ring of poly) for (let i = 0; i < ring.length - 1; i++) {
    const p = ring[i]
    const q = ring[i + 1]
    const len = Math.hypot(q[0] - p[0], q[1] - p[1])
    if (len < 2.5 || len > 14) continue
    const u = [(q[0] - p[0]) / len, (q[1] - p[1]) / len]
    let n = [-u[1], u[0]]
    const mid = [(p[0] + q[0]) / 2, (p[1] + q[1]) / 2]
    if (inWalls(walls, [mid[0] + n[0] * 0.5, mid[1] + n[1] * 0.5])) n = [-n[0], -n[1]]
    let hit = 0
    for (let t = 1; t <= 96; t += 0.5) {
      if (inWalls(walls, [mid[0] + n[0] * t, mid[1] + n[1] * t])) { hit = t; break }
    }
    if (!hit) continue
    // Under a foot: a drafting sliver between strips, filled full height.
    const sliver = hit < 12
    if (!sliver) {
      // far side must be a wall end of similar section, lined up with this face
      const far = section(walls, [mid[0] + n[0] * (hit + 1), mid[1] + n[1] * (hit + 1)], u, 16)
      if (!far || far[1] - far[0] > MAX_WALL || Math.abs((far[0] + far[1]) / 2) > 4) continue
    }
    const t0 = -len / 2 - 0.25
    const t1 = len / 2 + 0.25
    const pts = [[0, t0], [0, t1], [hit, t0], [hit, t1]].map(([a, b]) => [mid[0] + n[0] * a + u[0] * b, mid[1] + n[1] * a + u[1] * b])
    const cx = mid[0] + n[0] * hit / 2
    const cy = mid[1] + n[1] * hit / 2
    const key = `${Math.round(cx / 3)},${Math.round(cy / 3)}`
    if (seen.has(key)) continue
    seen.add(key)
    if (skip([cx, cy], sliver)) continue
    out.push({ pts, width: hit, centre: [cx, cy], sliver })
  }
  return out
}

const local = (origin) => ([x, y]) => [(x - origin[0]) / UNIT, -(y - origin[1]) / UNIT]
const r4 = (v) => +v.toFixed(4)

const result = { unit: UNIT, doorHead: 84 / UNIT, note: 'floor-local Three.js units; Blender y = -z', floors: {} }
for (const [id, range] of Object.entries(FLOORS)) {
  const cols = columns(range)
  const walls = polygonClipping.union(...pairStrips(layer(range, 'WALL')), ...cols)
  const sills = polygonClipping.difference(polygonClipping.union(...pairStrips(layer(range, 'window'), 2, 14)), walls)
  const site = layer(range, 'SITE')
  const [x0, y0, x1, y1] = bounds([...walls, [[...site.flat()]]])
  const origin = [(x0 + x1) / 2, (y0 + y1) / 2]
  const L = local(origin)
  // Doors outside the building's walls (the compound gates on the site layer) are skipped.
  const [wx0, wy0, wx1, wy1] = bounds(walls)
  const offsite = []
  const toRect = (pts, extra) => {
    const cx = pts.reduce((a, p) => a + p[0], 0) / pts.length
    const cy = pts.reduce((a, p) => a + p[1], 0) / pts.length
    if (cx < wx0 - 2 || cx > wx1 + 2 || cy < wy0 - 2 || cy > wy1 + 2) {
      offsite.push({ source: extra.source, at: L([cx, cy]).map(r4) })
      return null
    }
    const q = pts.map(L)
    const xs = q.map((p) => p[0])
    const zs = q.map((p) => p[1])
    return { x0: r4(Math.min(...xs)), z0: r4(Math.min(...zs)), x1: r4(Math.max(...xs)), z1: r4(Math.max(...zs)), ...extra }
  }

  const doors = []
  const rejected = []
  const pushDoor = (d) => { if (d) doors.push(d) }
  const cands = doorCandidates(range)
  for (const c of cands) {
    // Prefer the end that gives a gap with walls at both jambs.
    const tries = c.ends.map((E) => gapRect(walls, c.H, E)).filter(Boolean).sort((a, b) => b.both - a.both)
    if (!tries.length && c.closed) {
      // Fallback for block doors: the closed leaf with a nominal 9 in wall.
      const len = Math.hypot(c.closed[0] - c.H[0], c.closed[1] - c.H[1])
      const u = [(c.closed[0] - c.H[0]) / len, (c.closed[1] - c.H[1]) / len]
      const n = [-u[1], u[0]]
      const pts = []
      for (const a of [-1, len + 1]) for (const t of [-4.5, 4.5]) pts.push([c.H[0] + u[0] * a + n[0] * t, c.H[1] + u[1] * a + n[1] * t])
      pushDoor(toRect(pts, { width_ft: +(len / 12).toFixed(2), source: c.source, jambs: 0 }))
      continue
    }
    if (!tries.length) { rejected.push({ source: c.source, at: L(c.H).map(r4) }); continue }
    const g = tries[0]
    pushDoor(toRect(g.pts, { width_ft: +(g.width / 12).toFixed(2), source: c.source, jambs: g.both ? 2 : 1 }))
  }
  for (const [A, B] of linePairs(range, cands.map((c) => c.H))) {
    const g = gapRect(walls, A, B)
    if (!g || !g.both) { rejected.push({ source: 'lines', at: L(A).map(r4) }); continue }
    pushDoor(toRect(g.pts, { width_ft: +(g.width / 12).toFixed(2), source: 'lines', jambs: g.both ? 2 : 1 }))
  }

  // Non-door gaps, minus anything already a door or a window.
  const doorBoxes = doors.map((d) => [d.x0, d.z0, d.x1, d.z1])
  const sillBoxes = sills.map((poly) => bounds([poly]))
  const near = (x, y, b, pad) => x > b[0] - pad && x < b[2] + pad && y > b[1] - pad && y < b[3] + pad
  const skip = ([x, y], sliver) => {
    const [lx, lz] = L([x, y])
    return doorBoxes.some((b) => near(lx, lz, b, sliver ? 0 : 0.05)) || sillBoxes.some((b) => near(x, y, b, sliver ? 0 : 3))
  }
  const gaps = wallGaps(walls, skip).map((g) => {
    const [cx, cy] = g.centre
    const perimeter = cx - wx0 < 18 || wx1 - cx < 18 || cy - wy0 < 18 || wy1 - cy < 18
    return toRect(g.pts, { width_ft: +(g.width / 12).toFixed(2), perimeter, sliver: g.sliver })
  }).filter(Boolean)
  const slivers = gaps.filter((g) => g.sliver)
  const openGaps = gaps.filter((g) => !g.sliver)

  const windows = sills.map((poly) => {
    const [a, b, c, d] = bounds([poly])
    const q = [L([a, b]), L([c, d])]
    const sx = Math.abs(q[1][0] - q[0][0])
    const sz = Math.abs(q[1][1] - q[0][1])
    return { x0: r4(Math.min(q[0][0], q[1][0])), z0: r4(Math.min(q[0][1], q[1][1])), x1: r4(Math.max(q[0][0], q[1][0])), z1: r4(Math.max(q[0][1], q[1][1])), length: r4(Math.max(sx, sz)), simple: Math.max(sx, sz) >= 0.18 && Math.min(sx, sz) <= 0.2 }
  })
  result.floors[id] = { doors, gaps: openGaps, slivers, windows, rejected, offsite }
  console.log(`${id}: ${doors.length} doors (${doors.map((d) => d.width_ft).join(', ')} ft), ${rejected.length} rejected, ${offsite.length} off-site, ${openGaps.length} other gaps (${openGaps.filter((g) => g.perimeter).length} perimeter), ${slivers.length} slivers (${slivers.filter((g) => g.perimeter).length} perimeter), ${windows.length} sill islands (${windows.filter((w) => w.simple).length} simple)`)
}
mkdirSync(dirname(OUT), { recursive: true })
writeFileSync(OUT, JSON.stringify(result, null, 2) + '\n')
console.log(`wrote ${OUT}`)
