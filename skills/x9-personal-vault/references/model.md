# The vault model

One folder holds one person's life material. Every matter, short or never-ending, is one topic folder; a property groups topics, so a wrong guess costs a property edit, not a move. Every rule below exists so that a person and any agent session, started cold, put the same thing in the same place.

## Folders

Folder names are chosen in the user's language during setup; the Russian defaults are shown. Elsewhere in this skill, `<Inbox>`, `<Topics>`, `<Archive>`, `<System>`, and `<Templates>` stand for the chosen names.

| Role | Russian default | Holds |
| --- | --- | --- |
| Inbox | `Входящее/` | the user's drop zone: notes and files they leave for the agent to sort; no properties |
| Topics | `Темы/<Name>/` | every matter: health, a video blog, a tax deduction, a trip |
| Archive | `Архив/` | old periods and material nobody works with; changes only on request |
| System | `Система/` | templates (`Шаблоны/`, the Templates role), the how-to note, optional Obsidian views |
| Memory | `memory/` | agent memory: `USER.md` stable profile, `MEMORY.md` pointers and preferences |

The vault root holds only these folders, `AGENTS.md`, `CLAUDE.md`, `.x9-okf.json`, the optional Obsidian home note, and hidden tool folders.

## Where material goes

New material needs one decision:

- **Part of an existing topic:** it goes inside that topic, following the layout the topic's `README.md` describes; a large part, such as one year's medical checkup, becomes a subfolder. An existing topic is preferred over a new one.
- **A new matter the user is working on:** a new topic, created as soon as the work starts; questions are asked inside it.
- **No topic fits and the matter is unclear:** the agent asks where it goes, offering two or three concrete options, such as the closest existing topics or a new topic with `state: later`.

News about a tracked matter, such as a video reaching the next stage or a reply arriving, is an update to the existing item or topic, never a new note.

A topic lasts as long as its matter: health never closes, a tax deduction closes in a month. A finished topic stays in place with `state: done`. A long-lived topic's `README.md` says what it holds and how it is laid out inside, so every session files new material the same way.

## Groups

`area` groups topics for lists and views, such as `Здоровье`, `Контент`, `Быт`. The vault block lists the allowed values; a new value is added only with the user's agreement, because a group that exists for one topic adds nothing.

## Streams

A stream is a series of same-shaped items moving through stages, such as videos. It is a folder inside its topic with one folder `<Name>/README.md` per item, created from the stream's template in `<System>/<Templates>/` as soon as the item exists, even as a bare idea; the template carries `stage` and the stage list in a comment, for example `идея → сценарий → съёмка → монтаж → опубликовано`. A stream exists only after the user agrees to it.

## Repeats

- **The same kind of matter again,** such as another renovation or another tax deduction, even in another room or year, belongs in the existing topic, which becomes a collection of episodes. Each episode is a subfolder named by what sets it apart, `Темы/Ремонт/Кухня/` and `Темы/Ремонт/Ванная/`, with its own `README.md` carrying the topic properties, so views show it as a separate matter. The topic's README lists the episodes.
- Turning a topic into a collection moves the first episode's files from the topic root into their own subfolder, and may rename the topic to the general matter, such as `Ремонт кухни` to `Ремонт`. The agent proposes this and waits for agreement, then moves through `x9-obsidian` so links survive. Once the collection exists, a new episode is just a new subfolder.
- **A different matter with a similar name** gets a more precise name, such as `Ремонт квартиры` and `Ремонт машины`.

## Inside a topic

- One question has one note. A later pass on the same question, by any agent at any time, updates that note; when it is rewritten wholesale, the previous version moves to the topic's `archive/`. Parallel copies such as `<note>-codex.md` and backup files beside a note are not kept: `archive/` and Git hold history.
- The topic's `README.md` says how the topic is laid out and links to its current notes; raw material goes into `raw/`.
- When a topic's root gets crowded, the agent proposes grouping its notes into subfolders by subject and waits, because it is a move.

## Names and dates

