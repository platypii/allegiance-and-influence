import { useEffect, useRef, useState } from "react"
import styles from "./panel.module.css"
import type { Character } from "./characters"
import type { Chat, Seat } from "./client"

export default function Panel({ playerName, character, chat, enabled, busy, onMessage, onDone, onClose }: {
  playerName: Seat; character: Character; chat: Chat; enabled: boolean; busy: boolean
  onMessage: (text: string) => Promise<boolean>; onDone: () => void; onClose: () => void
}) {
  const [text, setText] = useState("")
  const scroll = useRef<HTMLDivElement>(null)
  const count = chat.messages.filter(m => m.name === playerName).length
  useEffect(() => { scroll.current?.scrollTo({ top: scroll.current.scrollHeight }) }, [chat.messages])
  useEffect(() => setText(""), [character.UID])
  return <section className={styles.panel} aria-label={`Conversation with ${character.Character}`}>
    <div className={styles.panelContent}>
      <div className={styles.chatArea} ref={scroll} role="log" aria-label="Conversation">
        {chat.messages.map((message, i) => <div key={i} className={message.name === playerName ? styles[playerName] : styles.assistant}>
          <strong>{message.name === playerName ? "You" : character.Character}: </strong>{message.content}
        </div>)}
      </div>
      <div className={styles.inputArea}>
        <p>{chat.done ? "Conversation finished. Waiting for the other player." : !enabled ? "Waiting for the other player to choose." : `${count}/5 messages · two recruit in this demo`}</p>
        <form onSubmit={async e => { e.preventDefault(); if (await onMessage(text)) setText("") }}>
          <textarea aria-label="Your message" value={text} maxLength={2000} onChange={e => setText(e.target.value)} disabled={!enabled || busy || count >= 5} placeholder="Make your case…" />
          <button aria-label="Send message" className={styles.sendit} disabled={!enabled || busy || !text.trim() || count >= 5} />
        </form>
        <button disabled={!enabled || busy} onClick={onDone}>Done talking</button>
      </div>
    </div>
    <div className={styles.panelBio}>
      <img src={`/images/agents/${character.UID}.jpg`} alt={character.Character} />
      <div className={styles.panelStats}>
        <h1>{character.Character}</h1><p>{character.Description}</p>
        <ul>{(["Charisma", "Intellect", "Stubbornness", "Empathy", "Influence Range", "Loyalty", "Curiosity", "Consistency"] as const).map(key => <li key={key}>{key}: <span>{character[key]}</span></li>)}</ul>
      </div>
    </div>
    <button className={styles.close} aria-label="Close conversation" onClick={onClose}>×</button>
  </section>
}
