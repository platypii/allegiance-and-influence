"use client"

import ForceGraph from "react-force-graph-2d"
import styles from "./page.module.css"

export default function Home() {
  return (
    <div className={styles.page}>
      <main className={styles.main}>
        <div className={styles.welcome}>
          <h1>How To Win Friends and Influence Agents</h1>
          A game of human-machine influence
        </div>
        <ForceGraph
          graphData={{
            nodes: [
              { id: "You", color: "blue" },
              { id: "Agent", color: "red" },
            ],
            links: [{ source: "You", target: "Agent" }],
          }}
          nodeCanvasObject={(node, ctx, globalScale) => {
            const label = node.id
            const fontSize = 12 / globalScale
            ctx.font = `${fontSize}px Sans-Serif`
            ctx.fillStyle = node.color
            ctx.fillText(label, node.x, node.y)
          }}
        />
      </main>
    </div>
  )
}
