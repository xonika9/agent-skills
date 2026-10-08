import { createApp } from "./app";
import { connect } from "./db/client";
import { loadEnv } from "./env";
import { createLogger } from "./shared/log";

// The only file allowed to use Bun.*: tests run on Node.
const env = loadEnv(Bun.env);
const log = createLogger();
const { sql, db } = connect(env.DATABASE_URL);

const app = createApp({
  db,
  log,
  now: () => new Date(),
  // Replace with the chosen sign-in variant's token or session check.
  authenticate: async () => null,
  publicOrigin: env.PUBLIC_ORIGIN,
});

// Keep this at or above the bodyLimit in app.ts so oversized bodies still get
// a problem+json response.
const server = Bun.serve({ port: env.PORT, fetch: app.fetch, maxRequestBodySize: 2 * 1024 * 1024 });
log.info("listening", { port: server.port });

// Stop accepting, finish in-flight requests, then close the pool. The total
// stays under Compose's default 10 s stop grace period.
let stopping = false;
async function shutdown() {
  if (stopping) return;
  stopping = true;
  log.info("shutting down");
  const force = setTimeout(() => server.stop(true), 5_000);
  await server.stop();
  clearTimeout(force);
  await sql.end({ timeout: 3 });
  process.exit(0);
}
process.on("SIGTERM", shutdown);
process.on("SIGINT", shutdown);
