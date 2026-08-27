---
name: x9-task-graph
description: Use when an approved, implementation-ready plan must become a dependency-aware, tracker-ready draft of vertical work items — «разбей утверждённый план на работы», «построй граф работ по готовому плану», "turn this approved plan into work items". Do not use for a raw idea, a draft or unapproved plan, product replanning, or implementation; route those inputs to planning such as `ce-plan`.
---

# Task graph

Turn an approved implementation plan into a complete, reviewable draft of connected vertical work items. This skill is model-invoked in Claude Code and Codex; its portable claim is structural Agent Skills compatibility only. Evidence tier: static.

## Accept only a settled plan

Read the supplied artifact completely before deriving work. Approval means an explicit marker in the artifact or the user's confirmation in the current thread. Accept `ce-unified-plan/v1` only when it is approved and its readiness is `implementation-ready`. Accept an equivalent plan only when it is approved and has a goal, requirements, decisions, implementation or work units, and verification.

Stop before decomposition when the input is unreadable, contradictory, partial, draft, or unapproved. Identify the exact missing, conflicting, or unapproved part and ask for the accepted version. A raw idea or request to choose product direction belongs to planning, not this skill.

Do not redesign the product, reopen accepted decisions, add requirements, invent implementation work, or implement the resulting items. Trace the approved source; an ambiguity that changes its meaning is a blocker rather than an invitation to replan.

## Derive the draft

Read [the work-item contract](references/work-item-contract.md) before deriving the graph. It owns work-item shape, vertical slicing, dependency/frontier semantics, tracker-ready representation, and the complete coverage matrix.

Use the plan's identifiers and wording where possible. Make dependencies only from accepted source constraints. A source-unit split or merge is allowed only when the coverage matrix explains why traceability remains complete.

Return the draft in chat by default. Read [the publication boundary](references/publication-boundary.md) only when the user asks to save locally or publish externally; it owns all local-write and external-mutation gates, correlation, preview, retry, and reconciliation rules.

## Done

For a valid source, completion is a chat draft that satisfies the work-item contract and whose coverage matrix accounts for every known requirement, decision, and source work unit. For refused input or gated mutation, completion is the named status and the exact missing authority, source evidence, or interface capability. Static validation does not prove live tracker publication or reconciliation.
