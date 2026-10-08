# Test design

Practices for writing or rewriting a test that passes the [gate in SKILL.md](../SKILL.md#writing-a-test). Each one closes a known way for a suite to lie, flake, or cost more than it protects. Runner-specific mechanics live in [tooling.md](tooling.md).

## Contents

- [Layer](#layer)
- [Determinism](#determinism)
- [Isolation](#isolation)
- [Test doubles](#test-doubles)
- [Assertions](#assertions)
- [Readability](#readability)
- [Properties and executable examples](#properties-and-executable-examples)
- [Code without tests](#code-without-tests)

## Layer

Choose the cheapest test that gives confidence the behavior works. Logic belongs in small tests; persistence, transport, and framework wiring in medium tests against real local dependencies; end-to-end tests cover only critical user journeys. Edge cases, validation rules, and API contracts do not need an end-to-end run.

A real dependency in a medium test means the same engine and major version as production, started in a disposable container when needed. An in-memory substitute with another dialect, such as SQLite or H2 standing in for PostgreSQL, passes while production queries fail. This applies to tests of the persistence code itself; small tests of logic that uses it may take a fake at the repository interface.

Each layer asserts what only it can verify, as the [gate](../SKILL.md#writing-a-test) requires. Between services, prefer a contract test over a cross-service end-to-end run (see [project-audit.md](project-audit.md#service-seams)).

End-to-end tests prepare state through an API or direct seeding, not through the UI, and log in through an API or a stored session, except tests of the login flow itself.

Reuse the fixtures and factories of the nearest tests found by [gate](../SKILL.md#writing-a-test) question 3, giving each test only the fields it cares about as overrides.

## Determinism

- Never wait a fixed duration. Wait for an observable condition with a deadline, and fail with a message naming what did not happen. A sleep that "fixes" a flake only makes it rarer.
- Start tests against a server only after a readiness probe (port or health endpoint) succeeds within a timeout.
- Control time, timezone, randomness, and generated IDs: inject a clock, freeze time, seed random data and print the seed so a failure can be replayed.
- A test passes in any order and in parallel. Shared mutable state between tests is a defect, not a convenience.

## Isolation

- Reset the state a test depends on before it runs, not only after: an interrupted run must not poison the next one. Teardown cleanup is a complement, not the guarantee.
- Parallel workers and CI shards get unique data; include the shard identity, since worker numbers repeat on every shard. No shared "god" account: each role is its own account.
- Files, environment variables, globals, and mocks go through sandboxes that restore automatically (temporary directories, environment stubs, automatic mock reset).
- Tests that move money, send messages, or delete data cannot run against production; guard them by environment. Secrets come only from the environment, and stored login state is never committed.

## Test doubles

- Prefer, in order: the real implementation when it is fast, deterministic, and simple to set up; a fake, meaning a working lightweight implementation such as an in-memory store; a stub returning canned values; and only then a mock that verifies interactions.
- Replace only boundaries that are slow, nondeterministic, or outside your control: third-party services, time, randomness, sometimes the network, filesystem, or storage behind a repository interface. Prefer not to mock your own modules; when you do, say why the real one is unsuitable.
- Prefer the existing fake from the real implementation's owner. A new fake lives beside the real implementation instead of being rewritten by each caller; once several test files share it, it passes the same contract tests as the real implementation so it cannot drift.
- A double is faithful in every field and side effect the code under test uses; a mock that omits a field the code reads passes while integration breaks. Learn the real method's side effects before replacing it, so the double does not swallow a write the test relies on.
- Give each branch (success, error, malformed response) its own specific double; a fake that accepts anything verifies nothing.
- When mock wiring dominates a test, widen the unit or move the case to a medium test, and say which.
- A double of a third-party service needs a drift guard: a contract test, or a recorded real response refreshed on a schedule.
- Assert call counts or call order only when they are the contract, such as "a failing call is retried three times and the fourth never happens".
- Use the boundary double to test failure paths: inject errors, timeouts, and latency, and assert the retry, fallback, or error the caller actually sees.

## Assertions

- Assert the strongest property the code supports: no crash < type preserved < invariant < idempotence < round trip or independent oracle. A sort test checking only length leaves order unprotected.
- Expected values are literals derived independently of the code under test; a table-driven test with literal expectations is the preferred shape. A missing exception is an assertion only when not throwing is the contract.
- One behavior per test; several assertions are fine when they describe that one behavior. Split a test whose failure would not say which behavior broke.
- Snapshot and golden files stay small and focused, are never written by CI, are reviewed as diffs, and are updated only after reading why the output changed.

## Readability

A test is read most often when it fails, by someone who did not write it.

- The name states the behavior and its condition, so a failure report alone says what broke.
- Everything the assertion depends on is visible in the test body. Share setup that is incidental to the assertion, but keep the values the assertion depends on in the test even at the cost of some duplication; a helper asserts one fact.
- No conditionals or computed expectations in the test body outside property tests; straight-line code is its own proof. A table-driven loop over literal cases is the exception.
- A failure message names the expected value, the actual value, and the relevant input.
- Test code is reviewed to the same standard as production code.

## Properties and executable examples

- When code has an algebraic shape (round trip, idempotence, invariant, oracle), a property-based test covers more than added examples. Put constraints into the generator rather than filtering inputs, keep known edge cases (empty, single, duplicates, zero, maximum) as explicit examples, and keep the failing seed reproducible.
- Code examples in documentation run as tests that check their output; an example that only compiles drifts silently.

## Code without tests

Before refactoring code that has no tests, or making a risky change to it, propose characterization tests at the boundary you are about to change, and write them when the user agrees or the task already includes tests: they record what the code does now, including behavior that looks wrong, so the change shows exactly what moved. Their expected values are observed from the current code, the one exception to independently derived literals, and their names say they characterize current behavior. Introduce only the seams that pass [gate](../SKILL.md#writing-a-test) question 4. When a recorded behavior turns out to be a bug, fix it as a separate, stated change and update its test there.
