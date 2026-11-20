# The vault model

One folder holds one person's life material. Every matter, short or never-ending, is one topic folder; a property groups topics, so a wrong guess costs a property edit, not a move. Every rule exists so that a person and any agent session, started cold, put the same thing in the same place. The everyday rules have one canonical text, the vault block in [the template](agents-block.md#template); this file holds the rationale and what the block does not.

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

The placement, repeat, inbox, naming, date, and property rules an everyday session follows are written once, in the [block template](agents-block.md#template). This file does not restate them. A long-lived topic's `README.md` says what it holds and how it is laid out inside, so every session files new material the same way.

## Groups

`area` groups topics for lists and views, such as `Здоровье`, `Контент`, `Быт`. The vault block lists the allowed values; a new value is added only with the user's agreement, because a group that exists for one topic adds nothing.

## Streams

A stream is a series of same-shaped items moving through stages, such as videos. Its template in `<System>/<Templates>/` carries `stage` and the stage list in a comment, for example `идея → сценарий → съёмка → монтаж → опубликовано`. A stream exists only after the user agrees to it.

## Repeats

Each episode of a collection carries the topic's properties, so views show it as a separate matter. Turning a topic into a collection moves the first episode's files from the topic root into their own subfolder, and may rename the topic to the general matter, such as `Ремонт кухни` to `Ремонт`. The agent proposes this and waits for agreement, then moves through `x9-obsidian` when Obsidian is in use, so links survive. Once the collection exists, a new episode is just a new subfolder.

## Inside a topic

The topic's `README.md` links to its current notes; raw material goes into `raw/`.

## Inbox

The inbox belongs to the user, who drops notes and files there in one tap on any device and without properties. The agent never creates anything in it, so it only ever holds what the user has not had sorted yet.

## Properties

Every note outside the OKF exclusions is an OKF document, so an agent can choose a note from its header without reading it. `x9-okf-docs` owns the header (`type`, `title`, `description`, `tags`, all required) and its own block in `AGENTS.md`; the vault block does not restate it. The block's Local part lists the vault's `type` values. Bodies of notes the user brought in stay byte-identical when they receive a header.

OKF exclusions: `<Inbox>/` (the user's drop zone, without frontmatter), `raw/`, `archive/` inside topics, `<Archive>/`, `memory/`, and `<System>/<Templates>/`. The vault's `.x9-okf.json` lists them and includes `README.md`, so every check uses the same scope.

The vault's own keys on entry notes (`state`, `step`, `area`, `stage`, `aliases`) are defined in the template's Properties. Each topic keeps `log.md` in the OKF log format: `## YYYY-MM-DD` headings, newest first, one line per notable change, no frontmatter. History is not reconstructed retroactively.

## Agent root

Usually the agent starts in the vault root and reads its `AGENTS.md`. Some users start it in a parent folder that holds more than the vault, such as shared notes. The vault keeps its own `AGENTS.md` and `CLAUDE.md` either way, with paths relative to the vault root, so the vault works the same when opened alone. The parent's `AGENTS.md` gets a short marked pointer so a session started there explicitly loads the vault rules before touching its contents.

## External folders

Editing projects, raw media, and other bulky or app-owned material can stay on an external disk or in a cloud folder and appear in the vault as a symbolic link inside the topic that uses it. The block names every such link and carries the rules for working through it.

## Memory

`memory/USER.md` holds stable facts about the user; `memory/MEMORY.md` holds pointers to live notes and working preferences, never copies of facts that live elsewhere in the vault.

## Optional layers

- **Obsidian.** When the user uses Obsidian, add a home note in the root and a Bases file in `<System>/` with views built from properties, not folder paths: Now (`state: active`, with `step`), Waiting (`state: waiting`), Attention (topics with an unknown `state`, or `active`/`waiting` without `step`), Inbox (notes in the inbox folder), topics grouped by `area`, and one board per stream grouped by `stage`. Views show a topic by its `aliases`. Set the app's folder for new notes to the inbox. Bases syntax and link-safe moves belong to `x9-obsidian`. Without Obsidian, an agent answers "what is active now" from the same properties on request.
- **Git.** Local history only; when the vault sits inside an existing repository, use that one. Ignore media and app project files. A remote is the user's separate decision.
