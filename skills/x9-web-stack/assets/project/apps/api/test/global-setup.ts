import { fileURLToPath } from "node:url";
import { migrate } from "drizzle-orm/postgres-js/migrator";
import { connect } from "../src/db/client.ts";

// Rebuilds the test database from migrations once per run, so a fresh
// database is what the tests always see.
export default async function setup() {
  const { sql, db } = connect(testDatabaseUrl(), 1);
  await sql.unsafe("DROP SCHEMA IF EXISTS drizzle CASCADE; DROP SCHEMA public CASCADE; CREATE SCHEMA public;");
  await migrate(db, { migrationsFolder: fileURLToPath(new URL("../migrations", import.meta.url)) });
  await sql.end();
}

export function testDatabaseUrl() {
  const url = process.env.TEST_DATABASE_URL;
  if (!url) throw new Error("TEST_DATABASE_URL is required for tests");
  // The setup drops every table; refuse anything that is not a test database.
  const parsed = new URL(url);
  if (parsed.hostname === "[::1]") {
    throw new Error("TEST_DATABASE_URL cannot use an IPv6 URL with this driver; use localhost or 127.0.0.1");
  }
  if (!["localhost", "127.0.0.1"].includes(parsed.hostname)) {
    throw new Error("TEST_DATABASE_URL must use a loopback host; remote database resets are forbidden");
  }
  if (!parsed.pathname.endsWith("_test")) throw new Error("TEST_DATABASE_URL must name a *_test database");
  return url;
}
