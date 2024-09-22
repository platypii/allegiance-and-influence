"use client"

import styles from "./page.module.css"
import Welcome from "./welcome"
import Panel from "./panel"
import ForceGraph, { Edge } from "./forcegraph"
import { GraphNode } from "./forcegraph"
import { useState } from "react"
import characters from "./characters.json"

export default function Home() {
  const [chatWith, setChatWith] = useState<string | undefined>()

  function clickNode(id: string) {
    setChatWith(chatWith => chatWith === id ? undefined : id)
  }

  const nodes: GraphNode[] = characters.map((character, i) => {
    const team = i % 2 === 0 ? -1 : 1
    // scale -1 red to 0 grey to 1 blue
    const background = teamColor(team)
    return {
      id: character.UID,
      x: Math.random() * 800,
      y: Math.random() * 600,
      team,
      element: <div
        onClick={() => clickNode(character.UID)}
        style={{ background }}>
        {character.Character}
      </div>,
    }
  })

  // Define your edges
  const edges: Edge[] = [
    { source: 'Napoleon', target: 'Einstein' },
  ]

  const redCount = nodes.filter(node => node.team < 0).length
  const blueCount = nodes.filter(node => node.team > 0).length

  return (
    <div className={styles.page}>
      <Panel
        chatWith={chatWith}
      />
      <main className={styles.main}>
        <ForceGraph
          nodes={nodes}
          edges={edges}
        />
        <div className={styles.overlay}>
          <div className={styles.red}>{redCount}</div>
          -
          <div className={styles.blue}>{blueCount}</div>
        </div>
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
