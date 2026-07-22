---
name: x9-agent-instructions
description: Use when drafting a one-off prompt/task brief for another agent without executing it, or when creating, auditing, or editing global personal agent instructions — «напиши промпт для агента», «поправь глобальные правила», «обнови CLAUDE.md/AGENTS.md», "write an agent prompt", "edit my global instructions". Do not use for repository onboarding files (x9-context-files-generator), skill authoring (x9-skill-creator), ordinary prose, or actually delegating a task to Codex.
---

# Agent instructions

Own global behavioral policy in `~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`, and bounded briefs handed to another agent. Write machine-facing instructions in English; preserve literal user phrases in their original language.

## Classify before editing

Place each rule in the narrowest owner that can reliably enforce it:

- **Stable personal policy:** authority, preservation, uncertainty, completion, communication → mirrored shared core in both global files.
- **Runtime adapter:** current models, tools, CLI flags, browser and subagent schemas → a runtime-specific global section or a user-owned adapter outside the reusable skill.
- **Repository context:** commands and local constraints → repository `AGENTS.md`/`CLAUDE.md`, owned by `x9-context-files-generator`.
- **Domain behavior:** situation-specific method → the relevant skill.
- **Operational state:** rankings, measurements, experiments, freshness dates → a dated state/log file, not standing policy.
- **One-off task:** goal, constraints, evidence, authority, deliverable, and observable completion bar → the task brief.

System and developer instructions remain higher authority than user, repository, or skill instructions. Never write a lower layer as though it can override a higher one.

## Editing contract

1. Read both global files and any runtime adapter affected by the change.
2. Identify the canonical owner. Allow a short audience-specific summary elsewhere only when it changes behavior; point back to the owner.
3. Preserve unrelated user content. Replace only the intended bounded section when markers exist.
4. Keep the shared block between `<!-- BEGIN SHARED PERSONAL CORE -->` and `<!-- END SHARED PERSONAL CORE -->` byte-identical in both global files.
5. State hard negative boundaries explicitly when safety or preservation depends on them. Prefer positive target behavior for ordinary guidance.
6. Specify process only when the path is part of correctness: dependencies, approval gates, deterministic transformations, state/checkpoints, or known failure modes.
7. Resolve the installed `x9-agent-instructions` directory from the loaded `SKILL.md`, then run `python3 <skill-directory>/scripts/check_globals.py`. Do not resolve the script from the caller's current working directory. Exercise the behavior scenarios below; a prose reread alone is not validation.

## Behavior scenarios

- Answer/review request → inspect and report; no edits.
- Explicit build/fix request → safe in-scope local edits and tests proceed; external, destructive, costly, or expanded actions require confirmation.
- Required tool fails → report the failure; no from-memory substitution.
- Runtime fact changes → update one adapter and its freshness marker, not every skill.
- Shared policy changes → both global copies match; runtime-specific sections may differ deliberately.
- One-off brief has a load-bearing ambiguity → ask one question; otherwise proceed with a stated assumption.

## Done

- The rule has one canonical owner and no accidental contradiction.
- Shared global policy passes `python3 <skill-directory>/scripts/check_globals.py` from an unrelated working directory.
- At least one positive and one boundary scenario were checked in a fresh context for substantive changes.
- The handoff names changed files and validation performed.
