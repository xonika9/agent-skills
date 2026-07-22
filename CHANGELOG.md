# Changelog

## Unreleased

### Highlights

### Install / update

### Compatibility

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
- Added same-task changelog rules, release-time diff reconciliation, and a CI gate that catches release-relevant changes when `Unreleased` is empty.

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
