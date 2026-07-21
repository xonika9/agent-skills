# Skill patterns: bad → better

Use the principle, not the wording.

## Triggering

Bad: `description: Creates a skill, writes files, then validates.`

Better: `description: Use when the user asks to create or audit an Agent Skill — «создай скилл», "audit skill". Do not use for ordinary code.`

## Runtime

Bad: one body mixes `~/.claude/skills`, Codex metadata, and exact current CLI flags.

Better: shared method in `SKILL.md`; Claude/Codex mechanics in separate dated adapters selected at runtime.

## Freedom

Bad: a prose agent computes byte offsets and rewrites line endings.

Better: a deterministic script owns byte-sensitive insertion; the agent chooses semantic metadata.

## Authority

Bad: "Research the topic and update the repository" when the user only asked for an answer.

Better: gathering and answering are authorized; persistent artifacts require an explicit request or a repository workflow already in scope.

## Preservation

Bad: `git checkout -- <file>` to remove an agent's unintended edit.

Better: inspect the diff and restore only the known generated change from a pre-edit snapshot or inverse patch.

## Context and freshness

Bad: model rankings, temporary experiment counters, and permanent method live together.

Better: durable method in the skill, current routing in a dated runtime adapter, measurements in operational state.

## Progressive disclosure

Bad: unlinked `references/advanced.md`, or the same rule copied into every runtime branch.

Better: the body says when to read each resource; one canonical rule is referenced by thin adapters.

## Completion

Bad: "Make sure the migration worked."

Better: all required fields validate and pre/post body hashes, BOM, and line endings match.

## Behavioral evidence

Bad: lint exits 0, therefore the skill is declared effective.

Better: lint exits 0 and clean-context positive, near-miss, failure, authority, and completion assertions pass.

## Degradation

Bad: one of two critics fails, but the synthesis is presented as complete.

Better: return `DEGRADED`, name the missing route, and limit the conclusion accordingly.

## Clarity

Bad: an interview is mandatory even when the request fully specifies scope and output.

Better: ask one question only when an unrecoverable ambiguity materially changes the implementation.
