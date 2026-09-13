---
name: x9-opencode-sessions
description: OpenCode V2 only. Use to find, read, continue, message, coordinate, wait for, or collect results from other OpenCode chats — «найди сессию OpenCode», «прочитай другой чат», «продолжи чат», «напиши в сессию», «скоординируй OpenCode-чаты», «дождись завершения сессии». Do not use for OpenCode documentation or configuration questions (use opencode), the current parent session's own child agents (use native subagent), or Codex/Claude and other cross-harness sessions.
compatibility: Requires OpenCode V2 with the opencode2 CLI connected to its Sessions API, plus Python 3. It is not compatible with Claude Code, Codex, or other session harnesses.
---

# OpenCode sessions

Use this skill only in OpenCode V2. For child sessions owned by the current parent,
prefer the native `subagent` tool. Use the Sessions API only to inspect or coordinate a
different root or child branch.

The [machine-readable onboarding contract](references/onboarding.json) lists external prerequisites.

List only enough session metadata to resolve the request. Start with a supplied session
ID when available; otherwise constrain the list by title/search, project, directory, or
parent. Stop before sending when the match is ambiguous, and ask the user to select one
target.

Run [the wrapper](scripts/opencode_sessions.py) for API calls. It emits normalized JSON,
shows only text message parts, and keeps reasoning bodies and tool arguments out of the
default output. Read [the API reference](references/open-code-v2.md) for command forms
and response semantics.

## Sending and waiting

`prompt` is preview-first. Run it without `--apply`, retain and show its generated
`message_id`, then dispatch the same ID with `--apply` only after the user has explicitly
asked to send and one target is unambiguous. The original explicit request is sufficient;
do not add a confirmation step. Never send a live message unless the user requested it.
The wrapper permanently reserves each preview ID and records a one-use local receipt
containing the session ID and a hash of the text; `--apply` rejects a missing, reused, or
mismatched receipt.

If dispatch times out or its outcome is unknown, do not retry. Reconcile that exact
`message_id` with `message` before any further action. Do not delete, rename, move, or
otherwise alter sessions.

`wait` may be unavailable on a running V2 service. Treat that response as blocked, then
inspect `active` and paginated `messages`; never infer completion from the failed wait.

## Done

Return the selected session ID, requested text or activity/result, and any child-session
relationship observed. For a sent message, return its `message_id` and the dispatch or
reconciliation status. A failed API call is `BLOCKED` or `UNKNOWN`, not evidence that a
session completed or received a message.
