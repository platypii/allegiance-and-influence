import { useState } from "react"
import styles from "./page.module.css"

export default function Welcome() {
  const [dismissed, setDismissed] = useState(false)
  if (dismissed) return null
  return (
    <div
      className={styles.welcome}
      onClick={() => setDismissed(true)}>
      <h1>How To Win Friends and Influence Agents</h1>
      <sub>A game of human-machine influence</sub>
    </div>
  )
}
