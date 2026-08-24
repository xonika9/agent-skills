---
name: x9-idea-critic
description: Use only when the user explicitly asks to criticize, red-team, pressure-test, or find reasons an idea may fail — «раскритикуй идею», «найди слабые места», «red-team this idea». Do not trigger for ordinary brainstorming, balanced evaluation, implementation review, or when the user only asks to improve an idea.
---

# Idea critic

Criticize through the routes the user selected. Opus and GPT are independent perspectives with different error profiles; neither route is a fallback or a quality tier.

## Select mode

For `/x9-idea-critic [mode] [idea]`, treat the first argument as a mode only when it is one of the recognized words below. Otherwise it is part of the idea. Natural-language requests map to the same modes.

When the invocation omits the idea, recover the latest clearly discussed proposal, intended outcome, success criterion, and known constraints from the conversation. Ask one short question only when the conversation leaves the target idea ambiguous.

| Mode | Natural-language examples | Critics |
|---|---|---|
| default / omitted | «раскритикуй идею», «проверь на прочность» | one fresh Opus critic and one fresh GPT critic |
| `opus` | «раскритикуй опусом» | one fresh Opus critic |
| `gpt` | «спроси GPT», «раскритикуй через GPT» | one fresh GPT critic |
| `full` | «разнеси по полной», «панель критиков» | one critic from each provider for each of 2–3 declared lenses |

For `full`, select and declare exactly two or three applicable lenses before dispatch from feasibility/execution, user or market demand, and devil's-advocate/simpler alternative. Tell the user that this mode is slower and heavier, then start one critic per declared lens/provider pair as host capacity permits. That declared matrix is the completion boundary.

## Sealed brief

Before dispatch, collect the load-bearing evidence into one sealed packet. Give every critic the same factual packet:

- the proposal in neutral language;
- intended user/outcome and observable success criterion;
- known constraints and an evidence packet containing the relevant content or excerpt, its source path or URL as provenance, retrieval time when freshness matters, whether the packet includes the full source or an excerpt, and any extraction limits;
- the critic's job: identify invalidating assumptions, failure modes, relevant competition, a cheaper or simpler path to the same outcome, the most likely practical cause of failure, and the cheapest disconfirming tests;
- required output: `KILLER`, `SERIOUS`, `MINOR`, evidence/uncertainty, and a verdict.

For `full`, append exactly one declared lens to each critic's job; the lens is the only per-critic difference. A provenance path or URL identifies the supplied evidence but does not authorize the critic to read beyond the packet. Do not put credentials, secret values, or irrelevant private content in it.

Exclude advocacy and solution-selling from the critic's role, but do not omit factual context that would make the critique a straw man. Critics work only from the sealed packet and must identify evidence gaps instead of searching for more context, using tools, or delegating.

## Runtime routes

- **From Claude Code:** read [the Claude Code adapter](references/claude-code.md).
- **From Codex:** read [the Codex adapter](references/codex.md).
- **From OpenCode:** read [the OpenCode adapter](references/opencode.md).

Every critic must run at `high` effort. Every adapter must select a currently available model from the promised provider family. Honor an exact user-selected version only when live discovery confirms it; otherwise fail that route rather than silently substituting another family. An accepted runtime selector is evidence that the control was applied; when the runtime omits post-run effective-model or effort telemetry, record that property as `NOT_PROVEN` without failing an otherwise successful route.

## Failure and synthesis

- Retry a failed route once only when the failure is transient and the retry changes something concrete.
- Judge completeness against the selected mode. A successful `opus` or `gpt` run is `COMPLETE`; it is not degraded merely because the user requested one critic.
- In default mode, one missing route yields `DEGRADED`. In `full`, a missing requested provider or lens yields `DEGRADED`.
- If every requested route fails or the orchestrator cannot assemble a sufficient packet of load-bearing evidence, return `BLOCKED` with verdict `NOT_PROVEN`; do not manufacture a substantive verdict from the orchestrator's prior beliefs.
- Keep attribution: show which critic raised each invalidating point and whether the other independently agreed.
- Resolve duplicate wording, not disagreement. Surface material conflicts and judge them against evidence.
- Keep the synthesis concise by grouping overlap and separating required changes from optional improvements, not by dropping findings or dependencies that could change the verdict.
- Critics own diagnosis; the orchestrator owns the post-critique rewrite. After resolving the findings, turn them into the strongest defensible next version of the idea rather than stopping at recommendations.
- Base the rewrite only on findings upheld during synthesis and available evidence. Preserve the intended outcome and success criterion unless they were invalidated; change the intended user, scope, mechanism, assumptions, or delivery model where necessary.

## Output

1. Status: `COMPLETE`, `DEGRADED`, or `BLOCKED`.
2. Verdict: `KILL`, `REVISE`, `SURVIVES`, or `NOT_PROVEN` when blocked.
3. Invalidating findings with evidence and attribution.
4. Serious/minor risks.
5. For a substantive verdict, the best defensible next version: a self-contained rewritten proposal covering its intended user, outcome, operating mechanism, scope, and success criterion. It must be understandable without rereading the critique.
6. Change map connecting every material difference from the original proposal to the upheld finding or evidence that justifies it. Group overlapping work, show dependencies, and distinguish changes required by `KILLER` or `SERIOUS` findings from optional improvements, accepted risks, or deferred work associated with `MINOR` findings.
7. Cheapest tests that could falsify the remaining assumptions.
8. Missing evidence and unresolved disagreement.

For `REVISE`, rewrite the original proposal and include every change needed to address upheld `KILLER` and `SERIOUS` findings. For `SURVIVES`, return a hardened version with only the changes justified by the findings. For `KILL`, do not disguise the invalidated core as a revision: return the closest evidence-supported replacement for the same intended outcome, or state that no defensible replacement is proven. For `BLOCKED`, do not manufacture a rewrite; explain what evidence is needed before one can be produced.
