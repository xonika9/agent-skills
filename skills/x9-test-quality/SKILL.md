---
name: x9-test-quality
description: Use when writing, changing, reviewing, or pruning automated tests, or when auditing how a project organizes and runs its tests, including flaky tests and CI test stages, and guiding it to a better setup — «проверь тесты», «почисти тесты», «как устроить тестирование в проекте», «у нас флакают тесты», "audit our test setup". Do not use for only running tests, or for debugging one failure without changing a test or the test setup.
---

# Test quality

Help tests catch regressions without slowing the developer down. This file governs every test written or changed during ordinary work; the deeper modes run only when the user asks for them and load their own reference:

- **Test audit:** find low-value existing tests and remove or repair them. Read [references/test-audit.md](references/test-audit.md).
- **Project audit:** judge how the project organizes testing, scaled to its size, with a short report, approved fixes, and on request a `TESTING.md`. Read [references/project-audit.md](references/project-audit.md).
- **Campaign:** prune one subsystem's whole test surface. Read [references/test-audit.md](references/test-audit.md) and [references/campaign.md](references/campaign.md).

Practices for writing tests are in [references/test-design.md](references/test-design.md); runner mechanics in [references/tooling.md](references/tooling.md).

This skill is model-invoked in Claude Code and Codex; its portable claim is structural Agent Skills compatibility only. It assumes no particular language, test runner, or CI system.

## Authority

What the current task and the repository's rules already authorize continues without new questions: writing and fixing the tests the change needs, small testability refactors such as extracting a pure function (explained in the result), and the project's usual local and CI runs. Ask first when an action widens the scope, adds a recurring or paid cost, touches a shared or production environment or an external service, weakens a protection, or changes a public interface or the architecture.

A request to audit or review, in any mode, is read-only: report and change nothing. A fix or cleanup request authorizes the edits it names or the recommendations the user approved; quarantining a test, changing retry or timeout policy, changing repository settings such as branch protection, required checks, or a merge queue, and adding a blocking gate or scheduled job are approved one by one unless the request named them. An explicit campaign request authorizes the campaign's edits. Commit, push, integrate branches, open a pull request, or merge only when authorized, under the repository's policy.

## Writing a test

Apply this gate silently. It is a few seconds of judgment, not a report; mention it only when it finds a problem, in one line.

Before adding a test, know:

1. the observable behavior or contract it protects;
2. a credible regression that would make it fail;
3. that the one to three nearest tests of the same owner do not already catch that regression; if one nearly does, extend it or its table instead;
4. that it needs no production seam (export, flag, wrapper, injection hook) that no real caller needs. A seam that makes a real contract reachable, such as an injected clock or a pure core extracted from I/O, is fine.

Write it at the owner's boundary: the public interface of the module that owns the behavior, which is not necessarily the highest layer. It must not match a [junk pattern](#junk-patterns) unless the [retention bar](#retention-bar) names the contract it guards. A test whose assertions a behavior-preserving refactor would force to change asserts implementation; write it against the behavior instead. Updating setup or imports after a refactor does not count.

If the user asked for a specific test, write it as asked. When it matches a junk pattern, duplicates an existing test, or sits at a weaker boundary, add one sentence naming the better alternative; switch only if the user agrees.

Do not rewrite or consolidate existing tests the task does not touch; name them as a follow-up instead.

Before finishing, consider a few realistic mutations of the behavior you touched: a wrong constant, the wrong branch, a missing side effect, a default return, missing validation of empty, zero, unauthorized, or malformed input. Cover any credible one with a test; report only those you leave uncaught, one line each, with why.

A bug regression test should be seen failing for the intended reason, on the asserted behavior rather than on broken setup, and then pass with the fix. Running it on the pre-fix code is the default; when that is impractical, reintroduce the defect temporarily, or state why neither is possible. One regression at the owner's boundary covers the bug; a test at another layer needs its own distinct failure, such as the wiring between components.

## Red tests

