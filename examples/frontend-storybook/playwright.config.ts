import type { PlaywrightTestConfig } from "@playwright/test";

const config: PlaywrightTestConfig = {
  testDir: "./tests/visual",
  snapshotDir: "./tests/visual/__snapshots__",
  reporter: [["line"]],
  use: {
    baseURL: "http://127.0.0.1:6006",
    trace: "retain-on-failure"
  }
};

export default config;
