import { useState, useEffect } from "react"
import styles from "./welcome.module.css"

export default function Welcome() {
  const [dismissed, setDismissed] = useState(false)

  function clickPlayer1() {
    setDismissed(true)
  }
  function clickPlayer2() {
    setDismissed(true)
  }

  if (dismissed) return null

  return (
    <div className={styles.welcome}>
      <h1>How To Win Friends and Influence Agents</h1>
      <sub>A game of human-machine influence</sub>
      
      <div className={styles.choose}>
        <button style={{ color: 'red' }} onClick={clickPlayer1}>Player 1</button>
        <button style={{ color: 'blue' }} onClick={clickPlayer2}>Player 2</button>
      </div>
    </div>
  )
}
