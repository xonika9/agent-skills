---
name: x9-loop-engineering
description: Use when designing a repeated agent loop, manager/orchestrator skill, multi-agent workflow, evaluator/optimizer cycle, or long-running autonomous process, including turning a recurring manual workflow into one reusable skill — «спроектируй агентный цикл», «оберни ручной процесс в скилл», «сделай скилл-оркестратор», «спроектируй multi-agent workflow», "design an agent loop", "design a graph-structured workflow". Do not use for auditing ordinary Agent Skills, one-off delegation, simple linear scripts, ordinary project planning, or adding multiple agents without a demonstrated coordination need.
---

# Loop engineering

Design loops as bounded decision systems, not repeated prompts.

## Qualify the loop

Build a loop only when the work recurs, its state can live in durable artifacts, and coordination or repeated verification is a meaningful part of the cost. If the task is one-off, state is only conversational, or human judgment dominates the work, recommend a bounded delegation or linear workflow instead of adding loop machinery.

## Qualify the topology

Default to the smallest topology that can satisfy the contract:

- one agent when one context, toolset, and authority boundary are sufficient;
- a linear workflow when order matters but no branching or independent ownership is needed;
- a static graph when work has stable parallel branches, specialist ownership, joins, or independent gates;
- a dynamic graph only when evidence discovered at runtime can legitimately create, cancel, merge, or reorder work.

Add a node only when it provides distinct context, tools, authority, evidence, or parallel capacity. Do not create agents merely to simulate job titles, add agreeable reviewers, or make the workflow look multi-agent.

## Invariants

Every production loop needs:

- an explicit outcome, decision contract, and authority for each load-bearing decision;
- the smallest sufficient topology, with a demonstrated responsibility for every added stage or node;
- a boundary contract and receiving-side acceptance check for every handoff that can change downstream work;
- explicit ownership for every shared state field and contended resource that exists;
- durable state sufficient to resume without reconstructing hidden context when work must survive interruption;
- an observable completion condition plus a bounded non-convergence condition;
- evidence proportional to the consequence, independent when self-certification would be unsafe;
- a human gate before irreversible or externally consequential actions unless standing authority explicitly covers them;
- an honest terminal status such as `COMPLETE`, `DEGRADED`, `NOT_PROVEN`, or `BLOCKED`.

For multi-node workflows, add only the node, edge, ownership, failure-propagation, observation, and shared-budget contracts required by the selected topology and demonstrated failure modes. Do not require graph artifacts for a single-agent loop or linear workflow unless they change routing, recovery, verification, or cost control.

## Design method

1. Confirm that a reusable loop or orchestrated workflow is justified. Define the outcome, unit of work, consumers, and observable completion evidence.
2. Choose the smallest sufficient topology: single agent, linear workflow, static graph, or dynamic graph.
3. For resumable or mutating work, start and resume by reconciling the durable contract, current artifacts or Git state, live owner state, and current evidence. Adopt valid completed or partial work; do not redispatch it merely because the orchestrator restarted.
4. For graph-shaped multi-node work, read [references/topology.md](references/topology.md), draw the declared graph, and define its nodes, edges, joins, gates, and terminal states. For a linear workflow, define only the ordered stage boundaries, gates, and terminal states unless graph mechanics change a decision.
5. Define each stage or direct owner's responsibility, boundary inputs and outputs, tools, state access, decision authority, completion evidence, and failure statuses. Let a direct owner manage its own nested workers unless cross-boundary coordination requires escalation.
6. Define every load-bearing handoff's trigger, payload or artifact contract, provenance, receiving-side acceptance check, invalidation rule, and failure route. Require a schema only when machine validation or replay needs one.
7. Draw decision rights: what an executor may decide, what a critic may only recommend, and what requires a human. Give critics access to the real artifacts they must judge; model diversity alone is not independent evidence.
8. Assign one authoritative writer for each shared state field or contended resource. Default one active task to one execution context; isolate another working copy or execution context only for a separate concurrent task or a proven ownership conflict. Declare how contended integration is serialized.
9. Choose durable checkpoints appropriate to the runtime. For dynamic or recovery-sensitive multi-node work, record enough realized work to explain consequential routing, retries, cancellations, and replacements. Never assume commit authority, Git availability, or conversation memory.
10. Define failure propagation: which downstream decisions become stale, which branches may continue, and who may reopen accepted work. Bind accepted evidence to the current contract, source or artifact identity, producing attempt, claim, and system boundary; invalidate and repeat only dependent proof after a relevant change.
11. Bound retries and non-convergence at the narrowest useful boundary. Charge a semantic engineering retry only when the evidence, input, hypothesis, or method changes. Track protocol repair, runtime or tool recovery, capacity backpressure, crash reconciliation, and safe replacement separately. Add graph-wide fan-out, depth, concurrency, tool, time, or cost budgets only when nested, parallel, or dynamic work consumes a shared budget.
12. Specify recovery, degraded output, resumption, pause, cancellation, switching, and orphaned-work handling only for lifecycle operations the runtime actually exposes.
13. Select only the patterns that address demonstrated failure modes. Read [references/principles.md](references/principles.md) as a pattern catalog, not a mandatory checklist.
14. Validate representative success and failure scenarios in proportion to the selected topology. Add stale-dependency, duplicate-delivery, crash/resume, lifecycle, and budget-exhaustion scenarios only when those mechanisms exist.
15. When the requested deliverable is a reusable Agent Skill, hand one validated workflow contract to `x9-skill-creator`. This skill owns topology, boundary contracts, workflow state, authority, checkpoints, budgets, and recovery; `x9-skill-creator` owns triggering, package structure, progressive disclosure, runtime adapters, and skill validation. Do not maintain two independent designs.

Use [references/harvesting.md](references/harvesting.md) only after real runs exist: record significant candidate lessons, and promote them only after representative repeated evidence.

## Done

- The delivered workflow contract identifies the qualified outcome, selected topology,
  applicable invariants, terminal statuses, and evidence for consequential decisions.
- Validation records at least one representative success and one applicable failure
  scenario as executed or unverified.
- When packaging was requested, the resulting Agent Skill preserves this workflow
  contract as its single design and passes `x9-skill-creator` checks.
