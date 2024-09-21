import styles from "./panel.module.css"

export default function Panel() {
  return (
    <div className={styles.panel}>
      <h1>Command Panel</h1>
      <div className={styles.chatArea} />
      <div className={styles.inputArea}>
        <input type="text" placeholder="Make an argument" />
        <button>Supply</button>
      </div>
    </div>
  )
}
