# Change and check a vault

Every change keeps the block, the folders, the templates, and the how-to note describing the same vault. A request that names the change and leaves no real choice, such as "add a Recipes group", authorizes it. When the shape is still open (a new topic or part of an existing one, name, stages, what moves), propose it and wait.

## Change the structure

- **New `area` value:** add it to the block's list and set it on the topics the user named.
- **New stream:** the folder inside its topic and a template in `<System>/<Templates>/` with `stage` and the ordered stage list; add it to the block's stream list and, with Obsidian, a board view grouped by `stage`.
- **Rename a topic, stream, or `area` value:** move through `x9-obsidian` when Obsidian is in use, so links update; update `area` on the affected topics, the block, and the how-to note.
- **Merge or remove:** move the contents to their new place first; an emptied folder is removed only after the user confirms it.
- **Bring in another folder:** inspect it and apply a manifest as in [setup](setup.md#plan).
- **Change the vault's rules:** rewrite only the content between the block's markers, then the templates and the how-to note to match.

Record the change in the `log.md` of each touched topic.

## Check

Read-only. Report, with the path and the fix for each:

- streams that exist as folders but are missing from the block, or named in the block but missing;
- topics with an `area` outside the block's list, an unknown `state`, or `active`/`waiting` without `step`;
- stream items whose `stage` is not in their template's list;
- topic or stream item folders named with a date, a transliterated slug, or a character the [model](model.md#names-and-dates) avoids, and topics that repeat one matter instead of being episodes of one topic;
- parallel copies of one note, such as `<note>-codex.md` or backup files, and crowded topic roots;
- folders or notes in the vault root outside the model, and inbox notes older than about a month;
- `log.md` files with properties, and notes that fail `x9-okf-docs` validation outside the exclusions;
- a block that differs from [the template](agents-block.md#template) in more than its filled slots, or a parent folder that starts the agent without the pointer;
- external links that are unreachable, reported as disconnected rather than broken.

Apply only the fixes the user selects.

## Done

- Change: the diff touches only the paths in the agreed change, and the [block's Done](agents-block.md#done) holds.
- Check: every finding names a path and a fix, and nothing changed before the user's selection.
