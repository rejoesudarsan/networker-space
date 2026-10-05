import * as THREE from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

// Checks a baked floor from blender/tools/bake_site.py on its own: the atlas
// shown unlit and untouched (it already went through Blender's view
// transform), glass and lamps from the fixtures file.
// ?floor=ground&set=day&az=15&el=50&x0=0.6&z0=1.3&x1=2.4&z1=3.2 frames a room like room_shot.py.
const q = new URLSearchParams(location.search)
const floor = q.get('floor') || 'ground'
const set = q.get('set') || 'day'
const canvas = document.getElementById('c')
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true })
renderer.setPixelRatio(Math.min(devicePixelRatio, 2))
renderer.toneMapping = THREE.NoToneMapping
const scene = new THREE.Scene()
scene.background = new THREE.Color('#d1bfc2')
const camera = new THREE.PerspectiveCamera(54.4, 1, 0.01, 200)
const controls = new OrbitControls(camera, canvas)

const loader = new GLTFLoader()
const baked = await loader.loadAsync(`/models/baked/${floor}-${set}.gltf`)
baked.scene.traverse((o) => {
  if (!o.isMesh) return
  const map = o.material.map
  map.colorSpace = THREE.SRGBColorSpace
  map.anisotropy = renderer.capabilities.getMaxAnisotropy()
  o.material = new THREE.MeshBasicMaterial({ map })
})
scene.add(baked.scene)
const fx = await loader.loadAsync(`/models/baked/${floor}-fixtures.gltf`).catch(() => null)
if (fx) {
  fx.scene.traverse((o) => {
    if (!o.isMesh) return
    const m = o.material
    const x = m.userData || {}
    o.material = x.glass
      ? new THREE.MeshBasicMaterial({ color: m.color, transparent: true, opacity: 0.25, depthWrite: false })
      : new THREE.MeshBasicMaterial({ color: m.emissive && m.emissive.getHex() ? m.emissive : m.color })
  })
  scene.add(fx.scene)
}

// Frame the room the way room_shot.py does.
const n = (k, d) => (q.has(k) ? +q.get(k) : d)
const [x0, z0, x1, z1] = [n('x0', 0.6), n('z0', 1.3), n('x1', 2.4), n('z1', 3.2)]
const az = THREE.MathUtils.degToRad(n('az', 15))
const el = THREE.MathUtils.degToRad(n('el', 50))
const span = Math.max(x1 - x0, z1 - z0)
const fov = 2 * Math.atan(18 / 35)
const dist = (span * 0.62) / Math.tan(fov / 2) + span * 0.15
const target = new THREE.Vector3((x0 + x1) / 2, 1.3 * 0.35, (z0 + z1) / 2)
camera.position.set(target.x + Math.sin(az) * Math.cos(el) * dist, target.y + Math.sin(el) * dist, target.z + Math.cos(az) * Math.cos(el) * dist)
controls.target.copy(target)

function resize() {
  const w = innerWidth
  const h = innerHeight
  renderer.setSize(w, h, false)
  camera.aspect = w / h
  // Horizontal FOV fixed (Blender's sensor fit), like the 35 mm room shot.
  camera.fov = THREE.MathUtils.radToDeg(2 * Math.atan(Math.tan(fov / 2) / camera.aspect))
  camera.updateProjectionMatrix()
}
resize()
addEventListener('resize', resize)
document.getElementById('hud').textContent = `${floor} · ${set} · baked`
renderer.setAnimationLoop(() => {
  controls.update()
  renderer.render(scene, camera)
})
