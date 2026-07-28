---
name: x9-context-files-generator
description: Use when creating, auditing, or updating repository-level AGENTS.md, CLAUDE.md, or README.md — «создай AGENTS.md», «обнови README», «настрой контекст репозитория», "generate repository context files". Do not use for global personal instructions, skills, or ordinary documentation unrelated to onboarding agents or humans.
compatibility: Full creation, audit, or update of agent-facing repository instructions requires x9-agent-instructions. README-only work does not.
---

# Repository context files

Create concise, evidence-backed onboarding files for two audiences: agents (`AGENTS.md`/`CLAUDE.md`) and humans (`README.md`). Existing files are user-owned inputs, not blank templates.

For every Create, Audit, or Update that touches agent-facing instructional prose in `AGENTS.md` or an explicitly exceptional `CLAUDE.md`, load and apply `x9-agent-instructions` before writing or judging that prose. It is a subordinate instruction-quality rubric, not the primary context-file workflow, and owns language, prescription, duplication, artifact references, and what earns a line. This skill remains the owner of repository evidence, audience selection, canonical files, merge and preservation behavior, `AGENTS.md`/`CLAUDE.md` normalization, and `README.md`.

Do not apply the subordinate rubric to `README.md` or to a `CLAUDE.md` that contains only the canonical `@AGENTS.md` import. Fold its findings into this workflow's single report and approval gate rather than producing a second handoff. If `x9-agent-instructions` is unavailable, continue the remaining repository and structural checks, record the instruction rubric as `degraded`, and do not claim a complete or clean agent-file result. README-only work records it as `not applicable`.

## Select the action

- **Create or update:** an explicit request to create, update, fix, or rewrite a context file authorizes the requested in-scope edits; do not ask for the same permission again.
- **Audit:** an explicit audit/check request is read-only. Report findings and proposed changes, then ask once whether to apply them.
- **Bare skill invocation:** inspect the current repository read-only by default. If changes would help, show the proposal and ask once before editing.

Infer the action from the whole request, not only trigger words. When an authorized edit reveals an additional normalization outside the requested change, ask once before applying that extra change.

## Workflow

1. Read current repository instructions and README completely enough to preserve non-inferable rules. Inspect actual commands, manifests, CI, and representative code before writing.
2. Classify content by audience:
   - Agent file: commands, dangerous gotchas, local constraints, non-inferable conventions, and verification contracts.
   - README: purpose, setup, normal usage, and links to deeper material.
3. Keep one canonical owner for each fact. A short audience-specific summary is allowed when it changes behavior; link to the owner instead of copying full detail.
4. Make root `AGENTS.md` the single canonical local instruction file and root `CLAUDE.md` exactly `@AGENTS.md` plus a final newline, unless the repository or user declares an exception. Put every new local rule in `AGENTS.md`. Before normalizing an existing `CLAUDE.md`, merge its unique rules into `AGENTS.md`; never discard them silently or preserve a duplicate copy by default. Apply this normalization immediately when it was explicitly requested or already required by repository policy; otherwise propose it and ask once before editing.
5. Treat an existing `AGENTS.md`, `CLAUDE.md`, or `README.md` as merge-only unless the user explicitly requests replacement. Show a diff for substantive rewrites.
6. For agent files, remove content that is cheap to reconstruct only when its absence would not change the reader's next decision or action; use the detailed test in [references/agents-md.md](references/agents-md.md). Include architecture only when the rationale or boundary cannot be recovered cheaply from code and materially affects decisions. Avoid generated file trees and generic overviews.
7. Use English for machine-facing instructions by default; follow repository/user language when human maintenance or domain literals make that clearer.
8. Run commands you present only when they are safe, local, and within the requested repository scope. Read-only inspection and ordinary local validation are allowed by default. Destructive, external, costly, deployment, migration, production-data, account-mutating, or credential-changing commands require explicit user authority; otherwise preserve the command and label it unverified with the reason.

Read [references/agents-md.md](references/agents-md.md) when editing agent files, [references/readme.md](references/readme.md) for README work, and [references/research-basis.md](references/research-basis.md) when judging how much inferred architecture belongs in context.

## Boundaries

- Global `~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md` belong to `x9-agent-instructions`.
- Skill folders belong to `x9-skill-creator`.
- Do not put personal absolute paths such as `/Users/<name>/...` or `/home/<name>/...` in committed files. Prefer repository-relative paths or neutral placeholders; keep a machine-bound path only when the repository genuinely depends on that machine and the user explicitly wants it documented.
- Do not overwrite existing instructions by position from a stale read; re-read immediately before applying a patch.

## Done

- Existing non-inferable rules are preserved or intentionally changed with user authority.
- When canonical-file normalization was authorized and no exception applies, `CLAUDE.md` contains only `@AGENTS.md` and all local instructions are owned by `AGENTS.md`.
- Commands and paths trace to the current repository.
- Agent and human files contain only behavior-changing audience-specific material.
- The instruction rubric is reported as `applied`, `not applicable`, or `degraded`; a complete or clean agent-file result requires `applied`.
- A fresh-context reader can start the project without inventing a command.
