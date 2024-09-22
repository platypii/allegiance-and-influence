"use client"

import styles from "./page.module.css"
import Welcome from "./welcome"
import Panel from "./panel"
import ForceGraph, { Edge } from "./forcegraph"
import { GraphNode } from "./forcegraph"
import { useState } from "react"
import characters from "./characters.json"
import { randomEdges } from "./utils"
import { teamColor } from "./teamColor"

export default function Home() {
  const [chatWith, setChatWith] = useState<string | undefined>()

  function clickNode(id: string) {
    setChatWith(chatWith => chatWith === id ? undefined : id)
  }

  const nodes: GraphNode[] = characters.map((character, i) => {
    const team = Math.random() * 2 - 1
    // scale -1 red to 0 grey to 1 blue
    const borderColor = teamColor(team)
    return {
      id: character.UID,
      x: Math.random() * 800,
      y: Math.random() * 600,
      team,
      element: <div
        onClick={() => clickNode(character.UID)}
        style={{ borderColor }}>
        <img src={`/images/agents/${character.UID}.jpg`} alt={character.Character} />
        <div style={{
          position: "absolute",
          bottom: 0,
          top: 0,
          left: 0,
          right: 0,
          backgroundColor: borderColor,
          opacity: 0.4,
          mixBlendMode: "multiply",
        }} />
      </div>,
    }
  })

  // Make random connections, at most one connection per person
  const edges: Edge[] = randomEdges(characters.map(character => character.UID), 10)

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
