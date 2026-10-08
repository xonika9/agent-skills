# Library notes

Facts checked on 2026-10-08 against official documentation, package sources, or a run (`[run]`). Libraries change; when a note decides a fix or a config value, confirm it against the installed version or current documentation first, and treat a contradiction as the note being stale.

## Bun

- Version pinned in `packageManager`; `oven-sh/setup-bun` reads it with `bun-version-file: package.json`. Whether Bun itself enforces the field is unconfirmed.
- `minimumReleaseAge` in `bunfig.toml` is in seconds (604800 = one week) and applies to new resolutions only. [bunfig](https://bun.com/docs/runtime/bunfig)
- Install scripts are blocked by default; setting `trustedDependencies` replaces the built-in trusted list rather than extending it. [lifecycle](https://bun.com/docs/pm/lifecycle)
- `bun ci` is the frozen-lockfile install; Bun does not freeze automatically in CI. [install](https://bun.com/docs/pm/cli/install)
- `bun audit --audit-level=high --prod`; `bun pm diff` shows new install scripts between versions. [audit](https://bun.com/docs/pm/cli/audit)
- Isolated installs are the default for new workspaces; pin `linker = "isolated"` explicitly. [isolated installs](https://bun.com/docs/pm/isolated-installs)
- `package.json` `imports` with `#api/*` resolve in Bun 1.4.2, TypeScript 7, Vitest 5, Vite 8, and drizzle-kit; a bare `#/*` prefix does not resolve in Bun 1.4.2. [run]
- `bun check` (typescript-go inside Bun, [PR #44361](https://github.com/oven-sh/bun/pull/44361)) exists only in canary builds as of this date. It defers to a `check` script in `package.json`, so name the type-check script `typecheck`. [bun check](https://bun.com/docs/runtime/check)
- `Server.stop()` waits for in-flight requests; `stop(true)` closes them. [Server.stop](https://bun.com/reference/bun/Server/stop)

## TypeScript 7

- `baseUrl` is an error in 7.0; `strict` on and empty `types` are defaults since 6.0, so list `types` explicitly (`["bun"]`, `["vite/client"]`). [TS 7.0](https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/)
- No programmatic API until 7.1; tools that import `typescript` need it aliased to `@typescript/typescript6`. dependency-cruiser silently degrades under TS 7. [#1069](https://github.com/sverweij/dependency-cruiser/issues/1069)
- `allowImportingTsExtensions` with `noEmit` lets every tool share `.ts`-suffixed imports. [run]

## Hono and the contract

- `csrf` middleware inspects only form content types; JSON APIs with cookies need their own `Sec-Fetch-Site`/`Origin` check. [csrf](https://hono.dev/docs/middleware/builtin/csrf)
- `bodyLimit` requires `maxSize`; Bun's `maxRequestBodySize` fires first when smaller and bypasses `onError`. [body limit](https://hono.dev/docs/middleware/builtin/body-limit)
- `secureHeaders` sends no Content-Security-Policy unless configured.
- `@hono/zod-openapi`: `defaultHook` is per `OpenAPIHono` instance; route types reach `AppType` only through chained `.openapi()` calls and `.route()`. [Hono RPC](https://hono.dev/docs/guides/rpc)
- `hono/client` `parseResponse` throws `DetailedError` whose `detail.data` holds the parsed `application/problem+json` body. [run]
- `strict: true` is required on both sides or `hc` loses types. [Hono RPC](https://hono.dev/docs/guides/rpc)

## Drizzle and PostgreSQL

- Stable line 0.45.x; v1 is a release candidate. The website documents v1, so check examples against the installed version.
- The migrator takes no lock (parallel runs race, [#874](https://github.com/drizzle-team/drizzle-orm/issues/874)) and applies all pending migrations in one transaction, so `CREATE INDEX CONCURRENTLY` fails inside it ([#860](https://github.com/drizzle-team/drizzle-orm/issues/860)).
- The migrator applies only migrations whose folder timestamp is newer than the last applied one and skips older ones without error (`pg-core/dialect.js`, 0.45.3). [run]
- `PgDatabase<PostgresJsQueryResultHKT>` accepts both the root database and a transaction when `drizzle()` is called without a schema. [run]
- `uuidv7()` is built in from PostgreSQL 18. [UUID functions](https://www.postgresql.org/docs/current/functions-uuid.html)
- The `postgres:18` image keeps data under `/var/lib/postgresql`; mount that path. [postgres image](https://hub.docker.com/_/postgres)

## Client

- TanStack Query: `ensureQueryData`, `fetchQuery`, `prefetchQuery` are deprecated; use `queryClient.query(options)`, with `staleTime: 'static'` for `ensureQueryData` behaviour. [QueryClient](https://tanstack.com/query/latest/docs/reference/QueryClient)
- TanStack Router: `tanstackRouter({ target: 'react', autoCodeSplitting: true })` before `react()`; register the router type; Zod 4 schemas go straight into `validateSearch`; with Query set `defaultPreloadStaleTime: 0`. [data loading](https://tanstack.com/router/latest/docs/framework/react/guide/data-loading)
- Vite 8 bundles with Rolldown (`build.rolldownOptions`); React Compiler runs through `@rolldown/plugin-babel` with `reactCompilerPreset()` and needs `@babel/core`. [migration](https://vite.dev/guide/migration), [React Compiler 1.0](https://react.dev/blog/2025/10/07/react-compiler-1)
- Vite does not type-check. [Vite features](https://vite.dev/guide/features)
- Testing Library unmounts between tests automatically only when Vitest globals are enabled; otherwise call `cleanup` in `afterEach`. [run]
- shadcn defaults to Base UI and ships its own `Toast` (July 2026); Sonner remains in the Radix branch. [Toast](https://ui.shadcn.com/docs/changelog/2026-07-toast)

## Biome

- Rules run at 2.5.15 [run]:
  - `noRestrictedImports` patterns match the import string as written, including relative paths and `#` aliases;
  - `!` negation works inside a group;
  - when several `overrides` match a file, the last one replaces the rule's whole option list, so each override restates its complete set;
  - `noImportCycles` follows `#` aliases.
- `linter.rules.recommended` is deprecated in favour of `preset: "recommended"`. [run]
- `noImportCycles` is not in the recommended set and is costly; `noFloatingPromises` is nursery, so keep it a warning. [noImportCycles](https://biomejs.dev/linter/rules/no-import-cycles/)

## Sign-in

- `@supabase/ssr` cookies are not `httpOnly` by default; an `httpOnly` session in variants A and C requires server-side sign-in handlers that set the cookie.
- Verify Supabase tokens with `jose` against the JWKS: algorithm allowlist (`ES256`), `iss`, `aud: "authenticated"`. [JWTs](https://supabase.com/docs/guides/auth/jwts)
- Self-hosted Supabase uses Envoy as its gateway; signing keys go in `JWT_KEYS`/`JWT_JWKS`, read by the auth service as `GOTRUE_JWT_KEYS`, which the official Compose ships commented out. [self-hosted keys](https://supabase.com/docs/guides/self-hosting/self-hosted-auth-keys)
- Variant C: pre-create the `supabase_auth_admin` role and the `auth` schema; a `postgres` role must exist. No public end-to-end example was found. [init_postgres.sql](https://raw.githubusercontent.com/supabase/auth/master/hack/init_postgres.sql)
- Better Auth had several 2026 advisories; use a version at or above the latest fixed release. [advisories](https://github.com/better-auth/better-auth/security/advisories)

## Storage and operations

- MinIO's repository was archived on 2026-04-24; use managed S3, Garage, or RustFS once mature.
- Docker `json-file` logs grow without `max-size`/`max-file`. [compose services](https://docs.docker.com/reference/compose-file/services/)
- Dependabot supports `package-ecosystem: bun` with `cooldown` but sends no security updates for Bun. [Dependabot](https://docs.github.com/en/code-security/dependabot)