- A topic or stream item is named as the user would say it, in their language: `Темы/Здоровье/`, `Темы/Налоги ИП/`. No date and no transliterated slug. A name never repeats an existing topic's name; see [repeats](#repeats). A year appears in a name only when it is what sets episodes apart, as with an annual tax return.
- Names avoid `/ \ : * ? " < > | # ^ [ ]`, which break Obsidian links or some file systems.
- A file name starts with a date only when the note records one day, such as a doctor's visit or a meeting: `YYYY-MM-DD <name>.md`. Other notes are named by content. A research note states in its text the date its data is current to.
- Dates are `YYYY-MM-DD`. A date is never invented: when the real date is unknown, the note uses the date the material was captured (for an inbox note, its file date) and says so.

## Inbox

The inbox belongs to the user: they drop notes and files there, in one tap on any device and without properties, for the agent to sort. An agent never creates anything in it, so the inbox only ever holds what the user has not had sorted yet. Sorting happens when the user asks: each note's content moves to its place and the inbox note is removed, because its text now lives there. For a note whose place is unclear, the agent offers options as above; until the user chooses, the note stays.

## Properties

Every note outside the OKF exclusions is an OKF document, so an agent can choose a note from its header without reading it. `x9-okf-docs` owns the header (`type`, `title`, `description`, `tags`, all required) and its own block in `AGENTS.md`; the vault block does not restate it. The block's Local part lists the vault's `type` values. Bodies of notes the user brought in stay byte-identical when they receive a header.

OKF exclusions: `<Inbox>/` (the user's drop zone, without frontmatter), `raw/`, `archive/` inside topics, `<Archive>/`, `memory/`, and `<System>/<Templates>/`. The vault's `.x9-okf.json` lists them and includes `README.md`, so every check uses the same scope.

The vault adds its own keys to entry notes:

| Note | Vault keys |
| --- | --- |
| Topic or episode `README.md` | `state`: `active` (now), `waiting` (blocked on something), `later`, `done`, `reference` (nothing pending, kept for reference); `step`: the next action for `active` or what we wait for in `waiting`, required for both; `area`: one value from the block's list |
| Stream item `README.md` | `stage`: one value from the stream template's list |

Each topic keeps `log.md` in the OKF log format: `## YYYY-MM-DD` headings, newest first, one line per notable change, no frontmatter. History is not reconstructed retroactively.

## Agent root

Usually the agent starts in the vault root and reads its `AGENTS.md`. Some users start it in a parent folder that holds more than the vault, such as shared notes. The vault keeps its own `AGENTS.md` and `CLAUDE.md` either way, with paths relative to the vault root, so the vault works the same when opened alone. The parent's `AGENTS.md` gets a short marked pointer to them, because Codex never reads instruction files below its starting folder, and Claude Code and OpenCode read them only after opening a file there.

## External folders

Editing projects, raw media, and other bulky or app-owned material can stay on an external disk or in a cloud folder and appear in the vault as a symbolic link inside the topic that uses it. The block names every such link. An agent never moves, renames, or deletes anything through it; when the target is unreachable, the disk is disconnected, which is reported and never "repaired" by recreating the folder.

## Memory

`memory/USER.md` holds stable facts about the user; `memory/MEMORY.md` holds pointers to live notes and working preferences, never copies of facts that live elsewhere in the vault. An agent changes them only when the user asks it to remember or forget something.

## Optional layers

- **Obsidian.** When the user uses Obsidian, add a home note in the root and a Bases file in `<System>/` with views built from properties, not folder paths: Now (`state: active`, with `step`), Waiting (`state: waiting`), Attention (topics with an unknown `state`, or `active`/`waiting` without `step`), Inbox (notes in the inbox folder), topics grouped by `area`, and one board per stream grouped by `stage`. Views show a topic by its folder name. Set the app's folder for new notes to the inbox. Bases syntax and link-safe moves belong to `x9-obsidian`. Without Obsidian, an agent answers "what is active now" from the same properties on request.
- **Git.** Local history only; when the vault sits inside an existing repository, use that one. Ignore media and app project files. A remote is the user's separate decision.
