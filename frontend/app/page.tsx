"use client"

import styles from "./page.module.css"
import Welcome from "./welcome"
import Panel from "./panel"
import ForceGraph, { Edge } from "./forcegraph"
import { GraphNode } from "./forcegraph"

const nodes: GraphNode[] = [
  {
    id: 'Napoleon',
    x: 100,
    y: 100,
    team: -1,
  },
  {
    id: 'Einstein',
    x: 300,
    y: 100,
    team: 0,
  },
  {
    id: 'Trump',
    x: 200,
    y: 300,
    team: 0.5, // mostly blue
  },
].map(node => {
  // scale -1 red to 0 grey to 1 blue
  const background = teamColor(node.team)
  return {
    ...node,
    element: <div
      style={{ background }}>
      {node.id}
    </div>,
  }
})

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
        />
        <Welcome />
      </main>
    </div>
  )
}

function teamColor(team: number) {
  const red = [255, 0, 0] // -1: red
  const grey = [128, 128, 128] // 0: grey
  const blue = [0, 0, 255] // 1: blue

  // Interpolate between colors based on the value
  let color
  if (team < 0) {
    // Interpolate between red and grey
    const t = (team + 1) / 1 // Map -1 to 0, and 0 to 1
    color = red.map((c, i) => Math.round(c * (1 - t) + grey[i] * t))
  } else {
    // Interpolate between grey and blue
    const t = team // Map 0 to 0, and 1 to 1
    color = grey.map((c, i) => Math.round(c * (1 - t) + blue[i] * t))
  }

  // Return the color as a CSS rgb string
  return `rgb(${color.join(",")})`
}
