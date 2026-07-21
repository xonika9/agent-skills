# Metadata proposal brief

Use this brief for a read-only metadata proposer. The proposer does not edit documents.

## Input

- Explicit file list.
- Repository OKF type/tag conventions.
- Complete document text when practical; otherwise headings plus enough representative body context to support an accurate description.

## Output

Return one JSON object per file:

```json
{
  "path": "docs/topic.md",
  "type": "Research Note",
  "title": "Topic",
  "description": "Current scope of the topic note",
  "tags": ["topic", "research"],
  "timestamp": "2026-07-15T12:00:00+03:00",
  "confidence": "high",
  "basis": ["heading", "section name"]
}
```

## Rules

- Use only supplied content; report insufficient context instead of inventing metadata.
- Keep descriptions unique and single-line.
- Preserve existing valid custom metadata in a separate `preserve` object when relevant.
- Do not emit shell commands, patches, or rewritten document bodies.
- The orchestrator validates proposals and passes an approved manifest to `scripts/insert_frontmatter.py`.

If an agent or script touches an out-of-scope file, stop and inspect the actual diff. Restore only the specific generated change using a known pre-edit snapshot or inverse patch; never discard the working tree with `git checkout` or reset commands.
