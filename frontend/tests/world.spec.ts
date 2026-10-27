import { test, expect } from "@playwright/test"

// CI uses software WebGL for functional evidence, not mobile performance claims.
test.use({ launchOptions: { args: ["--enable-unsafe-swiftshader"] } })
test.setTimeout(60000)

test("3D renders actual geometry, picks a miniature, recruits and completes a saved match", async ({ page }) => {
  const errors: string[] = [], external: string[] = []
  page.on("pageerror", error => errors.push(error.message))
  await page.route("**/*", route => {
    if (new URL(route.request().url()).hostname !== "127.0.0.1") { external.push(route.request().url()); return route.abort() }
    return route.continue()
  })
  await page.goto("/world/")
  await page.getByLabel("Rounds", { exact: true }).fill("2")
  await page.getByRole("button", { name: "Start single-player game" }).click()
  const canvas = page.locator("canvas")
  await expect(canvas).toHaveAttribute("data-rendered", "true", { timeout: 20000 })
  expect(Number(await canvas.getAttribute("data-triangles"))).toBeGreaterThan(10000)
  expect(Number(await canvas.getAttribute("data-draw-calls"))).toBeLessThan(400)
  expect((await canvas.screenshot()).byteLength).toBeGreaterThan(20000)
  await page.screenshot({ path: "../artifacts/screenshots/world-desktop.png", fullPage: true })
  const positions = JSON.parse((await canvas.getAttribute("data-targets"))!)
  const target = positions.winston_churchill
  const bounds = (await canvas.boundingBox())!
  expect(target.y).toBeGreaterThan(0)
  expect(target.y).toBeLessThan(bounds.height)
  await page.mouse.click(bounds.x + target.x, bounds.y + target.y)
  await expect(page.getByRole("dialog")).toBeVisible()
  await expect(page.getByRole("dialog").getByRole("heading", { name: "Winston Churchill" })).toBeVisible()
  for (const text of ["Let us work together.", "We have a common purpose."]) {
    await expect(page.getByLabel("Your message")).toBeEnabled()
    await page.getByLabel("Your message").fill(text)
    await page.getByRole("button", { name: "Send message", exact: true }).click()
    await expect(page.getByLabel("Your message")).toHaveValue("")
    await expect(page.getByRole("button", { name: "Cancel reply" })).not.toBeVisible()
  }
  await page.getByRole("button", { name: "Done talking" }).click()
  await expect(page.getByRole("button", { name: "Next round" })).toBeVisible({ timeout: 15000 })
  await expect.poll(async () => JSON.parse((await canvas.getAttribute("data-factions"))!).winston_churchill).toBe(-1)
  await page.screenshot({ path: "../artifacts/screenshots/world-recruited.png", fullPage: true })
  await page.reload()
  await expect(page.locator("canvas")).toHaveAttribute("data-rendered", "true")
  await page.getByRole("button", { name: "Next round" }).click()
  await page.getByRole("button", { name: /^Recruit/ }).first().click()
  await expect(page.getByLabel("Your message")).toBeEnabled()
  await page.getByRole("button", { name: "Done talking" }).click()
  await expect(page.getByText(/Final score: Red/)).toBeVisible({ timeout: 15000 })
  await expect(page.getByRole("link", { name: "New game" })).toHaveAttribute("href", "/world/")
  await page.getByRole("button", { name: "Review final board" }).click()
  await page.getByRole("button", { name: "Review replay" }).click()
  await expect(page.getByLabel("Replay step")).toBeVisible()
  await page.getByLabel("Replay step").fill("0")
  await expect.poll(async () => JSON.parse((await canvas.getAttribute("data-factions"))!).winston_churchill).toBe(0)
  await page.getByRole("button", { name: "Back to live game" }).click()
  await expect.poll(async () => JSON.parse((await canvas.getAttribute("data-factions"))!).winston_churchill).toBe(-1)
  expect(errors).toEqual([])
  expect(external).toEqual([])
})

test("3D motion, camera, pause and runtime reduced motion remain controllable", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "no-preference" })
  await page.goto("/world/")
  await page.getByRole("button", { name: "Start single-player game" }).click()
  const canvas = page.locator("canvas")
  await expect(canvas).toHaveAttribute("data-rendered", "true")
  const before = await canvas.getAttribute("data-targets")
  await expect.poll(() => canvas.getAttribute("data-targets")).not.toBe(before)
  await page.getByRole("button", { name: "Pause", exact: true }).click()
  await expect(canvas).toHaveAttribute("data-motion", "paused")
  const paused = await canvas.getAttribute("data-targets")
  await page.waitForTimeout(250)
  expect(await canvas.getAttribute("data-targets")).toBe(paused)
  await page.getByRole("button", { name: "Rotate scene left" }).click()
  await expect.poll(() => canvas.getAttribute("data-targets")).not.toBe(paused)
  await page.getByRole("button", { name: "Resume", exact: true }).click()
  await page.emulateMedia({ reducedMotion: "reduce" })
  await expect(canvas).toHaveAttribute("data-motion", "reduced")
  const reduced = await canvas.getAttribute("data-targets")
  await page.waitForTimeout(250)
  expect(await canvas.getAttribute("data-targets")).toBe(reduced)
  await page.getByLabel("Board view").selectOption("2d")
  await expect(canvas).toHaveCount(0)
  await expect(page.getByLabel("Influence board")).toBeVisible()
  await page.getByLabel("Board view").selectOption("3d")
  await expect(page.locator("canvas")).toHaveAttribute("data-rendered", "true")
})

