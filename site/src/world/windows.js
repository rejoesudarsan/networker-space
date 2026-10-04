import * as THREE from 'three'

const cube = new THREE.BoxGeometry(1, 1, 1)
const wood = new THREE.MeshStandardMaterial({ color: '#785640', roughness: 0.8 })
const glass = new THREE.MeshStandardMaterial({ color: '#9daaa5', roughness: 0.22, transparent: true, opacity: 0.22, depthWrite: false })

// Window locations come from the CAD window-layer sills, not guessed facade
// openings. Weld split exporter vertices to recover each disconnected sill.
function islands(geometry) {
  const pos = geometry.getAttribute('position')
  const ids = [], parent = [], points = [], keys = new Map()
  for (let i = 0; i < pos.count; i++) {
    const v = new THREE.Vector3().fromBufferAttribute(pos, i)
    const key = [v.x, v.y, v.z].map((n) => Math.round(n * 10000)).join(',')
    if (!keys.has(key)) {
      keys.set(key, points.length)
      parent.push(points.length)
      points.push(v)
    }
    ids.push(keys.get(key))
  }
  const root = (i) => { while (parent[i] !== i) { parent[i] = parent[parent[i]]; i = parent[i] } return i }
  const count = geometry.index?.count ?? pos.count
  const at = (i) => ids[geometry.index ? geometry.index.getX(i) : i]
  for (let i = 0; i < count; i += 3) {
    parent[root(at(i + 1))] = root(at(i))
    parent[root(at(i + 2))] = root(at(i))
  }
  const bounds = new Map()
  points.forEach((p, i) => {
    const r = root(i)
    if (!bounds.has(r)) bounds.set(r, new THREE.Box3())
    bounds.get(r).expandByPoint(p)
  })
  return [...bounds.values()]
}

export function addWindows(floor, model) {
  const group = new THREE.Group()
  group.name = 'CAD window frames'
  const frames = [], panes = []
  const transform = new THREE.Object3D()
  const put = (target, x, y, z, w, h, d) => {
    transform.position.set(x, y, z)
    transform.scale.set(w, h, d)
    transform.updateMatrix()
    target.push(transform.matrix.clone())
  }
  const sillHeight = 22 / 96
  const height = 0.86
  group.position.y = sillHeight
  model.traverse((o) => {
    if (!o.isMesh || o.name !== 'sills') return
    for (const b of islands(o.geometry)) {
      const sx = b.max.x - b.min.x, sz = b.max.z - b.min.z
      const alongX = sx > sz, length = Math.max(sx, sz)
      // Curved or broad areas are not simple window strips.
      if (length < 0.18 || Math.min(sx, sz) > 0.2) continue
      const x = (b.min.x + b.max.x) / 2, z = (b.min.z + b.max.z) / 2
      for (const y of [0.018, height - 0.018]) put(frames, x, y, z, alongX ? length : 0.035, 0.036, alongX ? 0.035 : length)
      const divisions = Math.max(1, Math.ceil(length / 0.42))
      for (let j = 0; j <= divisions; j++) {
        const offset = -length / 2 + j * length / divisions
        put(frames, x + (alongX ? offset : 0), height / 2, z + (alongX ? 0 : offset), 0.025, height, 0.025)
      }
      put(panes, x, height / 2, z, alongX ? length : 0.012, height - 0.05, alongX ? 0.012 : length)
    }
  })
  for (const [mat, transforms] of [[wood, frames], [glass, panes]]) {
    if (!transforms.length) continue
    const mesh = new THREE.InstancedMesh(cube, mat, transforms.length)
    transforms.forEach((m, i) => mesh.setMatrixAt(i, m))
    mesh.castShadow = mat === wood
    mesh.receiveShadow = mat === wood
    mesh.computeBoundingSphere()
    group.add(mesh)
  }
  floor.add(group)
  return { o: group, full: 1, low: (0.42 - sillHeight) / height }
}
