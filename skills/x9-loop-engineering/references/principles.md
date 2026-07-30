# Loop pattern catalog

These are selectable patterns, not universal requirements. Choose a pattern only when its failure mode exists and validate it on real runs.

| Failure mode | Pattern | Evidence to collect |
|---|---|---|
| Decisions are ambiguous | Typed decisions with explicit fields and owners | Invalid/unknown decisions are rejected or escalated |
| Work cannot resume | Durable checkpoint carrying inputs, state, outputs, and next action | Crash/restart resumes without conversation history |
| A worker self-certifies | Independent critic/auditor reads the real artifact without relying on the worker's narrative | Findings trace to artifact evidence rather than the worker's summary |
| Two checks repeat the same blind spot | Recompute through a different data source or computation path; model diversity alone is not independence | A seeded systematic error is caught by the independent route |
| Critics can mutate work | Separate recommendation authority from execution authority | Critic output cannot directly change external state |
| Repeated or misclassified retries burn budget | Charge a semantic retry only when the next engineering attempt changes evidence, input, hypothesis, or method; track protocol repair, transient tool recovery, capacity wait, crash reconciliation, and replacement separately | Same-cause engineering repeats terminate honestly, while infrastructure recovery does not exhaust the semantic budget |
| Orchestrator repair displaces the user's task | In a self-repairing orchestrator, let repair preempt task work only for a closed safety class; derive a small urgent-repair budget from durable repair starts and defer other defects | A non-safety defect is recorded while task work continues; a safety repair returns to the task, and another distinct repair cannot start automatically after exhaustion |
| Extra agents add ceremony without value | Require distinct context, tools, authority, evidence, or useful parallelism for every node | Removing a node measurably worsens quality, safety, latency, or coverage |
| A downstream node accepts incomplete work | Use an explicit payload or artifact boundary plus a receiving-side acceptance check; add a schema only when mechanical validation or replay requires one | A seeded malformed or incomplete handoff is rejected before downstream work starts |
| Resume duplicates consequential effects | Attach an idempotency key or durable delivery record to consequential edges | Replaying the same accepted handoff does not duplicate the effect |
| A multi-write or non-repeatable public lifecycle mutation can partially apply or lose its response | Give the caller-visible operation one stable identity and enough durable phases to resume the same semantics; reject conflicting replay and reconcile an unfinished operation before another conflicting mutation. Persist intent before a consequential mutating dispatch and fence replacement while its occurrence is indeterminate | Fault injection after each durable phase through the public API converges to one accepted result; a post-commit derived-view failure or unknown launch never duplicates the authoritative effect |
| Parallel workers collide | Default one active task to one execution context; declare writers for files, state, services, ports, databases, browser sessions, caches, and mutable Git refs; isolate only a separate concurrent task or proven ownership conflict; serialize contended integration | No lost writes, hidden last-writer wins, or unnecessary working-copy proliferation |
| Accepted evidence is replayed after contract or source drift | Bind evidence to the current outcome contract, source or artifact identity, producing attempt, claim, and system boundary; invalidate and repeat only dependent proof after a relevant change | Stale or cross-run evidence is rejected while unaffected checks remain current |
| Versioned or cross-run work loses its accepted ancestry | Preserve immutable predecessor and acceptance bindings plus explicit version reader or migration boundaries; reject gaps, cycles, forged ancestry, and prose backfill of unknown historical facts | A successor chain retains its accepted basis, old records keep their recorded semantics, and a forged predecessor is rejected |
| A failed node leaves dependent work apparently valid | Link dependencies to explicit invalidation and reopening rules | Downstream decisions become stale when their supporting artifact or decision changes |
| Dynamic spawning explodes cost | Enforce graph-wide fan-out, depth, concurrency, and cost budgets | Adversarial decomposition terminates within the shared budget |
| The orchestrator mutates topology opaquely | Record every spawn, cancel, merge, and reroute with its evidence and authority | The realized work graph is reconstructable and each mutation is explainable |
| Context crosses ownership boundaries | Allowlist state fields and artifacts on each edge | A receiving node cannot inspect unrelated or unauthorized state |
| Branches wait on one another indefinitely | Detect missing producers, unreachable joins, circular waits, and graph-level no-progress | Deadlock terminates honestly instead of waiting forever |
| External actions escape scope | Explicit irreversible/external gate | Action occurs only under standing or fresh authority |
| State is scattered | One discoverable run record with links to large artifacts | Another agent can locate the current state cheaply |
| Derived state competes with authoritative facts | Assign one authority to each fact class; when source facts are already durable, make projections, usage counters, trees, traces, history, and reports reproducible views, while a live lock or claim contains only facts it uniquely owns | Deleting and rebuilding a derived view reproduces the same result, and failure to refresh it cannot reverse or duplicate an accepted fact |
| A metric is gamed | Pair target metric with guardrails and periodic qualitative review | Improvements do not degrade protected outcomes |
| Evaluator drift | Calibrate against a stable representative set | Score changes trace to model/rubric changes |
| Override policy is opaque | Record overrides with reason and downstream result | Override rate is interpreted against task risk, not a universal target |
| One executor becomes a bottleneck | Use one writer per contended resource, not necessarily one global executor | Independent units remain parallel without conflicts |
| Nodes succeed locally while the workflow fails globally | Separate node completion from join and graph-level completion | Required joins and graph invariants are checked before `COMPLETE` |
| A declared trace, role, or synthetic no-op substitutes for realized work | Derive accepted stage claims from current terminal occurrences or contracted deterministic gates, binding the outcome or applicability owner, artifact identity, result, and evidence; do not count logical roles or checkpoints as runtime agent launches | Names-only or stale traces and no-ops from the wrong owner are rejected, while a current owner result or contracted deterministic skip can close the stage |
| Internal gates share the loop's blind spots | For high-risk or release-gated work, run one fresh post-terminal audit before the irreversible human action | Audit findings reopen the owning decision instead of being deferred past release |

## Selection questions

- What concrete incident or plausible failure justifies this pattern?
- What signal will show that it helped?
- What cost or rigidity does it add?
- When will the pattern be removed or revised?

Checkpoint media are runtime-specific. Git commits, files, database rows, and workflow state can all be valid if they are durable, recoverable, and authorized.
