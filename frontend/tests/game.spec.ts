import { test, expect, Page } from "@playwright/test"

async function message(page: Page, text: string) {
  await page.getByLabel("Your message").fill(text)
  await page.getByRole("button", { name: "Send message", exact: true }).click()
  await expect(page.getByLabel("Your message")).toHaveValue("")
}

test("two independent players finish, reload, replay, and make no external requests", async ({ browser }) => {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: "reduce" })
  const other = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: "reduce" })
  const external: string[] = []
  const errors: string[] = []
  for (const ctx of [context, other]) {
    await ctx.route("**/*", route => {
      const url = new URL(route.request().url())
      if (url.hostname !== "127.0.0.1") { external.push(url.href); return route.abort() }
      return route.continue()
    })
    ctx.on("page", page => page.on("pageerror", e => errors.push(e.message)))
  }
  const red = await context.newPage()
  const blue = await other.newPage()
  await red.goto("http://127.0.0.1:8765")
  await expect(red.getByRole("heading", { name: "A room full of possibilities" })).toBeVisible()
  await red.screenshot({ path: "../artifacts/screenshots/01-welcome.png" })
  await red.getByLabel("Rounds", { exact: true }).fill("2")
  await red.getByRole("button", { name: "Create local game" }).click()
  await expect(red.getByRole("button", { name: "Join Red" })).toBeVisible()
  const address = red.url()
  await red.getByRole("button", { name: "Join Red" }).click()
  await expect(red.getByText("You are Red", { exact: true })).toBeVisible()
  await blue.goto(address)
  await blue.getByRole("button", { name: "Join Blue" }).click()
  await expect(blue.getByText("You are Blue", { exact: true })).toBeVisible()
  for (let round = 1; round <= 2; round++) {
    await expect(red.getByRole("heading", { name: `Round ${round} of 2` })).toBeVisible()
    await expect(red.getByRole("button", { name: /^Recruit/ }).first()).toBeEnabled()
    await red.screenshot({ path: `../artifacts/screenshots/02-board-round-${round}.png` })
    await red.getByRole("button", { name: /^Recruit/ }).first().click()
    const available = blue.getByRole("button", { name: /^Recruit/ }).filter({ visible: true })
    await expect(available.nth(1)).toBeEnabled()
    await available.nth(1).click()
    await expect(red.getByLabel("Your message")).toBeEnabled()
    if (round === 1) {
      await red.getByLabel("Your message").fill("Let us build something together.")
      await red.getByRole("button", { name: "Send message", exact: true }).click()
      await expect(red.getByRole("button", { name: "Cancel reply" })).toBeVisible()
      await red.screenshot({ path: "../artifacts/screenshots/06-agent-pending.png" })
      await red.getByRole("button", { name: "Cancel reply" }).click()
      await expect(red.getByText("Reply cancelled.", { exact: false })).toBeVisible()
      await red.getByRole("button", { name: "Retry reply" }).click()
      await expect(red.getByRole("button", { name: "Cancel reply" })).not.toBeVisible()
      await expect(red.getByRole("log").getByText("Let us build something together.", { exact: false })).toHaveCount(1)
    } else {
      await message(red, "Let us build something together.")
    }
    await message(red, "We share a purpose.")
    await red.screenshot({ path: `../artifacts/screenshots/03-conversation-round-${round}.png` })
    await red.getByRole("button", { name: "Done talking" }).click()
    await message(blue, "I value your ideas.")
    await message(blue, "Let us work as allies.")
    await blue.getByRole("button", { name: "Done talking" }).click()
    if (round === 1) {
      await expect(red.getByRole("button", { name: "Next round" })).toBeVisible()
      await red.reload()
      await expect(red.getByText("You are Red", { exact: true })).toBeVisible()
      await red.getByRole("button", { name: "Next round" }).click()
    }
  }
  await expect(red.getByRole("heading", { name: "A shared victory — it’s a tie!" })).toBeVisible()
  await expect(blue.getByText("Final score: Red 1 · Blue 1")).toBeVisible()
  await red.screenshot({ path: "../artifacts/screenshots/04-finish.png" })
  await red.getByRole("button", { name: "Review final board" }).click()
  await red.getByRole("button", { name: "Review replay" }).click()
  await expect(red.getByLabel("Replay step")).toBeVisible()
  await red.getByLabel("Replay step").fill("0")
  await expect(red.getByText("Replay · step 1", { exact: false })).toBeVisible()
  await red.getByRole("button", { name: "Back to live game" }).click()
  await expect(red.getByText("Game finished", { exact: true })).toBeVisible()
  expect(external).toEqual([])
  expect(errors).toEqual([])
  await context.close()
  await other.close()
})

test("mobile start screen fits and can create a game", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto("/")
  await page.getByRole("button", { name: "Create local game" }).click()
  await page.getByRole("button", { name: "Join Red" }).click()
  await expect(page.getByText("You are Red", { exact: true })).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390)
  await page.screenshot({ path: "../artifacts/screenshots/05-mobile.png" })
})
