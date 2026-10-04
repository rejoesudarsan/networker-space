import * as THREE from 'three'
import { RIDE_H } from './characters.js'

// Small silhouettes that still read as vehicles as they pass the front gate.
const cube = new THREE.BoxGeometry(1, 1, 1)
const tyre = new THREE.CylinderGeometry(1, 1, 1, 12)
tyre.rotateX(Math.PI / 2)
const materials = new Map()
function material(color) {
  if (!materials.has(color)) materials.set(color, new THREE.MeshStandardMaterial({ color, roughness: 0.72 }))
  return materials.get(color)
}
function part(group, size, at, color, geometry = cube) {
  const mesh = new THREE.Mesh(geometry, material(color))
  mesh.scale.set(...size)
  mesh.position.set(...at)
  mesh.castShadow = true
  group.add(mesh)
  return mesh
}

export function createVehicle(auto, createPerson, posePerson) {
  const group = new THREE.Group()
  const wheels = []
  const wheel = (x, z, radius) => {
    const pivot = new THREE.Group()
    pivot.position.set(x, radius, z)
    group.add(pivot)
    part(pivot, [radius, radius, 0.065], [0, 0, 0], '#252625', tyre)
    part(pivot, [radius * 0.48, radius * 0.48, 0.07], [0, 0, 0], '#93938b', tyre)
    wheels.push(pivot)
  }
  if (auto) {
    wheel(0.4, 0, 0.115)
    wheel(-0.32, -0.25, 0.115)
    wheel(-0.32, 0.25, 0.115)
    part(group, [0.94, 0.09, 0.51], [0, 0.2, 0], '#303735')
    part(group, [0.2, 0.29, 0.48], [-0.4, 0.38, 0], '#356345')
    for (const z of [-0.235, 0.235]) {
      part(group, [0.43, 0.22, 0.035], [-0.2, 0.35, z], '#356345')
      part(group, [0.035, 0.33, 0.035], [-0.44, 0.59, z], '#454a40')
      part(group, [0.035, 0.3, 0.035], [0.29, 0.57, z], '#454a40')
      part(group, [0.6, 0.025, 0.025], [-0.14, 0.46, z], '#d5b050')
    }
    part(group, [0.85, 0.095, 0.57], [-0.06, 0.78, 0], '#d8af46')
    part(group, [0.13, 0.27, 0.46], [0.38, 0.38, 0], '#d8af46')
    const windscreen = part(group, [0.024, 0.23, 0.41], [0.32, 0.625, 0], '#859c99')
    windscreen.rotation.z = 0.13
    part(group, [0.27, 0.065, 0.41], [-0.27, 0.37, 0], '#343630')
    part(group, [0.07, 0.2, 0.41], [-0.4, 0.47, 0], '#343630')
    part(group, [0.03, 0.085, 0.13], [0.453, 0.39, 0], '#f4dfad')
    part(group, [0.03, 0.045, 0.2], [0.464, 0.26, 0], '#e6d9af')
    part(group, [0.065, 0.045, 0.59], [0.46, 0.21, 0], '#64685e')
    for (const z of [-0.3, 0.3]) part(group, [0.085, 0.055, 0.025], [0.26, 0.62, z], '#373b36')
  } else {
    wheel(-0.3, 0, 0.13)
    wheel(0.31, 0, 0.13)
    part(group, [0.56, 0.075, 0.16], [0, 0.21, 0], '#3b4545')
    part(group, [0.31, 0.18, 0.19], [-0.2, 0.29, 0], '#7d4136')
    part(group, [0.32, 0.055, 0.21], [-0.17, 0.405, 0], '#272b29')
    const front = part(group, [0.07, 0.32, 0.19], [0.23, 0.35, 0], '#7d4136')
    front.rotation.z = 0.18
    part(group, [0.07, 0.04, 0.31], [0.2, 0.52, 0], '#343c39')
    part(group, [0.035, 0.075, 0.09], [0.275, 0.49, 0], '#f4dfad')
    const rider = createPerson()
    posePerson(rider, 'ride', 0, 0)
    rider.rotation.y = Math.PI / 2
    rider.position.set(-0.09, 0.4325 - RIDE_H, 0)
    group.add(rider)
  }
  group.userData.wheels = wheels
  return group
}

export function rollVehicle(group, distance) {
  for (const wheel of group.userData.wheels) wheel.rotation.z -= distance / 0.12
}
