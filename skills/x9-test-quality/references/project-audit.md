# Project audit

Judge how an existing project organizes its testing and guide the owner to a setup that catches regressions at a cost this project can carry. The organizing principle: checks are split by cost and run at different frequencies, so cheap checks give fast feedback on every change and expensive ones still run often enough to stay working.

A missing mechanism is not a finding by itself. A finding is an observed loss of signal or time, or a necessary protection that is absent, together with the smallest change that pays for itself here. The numbers below are heuristics with stated units, not laws; adapt them to the project. Runner mechanics are in [tooling.md](tooling.md); check the exact flag against the current documentation of the project's version before recommending it.

## Contents

- [Scale and scope](#scale-and-scope)
- [Inventory](#inventory)
- [Sizes and timeouts](#sizes-and-timeouts)
- [Run frequency](#run-frequency)
- [Affected-only runs](#affected-only-runs)
- [Service seams](#service-seams)
- [Flaky tests](#flaky-tests)
- [Main branch health](#main-branch-health)
- [Gate hygiene](#gate-hygiene)
- [Isolation and safety](#isolation-and-safety)
- [Environment and data](#environment-and-data)
- [Coverage and gaps](#coverage-and-gaps)
- [CI speed and suite health](#ci-speed-and-suite-health)
- [Beyond the suite](#beyond-the-suite)
- [Findings and report](#findings-and-report)
- [Applying fixes](#applying-fixes)
- [Testing policy file](#testing-policy-file)

## Scale and scope

First classify the project, with the evidence: **solo** (one regular contributor), **small team** (a handful of contributors, one deployable), or **multi-team or multi-service**. Then settle the question the audit answers; a narrow question ("why is CI slow?") inspects only what bears on it.

The scale switches sections off. A section that does not apply is left out of the report, not listed as not applicable.

| Section | Solo | Small team | Multi-team or multi-service |
|---|---|---|---|
| Sizes and timeouts | only when the suite mixes fast and slow tests | yes | yes |
| Scheduled heavy run | only when the full suite exceeds the change-request budget | when such a suite exists | yes |
| Affected-only runs | no | when the full run exceeds the budget | yes |
| Service seams (contracts) | no | when two deployables talk to each other | yes |
| Flaky quarantine | fix or delete; no owner or expiry process | owner and issue; expiry optional | full policy |
| Main branch health | no merge queue, rotation, or owners; revert-first only | required up-to-date branch, revert-first | full section |
| Real database in persistence tests | when the code uses engine-specific features | same | yes |
| Migrations over realistic data | synthetic representative data | same, or masked data when available | masked data |
| Suite health metrics | a list of the slowest tests | slowest and flakiest tests | full metrics |

## Inventory

Work through this list as the audit's internal checklist, limited to the scope; it is not report content. Run only cheap, local, read-only commands, such as listing tests or a fast small-test run; long suites need permission.

- test locations, naming, and how many tests sit at each layer;
- test runner configuration: categories, tags or markers, timeouts, retries, parallelism, ordering, snapshot and coverage settings;
- CI workflows: which jobs run on which events, which block merge, scheduled jobs, caching, sharding, artifacts;
- branch protection and merge settings, and who owns tests, fixtures, and fakes;
- lockfiles, install commands in CI, and how runtime, tool, and CI action versions are pinned;
- database migrations, how CI applies them, and how test data is produced;
- local hooks and task-runner scripts that run tests;
- skipped, quarantined, focused, and expected-failure tests, with their stated reasons;
- a sample of tests per layer, checked against the [junk patterns](../SKILL.md#junk-patterns) and [test-design.md](test-design.md); a deep sweep belongs to a [test audit](test-audit.md);
- a sample of recent refactoring changes: assertions edited by a behavior-preserving change mark tests coupled to implementation;
- recent CI history when accessible: reruns, pass-after-retry results, the slowest jobs, red checks that do not block;
- the project's testing documentation and instruction files;
- when in scope, deployment practice, production configuration checks, and UI accessibility checks.

## Sizes and timeouts

Classify tests by the resources they use, not by name:

| Size | May use | Default timeout per test target |
|---|---|---|
| Small | one process, usually one thread; no network, database, external programs, sleeping, or blocking calls; a filesystem only if hermetic and in memory | 60 s |
| Medium | one machine; several processes and threads, blocking calls, localhost network, a local database, the filesystem; external systems discouraged | 300 s |
| Large | several machines or the whole deployed system, including external services | 900 s |

These are Google's size classes and Bazel's default timeouts, which apply to a whole test target (a file or binary of many cases), not to one test case. Runners such as Jest and Vitest time out each test case, by default after five seconds; keep those per-case defaults unless there is evidence, and never raise them toward the per-target numbers. The timeout turns a hung test into a failure; it is not a target duration.

Larger tests flake far more often, which is one reason to keep them few. Do not impose a shape such as a pyramid or a trophy: the sources disagree on the ideal mix. Flag a suite dominated by end-to-end tests, or one with no medium tests between units and full end-to-end runs, when it shows as slow or flaky feedback.

Folders such as `unit/` and `integration/` are a working convention; flag them only when they leak, such as a "unit" test that opens a database. Where the runner supports it, an undeclared category should be an error so a typo cannot drop tests from a run; elsewhere, do not raise it as a finding.

## Run frequency

| When | What runs | Blocks |
|---|---|---|
| Local, before commit | small tests affected by the change | nothing |
| Every change request | lint and types, small and medium tests (affected, or all while cheap), contract tests, a small end-to-end smoke set | merge |
| Main branch after merge | the full small and medium suites | the next release until fixed |
| Scheduled, such as nightly | the full large and end-to-end suite, extra browsers and platforms, high-iteration property tests | nothing directly; failures get an owner the same day |
| Release | the smoke set: login and the few journeys whose failure stops the business | release |

A heavy suite run only before releases decays silently and is broken exactly when it is needed; when the full suite fits the change-request budget, running it on every change is simpler than any schedule. A useful budget for change-request feedback is about ten minutes; when it grows, apply [CI speed](#ci-speed-and-suite-health) before moving checks out of the blocking path.

## Affected-only runs

Use the build or module dependency graph to run only tests whose code a change can reach. This pays once the full run exceeds the change-request budget. Graph detection misses configuration, generated code, and dynamic dependencies, so the full suite still runs after merge or on a schedule.

## Service seams

Check the boundary between two services with consumer-driven contract tests, such as Pact: the consumer records the requests it makes and the responses it relies on, and the provider verifies it satisfies them, without starting the services together. Contracts complement or replace part of the cross-service end-to-end runs; a few journeys remain for what only the assembled system can show. They fit when both sides are under the project's control, are actively developed, and the consumers are known. They do not fit public APIs with unknown consumers, a provider team that will not run the verification, functional testing of the provider itself, or load testing. For a third-party API, use a double with a drift guard instead (see [test-design.md](test-design.md#test-doubles)).

## Flaky tests

A flaky test passes and fails on the same code. It teaches people to ignore red, so it is a defect in the gate, not noise.

- **Detect.** Retries are off locally and limited in CI, at most two per test. A test that passes only on retry is recorded as flaky, not as passed; rerunning a job until it is green hides the signal. Google reports that tests lose their value as flaky results approach one percent of test runs.
- **Diagnose** before fixing. Classify the cause as timing or UI waiting, environment, data or parallelism, or test order. Repeat the test; compare one worker with many; reproduce in CI-like conditions; run it alone and after its usual neighbours.
- **Quarantine** at the depth the [scale](#scale-and-scope) calls for: move the test out of the blocking set while it keeps running and reporting, with an owner, a linked issue, and an expiry. The expiry is a team convention; 14 days is a reasonable default, or cap how many tests may sit in quarantine. At expiry it is fixed, or deleted with the [evidence](test-audit.md#candidate-evidence) a deletion needs. A plain skip is not quarantine: the test stops reporting and nobody brings it back.
- **Critical checks** guarding security, money, data loss, or the release smoke set stay blocking. When one flakes, the owner decides between fixing it at once and a temporary replacement guard; it never silently leaves the gate.

## Main branch health

Applies at the depth the [scale](#scale-and-scope) calls for. A red main blocks everyone and hides new failures behind the old one.

- Every change is tested against the current main before it merges: a merge queue or merge train in busy repositories, otherwise a required up-to-date branch. A queue bounds integration time by test time, so it needs a fast blocking suite.
- Recommend a policy where a red main is reverted first and fixed on a branch, with a fix forward when the cause is obvious and the fix quick.
- In larger teams someone owns a red main at any moment, such as a rotating build owner, and every heavy test, shared fake, and shared fixture has a named owner whom its failures reach.

## Gate hygiene

Flag each of these when present:

- CI tests that should block merge but do not, or jobs disabled to get a green pipeline; a deliberately advisory job is fine when it is labelled as such;
- focused tests (`only`) allowed to reach CI;
- skips without a reason and a linked issue, a growing skip count, or expected-failure markers that do not fail when the test unexpectedly passes;
- snapshots or golden files that CI writes instead of failing on a mismatch;
- order dependence observed in failures, where random order with a reproducible seed would expose it;
- concurrency bugs in a language with a cheap race detector that CI does not run;
- cached test results for tests whose external dependencies the cache cannot see.

## Isolation and safety

Check that the infrastructure enforces the [isolation practices](test-design.md#isolation) rather than leaving them to each author: per-test reset, per-worker and per-shard data, automatic restore of environment, files, and mocks, test environments separated from production, a guard that keeps destructive tests away from production, and secrets supplied by the CI secret store.

## Environment and data

- **Reproducible runs.** The lockfile is committed and CI installs strictly from it (a frozen or clean install); runtime and tool versions are pinned; no `latest` or floating tags in the test path. Pinning third-party CI actions to a full commit hash is security hardening; rank it low unless the project publishes artifacts or exposes secrets to CI.
- **Real dependencies.** Persistence code is tested against the production engine, as [test-design.md](test-design.md#layer) defines. An in-memory or different-dialect substitute is a high finding when the code uses engine-specific features (JSON types, upserts, locking, raw SQL) or a production-only failure is on record, medium otherwise.
- **Migrations.** CI applies every migration from an empty database and over data that resembles production, synthetic and representative or a masked snapshot, at the depth the scale calls for, since real data breaks migrations that pass on an empty schema. Whether down-migrations are tested is an owner decision.
- **Configuration.** The service starts with each environment's real configuration, secrets replaced, in CI, so a broken config file fails before deployment.
- **Test data.** Production data used for tests is masked; test data in shared or production systems is labelled, isolated, and cleaned up.

## Coverage and gaps

Coverage is a gap finder, as the [retention bar](../SKILL.md#retention-bar) says, and no percentage is right for every project. A global threshold imposed to chase a number turns into a checkbox and invites tests that execute lines without asserting anything; recommend against adding or raising one. Reviewing uncovered lines in changed code is the useful form of the signal. Count files no test loads, and exclude generated code, which inflates the number.

Anything the project would not want to break needs a test, including failure handling, security, accessibility, and performance promises. When a change passes every test and still breaks the product, the product's owner adds the missing test.

Look for gaps by what the code does, in this order: security and access control; money and persistent state; business rules; observability. A gap is a behavior where no realistic mutation would make any test fail; inspect uncovered lines with the mutations from [writing a test](../SKILL.md#writing-a-test).

## CI speed and suite health

When feedback is slow, apply the remedies in order of payoff: cache dependencies and builds; run independent jobs in parallel; skip work unaffected by the change (path filters, [affected-only runs](#affected-only-runs)); shard a suite across machines once it takes more than about five minutes at full local parallelism, without cancelling sibling shards on the first failure, and merge the shard reports; move slow suites to the schedule; only then buy bigger runners. Keep traces, screenshots, and logs only for failed tests, with a retention limit.

Make decay visible at the depth the scale calls for: the flaky rate, feedback time against the budget, the slowest tests, and the age of every skip and quarantine. A simple table of the slowest and flakiest tests is often enough.

## Beyond the suite

Tests cannot cover every production scenario. Note these as complements only when the inventory shows failures that pre-merge tests could not catch, or the owner asks; they are not findings and never replace pre-merge tests:

- for services with live traffic and monitoring: a staged or canary rollout that compares metrics with the baseline, feature flags for risky changes, read-only probes against production, and a rollback known to work;
- for user interfaces: an automated accessibility check in CI, which finds many but not all problems, so manual review remains; visual screenshot comparison only when the rendering environment is pinned.

## Findings and report

Rank only findings in sections the scale enables, by risk:

1. **Critical:** a necessary protection that does not work: required tests that do not block, disabled or silently skipped tests, retry-until-green, destructive tests that can reach production, or security, money, or data-loss paths with no test that would fail.
2. **High:** flaky tests without a policy, observed nondeterminism or order dependence, service seams with no contract or drift guard, a heavy suite that never runs, main often red with no revert policy, migrations never applied in CI, unpinned dependencies in CI installs.
3. **Medium:** cost structure: slow feedback, end-to-end tests doing a small test's job, invisible suite health, heavy tests without owners in larger teams.
4. **Low:** hygiene, readability, and reporting gaps.

Report:

- a one-paragraph verdict that names the scale;
- at most five findings in full, each as evidence (file and line, configuration key, command output, or CI run) → the failure it allows → the smallest fix → its cost, marking any that needs an owner decision;
- the remaining findings one line each;
- a short ordered plan in which each step can land as one change set;
- one line naming what was not inspected.

Keep observed facts separate from inferences. A new tool or a rewritten pipeline needs a concrete defect that nothing smaller fixes. When the project has few tests or no CI, the deliverable is a target setup instead: the classes and run tiers this project needs at its scale, the first tests to write in [gap order](#coverage-and-gaps), and the minimal CI that runs them.

The audit is done when the scoped inventory has been inspected or named as not inspected, the report follows this shape, and the plan covers every critical and high finding.

## Applying fixes

Within the [authority](../SKILL.md#authority) the user granted, apply one plan step at a time and validate it as an [audit batch](test-audit.md#validation). Prove each configuration change by its effect: a category filter selects the expected tests, an undeclared category fails, a focused test fails CI, a quarantined test still runs and reports without blocking.

## Testing policy file

When the user asks for it, record the adopted testing rules in the project, by default as `TESTING.md` at the repository root unless the project keeps such documents elsewhere; update an existing file rather than adding a second one. It is for people and agents working in the project, so it states rules and commands, not the audit's findings, and it stays as short as the project's scale allows.

Record only what the project adopted or already enforces, and mark a rule as planned when its configuration is not in place yet:

- the test classes, what each may use, and how a test declares its class;
- the commands to run small tests, affected tests, one class, and the full suite;
- which checks run locally, on every change, after merge, on a schedule, and before release, and which block;
- the flaky-test policy and which checks may never leave the gate;
- what happens when main is red, and who owns heavy tests, shared fakes, and fixtures;
- how the test environment is made reproducible and how test data and migrations are handled;
- the isolation and safety rules tests follow, and how secrets are provided;
- how coverage is used;
- where new tests go and the [questions](../SKILL.md#writing-a-test) every new test must answer.

Every command in the file has been run, or is listed as not run with the reason, and every rule not marked planned matches the configuration it describes. Agents do not load this file automatically: propose a one-line pointer to it in the repository's agent instruction file, such as `AGENTS.md`, instead of copying its rules there.
