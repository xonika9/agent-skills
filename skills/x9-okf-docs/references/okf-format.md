# OKF v0.2 metadata contracts

## Official conformance

A concept document is a UTF-8 Markdown file with YAML frontmatter. The only always-required field is:

```yaml
---
type: Research Note
---
```

`title`, `description`, `resource`, `tags`, and the provenance, trust, lifecycle, and computation families are optional. Unknown types and extension fields are valid and must survive round-tripping.

`index.md` and `log.md` are reserved files, not concepts. Nested index files and log files have no frontmatter. A bundle-root `index.md` may contain only:

```yaml
---
okf_version: "0.2"
---
```

## x9 curated profile

Newly adapted curated documents use a richer profile:

```yaml
---
type: Research Note
title: Display title
description: One line describing the document's current purpose
tags: [stable-topic, second-topic]
generated: {by: x9-okf-docs/<version>, at: "2026-07-15T12:00:00+03:00"}
---
```

- `title` and `description` are non-empty; `description` is one line and unique within the selected curated scope.
- `tags` contains 2–5 unique English kebab-case strings.
- `generated.by` truthfully identifies the producer, person, or process. Never infer it from Git authorship.
- `generated.at` is an ISO 8601 datetime with timezone marking the last meaningful change.
- A local type catalog is an optional profile rule, never an OKF conformance rule.

## Optional v0.2 families

- `sources`: every entry has `resource`; optional `id` values are unique.
- `verified`: one event or a list of events, each with truthful `by` and timezone-aware `at`.
- `status`: `draft`, `stable`, or `deprecated`; absence means `stable`.
- `stale_after`: an absolute ISO 8601 datetime with an explicit UTC offset. Date-only legacy values are invalid under OKF v0.2 and require an explicitly chosen migration instant.
- `sources[].last_modified`: an ISO 8601 datetime with an explicit UTC offset when present.
- `Attested Computation`: requires `runtime`; its other computation fields follow the official specification.

Absence is preferable to invented provenance, verification, freshness, or lifecycle data.

## v0.1 compatibility

- A legacy `timestamp` remains readable when `generated` is absent.
- Metadata migration may copy `timestamp` to `generated.at` only when a truthful `generated.by` is supplied.
- Keep `timestamp` during a compatibility window unless its removal is explicitly requested.
- Legacy `# Citations` may remain in the body. Moving checked resources into `sources` can preserve body bytes, but converting claims to keyed footnotes changes the body and is outside the default workflow.

For normal substantive edits, `--touch` updates only explicitly named documents. It sets `generated` to the supplied actor and operation time and synchronizes an existing `timestamp` for legacy consumers. Reading a file, editing another file, or updating repository instructions never triggers a document migration.

## Selection and preservation

Default exclusions cover generated or bulk material such as `raw/`, `transcripts/`, `summaries/`, `artifacts/`, `archive/`, dependencies, build outputs, hidden directories, and vendored content. These are x9 scope rules, not OKF rules.

For frontmatter insertion and migration, the pre-existing body bytes are immutable. Preserve UTF-8 BOM presence and original line endings; validate them against the pre-edit inventory.
