# The vault block in AGENTS.md

The block carries every rule an ordinary session needs for daily work, so the vault does not depend on this skill being invoked. Claude Code and Codex load `AGENTS.md` from the folder where the session starts; a rule moved to another file behind a pointer is often not followed on short requests.

## Template

Fill the angle-bracket slots from the agreed plan, write folder names as they exist, and drop any line with nothing to say. The block is written in English; the names inside it stay in the user's language.

```markdown
<!-- x9-personal-vault:start -->
## Personal vault

<Owner's name>'s personal vault: notes, documents, and ongoing life matters. Paths here are relative to this folder. Names are in <language>; keep new names in <language>. Local exceptions go outside this block.

### Where new material goes

Every matter lives in one topic folder, `<Topics>/<Name>/`, whether it never ends, like health, or takes a month, like a tax deduction. For anything new, decide only this:

- **Part of an existing topic:** put it inside that topic, following the layout its `README.md` describes; a large part becomes a subfolder. Find the topic by folder name, `area`, and README description, and prefer it over a new topic.
- **A new matter the user is working on:** create `<Topics>/<Name>/README.md` from `<System>/<Templates>/<topic>.md` right away, then ask what is needed.
- **No topic fits and the matter is unclear:** ask where it goes, offering two or three concrete options, such as the closest existing topics or a new topic with `state: later`.

News about something the vault tracks, such as a stage reached or a reply received, is an update: change the item's `stage` or the topic's `state` and `step` right away and add a log line.

Streams are series of same-shaped items moving through stages. Each item, from a bare idea on, is a folder `<Name>/README.md` created from the stream's template at its first stage, never an inbox note. Streams: `<Topics>/<topic>/<stream>/` (template `<System>/<Templates>/<item>.md`).

`<Inbox>/` is the user's drop zone for notes and files they want sorted; never create anything in it. Sort it only when the user asks: move each note's content to its place by these rules, merging it into an existing note when it continues one, then remove the inbox note. For a note whose place is unclear, offer options as above; until the user chooses, it stays.

A finished topic stays in place with `state: done`. `<Archive>/` holds old periods; add to it or change it only when the user asks.

### Names and dates

- Name a topic or stream item as the user would say it: `<Topics>/<example name>/`, with no date and no transliteration. When the name is taken by a different matter, add the year or a distinguishing word. Avoid `/ \ : * ? " < > | # ^ [ ]`.
- Start a file name with a date only when the note records one day, such as a visit or a meeting: `YYYY-MM-DD <name>.md`. Name other notes by content; a research note states in its text the date its data is current to.
- Never invent a date: when the real one is unknown, use the date the material was captured (for an inbox note, its file date) and say so in the note.

### Properties

- Topic `README.md`, from its template: `state` (`active` now, `waiting` blocked on something, `later`, `done`, `reference` nothing pending); `step`, the next action for `active` or what we wait for in `waiting`, required for both; `area`, one of <`value`, `value`, …>.
- Stream item `README.md`, from its template: `stage`, one value from the list in the stream's template; moving on is an edit of `stage`.
- Every note outside `<Inbox>/`, `raw/`, `<Archive>/`, `memory/`, and `<System>/<Templates>/`, including these READMEs, also carries the OKF header described in the `x9-okf-docs` block of this file. `log.md` files have no properties.

Record each notable change as one line in the topic's `log.md` under `## YYYY-MM-DD`, newest first.

### Structure changes

A new `area` value or stream, renaming, merging, or removing a topic or stream, and any change to these rules change the structure: describe the change and wait for the user's agreement; a request that already names the change exactly, including a new stream's stages, is that agreement. Rename and move through `x9-obsidian` when the vault is used in Obsidian, so links update. Apply the change with `x9-personal-vault`, or, if that skill is unavailable, update this block, the templates, and `<System>/<how-to>.md` together.

### Boundaries

- `<link path>` links to <what and where: an external disk with editing projects and media>. Never move, rename, or delete anything inside it. If it is unreachable, the disk is not connected: say so and do not recreate the folder.
- Move the user's files rather than deleting them; delete only on an explicit request. Removing a sorted inbox note is part of its move.
- `memory/USER.md` holds the stable profile and `memory/MEMORY.md` pointers and preferences; change them only when the user asks to remember or forget something.
<!-- x9-personal-vault:end -->
```

Keep the block within about 50 lines. A rule the vault's owner adds outside the block wins over the block for that vault; when the two conflict, report it and keep both until the user chooses.

## Parent folder pointer

When the agent starts in a parent folder of the vault (see [the model](model.md#agent-root)), the parent's `AGENTS.md` gets this block, and nothing else of the vault's rules:

```markdown
<!-- x9-personal-vault:start -->
## Personal vault

`<vault folder>/` is <Owner's name>'s personal vault with its own rules. A request to note or save something, and news about <Owner's name>'s matters, concern this vault. Before reading or writing anything inside it, read `<vault folder>/AGENTS.md` and follow it; its paths are relative to `<vault folder>/`.
<!-- x9-personal-vault:end -->
```

If the parent's `AGENTS.md` already describes the vault's folders or properties outside the marker, list those lines in the plan as moving into the vault's block, and remove them from the parent only with the plan's approval.

## Writing and updating

- `AGENTS.md`: with markers, replace only the content between them; without markers, insert the block after the file's opening summary; with no file, create one holding a one-line title and the block.
- `CLAUDE.md`, which Claude Code reads instead of `AGENTS.md`: with no file, create it containing exactly `@AGENTS.md`; when an existing file lacks that import, add the line `@AGENTS.md` at its top and keep the rest. Show either change in the plan. Do this in the vault and, when it holds the pointer, in the parent.
- Load `x9-agent-instructions` before writing the block, because it is agent-facing prose.

## Done

`CLAUDE.md` beside each written `AGENTS.md` contains the line `@AGENTS.md`, the vault's `AGENTS.md` holds the `x9-okf-docs` block, every stream, template, and external link named in the block exists, every stream folder is named in the block, every topic's `area` is in the block's list, the block is within budget, and nothing outside the markers changed except the agreed insertion point, a newly created file, or lines the plan moved from a parent.
