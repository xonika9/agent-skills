# Prompt mode

Selected by the installed `x9-cto prompt` invocation, or by a request to prepare
executor handoffs. Mode spelling and launches follow
[runtime mechanics](runtime.md). An internal handoff during active CTO delivery
stays in that delivery unless the owner explicitly pauses it.

Resolve the target and any repository-specific prompt kinds through
[repository context](repository-context.md). Load the declared local owner and
its handoff reference only when applicable. Do not assume a tracker, numeric
queue, shared deploy, base branch, merge grant, or publication permission.

For an undefined kind, use the shared rules only when the target is sufficiently
specified; state that no kind-specific contract exists. An unresolved identifier
is not a task description. An inaccessible declared owner is not an absent one.

## Shared prompt rules

These rules govern every prompt the CTO writes for another chat or agent: this
mode, a Judge continuation, and the external handoff in
[Next action and ownership](../SKILL.md#next-action-and-ownership).

- Write the prompt in the user's language; keep identifiers, commands, paths,
  and URLs exact.
- Carry only what the executor cannot load itself: decisions taken in this
  chat, current state, conflicts with neighboring work, and granted or withheld
  authority. Do not retell a card, plan, skill, or `AGENTS.md` that the
  executor reads anyway; point to it.
- A prompt for a chat that already holds the task context is a delta. A prompt
  for a new chat is self-contained for what the linked sources do not supply.
- State the outcome and the completion bar, not a path. Fence only actions that
  are irreversible, externally visible, costly, or touch shared state, and say
  which.
- List document edits as edits, without the reasons; the reasons go to the
  user outside the prompt.
- If a previous prompt was wrong, cancel that instruction explicitly in the new
  one.
- End by naming what the executor returns.

## Preparing and launching

Return one prompt per independent target, with the actual installed invocation
of `x9-cto` when the executor needs this role. Take working-directory,
isolation, closure, and authority terms from the task and applicable local
contract. Point to their owners instead of restating their full instructions.

Preparing prompts is not execution authority. Launch a top-level chat only on
an explicit request for one, using the active runtime's supported route. An
internal subagent is a different lifecycle; do not create an ordinary chat just
because the owner asked for delegated work. If launch is unavailable, return
the prompt and report that no chat was started. Runtime orchestration owns
idempotency, reconciliation, and cancellation.
