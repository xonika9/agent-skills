---
name: x9-idea-critic
description: Use only when the user explicitly asks to criticize, red-team, pressure-test, or find reasons an idea may fail — «раскритикуй идею», «найди слабые места», «red-team this idea». Do not trigger for ordinary brainstorming, balanced evaluation, implementation review, or when the user only asks to improve an idea.
---

# Idea critic

Criticize through the routes the user selected. Opus and GPT are independent perspectives with different error profiles; neither route is a fallback or a quality tier.

## Select mode

For `/x9-idea-critic [mode] [idea]`, treat the first argument as a mode only when it is one of the recognized words below. Otherwise it is part of the idea. Natural-language requests map to the same modes.

| Mode | Natural-language examples | Critics |
|---|---|---|
| default / omitted | «раскритикуй идею», «проверь на прочность» | one fresh Opus critic and one fresh GPT critic |
| `opus` | «раскритикуй опусом» | one fresh Opus critic |
| `gpt` | «спроси GPT», «раскритикуй через GPT» | one fresh GPT critic through Codex |
| `full` | «разнеси по полной», «панель критиков» | one critic from each provider for each of 2–3 declared lenses |

For `full`, select and declare exactly two or three applicable lenses before dispatch from feasibility/execution, user or market demand, and devil's-advocate/simpler alternative. Tell the user that this mode is slower and heavier, then start one critic per declared lens/provider pair as host capacity permits. That declared matrix is the completion boundary.

## Sealed brief

Give each critic the same bounded brief:

- the proposal in neutral language;
- intended user/outcome and observable success criterion;
- known constraints, evidence, and source paths/URLs;
- the critic's job: identify invalidating assumptions, failure modes, relevant competition, a cheaper or simpler path to the same outcome, the most likely practical cause of failure, and the cheapest disconfirming tests;
- required output: `KILLER`, `SERIOUS`, `MINOR`, evidence/uncertainty, and a verdict.

Exclude advocacy and solution-selling from the critic's role, but do not omit factual context that would make the critique a straw man. A critic making factual claims must be able to read the cited repository artifacts or live sources.

## Runtime routes

- **From Claude Code:** read [the Claude Code adapter](references/claude-code.md).
- **From Codex:** read [the Codex adapter](references/codex.md).

Both adapters must select a currently available model from the promised provider family. Honor an exact user-selected version only when live discovery confirms it; otherwise fail that route rather than silently substituting another family. Pass only the sealed brief and explicit evidence locations, and grant only the read surfaces needed to inspect load-bearing evidence.

## Failure and synthesis

- Retry a failed route once only when the failure is transient and the retry changes something concrete.
- Judge completeness against the selected mode. A successful `opus` or `gpt` run is `COMPLETE`; it is not degraded merely because the user requested one critic.
- In default mode, one missing route yields `DEGRADED`. In `full`, a missing requested provider or lens yields `DEGRADED`.
- If every requested route fails or no critic can inspect the load-bearing evidence, return `BLOCKED` with verdict `NOT_PROVEN`; do not manufacture a substantive verdict from the orchestrator's prior beliefs.
- Keep attribution: show which critic raised each invalidating point and whether the other independently agreed.
- Resolve duplicate wording, not disagreement. Surface material conflicts and judge them against evidence.
- Keep the synthesis concise by grouping overlap and separating required changes from optional improvements, not by dropping findings or dependencies that could change the verdict.

## Output

1. Status: `COMPLETE`, `DEGRADED`, or `BLOCKED`.
2. Verdict: `KILL`, `REVISE`, `SURVIVES`, or `NOT_PROVEN` when blocked.
3. Invalidating findings with evidence and attribution.
4. Serious/minor risks.
5. Cheapest tests that could falsify the remaining assumptions.
6. Missing evidence and unresolved disagreement.
7. For `REVISE`, give a concrete revision agenda covering all findings upheld during synthesis. Distinguish changes required to address `KILLER` and `SERIOUS` findings from optional improvements, accepted risks, or deferred work associated with `MINOR` findings. Group overlapping work and show dependencies; do not cap the number of changes or omit necessary architecture work for brevity. For `SURVIVES`, recommend only changes justified by the findings and distinguish them from risks that can reasonably be accepted. For `KILL`, do not manufacture a rescue plan.
