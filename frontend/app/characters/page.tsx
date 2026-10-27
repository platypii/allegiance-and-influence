"use client"

import { useEffect, useRef, useState } from "react"
import characters from "../characters"
import type { WorldScene } from "../world/scene"
import styles from "./portraits.module.css"

const featured = ["albert_einstein", "marie_curie", "winston_churchill", "nelson_mandela", "napoleon_bonaparte", "martin_luther", "genghis_khan"]

export default function CharacterGallery() {
  const [id, setId] = useState(featured[0])
  const [failed, setFailed] = useState(false)
  const [ready, setReady] = useState(false)
  const [paused, setPaused] = useState(false)
  const canvas = useRef<HTMLCanvasElement>(null)
  const scene = useRef<WorldScene | null>(null)
  const character = characters.find(c => c.UID === id)!
  useEffect(() => {
    let stopped = false
    setReady(false); setFailed(false)
    import("../world/scene").then(({ createWorld }) => {
      if (stopped || !canvas.current) return
      try {
        scene.current = createWorld(canvas.current, { people: [{ id, name: character.Character, team: 0, selectable: false }], pairs: [], talking: [] }, () => {}, () => {}, () => { scene.current?.dispose(); scene.current = null; setFailed(true) }, true)
        scene.current.pause(paused)
        setReady(true)
      } catch { setFailed(true) }
    }).catch(() => { if (!stopped) setFailed(true) })
    return () => { stopped = true; scene.current?.dispose(); scene.current = null }
  }, [id]) // Character identity recreates the single-figure scene; controls act directly.
  return <main className={styles.gallery}>
    <header><a href="/world/">← Back to the gathering</a><span className="eyebrow">Meet the company</span></header>
    <div className={styles.layout}>
      <section className={styles.stage} aria-label="Character portrait">
        <canvas key={id} ref={canvas} aria-label={`3D portrait of ${character.Character}`} />
        {failed && <div className={styles.fallback}><img src={`/images/agents/${id}.jpg`} alt={character.Character} /><p>3D is unavailable in this browser. Original game portrait shown.</p></div>}
        {!ready && !failed && <p className={styles.loading} role="status">Preparing the portrait…</p>}
        <div className={styles.controls}>
          <button aria-label="Turn portrait left" disabled={!ready || failed} onClick={() => scene.current?.rotate(-1)}>↶</button>
          <button aria-label="Turn portrait right" disabled={!ready || failed} onClick={() => scene.current?.rotate(1)}>↷</button>
          <button disabled={!ready || failed} aria-pressed={paused} onClick={() => { scene.current?.pause(!paused); setPaused(!paused) }}>{paused ? "Resume motion" : "Pause motion"}</button>
        </div>
      </section>
      <section className={styles.details}>
        <p className="eyebrow muted">A closer look</p><h1>{character.Character}</h1><p>{character.Description}</p>
        <label>Choose a character<select value={id} onChange={e => setId(e.target.value)}>{featured.map(uid => <option key={uid} value={uid}>{characters.find(c => c.UID === uid)!.Character}</option>)}</select></label>
        <p>Turn the miniature to see its face, silhouette and costume. These seven characters have received the first likeness pass.</p>
        <a href="/world/" className="buttonLink primary">Play on the 3D board</a>
      </section>
    </div>
  </main>
}
