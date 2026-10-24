import { useEffect, useRef, useState } from "react"
import styles from "./panel.module.css"
import type { Character } from "./characters"
import type { Chat, Seat } from "./client"

export default function Panel({ mode, playerName, character, chat, enabled, busy, onMessage, onDone, onClose, onRetry, onCancel }: {
  mode: "scripted" | "model"; playerName: Seat; character: Character; chat: Chat; enabled: boolean; busy: boolean
  onMessage: (text: string) => Promise<boolean>; onDone: () => void; onClose: () => void; onRetry: () => void; onCancel: () => void
}) {
  const [text, setText] = useState("")
  const scroll = useRef<HTMLDivElement>(null)
  const waiting = chat.work?.status === "pending"
  const failed = chat.work && ["failed", "cancelled", "interrupted"].includes(chat.work.status)
  const explanation: Record<string, string> = {
    input_limit: "This conversation exceeds the model’s input limit.", model_mismatch: "The service returned a different model than requested.", incomplete_response: "The model did not finish its reply.", provider_connection: "The model service could not be reached.", provider_http_error: "The model service rejected this request.",
    timeout: "The reply took too long.", cancelled: "Reply cancelled.", server_restarted: "The server restarted before the reply finished.",
    budget_exhausted: "This game's agent budget has been used up.", provider_changed: "This game's agent configuration is unavailable.", provider_bounds_exceeded: "The agent exceeded its usage limits. Finish this conversation to continue.",
  }
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
        <p>{chat.done ? "Conversation finished. Waiting for the other player." : !enabled ? "Waiting for the other player to choose." : `${count}/5 messages${mode === "scripted" ? " · two recruit in this demo" : " · make your case"}`}</p>
        {waiting && <p role="status" aria-label="Agent reply">Waiting for a reply… <button disabled={busy} onClick={onCancel}>Cancel reply</button></p>}
        {failed && !chat.done && <p role="status" aria-label="Agent reply">{explanation[chat.work?.error || ""] || "The character could not reply."} You can retry or finish the conversation. <button disabled={busy || !enabled} onClick={onRetry}>Retry reply</button></p>}
        <form onSubmit={async e => { e.preventDefault(); if (await onMessage(text)) setText("") }}>
          <textarea aria-label="Your message" value={text} maxLength={2000} onChange={e => setText(e.target.value)} disabled={!enabled || busy || waiting || count >= 5} placeholder="Make your case…" />
          <button aria-label="Send message" className={styles.sendit} disabled={!enabled || busy || waiting || !text.trim() || count >= 5} />
        </form>
        <button disabled={!enabled || busy || waiting} onClick={onDone}>Done talking</button>
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
