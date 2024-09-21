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
  velocityThreshold?: number // New prop for velocity threshold
}

export default function ForceGraph({
  nodes: initialNodes,
  edges,
  chargeStrength = -30,
  linkDistance = 100,
  friction = 0.9,
  velocityThreshold = 0.1, // Default threshold value
}: ForceGraphProps) {
  const [nodes, setNodes] = useState<Node[]>(() =>
    initialNodes.map(node => ({ ...node, vx: 0, vy: 0 }))
  )
  const animationRef = useRef<number | null>(null)
  const graphRef = useRef<HTMLDivElement>(null)

  // Create a map for quick node lookup
  const nodeMap = useRef<Map<string, Node>>(new Map())

  // Dimensions of the graph container
  const [dimensions, setDimensions] = useState<{ width: number; height: number }>({
    width: 800,
    height: 600,
  })

  // Update nodeMap whenever nodes change
  useEffect(() => {
    nodeMap.current = new Map(nodes.map(node => [node.id, node]))
  }, [nodes])

  // Update dimensions on mount and when the window resizes
  useEffect(() => {
    const updateDimensions = () => {
      if (graphRef.current) {
        setDimensions({
          width: graphRef.current.clientWidth,
          height: graphRef.current.clientHeight,
        })
      }
    }

    updateDimensions()
    window.addEventListener('resize', updateDimensions)
    return () => {
      window.removeEventListener('resize', updateDimensions)
    }
  }, [])

  useEffect(() => {
    const simulate = () => {
      let shouldContinue = false // Flag to determine if animation should continue

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

        // Calculate velocity magnitude
        const velocity = Math.sqrt(node.vx * node.vx + node.vy * node.vy)

        if (velocity >= velocityThreshold) {
          shouldContinue = true // At least one node is still moving
        } else {
          // Stop the node by setting its velocity to zero
          node.vx = 0
          node.vy = 0
        }

        // Update position
        node.x += node.vx
        node.y += node.vy

        // Boundary conditions
        node.x = Math.max(0, Math.min(dimensions.width, node.x))
        node.y = Math.max(0, Math.min(dimensions.height, node.y))
      })

      setNodes([...nodes])

      if (shouldContinue) {
        animationRef.current = requestAnimationFrame(simulate)
      } else {
        // All nodes have velocities below the threshold; stop the animation
        animationRef.current = null
      }
    }

    // Start the simulation
    if (animationRef.current === null) {
      animationRef.current = requestAnimationFrame(simulate)
    }

    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current)
    }
  }, [nodes, edges, chargeStrength, linkDistance, friction, dimensions, velocityThreshold])

  return (
    <div className={styles.graph} ref={graphRef}>
      {/* Render edges as SVG lines */}
      <svg
        className={styles.edges}
        width={dimensions.width}
        height={dimensions.height}
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
                stroke="#333"
                strokeWidth={2}
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
