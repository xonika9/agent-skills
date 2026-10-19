# Judge mode

Triggered outside active autonomous delivery by the exact installed invocation
with the whole mode token `judge` under [runtime mechanics](runtime.md), or by
a report from an external executor/chat that needs a decision. A report from an executor owned by the current autonomous
delivery is an internal integration input and follows `execution-mode.md`; it
does not switch this chat into prompt-handoff mode.

Context: the user works in the head chat; the executors are agents in other
chats with no memory of this dialogue. The user brings an executor's report and
expects a decision from you, plus ready-to-paste continuation text only when the
decision requires more executor work.

When the user provides a link or identifier for an external task that is not a
registered executor of the active delivery, inspect its current state,
artifacts, and claimed checks through the runtime's native task primitives
before judging it. The link authorizes read-only inspection, not adoption or
continuation. Return one concrete recommendation: accept and close, prepare a
focused continuation, or request a user decision. If the task or its claimed
evidence cannot be inspected, report `NOT_PROVEN` and request the missing access
or report. Do not continue, close, archive, or otherwise mutate it without
separate authority.

If autonomous delivery is active, this mode applies only when the user
explicitly asks to pause that delivery and prepare a prompt for an external
chat. Otherwise keep owning the delivery and actively collect internal
subagents.

## What you do

1. **Assess the report on the merits.** For each finding — valid, cosmetic, or wrong. Do not echo the report's wording; give your own judgment.
2. **Check against decisions already made in this chat.** If a finding repeats something already closed, say so plainly and do not reopen it (the same "do not reopen closed decisions" rule from `SKILL.md` → How to make decisions).
3. **Check against the repo canon.** If a finding proposes changing the canon, first record the conflict; do not propose a new canon automatically.
4. **Give a recommendation for each open item** — which option we take and why. No long reasoning.
5. **Prepare an executor prompt only for a focused continuation.** An accepted
   result or a decision that belongs to the user needs no synthetic follow-up.

## Response format in Judge mode

Always return a **short explanation** of what is valid, what is not, and the
recommendation. Add a second **prompt in a code block** only when the
recommendation is a focused continuation for the executor. For `accept and
close`, stop after the explanation. For a user-owned decision, present that
decision under the repository's normal question contract instead of inventing
executor work.

## Prompt discipline

Write the continuation under the
[shared prompt rules](prompt-mode.md#shared-prompt-rules). By default it goes
into the executor's chat, which already holds the task context, so it is a
delta; make it self-contained only when the user asks for a new chat. Add an
instruction to start implementation only when the user asks for it, and do not
repeat items that earlier prompts already closed.

## What you do not do

- Do not reopen accepted decisions without a clear new contradiction.
- Do not dump every option when the recommendation is obvious.
- Do not edit documents or the canon yourself — the executor does that from your prompt.
- Do not turn Judge into a brainstorm. If the report is raw and needs discussion, say so and switch to brainstorm mode.
