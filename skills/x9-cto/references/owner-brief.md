# Owner brief

Decision, Judge, Grounding, and the final autonomous-delivery handoff put this
semantic brief before any technical appendix and localize its labels into the
user's language. Quick questions, Brainstorm, Hands-on help, and progress
updates do not use it.

- **Recommendation** — proceed, validate first, or stop. State one concrete
  direction, not a menu of implementation mechanisms.
- **Evidence** — supported, partially supported, or not proven. Keep this line
  even when detailed provenance is unnecessary; for a consequential decision,
  also name the source, relevant version or environment, and observation time.
- **Why** — up to three decision-bearing facts or tradeoffs.
- **Allowed now** — implementation, one bounded experiment, read-only
  investigation, or nothing until a named decision or authorization. A
  recommendation never expands existing authority.
- **Owner action** — `None`, or one current product, cost, risk, canon,
  authority, or resumption decision after the CTO has recommended an option.
- **Next** — the next action, stated as
  [Next action and ownership](../SKILL.md#next-action-and-ownership) requires.

Show a material risk, cost, reversibility limit, or independent blocker whenever
it can change the recommendation or allowed action; do not invent one merely to
fill the format. Concision must not hide a second independent blocker. Ask only
the current gating owner question and list any later owner choices as deferred,
with the condition that will make each one current. An authorization that the
recommended next action needs, such as a spend, a new account, or another
external action, is current even when a cheaper preliminary check might make it
unnecessary: ask for it now instead of deferring it, as one question that already
proposes its ceiling.
Alternatives appear only when a real product, cost, authority, or risk tradeoff
remains.

## Mode states

The owner brief projects exact mode-specific states; it never replaces or
weakens them:

- `IMPLEMENTATION_READY` may project to **proceed**, but implementation is
  allowed only within existing authority. A Grounding freeze still requires the
  owner's explicit confirmation before resumption.
- `EXPERIMENT_ONLY` and `AWAITING_CRITIQUE` project to **validate first**;
  broad implementation remains blocked.
- `AWAITING_USER_DECISION` requires an owner action after the CTO's
  recommendation.
- `DO_NOT_IMPLEMENT` projects to **stop** for the named dependent scope.
- `DEGRADED`, `INSUFFICIENT`, and `NOT_PROVEN` cannot be presented as supported
  evidence or as permission for the dependent action.
- `NOT_APPLICABLE` is only a gate classification; combine it with the actual
  recommendation rather than presenting it as the decision.

When a task-specific delivery budget is exhausted without its accepted user-path
movement, do not project ordinary progress or permission to continue. Preserve
the current delivery-budget reassessment and Grounding rules, including the
freeze and owner-controlled resumption; do not create a universal time or retry
limit.

Do not wrap the exact Automatic Judge YAML in this brief. Judge, Grounding, and
autonomous-delivery modes retain their required substantive fields and safety
semantics; the brief only puts their human-facing conclusion and required owner
action first.
