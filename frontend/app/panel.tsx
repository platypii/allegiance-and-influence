import { useRef, useState } from "react"
import styles from "./panel.module.css"

interface PanelProps {
  chatWith: string | undefined
}

interface Message {
  role: "user" | "assistant"
  text: string
}

export default function Panel({ chatWith }: PanelProps) {
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

  return (
    <div className={styles.panel} style={chatWith ? {} : {width: "0px"}}>
      <div className={styles.panelContent}>
        <h1>{chatWith}</h1>
        <div className={styles.chatArea}>
          {messages.map((message, index) => (
            <div key={index} className={styles[message.role]}>
              {message.text}
            </div>
          ))}
        </div>
        <form className={styles.inputArea} onSubmit={handleInput}>
          <input ref={inputRef} type="text" placeholder="Make an argument" />
        </form>
      </div>
    </div>
  )
}
