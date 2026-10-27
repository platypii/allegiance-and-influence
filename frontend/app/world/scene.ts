import * as THREE from "three"
import { miniature, palette, scenery, solid } from "./miniatures"

export interface WorldPerson { id: string; name: string; team: number; selectable: boolean }
export interface WorldState { people: WorldPerson[]; pairs: [string, string][]; talking: string[] }
export interface WorldScene {
  update: (state: WorldState) => void
  pause: (paused: boolean) => void
  rotate: (direction: number) => void
  zoom: (direction: number) => void
  focus: (id: string | null) => void
  dispose: () => void
}

export function createWorld(canvas: HTMLCanvasElement, initial: WorldState, onPick: (id: string) => void, onHover: (name: string) => void, onLost: () => void): WorldScene {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: "low-power" })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5))
  renderer.shadowMap.enabled = true
  renderer.shadowMap.type = THREE.PCFShadowMap
  renderer.outputColorSpace = THREE.SRGBColorSpace
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  renderer.toneMappingExposure = 1
  const scene = new THREE.Scene()
  const camera = new THREE.OrthographicCamera(-14, 14, 10, -10, .1, 100)
  let azimuth = .12, zoom = 1, width = 0, height = 0
  const target = new THREE.Vector3(0, .5, 0)
  function positionCamera() {
    camera.position.set(Math.sin(azimuth) * 23, 19, Math.cos(azimuth) * 23)
    camera.lookAt(target)
    camera.zoom = zoom * (width && width < 600 ? 1.2 : 1)
    camera.updateProjectionMatrix()
    camera.updateMatrixWorld()
  }
  positionCamera()
  const paint = palette()
  scene.add(new THREE.HemisphereLight("#fff1d2", "#698e91", 1.8))
  const sun = new THREE.DirectionalLight("#ffdfae", 2.8)
  sun.position.set(-8, 16, 8)
  sun.castShadow = true
  sun.shadow.mapSize.set(1024, 1024)
  Object.assign(sun.shadow.camera, { left: -13, right: 13, top: 13, bottom: -13, near: 1, far: 50 })
  sun.shadow.normalBias = .04
  sun.shadow.bias = -.0003
  scene.add(sun)
  const rim = new THREE.DirectionalLight("#9bc9d7", 1.2)
  rim.position.set(6, 7, -9)
  scene.add(rim)
  scene.add(scenery(paint))
  const floor = solid(scene, new THREE.PlaneGeometry(200, 200), paint("#1b3934"), 0, -1.09, 0)
  floor.rotation.x = -Math.PI / 2
  floor.castShadow = false
  const figures = new Map<string, { root: THREE.Group; figure: THREE.Group; ring: THREE.Mesh; person: WorldPerson; x: number; z: number; homeX: number; homeZ: number; celebration: number }>()
  const factionColor = (team: number) => team < 0 ? "#cb6251" : team > 0 ? "#5b9fbd" : "#c5a971"
  initial.people.forEach((person, index) => {
    const outer = index >= 10
    const count = outer ? initial.people.length - 10 : Math.min(initial.people.length, 10)
    const angle = (outer ? index - 10 : index) / count * Math.PI * 2 + (outer ? .25 : .1)
    const radius = initial.people.length <= 10 ? 3.9 : outer ? 5.4 : 2.8
    const x = Math.sin(angle) * radius, z = Math.cos(angle) * radius
    const root = new THREE.Group()
    root.position.set(x, .58, z)
    const figure = miniature(person.id, paint)
    figure.position.y = .12
    if (initial.people.length > 14) figure.scale.setScalar(.78)
    root.add(figure)
    const base = solid(root, new THREE.CylinderGeometry(.63, .7, .14, 32), paint("#5d6450"), 0, .06, 0)
    const ring = solid(root, new THREE.TorusGeometry(.63, .055, 8, 32), paint(factionColor(person.team)), 0, .15, 0)
    ring.rotation.x = Math.PI / 2
    root.traverse(object => { object.userData.person = person.id })
    base.receiveShadow = true
    scene.add(root)
    figures.set(person.id, { root, figure, ring, person, x, z, homeX: x, homeZ: z, celebration: 0 })
  })
  const pairLines = new THREE.Group()
  scene.add(pairLines)
  let state = initial, pairsKey = "", paused = false, reduced = false, hover: string | null = null, keyboardFocus: string | null = null
  let elapsed = 0, lastTime = 0, frame = 0, disposed = false, dirty = true, lastDraw = 0
  const preference = matchMedia("(prefers-reduced-motion: reduce)")
  reduced = preference.matches
  const preferenceChanged = (event: MediaQueryListEvent) => { reduced = event.matches; dirty = true }
  preference.addEventListener("change", preferenceChanged)
  function update(next: WorldState) {
    state = next
    for (const person of next.people) {
      const item = figures.get(person.id)
      if (!item) continue
      if (item.person.team !== person.team) item.celebration = 1.5
      item.person = person
      item.ring.material = paint(factionColor(person.team))
    }
    const key = JSON.stringify(next.pairs)
    if (key !== pairsKey) {
      pairsKey = key
      for (const line of [...pairLines.children]) {
        if (line instanceof THREE.Line) { line.geometry.dispose(); (line.material as THREE.Material).dispose() }
        pairLines.remove(line)
      }
      for (const [source, target] of next.pairs) {
        const geometry = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3()])
        const line = new THREE.Line(geometry, new THREE.LineBasicMaterial({ color: "#a87933", transparent: true, opacity: .75 }))
        line.userData = { source, target }
        pairLines.add(line)
      }
    }
    dirty = true
  }
  update(initial)
  const raycaster = new THREE.Raycaster()
  const pointer = new THREE.Vector2()
  function pick(event: PointerEvent) {
    const rect = canvas.getBoundingClientRect()
    pointer.set((event.clientX - rect.left) / rect.width * 2 - 1, -(event.clientY - rect.top) / rect.height * 2 + 1)
    raycaster.setFromCamera(pointer, camera)
    return raycaster.intersectObjects([...figures.values()].map(item => item.root), true)[0]?.object.userData.person as string | undefined
  }
  function moved(event: PointerEvent) {
    hover = pick(event) || null
    const item = hover ? figures.get(hover) : null
    canvas.style.cursor = item?.person.selectable ? "pointer" : "default"
    onHover(item?.person.name || "")
    dirty = true
  }
  let pressed: { id: string; x: number; y: number } | null = null
  function down(event: PointerEvent) { const id = pick(event); pressed = id ? { id, x: event.clientX, y: event.clientY } : null; if (id) hover = id }
  function up(event: PointerEvent) {
    if (pressed && Math.hypot(event.clientX - pressed.x, event.clientY - pressed.y) < 12 && figures.get(pressed.id)?.person.selectable) onPick(pressed.id)
    pressed = null
    if (event.pointerType !== "mouse") hover = null
  }
  function leave() { hover = null; pressed = null; onHover(""); dirty = true }
  function lost(event: Event) { event.preventDefault(); onLost() }
  canvas.addEventListener("pointermove", moved)
  canvas.addEventListener("pointerdown", down)
  canvas.addEventListener("pointerup", up)
  canvas.addEventListener("pointerleave", leave)
  canvas.addEventListener("pointercancel", leave)
  canvas.addEventListener("webglcontextlost", lost)
  const observer = new ResizeObserver(() => {
    width = canvas.clientWidth; height = canvas.clientHeight
    if (!width || !height) return
    renderer.setSize(width, height, false)
    const aspect = width / height
    const horizontal = Math.max(12.3, 9.6 * aspect)
    camera.left = -horizontal; camera.right = horizontal
    camera.top = horizontal / aspect; camera.bottom = -horizontal / aspect
    positionCamera()
    dirty = true
  })
  observer.observe(canvas)
  const worldPoint = new THREE.Vector3()
  const projected: Record<string, { x: number; y: number }> = {}
  function animate(time: number) {
    if (disposed) return
    frame = requestAnimationFrame(animate)
    const dt = lastTime ? Math.min((time - lastTime) / 1000, .05) : 0
    lastTime = time
    if (document.hidden || !width || !height) return
    const moving = !paused && !reduced
    if (moving) elapsed += dt
    // Cap display updates at 30 fps; paused/reduced scenes render only on changes.
    if ((!moving && !dirty) || time - lastDraw < 1000 / 30) return
    lastDraw = time
    let index = 0
    for (const [id, item] of figures) {
      const targeted = hover === id || keyboardFocus === id
      if (moving && !targeted) {
        const t = elapsed * .4 + index * 1.9
        item.x = item.homeX + Math.sin(t) * .23
        item.z = item.homeZ + Math.cos(t * .8) * .22
      }
      item.root.position.x = item.x; item.root.position.z = item.z
      const talking = state.talking.includes(id)
      const pair = state.pairs.find(([a, b]) => a === id || b === id)
      const partner = pair ? figures.get(pair[0] === id ? pair[1] : pair[0]) : null
      const facing = partner ? Math.atan2(partner.x - item.x, partner.z - item.z) : azimuth + Math.sin(index * 2) * .25
      item.figure.rotation.y = facing + (moving ? Math.sin(elapsed * (talking ? 3 : .85) + index) * (talking ? .1 : .035) : 0)
      if (moving) item.celebration = Math.max(0, item.celebration - dt * 2)
      item.figure.position.y = .12 + (moving ? Math.sin(elapsed * 2 + index) * .025 + Math.abs(Math.sin(item.celebration * 8)) * item.celebration * .14 : 0)
      item.figure.rotation.z = moving && talking ? Math.sin(elapsed * 2.8) * .035 : 0
      item.ring.scale.setScalar(targeted ? 1.16 : 1)
      worldPoint.set(item.x, 2, item.z).project(camera)
      projected[id] = { x: (worldPoint.x * .5 + .5) * width, y: (-worldPoint.y * .5 + .5) * height }
      index++
    }
    for (const object of pairLines.children) {
      const line = object as THREE.Line
      const source = figures.get(line.userData.source), target = figures.get(line.userData.target)
      if (!source || !target) continue
      const position = line.geometry.getAttribute("position") as THREE.BufferAttribute
      position.setXYZ(0, source.x, .6, source.z); position.setXYZ(1, target.x, .6, target.z)
      position.needsUpdate = true
      line.geometry.computeBoundingSphere()
    }
    renderer.render(scene, camera)
    canvas.dataset.rendered = "true"
    canvas.dataset.drawCalls = String(renderer.info.render.calls)
    canvas.dataset.triangles = String(renderer.info.render.triangles)
    // Projected positions support end-to-end hit testing without depending on a
    // particular viewport or inspecting internal Three.js scene objects.
    canvas.dataset.targets = JSON.stringify(projected)
    canvas.dataset.factions = JSON.stringify(Object.fromEntries([...figures].map(([id, item]) => [id, item.person.team])))
    canvas.dataset.motion = reduced ? "reduced" : paused ? "paused" : "running"
    dirty = false
  }
  frame = requestAnimationFrame(animate)
  return {
    update,
    pause(value) { paused = value; dirty = true },
    rotate(direction) { azimuth += direction * .28; positionCamera(); dirty = true },
    zoom(direction) { zoom = THREE.MathUtils.clamp(zoom + direction * .12, .8, 1.45); positionCamera(); dirty = true },
    focus(id) { keyboardFocus = id; dirty = true },
    dispose() {
      disposed = true
      cancelAnimationFrame(frame); observer.disconnect()
      preference.removeEventListener("change", preferenceChanged)
      canvas.removeEventListener("pointermove", moved); canvas.removeEventListener("pointerdown", down)
      canvas.removeEventListener("pointerup", up); canvas.removeEventListener("pointerleave", leave)
      canvas.removeEventListener("pointercancel", leave); canvas.removeEventListener("webglcontextlost", lost)
      const materials = new Set<THREE.Material>(), geometries = new Set<THREE.BufferGeometry>()
      scene.traverse(object => {
        if (object instanceof THREE.Mesh || object instanceof THREE.Line) {
          geometries.add(object.geometry)
          for (const material of Array.isArray(object.material) ? object.material : [object.material]) materials.add(material)
        }
      })
      geometries.forEach(geometry => geometry.dispose()); materials.forEach(material => material.dispose())
      sun.shadow.dispose(); renderer.dispose(); renderer.forceContextLoss()
    },
  }
}
