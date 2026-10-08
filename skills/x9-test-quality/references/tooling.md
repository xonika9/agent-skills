# Tooling map

Where the [project audit](project-audit.md) recommendations live in common runners. Flags and defaults change between major versions: read the project's installed version, check the current documentation for that version before recommending a flag, and say so when a cell below no longer holds. The table was checked against Vitest 5.0, Jest 30.5, pytest 9.1 with the named plugins, Go 1.27, and Playwright 1.64.

"none" means the runner documents no built-in equivalent; recommend a plugin or a project convention instead of inventing a flag.

| Capability | Vitest | Jest | pytest | Go | Playwright |
|---|---|---|---|---|---|
| Declared categories, unknown one fails | `test.tags` with per-tag `timeout`/`retry`; `strictTags` (on by default) | none | `markers` + `--strict-markers` (or `strict = true`) | none: `//go:build` tags and `-short` are conventions | none: `@tag` in titles filtered by `--grep` |
| Run one category | `--tags-filter "<expr>"` | `--selectProjects`, `-t` | `-m "<expr>"` | `-tags <tag>`, `-short`, `-run` | `--grep`, `--grep-invert`, `--project` |
| Test and category timeout | `testTimeout`; per-test and per-tag `timeout` | `testTimeout`; per-test argument | plugin `pytest-timeout`: `--timeout`, `@pytest.mark.timeout` | `-timeout` per package binary (default 10m, panics) | `timeout`, `test.setTimeout`, `testProject.timeout` |
| Whole-run timeout | none | none | `pytest-timeout`: `--session-timeout` | none (`-timeout` is per package binary) | `globalTimeout` |
| Affected by a change | `--changed [ref]`, `vitest related <files>` | `--changedSince`, `--findRelatedTests`, `--onlyChanged` | plugin `pytest-testmon` | test cache skips unchanged packages; otherwise use the build graph | `--only-changed [ref]`: changed test files plus test files importing a changed file; code reached only over HTTP is not tracked |
| Random order with seed | `sequence.shuffle`, `sequence.seed` | `--randomize`, `--seed` | plugin `pytest-randomly`: `--randomly-seed` | `-shuffle on` (prints seed) | `--shuffle [seed]` |
| Repeat to expose flakiness | `--repeats N` | none | plugin `pytest-repeat`: `--count N` | `-count N` | `--repeat-each N` |
| Retries and flaky reporting | `--retry.count` | `jest.retryTimes()` in code; no flaky status | plugin `pytest-rerunfailures`: `--reruns` | none | `retries`; `flaky` result; `failOnFlakyTests` |
| Visible known-broken marker | `test.fails`, `test.skip`, `context.skip(cond, msg)` | `test.failing`, `test.skip` | `xfail(reason=, strict=True)`, `skip(reason=)` | `t.Skip(reason)` | `test.fixme`, `test.fail`, `test.skip(cond, reason)` |
| Focused tests fail in CI | `allowOnly` (off in CI by default) | none | n/a | n/a | `forbidOnly` |
| Shard across machines | `--shard i/n` + `blob` reporter + `--merge-reports` | `--shard i/n` | none built in; `pytest-xdist` parallelizes on one machine | none | `--shard i/n` + `blob` reporter + `merge-reports` |
| Snapshots fail instead of writing in CI | default under `CI` (`update` behaves as `none`) | `--ci` | n/a | n/a | `updateSnapshots: 'none'` |
| Race and leak detection | `--detectAsyncLeaks` (slow) | `--detectOpenHandles` | n/a | `-race`; `testing/synctest` for time in concurrent code | n/a |

Notes that change a recommendation:

- Go timeouts and the `-short` flag act per package and by convention; per-size limits need separate packages, build tags, or a helper that fails a test on its own deadline.
- Go caches passing test results per package; medium tests that use external services need `-count=1` so a cached pass cannot hide their failures.
- pytest's `faulthandler_timeout` only prints stack traces; a failing timeout needs `pytest-timeout`.
- Monorepo build tools select affected projects from the dependency graph: `nx affected`, `turbo run --affected`, and Bazel test targets by `size` and `timeout`.
- A quarantine that keeps a test running without blocking needs either a separate non-blocking CI job that runs the quarantined category, or a reporter that treats it as non-fatal; a plain skip does neither.
