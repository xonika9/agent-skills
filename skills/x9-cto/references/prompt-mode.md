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
mode, a Judge continuation, an owned executor's task, and the external handoff
in [Next action and ownership](../SKILL.md#next-action-and-ownership).

Load `x9-agent-instructions` before the first such prompt and apply its rubric;
it owns what a prompt carries and leaves out. If it is unavailable, state the
outcome, completion bar, fenced actions with their reasons, and what the
executor returns, apply the rules below, and say that the instruction rubric was
not applied. The CTO adds only these:

- Carry conflicts with neighboring work alongside the decisions, state, and
  authority from this chat.
- A prompt for a chat that already holds the task context is a delta. A prompt
  for a new chat is self-contained for what the linked sources do not supply.
- If a previous prompt was wrong, cancel that instruction explicitly in the new
  one.

## Preparing and launching

Return one prompt per independent target, with the actual installed invocation
of `x9-cto` when the executor needs this role. Take working-directory,
isolation, closure, and authority terms from the task and applicable local
contract. Point to their owners instead of restating their full instructions.

Preparing prompts is not execution authority. Launch a top-level chat only on
an explicit request for one, using the active runtime's supported route and
the models chosen under [launch defaults](runtime.md#launch-defaults). An
internal subagent is a different lifecycle; do not create an ordinary chat just
because the owner asked for delegated work. If launch is unavailable, return
the prompt and report that no chat was started. Runtime orchestration owns
idempotency, reconciliation, and cancellation.
