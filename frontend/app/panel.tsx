import styles from "./panel.module.css"

interface PanelProps {
  chatWith: string | undefined
}

export default function Panel({ chatWith }: PanelProps) {
  return (
    <div className={styles.panel} style={chatWith ? {} : {width: "0px"}}>
      <div className={styles.panelContent}>
        <h1>{chatWith}</h1>
        <div className={styles.chatArea}>
          <div className={styles.user}>Hello</div>
          <div className={styles.assistant}>Hi</div>
        </div>
        <div className={styles.inputArea}>
          <input type="text" placeholder="Make an argument" />
          <button>Supply</button>
        </div>
      </div>
    </div>
  )
}
