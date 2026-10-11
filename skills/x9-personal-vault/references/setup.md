# Set up a vault

The goal is a vault the user recognizes as theirs: their matters as topics, their recurring work as streams, their existing material in place, and nothing lost or broken on the way.

## Inspect

Survey the target folder before asking anything: its tree to a sensible depth, file counts and sizes by kind, existing `AGENTS.md`, `CLAUDE.md`, `.obsidian/`, `.git/`, symbolic links, links between the user's notes, and the material that must not be moved (see the manifest kinds below). On macOS, cloud files that are not downloaded carry the `dataless` flag (`ls -lO`); `scripts/apply_plan.py` refuses them.

Inspection reads; it does not open the contents of every file. Read enough of each folder to classify it.

## Talk

Ask only what inspection could not answer, offering your best reading of the folder for the user to confirm or correct. Cover:

- what keeps accumulating in their life and what they are working through right now: the topics;
- how they would group those topics: the `area` values, a handful at most;
- what they produce again and again in the same shape, and the stages each item goes through: the candidate streams;
- other folders anywhere else that belong in this vault, by path; inspect each one named the same way;
- what lives on external disks or in cloud folders and should stay there;
- whether they use Obsidian, and on which devices;
- whether anything is shared with another person or owned by another app or skill;
- where they start the agent: in this folder, or in a parent folder that also holds other material;
- the language for folder names when it is not obvious from the conversation.

Several answers can come from one message. Stop asking once the plan can be written; a missing detail with a reasonable default becomes a stated assumption in the plan.

## Plan

Present one plan in the conversation:

- the folder tree with topics and streams, and the `area` values;
- for each long-lived topic, what its README will say it holds and how it is laid out; for each stream, its stages;
- for a folder that already has its own structure, how each existing folder maps onto the model, including renames of topic folders whose names carry a date or a slug;
- a manifest table: source, destination, kind, action;
- what stays where it is and is linked instead;
- the optional layers chosen (Obsidian views, Git) and the block that will be written;
- assumptions the user should correct.

An approval of part of the plan applies only that part.

### Manifest kinds

| Kind | Examples | Action |
| --- | --- | --- |
| note or document | `.md`, `.txt`, office files, PDFs, scans, photos of documents | move inside the target folder; copy from other folders |
| media | video, audio, raw photo libraries | stays where it is and is linked from the topic's README; moved only when the user asks for that folder |
| app project | editor, design, or photo-library projects and bundles | never moved; a symbolic link to its folder may be added to the topic |
| cloud placeholder | files not downloaded from a cloud service | not copied; the user downloads them first or leaves them |

The script does not rewrite links. Split the manifest by that:

- Notes that link to each other inside an Obsidian vault move through `x9-obsidian`, which updates the links, including when the app cannot address this exact folder, such as a copy; its evidence is the link targets compared before and after.
- Linked notes outside Obsidian move together so their relative layout survives, or the plan lists the links that will need fixing.
- Everything else goes through the script.

## Apply

`scripts/apply_plan.py` runs the file operations from a JSON manifest on macOS and Linux. It validates every operation before changing anything, verifies every copy by SHA-256 and keeps file metadata such as Finder tags, never overwrites (names that differ only in case or Unicode form count as the same), never writes outside the vault or through a link, refuses cloud placeholders, and writes a journal that `--undo` reverses. Without `--apply` it only reports what it would do.

```json
{
  "vault": "/absolute/path/to/vault",
  "operations": [
    {"op": "mkdir", "path": "Темы/Здоровье/Визиты"},
    {"op": "move", "from": "старое/анализы.pdf", "to": "Темы/Здоровье/Анализы/анализы.pdf"},
    {"op": "copy", "from": "/absolute/path/to/other/folder", "to": "Темы/Видеоблог/Сценарии"},
    {"op": "symlink", "target": "/Volumes/Disk/Projects", "path": "Темы/Видеоблог/Проекты"},
    {"op": "remove", "path": "/absolute/path/to/other/folder", "verified_copy": "Темы/Видеоблог/Сценарии"}
  ]
}
```

```bash
python3 <skill-directory>/scripts/apply_plan.py <manifest.json>            # report only
python3 <skill-directory>/scripts/apply_plan.py <manifest.json> --apply    # run, print the journal path
python3 <skill-directory>/scripts/apply_plan.py --undo <journal.jsonl>     # reverse a run
```

Relative paths resolve inside the vault. `remove` is accepted only in a manifest of its own and only when an independent copy inside the vault is byte-identical; it cannot be undone, so it runs after the deletion confirmation the skill's boundaries require. Keep the manifest outside the vault; the script writes journals to `.x9-personal-vault/` in the vault.

After the files are in place, write:

- OKF headers for every note that came in, through the adoption route of `x9-okf-docs`, outside the exclusions in [the model](model.md#properties); the vault's `.x9-okf.json` with those exclusions and `README.md` included; and the `x9-okf-docs` block in the vault's `AGENTS.md`, whose Local part lists the vault's `type` values and names its language; when the parent folder has its own `.x9-okf.json`, exclude the vault there so each note is checked once;
- each topic's `README.md` and `log.md`, each stream's template, and the topic template in `<System>/<Templates>/`;
- `memory/USER.md` with what the user said about themselves, and an empty `memory/MEMORY.md`;
- the how-to note in `<System>/`, one screen in the user's language: where to open the agent; capture into the inbox; ask the agent to sort it; everything is a topic, grouped by `area`, with streams inside topics; how to change a topic's `state` or an item's `stage`;
- the block per [agents-block](agents-block.md), and the parent folder's pointer when the agent starts there;
- the optional Obsidian views and Git setup when chosen.

## Done

- The script's report shows every scripted operation applied and verified, with no failures, and its journal path is given to the user; moves made through `x9-obsidian` have their link check.
- Every source in the manifest is accounted for: moved, copied, linked, or listed as left in place.
- The tree matches the approved plan, `x9-okf-docs` validation passes outside the exclusions with the pre-edit body inventory, and the [block's Done](agents-block.md#done) holds.
