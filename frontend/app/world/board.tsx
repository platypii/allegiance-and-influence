"use client"

import { useEffect, useRef, useState } from "react"
import InfluenceBoard, { Edge, GraphNode } from "../influence-board"
import type { WorldScene, WorldState } from "./scene"
import styles from "./world.module.css"

export default function WorldBoard({ nodes, edges, talking }: { nodes: GraphNode[]; edges: Edge[]; talking: string[] }) {
  const canvas = useRef<HTMLCanvasElement>(null)
  const scene = useRef<WorldScene | null>(null)
  const current = useRef(nodes)
  current.current = nodes
  const [failed, setFailed] = useState(false)
  const [ready, setReady] = useState(false)
  const [paused, setPaused] = useState(false)
  const [hover, setHover] = useState("")
  const rosterKey = nodes.map(node => node.id).join(":")
  const state: WorldState = { people: nodes.map(({ id, name, team, selectable }) => ({ id, name, team, selectable })), pairs: edges.map(({ source, target }) => [source, target]), talking }
  const latest = useRef(state)
  latest.current = state
  useEffect(() => { scene.current?.update(state) }, [nodes, edges, talking]) // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    let disposed = false
    if (!canvas.current || failed) return
    setReady(false)
    import("./scene").then(({ createWorld }) => {
      if (disposed || !canvas.current) return
      try {
        scene.current = createWorld(canvas.current, latest.current, id => {
          const node = current.current.find(node => node.id === id)
          if (node?.selectable) node.onSelect()
        }, setHover, () => setFailed(true))
        scene.current.pause(paused)
        setReady(true)
      } catch { setFailed(true) }
    }).catch(() => { if (!disposed) setFailed(true) })
    return () => { disposed = true; scene.current?.dispose(); scene.current = null }
  }, [rosterKey, failed]) // eslint-disable-line react-hooks/exhaustive-deps

  if (failed) return <><p className={styles.fallback} role="status">3D is unavailable in this browser. You can keep playing on the illustrated board.</p><InfluenceBoard nodes={nodes} edges={edges} /></>
  return <div className={styles.world}>
    <div className={styles.stage}>
      <div className={styles.sceneTitle}><span className="eyebrow">The art of persuasion</span><strong>The Grand Gathering</strong><span>Every voice can change the world.</span></div>
      <canvas ref={canvas} className={styles.canvas} aria-label="3D gathering with selectable character miniatures" />
      {!ready && <p className={styles.loading} role="status">Setting the scene…</p>}
      <div className={styles.camera} aria-label="Camera controls">
        <button aria-label="Rotate scene left" disabled={!ready} onClick={() => scene.current?.rotate(-1)}>↶</button>
        <button aria-label="Rotate scene right" disabled={!ready} onClick={() => scene.current?.rotate(1)}>↷</button>
        <span />
        <button aria-label="Zoom out" disabled={!ready} onClick={() => scene.current?.zoom(-1)}>−</button>
        <button aria-label="Zoom in" disabled={!ready} onClick={() => scene.current?.zoom(1)}>+</button>
        <span />
        <button aria-pressed={paused} disabled={!ready} onClick={() => { scene.current?.pause(!paused); setPaused(!paused) }}>{paused ? "Resume" : "Pause"}</button>
      </div>
      <p className={styles.hover} aria-live="polite">{hover || "Tap a figure or choose from the cast"}</p>
      <span className={styles.preview}>3D art preview</span>
    </div>
    <section className={styles.cast} aria-label="Choose a character">
      <div className={styles.castHeading}><h2>The company</h2><span>{nodes.filter(node => !node.id.startsWith("player_")).length} personalities · one unlikely alliance</span></div>
      <div className={styles.castList}>{nodes.map(node => <div key={node.id} onFocusCapture={() => scene.current?.focus(node.id)} onBlurCapture={() => scene.current?.focus(null)}>{node.element}</div>)}</div>
    </section>
  </div>
}
