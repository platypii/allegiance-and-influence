import styles from "./panel.module.css"

export default function Panel() {
  return (
    <div className={styles.panel}>
      <h1>Command Panel</h1>
      <button>Attack</button>
      <button>Defend</button>
      <button>Retreat</button>
      <button>Supply</button>
    </div>
  )
}
