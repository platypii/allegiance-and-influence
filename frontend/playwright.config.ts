import { defineConfig } from "@playwright/test"

export default defineConfig({
  testDir: "./tests",
  outputDir: "../artifacts/browser-tests",
  timeout: 45000,
  workers: 1,
  retries: 0,
  use: { baseURL: "http://127.0.0.1:8765", viewport: { width: 1440, height: 1000 }, reducedMotion: "reduce", trace: "retain-on-failure", screenshot: "only-on-failure" },
  webServer: [{ command: "bash ../scripts/e2e-server.sh", url: "http://127.0.0.1:8765/api/health", reuseExistingServer: false, timeout: 20000 },
    { command: "GAME_TEST_MODE=model bash ../scripts/e2e-server.sh", url: "http://127.0.0.1:8766/api/health", reuseExistingServer: false, timeout: 20000 }],
})
