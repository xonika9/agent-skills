---
name: x9-performance
description: Use when software is too slow, cannot hold its load, or spends too much memory, CPU, size, or money — to audit where it wastes time or resources, or to find and fix a named problem with measurements — slow pages, requests, queries, jobs, cold starts, local dev feedback, throughput limits, memory growth, high cloud or model bills — «тормозит», «проведи аудит оптимизации», «почему так долго», «не держит нагрузку», «жрёт память», "performance audit", "why is this slow". Not for test or CI speed (x9-test-quality), readability refactors, or implementing an already chosen change when the person does not ask whether it helps.
---

# Performance

Find where a system spends time or resources it does not need to, prove why, and remove the waste without weakening correctness. The method does not depend on the stack.

## Modes

- **Audit:** the person does not know what is wrong. Follow [audit](references/audit.md). An audit leaves no code change behind. When the request also asks to fix, each cheap item that can be verified locally goes through Optimize, one at a time, with the audit's agreed scope and defaults standing in for the metric confirmation; items that cost money, change architecture, or touch shared systems wait for the owner's choice.
- **Optimize:** the person names a problem. Name the metric, find where it goes per [locate](references/locate.md), then change and verify per [measurement](references/measurement.md). A question without a request to fix, such as «почему так долго?», stops after locating and leaves no code change behind.

Route by where the wait is paid: test runs and pipelines belong to x9-test-quality; a developer's machine — dev server, hot reload, local build — belongs here.

Both modes start by reading the project's performance notes and end by updating them as [notes](references/notes.md) describes.

## Name the metric

People describe symptoms, not metrics. Find what the person notices from code, logs, or a quick measurement; when that is not enough, ask one plain question: what do you do, and what do you see then? State the metric in plain words for confirmation: what is measured, from which event to which, in which scenario and conditions. Then settle who pays for it — a person waiting, the system at its load, or a budget — the smallest gain worth keeping, the guard metrics that must not get worse, and the budget. Correctness is always a guard; add what a change could shift, such as memory spent by a cache or money spent by idle capacity.

When the owner cannot give a value, propose one with its reason and label it `assumed`: the minimum gain is the larger of 10% and the spread of at least three baseline runs taken before any change, where spread is (max − min) / median; expected load is the observed peak times two, or `NOT_PROVEN` without data; the budget is 30 minutes of local runs and no paid runs. Keep the work inside the agreed scenario and budget.

## Evidence

Label every claim `measured` (a number from data, with its conditions), `code` (a cause at a file and line, size estimated), `assumed`, or `NOT_PROVEN`. A number proves size, not cause; a static finding is a hypothesis that names the measurement that would confirm it. Report time and money spent inside a model or external provider as a separate part the project cannot shorten; the calls, payloads, and ordering around it remain levers. Measure browser behaviour through x9-browser-session when it is available.

## Delegation

The orchestrator talks to the person, agrees on the metric, holds permissions and decisions, and keeps the journal. Fresh workers read the project, locate causes, run measurements, and make larger edits, so the orchestrator's context holds conclusions rather than files. Give each worker the metric, scenario, conditions, what it must not do, and the reply format: findings with evidence labels, file and line, numbers with their conditions, and the path to raw data instead of the data itself. Use workers whenever the runtime offers them; stay in the main context only for a single search or a small edit, and when a whole step stays there, say so in the report.

- Reading and searching workers may run in parallel; measurements run one worker at a time, because parallel runs on one machine distort each other.
- A worker never asks the person and never takes an action from the ask-first list; it stops and returns the request.
- Before reporting a verdict or a decisive number, the orchestrator checks it against the raw data.

Worker model and effort follow the runtime and the user's own policy. Without subagents, do the work in the main context, keep only short summaries, and say that the run used the reduced mode.

## Authority

Audit and locating read code, logs, traces, metrics, and databases without changing them. Reads of a non-local system stay within what the owner allowed; on a non-local database, only statistics and catalog views such as `pg_stat_statements` are read without asking. Both may add temporary timing marks, measure, profile, or load-test locally, and write the notes as [notes](references/notes.md) describes. Local means the process and every dependency it calls are local or stubbed. A request to fix or optimize authorizes local edits and local measurements, including reversible local trials of larger options such as pre-started instances.

Ask first, naming the target, the number of runs, and the budget in runs or money, before paid runs; any load, profiler, or memory snapshot that touches a non-local system; changes to a cluster, shared environment, shared cache, or the project's verification harness; and executing statements such as `EXPLAIN ANALYZE` on a non-local database. Deploying any change is outside this skill's authority; for a change that alters cost, isolation, or operations, draft the decision under the project's decision rules and ask.

Never buy performance by weakening a test, check, coverage threshold, timeout policy, isolation, or architecture rule, by deleting a wait without replacing the condition it stood in for, or by serving stale data as fresh. Keep credentials, tokens, personal data, and request contents out of worker replies, notes, and reports.

## Stop

Missing data limits the conclusion: name what stayed unmeasured and mark the report `DEGRADED`. A comparison the budget cannot afford is not started; report what it would need.

## Done

- Audit: the report in [audit](references/audit.md#report); after fixes, the before-and-after table.
- Optimize: [locate](references/locate.md#done) for a question; [measurement](references/measurement.md#done) for a fix.
- The notes record this run per [notes](references/notes.md), and temporary timing marks are gone from the diff.

The [onboarding declaration](references/onboarding.json) lists the optional companion skills.
