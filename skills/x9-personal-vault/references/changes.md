# Change, check, and upgrade a vault

Every change keeps the block, the folders, the templates, and the how-to note describing the same vault. A request that names the change and leaves no real choice, such as "add a Recipes area", authorizes it. When the shape is still open (area or stream, name, stages, what moves), propose it and wait.

## Change the structure

- **New area:** the folder with `README.md` (what it holds, layout, `type` values) and `log.md`; add it to the block's area list.
- **New stream:** the folder inside its area and a template in `<System>/<Templates>/` with `stage` and the ordered stage list; add it to the block's stream list and, with Obsidian, a board view grouped by `stage`.
- **Rename:** move through `x9-obsidian` when Obsidian is in use; update `area` links in topic READMEs, the block, and the how-to note.
- **Merge or remove:** move the contents to their new place first; an emptied folder is removed only after the user confirms it.
- **Promote a topic:** when a topic turns out to be a lasting matter, create the area, move the topic's lasting material into it, and leave the topic in place linking there.
- **Bring in another folder:** inspect it and apply a manifest as in [setup](setup.md#plan).

Record the change in the `log.md` of each touched area.

## Check

Read-only. Report, with the path and the fix for each:

- areas or streams that exist as folders but are missing from the block, or named in the block but missing;
- topics with an unknown `state`, or `active`/`waiting` without `step`;
- stream units whose `stage` is not in their template's list;
- folders or notes in the vault root outside the model, and inbox notes older than about a month;
- `log.md` files with properties;
- external links that are unreachable, reported as disconnected rather than broken;
- a block whose schema version is older than [the model](model.md#schema-version).

Apply only the fixes the user selects.

## Upgrade

Compare the block's schema version with the model's. Present the migration listed in the model for each version in between as a plan; after approval, apply it and rewrite only the block's content between its markers with the new version.

## Done

- Change: the diff touches only the paths in the agreed change, and the [block's Done](agents-block.md#done) holds.
- Check: every finding names a path and a fix, and nothing changed before the user's selection.
- Upgrade: the block declares the current schema version and the migrated vault passes Check.
