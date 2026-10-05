import * as THREE from 'three'
import { createPerson, posePerson } from '../world/characters.js'

// People in the dioramas. They are not baked: they sit on the seats the
// Blender fit-out modules placed (blender/details/*.py; plan units, floor
// frame, rot as in _furniture.py so 0 faces the street) and move a little.

const E = Math.PI / 2
const W = -Math.PI / 2
const N = Math.PI
const S = 0
// Seat tops: the baked teak chairs are a touch higher than the characters'
// SEAT_H; armchair cushions match it.
const CHAIR = 0.026
const ARM = 0.004

// [x, z, rot, pose, lift, props]
const ROOM_PEOPLE = {
  cafe: [
    [1.74, 2.17, E, 'seated-table', CHAIR],
    [1.74, 2.87, E, 'seated-table', CHAIR],
    [0.99, 1.98, E, 'seated-table', CHAIR],
    [1.37, 1.98, W, 'seated-table', CHAIR],
    [1.18, 2.93, N, 'seated-table', CHAIR],
  ],
  lower: [
    [0.63, 0.59, S, 'seated-laptop', CHAIR],
    [1.23, 1.13, N, 'seated-laptop', CHAIR],
    [0.93, 1.13, N, 'seated-table', CHAIR],
  ],
  // The lounge at the north end of the terrace (terrace_evening.py).
  terrace: [
    [-1.87, -1.55, E, 'seated', ARM],
    [-1.25, -1.4, W, 'seated', ARM],
    [-1.72, -2.62, 0.4, 'idle', 0],
    [-1.5, -2.5, -2.5, 'idle', 0],
    [-1.42, -2.75, -1.2, 'idle', 0],
  ],
  // A talk: one on the stage, the audience on the bleachers
  // (event_space.py: stage top 0.123, cushion rows at x 1.97 / 2.22 / 2.47).
  event: [
    [1.02, 3.15, E, 'idle', 0.123],
    [1.973, 2.6, W, 'seated', 0.012],
    [1.973, 3.35, W, 'seated', 0.012],
    [2.219, 2.85, W, 'seated', 0.176],
    [2.219, 3.6, W, 'seated', 0.176],
    [2.465, 3.1, W, 'seated', 0.34],
  ],
}

// The court's armchairs (court_library.py): two people in conversation.
const COURT_A = [2.294, 0.98, W - 0.12]
const COURT_B = [2.294, 1.48, W + 0.12]

export function createPeople(floors, roomsMeta, fogify) {
  const groups = {}
  const all = []
  const add = (parent, [x, z, rot, pose, lift = 0, prop]) => {
    const p = createPerson()
    p.position.set(x, lift, z)
    p.rotation.y = rot
    p.userData.pose = pose
    p.userData.phase = Math.random() * 10
    if (prop === 'cup') p.userData.cup = true
    posePerson(p, pose, 0, p.userData.phase)
    parent.add(p)
    all.push(p)
    return p
  }
  for (const [room, list] of Object.entries(ROOM_PEOPLE)) {
    const g = new THREE.Group()
    g.visible = false
    floors[roomsMeta[room].floor].add(g)
    for (const e of list) add(g, e)
    groups[room] = g
  }

  const court = new THREE.Group()
  court.visible = false
  floors.first.add(court)
  groups.court = court
  add(court, [...COURT_A, 'seated', ARM])
  add(court, [...COURT_B, 'seated', ARM])

  for (const p of all) p.traverse((o) => o.isMesh && fogify(o.material))

  function update(t, room, still) {
    for (const [id, g] of Object.entries(groups)) g.visible = id === room
    const g = groups[room]
    if (!g || still) return
    for (const p of g.children) {
      if (!p.userData.rig) continue
      posePerson(p, p.userData.pose, t, p.userData.phase)
    }
  }
  return { update }
}