test("mouse drags turn and tilt the board without selecting characters or getting stuck", async ({ page }) => {
  const errors: string[] = []
  page.on("pageerror", error => errors.push(error.message))
  await page.goto("/world/")
  await page.getByRole("button", { name: "Start single-player game" }).click()
  const canvas = page.locator("canvas")
  await expect(canvas).toHaveAttribute("data-rendered", "true")
  // With motion disabled, position changes prove camera movement, not idle animation.
  await expect(canvas).toHaveAttribute("data-motion", "reduced")
  const bounds = (await canvas.boundingBox())!
  const original = (await canvas.getAttribute("data-targets"))!
  const target = JSON.parse(original).winston_churchill
  const x = bounds.x + target.x, y = bounds.y + target.y
  await page.mouse.move(x, y)
  await page.mouse.down()
  await page.mouse.move(x + 100, y, { steps: 8 })
  await expect.poll(() => canvas.getAttribute("data-targets")).not.toBe(original)
  await expect(canvas).toHaveCSS("cursor", "grabbing")
  const horizontal = await canvas.getAttribute("data-targets")
  await page.mouse.move(x + 100, y + 60, { steps: 6 })
  await expect.poll(() => canvas.getAttribute("data-targets")).not.toBe(horizontal)
  await page.mouse.up()
  await expect(page.getByRole("dialog")).not.toBeVisible()
  await page.screenshot({ path: "../artifacts/screenshots/world-dragged.png", fullPage: true })

  // Crossing the drag threshold then returning must not become a click.
  const positions = JSON.parse((await canvas.getAttribute("data-targets"))!)
  const next = positions.winston_churchill
  await page.mouse.move(bounds.x + next.x, bounds.y + next.y)
  await page.mouse.down()
  await page.mouse.move(bounds.x + next.x + 40, bounds.y + next.y, { steps: 4 })
  await page.mouse.move(bounds.x + next.x, bounds.y + next.y, { steps: 4 })
  await page.mouse.up()
  await expect(page.getByRole("dialog")).not.toBeVisible()

  // Pointer capture keeps the gesture alive outside the canvas, then releases it.
  await page.mouse.move(bounds.x + 100, bounds.y + 200)
  await page.mouse.down()
  await page.mouse.move(bounds.x - 20, bounds.y + 200, { steps: 8 })
  await page.mouse.up()
  await expect(canvas).toHaveCSS("cursor", "grab")
  await page.waitForTimeout(100)
  const released = await canvas.getAttribute("data-targets")
  await page.mouse.move(bounds.x + 120, bounds.y + 220)
  await page.waitForTimeout(100)
  expect(await canvas.getAttribute("data-targets")).toBe(released)

  for (const event of ["pointercancel", "lostpointercapture", "blur"]) {
    await page.mouse.move(bounds.x + 100, bounds.y + 200)
    await page.mouse.down()
    await page.mouse.move(bounds.x + 125, bounds.y + 220)
    await canvas.evaluate((element, event) => {
      if (event === "blur") window.dispatchEvent(new Event(event))
      else element.dispatchEvent(new Event(event))
    }, event)
    await expect(canvas).toHaveCSS("cursor", "grab")
    await page.waitForTimeout(100)
    const cancelled = await canvas.getAttribute("data-targets")
    await page.mouse.move(bounds.x + 180, bounds.y + 240)
    await page.mouse.up()
    await page.waitForTimeout(100)
    expect(await canvas.getAttribute("data-targets")).toBe(cancelled)
  }
  // Ordinary clicks still pick the actual mesh after camera changes and cancellation.
  const finalTarget = JSON.parse((await canvas.getAttribute("data-targets"))!).winston_churchill
  await page.mouse.move(bounds.x + finalTarget.x, bounds.y + finalTarget.y)
  await page.mouse.down()
  await page.mouse.move(bounds.x + finalTarget.x + 2, bounds.y + finalTarget.y + 1)
  await page.mouse.up()
  await expect(page.getByRole("dialog").getByRole("heading", { name: "Winston Churchill" })).toBeVisible()
  expect(errors).toEqual([])
})

