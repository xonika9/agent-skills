---
name: x9-okf-adapt
description: Use when adapting an existing Markdown knowledge base to OKF v0.1 frontmatter while preserving document bodies byte-for-byte — «адаптируй папку под OKF», «добавь OKF frontmatter», "migrate docs to OKF". Do not use for rewriting document bodies, ordinary Markdown cleanup, or repository onboarding files unless the user explicitly includes them.
---

# OKF adaptation

This is a low-freedom migration: frontmatter correctness and byte preservation are the contract. Use deterministic scripts for insertion and validation.

## Runtime and placement

The canonical source is the package-owned `skills/x9-okf-adapt` directory and the workflow supports Claude Code and Codex. Migration scripts require Python 3 and Ruby with Psych for strict YAML inspection. Git is optional: timestamp inventory falls back to filesystem modification time when Git history is unavailable.

## Scope contract

- Operate only on explicitly scoped Markdown files.
- Exclude generated/bulk directories and files according to [references/okf-format.md](references/okf-format.md).
- A complete header contains `type`, `title`, `description`, `tags`, and `timestamp`.
- A file with partial frontmatter belongs in repair scope; do not classify it as complete.
- Preserve every existing valid `type`, `title`, `description`, and `tags` value by default. A manifest fills missing or invalid fields; replacing a valid semantic field requires the explicit `--replace-existing-metadata` option. The script preserves a valid `timestamp` when meaning is unchanged and updates it automatically when an existing header receives a meaning-changing metadata repair.
- Preserve the original body bytes, BOM, and line-ending style. Header insertion is the only default mutation.
- Repository `AGENTS.md`, `CLAUDE.md`, and README changes belong to `x9-context-files-generator`; README files require `--include-readme`, and the other onboarding files stay outside this script even when integration is requested.

## Migration

1. Run `python3 scripts/check_dependencies.py` before inventory. Stop without editing documents when required dependencies fail; report Git fallback as `DEGRADED`, not blocked.
2. Snapshot candidate body hashes, line-ending/BOM metadata, and a deterministic suggested timestamp with `python3 scripts/insert_frontmatter.py <root> --inventory-out <inventory.json>`. For a new header or a missing/invalid timestamp, the script uses the last Git change and falls back to file modification time. During repair it updates a valid timestamp automatically only when semantic metadata changes.
3. Build the worklist with `python3 scripts/validate_okf.py <root> --missing`; review exclusions and partial headers.
4. Derive concise metadata from the complete document. For very large files, use headings plus enough body context to support an accurate description; do not claim to have read the full body when you did not.
5. Insert or repair headers only through `python3 scripts/insert_frontmatter.py <root> --manifest <metadata.json> --inventory <inventory.json>`, using an explicit metadata manifest. Existing valid core values win by default. Use `--replace-existing-metadata` only when the user explicitly requested changing them. Never use destructive Git restoration to undo an out-of-scope edit.
6. Run `python3 scripts/validate_okf.py <root> --inventory <inventory.json>` against the post-migration tree. It verifies all required fields, uniqueness rules, body hashes, BOM, and line endings.
7. Review the diff for header-only changes. Route onboarding-file changes separately if they were requested.

After changing the deterministic migration scripts, run `python3 scripts/test_okf.py` as their regression suite.

The metadata contract is in [references/okf-format.md](references/okf-format.md). Use [references/markup-agent-prompt.md](references/markup-agent-prompt.md) only to prepare metadata proposals; the agent never writes document bytes directly.

## Done

- Every in-scope file has five valid fields.
- Existing valid semantic metadata remained unchanged unless replacement was explicitly authorized; timestamp behavior matches the automatic meaning-change policy.
- Body hash, BOM, and line-ending checks pass against the pre-edit inventory.
- Exclusions and repaired partial headers are reported.
- No unrelated or onboarding file changed without explicit scope.
