# OKF v0.1 metadata contract

Each curated Markdown file begins with YAML frontmatter containing all five fields:

```yaml
---
type: Research Note
title: Display title
description: One line describing the document's current purpose
tags:
  - stable-topic
  - second-topic
timestamp: 2026-07-15T12:00:00+03:00
---
```

## Fields

- `type`: `Dossier` for a dossier README; otherwise one of `Research Note`, `Analysis`, `Plan`, `Playbook`, or `Reference` unless the repository defines an explicit extension.
- `title`: non-empty human display title.
- `description`: one non-empty line specific enough to distinguish the file from siblings.
- `tags`: 2–5 unique English kebab-case strings.
- `timestamp`: ISO 8601 with timezone. Preserve it for formatting-only normalization. When an existing header receives a repair that adds or changes the meaning of `type`, `title`, `description`, or `tags`, the migration script sets one operation timestamp automatically; the agent does not ask for timestamp permission file by file.

Unknown fields are preserved unless they conflict with the repository's OKF contract. Duplicate YAML keys, invalid types, and partial headers are errors.

## Default exclusions

Exclude generated or bulk material such as `raw/`, `transcripts/`, `summaries/`, `artifacts/`, `archive/`, dependencies, build outputs, hidden directories, and vendored content unless the user explicitly includes them.

## Preservation

For header insertion, the pre-existing body bytes are immutable. Preserve UTF-8 BOM presence and the original dominant line ending. Validation compares the post-edit body hash and byte metadata to a pre-edit inventory.
