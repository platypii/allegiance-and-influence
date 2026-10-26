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
