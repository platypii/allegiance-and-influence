import { useState } from "react"
import styles from "./welcome.module.css"
import type { Game, Seat } from "./client"

export default function Welcome({ game, busy, onCreate, onJoin }: {
  game: Game | null; busy: boolean
  onCreate: (config: Game["config"]) => void
  onJoin: (seat: Seat) => void
}) {
  const [rounds, setRounds] = useState(3)
  const [agents, setAgents] = useState(6)
  return <div className={styles.welcome}>
    <img src="/images/splash_logo.jpg" alt="Allegiance & Influence" width={480} />
    <div className={styles.setup}>
      <h1>{game ? "Choose your side" : "A room full of possibilities"}</h1>
      <p>Local demo · scripted characters · no API keys</p>
      {!game ? <form onSubmit={e => { e.preventDefault(); onCreate({ num_agents: agents, num_rounds: rounds, seed: 32 }) }}>
        <label>Characters <input aria-label="Characters" type="number" min={2} max={23} value={agents} onChange={e => setAgents(Number(e.target.value))} /></label>
        <label>Rounds <input aria-label="Rounds" type="number" min={1} max={20} value={rounds} onChange={e => setRounds(Number(e.target.value))} /></label>
        <button disabled={busy} type="submit">Create local game</button>
      </form> : <>
        <p>Share this address with another browser or tab. Each player chooses a different side.</p>
        <div className={styles.choose}>
          <button disabled={busy || game.players.player_red} onClick={() => onJoin("player_red")}>Join Red</button>
          <button disabled={busy || game.players.player_blue} onClick={() => onJoin("player_blue")}>Join Blue</button>
        </div>
        {game.players.player_red && game.players.player_blue && <p>Both seats are occupied. You can watch the board.</p>}
        <a href="/">Create another game</a>
      </>}
      <p>Choose a character, send two messages to recruit them, then finish the conversation. Unselected characters meet between rounds.</p>
    </div>
  </div>
}
