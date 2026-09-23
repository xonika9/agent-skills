---
name: x9-idea-critic
description: Use only when the user explicitly asks to criticize, red-team, pressure-test, or find reasons an idea may fail — «раскритикуй идею», «найди слабые места», «red-team this idea». Do not trigger for ordinary brainstorming, balanced evaluation, implementation review, or when the user only asks to improve an idea.
---

# Idea critic

Criticize through the routes the user selected. Run each provider route in a separate fresh context; neither route is a fallback or a quality tier. Route names identify providers, not the currently selected models. An unavailable provider does not become a second vote from the available provider.

The [machine-readable onboarding contract](references/onboarding.json) lists external prerequisites.

## Select mode

For `/x9-idea-critic [mode] [idea]`, treat the first argument as a mode only when it is one of the recognized words below. Otherwise it is part of the idea. Natural-language requests map to the same modes.

When the invocation omits the idea, recover the latest clearly discussed proposal, intended outcome, success criterion, and known constraints from the conversation. Ask one short question only when the conversation leaves the target idea ambiguous.

| Mode | Natural-language examples | Critics |
|---|---|---|
| default / omitted | «раскритикуй идею», «проверь на прочность» | one fresh Claude critic and one fresh GPT critic |
| `claude` | «раскритикуй через Claude» | one fresh Claude critic |
| `gpt` | «спроси GPT», «раскритикуй через GPT» | one fresh GPT critic |
| `full` | «разнеси по полной», «панель критиков» | one critic from each provider for each of 2–3 declared lenses |

For `full`, select and declare exactly two or three applicable lenses before dispatch from feasibility/execution, user or market demand, and devil's-advocate/simpler alternative. Tell the user that this mode is slower and heavier, then start one critic per declared lens/provider pair as host capacity permits. That declared matrix is the completion boundary.

## Sealed brief

Before dispatch, collect the load-bearing evidence into one sealed packet. Give every critic the same factual packet:

- the proposal in neutral language;
- intended user/outcome and observable success criterion;
- known constraints and an evidence packet containing the relevant content or excerpt, its source path or URL as provenance, retrieval time when freshness matters, whether the packet includes the full source or an excerpt, and any extraction limits;
- the critic's job: identify the few issues most likely to change the decision, the most likely practical cause of failure, a cheaper or simpler path to the same outcome, and the cheapest disconfirming test;
- required output: a `STOP`, `REVISE`, `PROCEED`, or `NOT_PROVEN` recommendation, followed by every distinct issue that could materially change the decision, rewritten proposal, or next action; prioritize them by impact, and for each state the evidence or uncertainty and the change or test it warrants.

For `full`, append exactly one declared lens to each critic's job; the lens is the only per-critic difference. A provenance path or URL identifies the supplied evidence but does not authorize the critic to read beyond the packet. Do not put credentials, secret values, or irrelevant private content in it.

Exclude advocacy, solution-selling, compliments, generic risk lists, and restatements of the proposal from the critic's role, but do not omit factual context that would make the critique a straw man. Critics work only from the sealed packet and must identify evidence gaps instead of searching for more context, using tools, or delegating.

## Model configuration

Before dispatch, read [`config.json`](config.json). Its four values are the sole source of default model and effort selections:

- `claude_model` is the selector passed to Claude CLI;
- `claude_effort` is the effort passed to Claude CLI;
- `gpt_model` is the OpenAI model selector resolved through the active runtime's live model catalog;
- `gpt_effort` is the GPT effort/variant selected through that runtime.

An official Claude CLI alias follows the service's current model in that alias's family, while an exact model ID stays pinned. These skill-specific selections override inherited model and effort defaults, not higher-priority runtime restrictions or explicit user model/effort choices.

Change only `config.json` to replace either default model or effort. Do not mirror its values in adapters or onboarding declarations. Confirm the configured model and effort through the selected adapter before each dispatch; editing the skill does not install a model or create a runtime agent.

## Runtime routes

- **From Claude Code:** read [the Claude Code adapter](references/claude-code.md).
- **From Codex:** read [the Codex adapter](references/codex.md).
- **From OpenCode:** read [the OpenCode adapter](references/opencode.md).

Every adapter must confirm that the selected model and effort controls are available. An explicit user-selected Claude or GPT model or effort replaces that route's default only when live discovery confirms it; otherwise fail that route rather than silently substituting another model, effort, or provider. Keep the requested selector and actual model as execution evidence, not as a user-facing section unless a mismatch or failure affects the recommendation. An accepted runtime selector is evidence that the control was applied; when the runtime omits post-run effective-model or effort telemetry, record that property as `NOT_PROVEN` without failing an otherwise successful route.

## Failure and synthesis

- Retry a failed route once only when the failure is transient and the retry changes something concrete.
- Treat a missing subscription, authentication, or exhausted quota as an unavailable route, not a transient failure. Continue the other selected provider without asking the user to subscribe or repeating the available provider as a stand-in.
- Judge completeness against the selected mode. A successful requested route is complete; in default mode one missing route is degraded, and in `full` any missing provider/lens pair is degraded.
- If every requested route fails or the orchestrator cannot assemble a sufficient evidence packet, the result is blocked and not proven; do not manufacture a recommendation from prior beliefs.
- Treat critic responses as private working material. Do not paste them, summarize them route by route, or preserve their structure in the user-facing answer.
- Test each objection against the evidence packet. Discard repetition, unsupported speculation, generic advice, and points that would not change the decision, proposal, or next action.
- Do not impose a numeric limit on material objections. Compression belongs in synthesis: group related findings without dropping any upheld issue that could change the recommendation or rewrite.
- Resolve duplicate wording, not disagreement. Mention a disagreement only when it materially changes the recommendation or the test needed to decide.
- Convert each retained issue into a concrete change to the proposal. Critics own diagnosis; the orchestrator owns prioritization, synthesis, and the rewritten proposal.
- Base the rewrite only on upheld issues and available evidence. Preserve the intended outcome and success criterion unless invalidated; change the intended user, scope, mechanism, assumptions, or delivery model where necessary.

## User-facing answer

Write for the person deciding what to do, not for another agent auditing the critique. Use the user's language and natural headings rather than internal status or severity codes.

1. **Recommendation.** In one short paragraph, say whether to stop, revise, proceed, or gather missing evidence, and give the decisive reason.
2. **What to change.** Give the smallest set of grouped, prioritized changes that covers every upheld issue material to viability. Connect each change to the practical problem it solves; do not omit a material issue to keep the list short.
3. **Better version.** Present the strongest defensible version of the idea as a compact, self-contained proposal covering its intended user, outcome, mechanism, scope, and success criterion. It must make sense without rereading the critique.
4. **Next step.** End with one concrete action and the observable result that determines whether to proceed, revise again, or stop.

Use only these four sections by default. Do not add separate critic reports, status fields, severity tables, risk registers, evidence inventories, change maps, test lists, or a second summary; include supporting evidence inline only when it changes confidence in the recommendation. Add a short limitation only when a route failed, evidence is missing, or unresolved disagreement could change the recommendation. Ask questions only when their answers are required to make a defensible recommendation or rewrite; in that case, the next step is to obtain those answers and state what would change direction.

When the original core fails, do not disguise it as a revision: offer the closest evidence-supported replacement for the same outcome, or state that none is proven. When evidence is insufficient, do not manufacture a better version. Otherwise, return the improved proposal directly rather than a catalogue of critic findings.
