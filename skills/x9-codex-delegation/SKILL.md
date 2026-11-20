---
name: x9-codex-delegation
description: Claude Code only; never use in a Codex session. Use when substantial, well-scoped work should actually be delegated to Codex — «отдай в Codex», «делегируй Codex», «передай эту часть работы в Codex, чтобы распределить лимиты», "use Codex", implementation, migration, codebase analysis, logged-in browser work, UI verification, or a second-opinion review. Do not use for checking or planning subscription quotas without a concrete task, trivial work, choosing between Claude models, merely drafting a prompt/brief that is not explicitly being sent to Codex, or generating images (x9-codex-imagegen).
---

# Delegate from Claude Code to Codex

Use the plugin route when it is available; otherwise fall back to the raw CLI.

The [onboarding declaration](references/onboarding.json) is the machine-readable onboarding contract.

When Claude and OpenAI/Codex are backed by separate subscriptions or usage pools, delegation can distribute substantial work instead of exhausting only the Claude allowance. Treat that as a user-specific routing benefit, not a promise of lower cost: API billing, plan limits, and available runtimes vary.

## Choose the route

- **Implementation or fixes:** use the installed `codex:codex-rescue` subagent when available. It is write-capable; the active project's local-change authority applies.
- **Read-only review or one-shot analysis:** use the plugin route when callable, otherwise raw `codex exec`.
- **Logged-in browsing:** delegate the whole bounded browse-and-return task and route it through `x9-browser-session`. Shell read-only mode does not change the separately approved browser authority.
- **Plugin commands marked user-only:** report the exact command for the user; do not pretend it was invoked programmatically.

## Raw fallback

Read [references/codex-cli.md](references/codex-cli.md) and use its one-shot or resume recipe after checking the current command help. That reference owns exact flags and known differences between `exec` and `resume`; this skill owns the delegation contract, not the volatile command surface.

## Brief contract

Load `x9-agent-instructions` before writing the first brief and apply its rubric; if it is unavailable, say so and pass a self-contained outcome, relevant files/sources, constraints, authority, deliverable, and completion bar. Add these failure rules when tools or current facts are load-bearing:

- In a one-shot run, carry authorized steps through instead of ending on a proposal or offer, and check the result against the brief before finishing.
- Report failed or cancelled calls exactly; do not substitute memory.
- Surface an unresolved fork only when it materially changes the result.
- Attach evidence appropriate to the task: paths/diff/tests for code; URLs and exact facts for research.

## Verify delegated work

For write-capable work, the delegate's report is advisory:

1. Inspect `git status` and the full relevant diff; preserve unrelated changes.
2. Run focused verification in the orchestrator's environment.
3. Confirm the result matches the brief rather than only the delegate's narration.

Stop retrying when the same blocking cause repeats, the budget is exhausted, or a fresh run cannot add evidence. Report the blocker instead of using a universal round count.

## Record the delegation

Logging is off by default. Append to the log only when the user explicitly opts in for the current task/session or an existing user-owned policy records that choice; follow [references/logging.md](references/logging.md) then. Delegation works normally without a log; do not ask again when the current scope already contains the answer.

## Done

- The actual Codex model/runtime is inherited or explicitly confirmed when load-bearing.
- Tool failures and degraded results are visible.
- Write results have orchestrator-owned diff review and verification evidence.
- When logging was enabled, the minimal telemetry row is recorded or the logging failure is visible.
