import styles from "./round.module.css"

interface Message {
  role: "user" | "assistant"
  text: string
}

export interface RoundState {
  roundNumber: number
  roundState: {
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
    agentsCompleted: boolean
  }
}

interface RoundProps {
  state: RoundState
}

export default function Round({ state }: RoundProps) {
  return (
    <div className={styles.round}>
      <h1>Round {state.roundNumber}</h1>
    </div>
  )
}
