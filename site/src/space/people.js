import * as THREE from 'three'
import { createPerson, posePerson } from '../world/characters.js'

// People in the dioramas. They are not baked: they sit on the seats the
// Blender fit-out modules placed (blender/details/*.py; plan units, floor
// frame, rot as in _furniture.py so 0 faces the street) and move a little.
// The court group follows the "Who's inside" choice.

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
  terrace: [
    [-1.62, 1.12, 0.6, 'idle', 0, 'cup'],
    [-1.42, 1.22, -2.2, 'idle', 0],
    [-1.47, 0.98, -0.6, 'idle', 0, 'cup'],
    [-1.55, -1.55 - 0.32, E, 'seated', ARM],
  ],
}

// The court's armchairs (court_library.py) and the side table between them.
const COURT_A = [2.294, 0.98, W - 0.12]
const COURT_B = [2.294, 1.48, W + 0.12]
export const INTERESTS = [
  { id: 'founders', name: 'Founders', caption: 'Find a sounding board.', line: 'A conversation can change the day.', poses: ['seated', 'seated'] },
  { id: 'artists', name: 'Artists', caption: 'Make something. Share a perspective.', line: 'Ideas take different forms here.', poses: ['seated-read', 'seated-read'] },
  { id: 'music', name: 'Music', caption: 'Listen closer.', line: 'A small room. A shared rhythm.', poses: ['play', 'seated'] },
  { id: 'play', name: 'Play', caption: 'Leave room for play.', line: 'A game. A pause. A different kind of focus.', poses: ['seated-table', 'seated-table'], board: true },
]

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

  // The court pair, re-posed per interest.
  const court = new THREE.Group()
  court.visible = false
  floors.first.add(court)
  groups.court = court
  const a = add(court, [...COURT_A, 'seated', ARM])
  const b = add(court, [...COURT_B, 'seated', ARM])
  // A small board game on the side table for Play; sketchbooks for Artists.
  const board = new THREE.Mesh(new THREE.BoxGeometry(0.11, 0.008, 0.11), fogify(new THREE.MeshStandardMaterial({ color: '#d8d0c0', roughness: 0.9 })))
  board.position.set(2.385, 0.21, 1.23)
  court.add(board)
  const pieces = []
  for (let i = 0; i < 6; i++) {
    const m = new THREE.Mesh(new THREE.CylinderGeometry(0.007, 0.007, 0.012, 8), fogify(new THREE.MeshStandardMaterial({ color: i % 2 ? '#b5653f' : '#2b2b2a' })))
    m.position.set(2.36 + (i % 3) * 0.025, 0.22, 1.21 + Math.floor(i / 3) * 0.04)
    court.add(m)
    pieces.push(m)
  }
  let interest = INTERESTS[0]
  function setInterest(id) {
    interest = INTERESTS.find((i) => i.id === id) || INTERESTS[0]
    a.userData.pose = interest.poses[0]
    b.userData.pose = interest.poses[1]
    // Two players lean in to the table, so they turn toward it.
    a.rotation.y = interest.board ? W - 0.5 : COURT_A[2]
    b.rotation.y = interest.board ? W + 0.5 : COURT_B[2]
    board.visible = !!interest.board
    for (const m of pieces) m.visible = !!interest.board
  }
  setInterest('founders')

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
  return { update, setInterest, get interest() { return interest } }
}
