---
name: x9-decision-map
description: Use when a large initiative has material unresolved decisions and needs a durable pre-plan decision map — «составь карту решений», «зафиксируй решения по инициативе», "map the decisions before planning". Do not use for an implementation plan or a repeated multi-stage agent workflow; design the latter with x9-loop-engineering.
---

# Decision map

Create, find, read, and update the durable decision map for a large initiative before turning it into an implementation plan. This skill is model-invoked in Claude Code and Codex; its portable claim is structural Agent Skills compatibility only.

Use this only when unresolved choices can materially change an initiative's direction, scope, or plan. A request to design a recurring, multi-stage agent workflow belongs to `x9-loop-engineering`, even if it also has open decisions.

## Durable map

Read [the map format](references/map-format.md) before creating or changing a map. Use a canonical initiative ID and retain former names and aliases so later sessions can recover the same artifact.

First follow the repository's local documentation convention. If it does not designate a location for decision maps, use `docs/decision-maps/<stable-slug>.md`.

Search existing maps by canonical initiative ID before searching aliases and former names. When one map matches, use it. When several candidates plausibly match, show the candidate paths and initiative IDs, ask the user to choose one, and do not create or update a map until they do. Absence of a confident match permits a new map.

Reading and reporting a map are safe. Create or update a local map only when the user requested a durable map; re-read the live artifact immediately before writing. Do not send, publish, or change external systems without separate authority.

Keep four kinds of state distinct:

- a `decision` selects or rejects an option under named authority;
- a `sharp open question` has an answer that can resolve a named decision;
- `fog` is material uncertainty that is not yet sharp enough to answer;
- `frontier` is the nearest evidence-gathering or decision-unblocking work, not an implementation plan.

When evidence changes, retain the old evidence and decision history. Mark every dependent decision, question, fog item, and frontier entry visibly invalidated or needing review; replace none silently. Then refresh the frontier from the still-current dependencies.

## Handoff

If Compound Engineering is available, hand the map to `ce-brainstorm` while major forks or material fog remain. Hand it to `ce-plan` once the key decisions are resolved. Otherwise provide a portable handoff brief with the current direction, accepted and invalidated decisions, sharp open questions, material fog, and the next frontier.

## Done

The inspected map is recoverable in a new session: it identifies the initiative, current decision state and evidence, dependencies and out-of-scope boundary, visible invalidation history, and the next decision-unblocking frontier. Report the map path, whether it was read or changed, the routing result, and any ambiguity or missing evidence that prevents completion.
