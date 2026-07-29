---
name: x9-okf-docs
description: Use when creating or substantively editing documentation in an OKF repository, adopting OKF for Markdown, repairing or migrating legacy metadata, or when repository instructions still name the former x9-okf-adapt skill — «создай OKF-документ», «обнови этот документ», «адаптируй папку под OKF», "migrate docs to OKF". Do not use for reading documents, ordinary Markdown cleanup, rewriting body prose without an OKF requirement, or treating repository instruction files as OKF documents.
---

# OKF documentation

Own the current OKF metadata contract so repositories do not copy version-specific fields into `AGENTS.md`. Preserve document bodies, operate only on explicit scope, and never invent provenance or trust signals.

## Choose one route

- For a new document or a substantive edit, read [maintain.md](references/maintain.md).
- For initial adoption or metadata repair, read [adapt-repair.md](references/adapt-repair.md).
- For an audit, bulk legacy migration, or bundle version declaration, read [migration.md](references/migration.md).
- For field semantics or authoring new frontmatter, read [okf-format.md](references/okf-format.md).
- Use [markup-agent-prompt.md](references/markup-agent-prompt.md) only for a read-only metadata proposal.

Do not load unrelated routes. `index.md` and `log.md` are reserved OKF files; `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md` are repository instructions, not OKF concepts.

## Runtime

The package-owned `skills/x9-okf-docs` directory is canonical for Claude Code and Codex. Its scripts require Python 3 and Ruby with Psych. Resolve script paths from this loaded skill directory.

## Completion

The selected route must leave only the intended files changed, preserve body bytes, BOM, and line endings where metadata tooling runs, and produce passing route-specific validation. Report any unavailable dependency or repository-policy update as `DEGRADED`.
