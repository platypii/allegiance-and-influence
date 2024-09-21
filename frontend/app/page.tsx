import styles from "./page.module.css"

export default function Home() {
  return (
    <div className={styles.page}>
      <main className={styles.main}>
        <div className={styles.welcome}>
          <h1>How To Win Friends and Influence Agents</h1>
          A game of human-machine influence
        </div>
      </main>
    </div>
  )
}
