# Maintain active OKF documents

Use this route only for documents created or substantively edited in the current task. Reading, link fixes, formatting cleanup, and unrelated repository work do not migrate metadata.

## Repository instructions

Inspect the applicable `AGENTS.md` OKF section once. If it pins an OKF version, copies field rules, or names the former `x9-okf-adapt` skill, use `x9-context-files-generator` to replace only that stale policy with a version-independent route to `x9-okf-docs`. Preserve repository-specific document scope, exclusions, navigation, and log conventions.

This is a one-time lazy repair performed on the first OKF write in that repository. A current version-independent OKF section stays untouched. If the companion skill is unavailable, do not improvise a broad rewrite; continue the document operation and report the repository policy as `DEGRADED`.

## Existing document

After the substantive body edit, update only the named documents:

```bash
python3 <skill-directory>/scripts/insert_frontmatter.py <repository-root> \
  --touch <path> [<path> ...] \
  --actor <actor>
```

The actor must be truthful: `<producer>/<version>`, `human:<id>`, or `process:<id>`. `--touch` upgrades legacy v0.1 metadata to the current v0.2 contract, refreshes native v0.2 provenance, and keeps legacy `timestamp` synchronized for older consumers. It does not scan or rewrite neighboring documents.

Use `--dry-run` for a requested preview. Use `--drop-legacy-timestamp` only when compatibility is explicitly no longer needed. An explicitly named `README.md` is allowed; reserved files and repository instruction files are rejected.

## New document

Read [okf-format.md](okf-format.md), derive metadata from the complete document, and use the manifest route in [adapt-repair.md](adapt-repair.md). Do not fabricate `generated`, verification, lifecycle, or source claims.

## Completion

Review the actual diff. Only the named documents and, when stale, the applicable `AGENTS.md` OKF section may change. The script must succeed without body, BOM, or line-ending drift.
