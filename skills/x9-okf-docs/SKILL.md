---
name: x9-okf-docs
description: Use when writing or updating OKF metadata for Markdown documents — creating a document in a repository or vault whose instructions use OKF, adopting OKF for a folder, checking OKF metadata, or removing retired OKF fields — «добавь OKF-метаданные», «адаптируй папку под OKF», «проверь OKF», "migrate docs to OKF". Do not use for reading documents, ordinary Markdown cleanup, prose rewrites, repositories whose instructions say they do not use OKF, or repository instruction files.
---

# OKF documentation

Own the x9 OKF metadata contract: each document's header carries enough for an agent to decide whether to open it. Repositories point to this skill instead of copying field rules into their instructions. Preserve document bodies and act only on the documents in scope.

Read [the contract](references/okf-format.md) before writing any metadata.

## Choose the route

- Create a document, edit one, or repair stale repository instructions: [maintain](references/maintain.md).
- Adopt a folder, check it, or remove retired fields: [adapt](references/adapt.md).
- Brief a read-only subagent that proposes metadata: [proposal brief](references/markup-agent-prompt.md).

## Runtime

The package-owned `skills/x9-okf-docs` directory is canonical. The skill is model-invoked in OpenCode, Claude Code, and Codex. Writing a header by hand needs no tools. The scripts need Python 3.9 or newer and Ruby with Psych, which stock macOS provides; resolve their paths from this loaded skill directory and run `scripts/check_dependencies.py` before the first script in a session. The [onboarding declaration](references/onboarding.json) lists these prerequisites.

## Completion

Only the intended files changed, bodies kept their bytes, BOM, and line endings where a script wrote, and the validator passes for the documents in scope. When a needed script cannot run, report the metadata as unchecked rather than skipping silently.
