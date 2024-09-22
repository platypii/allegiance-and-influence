import { useState, useEffect } from "react"
import styles from "./welcome.module.css"

export default function Welcome() {
  const [dismissed, setDismissed] = useState(true)

  // Check localStorage on component mount
  useEffect(() => {
    const isDismissed = localStorage.getItem('welcomeDismissed') === 'true'
    if (!isDismissed) {
      setDismissed(false)
    }
  }, [])

  // Handler for any click on the welcome message
  const handleDismiss = () => {
    setDismissed(true)
  }

  // Handler for checkbox click
  const handleCheckboxClick = (e: React.MouseEvent<HTMLLabelElement>) => {
    e.stopPropagation() // Prevent the parent onClick from firing
    localStorage.setItem('welcomeDismissed', 'true')
    setDismissed(true)
  }

  if (dismissed) return null

  return (
    <div className={styles.welcome} onClick={handleDismiss}>
      <h1>How To Win Friends and Influence Agents</h1>
      <sub>A game of human-machine influence</sub>
      
      <div className={styles.choose}>
        <button>Player 1</button>
        <button>Player 2</button>
      </div>
      <label className={styles.permadismiss} onClick={handleCheckboxClick}>
        <input type="checkbox" />
        Don't show this again
      </label>
    </div>
  )
}
