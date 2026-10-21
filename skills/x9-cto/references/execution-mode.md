# Autonomous delivery mode

Use this mode only when the user explicitly asks the CTO chat to deliver an
outcome that still requires a CTO-level decision, high-impact risk ownership, or
cross-system integration, or explicitly asks the CTO to lead such an outcome. A
settled plan, multi-step implementation, or subagent use alone belongs to the
applicable implementation skill. The head agent remains accountable for the CTO
outcome; delegation changes who executes a bounded unit, not who owns the result.

## Contents

- [Operating contract](#operating-contract)
- [Feasibility admission before broad delivery](#feasibility-admission-before-broad-delivery)
- [Start with a closure contract](#start-with-a-closure-contract)
- [Working-state-first evidence ladder](#working-state-first-evidence-ladder)
- [Delivery budget and strategy reassessment](#delivery-budget-and-strategy-reassessment)
- [Grounding control](#grounding-control)
- [Delegate execution](#delegate-execution)
- [Supervise actively](#supervise-actively)
- [Integrate and verify](#integrate-and-verify)
- [Tail audit](#tail-audit)
- [Completion gate](#completion-gate)

## Operating contract

- The head agent acts as delivery lead, reviewer, and integrator for the combined
  outcome. An internal subagent is a bounded executor.
- Prefer delegation when a unit can run independently, has an observable
  result, and separate context or ownership provides a material benefit. Keep
  load-bearing product decisions, cross-workstream integration, destructive or
  external authority, and final acceptance in the head chat.
- When the remaining work is ordinary implementation of a settled contract,
  route it through `ce-work` or the applicable implementation owner. The CTO
  retains acceptance only when that implementation remains part of the CTO
  outcome already in scope.
- Do not create a worktree unless the user asks for one or the repository's
  active workflow explicitly requires it. Shared-workspace subagents must be
  told which files or subsystem they own to avoid conflicting edits.
- Track internal subagents in the current turn until their required results are
  collected, verified, and either integrated or explicitly rejected.
- Autonomy does not expand authority. Production deploys, irreversible external
  mutations, or a new product direction still require the approval defined by
  the user and repository workflow.
- Missing authority for an action inside the requested outcome is not success.
  Keep the goal active and request the authority or decision; use a runtime's
  blocked status only when its own blocked-status rules are satisfied. An
  out-of-scope external action may instead be named in the final handoff.

## Feasibility admission before broad delivery

Apply [feasibility admission](feasibility-gate.md) before the closure contract
admits broad implementation. Current evidence must come from the same
product-path artifact and load-bearing target boundary. Otherwise keep the
contract at `EXPERIMENT_ONLY`; do not introduce a second CTO-owned lifecycle.

## Start with a closure contract

Before dispatching work, establish all of the following; their internal order is
adaptive:

- the current code, docs, task state, Git branches, and runtime state
  relevant to the outcome have been inspected;
- the outcome and observable done bar name the real user path or artifact, not
  only unit tests or a commit;
- one top-level `first_user_path` records the actor, entry point, observable end
  state, authoritative product-path evidence, and the smallest owned-surface
  allowlist needed to prove it. The path is `PROVEN` only when that
  authoritative evidence passes on the integrated state; until then it is
  unproven. This checkpoint and its delivery budget are inherited by every child
  workstream; a local fix, reassessment, or replacement executor cannot reset,
  replace, or enlarge them;
- before the first implementation write or dispatch, `architecture_gate` is
  recorded as `NOT_APPLICABLE — <reason>` or points to a durable decision packet
  and its current recommendation;
- feasibility records the current state and its matching evidence or falsifiable
  assumption and authority boundary under [feasibility admission](feasibility-gate.md);
- when the path would own a commodity capability or add a language, process, or
  protocol boundary, the same admission input contains the applicable
   `reuse_decision` from [feasibility admission](feasibility-gate.md), recorded as admitted or
   explicitly not applicable;
- stable acceptance milestones identify observable product movement before
  implementation; commits, diagnostics, reviews, receipts, retries, and
  contract generations cannot create or close those milestones by themselves;
- the task-specific delivery budget of `first_user_path`, the only delivery
  budget, defines the measurable envelope that can change the strategy: elapsed
  work when observable, external or target attempts, paid cost when applicable,
  and planned source or subsystem scope; omit a dimension that cannot be
  observed instead of inventing a value;
- likely blind spots are identified where the literal task could pass while the
  outcome remains incomplete, such as configuration, environment-specific
  behavior, migrations, cleanup, documentation, task state, release wiring, and
  rollback;
- scope boundaries and actions that still need user authority are recorded;
- a compact work ledger exists, and no unit is accepted before its evidence is
  reviewed by the head agent.

Treat `first_user_path` as one active user-outcome front. Every active child
workstream either moves its nearest acceptance barrier or is demonstrably
independent preparation that does not compete for the same decision, source
surface, or integration boundary. Derive this focus from the closure contract
and current task state; it creates no tracker field or parallel status record.

`AWAITING_CRITIQUE`, `AWAITING_USER_DECISION`, and `DO_NOT_IMPLEMENT` prohibit
implementation dispatch. `EXPERIMENT_ONLY` permits only the named experiment
and only when the existing authority permits it. `IMPLEMENTATION_READY` still
does not grant authority that the user or repository workflow has not supplied.

Before `first_user_path` is `PROVEN`, keep mutations within its accepted
source surface and architecture/reuse boundary. Ordinary reversible local source
and document edits that do not mutate live resources or exercise destructive or
external effects use existing executor controls and inspection of actual changes.
Their scope discipline does not require a new dispatch-enforcement subsystem.
Independently required security, access, external-action, and irreversible-effect
controls must be effective before the dependent action; later inspection is not
a substitute. If a required control is unavailable, stop that action and report
it. Grounding and user stop conditions remain binding.

Ordinary work remains in this chat or its authorized internal executors.

If a persistent goal was explicitly requested, keep it active across this cycle
and update it to complete only after the independent tail audit and integrated
checks pass. Nearing a token or time budget is not a completion condition; an
exhausted task-specific budget may require the reassessment below.

If a load-bearing choice cannot be recovered from the repository or external
sources, ask one targeted question. Do not turn ordinary implementation
uncertainty into a questionnaire.

## Working-state-first evidence ladder

Admission and hardening are different gates. Applicable architecture,
feasibility, authority, trust-boundary, migration, and irreversible-action
decisions remain settled before broad implementation; they do not require a
general review of code that has not yet demonstrated its real path.

Unless the accepted contract makes another order part of correctness:

1. Establish the observable completion bar and the cheapest representative
   end-to-end path.
2. Implement until that path works at the closest feasible integration
   boundary. Unit tests and mocked receipts may support this proof but do not
   replace it.
3. Before a costly, destructive, or hard-to-recover target action, reproduce
   the exact state and transition locally. Use the target attempt to qualify a
   candidate, not as the primary debugging loop.
4. After working-path evidence, perform bounded review and hardening against
   the risks that can invalidate the completion bar, safety boundary, required
   repository contract, or release gate.
5. Settle source-bearing changes and required documentation, run the required
   gates, freeze the candidate, and perform expensive live or release
   qualification only against that frozen state.

Before an expensive or hard-to-reverse direction begins, preregister in the
existing closure contract or work ledger the decision question, cheapest
direction-killing result, bounded experiment budget, and condition for later
reconsideration. When the killing result is observed, stop dependent work and
do not resurrect the direction until one named new fact changes the prior
conclusion. Use an observable task-specific bound; do not invent a time estimate
when elapsed work is not measurable. This extends the existing record; it does
not create a hypothesis registry or another approval gate.

A review, refactor, diagnostic improvement, or cleaner harness is progress only
when it enables working-path evidence or closes an accepted risk. Do not repeat
broad review or simplification merely because the implementation changed.
Tracked changes after candidate freeze invalidate downstream evidence whose
inputs they can affect.

Inside an admitted architecture and reuse boundary, follow the selected minimal
ownership option and any simplification ceiling recorded by the decision packet.
Do not prebuild its fallback. When the observable reconsideration signal occurs,
route the expansion through the existing strategy reassessment instead of
silently widening implementation.

## Delivery budget and strategy reassessment

Optimize delivery for accepted product movement and the smallest avoidable owned
surface. Track product milestones separately from evidence or diagnosis that
changes a load-bearing decision. A supporting-tool repair is not milestone
movement unless resulting product-path evidence proves or invalidates an
accepted product milestone; calling it a blocker or promising future evidence
does not suffice. Scope such repairs under [product scope and supporting
machinery](product-scope.md). New evidence can invalidate an approach and
justify strategy reassessment without a completed milestone, but must change the
causal conclusion about the accepted outcome, not merely describe another
failure of supporting machinery. Neither milestone movement nor reassessment
resets the delivery budget; it is cumulative. Use the existing work ledger;
create no new controller, record schema, approval step, or universal retry
count.

Suspend broad implementation and require one strategy reassessment when any of
these facts is recorded:

- the delivery budget is exhausted without the milestone movement it was
  intended to buy;
- implementation begins to own a commodity protocol, parser, platform client,
  helper process, or infrastructure subsystem absent from the accepted
  `reuse_decision`;
- an expensive target or external attempt fails in harness or transport and the
  next attempt lacks a cheaper local reproduction, differential observation, or
  evidence-backed reason why neither is possible; or
- the actual source or subsystem boundary leaves the approved delivery
  envelope before the real user path has passed.

These are task-specific facts, not universal retry counts or line thresholds.
The reassessment extends the existing work ledger; it creates no new lifecycle
status or parallel state machine. It records the
accepted milestone state, causal evidence, budget consumed, reuse alternatives,
keep/delete boundary, cheapest falsifier, and either one `next_action` naming
the action, its allowed surface, and the evidence it must produce, or a
[decision packet](architecture-decision-gate.md#decision-packet).

The head CTO performs the reassessment and may continue autonomously only
when no grounding trigger is recorded and the chosen `next_action` remains
inside the accepted product, architecture, `first_user_path` allowlist, trust
boundary, authority, and continuing-cost envelope. A new runtime or process
boundary, architecture commitment, scope change, continuing cost, or external
authority returns through the existing user decision route. Broad mutation
remains suspended until one of those two outputs is registered; local read-only
diagnosis and preservation remain allowed.

## Grounding control

When the user requests grounding or the delivery records a grounding trigger,
follow [grounding.md](grounding.md); it owns the freeze and the user-controlled
resumption.

## Delegate execution

Before dispatching a large, costly, or architecture-bearing unit, inspect only
the contract seams that have caused material false conclusions: plan against
acceptance, decision against authority, and evidence against claim. Put each
actual mismatch directly into the executor brief;
when none exists, the preflight creates no separate checklist or durable status.
Skip this preflight for routine narrow work.

Write each owned executor's task by the
[shared prompt rules](prompt-mode.md#shared-prompt-rules) and ask it to report
changed files, checks run, and unresolved risks.

For a research unit, also name the decision it is meant to unlock, one
answerable question, its evidence boundary, its effort or cost budget, and its
stop condition.

Prefer a fresh internal subagent when separate context creates a material
benefit: independent evidence, parallel work, isolated ownership, or an
adversarial review with a different error profile. Keep a compact sequential
unit in the current agent when delegation adds none of those benefits. Use
parallel executors only for genuinely independent units; keep one capacity slot
for integration and urgent continuation. Follow the repository's
subagent model policy when one exists.

Do not delegate the entire vague outcome to one agent and then repeat its conclusion.
Split by independently verifiable ownership, for example implementation,
documentation/canon, and adversarial verification.

## Supervise actively

For internal subagents after dispatch:

1. Keep a registry of required executors and their expected artifacts.
2. Check status after tool calls and at useful integration boundaries. If an
   executor stops without a usable final result, inspect what exists and send a
   focused continuation or replace the unit; do not wait for the user to notice.
3. Collect every required final result. A commit, confident summary, or green
   focused test is evidence to inspect, not proof of integrated completion.
4. Review shared-workspace diffs before accepting them. Detect overlapping edits
   and preserve unrelated user changes.
5. Give concise progress updates that name the current phase, accepted evidence,
   open items, and whether work can continue autonomously. Do not describe a
   direction as implementation-ready while required evidence, critique, or a
   user decision remains open.

When the owner asks how work is going, project the nearest observable acceptance barrier,
its current state, the last material change, and one action capable of changing
that barrier. Activity is context, not progress: commits, tests, elapsed work,
and executor count belong in the answer only when they change that projection.
A repository-specific status integration follows its declared invocation and
authority contract; do not substitute it for collecting this delivery's own
subagent results.

Before a focused continuation, replacement, reopened unit, or audit repair,
record the concrete evidence, input, or method delta that makes the next attempt
meaningfully different. A replacement worker does not reset the accepted outcome
or its task-specific budget. If the same evidenced cause repeats without a new
delta, or the available budget is exhausted, stop the repair loop and return
`NOT_PROVEN` with the last evidence and one concrete next action. Use native
`BLOCKED` only when that runtime's blocked-status rules and the authority or
external-state boundary are actually satisfied.

When another executor is warranted, compile its bounded continuation from the
exact unproved gap, already accepted evidence, current source fingerprint,
allowed change surface, and required evidence, input, or method delta. The head
CTO verifies the acceptance boundary before dispatch. The owner does not relay
this technical context between chats.

## Integrate and verify

The head agent personally verifies the integrated result:

- inspect the actual diff and current working trees; when a fix also changes
  tests, assertions, thresholds, skips, or suppressions, confirm that the original
  requirement remains checked;
- run focused checks, then the repository-level gate proportional to risk;
- exercise the real user or service path when feasible;
- verify local, release, and production defaults separately when configuration
  differs by environment;
- check cleanup, orphaned resources, rollback, and failure behavior;
- synchronize canonical docs, logs, and task state when they are in scope;
- confirm commits contain only intended changes and that no required executor
  is still running or uncollected.

When a false positive is materially plausible for the highest-risk acceptance
row and a disposable fixture or target makes the check safe, run one safe
disposable negative control. Breaking the required evidence binding must change
`pass` to `fail` or `NOT_PROVEN`; restore the fixture and rerun the authoritative
acceptance on the clean candidate. Do not impose this on every acceptance row or
build a universal evidence platform. From the same acceptance output, show the
owner the observable user result and name what later work may inherit and what it
must prove again.

After the first passing user path, inspect each proof-support artifact created by
this outcome. Keep it only when it is required for recurring acceptance, safety,
or diagnosis; otherwise remove it before final acceptance and rerun the affected
checks. Never delete historical evidence or unrelated user work, and do not turn
this closeout check into a repository-wide cleanup.

When a check reveals a new gap, reopen the relevant unit and continue. Do not
relabel a discovered requirement as a follow-up merely to preserve a completion
conclusion.

## Tail audit

The tail audit checks whether an accepted outcome was delivered. It does not
replace the pre-implementation challenge of the architecture premise and does
not widen the conclusion beyond the decision packet's evidence.

Before saying the outcome is done, dispatch a fresh-context subagent whose goal
is to prove it is **not** done. Point it at the real outcome, current diff,
acceptance bar, and runtime state; do not give it the builder's reasoning.

The audit checks at least:

1. Does the real path behave as requested, not merely the mocked path?
2. Are environment defaults and deployed configuration aligned with the conclusion?
3. Are migrations, cleanup, failure recovery, and rollback complete?
4. Are docs, task state, versioning, and release wiring current?
5. Are there uncommitted changes, stopped agents, or unverified reports?
6. What would the user's most likely next question expose as unfinished?

Resolve every valid in-scope finding and rerun the affected checks. Repair is
subject to the non-convergence rule above; a repeated cause without a new
evidence/input/method delta ends as `NOT_PROVEN`, not another implicit worker
budget. If a finding needs new authority or a product decision, report it
explicitly instead of guessing or hiding it under “done”.

A finding reopens delivery only when it falsifies the observable completion
bar, an accepted safety or authority boundary, a required repository contract,
or a release gate. Improvements that preserve those properties are recorded as
follow-up work and do not invalidate the working state or start another general
review cycle.

## Completion gate

The outcome is complete only when all are true:

- the observable done bar passes on the integrated state;
- any applicable architecture decision packet supports the bounded conclusion being
  reported, and its recommendation and actual authority agree with the work
  performed;
- any applicable feasibility receipt comes from the same product-path artifact
  and load-bearing target boundary as the completed conclusion;
- every required owned-executor result has been collected and reviewed;
- repository-level checks proportional to risk pass;
- the tail audit has no unresolved in-scope finding;
- docs and task state agree with code and runtime reality;
- any remaining action is genuinely outside the agreed outcome and is named in
  the handoff. An in-scope action waiting for authority keeps the outcome
  incomplete; it must never be converted to `complete` for a tidy handoff.

Finish with the [owner brief](owner-brief.md) and the outcome first, then
verification, commits/artifacts, and the small set of remaining external
actions. Never use “the executor finished” as a
completion criterion.
