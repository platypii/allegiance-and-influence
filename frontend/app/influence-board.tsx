"use client"

import React, { useEffect, useRef, useState } from "react"
import styles from "./influence-board.module.css"

export interface GraphNode { id: string; team: number; element: React.ReactElement }
export interface Edge { source: string; target: string }

/** Stable portrait layout; relationship lines follow actual image centers at every size. */
export default function InfluenceBoard({ nodes, edges }: { nodes: GraphNode[]; edges: Edge[] }) {
  const graphRef = useRef<HTMLDivElement>(null)
  const [positions, setPositions] = useState<Record<string, { x: number; y: number }>>({})
  useEffect(() => {
    const graph = graphRef.current
    if (!graph) return
    const measure = () => {
      const bounds = graph.getBoundingClientRect()
      const next: Record<string, { x: number; y: number }> = {}
      for (const element of graph.querySelectorAll<HTMLElement>("[data-node]")) {
        const image = element.querySelector("img")?.getBoundingClientRect()
        if (image) next[element.dataset.node!] = { x: image.left + image.width / 2 - bounds.left, y: image.top + image.height / 2 - bounds.top }
      }
      setPositions(next)
    }
    const observer = new ResizeObserver(measure)
    observer.observe(graph)
    for (const element of graph.querySelectorAll("[data-node]")) observer.observe(element)
    measure()
    return () => observer.disconnect()
  }, [nodes])

  return <div className={styles.graph} ref={graphRef} aria-label="Influence board">
    <svg className={styles.edges} width="100%" height="100%" aria-hidden="true">
      {edges.map(edge => {
        const source = positions[edge.source], target = positions[edge.target]
        if (!source || !target) return null
        return <line key={`${edge.source}:${edge.target}`} x1={source.x} y1={source.y} x2={target.x} y2={target.y} stroke="var(--brass)" strokeWidth={2} strokeOpacity={0.45} />
      })}
    </svg>
    {nodes.map(node => <div className={styles.node} data-node={node.id} key={node.id}>{node.element}</div>)}
  </div>
}
