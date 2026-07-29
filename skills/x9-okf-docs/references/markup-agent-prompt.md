# Metadata proposal brief

Use this brief for a read-only metadata proposer. The proposer never edits documents.

## Input

- Explicit concept file list; exclude reserved `index.md` and `log.md`.
- Target OKF version and either the official or curated profile.
- Repository type/tag conventions, clearly labeled as local profile rules.
- Pre-edit inventory, including `suggested_generated_at` and existing frontmatter.
- Complete document text when practical; otherwise headings plus enough representative context for an accurate description.
- A truthful actor supplied by the caller when `generated` will be created or updated.

## Output

Return one JSON object per file:

```json
{
  "path": "docs/topic.md",
  "type": "Research Note",
  "title": "Topic",
  "description": "Current scope of the topic note",
  "tags": ["topic", "research"],
  "confidence": "high",
  "basis": ["heading", "section name"]
}
```

The deterministic writer adds `generated` from the explicit `--actor` and inventory timestamp. A proposal may include optional v0.2 fields only when supplied evidence supports them.

## Rules

- Use only supplied content; report insufficient context instead of inventing metadata.
- Copy existing valid semantic fields unchanged. Fill only missing or invalid fields unless replacement is authorized.
- Accept unknown `type` values under official OKF conformance; apply a catalog only when the repository declares a local profile.
- Never invent `generated.by`, `verified`, `status`, `stale_after`, sources, or credibility signals.
- Keep descriptions unique and single-line only under the curated profile.
- Preserve existing custom metadata through the deterministic writer.
- Do not emit shell commands, patches, or rewritten document bodies.

If an agent or script touches an out-of-scope file, stop and inspect the actual diff. Restore only the specific generated change from a known snapshot or inverse patch; never discard the working tree with destructive Git commands.
