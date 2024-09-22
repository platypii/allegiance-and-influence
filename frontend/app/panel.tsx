import { useEffect, useRef, useState } from "react"
import styles from "./panel.module.css"
import { Character } from "./characters"
import { database } from "./firebase"
import { ref, update } from "firebase/database"

interface PanelProps {
  playerName: 'player_red' | 'player_blue'
  chatWith: Character | undefined
  firemessages: Message[]
  onClose: () => void
}

interface Message {
  name: string
  content: string
}

export default function Panel({ playerName, chatWith, firemessages, onClose }: PanelProps) {
  const [messages, setMessages] = useState<Message[]>(firemessages)
  const inputRef = useRef<HTMLInputElement>(null)

  function handleInput(event: React.FormEvent) {
    event.preventDefault()
    if (inputRef.current) {
      const content = inputRef.current.value
      setMessages(messages => [
        ...messages,
        { name: playerName, content },
      ])
      // Send message to Firebase
      const dbRef = ref(database, `/current_state/round_state/${playerName}`)
      update(dbRef, {messages: [...messages, { name: playerName, content }]})
      inputRef.current.value = ""
    }
  }

  useEffect(() => {
    setMessages(firemessages)
  }, [firemessages])

  function handleDone() {
    // Set done talking to true
    const dbRef = ref(database, `/current_state/round_state/${playerName}`)
    update(dbRef, { done_talking: true })
  }

  return (
    <div className={styles.panel} style={chatWith ? {} : {width: "0px"}}>
      <div className={styles.panelContent}>
        <div className={styles.chatArea}>
          {messages.map((message, index) => (
            <div key={index} className={styles[message.name]}>
              {message.name?.startsWith('player_') ? 'user' : chatWith?.Character}: {message.content}
            </div>
          ))}
        </div>
        <form className={styles.inputArea} onSubmit={handleInput}>
          <input ref={inputRef} type="text" placeholder="Make your argument" />
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
      <button className={styles.close} onClick={onClose}>X</button>
    </div>
  )
}
