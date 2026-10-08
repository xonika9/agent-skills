import { existsSync } from "node:fs";
import { defineConfig } from "vitest/config";

// Local runs read the root .env; CI sets the variables directly.
const envFile = new URL("../../.env", import.meta.url);
if (existsSync(envFile)) process.loadEnvFile(envFile);

export default defineConfig({
  test: {
    environment: "node",
    globalSetup: ["./test/global-setup.ts"],
    // Database tests share one database, so files run one at a time.
    fileParallelism: false,
  },
});
