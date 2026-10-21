import styles from "./round.module.css"
import characters from "./characters"
import { teamColor } from "./teamColor"
import type { Game } from "./client"

export default function Round({ game }: { game: Game }) {
  const latest = game.history.at(-1)
  return <aside className={styles.round} aria-label="Round details">
    <h1>Round {game.round_number} of {game.config.num_rounds}</h1>
    <div>{game.agents.length} characters</div>
    <sub>{game.phase.replaceAll("_", " ")}</sub>
    {latest && <><h2>Round {latest.round_number} recap</h2>{latest.summaries.map((summary, i) => <div className={styles.pairing} key={i}>
      <div className={styles.pair}>{summary.pair.map(id => <div key={id}>
        <img src={`/images/agents/${id}.jpg`} alt="" style={{ borderColor: teamColor(game.agents.find(a => a.UID === id)?.side || (id === "player_red" ? -1 : id === "player_blue" ? 1 : 0)) }} />
        {characters.find(c => c.UID === id)?.Character}
      </div>)}</div><div>{summary.text}</div>
    </div>)}</>}
  </aside>
}
