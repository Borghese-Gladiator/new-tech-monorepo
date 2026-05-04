import { defineConfig, devices } from "@playwright/test";

const SERVER_PORT = 4000;
const WEB_PORT = 3000;
const SERVER_URL = `http://localhost:${SERVER_PORT}`;
const WEB_URL = `http://localhost:${WEB_PORT}`;

export default defineConfig({
  testDir: ".",
  testMatch: "*.spec.ts",
  // Two browser contexts per test + Socket.IO realtime → keep specs serial
  // so flake from cross-test port reuse / DB churn is avoidable.
  fullyParallel: false,
  workers: 1,
  retries: 2,
  reporter: [["list"]],
  timeout: 60_000,
  expect: { timeout: 10_000 },
  use: {
    baseURL: WEB_URL,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: [
    {
      command: "pnpm --filter @gas-city/server run start",
      cwd: "../..",
      url: `${SERVER_URL}/health`,
      env: { PORT: String(SERVER_PORT) },
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
      stdout: "pipe",
      stderr: "pipe",
    },
    {
      command: "pnpm --filter @gas-city/web run dev",
      cwd: "../..",
      url: WEB_URL,
      env: {
        PORT: String(WEB_PORT),
        NEXT_PUBLIC_SERVER_URL: SERVER_URL,
        SERVER_URL,
      },
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      stdout: "pipe",
      stderr: "pipe",
    },
  ],
});