When a test goes red because of your change:

- if the change intentionally alters that behavior, update the assertion, or regenerate the snapshot after reading its diff (see [snapshots](references/test-design.md#assertions)), and say so in one line;
- if the test asserted an implementation detail, rewrite it against the owner's interface;
- otherwise fix the code.

Never weaken an assertion, skip, or delete a test just to get green, and never weaken repository gates, coverage thresholds, or size baselines to pass. Raise a timeout only with a stated cause other than "it was failing".

A red test outside your change: rerun it once and report it as flaky if it passes. If it fails again and you need to know whether your change caused it, run it on the base commit in a separate worktree, never by discarding or stashing changes; report it as pre-existing if it fails there, otherwise treat it as yours. Then continue the task. If it guards security, money, data loss, or the release smoke set, say that its owner must choose between fixing it now and a temporary replacement guard. Diagnosis and quarantine follow [project-audit.md](references/project-audit.md#flaky-tests) when the user asks.

## Junk patterns

A new test must not match one; a test audit hunts for existing tests that do.

- assertion-free coverage probes, and tests added to raise a coverage number rather than to protect a behavior;
- self-comparisons and identity copiers;
- copied fixtures, inventories, manifests, or export lists;
- exact source, import, or string greps;
- change detectors: tests of a constant's value, exact wording, or private structure that only this code reads, instead of the behavior that depends on it;
- private predicate or call-shape tests duplicated at real boundaries;
- verification through a side channel, such as reading the database, when a public read path exists;
- tests of the framework or a dependency instead of the project's use of it;
- duplicate invocations of the same contract;
- per-integration replays of a shared helper's tests;
- tests whose only purpose is preserving test-only exports, globals, or wrappers;
- expected values produced by the helper or renderer under test;
- doubles that compute the asserted result themselves, so a bug in the real code under test would not turn the test red, or one identical mock standing in for different APIs;
- fixtures that supply the receipt, admission, or callback ordering the owner should produce, or persistence asserted against a store the path never writes;
- capability tests that restate declared flags instead of exercising the delivery or acknowledgement the flag promises;
- negative controls that pass for an unrelated reason, such as a denial from a different guard or a rejection the production path never reaches;
- tests that pass when they cannot run: swallowed exceptions, assertions inside a condition that may be false, skips without a reason;
- property tests that restate the implementation or pass on zero generated cases;
- names or fixtures that promise more than the input exercises, such as a "retires the window" test asserting the window was not cleared.

## Retention bar

A test justifies its cost by protecting behavior, a credible regression, or an independently meaningful contract. A value read by a user, another system, or documentation is a contract; a value read only by this code is not. Keep a test that independently enforces a public API, plugin or extension SDK, protocol, config, migration, storage, security, platform, default, exact prompt or output bytes, generated cross-language, package, release, or architecture contract. Also keep:

- call ordering when order is observable behavior;
- regressions with a credible failure mode;
- source inspection when it is the cheapest independent guard: it fails when the contract changes (the user-facing key, byte, or path) and survives an identifier-only refactor;
- a self-comparison that checks determinism of code that is not obviously pure, such as hashing, serialization, or anything reading a clock;
- a pinning test that deliberately passes on both old and new code to guard adjacent unchanged behavior, when it says that is its purpose;
- a test that fails on the baseline: treat it as a possible product bug rather than deleting it.

Static or slow is not a deletion reason. Coverage locates code no test executes; it does not show that anything is asserted, so treat it as a list of questions, never as a target.

## Checking your work

Run the tests you touched and their owner's sibling tests with the repository's own commands, found in its instruction files, package manifests, task runners, and CI configuration; the package manager is not necessarily the test runner. A result counts only when no file changed during the run.

Repeat a new or changed test only when it uses real time, threads or async concurrency, or shared external state, or has flaked before: about ten runs in random order or one minute, whichever comes first. Where the runner cannot repeat tests, say so. A check that could not run is reported as not run with its reason.
