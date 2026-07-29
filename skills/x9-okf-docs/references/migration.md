# Audit and migrate legacy OKF

Bulk migration is optional. Prefer the active-document route in [maintain.md](maintain.md) so repositories converge during normal work.

## Audit v0.1

Audit is read-only by default:

```bash
python3 <skill-directory>/scripts/insert_frontmatter.py <root> \
  --migrate-v01 \
  --profile okf
```

OKF v0.1 remains consumable by v0.2 readers.

## Bulk migration

Migrate only when the scope is explicit and a truthful actor is known:

```bash
python3 <skill-directory>/scripts/insert_frontmatter.py <root> \
  --inventory-out <inventory.json>

python3 <skill-directory>/scripts/insert_frontmatter.py <root> \
  --migrate-v01 \
  --apply \
  --actor <actor> \
  --inventory <inventory.json>
```

This copies legacy `timestamp` to `generated.at` and keeps `timestamp` for older consumers. Remove it only with explicit `--drop-legacy-timestamp`. Leave legacy `# Citations` in the body; checked `sources` metadata and per-claim footnotes are separate body-aware work.

## Bundle version declaration

Only a bundle that deliberately uses a root `okf_version` needs a declaration. Validate the complete bundle first:

```bash
python3 <skill-directory>/scripts/validate_okf.py <root> \
  --profile okf \
  --target-version 0.2 \
  --whole-bundle \
  --ignore-version-declaration

python3 <skill-directory>/scripts/insert_frontmatter.py <root> \
  --declare-version 0.2 \
  --whole-bundle \
  --apply
```

Do not declare v0.2 while ordinary invalid or excluded Markdown remains inside the actual bundle.

Completion requires a reviewed frontmatter-only diff, passing whole-scope validation, and an explicit report of retained legacy compatibility.
