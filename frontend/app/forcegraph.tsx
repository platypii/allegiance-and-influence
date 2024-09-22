import React, { useEffect, useRef, useState } from 'react'
import styles from "./graph.module.css"

export interface GraphNode {
  id: string
  x: number
  y: number
  element: React.ReactElement
}

interface Node extends GraphNode {
  vx: number
  vy: number
}

export interface Edge {
  source: string
  target: string
}

interface ForceGraphProps {
  nodes: GraphNode[]
  edges: Edge[]
  // Optional simulation parameters
  chargeStrength?: number
  linkDistance?: number
  friction?: number
}

export default function ForceGraph({
  nodes: initialNodes,
  edges,
  chargeStrength = -30,
  linkDistance = 100,
  friction = 0.9,
}: ForceGraphProps) {
  const [nodes, setNodes] = useState<Node[]>(() =>
    initialNodes.map(node => ({ ...node, vx: 0, vy: 0 }))
  )
  const animationRef = useRef<number | null>(null)
  const graphRef = useRef<HTMLDivElement>(null)

  // Create a map for quick node lookup
  const nodeMap = useRef<Map<string, Node>>(new Map())

  const width = graphRef.current?.clientWidth || 800
  const height = graphRef.current?.clientHeight || 600

  useEffect(() => {
    nodeMap.current = new Map(nodes.map(node => [node.id, node]))
  }, [nodes])

  useEffect(() => {
    const simulate = () => {
      // Apply forces
      nodes.forEach(node => {
        // Initialize forces
        let fx = 0
        let fy = 0

        // Charge force (repulsion)
        nodes.forEach(other => {
          if (node.id !== other.id) {
            const dx = node.x - other.x
            const dy = node.y - other.y
            const distance = Math.sqrt(dx * dx + dy * dy) || 1
            const force = chargeStrength / (distance * distance)
            fx += (dx / distance) * force
            fy += (dy / distance) * force
          }
        })

        // Link force (attraction)
        edges.forEach(edge => {
          if (edge.source === node.id || edge.target === node.id) {
            const otherId = edge.source === node.id ? edge.target : edge.source
            const other = nodeMap.current.get(otherId)
            if (other) {
              const dx = other.x - node.x
              const dy = other.y - node.y
              const distance = Math.sqrt(dx * dx + dy * dy) || 1
              const force = (distance - linkDistance) * 0.1
              fx += (dx / distance) * force
              fy += (dy / distance) * force
            }
          }
        })

        // Update velocity
        node.vx = (node.vx + fx) * friction
        node.vy = (node.vy + fy) * friction

        // Update position
        node.x += node.vx
        node.y += node.vy

        // Boundary conditions
        node.x = Math.max(0, Math.min(width, node.x))
        node.y = Math.max(0, Math.min(height, node.y))
      })

      setNodes([...nodes])
      animationRef.current = requestAnimationFrame(simulate)
    }

    animationRef.current = requestAnimationFrame(simulate)
    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current)
    }
  }, [nodes, edges, chargeStrength, linkDistance, friction, width, height])

  return (
    <div
      className={styles.graph}
      ref={graphRef}
    >
      {/* Render edges as SVG lines */}
      <svg
        className={styles.edges}
        width={width}
        height={height}
        style={{ position: 'absolute', top: 0, left: 0, pointerEvents: 'none' }}
      >
        {edges.map((edge, index) => {
          const source = nodes.find(node => node.id === edge.source)
          const target = nodes.find(node => node.id === edge.target)
          if (source && target) {
            return (
              <line
                key={index}
                x1={source.x}
                y1={source.y}
                x2={target.x}
                y2={target.y}
                stroke="#999"
                strokeWidth={1}
              />
            )
          }
          return null
        })}
      </svg>

      {/* Render nodes as positioned elements */}
      {nodes.map(node => (
        <div
          className={styles.node}
          key={node.id}
          style={{ left: node.x, top: node.y }}
        >
          {node.element}
        </div>
      ))}
    </div>
  )
}
