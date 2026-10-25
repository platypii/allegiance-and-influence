import styles from "./welcome.module.css"
import type { Game } from "./client"

export default function Endgame({ game, onClose }: { game: Game; onClose: () => void }) {
  return <div className={styles.welcome}>
    <section className={`${styles.setup} ${styles.result}`} aria-label="Game result">
      <img src={`/images/agents/${game.winner === "tie" ? "albert_einstein" : game.winner}.jpg`} alt="" width={120} height={120} />
      <p className="eyebrow muted">The final allegiance</p>
      <h1>{game.winner === "tie" ? "A shared victory — it’s a tie!" : `${game.winner === "player_red" ? "Red" : "Blue"} wins!`}</h1>
      <p>Final score: Red {game.scores.player_red} · Blue {game.scores.player_blue}</p>
      <p className="muted">The room has chosen. Revisit the conversations and see how influence spread.</p>
      <div className={styles.resultActions}><button className="primary" onClick={onClose}>Review final board</button><a className="buttonLink" href="/">New game</a></div>
    </section>
  </div>
}
