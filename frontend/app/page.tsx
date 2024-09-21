"use client"

import ForceGraph from "react-force-graph-2d"
import styles from "./page.module.css"
import Welcome from "./welcome"

export default function Home() {
  return (
    <div className={styles.page}>
      <main className={styles.main}>
        <ForceGraph
          graphData={{
            nodes: [
              { id: "You", team: "blue" },
              { id: "Agent", team: "red" },
            ],
            links: [{ source: "You", target: "Agent" }],
          }}
          nodeCanvasObject={(node, ctx, globalScale) => {
            const label = node.id
            const fontSize = 4
            ctx.font = `${fontSize}px Sans-Serif`
            ctx.fillStyle = node.team
            // ctx.fillRect(node.x - 10, node.y - 10, 20, 20)
            ctx.beginPath()
            ctx.arc(node.x, node.y, 10, 0, 2 * Math.PI)
            ctx.fill()
            const textWidth = ctx.measureText(label).width
            ctx.fillStyle = "#eee"
            ctx.fillText(label, node.x - textWidth / 2, node.y + fontSize / 2)
          }}
        />
        <Welcome />
      </main>
    </div>
  )
}
