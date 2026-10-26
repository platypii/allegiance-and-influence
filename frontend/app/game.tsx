"use client"

import { useEffect, useMemo, useState } from "react"
import styles from "./page.module.css"
import Welcome from "./welcome"
import Invite from "./invite"
import Panel from "./panel"
import InfluenceBoard, { GraphNode } from "./influence-board"
import characters from "./characters"
import { teamColor } from "./teamColor"
import Round from "./round"
import Endgame from "./endgame"
import { Game, useGame } from "./client"
import WorldBoard from "./world/board"

export default function GameApp({ initialBoard = "2d" }: { initialBoard?: "2d" | "3d" }) {
  const { game, connection, error, busy, create, join, command, replay } = useGame()
  const [closedChat, setClosedChat] = useState(false)
  const [closedEnd, setClosedEnd] = useState(false)
  const [frames, setFrames] = useState<Game[] | null>(null)
  const [frame, setFrame] = useState(0)
  const [board, setBoard] = useState(initialBoard)
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
      return { id: c.UID, name: c.Character, team: c.team, selectable: canChoose && !busy, onSelect: () => command({ kind: "select", target: c.UID }), element: <button
        aria-label={`${isPlayer ? "" : "Recruit "}${c.Character}. ${c.team < 0 ? "Red" : c.team > 0 ? "Blue" : "Unaligned"}`}
        title={c.Character} disabled={!canChoose || busy}
        onClick={() => command({ kind: "select", target: c.UID })}>
        <img src={`/images/agents/${c.UID}.jpg`} alt={c.Character} style={{ borderColor }} />
        <span className={styles.nodeName}>{c.Character}</span>
        <span className={styles.nodeSide}>{c.team < 0 ? "Red" : c.team > 0 ? "Blue" : "Unaligned"}</span>
      </button> }
    })
  // command is rebound by the hook; rendering it here keeps the current state and credentials.
  }, [shown, frames, player, chat?.target, busy, command])

  const status = !game ? "" : game.phase === "lobby" ? "Share the link and wait for the other player to join" : game.phase === "selecting" ? chat?.target ? "Waiting for the other player to choose" : "Select a character to recruit" : game.phase === "conversing" ? chat?.done ? "Waiting for the other conversation to finish" : "Make your case" : game.phase === "round_complete" ? "Round complete — review what changed" : "Game finished"

  const welcome = !game || (!player && game.phase === "lobby")
  const ending = !frames && game?.phase === "finished" && !closedEnd
  const conversationOpen = !frames && character && player && chat && !closedChat && (game?.phase === "selecting" || game?.phase === "conversing")

  return <div className={styles.page}>
    <main className={styles.main}>
      {welcome ? <Welcome game={game} busy={busy} onCreate={create} onJoin={join} worldPreview={initialBoard === "3d"} /> : ending && game ? <Endgame game={game} homeHref={board === "3d" ? "/world/" : "/"} onClose={() => setClosedEnd(true)} /> : shown && <div className={styles.gameShell}>
        <header className={styles.header}>
          <a className={styles.brand} href="/" aria-label="Allegiance & Influence home">Allegiance <em>&amp;</em> Influence</a>
          <div className={styles.scoreboard}>
            <div className={styles.score} aria-label="Score">
              <span className={styles.red}>Red <strong>{shown.scores.player_red}</strong></span>
              <span className={styles.scoreDivider}>/</span>
              <span className={styles.blue}><strong>{shown.scores.player_blue}</strong> Blue</span>
            </div>
            <span className={styles.player}>{player ? `You are ${player === "player_red" ? "Red" : "Blue"}` : "Spectator"}</span>
          </div>
        </header>
        <div className={styles.gameGrid}>
          <section className={styles.board} aria-label="Game board">
            {board === "2d" && <div className={styles.boardHeading}><div><p className="eyebrow muted">The gathering</p><h1>Every alliance starts<br />with a conversation.</h1></div><span className={styles.roundBadge}>Round {shown.round_number}</span></div>}
            {board === "3d" ? <WorldBoard nodes={nodes} edges={(shown.pairings || []).map(([source, target]) => ({ source, target }))} talking={Object.values(shown.conversations).filter(chat => !chat.done && chat.target).map(chat => chat.target!)} /> : <InfluenceBoard nodes={nodes} edges={(shown.pairings || []).map(([source, target]) => ({ source, target }))} />}
            <div className={styles.status}>
              {!frames && game?.opponent?.error && <span role="alert">Opponent stopped this round ({game.opponent.error}). Finish your conversation to continue. </span>}
              <p>{frames ? `Replay · step ${frame + 1} of ${frames.length}` : status}</p>
              {!frames && game?.phase === "round_complete" && player && <button className="primary" disabled={busy} onClick={() => command({ kind: "advance" })}>Next round</button>}
              {!frames && character && closedChat && game?.phase === "conversing" && <button className="primary" onClick={() => setClosedChat(false)}>Open conversation</button>}
            </div>
          </section>
          <aside className={styles.sidebar} aria-label="Game information">
            <Round game={shown} />
            <section className={styles.toolbar} aria-label="Session controls">
              <div className={styles.sessionHeading}><h2>Your session</h2><span role="status" className={styles.connection}>{connection}</span></div>
              <label>Board view <select aria-label="Board view" value={board} onChange={event => setBoard(event.target.value as "2d" | "3d")}><option value="2d">Illustrated board</option><option value="3d">3D tabletop preview</option></select></label>
              <span className={styles.mode}>{shown.mode === "scripted" ? "Scripted demo" : "Model experiment"}</span>
              {shown.opponent && <p className={styles.opponent}>Blue: {shown.opponent.model}</p>}
              {(player || game?.phase !== "lobby") && <Invite gameId={shown.id} />}
              {player && <button disabled={busy} onClick={async () => { const result = await replay(); if (result) { setFrames(result.frames); setFrame(result.frames.length - 1) } }}>Review replay</button>}
              {frames && <><label>Replay step <input aria-label="Replay step" type="range" min={0} max={frames.length - 1} value={frame} onChange={e => setFrame(Number(e.target.value))} /></label><button onClick={() => setFrames(null)}>Back to live game</button></>}
              <a className={styles.newGame} href={board === "3d" ? "/world/" : "/"}>New game <span aria-hidden="true">↗</span></a>
            </section>
          </aside>
        </div>
      </div>}
      {error && !conversationOpen && <div role="alert" className={styles.error}>{error} <a href="/">Start page</a></div>}
    </main>
    {!frames && character && player && chat && !closedChat && (game?.phase === "selecting" || game?.phase === "conversing") && <Panel
      mode={game.mode} error={error} playerName={player} character={character} chat={chat} busy={busy}
      enabled={game.phase === "conversing" && !chat.done}
      onMessage={text => command({ kind: "message", text })}
      onDone={() => command({ kind: "done" })} onRetry={() => command({ kind: "retry" })} onCancel={() => command({ kind: "cancel" })} onClose={() => setClosedChat(true)} />}
  </div>
}
