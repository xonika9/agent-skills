# Workflow topology

Use this reference only when the workflow needs multiple executors, parallel branches, specialist ownership, joins, independent gates, or runtime task creation. A graph is justified by coordination needs, not by the number of available agents.

## Contents

- [Select the smallest topology](#select-the-smallest-topology)
- [Declare the graph](#declare-the-graph)
- [Node contract](#node-contract)
- [Edge contract](#edge-contract)
- [State and ownership](#state-and-ownership)
- [Failure propagation](#failure-propagation)
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

## Declare the graph

Record the intended nodes, control edges, data dependencies, review or veto edges, joins, human gates, and terminal states. A loop is a graph with a return edge; graph design extends loop design rather than replacing it.

Distinguish:

- the **declared graph**: the versioned topology and graph-generating rules approved for the workflow;
- the **realized work graph**: the nodes and edges actually created, run, retried, skipped, cancelled, or rerouted in one execution.

The run record must make the realized graph reconstructable. Dynamic topology changes need a recorded cause, authority, and budget impact.

## Node contract

Every node declares:

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

A role name such as `Researcher`, `Writer`, or `Reviewer` is not a contract. The node becomes operational only when its boundary, artifact, authority, and completion evidence are explicit.

## Edge contract

Define an edge when its delivery can activate work, transfer authority, mutate shared state, satisfy a dependency, invalidate an accepted decision, or cross a trust boundary.

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

- `payload_schema` states what is transferred rather than relying on a narrative summary.
- `provenance` links claims and decisions to the artifacts or observations that support them.
- `acceptance_check` belongs to the receiver and prevents malformed or incomplete work from propagating.
- `invalidation_rule` states which downstream work becomes stale when an upstream artifact or decision changes.
- `delivery_semantics` states whether replay is possible and how consequential effects remain idempotent after retries or resume.
- `failure_route` chooses retry, fallback, upstream reopen, human gate, branch cancellation, or an honest terminal status.

## State and ownership

Assign one authoritative writer to each shared state field or contended artifact. Parallel nodes may produce proposals or isolated artifacts, but merging requires an explicit owner or deterministic merge rule.

Record enough durable state to recover:

- graph and contract versions;
- active, completed, failed, skipped, and cancelled work;
- accepted edge deliveries and idempotency keys;
- artifact versions and dependency links;
- routing and topology-mutation decisions;
- remaining node and graph budgets;
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

## Budgets and observation

Set both node-level and graph-wide limits. At minimum consider fan-out, nesting depth, concurrency, retries, tool calls, elapsed time, and cost. Dynamic graph mutation consumes the same shared budget as execution.

Trace enough information to answer:

- Which declared nodes and edges actually ran?
- Why was work spawned, skipped, cancelled, retried, merged, or rerouted?
- Which node produced each consequential artifact or decision?
- Where did cost, latency, and failures accumulate?
- Did every additional node provide measurable value?

## Workflow contract

The design handed to `x9-skill-creator` should be one canonical artifact with:

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
