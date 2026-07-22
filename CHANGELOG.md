# Changelog

## Unreleased

### Highlights

- Tightened the README by folding validation and security proof into the contribution section instead of a separate internal-facing block.
- Restored the intended skill contracts for social research, authenticated personal browsing, cross-provider idea critique, cross-harness context files, subscription-aware Codex delegation, and packaging recurring workflows as skills.
- Replaced the generated-looking skill table with a problem-first guide and a human-readable catalog that explains the story and practical use of every skill.
- Added a batch-audit recipe that discovers project-owned skills from flexible paths, delegates bounded audits to fresh workers, preserves raw evidence per target, and requires orchestrator QA plus a consolidated table containing every retained Blocker, Important, and Minor finding.
- Hardened delegation temporary-file and opt-in telemetry handling; defined read-only/default and authorized context-file actions; added OKF dependency preflight and automatic semantic-repair timestamps; corrected single-target skill validation; and made Wildberries search breadth converge with explicit account actions and risk-based independent verification.

### Install / update

- Existing authenticated-browser users should add the privacy flags documented in `x9-browser-session` to their `chrome-devtools-mcp@latest` configuration, then restart Claude Code or Codex.

### Compatibility

- Added same-task changelog rules, release-time diff reconciliation, and a CI gate that catches release-relevant changes when `Unreleased` is empty.
- Defined deterministic `PATCH`, `MINOR`, `1.0.0`, and post-1.0 `MAJOR` selection rules for release preparation.
- Replaced stale-prone tool versions and verification dates in runtime guidance with live `--help`, documentation, schema, and session-metadata checks.

### Breaking changes

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
