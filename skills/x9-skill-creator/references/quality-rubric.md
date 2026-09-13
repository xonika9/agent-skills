# Skill quality rubric

Use every dimension when creating, auditing, or fixing a skill. Structural checks are marked `[s]`; judgment and behavior checks are `[j]` and `[b]`. Apply the loaded `x9-agent-instructions` rubric to all agent-facing instructional prose; this rubric does not duplicate that skill's language, prescription, or line-value rules.

## Contents

- [Triggering and scope](#1-triggering-and-scope-sjb)
- [Runtime and placement](#2-runtime-and-placement-jb)
- [Ownership boundary](#ownership-boundary-j)
- [Degree of freedom](#3-degree-of-freedom-j)
- [Authority and preservation](#4-authority-and-preservation-jb)
- [Context cost and freshness](#5-context-cost-and-freshness-sj)
- [Progressive disclosure](#6-progressive-disclosure-sj)
- [Observable completion](#7-observable-completion-jb)
- [Behavioral evidence](#8-behavioral-evidence-b)
- [Stop and degradation](#9-stop-and-degradation-jb)
- [Clarity and questions](#10-clarity-and-questions-sj)
- [Audit severity](#audit-severity)
- [Judge checklist](#judge-checklist)

## 1. Triggering and scope `[s+j+b]`

- `description` states the distinct user intent concisely; it does not summarize the workflow. Add example phrases or a near-miss only when they resolve a real routing ambiguity; keep the full trigger cases in the audit or evaluation evidence.
- Put the distinguishing use case first so the opening remains useful when a runtime shortens descriptions; `name` and folder match.
- With static evidence, classify at least one realistic positive trigger and one near-miss against the metadata. With behavioral evidence, verify them in a fresh runtime.

## 2. Runtime and placement `[j+b]`

- Name supported runtimes and canonical placement.
- Before frontmatter, classify the skill separately in each claimed runtime as `model-invoked` or `user-only`; record cross-skill consumption separately from that classification. A `user-only` claim needs a real invocation path in that runtime.
- Keep shared method in the core; isolate volatile metadata, tool, model, CLI, and browser facts in runtime adapters with live-discovery rules.
- Do not treat a runtime-specific invocation mechanism as portable metadata or as evidence for another runtime.
- With behavioral evidence, verify a representative run on each claimed runtime or mark the run `DEGRADED`. With static evidence, name unverified runtimes without turning that declared scope boundary into a finding.

## 3. Degree of freedom `[j]`

- Flexible judgment stays in outcome-oriented prose.
- Fragile repeated transformations use deterministic scripts.
- Before writing a numbered step, name the invariant that makes a wrong order impossible and write that invariant instead. A step survives only where a wrong order cannot be undone: irreversible sequences, approval gates, deterministic transformations, recovery from a known-bad state. A sequence present in the request is not evidence that the order is load-bearing.

## 4. Authority and preservation `[j+b]`

- Distinguish read/report, safe in-scope local change, and external/destructive/costly/scope-expanding actions.
- Preserve user-owned files, tabs, repository changes, and secrets.
- State hard negative boundaries explicitly when violating them would cause loss or external side effects.
- Exercise an authority or preservation boundary when behavioral evidence is selected for a skill that can mutate state.

## 5. Context cost and freshness `[s+j]`

- Every paragraph carries non-obvious behavior; details live in linked references.
- One rule lives in one place. A rule restated in a second file, in `Done`, or in a runtime adapter is a defect rather than emphasis; the second occurrence becomes a link to the owner.
- No two rules across the skill and its references may be impossible to satisfy at once.
- Volatile models, flags, schemas, tool versions, rankings, and performance claims use live discovery before they become load-bearing. A freshness date is not a substitute for current validation.
- No junk, placeholders, secrets, or temporary experiment state in the skill.

## 6. Progressive disclosure `[s+j]`

- Metadata triggers; the body is a concise map; references/scripts/assets load only when needed.
- Every agent-consumed resource is reachable from `SKILL.md`, directly or through a referenced resource. Runtime-loaded metadata and maintainer regression tests may instead be owned by their canonical loader or test command.
- Cross-skill ownership is explicit rather than duplicated silently.
- Shared material for multiple confirmed `user-only` skills is an ordinary accessible file, directly linked by every consumer. It is not a hidden owner or router skill.

## Ownership boundary `[j]`

- Create a new skill owner only for an independent user intent with a real invocation path in at least one claimed runtime, or for a proven independent consumer.
- Growing an existing file, a shared reference, or a consumption relationship alone does not establish a new owner; extend the current owner or use the shared file instead.

## 7. Observable completion `[j+b]`

- Done is a command, diff, schema, rendered result, source trace, hash, or reproduced behavior.
- Verification examines the real artifact, not the builder's report.
- Done names the artifact to inspect, not a self-check to perform. The author's own fresh-context attempt to disprove completion belongs to behavioral evaluation ([evals.md](evals.md)) and does not go inside the skill being written.

## 8. Behavioral evidence `[b]`

- State the selected evidence tier: static or behavioral. A behavioral check may be focused or full in proportion to the change.
- Run the applicable matrix from [evals.md](evals.md) when behavioral evidence is requested or required for a stable/shared/high-risk claim.
- For release-gated material changes, compare old/new or with/without on identical prompts in clean contexts.
- For rapidly changing personal skills, live evaluation may be deferred until real use yields a stable regression scenario. Record the deferral; it is not a finding by itself.
- Never claim behavior was proven by structural lint or instruction compliance.

## 9. Stop and degradation `[j+b]`

- Define retry/non-convergence conditions when tools, critics, or loops can fail.
- Missing evidence or a failed route produces `DEGRADED`, `NOT_PROVEN`, or `BLOCKED`, not false completion.
- Universal retry counts require task-specific evidence; otherwise stop on repeated cause or exhausted budget.

## 10. Clarity and questions `[s+j]`

- One sentence has one operational reading.
- Ask only for load-bearing ambiguity that cannot be recovered from context.
- Explain reasons where they improve judgment; use explicit prohibitions for safety/preservation and positive targets for ordinary guidance.

## Audit severity

- **Blocker:** unsafe, broken runtime, destructive behavior, leaked secret, or failing required validation.
- **Important:** likely mis-trigger, undelivered contract, stale adapter, required-but-missing behavioral evidence, or fragile prose operation.
- **Minor:** real lower-risk clarity, duplication, or maintenance issue.

Severity is assigned here. Finding lifecycle, filtering, status recomputation, and the handoff contract are owned by [audit reporting](audit-reporting.md).

## Judge checklist

Answer yes/no with a concrete fix:

1. Are triggers and near-misses precise?
2. Are runtime-specific facts isolated and fresh?
3. Does rigidity match fragility?
4. Are authority, preservation, and secrets handled?
5. Is context lean and progressively disclosed?
6. Is Done externally observable?
7. Is the evidence tier explicit, and did behavior pass when behavioral evidence was in scope?
8. Are stopping and ambiguity rules unambiguous?
9. Is invocation classified separately for every claimed runtime, with consumption and runtime mechanics kept separate?
10. Does a new owner meet the ownership boundary, and is shared `user-only` material directly accessible to every consumer?
11. Does every rule appear exactly once, with no pair that cannot both hold?
12. Was `x9-agent-instructions` applied to every agent-facing instruction in scope, or was its absence recorded as `not applicable` or `degraded`?
