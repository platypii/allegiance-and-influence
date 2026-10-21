"use client"

import React, { useEffect, useRef, useState } from "react"
import styles from "./graph.module.css"

export interface GraphNode { id: string; team: number; element: React.ReactElement }
interface Node extends GraphNode { x: number; y: number; vx: number; vy: number }
export interface Edge { source: string; target: string }

export default function ForceGraph({ nodes: initialNodes, edges }: { nodes: GraphNode[]; edges: Edge[] }) {
  const graphRef = useRef<HTMLDivElement>(null)
  const simulation = useRef<Node[]>([])
  const [nodes, setNodes] = useState<Node[]>([])
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 })

  useEffect(() => {
    const observer = new ResizeObserver(entries => {
      const { width, height } = entries[0].contentRect
      setDimensions({ width, height })
    })
    if (graphRef.current) observer.observe(graphRef.current)
    return () => observer.disconnect()
  }, [])

  useEffect(() => {
    const previous = new Map(simulation.current.map(node => [node.id, node]))
    simulation.current = initialNodes.map((node, i) => {
      const old = previous.get(node.id)
      const angle = i * 2.399963
      return { ...node, x: old?.x ?? Math.cos(angle) * 170, y: old?.y ?? Math.sin(angle) * 170, vx: old?.vx ?? 0, vy: old?.vy ?? 0 }
    })
    setNodes([...simulation.current])
  }, [initialNodes])

  useEffect(() => {
    const halfWidth = Math.max(0, dimensions.width / 2 - 35)
    const halfHeight = Math.max(0, dimensions.height / 2 - 35)
    for (const node of simulation.current) {
      node.x = Math.max(-halfWidth, Math.min(halfWidth, node.x))
      node.y = Math.max(-halfHeight, Math.min(halfHeight, node.y))
    }
    setNodes([...simulation.current])
  }, [dimensions])

  useEffect(() => {
    let frame = 0
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches
    const simulate = () => {
      const current = simulation.current
      const byId = new Map(current.map(node => [node.id, node]))
      for (const node of current) {
        let fx = 0, fy = 0
        for (const other of current) {
          if (other.id === node.id) continue
          const dx = node.x - other.x, dy = node.y - other.y
          const distance = Math.hypot(dx, dy) || 1
          const force = Math.min(10, 400 / (distance * distance))
          fx += dx / distance * force
          fy += dy / distance * force
        }
        for (const edge of edges) {
          if (edge.source !== node.id && edge.target !== node.id) continue
          const other = byId.get(edge.source === node.id ? edge.target : edge.source)
          if (!other) continue
          const dx = other.x - node.x, dy = other.y - node.y
          const distance = Math.hypot(dx, dy) || 1
          const force = (distance - 80) * 0.004
          fx += dx / distance * force
          fy += dy / distance * force
        }
        const distance = Math.hypot(node.x, node.y) || 1
        fx += -node.x / distance * 0.1 + node.team * 0.05
        fy += -node.y / distance * 0.1
        node.vx = (node.vx + fx) * 0.9
        node.vy = (node.vy + fy) * 0.9
        const halfWidth = Math.max(0, dimensions.width / 2 - 35)
        const halfHeight = Math.max(0, dimensions.height / 2 - 35)
        node.x = Math.max(-halfWidth, Math.min(halfWidth, node.x + node.vx))
        node.y = Math.max(-halfHeight, Math.min(halfHeight, node.y + node.vy))
      }
      setNodes([...current])
      frame = requestAnimationFrame(simulate)
    }
    if (!reducedMotion) frame = requestAnimationFrame(simulate)
    return () => cancelAnimationFrame(frame)
  }, [edges, dimensions])

  const byId = new Map(nodes.map(node => [node.id, node]))
  return <div className={styles.graph} ref={graphRef} aria-label="Influence board">
    <svg className={styles.edges} width={dimensions.width} height={dimensions.height}>
      {edges.map(edge => {
        const source = byId.get(edge.source), target = byId.get(edge.target)
        if (!source || !target) return null
        return <line key={`${edge.source}:${edge.target}`}
          x1={source.x + dimensions.width / 2} y1={source.y + dimensions.height / 2}
          x2={target.x + dimensions.width / 2} y2={target.y + dimensions.height / 2}
          stroke="#86551f" strokeWidth={Math.max(3, Math.min(8, 800 / (Math.hypot(target.x - source.x, target.y - source.y) + 1)))} />
      })}
    </svg>
    {nodes.map(node => <div className={styles.node} key={node.id} style={{ left: node.x + dimensions.width / 2, top: node.y + dimensions.height / 2 }}>{node.element}</div>)}
  </div>
}
