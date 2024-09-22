"use client"

import styles from "./page.module.css"
import Welcome from "./welcome"
import Panel from "./panel"
import ForceGraph, { Edge } from "./forcegraph"
import { GraphNode } from "./forcegraph"
import { useEffect, useState } from "react"
import characters, { Character } from "./characters"
import { randomEdges } from "./utils"
import { teamColor } from "./teamColor"
import { database } from "./firebase"
import { onValue, ref } from "firebase/database"

export default function Home() {
  const [chatWith, setChatWith] = useState<Character | undefined>()

  function clickNode(id: string) {
    const character = characters.find(character => character.UID === id)
    setChatWith(chatWith => chatWith?.UID === id ? undefined : character)
  }

  console.log("Firebase initialized", database)
  useEffect(() => {
    // /state
    // {
    //   roundNumber: 3,
    //   roundState: {
    //     player1: {
    //       choose: 'gary'
    //       messages: [{}, {}]
    //       doneTalking: false
    //     },
    //     player2: ...
    //     agentsCompleted: false
    //   }
    const dataRef = ref(database, '/rounders')
    onValue(dataRef, (snapshot) => {
      const rounds = snapshot.val()
      const { agents } = rounds[rounds.length - 1]
      console.log("Data updated", agents)
    })
  }, [])

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
        onClose={() => setChatWith(undefined)}
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
