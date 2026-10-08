import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";

// Imported only by src/index.ts, src/db/migrate.ts and test setup; everything
// else receives the database through ctx.
export function connect(url: string, max = 10) {
  const sql = postgres(url, { max });
  return { sql, db: drizzle(sql) };
}
