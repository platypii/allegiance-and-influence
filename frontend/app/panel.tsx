import { useRef, useState } from "react"
import styles from "./panel.module.css"
import { Character } from "./characters"
import { database } from "./firebase"

interface PanelProps {
  chatWith: Character | undefined
  onClose: () => void
}

interface Message {
  role: "user" | "assistant"
  text: string
}

export default function Panel({ chatWith, onClose }: PanelProps) {
  const [messages, setMessages] = useState<Message[]>([
    { role: "user", text: "Hello" },
    { role: "assistant", text: "Hi" },
  ])
  const inputRef = useRef<HTMLInputElement>(null)

  function handleInput(event: React.FormEvent) {
    event.preventDefault()
    if (inputRef.current) {
      const text = inputRef.current.value
      setMessages(messages => [
        ...messages,
        { role: "user", text },
      ])
      inputRef.current.value = ""
    }
  }

  function handleDone() {
    // TODO: Send messages to Firebase
    // database.ref('/state').update()
  }

  return (
    <div className={styles.panel} style={chatWith ? {} : {width: "0px"}}>
      <div className={styles.panelContent}>
        <div className={styles.chatArea}>
          {messages.map((message, index) => (
            <div key={index} className={styles[message.role]}>
              {message.role}: {message.text}
            </div>
          ))}
        </div>
        <form className={styles.inputArea} onSubmit={handleInput}>
          <input ref={inputRef} type="text" placeholder="Make an argument" />
          <button onClick={handleDone}>Done Talking</button>
        </form>
      </div>
      <div className={styles.panelBio}>
        <img src={`/images/agents/${chatWith?.UID}.jpg`} alt={chatWith?.Character} />
        <div className={styles.panelStats}>
          <h1>{chatWith?.Character}</h1>
          <p>{chatWith?.Description}</p>
          <ul>
            <li>Charisma: <span>{chatWith?.Charisma}</span></li>
            <li>Intellect: <span>{chatWith?.Intellect}</span></li>
            <li>Stubbornness: <span>{chatWith?.Stubbornness}</span></li>
            <li>Empathy: <span>{chatWith?.Empathy}</span></li>
            <li>Influence Range: <span>{chatWith?.['Influence Range']}</span></li>
            <li>Loyalty: <span>{chatWith?.Loyalty}</span></li>
            <li>Curiosity: <span>{chatWith?.Curiosity}</span></li>
            <li>Consistency: <span>{chatWith?.Consistency}</span></li>
          </ul>
        </div>
      </div>
      <div className={styles.close} onClick={onClose}>X</div>
    </div>
  )
}
