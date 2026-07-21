---
name: x9-codex-delegation
description: Claude Code only; never use in a Codex session. Use when substantial, well-scoped work should actually be delegated to Codex — «отдай в Codex», «делегируй Codex», "use Codex", implementation, migration, codebase analysis, logged-in browser work, UI verification, or a second-opinion review. Do not use for trivial work, choosing between Claude models, or merely drafting a prompt/brief that is not explicitly being sent to Codex.
---

# Delegate from Claude Code to Codex

Use `x9-browser-session` for browser routing. Use the plugin route when it is available; the raw CLI remains a fallback for an explicitly requested delegation.

## Choose the route

- **Implementation or fixes:** use the installed `codex:codex-rescue` subagent when available. It is write-capable; the active project's local-change authority applies.
- **Read-only review or one-shot analysis:** use the plugin route when callable, otherwise raw `codex exec`.
- **Logged-in browsing:** delegate the whole bounded browse-and-return task and follow the browser adapter. Shell read-only mode does not change the separately approved browser authority.
- **Plugin commands marked user-only:** report the exact command for the user; do not pretend it was invoked programmatically.

## Raw fallback

Read [references/codex-cli.md](references/codex-cli.md) and use its currently verified one-shot or resume recipe. That dated reference owns exact flags and known differences between `exec` and `resume`; this skill owns the delegation contract, not the volatile command surface. Prefer the model configured in `~/.codex/config.toml` unless the user explicitly chooses another.

## Brief contract

Pass a self-contained outcome, relevant files/sources, constraints, authority, deliverable, and completion bar. Add these failure rules when tools or current facts are load-bearing:

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

After every actual Claude-to-Codex delegation, append one row to `~/.local/share/x9/codex-delegation-log.md`. Create the parent directory and initialize a small Markdown table when the file does not exist; preserve an existing file or symlink. Read its current table header before writing. Record the route, actual model/effort when observable, wall-clock time, Codex tokens, whether rework was needed, and the outcome or failure. Use `н/д` for unavailable data and `?` when rework is not known yet; never invent telemetry.

The log is permanent operational history, not a temporary experiment or a completion gate. A missing or unwritable log must be reported but must not fail the delegated task.

## Done

- The actual Codex model/runtime is inherited or explicitly confirmed when load-bearing.
- Tool failures and degraded results are visible.
- Write results have orchestrator-owned diff review and verification evidence.
- The delegation is recorded when the log is available; a logging failure is visible.
