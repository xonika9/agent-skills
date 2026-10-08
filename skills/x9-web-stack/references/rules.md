# Development rules

Each rule has a stable ID, a **principle**, the **template** form, and what **enforces** it in the template. Audits cite IDs; the `AGENTS.md` block draws from this pool (see [agents-block.md](agents-block.md)). "Prose" means nothing mechanical catches a violation, so the rule must live in instructions or review.

Rules tagged **(convention)** state one reasonable choice among several. On another stack they apply only where the project has no consistent convention of its own; the other principles hold on any stack.

## Structure

- **S1 Public module entry.** Principle: code is grouped by domain area; other areas use a module only through its declared public surface. Template: `index.ts` exports functions and types, never routes; inside a module imports are relative, across modules only `#api/modules/<name>/index.ts`. Enforced: Biome `noRestrictedImports`.
- **S2 Data ownership.** Principle: one module owns each table and every write to it; others call its functions. Foreign-key references are allowed. Template: tables in the module's `schema.ts`; `db/schema.ts` only collects them for drizzle-kit. Enforced: prose (Biome blocks importing another module's `schema.ts`, not raw SQL).
- **S3 Dependency direction.** Principle: no cycles; a lower module never imports a higher one; when two modules need each other, move the shared part down or merge them. Side effects after commit go through a job enqueued in the same transaction. Enforced: Biome `noImportCycles`; direction is prose.
- **S4 Explicit dependencies.** Principle: business functions receive their dependencies (database, actor, logger, clock) instead of reaching for globals or the HTTP framework. Template: `fn(ctx, input)`; `createApp(deps)`; `index.ts` passes real dependencies, tests pass their own. Enforced: Biome forbids `hono` outside `routes.ts`/`app.ts` and `db/client.ts` outside `index.ts`, `db/migrate.ts`, tests.
- **S5 Transaction owner.** Principle: the module whose action it is opens a cross-module transaction and passes it down. Template: `ctx.db.transaction(tx => other.fn({ ...ctx, db: tx }, ...))`; `Db` is typed so a transaction satisfies it. Enforced: prose.
- **S6 Closed shared code.** Principle: shared code holds infrastructure only (errors, context, pagination, column helpers, time), no domain concepts, and never imports modules; code moves there at its second consumer. Enforced: Biome blocks module imports from `shared/`; content is prose.
- **S7 Thin client routes.** Principle: route files only bind URL, data loading, and a module component; queries, mutations, components, and forms live in the client module; `src/api/` only holds the client, the fetch wrapper, and error messages. Enforced: Biome blocks `hono` and `api/*` outside `src/api/` and deep imports across client modules; thinness is prose.
- **S8 Tests beside code.** Principle: tests live next to the code they cover and build data through the owning module's factories; the root `tests/` holds only end-to-end tests. Enforced: Biome restricts `testing.ts` to tests; placement is prose.

## Dependencies and supply chain

- **D1 Reproducible installs.** Principle: the lockfile is committed and CI installs exactly it; manifests keep version ranges and stay on the latest releases. Exact pins in manifests are the project's own choice, not an audit finding. Template: `bun.lock`, `bun ci`. Enforced: CI.
- **D2 One toolchain version.** Principle: the runtime version is pinned in one place and images and CI follow it; upgrade only after a full CI run. Template: `packageManager`, `oven/bun:<same>` images, `setup-bun` reading `package.json`. Enforced: prose (nothing compares the Dockerfiles with `packageManager`).
- **D3 Dependencies earn their place.** Principle: add a library or service only for a concrete need the platform and existing choices cannot meet. Enforced: prose.
- **D4 Release delay and scripts.** Principle: new versions wait before install; dependency install scripts are opt-in; updates arrive through a bot with a cooldown; vulnerability audit runs on dependency changes and on schedule without blocking unrelated merges; advisories for the auth library, router, and server framework are watched. Template: `minimumReleaseAge` in `bunfig.toml`, minimal `trustedDependencies`, Dependabot `cooldown`, `audit.yml`. Enforced: configuration; watching advisories is prose.

## Portability and configuration

- **P1 Web-standard server code (convention).** Principle: server code uses web standards so tests can run on another runtime; runtime-specific APIs sit only in the entry file or behind `src/platform/`. Enforced: Biome `noRestrictedGlobals` for `Bun`.
- **C1 Validated environment.** Principle: settings come from the environment and are validated by a schema at startup; `.env.example` lists them without secrets. Enforced: code (`env.ts`).
- **C2 Public client settings.** Principle: everything the client build sees is public; secrets stay on the server. Template: every `VITE_` variable is public. Enforced: prose.
- **C3 One origin (convention).** Principle: client and API are served from one origin through the proxy. Template: Caddy proxies `/api`; Vite `server.proxy` in development. Enforced: configuration.

## Contract and client

- **K1 Validate what enters.** Principle: everything entering the server is validated at runtime: requests, configuration, responses from third parties. The client trusts its own API by types unless runtime validation is required. Enforced: code for routes and env; third-party responses are prose.
- **K2 Typed route chain.** Principle: the API type the client depends on must be complete. Template: routes chained with `.openapi()` and mounted with `.route()`, explicit status in every `c.json`; otherwise `AppType` loses routes silently. Enforced: client typecheck fails on missing routes.
- **K3 Visible contract changes (convention).** Principle: the API description is committed and regenerated by a test, so every contract change appears in diffs. Template: `openapi.json` via `toMatchFileSnapshot`, updated with `vitest run -u`. Enforced: test.
- **K4 Additive API changes.** Principle: change the API by adding; remove a field only over two releases. Enforced: prose.
- **K5 One network layer.** Principle: all client requests pass through one wrapper that owns shared headers and 401 handling. Template: `src/api/client.ts` passes its `fetch` to `hc`. Enforced: Biome forbids `hono`, `api/*`, and the global `fetch` outside `src/api/`.
- **K6 Release-safe client.** Principle: a deploy must not strand open tabs on missing chunks. Template: `index.html` served `no-cache`, hashed assets `immutable`; reload once on `vite:preloadError`. Enforced: configuration and code.

