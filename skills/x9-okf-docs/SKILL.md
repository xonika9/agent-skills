---
name: x9-okf-docs
description: Use when writing or updating OKF metadata for Markdown documents — creating or working on a document in a repository or vault whose instructions use OKF, adopting OKF for a folder, checking OKF metadata, removing retired OKF fields, or putting the OKF block into a repository's AGENTS.md — «добавь OKF-метаданные», «адаптируй папку под OKF», «проверь OKF», «обнови блок OKF в AGENTS», "migrate docs to OKF". Do not use for reading documents, ordinary Markdown cleanup, prose rewrites, repositories whose instructions say they do not use OKF, or giving repository instruction files a header.
---

# OKF documentation

Own the x9 OKF metadata contract: each document's header carries enough for an agent to decide whether to open it. Own also the block between `<!-- x9-okf-docs:start -->` and `<!-- x9-okf-docs:end -->` in a repository's `AGENTS.md`, written from [the block template](references/agents-block.md), so every repository states the same rules in the same words. Preserve document bodies and act only on the documents in scope.

Read [the contract](references/okf-format.md) before writing any metadata.

## Choose the route

- Create a document, work on one, or bring the repository's `AGENTS.md` block up to date: [maintain](references/maintain.md).
- Adopt a folder, check it, or remove retired fields: [adapt](references/adapt.md).
- Brief a read-only subagent that proposes metadata: [proposal brief](references/markup-agent-prompt.md).

## Runtime

The package-owned `skills/x9-okf-docs` directory is canonical. Writing a header by hand needs no tools. The scripts need Python 3.9 or newer and Ruby with Psych, which stock macOS provides; resolve their paths from this loaded skill directory and run `scripts/check_dependencies.py` before the first script in a session. The [onboarding declaration](references/onboarding.json) lists these prerequisites.

## Completion

Only the intended files changed, bodies kept their bytes, BOM, and line endings where a script wrote, and the validator passes for the documents in scope. When a needed script cannot run, report the metadata as unchecked rather than skipping silently.
