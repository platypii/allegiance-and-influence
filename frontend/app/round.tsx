import styles from "./round.module.css"

interface Message {
  role: "user" | "assistant"
  text: string
}

export interface RoundState {
  round_number: number
  current_agents: string[]
  round_state: {
    player1: {
      choose: string | null
      messages: Message[]
      doneTalking: boolean
    }
    player2: {
      choose: string | null
      messages: Message[]
      doneTalking: boolean
    }
    agents_complete: boolean
  }
}

interface RoundProps {
  state: RoundState
}

export default function Round({ state }: RoundProps) {
  return (
    <div className={styles.round}>
      <h1>
        Round {state.round_number}
        {!state.round_state?.agents_complete && <div className={styles.spinner} />}
      </h1>
    </div>
  )
}
