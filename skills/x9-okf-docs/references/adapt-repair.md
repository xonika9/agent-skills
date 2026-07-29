# Adopt or repair OKF documents

Use this route for initial adoption, new frontmatter, or metadata that `--touch` rejects as incomplete or invalid.

Run the dependency check before mutation:

```bash
python3 <skill-directory>/scripts/check_dependencies.py
```

Inventory the explicitly scoped concept files and their body hashes:

```bash
python3 <skill-directory>/scripts/insert_frontmatter.py <root> \
  --inventory-out <inventory.json>
```

Build the default curated worklist:

```bash
python3 <skill-directory>/scripts/validate_okf.py <root> --missing
```

Use `--profile okf` only when official conformance, rather than the stricter x9 curated profile, is the requested target. Derive concise metadata from each complete document and obtain a truthful actor in the form `<producer>/<version>`, `human:<id>`, or `process:<id>`.

Apply an explicit manifest:

```bash
python3 <skill-directory>/scripts/insert_frontmatter.py <root> \
  --manifest <metadata.json> \
  --inventory <inventory.json> \
  --actor <actor>
```

Existing valid semantic metadata wins unless the user explicitly authorized `--replace-existing-metadata`. A meaning-changing repair refreshes `generated`. The field contract is owned by [okf-format.md](okf-format.md).

Validate against the pre-edit inventory:

```bash
python3 <skill-directory>/scripts/validate_okf.py <root> \
  --inventory <inventory.json>
```

Completion requires a frontmatter-only diff for existing documents, preserved body hashes/BOM/line endings, and a passing selected profile.
