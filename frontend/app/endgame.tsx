import styles from "./welcome.module.css"
import type { Game } from "./client"

export default function Endgame({ game, onClose }: { game: Game; onClose: () => void }) {
  return <div className={styles.welcome}>
    <img src={game.winner === "tie" ? "/images/splash_logo.jpg" : `/images/win/${game.winner}.png`} alt="Allegiance & Influence" width={480} />
    <div className={styles.setup}>
      <h1>{game.winner === "tie" ? "A shared victory — it’s a tie!" : `${game.winner === "player_red" ? "Red" : "Blue"} wins!`}</h1>
      <p>Final score: Red {game.scores.player_red} · Blue {game.scores.player_blue}</p>
      <button onClick={onClose}>Review final board</button> <a href="/">New game</a>
    </div>
  </div>
}
