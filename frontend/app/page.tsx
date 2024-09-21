"use client"

import styles from "./page.module.css"
import Welcome from "./welcome"
import Panel from "./panel"
import ForceGraph, { Edge } from "./forcegraph"
import { Node } from "./forcegraph"

const nodes: Node[] = [
  {
    id: '1',
    x: 100,
    y: 100,
    vx: 0,
    vy: 0,
    element: <div style={{ width: 50, height: 50, background: 'red', borderRadius: '50%' }} />,
  },
  {
    id: '2',
    x: 300,
    y: 100,
    vx: 0,
    vy: 0,
    element: <div style={{ width: 50, height: 50, background: 'blue', borderRadius: '50%' }} />,
  },
  {
    id: '3',
    x: 200,
    y: 300,
    vx: 0,
    vy: 0,
    element: <div style={{ width: 50, height: 50, background: 'green', borderRadius: '50%' }} />,
  },
]

// Define your edges
const edges: Edge[] = [
  { source: '1', target: '2' },
  { source: '2', target: '3' },
  { source: '3', target: '1' },
]

export default function Home() {
  return (
    <div className={styles.page}>
      <Panel />
      <main className={styles.main}>
        <ForceGraph
          nodes={nodes}
          edges={edges}
          width={400}
          height={400}
        />
        <Welcome />
      </main>
    </div>
  )
}
