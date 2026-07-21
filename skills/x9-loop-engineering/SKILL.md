---
name: x9-loop-engineering
description: Use when designing a repeated agent loop, long-running workflow, evaluator/optimizer cycle, or multi-stage autonomous process — «спроектируй агентный цикл», «сделай автономный workflow», "design an agent loop". Do not use for auditing ordinary Agent Skills, one-off tasks, simple linear scripts, or ordinary project planning.
---

# Loop engineering

Design loops as bounded decision systems, not repeated prompts.

## Qualify the loop

Build a loop only when the work recurs, its state can live in durable artifacts, and coordination or repeated verification is a meaningful part of the cost. If the task is one-off, state is only conversational, or human judgment dominates the work, recommend a bounded delegation or linear workflow instead of adding loop machinery.

## Invariants

Every production loop needs:

- a typed decision contract and explicit authority for each decision;
- durable state sufficient to resume without reconstructing hidden context;
- an observable completion condition plus a bounded non-convergence condition;
- independent evidence for consequential decisions;
- a human gate before irreversible or externally consequential actions unless standing authority explicitly covers them;
- an honest terminal status such as `COMPLETE`, `DEGRADED`, `NOT_PROVEN`, or `BLOCKED`.

## Design method

1. Confirm the qualification above, then define the outcome, unit of work, state, decision types, and consumers.
2. Draw decision rights: what the executor may decide, what a critic may only recommend, and what requires a human.
3. Choose checkpoints appropriate to the runtime: committed Git state, durable files, database records, or another recoverable boundary. Never assume commit authority or Git availability.
4. Select only the patterns that address demonstrated failure modes. Read [references/principles.md](references/principles.md) as a pattern catalog, not a mandatory checklist.
5. Give critics access to the real artifacts they must judge. A model/provider difference is useful diversity, not a substitute for evidence.
6. Define retry/non-convergence budgets from cost and failure semantics. Stop when the same cause repeats without new evidence.
7. Specify recovery, degraded output, and resumption before adding optimization.
8. Validate the loop on representative tasks, including failure and resume scenarios.

Use [references/harvesting.md](references/harvesting.md) only after real runs exist and a repeated lesson has evidence worth promoting.

## Done

- The design states why a loop is justified; an unqualified process is rejected or simplified.
- Every state transition, decision owner, stop condition, and irreversible gate is explicit.
- A crash/resume scenario preserves work without relying on conversation memory.
- A critic failure or exhausted budget yields an honest terminal status.
- At least one representative success and one failure scenario were executed or clearly marked unverified.
