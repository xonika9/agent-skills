---
name: x9-okf-adapt
description: Use when adapting an existing Markdown knowledge base to OKF v0.1 frontmatter while preserving document bodies byte-for-byte — «адаптируй папку под OKF», «добавь OKF frontmatter», "migrate docs to OKF". Do not use for rewriting document bodies, ordinary Markdown cleanup, or repository onboarding files unless the user explicitly includes them.
---

# OKF adaptation

This is a low-freedom migration: frontmatter correctness and byte preservation are the contract. Use deterministic scripts for insertion and validation.

## Scope contract

- Operate only on explicitly scoped Markdown files.
- Exclude generated/bulk directories and files according to [references/okf-format.md](references/okf-format.md).
- A complete header contains `type`, `title`, `description`, `tags`, and `timestamp`.
- A file with partial frontmatter belongs in repair scope; do not classify it as complete.
- Preserve every existing valid core field by default. A manifest fills missing or invalid fields; replacing a valid `type`, `title`, `description`, `tags`, or `timestamp` requires the explicit `--replace-existing-metadata` option.
- Preserve the original body bytes, BOM, and line-ending style. Header insertion is the only default mutation.
- Repository `AGENTS.md`, `CLAUDE.md`, and README changes belong to `x9-context-files-generator`; README files require `--include-readme`, and the other onboarding files stay outside this script even when integration is requested.

## Migration

1. Snapshot candidate body hashes, line-ending/BOM metadata, and a deterministic suggested timestamp with `python3 scripts/insert_frontmatter.py <root> --inventory-out <inventory.json>`. The script preserves an existing valid timestamp, otherwise uses the last Git change and falls back to file modification time.
2. Build the worklist with `python3 scripts/validate_okf.py <root> --missing`; review exclusions and partial headers.
3. Derive concise metadata from the complete document. For very large files, use headings plus enough body context to support an accurate description; do not claim to have read the full body when you did not.
4. Insert or repair headers only through `python3 scripts/insert_frontmatter.py <root> --manifest <metadata.json> --inventory <inventory.json>`, using an explicit metadata manifest. Existing valid core values win by default. Use `--replace-existing-metadata` only when the user explicitly requested changing them. Never use destructive Git restoration to undo an out-of-scope edit.
5. Run `python3 scripts/validate_okf.py <root> --inventory <inventory.json>` against the post-migration tree. It verifies all required fields, uniqueness rules, body hashes, BOM, and line endings.
6. Review the diff for header-only changes. Route onboarding-file changes separately if they were requested.

After changing the deterministic migration scripts, run `python3 scripts/test_okf.py` as their regression suite.

The metadata contract is in [references/okf-format.md](references/okf-format.md). Use [references/markup-agent-prompt.md](references/markup-agent-prompt.md) only to prepare metadata proposals; the agent never writes document bytes directly.

## Done

- Every in-scope file has five valid fields.
- Existing valid core metadata remained unchanged unless replacement was explicitly authorized.
- Body hash, BOM, and line-ending checks pass against the pre-edit inventory.
- Exclusions and repaired partial headers are reported.
- No unrelated or onboarding file changed without explicit scope.
