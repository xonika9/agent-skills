---
name: x9-web-stack
description: Use when starting a TypeScript web application on the x9 stack (Bun, React, Hono, PostgreSQL), auditing an existing web project's stack, structure, and development rules — on this stack or another — or writing durable development rules into a project's AGENTS.md — «создай проект на нашем стеке», «проверь стек проекта», «добавь правила разработки в AGENTS.md», "bootstrap a web app", "audit this project's stack". Not for a dedicated security review (x9-appsec), comparing architecture directions (x9-architecture-scout), or general AGENTS.md and README upkeep (x9-context-files-generator).
compatibility: Bootstrap requires python3, bun, and git; Docker for the dev database. Audit and the rules block need only read access to the project.
---

# Web stack

This package-owned skill is model-invoked in Claude Code and Codex. Its portable claim is structural Agent Skills compatibility only.

It owns a vetted template for TypeScript web applications — the stack, the project structure, and the development rules — and three ways to apply it. The template lives in this skill: [stack and structure](references/stack.md), [rules](references/rules.md), [library notes](references/library-notes.md), and the verified project scaffold in `assets/project`.

## Select the action

- **Bootstrap:** a new project on this stack. The request authorizes creating the project in an empty target directory, installing packages from the public registry, starting local containers, and running local checks. Follow [bootstrap](references/bootstrap.md).
- **Audit:** an existing project, on this stack or another. The first pass is read-only: a ranked report per [audit](references/audit.md). Apply only findings the user selects; an explicit request to fix already selects them.
- **Rules block:** write or refresh the development-rules block in the project's `AGENTS.md` per [agents-block](references/agents-block.md). A request for it authorizes editing the block. Bootstrap always writes it; an audit report offers it.

Infer the action from the whole request. A request to "set up" or "improve" an existing repository is an audit, not a bootstrap.

## Freshness

Versions, action tags, and library behaviour change faster than this skill. Install current releases and discover the current Bun version live; never copy a version from these files.

## Boundaries

- Never overwrite a non-empty directory, migrate a framework, language, or database, run migrations against non-local databases, deploy, commit, push, or create remote repositories unless the user asked for that exact action.
- Preserve user changes; read files immediately before editing them.
- Keep secrets out of reports and committed files; `.env` stays untracked.

## Done

- Bootstrap: the done condition in [bootstrap](references/bootstrap.md#done) holds and the report names what was not verified.
- Audit: the report follows [audit](references/audit.md#report); after fixes, each applied finding has check output.
- Rules block: the done condition in [agents-block](references/agents-block.md#done) holds.

The [onboarding declaration](references/onboarding.json) lists external prerequisites.
