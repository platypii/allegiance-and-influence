"use client"

import React, { useEffect, useRef, useState } from 'react'
import styles from "./graph.module.css"

export interface GraphNode {
  id: string
  team: number
  element: React.ReactElement
}

interface Node extends GraphNode {
  x: number
  y: number
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
  linkForce?: number
  teamForce?: number
  friction?: number
  gravityStrength?: number
}

export default function ForceGraph({
  nodes: initialNodes,
  edges,
  chargeStrength = 400,
  linkDistance = 80,
  linkForce = 0.004,
  teamForce = 0.05,
  friction = 0.9,
  gravityStrength = 0.1, // Default gravity strength
}: ForceGraphProps) {
  const [nodes, setNodes] = useState<Node[]>(() =>
    initialNodes.map(node => ({
      ...node,
      x: Math.random() * 800 - 400,
      y: Math.random() * 600 - 300,
      vx: 0,
      vy: 0
    }))
  )
  const animationRef = useRef<number | null>(null)
  const graphRef = useRef<HTMLDivElement>(null)

  // Create a map for quick node lookup
  const nodeMap = useRef<Map<string, Node>>(new Map())

  // State to handle dynamic width and height
  const [dimensions, setDimensions] = useState<{ width: number; height: number }>({
    width: 800,
    height: 600,
  })

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
    return () => window.removeEventListener('resize', updateDimensions)
  }, [])

  useEffect(() => {
    const nodes = initialNodes.map(node => {
      const existingNode = nodeMap.current.get(node.id)
      return {
        ...node,
        x: existingNode ? existingNode.x : Math.random() * 800 - 400,
        y: existingNode ? existingNode.y : Math.random() * 600 - 300,
        vx: existingNode ? existingNode.vx : 0,
        vy: existingNode ? existingNode.vy : 0,
      }
    })
    setNodes(nodes)
    nodeMap.current = new Map(nodes.map(node => [node.id, node]))
  }, [initialNodes])

  useEffect(() => {
    const simulate = () => {
      // Destructure width and height for easy access
      const { width, height } = dimensions

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
            const clamped = Math.min(10, Math.max(-10, force))
            fx += (dx / distance) * clamped
            fy += (dy / distance) * clamped
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
              const force = (distance - linkDistance) * linkForce
              fx += (dx / distance) * force
              fy += (dy / distance) * force
            }
          }
        })

        // Gravity force towards the center
        const distanceCenter = Math.sqrt(node.x * node.x + node.y * node.y) || 1
        // Normalize the direction and apply gravity strength
        fx += -(node.x / distanceCenter) * gravityStrength
        fy += -(node.y / distanceCenter) * gravityStrength

        // Team force (-1 to left, 1 to right)
        fx += node.team * teamForce

        // Update velocity
        node.vx = (node.vx + fx) * friction
        node.vy = (node.vy + fy) * friction

        if (node.vx > 100 || node.vy > 100) {
          console.log('High velocity', node.vx, fx, node)
        }
        // if (node.vx > 100) node.vx = 10
        // if (node.vx < -10) node.vx = -10
        // if (node.vy > 10) node.vy = 10
        // if (node.vy < -10) node.vy = -10

        // Update position
        node.x += node.vx
        node.y += node.vy

        // Boundary conditions (optional: keep nodes within the viewport)
        node.x = Math.max(-width / 2, Math.min(width / 2, node.x))
        node.y = Math.max(-height / 2, Math.min(height / 2, node.y))

        if (isNaN(node.x) || isNaN(node.y)) {
          console.log('NaN node', node, dimensions)
        }
      })

      setNodes([...nodes])
      animationRef.current = requestAnimationFrame(simulate)
    }

    animationRef.current = requestAnimationFrame(simulate)
    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current)
    }
  }, [nodes, edges, chargeStrength, linkDistance, friction, dimensions, gravityStrength])

  return (
    <div
      className={styles.graph}
      ref={graphRef}
    >
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
            if (isNaN(source.x) || isNaN(source.y)) {
              console.log('NaN source', source, dimensions)
              // source.x = 0
              // source.y = 0
            }
            if (isNaN(target.x) || isNaN(target.y)) {
              console.log('NaN target', source, dimensions)
              // target.x = 0
              // target.y = 0
            }
            const length = Math.sqrt(
              Math.pow(target.x - source.x, 2) + Math.pow(target.y - source.y, 2)
            ) + 1
            const strokeWidth = Math.max(3, Math.min(8, 800 / length))
            return (
              <line
                key={index}
                x1={source.x + 0.5 * dimensions.width}
                y1={source.y + 0.5 * dimensions.height}
                x2={target.x + 0.5 * dimensions.width}
                y2={target.y + 0.5 * dimensions.height}
                stroke="#86551f"
                strokeWidth={strokeWidth}
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
          style={{
            left: node.x + 0.5 * dimensions.width,
            top: node.y + 0.5 * dimensions.height,
          }}
        >
          {node.element}
        </div>
      ))}
    </div>
  )
}
