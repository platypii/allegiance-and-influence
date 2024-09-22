import styles from "./welcome.module.css"

interface EndgameProps {
  playerName: 'player_red' | 'player_blue'
}

export default function Endgame({ playerName }: EndgameProps) {
  return (
    <div className={styles.welcome}>
      <img src={`/images/win/${playerName}.png`} alt="Allegiance & Influence" width={500} />
      <div className={styles.win} style={{ color: playerName === 'player_red' ? '#ef8585' : '#8484e9' }}>
        {playerName === 'player_red' ? 'Red' : 'Blue'} Wins!
      </div>
    </div>
  )
}
