import * as THREE from 'three'
import { createPerson, posePerson } from '../world/characters.js'

// People. They are not baked. Inside, they sit on the seats the Blender
// fit-out modules placed (blender/details/*.py; plan units in the floor's
// frame, rot as in _furniture.py so 0 faces the street) and show with
// their floor. Outside, they walk the street and in at the gate, so the
// house reads at its real size.

const E = Math.PI / 2
const W = -Math.PI / 2
const N = Math.PI
const S = 0
// Seat tops: the baked teak chairs are a touch higher than the characters'
// SEAT_H; armchair cushions match it.
const CHAIR = 0.026
const ARM = 0.004

// [x, z, rot, pose, lift]
const FLOOR_PEOPLE = {
  basement: [
    [0.63, 0.59, S, 'seated-laptop', CHAIR],
    [1.23, 1.13, N, 'seated-laptop', CHAIR],
    [0.93, 1.13, N, 'seated-table', CHAIR],
    [1.12, -3.08, S, 'seated-table', CHAIR],
    [1.42, -2.52, N, 'seated-table', CHAIR],
  ],
  ground: [
    [1.74, 2.17, E, 'seated-table', CHAIR],
    [1.74, 2.87, E, 'seated-table', CHAIR],
    [0.99, 1.98, E, 'seated-table', CHAIR],
    [1.37, 1.98, W, 'seated-table', CHAIR],
    [1.18, 2.93, N, 'seated-table', CHAIR],
    [-0.08, -1.72, E, 'seated-table', CHAIR],
    [0.32, -1.33, W, 'seated-table', CHAIR],
    [-1.15, -1.3, N, 'idle', 0],
  ],
  first: [
    // The court: two in the armchairs (court_library.py).
    [2.294, 0.98, W - 0.12, 'seated', ARM],
    [2.294, 1.48, W + 0.12, 'seated', ARM],
    // The event room: a talk (event_space.py: stage top 0.123).
    [1.02, 3.15, E, 'idle', 0.123],
    [1.973, 2.6, W, 'seated', 0.012],
    [1.973, 3.35, W, 'seated', 0.012],
    [2.219, 2.85, W, 'seated', 0.176],
    [2.219, 3.6, W, 'seated', 0.176],
    [2.465, 3.1, W, 'seated', 0.34],
  ],
  second: [
    [-1.87, -1.55, E, 'seated', ARM],
    [-1.25, -1.4, W, 'seated', ARM],
    [-1.72, -2.62, 0.4, 'idle', 0],
    [-1.5, -2.5, -2.5, 'idle', 0],
    [-1.42, -2.75, -1.2, 'idle', 0],
    [-1.55, 0.55, 2.8, 'idle', 0],
    [-1.6, 0.3, 0.3, 'idle', 0],
  ],
}

// Walks in street coordinates (ground frame, y = 0 is the street).
const STREET_Z = 5.65
const FAR_Z = 9.85
const GATE = [[-2.75, 0, STREET_Z], [-2.75, 0, 4.9]]

export function createPeople(floors, street, fogify) {
  const all = []
  const groups = {}
  const add = (parent, [x, z, rot, pose, lift = 0]) => {
    const p = createPerson()
    p.position.set(x, lift, z)
    p.rotation.y = rot
    p.userData.pose = pose
    p.userData.phase = Math.random() * 10
    posePerson(p, pose, 0, p.userData.phase)
    parent.add(p)
    all.push(p)
    return p
  }
  for (const [id, list] of Object.entries(FLOOR_PEOPLE)) {
    const g = new THREE.Group()
    g.visible = false
    floors[id].add(g)
    for (const e of list) add(g, e)
    groups[id] = g
  }

  // Walkers: a handful on the near and far pavements, a few turning in at
  // the gate. Each loops along its path with its own pace.
  const walkers = []
  const walk = (pts, speed, offset) => {
    const p = createPerson()
    street.add(p)
    all.push(p)
    const v = pts.map((q) => new THREE.Vector3(...q))
    let total = 0
    const segs = v.slice(1).map((b, i) => {
      const s = { a: v[i], b, len: v[i].distanceTo(b), at: total }
      total += s.len
      return s
    })
    walkers.push({ p, segs, total, speed, d: offset * total, phase: Math.random() * 10 })
  }
  for (let i = 0; i < 6; i++) {
    const dir = i % 2 ? 1 : -1
    const z = (i < 4 ? STREET_Z : FAR_Z) + (Math.random() - 0.5) * 0.3
    walk([[-24 * dir, 0, z], [24 * dir, 0, z]], 0.55 + Math.random() * 0.25, Math.random())
  }
  for (let i = 0; i < 3; i++) {
    const from = i % 2 ? -18 : 18
    walk([[from, 0, STREET_Z + 0.1], ...GATE], 0.6 + Math.random() * 0.15, Math.random())
  }

  for (const p of all) p.traverse((o) => o.isMesh && fogify(o.material))

  const tmp = new THREE.Vector3()
  function update(dt, t, floorWeights, outside, still) {
    for (const [id, g] of Object.entries(groups)) g.visible = (floorWeights[id] || 0) > 0.5
    for (const w of walkers) w.p.visible = outside
    if (still) return
    for (const g of Object.values(groups)) {
      if (!g.visible) continue
      for (const p of g.children) if (p.userData.rig) posePerson(p, p.userData.pose, t, p.userData.phase)
    }
    if (!outside) return
    for (const w of walkers) {
      w.d = (w.d + w.speed * dt) % w.total
      let seg = w.segs[0]
      for (const s of w.segs) if (w.d >= s.at) seg = s
      const u = (w.d - seg.at) / seg.len
      tmp.lerpVectors(seg.a, seg.b, u)
      w.p.position.copy(tmp)
      w.p.rotation.y = Math.atan2(seg.b.x - seg.a.x, seg.b.z - seg.a.z)
      posePerson(w.p, 'walk', t * w.speed, w.phase)
      // Fade in and out at the ends of a walk, and at the gate.
      const edge = Math.min(w.d, w.total - w.d)
      w.p.scale.setScalar(Math.min(1, edge / 0.5) || 0.001)
    }
  }
  return { update }
}
