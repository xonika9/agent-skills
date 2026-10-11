# x9 OKF metadata contract

The contract follows OKF v0.2, whose canonical specification is `SPEC.md` in [GoogleCloudPlatform/open-knowledge-format](https://github.com/GoogleCloudPlatform/open-knowledge-format). OKF requires only `type`; every other field is optional. Before changing this contract or the scripts, compare them with the current specification.

## Fields

A document is a UTF-8 Markdown file whose YAML header holds:

| Field | Rule |
|---|---|
| `type` | Required. The kind of document in a few words, such as `Тема`, `Research Note`, or `Playbook`; use the values the repository or its area lists. |
| `description` | Required. One line on what the document holds and what it is for, so an agent can decide whether to open it. Keep it distinct from neighbouring documents. |
| `title` | Recommended. The human name; include it whenever the file name does not say what the document is, as with every `README.md`. |
| `tags` | Recommended. One to five unique English kebab-case tags for subjects that cross folders, such as `health` or `video-ideas`. |

```yaml
---
type: "Тема"
title: "Обследование 2026"
description: "План и результаты осеннего обследования: анализы, врачи, выводы"
tags: ["health", "checkup"]
---
```

Write string values in double quotes: an unquoted value containing `:` breaks some YAML readers.

Write no other OKF field. `generated`, `verified`, `status`, `stale_after`, `sources`, `usage_window`, `resource`, `timestamp`, and the computation fields are not part of this contract. A document's existing fields, including a repository's own such as `state`, stay untouched unless the user asks to remove them.

## Files that are not documents

- `index.md` and `log.md` are reserved by OKF and have no header; only a bundle-root `index.md` may carry `okf_version`. A `log.md` uses `## YYYY-MM-DD` headings, newest first.
- `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md` are repository instructions and never get a header.
- `README.md` is a document only where the repository's scope includes it.

## Scope

Hidden folders, links, and the folders `raw`, `transcripts`, `summaries`, `artifacts`, `archive`, `node_modules`, `dist`, `build`, and `vendor` are outside scope. A repository extends this in `.x9-okf.json` at its root, which every script reads:

```json
{"exclude": ["Входящее", "Архив", "memory", "Система/Шаблоны"], "include_readme": true}
```

An entry without `/` excludes every folder of that name; an entry with `/` is a path from the root and excludes that folder only. Case and Unicode form are ignored when names are compared.
