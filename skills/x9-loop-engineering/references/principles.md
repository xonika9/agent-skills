# Loop pattern catalog

These are selectable patterns, not universal requirements. Choose a pattern only when its failure mode exists and validate it on real runs.

| Failure mode | Pattern | Evidence to collect |
|---|---|---|
| Decisions are ambiguous | Typed decisions with explicit fields and owners | Invalid/unknown decisions are rejected or escalated |
| Work cannot resume | Durable checkpoint carrying inputs, state, outputs, and next action | Crash/restart resumes without conversation history |
| A worker self-certifies | Independent critic/auditor reads the real artifact without relying on the worker's narrative | Findings trace to artifact evidence rather than the worker's summary |
| Two checks repeat the same blind spot | Recompute through a different data source or computation path; model diversity alone is not independence | A seeded systematic error is caught by the independent route |
| Critics can mutate work | Separate recommendation authority from execution authority | Critic output cannot directly change external state |
| Repeated retries burn budget | Retry only when the next attempt changes evidence, inputs, or method | Same-cause repeats terminate honestly |
| Parallel workers collide | Declare resource/file/state ownership and serialize contention | No lost writes or hidden last-writer wins |
| Later work changes a shared surface | Reopen and re-verify accepted decisions that depend on the changed file, state, or interface | Dependency-linked decisions cannot remain accepted on stale evidence |
| External actions escape scope | Explicit irreversible/external gate | Action occurs only under standing or fresh authority |
| State is scattered | One discoverable run record with links to large artifacts | Another agent can locate the current state cheaply |
| A metric is gamed | Pair target metric with guardrails and periodic qualitative review | Improvements do not degrade protected outcomes |
| Evaluator drift | Calibrate against a stable representative set | Score changes trace to model/rubric changes |
| Override policy is opaque | Record overrides with reason and downstream result | Override rate is interpreted against task risk, not a universal target |
| One executor becomes a bottleneck | Use one writer per contended resource, not necessarily one global executor | Independent units remain parallel without conflicts |
| Internal gates share the loop's blind spots | For high-risk or release-gated work, run one fresh post-terminal audit before the irreversible human action | Audit findings reopen the owning decision instead of being deferred past release |

## Selection questions

- What concrete incident or plausible failure justifies this pattern?
- What signal will show that it helped?
- What cost or rigidity does it add?
- When will the pattern be removed or revised?

Checkpoint media are runtime-specific. Git commits, files, database rows, and workflow state can all be valid if they are durable, recoverable, and authorized.
