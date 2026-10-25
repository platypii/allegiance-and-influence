import styles from "./round.module.css"
import characters from "./characters"
import { teamColor } from "./teamColor"
import type { Game } from "./client"

export default function Round({ game }: { game: Game }) {
  const latest = game.history.at(-1)
  return <aside className={styles.round} aria-label="Round details">
    <p className="eyebrow">The balance of influence</p>
    <h2>Round {game.round_number} of {game.config.num_rounds}</h2>
    <div className={styles.meta}><span>{game.agents.length} characters</span><span className={styles.phase}>{game.phase.replaceAll("_", " ")}</span></div>
    {latest && <details open={game.phase === "round_complete" || game.phase === "finished"}><summary>Round {latest.round_number} recap</summary>{latest.summaries.map((summary, i) => <div className={styles.pairing} key={i}>
      <div className={styles.pair}>{summary.pair.map(id => <div key={id}>
        <img src={`/images/agents/${id}.jpg`} alt="" style={{ borderColor: teamColor(game.agents.find(a => a.UID === id)?.side || (id === "player_red" ? -1 : id === "player_blue" ? 1 : 0)) }} />
        {characters.find(c => c.UID === id)?.Character}
      </div>)}</div><p>{summary.text}</p>
    </div>)}</details>}
  </aside>
}
