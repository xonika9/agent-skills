# Grounding control

## Contents

- [Entry](#entry)
- [Control operation](#control-operation)
- [Output and resumption](#output-and-resumption)

Grounding has two contexts: pre-implementation architecture admission and
active-delivery drift control. It returns the work to observable user value
without deleting evidence or starting another implementation cycle.

Before implementation, Grounding first classifies the high-impact architecture
gate. When applicable, invoke and present the canonical decision packet in
[architecture-decision-gate.md](architecture-decision-gate.md); do not recreate
its packet here. When it is not applicable, keep Grounding lightweight: state
the evidence-based reason, the smallest proposed user path, and the next user
decision. A small change that stays within an accepted surface is not elevated
to a full architecture packet merely because Grounding was requested.

## Entry

Enter grounding when any of these is true:

- the user invokes the runtime-native `x9-cto ground`;
- the user explicitly asks to challenge the architecture premise or suspend
  implementation admission;
- during active autonomous delivery, the user asks to stop growth and return to
  the minimum user path;
- the delivery budget of `first_user_path` is exhausted without movement of
  that path;
- proposed work leaves the `first_user_path` allowlist before that path is
  `PROVEN`;
- proposed work introduces or expands a client, protocol, process, runtime,
  control plane, or infrastructure subsystem outside the accepted reuse and
  architecture decisions; or
- the same evidenced cause repeats without a meaningful evidence, input, or method
  delta, under the [continuation rule](execution-mode.md#supervise-actively).

Choose the context from the actual delivery state, not the trigger wording. If
implementation is active, freeze it first; when the same request also introduces
a new architecture direction, evaluate that direction only after the freeze. If
implementation has not started, use pre-implementation admission. These are
evidence conditions, not universal time, commit, line, or retry thresholds.

## Control operation

For pre-implementation admission, first state the mechanism-free user action
and the observed problem with its evidence, before comparing mechanisms, as the
[decision packet](architecture-decision-gate.md#decision-packet) requires, even
when the gate does not apply. Classify the existing high-impact architecture
gate. Do not create a second admission packet.

For active delivery, stop new implementation dispatches and broad mutation.
Inspect the current diff, closure contract, `first_user_path`, budget
consumption, product-path evidence, owned surface, reuse alternatives, active
executors, and fragile local state. Preserve produced work as evidence; do not
delete, rewrite, release, or deploy it. Compare alternatives as the
[decision packet](architecture-decision-gate.md#decision-packet) does.

Return exactly one existing recommendation:

- whenever Grounding classifies or re-evaluates an architecture direction, the
  recommendation defined by the applicable architecture gate, including
  `AWAITING_CRITIQUE`, or a lightweight `NOT_APPLICABLE` reason;
- `IMPLEMENTATION_READY` only when the exact `first_user_path` has authoritative
  product-path evidence and the proposed continuation stays inside its allowed
  surface;
- `EXPERIMENT_ONLY` with one cheapest path-killing experiment, its allowed
  surface, budget, and result-to-decision mapping;
- `AWAITING_USER_DECISION` when resumption requires a new product direction,
  authority, cost, scope, trust boundary, or architecture commitment; or
- `DO_NOT_IMPLEMENT` when evidence invalidates the direction or an applicable
  maintained complete component meets the mandatory requirements with lower
  avoidable project ownership.

For every recommendation, make evidence provenance explicit: name the source,
whether it is direct repository evidence, direct observation, a primary external
source, or an independently reported result, plus the relevant version,
environment, or observation time. For an applicable architecture gate,
`IMPLEMENTATION_READY` additionally requires its mandatory independent challenge
with no unresolved invalidating critique.

## Output and resumption

Put the [owner brief](owner-brief.md) first, then the view for the current
context.

For pre-implementation admission, lead with an owner-readable view:

1. the mechanism-free user action and observed problem;
2. what is proven now, its provenance, and the nearest blocking unknown;
3. the simplest credible option and why any simpler option is insufficient;
4. what the project would operate continuously and the cost of exit;
5. the independent challenge when the architecture gate applies and the CTO
   recommendation; and
6. the exact bounded experiment or user decision required next.

For active-delivery drift, lead with:

1. what a user can do successfully now;
2. the nearest unproved user barrier;
3. owned surface added since the last accepted product proof;
4. the smallest keep boundary and what must stop growing;
5. the recommendation and one cheapest falsifying action; and
6. the evidence provenance and evidence required before mutation can resume.

Do not treat a critique, refactor, test-only result, diagnostic improvement,
commit count, or executor completion as user-path proof. Grounding never resumes
implementation in the same turn. Wait for explicit user confirmation of the
grounded recommendation. After an active-delivery freeze, only the user can
resume work; routine technical choices inside that later accepted boundary remain
owned by the executor.
