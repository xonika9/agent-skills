import { fileURLToPath } from "node:url";
import { migrate } from "drizzle-orm/postgres-js/migrator";
import { connect } from "./client";

// Deploy step: run once, by one process, before the new app version starts.
// The migrator takes no lock, wraps pending migrations in one transaction (so
// CREATE INDEX CONCURRENTLY needs a separate script), and skips any migration
// older than the last applied one.
const url = process.env.DATABASE_URL;
if (!url) throw new Error("DATABASE_URL is required");
const { sql, db } = connect(url, 1);
await migrate(db, { migrationsFolder: fileURLToPath(new URL("../../migrations", import.meta.url)) });
await sql.end();
