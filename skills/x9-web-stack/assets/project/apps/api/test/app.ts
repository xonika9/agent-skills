import { afterAll } from "vitest";
import { createApp } from "../src/app";
import { connect } from "../src/db/client";
import { silentLogger } from "../src/shared/log";
import { testDatabaseUrl } from "./global-setup";

export const publicOrigin = "https://app.test";
export const { db, sql } = connect(testDatabaseUrl(), 2);
afterAll(() => sql.end());

// The test identity comes from a header so each test can act as anyone.
export const app = createApp({
  db,
  log: silentLogger,
  now: () => new Date("2026-01-01T00:00:00Z"),
  authenticate: async (request) => {
    const userId = request.headers.get("x-test-user");
    return userId ? { userId } : null;
  },
  publicOrigin,
});

export const as = (userId: string, init: RequestInit = {}): RequestInit => ({
  ...init,
  headers: { "x-test-user": userId, "content-type": "application/json", ...init.headers },
});