test("crowded mobile 3D and context-loss fallback preserve reachable characters", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto("/world/")
  await page.getByLabel("Characters", { exact: true }).fill("23")
  await page.getByRole("button", { name: "Start single-player game" }).click()
  const canvas = page.locator("canvas")
  await expect(canvas).toHaveAttribute("data-rendered", "true", { timeout: 20000 })
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390)
  await page.screenshot({ path: "../artifacts/screenshots/world-mobile-crowded.png", fullPage: true })
  await page.setViewportSize({ width: 320, height: 568 })
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(320)
  for (const button of await page.getByLabel("Camera controls").getByRole("button").all()) {
    const bounds = (await button.boundingBox())!
    expect(bounds.width).toBeGreaterThanOrEqual(44)
    expect(bounds.height).toBeGreaterThanOrEqual(44)
  }
  await expect(page.getByRole("button", { name: /^Recruit/ })).toHaveCount(23)
  await page.getByRole("button", { name: /^Recruit/ }).last().click()
  await expect(page.getByRole("dialog")).toBeVisible()
  await page.getByRole("button", { name: "Close conversation" }).click()
  await canvas.evaluate(element => element.dispatchEvent(new Event("webglcontextlost", { cancelable: true })))
  await expect(page.getByText("3D is unavailable in this browser.", { exact: false })).toBeVisible()
  await expect(page.getByLabel("Influence board")).toBeVisible()
  await expect(page.getByRole("button", { name: "Open conversation" })).toBeVisible()
  await page.getByRole("button", { name: "Open conversation" }).click()
  await expect(page.getByRole("dialog")).toBeVisible()
})

test("a browser without WebGL can still start and play", async ({ page }) => {
  await page.addInitScript(() => {
    const original = HTMLCanvasElement.prototype.getContext
    HTMLCanvasElement.prototype.getContext = function (this: HTMLCanvasElement, ...args: Parameters<typeof original>) {
      if (String(args[0]).includes("webgl")) return null
      return original.apply(this, args)
    } as typeof original
  })
  await page.goto("/world/")
  await page.getByRole("button", { name: "Start single-player game" }).click()
  await expect(page.getByText("3D is unavailable in this browser.", { exact: false })).toBeVisible()
  await page.getByRole("button", { name: /^Recruit/ }).first().click()
  await expect(page.getByRole("dialog")).toBeVisible()
})

test("character portraits switch reliably, rotate actual meshes and fit narrow screens", async ({ page }) => {
  const errors: string[] = [], external: string[] = []
  page.on("pageerror", error => errors.push(error.message))
  await page.route("**/*", route => {
    if (new URL(route.request().url()).hostname !== "127.0.0.1") { external.push(route.request().url()); return route.abort() }
    return route.continue()
  })
  await page.goto("/characters/")
  const ids = ["albert_einstein", "marie_curie", "winston_churchill", "nelson_mandela", "napoleon_bonaparte", "martin_luther", "genghis_khan", "albert_einstein"]
  for (const id of ids) {
    await page.getByLabel("Choose a character").selectOption(id)
    const canvas = page.locator("canvas")
    await expect(canvas).toHaveAttribute("data-rendered", "true")
    await expect(page.getByText("3D is unavailable", { exact: false })).toHaveCount(0)
    expect((await canvas.screenshot()).byteLength).toBeGreaterThan(10000)
    if (ids.indexOf(id) < 3) {
      await page.screenshot({ path: `../artifacts/screenshots/portrait-${id}-front.png` })
      const front = await canvas.screenshot()
      for (let i = 0; i < 3; i++) await page.getByRole("button", { name: "Turn portrait right" }).click()
      await expect.poll(async () => !(await canvas.screenshot()).equals(front)).toBeTruthy()
      await page.screenshot({ path: `../artifacts/screenshots/portrait-${id}-quarter.png` })
    }
  }
  const portrait = page.locator("canvas")
  const portraitBounds = (await portrait.boundingBox())!
  const beforeDrag = await portrait.screenshot()
  await page.mouse.move(portraitBounds.x + portraitBounds.width / 2, portraitBounds.y + 200)
  await page.mouse.down()
  await page.mouse.move(portraitBounds.x + portraitBounds.width / 2 + 90, portraitBounds.y + 200, { steps: 6 })
  await page.mouse.up()
  await expect.poll(async () => !(await portrait.screenshot()).equals(beforeDrag)).toBeTruthy()
  await page.setViewportSize({ width: 320, height: 568 })
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(320)
  await page.screenshot({ path: "../artifacts/screenshots/portrait-mobile.png", fullPage: true })
  await page.locator("canvas").evaluate(element => element.dispatchEvent(new Event("webglcontextlost", { cancelable: true })))
  await expect(page.getByText("3D is unavailable", { exact: false })).toBeVisible()
  await page.getByLabel("Choose a character").selectOption("marie_curie")
  await expect(page.locator("canvas")).toHaveAttribute("data-rendered", "true")
  expect(errors).toEqual([])
  expect(external).toEqual([])
})
