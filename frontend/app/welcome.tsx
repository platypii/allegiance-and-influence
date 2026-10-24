import { useEffect, useState } from "react"
import styles from "./welcome.module.css"
import Invite from "./invite"
import type { Game, Seat } from "./client"

export default function Welcome({ game, busy, onCreate, onJoin }: {
  game: Game | null; busy: boolean
  onCreate: (config: Game["config"]) => void
  onJoin: (seat: Seat) => void
}) {
  const [solo, setSolo] = useState(true)
  const [profiles, setProfiles] = useState<{profile: string; model: string; kind: string}[]>([])
  const [profile, setProfile] = useState("")
  const [optionsError, setOptionsError] = useState(false)
  useEffect(() => {
    fetch("/api/options").then(r => { if (!r.ok) throw new Error(); return r.json() }).then(data => {
      setProfiles(data.opponents)
      setProfile((data.opponents.find((p: {kind: string}) => p.kind !== "scripted") || data.opponents[0])?.profile || "")
    }).catch(() => setOptionsError(true))
  }, [])
  const [rounds, setRounds] = useState(3)
  const [agents, setAgents] = useState(6)
  return <div className={styles.welcome}>
    <img src="/images/splash_logo.jpg" alt="Allegiance & Influence" width={480} />
    <div className={styles.setup}>
      <h1>{game ? "Choose your side" : "A room full of possibilities"}</h1>
      <p>{game?.mode === "scripted" ? "Local demo · scripted characters · no API keys" : game ? "Model experiment · character-specific model assignments" : "Persuasion game · local server"}</p>
      {!game ? <form onSubmit={e => { e.preventDefault(); onCreate({ num_agents: agents, num_rounds: rounds, seed: 32, opponent_profile: solo ? profile : null }) }}>
        <label>Play mode <select aria-label="Play mode" value={solo ? "solo" : "multiplayer"} onChange={e => setSolo(e.target.value === "solo")}>
          <option value="solo">Single player</option><option value="multiplayer">Two players</option>
        </select></label>
        {solo && <label>Opponent model <select aria-label="Opponent model" value={profile} onChange={e => setProfile(e.target.value)}>
          {profiles.map(p => <option key={p.profile} value={p.profile}>{p.kind === "scripted" ? "Scripted opponent (offline)" : p.model} · {p.profile}</option>)}
        </select></label>}
        {solo && optionsError && <p role="alert">Could not load opponent models. Reload to try again.</p>}
        <label>Characters <input aria-label="Characters" type="number" min={2} max={23} value={agents} onChange={e => setAgents(Number(e.target.value))} /></label>
        <label>Rounds <input aria-label="Rounds" type="number" min={1} max={20} value={rounds} onChange={e => setRounds(Number(e.target.value))} /></label>
        <button disabled={busy || (solo && !profile)} type="submit">{solo ? "Start single-player game" : "Create local game"}</button>
      </form> : <>
        {game.opponent ? <p>You play Red against {game.opponent.model}. Blue is ready.</p> : <>
          <p>Share this session link. Each player chooses a different side.</p>
          <Invite gameId={game.id} expanded />
        </>}
        <div className={styles.choose}>
          <button disabled={busy || game.players.player_red} onClick={() => onJoin("player_red")}>{game.opponent ? "Play as Red" : "Join Red"}</button>
          {!game.opponent && <button disabled={busy || game.players.player_blue} onClick={() => onJoin("player_blue")}>Join Blue</button>}
        </div>
        {game.players.player_red && game.players.player_blue && <p>Both seats are occupied. You can watch the board.</p>}
        <a href="/">Create another game</a>
      </>}
      <p>Choose a character, make your case, then finish the conversation. Watch allegiances change when the round ends.</p>
    </div>
  </div>
}