## Access

- **A1 Server decides.** Principle: the server checks permission for every action and every object, owns writes to product data, and denies by default. Enforced: prose.
- **A2 Scoped queries.** Principle: every data query carries the access condition (owner or team), so another user's object and a missing one get the same 404. Enforced: prose plus A4 tests.
- **A3 Explicit response fields.** Principle: responses list their fields explicitly so new columns never leak. Template: a `toDto` per resource. Enforced: prose.
- **A4 Access tests.** Principle: tests for reaching another user's objects are mandatory for every resource. Enforced: prose (review).

## Errors

- **E1 Problem details (convention).** Principle: errors use RFC 9457 `application/problem+json` with a stable `code`, field `errors`, and `requestId`. Unknown routes answer in the same format. Enforced: code (`onError`, `notFound`, `rejectInvalid`).
- **E2 One code registry.** Principle: error codes live in one registry, namespaced by module (`orders.not_found`); a code never changes meaning. Enforced: prose.
- **E3 Every code has a message.** Principle: the client maps every code to a message, and the build fails when one is missing; field errors appear on the form. Template: `Record<ErrorCode, string>`. Enforced: typecheck.
- **E4 Bounded retry.** Principle: retry only network errors and 5xx. Enforced: code (`shouldRetry`).

## Protection

- **X1 Security headers.** Principle: security headers and an explicit Content Security Policy on the HTML documents and on API responses. Template: Caddy for the client files, `secureHeaders` with CSP for the API (Hono's default has none). Enforced: configuration.
- **X2 Body limit.** Principle: an explicit request-body limit at the framework, with the runtime limit not below it. Enforced: code.
- **X3 Cross-origin writes.** Principle: one middleware rejects state-changing requests from another origin, including bodiless ones. Template: `Sec-Fetch-Site`, then `Origin`, in `app.ts`. Enforced: code and test.
- **X4 Sign-in rate limit.** Principle: sign-in and other abusable routes are rate-limited. Enforced: prose.
- **X5 Trusted client address.** Principle: behind a proxy, the client address comes only from the trusted proxy's header. Enforced: prose.

## Operations

- **O1 Structured logs.** Principle: JSON logs to stdout with a request id, never secrets or personal data. Enforced: code for format; content is prose.
- **O2 Health route.** Principle: a cheap `/health` endpoint. Enforced: code.
- **O3 Graceful shutdown.** Principle: on `SIGTERM` stop accepting, finish in-flight requests within the container stop timeout, close the pool. Enforced: code (`index.ts`).
- **O4 Container hygiene.** Principle: application containers use exec-form `CMD`, `init: true`, and a non-root user; only the proxy publishes ports; every service rotates its logs. Enforced: configuration.

## Database

- **B1 Versioned migrations.** Principle: schema changes only through versioned migrations whose SQL is reviewed; `push` is local only; applied migrations are never edited. A branch's migration must be newer than the newest one on the main branch: the Drizzle migrator silently skips older ones, so regenerate it after merging main. Template: `drizzle-kit generate`, `drizzle-kit check`. Enforced: `db:check` for consistency; review, immutability, and ordering are prose.
- **B2 Fresh and upgrade paths.** Principle: tests build the database from scratch; CI applies the base branch's migrations, then the branch's. Enforced: test setup and CI.
- **B3 Migrations before start.** Principle: migrations run as a separate single-runner deploy step before the new version starts. Template: Compose `migrate` service. Enforced: configuration.
- **B4 Schema conventions.** Principle: UUID keys with `gen_random_uuid()` (`uuidv7()` once every database runs PostgreSQL 18); `timestamptz`; money as `numeric` or integer minor units; `created_at`/`updated_at` on every table; explicit snake_case column names; indexes on foreign-key columns; `NOT NULL`, `UNIQUE`, `CHECK`, and foreign keys in the database. Enforced: prose.
- **B5 Online migrations.** Principle: when downtime is unacceptable, expand then contract, build indexes `CONCURRENTLY` outside the migrator's transaction, set `lock_timeout`. Enforced: prose; on demand.

## Conventions

- **N1 Clock from context.** Principle: time-dependent logic reads time from `ctx.now()`, not `new Date()`. Enforced: prose.
- **N2 Names (convention).** Principle: kebab-case files; `/api/<plural>/:id`; camelCase JSON; ISO-8601 UTC timestamps in the API. Enforced: prose.
- **T1 Server tests.** Principle: real PostgreSQL of the production major version; migrations once per run; each test creates its own data; database tests run serially or with a database per worker. Enforced: Vitest configuration; isolation is prose.

## Verification

- **V1 One verify command.** Principle: one command runs lint, typecheck, tests, migration check, and build; CI, people, and agents run it before merging. The bundler does not type-check, so typecheck is its own step. Template: `bun run verify`. Enforced: CI.
- **V2 Generated files.** Principle: generated files are regenerated, never edited: applied migrations, `routeTree.gen.ts`, `openapi.json`, `bun.lock`. Enforced: prose.
- **V3 Lint over prose.** Principle: a rule a linter can check is configured in the linter, not written as an instruction. Enforced: this pool.
