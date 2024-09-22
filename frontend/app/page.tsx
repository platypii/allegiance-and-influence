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
import Round, { RoundState } from "./round"

export default function Home() {
  const [chatWith, setChatWith] = useState<Character | undefined>()
  const [state, setState] = useState<RoundState>({
    round_number: 1,
    current_agents: [],
    round_state: {
      player1: {
        choose: null,
        messages: [],
        doneTalking: false,
      },
      player2: {
        choose: null,
        messages: [],
        doneTalking: false,
      },
      agents_complete: false,
    },
  })

  function clickNode(id: string) {
    const character = characters.find(character => character.UID === id)
    setChatWith(chatWith => chatWith?.UID === id ? undefined : character)
  }

  useEffect(() => {
    const stateRef = ref(database, '/current_state')
    onValue(stateRef, (snapshot) => {
      const state = snapshot.val()
      console.log("Data updated", state)
      setState(state)
    })
  }, [])

  const nodes: GraphNode[] = state?.current_agents?.map((id, i) => {
    const character = characters.find(character => character.UID === id)
    if (!character) throw new Error(`Character not found: ${id}`)
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
          opacity: 0.3,
          mixBlendMode: "multiply",
        }} />
      </div>,
    }
  }) || []
  console.log("Nodes", nodes)

  // Make random connections, at most one connection per person
  const edges: Edge[] = randomEdges(characters.map(character => character.UID), 10)

  const redCount = nodes?.filter(node => node.team < 0)?.length
  const blueCount = nodes?.filter(node => node.team > 0)?.length

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
        {state && <Round state={state} />}
      </main>
    </div>
  )
}
