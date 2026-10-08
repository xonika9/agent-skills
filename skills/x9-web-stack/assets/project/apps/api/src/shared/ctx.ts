import type { PgDatabase } from "drizzle-orm/pg-core";
import type { PostgresJsQueryResultHKT } from "drizzle-orm/postgres-js";
import type { Logger } from "./log";

// Both the root database and a transaction satisfy this type, so module
// functions accept either through ctx.db.
export type Db = PgDatabase<PostgresJsQueryResultHKT>;

export type Actor = { userId: string };

export type Ctx = {
  db: Db;
  actor: Actor | null;
  log: Logger;
  now: () => Date;
};

export type AppEnv = { Variables: { ctx: Ctx; requestId: string } };
