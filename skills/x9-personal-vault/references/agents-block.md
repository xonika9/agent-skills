# The vault block in AGENTS.md

The block carries every rule an ordinary session needs for daily work, so the vault does not depend on this skill being invoked. Claude Code and Codex load the root `AGENTS.md` automatically when the session starts in the vault root; a rule moved to another file behind a pointer is often not followed on short requests.

## Template

Fill the angle-bracket slots from the agreed plan, write folder names as they exist, and drop any line with nothing to say. The block is written in English; the names inside it stay in the user's language.

```markdown
<!-- x9-personal-vault:start -->
## Personal vault

<Owner's name>'s personal vault: notes, documents, and ongoing life matters. Folder and file names are in <language>; keep new names in <language>. Schema: x9-personal-vault <schema version>. Local exceptions go outside this block.

### Where new material goes

Decide by the shape of the material, not its subject:

- **Stream unit** — one of many same-shaped items moving through stages. Create `<Areas>/<area>/<stream>/<YYYY-MM-DD>-<slug>/README.md` from the stream's template. Streams: `<Areas>/<area>/<stream>/` (template `<System>/<Templates>/<unit>.md`).
- **Area material** — a never-finished matter that keeps accumulating. Put it inside its area, following the layout and `type` values in the area's `README.md`. Areas: `<Areas>/<area>/`, ….
- **Topic** — a question or project to work through and then keep for reference. When the user starts on one, create `<Topics>/<YYYY-MM-DD>-<slug>/README.md` from `<System>/<Templates>/<topic>.md` right away, then ask what is needed. Continue an existing topic instead when one covers the matter.
- **Unclear or quick capture** — a plain note in `<Inbox>/`, no properties.

Sort the inbox only when the user asks. Sorting moves each note's content to its place by these rules, merging it into an existing note when it continues one, then removes the inbox note. A note whose place is still unclear stays; say why.

`<Archive>/` holds finished periods and old material; add to it or change it only when the user asks.

A closed topic stays in place. Move its lasting conclusion into the related area and link to it from the topic.

Creating, renaming, merging, or removing an area or stream, or changing these rules, changes the structure: describe the change and wait for the user's agreement before creating anything; a request that already names the change exactly is that agreement. Then apply it with `x9-personal-vault`, or, if that skill is unavailable, update this block, the templates, and `<System>/<how-to>.md` together.

### Properties

- Topic `README.md`, from its template: `state` (`active` now, `waiting` blocked on something, `later`, `done`, `reference`); `step` — the next action for `active` or what we wait for in `waiting`, required for both; `area` — a link such as `"[[<Areas>/<area>/README|<area>]]"`, omitted when none; `aliases` — one short name.
- Stream unit `README.md`, from its template: `stage` — one value from the list in the stream's template; moving on is an edit of `stage`.
- Every note outside `<Inbox>/`, `raw/`, `<Archive>/`, `memory/`, and `<System>/<Templates>/`, including these READMEs, also carries the OKF header described in the `x9-okf-docs` block of this file. `log.md` files have no properties.
- Dates are `YYYY-MM-DD`. Never invent one: when the real date is unknown, use the date the material was captured (for an inbox note, its file date) and say so in the note. A slug is a few lowercase words in <language> joined by hyphens.

Record each notable change as one line in the touched topic's or area's `log.md` under `## YYYY-MM-DD`, newest first.

### Boundaries

- `<link path>` links to <what and where: an external disk with editing projects and media>. Never move, rename, or delete anything inside it. If it is unreachable, the disk is not connected: say so and do not recreate the folder.
- Move the user's files rather than deleting them; delete only on an explicit request. Removing a sorted inbox note is part of its move.
- `memory/USER.md` holds the stable profile and `memory/MEMORY.md` pointers and preferences; change them only when the user asks to remember or forget something.
<!-- x9-personal-vault:end -->
```

Keep the block within about 50 lines. A rule the vault's owner adds outside the block wins over the block for that vault; when the two conflict, report it and keep both until the user chooses.

## Writing and updating

- `AGENTS.md`: with markers, replace only the content between them; without markers, insert the block after the file's opening summary; with no file, create one holding a one-line title and the block.
- `CLAUDE.md`, which Claude Code reads instead of `AGENTS.md`: with no file, create it containing exactly `@AGENTS.md`; when an existing file lacks that import, add the line `@AGENTS.md` at its top and keep the rest. Show either change in the plan.
- Claude Code resolves the `@AGENTS.md` import only when the session starts in the vault root, so the how-to note tells the user to open the agent there.
- Load `x9-agent-instructions` before writing the block, because it is agent-facing prose.

## Done

`CLAUDE.md` contains the line `@AGENTS.md`, the `x9-okf-docs` block is present, every area, stream, template, and external link named in the block exists, every area and stream folder is named in the block, the block is within budget, and nothing outside the markers changed except the agreed insertion point or a newly created file.
