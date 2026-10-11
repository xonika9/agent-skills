# Adopt, check, and clean up a folder

Run the dependency check first:

```bash
python3 <skill-directory>/scripts/check_dependencies.py
```

## Check

```bash
python3 <skill-directory>/scripts/validate_okf.py <root>
```

`FAIL` lines block; `WARN` lines are advice. `--missing` prints only the documents that need metadata work. A header the scripts cannot rewrite safely, such as one written in `{ }` style or with unquoted `:` in a value, is reported for a fix by hand.

## Adopt

1. Agree on the scope, write `.x9-okf.json` as described in [the contract](okf-format.md#scope) when the defaults do not fit, and bring the `AGENTS.md` block in line with [the template](agents-block.md). Show both in the plan.
2. Record body hashes in a file outside the folder:

   ```bash
   python3 <skill-directory>/scripts/insert_frontmatter.py <root> --inventory-out <inventory.json>
   ```

3. List the work with `validate_okf.py <root> --missing`, read each listed document, and write a manifest that sets all four contract fields. A read-only subagent can propose them with [the proposal brief](markup-agent-prompt.md).

   ```json
   {"Темы/2026-09-21-medicine/README.md": {"type": "Тема", "title": "Обследование 2026", "description": "…", "tags": ["health", "checkup"]}}
   ```

4. Preview, then apply:

   ```bash
   python3 <skill-directory>/scripts/insert_frontmatter.py <root> \
     --manifest <manifest.json> --inventory <inventory.json> --dry-run
   ```

   The preview names every value it keeps or replaces. An existing valid value is kept; an invalid one, such as a Russian tag, is replaced and its old value printed. Show the user every replacement of their own values before applying. `--replace-existing` also replaces valid values; use it only when the user asked for that. Run the same command without `--dry-run` to write.

5. Confirm that the bodies did not change:

   ```bash
   python3 <skill-directory>/scripts/validate_okf.py <root> --inventory <inventory.json>
   ```

## Remove retired fields

Only when the user asks, and after naming the fields and the number of documents in the plan:

```bash
python3 <skill-directory>/scripts/insert_frontmatter.py <root> \
  --remove-fields generated timestamp verified --dry-run
```

`--paths` limits the removal to named documents; the four contract fields cannot be removed. Run without `--dry-run` to write.

## Completion

The diff touches only headers and the agreed `.x9-okf.json`, and the check with the inventory passes.
