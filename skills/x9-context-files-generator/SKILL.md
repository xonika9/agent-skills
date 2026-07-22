---
name: x9-context-files-generator
description: Use when creating, auditing, or updating repository-level AGENTS.md, CLAUDE.md, or README.md — «создай AGENTS.md», «обнови README», «настрой контекст репозитория», "generate repository context files". Do not use for global personal instructions, skills, or ordinary documentation unrelated to onboarding agents or humans.
---

# Repository context files

Create concise, evidence-backed onboarding files for two audiences: agents (`AGENTS.md`/`CLAUDE.md`) and humans (`README.md`). Existing files are user-owned inputs, not blank templates.

## Workflow

1. Read current repository instructions and README completely enough to preserve non-inferable rules. Inspect actual commands, manifests, CI, and representative code before writing.
2. Classify content by audience:
   - Agent file: commands, dangerous gotchas, local constraints, non-inferable conventions, and verification contracts.
   - README: purpose, setup, normal usage, and links to deeper material.
3. Keep one canonical owner for each fact. A short audience-specific summary is allowed when it changes behavior; link to the owner instead of copying full detail.
4. In the user's personal repositories, make root `AGENTS.md` the single canonical local instruction file and root `CLAUDE.md` exactly `@AGENTS.md` plus a final newline, unless the user explicitly declares an exception. Put every new local rule in `AGENTS.md`. Before normalizing an existing `CLAUDE.md`, merge its unique rules into `AGENTS.md`; never discard them silently or preserve a duplicate copy by default.
5. Treat an existing `AGENTS.md`, `CLAUDE.md`, or `README.md` as merge-only unless the user explicitly requests replacement. Show a diff for substantive rewrites.
6. Include architecture only when the rationale or boundary cannot be recovered cheaply from code and materially affects decisions. Avoid generated file trees and generic overviews.
7. Use English for machine-facing instructions by default; follow repository/user language when human maintenance or domain literals make that clearer.
8. Run every command you present when safe and available. Label unverified commands rather than guessing.

Read [references/agents-md.md](references/agents-md.md) when editing agent files, [references/readme.md](references/readme.md) for README work, and [references/research-basis.md](references/research-basis.md) when judging how much inferred architecture belongs in context.

## Boundaries

- Global `~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md` belong to `x9-agent-instructions`.
- Skill folders belong to `x9-skill-creator`.
- Do not put personal absolute paths such as `/Users/<name>/...` or `/home/<name>/...` in committed files. Prefer repository-relative paths or neutral placeholders; keep a machine-bound path only when the repository genuinely depends on that machine and the user explicitly wants it documented.
- Do not overwrite existing instructions by position from a stale read; re-read immediately before applying a patch.

## Done

- Existing non-inferable rules are preserved or intentionally changed with user authority.
- In a personal repository without an explicit exception, `CLAUDE.md` contains only `@AGENTS.md` and all local instructions are owned by `AGENTS.md`.
- Commands and paths trace to the current repository.
- Agent and human files contain only behavior-changing audience-specific material.
- A fresh-context reader can start the project without inventing a command.
