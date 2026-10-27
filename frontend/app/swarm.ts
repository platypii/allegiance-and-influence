/** Presentation-only physics. The server's game state never depends on these coordinates. */
export interface Body {
  id: string; team: number; x: number; y: number; width: number; height: number
  vx: number; vy: number; homeX: number; homeY: number
}
export interface Link { source: string; target: string }

const gap = 8
const clamp = (value: number, min: number, max: number) => Math.max(min, Math.min(max, value))
function contain(body: Body, width: number, height: number) {
  body.x = clamp(body.x, body.width / 2 + 8, width - body.width / 2 - 8)
  body.y = clamp(body.y, body.height / 2 + 60, height - body.height / 2 - 8)
}
function overlap(a: Body, b: Body) {
  return {
    x: (a.width + b.width) / 2 + gap - Math.abs(a.x - b.x),
    y: (a.height + b.height) / 2 + gap - Math.abs(a.y - b.y),
  }
}

export function stepSwarm(bodies: Body[], links: Link[], width: number, height: number, time: number, dt: number) {
  const previous = bodies.map(b => ({ x: b.x, y: b.y }))
  const byId = new Map(bodies.map(b => [b.id, b]))
  const forces = bodies.map((body, i) => {
    // Slow wandering keeps the gathering alive after the initial forces settle.
    let x = Math.cos(time * .65 + i * 2.4) * .065
    let y = Math.sin(time * .52 + i * 1.7) * .055
    x += (width / 2 + body.team * width * .18 - body.x) * .00035
    y += (height / 2 + 30 - body.y) * .00035
    for (const other of bodies) {
      if (body === other) continue
      const dx = body.x - other.x, dy = body.y - other.y
      const distance = Math.max(1, Math.hypot(dx, dy))
      const force = Math.min(.5, 900 / (distance * distance))
      x += dx / distance * force
      y += dy / distance * force
    }
    for (const link of links) {
      if (link.source !== body.id && link.target !== body.id) continue
      const other = byId.get(link.source === body.id ? link.target : link.source)
      if (!other) continue
      const dx = other.x - body.x, dy = other.y - body.y
      const distance = Math.max(1, Math.hypot(dx, dy))
      const force = (distance - 180) * .0012
      x += dx / distance * force
      y += dy / distance * force
    }
    return { x, y }
  })
  for (const [i, body] of bodies.entries()) {
    body.vx = clamp((body.vx + forces[i].x * dt) * Math.pow(.94, dt), -.8, .8)
    body.vy = clamp((body.vy + forces[i].y * dt) * Math.pow(.94, dt), -.8, .8)
    body.x += body.vx * dt
    body.y += body.vy * dt
    contain(body, width, height)
  }
  // Resolve the entire portrait + label rectangle, not just the image circle.
  for (let pass = 0; pass < 8; pass++) {
    for (let i = 0; i < bodies.length; i++) {
      for (let j = i + 1; j < bodies.length; j++) {
        const a = bodies[i], b = bodies[j], penetration = overlap(a, b)
        if (penetration.x <= 0 || penetration.y <= 0) continue
        const axis = penetration.x < penetration.y ? "x" : "y"
        const direction = a[axis] <= b[axis] ? -1 : 1
        const shift = (penetration[axis] + .1) / 2
        a[axis] += shift * direction
        b[axis] -= shift * direction
      }
    }
    for (const body of bodies) contain(body, width, height)
  }
  // Crowded screens may have no solution for a proposed step. Keep the last safe
  // frame instead of letting a name or touch target overlap another one.
  const collision = bodies.some((a, i) => bodies.slice(i + 1).some(b => {
    const penetration = overlap(a, b)
    return penetration.x > .2 && penetration.y > .2
  }))
  if (collision) bodies.forEach((body, i) => {
    body.x = previous[i].x
    body.y = previous[i].y
    body.vx *= -.4
    body.vy *= -.4
  })
}
