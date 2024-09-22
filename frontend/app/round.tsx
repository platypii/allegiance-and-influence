import { useEffect, useState } from "react"
import styles from "./round.module.css"
import { database } from "./firebase"
import { onValue, ref } from "firebase/database"
import { teamColor } from "./teamColor"

interface Message {
  name: string
  content: string
}

export interface RoundState {
  round_number: number
  current_agents: string[]
  current_pairing: [string, string][]
  round_state: {
    player_red: {
      choose: string | null
      messages: Message[]
      done_talking: boolean
    }
    player_blue: {
      choose: string | null
      messages: Message[]
      done_talking: boolean
    }
    agents_complete: boolean
  }
}

export interface RoundType {
  agents: {[key: string]: {
    current_chat_messages: {
      name?: string
      content: string
    }[]
    side: number
  }}
  current_pairing: [string, string][]
  pairing_summaries: string[]
}

interface RoundProps {
  state: RoundState
  round?: RoundType
}

export default function Round({ state, round }: RoundProps) {
  const statsRound = state.round_state?.agents_complete ? state.round_number : state.round_number - 1

  return (
    <div className={styles.round}>
      <h1>
        Round {state.round_number ? state.round_number + 1 : 1}
      </h1>
      <div>
        {state.current_agents?.length} Agents
      </div>
      <sub>
        {!state.round_state?.agents_complete && '(in progress)'}
      </sub>
      {round && statsRound >= 0 && <>
        {state.round_number !== statsRound && <h2>Previous Round {statsRound + 1}</h2>}
        {round.current_pairing.map(([agent1, agent2], index) => (
          <div className={styles.pairing} key={index}>
            <div className={styles.pair}>
              <div>
                <img src={`/images/agents/${agent1}.jpg`} alt={agent1} style={{ borderColor: teamColor(round.agents?.[agent1]?.side || 0) }} />
                {agent1}
              </div>
              <div>
                <img src={`/images/agents/${agent2}.jpg`} alt={agent2} style={{ borderColor: teamColor(round.agents?.[agent2]?.side || 0) }} />
                {agent2}
              </div>
            </div>
            <div>{round.pairing_summaries?.[index]}</div>
          </div>
        ))}
      </>}
    </div>
  )
}
