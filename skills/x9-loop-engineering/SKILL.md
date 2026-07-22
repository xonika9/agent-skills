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

- a typed decision contract and explicit authority for each decision;
- a minimal declared topology in which every node has a demonstrated responsibility;
- a typed handoff contract for every edge that can change downstream work;
- explicit ownership for shared state and every contended artifact;
- durable state sufficient to resume without reconstructing hidden context;
- an observable completion condition plus a bounded non-convergence condition;
- independent evidence for consequential decisions;
- a runtime trace sufficient to compare the declared topology with the work that actually ran;
- a human gate before irreversible or externally consequential actions unless standing authority explicitly covers them;
- an honest terminal status such as `COMPLETE`, `DEGRADED`, `NOT_PROVEN`, or `BLOCKED`.

## Design method

1. Confirm that a reusable loop or orchestrated workflow is justified. Define the outcome, unit of work, consumers, and observable completion evidence.
2. Choose the smallest sufficient topology: single agent, linear workflow, static graph, or dynamic graph.
3. For multi-node work, read [references/topology.md](references/topology.md), draw the declared graph, and define its nodes, edges, joins, gates, and terminal states.
4. Define every node's responsibility, inputs, outputs, tools, state access, decision authority, completion evidence, and failure statuses.
5. Define every load-bearing edge's trigger, typed payload, provenance, receiving-side acceptance check, invalidation rule, and failure route.
6. Draw decision rights: what an executor may decide, what a critic may only recommend, and what requires a human. Give critics access to the real artifacts they must judge; model diversity alone is not independent evidence.
7. Assign one authoritative writer for each shared state field or contended artifact. Declare how concurrent work is merged or serialized.
8. Choose durable checkpoints appropriate to the runtime and record both declared topology and realized work. Never assume commit authority, Git availability, or conversation memory.
9. Define failure propagation: which downstream decisions become stale, which branches may continue, and who may reopen accepted work.
10. Set node-level and graph-wide budgets for fan-out, depth, concurrency, retries, tool calls, cost, and non-convergence. Stop when repeated work produces no new evidence.
11. Specify recovery, degraded output, resumption, and orphaned-work handling before adding optimization.
12. Select only the patterns that address demonstrated failure modes. Read [references/principles.md](references/principles.md) as a pattern catalog, not a mandatory checklist.
13. Validate representative success, partial failure, stale dependency, duplicate delivery, crash/resume, and budget-exhaustion scenarios in proportion to the selected topology.
14. When the requested deliverable is a reusable Agent Skill, hand one validated workflow contract to `x9-skill-creator`. This skill owns topology, node and edge contracts, workflow state, authority, checkpoints, budgets, and recovery; `x9-skill-creator` owns triggering, package structure, progressive disclosure, runtime adapters, and skill validation. Do not maintain two independent designs.

Use [references/harvesting.md](references/harvesting.md) only after real runs exist and a repeated lesson has evidence worth promoting.

## Done

- The design states why a loop is justified; an unqualified process is rejected or simplified.
- The selected topology is the smallest one that satisfies the contract, and every additional node has a stated justification.
- Every state transition, decision owner, stop condition, and irreversible gate is explicit.
- Every load-bearing edge has a typed payload, receiving-side acceptance check, invalidation rule, and failure route.
- Shared state and contended artifacts have explicit writers and merge or serialization rules.
- A crash/resume scenario preserves work without relying on conversation memory.
- The run record shows realized work, including skipped, retried, cancelled, and dynamically created nodes or edges.
- A node failure cannot leave dependent downstream decisions silently accepted.
- Graph-wide fan-out, concurrency, retry, and cost budgets terminate honestly when exhausted.
- A critic failure or exhausted budget yields an honest terminal status.
- At least one representative success and one failure scenario were executed or clearly marked unverified.
- When packaging was requested, the resulting Agent Skill preserves the validated workflow contract and passes `x9-skill-creator` checks.
