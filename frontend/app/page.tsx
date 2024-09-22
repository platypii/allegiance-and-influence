"use client"

import styles from "./page.module.css"
import Welcome from "./welcome"
import Panel from "./panel"
import ForceGraph, { Edge } from "./forcegraph"
import { GraphNode } from "./forcegraph"
import { useEffect, useState } from "react"
import characters, { Character } from "./characters"
import { teamColor } from "./teamColor"
import { database } from "./firebase"
import { onValue, ref, update } from "firebase/database"
import Round, { RoundState, RoundType } from "./round"

export default function Home() {
  const [chatWith, setChatWith] = useState<Character | undefined>()
  const [playerName, setPlayerName] = useState<'player_red' | 'player_blue' | undefined>()
  const [state, setState] = useState<RoundState>({
    round_number: 1,
    current_agents: [],
    current_pairing: [],
    round_state: {
      player_red: {
        choose: null,
        messages: [],
        done_talking: false,
      },
      player_blue: {
        choose: null,
        messages: [],
        done_talking: false,
      },
      agents_complete: false,
    },
  })
  const [round, setRound] = useState<RoundType | undefined>()

  function clickNode(id: string) {
    if (!playerName) return
    if (state.round_state[playerName]?.choose) return console.log("Already made a choice")
    if (id.startsWith('player_')) return console.log("Can't choose a player")
    // Set the player's choice
    const dbRef = ref(database, `/current_state/round_state/${playerName}`)
    update(dbRef, { choose: id })
    const character = characters.find(character => character.UID === id)
    setChatWith(character)
  }

  useEffect(() => {
    const stateRef = ref(database, '/current_state')
    const unsubscribe = onValue(stateRef, (snapshot) => {
      const state = snapshot.val()
      console.log("State updated", state)
      setState(state)

      if (!playerName) return
      if (!state?.round_state?.[playerName]) return
      if (state?.round_state?.[playerName].done_talking) return
      const { choose } = state?.round_state[playerName]
      const character = characters.find(character => character.UID === choose)
      if (character) setChatWith(character)

      if (state.round_state.agents_complete) {
        setChatWith(undefined)
      }
    })

    return () => unsubscribe()
  }, [playerName])

  useEffect(() => {
    const roundRef = ref(database, '/rounds')
    const unsubscribe = onValue(roundRef, (snapshot) => {
      const rounds = snapshot.val()
      const round = rounds?.[state.round_number - 1]
      setRound(round)
    })

    return () => unsubscribe()
  }, [state?.round_number])

  const agents = [...(state?.current_agents || []), 'player_red', 'player_blue']
  const nodes: GraphNode[] = agents.map(id => {
    const character = characters.find(character => character.UID === id)
    if (!character) throw new Error(`Character not found: ${id}`)
    // Get score from round
    let team = round?.agents?.[id]?.side || 0
    if (id === 'player_red') team = -1
    if (id === 'player_blue') team = 1
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

  // Make random connections, at most one connection per person
  const edges: Edge[] = state?.current_pairing?.map(([agent1, agent2]) => {
    const source = nodes.find(node => node.id === agent1)
    const target = nodes.find(node => node.id === agent2)
    if (source && target) {
      return {
        source: source.id,
        target: target.id,
      }
    }
    return null
  }).filter(edge => edge !== null) as Edge[] || []

  const redCount = nodes?.filter(node => node.team < 0)?.length
  const blueCount = nodes?.filter(node => node.team > 0)?.length

  const messages = playerName ? state?.round_state?.[playerName]?.messages || [] : []

  const status = playerName ? (state?.round_state?.[playerName]?.choose ? null : 'Select a character to recruit') : null

  return (
    <div className={styles.page}>
      {playerName && <Panel
        playerName={playerName}
        chatWith={chatWith}
        firemessages={messages}
        onClose={() => setChatWith(undefined)}
      />}
      <main className={styles.main}>
        <ForceGraph
          nodes={nodes}
          edges={edges}
        />
        <div className={styles.overlay}>
          <div className={styles.score}>
            <div className={styles.red}>{redCount}</div>
            -
            <div className={styles.blue}>{blueCount}</div>
          </div>
          <div className={playerName === 'player_red' ? styles.red : styles.blue}>
            You Are Player {playerName === 'player_red' ? 'Red' : 'Blue'}
          </div>
        </div>
        {!playerName && <Welcome setPlayerName={setPlayerName} />}
        {state && <Round state={state} round={round} />}
        {status && <div className={styles.status}>{status}</div>}
      </main>
    </div>
  )
}
