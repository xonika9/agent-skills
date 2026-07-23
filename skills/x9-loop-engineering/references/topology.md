# Workflow topology

Use this reference only when the workflow needs multiple executors, parallel branches, specialist ownership, joins, independent gates, or runtime task creation. A graph is justified by coordination needs, not by the number of available agents.

## Contents

- [Select the smallest topology](#select-the-smallest-topology)
- [Use hierarchical ownership](#use-hierarchical-ownership)
- [Declare the graph](#declare-the-graph)
- [Node contract](#node-contract)
- [Edge contract](#edge-contract)
- [State and ownership](#state-and-ownership)
- [Failure propagation](#failure-propagation)
- [Lifecycle semantics](#lifecycle-semantics)
- [Budgets and observation](#budgets-and-observation)
- [Workflow contract](#workflow-contract)

## Select the smallest topology

| Topology | Use when | Avoid when |
|---|---|---|
| Single agent | One context, toolset, authority boundary, and state owner are sufficient | Independent evidence or parallel ownership is load-bearing |
| Linear workflow | Ordered stages have distinct contracts but no branching or dynamic routing | A deterministic script can perform the same transformation more reliably |
| Static graph | Stable branches, joins, specialist ownership, or veto gates recur across runs | The structure changes arbitrarily per task |
| Dynamic graph | Runtime evidence legitimately creates, cancels, merges, or reorders work | Static routing plus bounded retries is sufficient |

Each additional node must contribute distinct context, tools, authority, evidence, or useful parallel capacity. Prefer a deterministic function, router, join, or human checkpoint when an autonomous agent loop is unnecessary.

## Use hierarchical ownership

Keep the orchestrator thin: route, supervise, reconcile, and verify across ownership boundaries while one direct owner remains responsible for each delegated unit. A direct owner may create and manage nested workers within its contract; the top-level orchestrator should not micromanage those workers unless they contend for shared resources, cross authority boundaries, change shared topology, or affect integration.

Normalize native owner results only at the orchestrator boundary. Internal worker formats and private stages need no shared schema when the direct owner can satisfy the boundary contract and preserve required evidence.

## Declare the graph

Record the intended nodes, control edges, data dependencies, review or veto edges, joins, human gates, and terminal states. A loop is a graph with a return edge; graph design extends loop design rather than replacing it.

Distinguish:

- the **declared graph**: the versioned topology and graph-generating rules approved for the workflow;
- the **realized work graph**: the nodes and edges actually created, run, retried, skipped, cancelled, or rerouted in one execution.

For dynamic or recovery-sensitive workflows, the run record must make consequential realized work reconstructable. A simple static graph may record only deviations, retries, cancellations, and replacements needed to explain the outcome. Dynamic topology changes need a recorded cause, authority, and budget impact.

## Node contract

Every load-bearing node needs an operational boundary: responsibility, accepted inputs, produced artifacts or decisions, authority, completion evidence, and failure behavior. Add fields only when they change routing, recovery, verification, ownership, or budget decisions.

For a boundary that must be machine-checked or replayed, the contract may be encoded as:

```yaml
node:
  id:
  responsibility:
  activation_condition:
  inputs:
  outputs:
  tools:
  readable_state:
  writable_state:
  decision_authority:
  completion_evidence:
  failure_statuses:
  retry_owner:
  cost_budget:
```

A role name such as `Researcher`, `Writer`, or `Reviewer` is not a contract. A prose contract or native artifact is sufficient when it makes the boundary, authority, evidence, and failure behavior unambiguous; do not impose one shared schema on private internal stages.

## Edge contract

Define an edge when its delivery can activate work, transfer authority, mutate shared state, satisfy a dependency, invalidate an accepted decision, or cross a trust boundary.

When mechanical validation or replay is required, an edge may be encoded as:

```yaml
edge:
  from:
  to:
  trigger:
  payload_schema:
  artifact_links:
  provenance:
  acceptance_check:
  invalidation_rule:
  delivery_semantics:
  failure_route:
```

- `payload_schema` states what is transferred when a machine-readable schema is necessary; otherwise use a concise artifact or payload contract.
- `provenance` links claims and decisions to the artifacts or observations that support them.
- `acceptance_check` belongs to the receiver and prevents malformed or incomplete work from propagating.
- `invalidation_rule` states which downstream work becomes stale when an upstream artifact or decision changes.
- `delivery_semantics` states whether replay is possible and how consequential effects remain idempotent after retries or resume.
- `failure_route` chooses retry, fallback, upstream reopen, human gate, branch cancellation, or an honest terminal status.

## State and ownership

Assign one authoritative writer to each shared state field or contended artifact. Parallel nodes may produce proposals or isolated artifacts, but merging requires an explicit owner or deterministic merge rule.

Record enough durable state to recover. Depending on the topology and failure modes, this may include:

- graph and contract versions when version drift changes validity;
- active, completed, failed, skipped, and cancelled work;
- accepted consequential deliveries and idempotency keys when replay can duplicate effects;
- artifact versions and dependency links;
- routing and topology-mutation decisions;
- remaining selected node and shared graph budgets;
- the next recoverable action.

Do not copy all context across every edge. Transfer the smallest payload that satisfies the receiver's contract, with artifact links for large evidence.

## Failure propagation

A local node status is not a graph-level verdict. For every failure class, define:

- whether independent branches may continue;
- which downstream decisions become stale or must reopen;
- whether a join can degrade or must block;
- who owns retry, fallback, cancellation, or escalation;
- how orphaned work is detected after crash or topology change.

Detect graph-level no-progress separately from node retries. Missing producers, unreachable joins, circular waits, and repeated rerouting terminate as `BLOCKED` or `DEGRADED`, not as an endless wait.

## Lifecycle semantics

Define lifecycle behavior only when the runtime exposes it:

- pause stops new dispatch and preserves authoritative state without relabeling unfinished work as complete;
- resume and task switching reconcile durable state, current artifacts, live direct owners, and current evidence before dispatch;
- cancel is an honest terminal non-success state that preserves useful partial work and records whether external effects remain;
- replacement begins only after the prior owner's mutation authority is released or safely fenced, then adopts valid completed work instead of restarting it;
- orphaned work is detected, reconciled, adopted, fenced, or cancelled explicitly rather than silently duplicated.

## Budgets and observation

Set a node- or stage-level limit wherever retry or non-convergence exists. Add graph-wide fan-out, nesting-depth, concurrency, tool-call, elapsed-time, or cost limits only when nested, parallel, or dynamic work consumes a shared budget. Dynamic graph mutation consumes the same selected shared budget as execution.

Trace enough information, in proportion to the topology and recovery needs, to answer:

- Which declared nodes and edges actually ran?
- Why was work spawned, skipped, cancelled, retried, merged, or rerouted?
- Which node produced each consequential artifact or decision?
- Where did cost, latency, and failures accumulate?
- Did every additional node provide measurable value?

## Workflow contract

The design handed to `x9-skill-creator` should remain one canonical contract. Use only the sections needed by the selected topology:

```markdown
# Workflow Contract

## Qualification
## Outcome and completion evidence
## Declared topology
## Node contracts
## Edge contracts
## State ownership and checkpoints
## Decision authority and human gates
## Budgets and non-convergence
## Failure propagation and recovery
## Validation evidence
```

Packaging may distribute this content across the skill body, references, scripts, and runtime adapters, but it must preserve one coherent contract rather than inventing a second workflow design.
