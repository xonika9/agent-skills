# Architecture decision gate

## Contents

- [Decision packet](#decision-packet)
- [Minimal ownership ladder](#minimal-ownership-ladder)
- [Evidence](#evidence)
- [Independent challenge](#independent-challenge)
- [Recommendation](#recommendation)

Use this gate only after `SKILL.md` classifies it as applicable. It prevents a
large implementation from validating its own premise.

## Decision packet

In advisory mode, return the packet in the response and do not create a file
without authority.

In autonomous delivery, store it in an already-authorized research, plan, or
workstream artifact. If no durable target is authorized, stop before
implementation and request that authority.

The packet contains:

- required outcome, constraints, current authority, and observable success. State
  the user's successful action without naming the proposed mechanism, product,
  or technology; inability to do so blocks `IMPLEMENTATION_READY`;
- current canon and any conflict with the proposed direction;
- the proposed mechanism treated as a hypothesis;
- a materially different credible alternative;
- the simplest credible alternative from the minimal ownership ladder below;
- when the proposal starts from a low-level primitive, a product-level ownership
  map of the lifecycle, scheduling, capacity, access, file movement,
  publication, recovery, cleanup, deployment, and qualification capabilities
  that the primitive leaves to this project;
- for platform, vendor, or continuing-cost decisions, comparable one-time
  effort, recurring ownership cost, material risks, reversibility, and evidence
  confidence for each credible option;
- compare credible alternatives by the total operational surface this project
  would own and their reversibility, including operation, upgrades, recovery,
  observability, exit, and every new setting, command, environment variable, or
  mandatory user step. Open source, vendor maintenance, or prior investment
  does not reduce the surface that this project must operate;
- a claim-to-evidence table;
- what was measured, under which load and environment;
- the limits of any extrapolation beyond the measured envelope;
- the cheapest reversible experiment that could disprove each load-bearing
  assumption;
- when the proposed owned surface is itself a load-bearing choice, an experiment
  that can disprove its necessity rather than merely demonstrate that the
  mechanism works;
- for a proposed experiment, the exact question, result-to-decision mapping,
  time, resource, and cost ceilings, and stop and cleanup conditions;
- independent-critique status and unresolved facts;
- evidence and recommendation fields defined below.

Use the existing `Evidence` section in `SKILL.md`; do not duplicate
its source or freshness rules here. For this gate, extend that research from the
initial mechanism to the relevant solution landscape.

## Minimal ownership ladder

Compare from the least owned surface and stop at the first credible option that
meets the mandatory outcome:

1. do not build or defer the capability;
2. use an existing project capability;
3. use the standard library or native platform;
4. use an already-installed dependency;
5. consume a maintained component through a thin integration;
6. add the smallest bounded custom component; or
7. own a custom infrastructure subsystem.

This is an order of proof, not an automatic ranking. Inspect the real end-to-end
flow before selecting a rung, and compare total operational surface and
reversibility; a maintained product can impose more project ownership than a
small local component when this project must operate its lifecycle.

When the selected simple option deliberately accepts a known ceiling, record
that ceiling, the observable signal that requires reconsideration, and the next
credible option. This extends the existing decision packet or work ledger; it
does not create a code-comment convention, separate debt store, or speculative
fallback implementation.

## Evidence

Set one value:

- `SUPPORTED`: evidence is sufficient for the stated, bounded claim.
- `DEGRADED`: one or more load-bearing evidence routes are unavailable.
- `INSUFFICIENT`: the current evidence does not support the claim.

A working prototype proves only the mechanism and operating envelope it
actually exercised. A bounded rollout with explicit rollback may support the
next stage without claiming universal scale.

For each load-bearing claim, identify evidence provenance: direct repository
source, direct observation or test, primary external source, or independently
reported evidence. Record the source and relevant version, environment, or
observation time. A subagent report is independently reported evidence until its
underlying source is inspected.

## Independent challenge

Independent criticism is required before `IMPLEMENTATION_READY`.

By default, give a sealed decision brief to a fresh internal subagent whose job
is to disprove the proposed direction. If the user explicitly invokes
`x9-idea-critic`, use that skill under its own contract instead.

`x9-idea-critic` supplies generic sealed-packet criticism only. Grounding owns
live-state inspection, freeze behavior, architecture admission, and the final
CTO recommendation; the critic cannot grant authority or resume work.

If no independent critic can inspect the load-bearing evidence, record the
missing route and set `AWAITING_CRITIQUE`. Do not replace independent criticism
with self-review.

The author of the proposed direction cannot supply the dissent. An unresolved
critique that invalidates a load-bearing claim blocks `IMPLEMENTATION_READY`
until the claim is resolved or the recommendation changes.

## Recommendation

Set one value:

- `NOT_APPLICABLE`: the gate was evaluated and does not apply.
- `IMPLEMENTATION_READY`: evidence and criticism support the bounded direction.
- `EXPERIMENT_ONLY`: only the named reversible experiment is supported.
- `DO_NOT_IMPLEMENT`: evidence invalidates the proposed direction.
- `AWAITING_CRITIQUE`: the required independent challenge lacks authority or
  has not run.
- `AWAITING_USER_DECISION`: evidence supports real alternatives that require a
  product, authority, cost, or risk choice.

These values are recommendations, not permissions. They never expand the
authority supplied by the user or repository workflow.

`EXPERIMENT_ONLY` supports exactly one named bounded reversible experiment. Its
result returns through Grounding for a fresh recommendation; completing the
experiment never automatically admits implementation.

Before `IMPLEMENTATION_READY`, every load-bearing assumption that could have
been cheaply tested must either be tested or remain explicitly unresolved with
a reason.

An unresolved fact that could invalidate the selected class of solution blocks
`IMPLEMENTATION_READY`. Simpler credible alternatives must be rejected on
proportionate evidence, and the selected option's operational and exit surface
must be explicit.

A low-level primitive cannot become `IMPLEMENTATION_READY` merely because the
primitive works when satisfying the required outcome would make this project
own the missing product control plane. Current landscape research must identify
the applicable maintained complete products and compare their mandatory-requirement
fit, integration boundary, and ownership cost on comparable evidence. When none
meets a named mandatory requirement, that negative evidence may support a
bounded custom direction. Prior investment in the custom direction is not
supporting evidence.
