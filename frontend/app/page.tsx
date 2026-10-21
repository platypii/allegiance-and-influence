"use client"

import { useEffect, useMemo, useState } from "react"
import styles from "./page.module.css"
import Welcome from "./welcome"
import Panel from "./panel"
import ForceGraph, { GraphNode } from "./forcegraph"
import characters from "./characters"
import { teamColor } from "./teamColor"
import Round from "./round"
import Endgame from "./endgame"
import { Game, useGame } from "./client"

export default function Home() {
  const { game, connection, error, busy, create, join, command, replay } = useGame()
  const [closedChat, setClosedChat] = useState(false)
  const [closedEnd, setClosedEnd] = useState(false)
  const [frames, setFrames] = useState<Game[] | null>(null)
  const [frame, setFrame] = useState(0)
  const [copied, setCopied] = useState(false)
  const shown = frames ? frames[frame] : game
  const player = game?.you
  const chat = player && shown ? shown.conversations[player] : null
  const character = shown?.agents.find(a => a.UID === chat?.target)

  useEffect(() => { setClosedChat(false) }, [game?.round_number, chat?.target])
  const nodes: GraphNode[] = useMemo(() => {
    if (!shown) return []
    return [...shown.agents.map(a => ({ ...a, team: a.side })), ...characters.filter(c => c.UID.startsWith("player_")).map(c => ({ ...c, team: c.UID === "player_red" ? -1 : 1 }))].map(c => {
      const isPlayer = c.UID.startsWith("player_")
      const taken = Object.values(shown.conversations).some(conv => conv.target === c.UID)
      const canChoose = !frames && !!player && shown.phase === "selecting" && !chat?.target && !taken && !isPlayer
      const borderColor = teamColor(c.team)
      return { id: c.UID, team: c.team, element: <button
        aria-label={`${isPlayer ? "Player" : "Recruit"} ${c.Character}`}
        title={c.Character} disabled={!canChoose || busy}
        onClick={() => command({ kind: "select", target: c.UID })}
        style={{ borderColor }}>
        <img src={`/images/agents/${c.UID}.jpg`} alt={c.Character} />
        <span style={{ position: "absolute", inset: 0, backgroundColor: borderColor, opacity: 0.3, mixBlendMode: "multiply", pointerEvents: "none" }} />
      </button> }
    })
  // command is rebound by the hook; rendering it here keeps the current state and credentials.
  }, [shown, frames, player, chat?.target, busy, command])

  const status = !game ? "" : game.phase === "lobby" ? "Share the link and wait for the other player to join" : game.phase === "selecting" ? chat?.target ? "Waiting for the other player to choose" : "Select a character to recruit" : game.phase === "conversing" ? chat?.done ? "Waiting for the other conversation to finish" : "Make your case" : game.phase === "round_complete" ? "Round complete — review what changed" : "Game finished"

  return <div className={styles.page}>
    <main className={styles.main}>
      <ForceGraph nodes={nodes} edges={(shown?.pairings || []).map(([source, target]) => ({ source, target }))} />
      {shown && <>
        <div className={styles.overlay}>
          <div className={styles.score} aria-label="Score"><div className={styles.red}>{shown.scores.player_red}</div>–<div className={styles.blue}>{shown.scores.player_blue}</div></div>
          <div>{player ? `You are ${player === "player_red" ? "Red" : "Blue"}` : "Spectator"}</div>
        </div>
        <Round game={shown} />
        <div className={styles.toolbar}>
          <span role="status">{connection}</span><span>Scripted demo</span>
          <button onClick={async () => { try { await navigator.clipboard.writeText(location.href); setCopied(true) } catch { setCopied(false) } }}>{copied ? "Link copied" : "Copy invite link"}</button>
          <a href="/">New game</a>
          {player && <button disabled={busy} onClick={async () => { const result = await replay(); if (result) { setFrames(result.frames); setFrame(result.frames.length - 1) } }}>Review replay</button>}
          {frames && <><label>Replay step <input aria-label="Replay step" type="range" min={0} max={frames.length - 1} value={frame} onChange={e => setFrame(Number(e.target.value))} /></label><button onClick={() => setFrames(null)}>Back to live game</button></>}
        </div>
        <div className={styles.status}>
          {frames ? `Replay · step ${frame + 1} of ${frames.length}` : status}
          {!frames && game?.phase === "round_complete" && player && <button disabled={busy} onClick={() => command({ kind: "advance" })}>Next round</button>}
          {!frames && character && closedChat && game?.phase === "conversing" && <button onClick={() => setClosedChat(false)}>Open conversation</button>}
        </div>
      </>}
      {(!game || (!player && game.phase === "lobby")) && <Welcome game={game} busy={busy} onCreate={create} onJoin={join} />}
      {error && <div role="alert" className={styles.error}>{error} <a href="/">Start page</a></div>}
      {!frames && game?.phase === "finished" && !closedEnd && <Endgame game={game} onClose={() => setClosedEnd(true)} />}
    </main>
    {!frames && character && player && chat && !closedChat && (game?.phase === "selecting" || game?.phase === "conversing") && <Panel
      playerName={player} character={character} chat={chat} busy={busy}
      enabled={game.phase === "conversing" && !chat.done}
      onMessage={text => command({ kind: "message", text })}
      onDone={() => command({ kind: "done" })} onClose={() => setClosedChat(true)} />}
  </div>
}
