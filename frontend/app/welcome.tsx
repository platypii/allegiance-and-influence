import styles from "./welcome.module.css"

interface WelcomeProps {
  setPlayerName: (name: 'player_red' | 'player_blue') => void
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
      <img src="/images/splash_logo.jpg" alt="Allegiance & Influence" />
      
      <div className={styles.choose}>
        <button style={{ color: '#ef8585' }} onClick={clickPlayer1}>Player 1</button>
        <button style={{ color: '#8484e9' }} onClick={clickPlayer2}>Player 2</button>
      </div>
    </div>
  )
}
