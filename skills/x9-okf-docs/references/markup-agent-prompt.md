# Metadata proposal brief

Use this brief for a read-only subagent that proposes metadata. It never edits files.

## Input

- The explicit list of documents.
- [The contract](okf-format.md) and the `type` values the repository lists.
- The complete text of each document when practical; otherwise its headings and enough of the body for an accurate description.
- Each document's existing header.

## Output

One JSON object per document:

```json
{
  "path": "docs/topic.md",
  "type": "Research Note",
  "title": "Topic",
  "description": "What the document holds and what it is for",
  "tags": ["topic", "research"],
  "confidence": "high",
  "basis": ["heading", "section name"]
}
```

## Rules

- Use only the supplied content; report insufficient context instead of guessing.
- Copy existing valid values unchanged; propose only missing or invalid ones.
- Propose all four of `type`, `title`, `description`, and `tags`, and nothing else.
- Keep each description one line and distinct from its neighbours.
- Do not emit shell commands, patches, or rewritten bodies.
