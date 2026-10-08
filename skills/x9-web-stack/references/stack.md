# Stack and project structure

The template has two parts. **Core** is in every project from day one. **On demand** is added when its named trigger appears, not before. Library specifics are in the [library notes](library-notes.md).

## Core

| Layer | Choice | Why |
| --- | --- | --- |
| Language and runtime | TypeScript in strict mode; Bun for packages, scripts, and the server; Bun workspaces with a root version catalog | One toolchain; the catalog keeps shared versions identical |
| Client | React + Vite | Plain SPA served as static files |
| Server rendering, when SEO or streaming is needed | TanStack Start on the same Router and Query | No second data or routing model |
| UI | Tailwind CSS 4 + shadcn/ui on Base UI; Lucide icons; shadcn `Toast` | Owned component source, accessible primitives |
| Routing | TanStack Router, file-based, generated `routeTree.gen.ts` committed | Typed routes and search params |
| Client data | TanStack Query for server data; TanStack Form with Zod schemas; UI state in React | One cache owner; forms validated by the same kind of schema as the server |
| Server | Hono on Bun | Web-standard `Request`/`Response`, portable to Node for tests |
| API contract | Zod + `@hono/zod-openapi`; client is Hono `hc` over `fetch`, no axios | Types and OpenAPI from one definition |
| Database | PostgreSQL + Drizzle (latest stable line; move to v1 after its stable release), SQL migrations, `postgres` driver | Typed SQL close to the database |
| Quality | Biome (format, lint, module boundaries) + a `typecheck` script (`tsc`; `bun check` once it ships in stable Bun) | Boundaries enforced by the linter, not by prose |
| Tests | Vitest on Node + Testing Library; Playwright for end-to-end | Server tests against real PostgreSQL |
| Packaging | Docker + Compose; Caddy is the only public service and terminates TLS | One origin for client and API |

### Sign-in, when the product needs it

Pick one per project. In every variant the sign-in service only establishes identity; the server checks permissions and verifies tokens itself. Every variant needs outgoing email.

- **A. Full self-hosted Supabase.** Its PostgreSQL is the project database. Choose it when other Supabase parts are wanted: storage, realtime, Studio.
- **B. Own database + Better Auth.** Choose it when everything must live in one Compose project. Users and sessions in the same database; session in an `httpOnly` cookie. Obligation: watch Better Auth security advisories and upgrade quickly.
- **C. Own database + only the Supabase Auth service (`supabase/auth`).** One container on the project database. Choose it for ready sign-in flows and `supabase-js` without the rest of Supabase. Least proven variant; see library notes.

## On demand

| What | Trigger | With |
| --- | --- | --- |
| Database backups and a restore test | before the first real data | scheduled `pg_dump`; pgBackRest when point-in-time recovery is required |
| Outgoing email | first email (confirmation, password reset) | `nodemailer` over an external SMTP provider; Mailpit locally |
| File storage | first upload | Docker volume behind a `storage` module (put, get, delete, signed link); in variant A, Supabase Storage with file backend |
| S3-compatible storage | several servers, direct browser uploads, large volume, or an off-server copy | managed S3 (Hetzner, Backblaze B2, Cloudflare R2); self-hosted Garage; RustFS once mature. Not MinIO: the project is archived |
| Uptime monitoring | first live users | external free service or Uptime Kuma polling `/health` |
| Error tracking | first deployment with live users | Sentry SaaS or self-hosted GlitchTip |
| External service (payments, LLM) | first such service | small module: type, real implementation, and a fake for tests, injected through `createApp` |
| Background jobs | work longer than a request, or scheduled | pg-boss on the same database in a separate process; idempotent handlers; enqueue in the same transaction as the data |
| Bun-specific APIs | `Bun.*` needed outside the entry file | `src/platform/` with small interfaces |
| Rate limiting on costly routes | a public route spends money (LLM, SMS, email) | rate-limit middleware; PostgreSQL or Valkey store with several API instances |
| Shared secrets | a second person or server | SOPS + age for secrets in Git |
| Several UI languages | the second language | Paraglide JS |
| Search | a plain filter is not enough | PostgreSQL full-text search and `pg_trgm` |
| Dead-code search | the project has grown | knip, periodically |
| Complex module boundaries | Biome rules are not enough | dependency-cruiser |
| Runtime validation of own API responses on the client | the client must validate at runtime | a `packages/contract` package with the Zod schemas |
| Editor speed | `hc` type hints become slow | prebuilt server types, one client per module |
| Upload progress | a progress indicator is needed | `XMLHttpRequest` inside `src/api/` |
| One image for several environments | staging and production differ in client settings | the client fetches its settings from the server at startup |
| API versions | an external consumer or mobile app appears | `/api/v1`, deprecation marks, OpenAPI compatibility check in CI |
| Decision records | the project departs from this template or a choice was costly | `docs/decisions/NNNN-title.md`, one page; a module README when it has rules not visible in code |
| Zero-downtime deploys | the app cannot stop during a migration | rule B5 in [rules](rules.md) |

## Project structure

The bootstrap assets are the canonical instance of this layout; read them for the exact code.

```
apps/
  api/
    package.json        # "imports": { "#api/*": "./src/*" }, "exports": { "./contract": ... }
    src/
      modules/orders/
        index.ts        # for other modules: functions and types, never routes
        routes.ts       # HTTP routes; imported only by app.ts
        schemas.ts      # Zod request/response schemas
        service.ts      # product rules: functions (ctx, input)
        queries.ts      # Drizzle queries, always with the access condition
        schema.ts       # the module's tables
        testing.ts      # test-data factories, tests only
      shared/           # closed list: errors, ctx, log, pagination, db columns, problem schema
      db/               # connection, migration runner, schema barrel for drizzle-kit
      app.ts            # createApp(deps): middleware, error handler, route mounting
      contract.ts       # AppType and ErrorCode, the client's only server import
      env.ts            # environment schema, parsed at startup
      index.ts          # entry: real dependencies, Bun.serve, shutdown
    test/               # test app factory, global setup, OpenAPI snapshot test
    migrations/
    openapi.json        # OpenAPI snapshot, updated by a test
  web/
    package.json        # "imports": { "#web/*": "./src/*" }
    src/
      routes/orders/index.tsx   # params, loader, module component
      routes/orders/-components/ # parts of one page
      modules/orders/{index.ts, queries.ts, components/, forms/}
      api/              # hc client, fetch wrapper, error code → message
      components/ui/    # shadcn only
      main.tsx
tests/                  # Playwright end-to-end
AGENTS.md
compose.yaml            # production-shaped; compose.dev.yaml publishes the dev database on loopback
```

Create `packages/`, `scripts/`, `docs/`, and a client `env.ts` when they get content. Extract a shared package at the second real consumer.

Import aliases use `package.json` `imports` with a distinct prefix per workspace (`#api/`, `#web/`), not `tsconfig` `paths`: the client type-checks server files through `AppType`, and `paths` are resolved per program, so a shared `@/` alias breaks server types inside the client.
