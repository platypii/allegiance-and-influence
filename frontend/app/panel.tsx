import { useEffect, useRef, useState } from "react"
import styles from "./panel.module.css"
import type { Character } from "./characters"
import type { Chat, Seat } from "./client"

export default function Panel({ mode, error, playerName, character, chat, enabled, busy, onMessage, onDone, onClose, onRetry, onCancel }: {
  error: string; mode: "scripted" | "model"; playerName: Seat; character: Character; chat: Chat; enabled: boolean; busy: boolean
  onMessage: (text: string) => Promise<boolean>; onDone: () => void; onClose: () => void; onRetry: () => void; onCancel: () => void
}) {
  const [text, setText] = useState("")
  const scroll = useRef<HTMLDivElement>(null)
  const dialog = useRef<HTMLDialogElement>(null)
  useEffect(() => {
    const element = dialog.current
    element?.showModal()
    return () => element?.close()
  }, [])
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
  return <dialog ref={dialog} className={styles.panel} aria-labelledby="conversation-title" onCancel={e => { e.preventDefault(); onClose() }}>
    <header className={styles.panelHeader}>
      <div className={styles.topline}><span className="eyebrow muted">Private conversation</span><button className={styles.close} aria-label="Close conversation" onClick={onClose}>Back to board <span aria-hidden="true">×</span></button></div>
      <div className={styles.identity}><img src={`/images/agents/${character.UID}.jpg`} alt="" width={64} height={64} /><div><h2 id="conversation-title">{character.Character}</h2><p>{character.Description}</p></div></div>
      <details className={styles.profile}><summary>Character profile</summary>
        <dl>{(["Charisma", "Intellect", "Stubbornness", "Empathy", "Influence Range", "Loyalty", "Curiosity", "Consistency"] as const).map(key => <div key={key}><dt>{key}</dt><dd>{character[key]}<span className="muted"> / 10</span></dd></div>)}</dl>
      </details>
    </header>
    <div className={styles.panelContent}>
      <div className={styles.chatArea} ref={scroll} role="log" aria-label="Conversation">
        {chat.messages.map((message, i) => <div key={i} className={message.name === playerName ? styles[playerName] : styles.assistant}>
          <strong>{message.name === playerName ? "You" : character.Character}</strong><p>{message.content}</p>
        </div>)}
      </div>
      <div className={styles.inputArea}>
        {error && <p role="alert">{error}</p>}
        <p>{chat.done ? "Conversation finished. Waiting for the other player." : !enabled ? "Waiting for the other player to choose." : `${count}/5 messages${mode === "scripted" ? " · two recruit in this demo" : " · make your case"}`}</p>
        {waiting && <p role="status" aria-label="Agent reply">Waiting for a reply… <button disabled={busy} onClick={onCancel}>Cancel reply</button></p>}
        {failed && !chat.done && <p role="status" aria-label="Agent reply">{explanation[chat.work?.error || ""] || "The character could not reply."} You can retry or finish the conversation. <button disabled={busy || !enabled} onClick={onRetry}>Retry reply</button></p>}
        <form onSubmit={async e => { e.preventDefault(); if (await onMessage(text)) setText("") }}>
          <textarea aria-label="Your message" value={text} maxLength={2000} onChange={e => setText(e.target.value)} disabled={!enabled || busy || waiting || count >= 5} placeholder="Make your case…" />
          <button aria-label="Send message" className="primary" disabled={!enabled || busy || waiting || !text.trim() || count >= 5}>Send <span aria-hidden="true">↑</span></button>
        </form>
        <button disabled={!enabled || busy || waiting} onClick={onDone}>Done talking</button>
      </div>
    </div>
  </dialog>
}
