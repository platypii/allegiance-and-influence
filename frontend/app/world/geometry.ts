import * as THREE from "three"
import { mergeGeometries } from "three/addons/utils/BufferGeometryUtils.js"

export function palette() {
  const materials = new Map<string, THREE.MeshStandardMaterial>()
  return (color: string, metalness = 0) => {
    const key = `${color}:${metalness}`
    if (!materials.has(key)) materials.set(key, new THREE.MeshStandardMaterial({ color, roughness: metalness ? .4 : .78, metalness }))
    return materials.get(key)!
  }
}
export type Paint = ReturnType<typeof palette>
export function solid(parent: THREE.Object3D, geometry: THREE.BufferGeometry, material: THREE.Material, x = 0, y = 0, z = 0) {
  const mesh = new THREE.Mesh(geometry, material)
  mesh.position.set(x, y, z)
  mesh.castShadow = true; mesh.receiveShadow = true
  parent.add(mesh)
  return mesh
}
export function sphere(parent: THREE.Object3D, paint: Paint, color: string, x: number, y: number, z: number, sx: number, sy = sx, sz = sx) {
  const mesh = solid(parent, new THREE.SphereGeometry(1, 16, 10), paint(color), x, y, z)
  mesh.scale.set(sx, sy, sz)
  return mesh
}
export function box(parent: THREE.Object3D, paint: Paint, color: string, x: number, y: number, z: number, w: number, h: number, d: number) {
  return solid(parent, new THREE.BoxGeometry(w, h, d), paint(color), x, y, z)
}
export function cylinder(parent: THREE.Object3D, paint: Paint, color: string, x: number, y: number, z: number, top: number, bottom: number, h: number, segments = 24) {
  return solid(parent, new THREE.CylinderGeometry(top, bottom, h, segments), paint(color), x, y, z)
}

// Batch immobile parts by material: a detailed miniature is a handful of draws,
// rather than a separate draw call for every curl, button, leaf and window.
export function batch(group: THREE.Group) {
  group.updateMatrixWorld(true)
  const parts = new Map<THREE.Material, THREE.BufferGeometry[]>()
  group.traverse(object => {
    if (!(object instanceof THREE.Mesh) || Array.isArray(object.material)) return
    const geometry = object.geometry.index ? object.geometry.toNonIndexed() : object.geometry.clone()
    geometry.applyMatrix4(object.matrixWorld)
    if (!parts.has(object.material)) parts.set(object.material, [])
    parts.get(object.material)!.push(geometry)
    object.geometry.dispose()
  })
  group.clear()
  for (const [material, geometries] of parts) {
    const merged = mergeGeometries(geometries)
    if (merged) solid(group, merged, material)
    geometries.forEach(geometry => geometry.dispose())
  }
}

