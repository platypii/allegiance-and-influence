import { test, expect } from "@playwright/test"
import { Body, stepSwarm } from "../app/swarm"

function crowd(count: number, width: number, columns: number, cardWidth: number, cardHeight: number, cellHeight: number) {
  return Array.from({ length: count }, (_, i): Body => ({
    id: String(i), team: 0, x: width / columns * (i % columns + .5), y: 76 + cardHeight / 2 + Math.floor(i / columns) * cellHeight,
    width: cardWidth, height: cardHeight, vx: 0, vy: 0, homeX: 0, homeY: 0,
  }))
}

for (const [count, width, columns, cardWidth, cardHeight, cellHeight] of [[8, 1000, 4, 144, 170, 210], [25, 288, 2, 116, 160, 184]]) {
  test(`swarm keeps moving safely after a minute with ${count} portraits`, () => {
    const height = 100 + Math.ceil(count / columns) * cellHeight
    const bodies = crowd(count, width, columns, cardWidth, cardHeight, cellHeight)
    let lateMoving = 0
    for (let frame = 0; frame < 3600; frame++) {
      const old = bodies.map(body => [body.x, body.y])
      stepSwarm(bodies, [], width, height, frame / 60, 1)
      if (frame > 3000 && bodies.some((body, i) => Math.hypot(body.x - old[i][0], body.y - old[i][1]) > .01)) lateMoving++
      for (const [i, a] of bodies.entries()) {
        // Throw only on a violated invariant: avoid millions of matcher allocations.
        if (a.x < a.width / 2 || a.x + a.width / 2 > width || a.y < a.height / 2 || a.y + a.height / 2 > height) throw new Error("Portrait escaped the board")
        for (const b of bodies.slice(i + 1)) {
          if (Math.abs(a.x - b.x) < (a.width + b.width) / 2 && Math.abs(a.y - b.y) < (a.height + b.height) / 2) throw new Error("Portrait labels overlap")
        }
      }
    }
    expect(lateMoving).toBeGreaterThan(300)
  })
}

test("paired characters attract while labels stay separate", () => {
  const initial = crowd(2, 1000, 2, 144, 170, 210)
  const paired = structuredClone(initial), unpaired = structuredClone(initial)
  for (let frame = 0; frame < 180; frame++) {
    stepSwarm(paired, [{ source: "0", target: "1" }], 1000, 600, frame / 60, 1)
    stepSwarm(unpaired, [], 1000, 600, frame / 60, 1)
    if (frame === 0) {
      expect(paired[0].vx).toBeGreaterThan(unpaired[0].vx)
      expect(paired[1].vx).toBeLessThan(unpaired[1].vx)
    }
  }
  const distance = (b: Body[]) => Math.hypot(b[0].x - b[1].x, b[0].y - b[1].y)
  expect(distance(paired)).toBeLessThan(distance(unpaired))
  expect(distance(paired)).toBeGreaterThanOrEqual(144)
})
