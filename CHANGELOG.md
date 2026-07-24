# Changelog

## Unreleased

### Highlights

### Install / update

### Compatibility

### Breaking changes

## 1.3.0 - 2026-07-24

### Highlights

- Clarified browser routing for both runtimes: local web development and explicit in-app requests use the runtime's in-app browser, while every other browser task uses the runtime-specific default — its Edge extension in Codex and `chrome-devtools` MCP in Claude Code — with `agent-edge` reserved as an unattended fallback.
- Expanded the `x9-browser-session` skill with sticky explicit-surface selection, shared Edge focus-safety and task-tab isolation rules, and defined runtime-specific fallback chains.
- Synchronized the sanitized global instruction examples with the runtime-specific routes and their explicit in-app browser boundaries.

### Install / update

- Existing users should keep the Edge extension and local CDP endpoint configured as described in the `x9-browser-session` setup guide. No migration steps are required.

### Compatibility

- Local web development and explicit in-app or built-in browser requests continue to use the runtime's in-app browser, and that explicit choice stays sticky through connection failures.
- Other browser work now follows a defined runtime-specific default and fallback chain instead of a generic runtime selection. The `agent-edge` route remains an unattended fallback for periods when the user is not working in Edge.

### Breaking changes

- None.

## 1.2.0 - 2026-07-23

### Highlights

- Added explicit research delivery routing: plain requests stay in chat, save or folder requests persist Markdown, and HTML requests add a same-basename reader presentation without replacing the evidence-oriented work file.
- Added OKF-frontmatter discovery for existing subject areas and research files, including automatic synchronization of an existing same-basename HTML presentation when the underlying research is updated.
- Added a reusable responsive light editorial theme without imposing one report layout, plus a Russian HTML editing pipeline with `humanizer-ru` and a post-edit fact and citation check.
- Made one-off agent briefs follow the user's language by default while preserving exact technical literals and documented target-language constraints.

### Install / update

- Existing users can update through their current Agent Skills, Claude Code, or Codex installation route without migration steps.

### Compatibility

- Existing plain research requests remain chat-only. Existing saved research remains Markdown-first; a missing HTML file is created only when HTML output is explicit, while an already paired HTML file follows later research updates automatically.
- Existing skill names and installation routes are unchanged. Standing machine-facing policy remains English by default; only one-off brief language selection was clarified.

### Breaking changes

- None.

## 1.1.0 - 2026-07-23

### Highlights

- Made idea-critique synthesis preserve every verdict-changing finding while turning upheld issues into a complete, dependency-aware revision agenda.
- Refined loop engineering around the smallest sufficient topology, hierarchical ownership, proportional contracts and evidence, durable resumption, lifecycle handling, and correctly classified retry budgets.
- Made the published global-instruction examples keep Russian as the carrier language of technical explanations while separating exact English identifiers and reference names from narrative prose.

### Install / update

- Existing users can update through their current Agent Skills, Claude Code, or Codex installation route without migration steps.

### Compatibility

- Kept existing skill names and installation routes unchanged while expanding the public guidance and output contracts for idea critique and loop engineering.

### Breaking changes

- None.

## 1.0.0 - 2026-07-22

### Highlights

- Reworked the public guide into a problem-first catalog that explains the practical role of every skill and keeps contribution, validation, and security guidance concise.
- Restored the intended contracts for social research, authenticated personal browsing, cross-provider idea critique, cross-harness context files, subscription-aware Codex delegation, and packaging recurring workflows as skills.
- Added a batch-audit workflow that discovers project-owned skills, delegates bounded fresh-context reviews, preserves raw evidence, and consolidates every retained finding through orchestrator QA.
- Expanded loop engineering with topology guidance for choosing, composing, and validating reliable multi-agent workflows.
- Hardened temporary-file and opt-in telemetry handling, context-file authority boundaries, OKF dependency checks and semantic metadata repair, single-target validation, and Wildberries search verification.

### Install / update

- Existing authenticated-browser users should add the privacy flags documented in `x9-browser-session` to their `chrome-devtools-mcp@latest` configuration, then restart Claude Code or Codex.
- Other users can update through their existing Agent Skills, Claude Code, or Codex installation route without migration steps.

### Compatibility

- Declared the public skill names, installation and update routes, and supported behavior stable enough for normal compatibility guarantees starting with 1.0.0.
- Added same-task changelog rules, release-time diff reconciliation, and a CI gate that catches release-relevant changes when `Unreleased` is empty.
- Defined deterministic release-version selection rules and replaced stale runtime facts with live `--help`, documentation, schema, and session-metadata checks.

### Breaking changes

- None.

## 0.2.0 - 2026-07-22

### Highlights

- Rebuilt the public presentation around a clear English landing page, a matching Russian version, a compact skill catalog, and a distinct visual identity.
- Added contributor, security, conduct, issue, and pull request guidance for a more predictable open-source workflow.

### Install / update

- Simplified the primary installation path to the interactive `npx skills add xonika9/agent-skills` flow while keeping native Claude Code and Codex plugin alternatives.
- Added a maintainer recording plan for a short, real product demonstration.

### Compatibility

- Clarified that the package follows the open Agent Skills format, targets Claude Code and Codex, and documents runtime-specific exceptions and companion skills.
- Added validated Codex plugin identity assets and a project brand color.
- Made the Wildberries workflow execute entirely in the current Claude Code or Codex runtime instead of delegating between them.
- Restored a portable authenticated Chromium/CDP contract while retaining the verified Microsoft Edge adapter.
- Made the global-instructions validator independent of the caller's working directory.
- Published sanitized Claude Code and Codex runtime adapters alongside the shared global-instructions core, without machine-specific installation paths.

### Breaking changes

- None.

## 0.1.0 - 2026-07-22

- Первый публичный выпуск скиллов `x9-*` для AI-агентов с поддержкой Agent Skills.
- Установка всего набора как плагина для Claude Code или Codex.
- README с проблемами, которые решают скиллы, сравнением способов установки и ссылкой на Telegram.
- Пример общего `SHARED PERSONAL CORE` для глобальных `AGENTS.md` и `CLAUDE.md`.
- Репозиторные инструкции для поддержки README, changelog, plugin manifests и release-тегов.
- Автоматический GitHub Release после успешной проверки новой версии в `main`.
- Инструкция по работе с отдельным профилем Edge через CDP и запасной маршрут `agent-edge`.
- Установка и обновление через CLI `skills`.
