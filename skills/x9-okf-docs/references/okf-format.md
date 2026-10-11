# x9 OKF metadata contract

The contract follows OKF v0.2, whose canonical specification is `SPEC.md` in [GoogleCloudPlatform/open-knowledge-format](https://github.com/GoogleCloudPlatform/open-knowledge-format). OKF requires only `type`; every other field is optional. Before changing this contract or the scripts, compare them with the current specification.

## Fields

A document is a UTF-8 Markdown file whose YAML header holds all four fields. Every one is required, so no agent has to judge which to skip.

| Field | Rule |
|---|---|
| `type` | The kind of document in a few words, such as `Тема`, `Research Note`, or `Playbook`; use the values the repository's block lists. |
| `title` | The human name, even when the file name looks descriptive. |
| `description` | One line on what the document holds and what it is for, so an agent can decide whether to open it. Keep it distinct from neighbouring documents. |
| `tags` | One to five unique English kebab-case tags for subjects that cross folders, such as `health` or `video-ideas`. |

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

## Repository rules

The Local part of a repository's block outranks this contract. It may keep a retired OKF field with its OKF meaning, such as `status` for `draft`, `stable`, and `deprecated` documents, and it may name the repository's own header fields, which this skill never touches. A repository's own field never reuses an OKF field name. Files whose header another tool owns under OKF names, such as Compound Engineering plans with `type: feat`, are excluded from scope in `.x9-okf.json` and named in Local.

## Files that are not documents

- `index.md` and `log.md` are reserved by OKF and have no header; only a bundle-root `index.md` may carry `okf_version`. A `log.md` uses `## YYYY-MM-DD` headings, newest first.
- `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md` are repository instructions and never get a header.
- `README.md` is a document only where the repository's scope includes it.

## Scope

Hidden folders, links, and the folders `raw`, `transcripts`, `summaries`, `artifacts`, `archive`, `node_modules`, `dist`, `build`, and `vendor` are outside scope. A repository sets its scope in `.x9-okf.json` at its root, which every script reads:

```json
{"include": ["docs", "research"], "exclude": ["Входящее", "Система/Шаблоны"], "include_readme": true}
```

- `include` limits documents to these folders, as paths from the root, including a listed hidden folder; without it the whole root is in scope.
- `exclude` removes folders and files: an entry without `/` excludes every folder or file of that name, such as `PLAN.md`; an entry with `/` is a path from the root.
- `include_readme` makes `README.md` files documents; they are excluded by default.

Case and Unicode form are ignored when names are compared.
