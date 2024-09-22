import { useEffect, useState } from "react"
import styles from "./round.module.css"
import { database } from "./firebase"
import { onValue, ref } from "firebase/database"

interface Message {
  role: "user" | "assistant"
  text: string
}

export interface RoundState {
  round_number: number
  current_agents: string[]
  round_state: {
    player_red: {
      choose: string | null
      messages: Message[]
      doneTalking: boolean
    }
    player_blue: {
      choose: string | null
      messages: Message[]
      doneTalking: boolean
    }
    agents_complete: boolean
  }
}

interface Round {
  agents: {[key: string]: {
    current_chat_messages: {
      name?: string
      content: string
    }[]
    side: string
  }}
  current_pairing: [string, string][]
}

interface RoundProps {
  state: RoundState
}

export default function Round({ state }: RoundProps) {
  const [round, setRound] = useState<Round>()

  const statsRound = state.round_state?.agents_complete ? state.round_number : state.round_number - 1
  useEffect(() => {
    // get data from firebase
    if (statsRound >= 0) {
      const roundRef = ref(database, '/rounds')
      onValue(roundRef, (snapshot) => {
        const rounds = snapshot.val()
        const round = rounds?.[statsRound]
        setRound(round)
        console.log("Round data", round)
      })
    }
  }, [])

  return (
    <div className={styles.round}>
      <h1>
        Round {state.round_number}
        {!state.round_state?.agents_complete && <div className={styles.spinner} />}
      </h1>
      <div>{state.current_agents?.length} Agents</div>
      {round && <>
        <h2>Previous Round {statsRound}</h2>
        {round.current_pairing.map(([agent1, agent2], index) => (
          <div className={styles.pairing} key={index}>
            <div>
              <img src={`/images/agents/${agent1}.jpg`} alt={agent1} />
              {round.agents?.[agent1]?.side}
              {agent1}
            </div>
            <div>
              <img src={`/images/agents/${agent2}.jpg`} alt={agent2} />
              {round.agents?.[agent2]?.side}
              {agent2}
            </div>
          </div>
        ))}
      </>}
    </div>
  )
}
