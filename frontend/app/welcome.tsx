import styles from "./welcome.module.css"

interface WelcomeProps {
  setPlayerName: (name: string) => void
}

export default function Welcome({ setPlayerName }: WelcomeProps) {
  function clickPlayer1() {
    setPlayerName("player_red")
  }
  function clickPlayer2() {
    setPlayerName("player_blue")
  }

  return (
    <div className={styles.welcome}>
      <h1>Allegiance & Influence</h1>
      <sub>A game of human-machine influence</sub>
      
      <div className={styles.choose}>
        <button style={{ color: '#d11' }} onClick={clickPlayer1}>Player 1</button>
        <button style={{ color: '#11e' }} onClick={clickPlayer2}>Player 2</button>
      </div>
    </div>
  )
}
