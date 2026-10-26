"use client"

import React, { useEffect, useRef, useState } from "react"
import { Body, stepSwarm } from "./swarm"
import styles from "./influence-board.module.css"

export interface GraphNode { id: string; name: string; team: number; selectable: boolean; onSelect: () => void; element: React.ReactElement }
export interface Edge { source: string; target: string }

export default function InfluenceBoard({ nodes, edges }: { nodes: GraphNode[]; edges: Edge[] }) {
  const graphRef = useRef<HTMLDivElement>(null)
  const latest = useRef({ nodes, edges })
  const pausedRef = useRef(false)
  const hovered = useRef(false)
  const focused = useRef(false)
  const [paused, setPaused] = useState(false)
  const [reduced, setReduced] = useState(false)
  const rosterKey = nodes.map(node => node.id).join(":")
  useEffect(() => { latest.current = { nodes, edges } }, [nodes, edges])
  useEffect(() => { pausedRef.current = paused }, [paused])

  useEffect(() => {
    const graph = graphRef.current
    if (!graph) return
    const preference = window.matchMedia("(prefers-reduced-motion: reduce)")
    // Cache change events: reading MediaQueryList.matches in every animation
    // frame can consume a pending Chromium preference change before its event.
    let prefersReducedMotion = preference.matches
    const updatePreference = (event: MediaQueryListEvent) => {
      prefersReducedMotion = event.matches
      setReduced(event.matches)
    }
    setReduced(prefersReducedMotion)
    preference.addEventListener("change", updatePreference)
    let bodies: (Body & { element: HTMLElement; imageX: number; imageY: number })[] = []
    let width = 0, height = 0, frame = 0, previousTime = 0, elapsed = 0
    let paintedEdges: Edge[] | null = null
    const paint = () => {
      for (const body of bodies) body.element.style.transform = `translate(${body.x - body.homeX}px, ${body.y - body.homeY}px)`
      const byId = new Map(bodies.map(body => [body.id, body]))
      for (const line of graph.querySelectorAll<SVGLineElement>("line[data-source]")) {
        const source = byId.get(line.dataset.source!), target = byId.get(line.dataset.target!)
        if (!source || !target) continue
        line.setAttribute("x1", String(source.x + source.imageX))
        line.setAttribute("y1", String(source.y + source.imageY))
        line.setAttribute("x2", String(target.x + target.imageX))
        line.setAttribute("y2", String(target.y + target.imageY))
      }
    }
    const measure = () => {
      const elements = [...graph.querySelectorAll<HTMLElement>("[data-node]")]
      for (const element of elements) element.style.transform = ""
      const bounds = graph.getBoundingClientRect()
      width = bounds.width; height = bounds.height
      bodies = elements.flatMap(element => {
        const button = element.querySelector("button")?.getBoundingClientRect()
        const image = element.querySelector("img")?.getBoundingClientRect()
        if (!button || !image) return []
        const id = element.dataset.node!
        const x = button.left + button.width / 2 - bounds.left, y = button.top + button.height / 2 - bounds.top
        return [{ id, team: 0, x, y, homeX: x, homeY: y, width: button.width, height: button.height,
          vx: 0, vy: 0, element, imageX: image.left + image.width / 2 - bounds.left - x,
          imageY: image.top + image.height / 2 - bounds.top - y }]
      })
      paint()
    }
    const animate = (time: number) => {
      const dt = previousTime ? Math.min(2, (time - previousTime) / (1000 / 60)) : 1
      previousTime = time
      const moving = !prefersReducedMotion && !pausedRef.current && !hovered.current && !focused.current && !document.hidden
      if (moving) {
        elapsed += dt / 60
        const teams = new Map(latest.current.nodes.map(node => [node.id, node.team]))
        for (const body of bodies) body.team = teams.get(body.id) || 0
        stepSwarm(bodies, latest.current.edges, width, height, elapsed, dt)
      }
      if (moving || paintedEdges !== latest.current.edges) {
        paint() // New pairing lines also get coordinates while paused/reduced.
        paintedEdges = latest.current.edges
      }
      frame = requestAnimationFrame(animate)
    }
    const observer = new ResizeObserver(measure)
    observer.observe(graph)
    for (const element of graph.querySelectorAll("[data-node]")) observer.observe(element)
    measure()
    frame = requestAnimationFrame(animate)
    return () => { observer.disconnect(); cancelAnimationFrame(frame); preference.removeEventListener("change", updatePreference) }
  }, [rosterKey])

  return <div className={styles.graph} ref={graphRef} aria-label="Influence board" data-motion={reduced ? "reduced" : paused ? "paused" : "running"}>
    <div className={styles.motionControl}>{reduced ? <span>Reduced motion</span> : <button type="button" aria-pressed={paused} onClick={() => { pausedRef.current = !paused; setPaused(!paused) }}>{paused ? "Resume board motion" : "Pause board motion"}</button>}</div>
    <svg className={styles.edges} width="100%" height="100%" aria-hidden="true">
      {edges.map(edge => <line key={`${edge.source}:${edge.target}`} data-source={edge.source} data-target={edge.target} stroke="var(--brass)" strokeWidth={2} strokeOpacity={0.55} />)}
    </svg>
    {nodes.map(node => <div className={styles.node} data-node={node.id} key={node.id}
      onPointerEnter={event => { if (event.pointerType === "mouse") hovered.current = true }}
      onPointerLeave={() => { hovered.current = false }}
      onPointerDown={() => { hovered.current = true }}
      onPointerUp={() => { hovered.current = false }}
      onPointerCancel={() => { hovered.current = false }}
      onFocusCapture={() => { focused.current = true }}
      onBlurCapture={() => { focused.current = false }}>{node.element}</div>)}
  </div>
}
