# The vault model

One folder holds one person's life material. Folders say what kind of material lives there; properties on a few entry notes say what state it is in. Every rule below exists so that a person and any agent session, started cold, put the same thing in the same place.

## Folders

Folder names are chosen in the user's language during setup; the Russian defaults are shown. Elsewhere in this skill, `<Inbox>`, `<Areas>`, `<Topics>`, `<Archive>`, `<System>`, and `<Templates>` stand for the chosen names.

| Role | Russian default | Holds |
| --- | --- | --- |
| Inbox | `Входящее/` | quick captures with no properties; membership is by location |
| Areas | `Области/` | long-lived matters that keep accumulating: health, a video blog, finances |
| Topics | `Темы/<YYYY-MM-DD>-<slug>/` | questions and projects worked through and then kept for reference |
| Archive | `Архив/` | finished periods and old material; changes only on request |
| System | `Система/` | templates (`Шаблоны/`, the Templates role), the how-to note, optional Obsidian views |
| Memory | `memory/` | agent memory: `USER.md` stable profile, `MEMORY.md` pointers and preferences |

The vault root holds only these folders, `AGENTS.md`, `CLAUDE.md`, the optional Obsidian home note, and hidden tool folders.

## Kinds of material

Classify by the shape of the material, not its subject:

- **Stream unit:** one of many same-shaped items that move through stages, such as a video. A stream is a folder inside its area with one unit folder `<YYYY-MM-DD>-<slug>/README.md` per item; the unit is created from the stream's template, which lists the stages in order.
- **Area material:** a never-finished matter that keeps accumulating, such as visits to doctors. It goes inside its area, following the layout in the area's `README.md`.
- **Topic:** a question or project worked through once or twice and then kept, such as a tax deduction. Its `README.md` is the entry; supporting documents sit beside it, raw material in `raw/`.
- **Unclear capture:** a plain note in the inbox.

The same subject can produce all four: the video blog is an area, each video is a stream unit, "choose a camera" is a topic, and an idea jotted on the phone starts in the inbox.

## Areas and streams

- An area is `<Areas>/<Name>/` with `README.md` and `log.md`. The README says what the area holds, how it is laid out inside, and which `type` values its notes use; the agent follows that layout when adding material. A short "Now" section may list current commitments such as an ongoing treatment.
- A stream lives inside the area it serves. Its template sits in `<System>/<Templates>/` and carries the stage list in a comment, for example `идея → сценарий → съёмка → монтаж → опубликовано`.
- An area or stream exists only after the user agrees to it. An area becomes worth creating when material for it keeps arriving; a single question is a topic.

## Topics

- A topic is created as soon as the user starts working on a matter; questions are asked inside it. An existing topic covering the matter is continued instead.
- A closed topic stays in place with `state: done` or `reference`. Its lasting conclusion moves into the related area, which becomes the single source; the topic links to it rather than keeping a second copy.

## Inbox

Notes in the inbox carry no properties, so a thought can be captured in one tap on any device. Sorting moves each note's content to its place and then removes the inbox note, because its text now lives there; a note whose place is still unclear stays. Sorting happens when the user asks.

## Properties

| Note | Properties |
| --- | --- |
| Topic `README.md` | `state`: `active` (now), `waiting` (blocked on something), `later`, `done`, `reference`; `step`: the next action for `active` or what we wait for in `waiting`, required for both; `area`: a link to the related area's README, omitted when none; `aliases`: one short name in the user's language; plus `type`, `title`, `description`, `tags` |
| Stream unit `README.md` | `stage`: one value from the stream template's list; plus `type`, `title`, `description`, `tags` |
| Any other note an agent writes | `type` (from the area README or template), `title`, `description` (one sentence), `tags` |
| `log.md` | none |
| Notes the user brought in | left as they are; the agent adds properties only when it substantively rewrites the note |

- `area` is a wiki link, for example `"[[Области/Медицина/README|Медицина]]"`, so a rename in Obsidian updates it.
- Dates are `YYYY-MM-DD`. A date is never invented: when the real date is unknown, the note uses the date the material was captured (for an inbox note, its file date) and says so.
- A slug is a few lowercase words in the user's language joined by hyphens.
- Each topic and area keeps `log.md`: `## YYYY-MM-DD` headings, newest first, one line per notable change. History is not reconstructed retroactively.

The `type`, `title`, `description`, `tags` set is compatible with OKF, but the vault does not claim OKF conformance: inbox notes deliberately carry no frontmatter. Fields such as `generated`, `verified`, or `stale_after` are added only when the user opts into OKF, through `x9-okf-docs`.

## External folders

Editing projects, raw media, and other bulky or app-owned material can stay on an external disk or in a cloud folder and appear in the vault as a symbolic link inside the area that uses it. The block names every such link. An agent never moves, renames, or deletes anything through it; when the target is unreachable, the disk is disconnected, which is reported and never "repaired" by recreating the folder.

## Memory

`memory/USER.md` holds stable facts about the user; `memory/MEMORY.md` holds pointers to live notes and working preferences, never copies of facts that live elsewhere in the vault. An agent changes them only when the user asks it to remember or forget something.

## Optional layers

- **Obsidian.** When the user uses Obsidian, add a home note in the root and a Bases file in `<System>/` with views built from properties, not folder paths: Now (`state: active`, with `step`), Waiting (`state: waiting`), Attention (topics with an unknown `state`, or `active`/`waiting` without `step`), Inbox (notes in the inbox folder), and one board per stream grouped by `stage`. Set the app's folder for new notes to the inbox. Bases syntax and link-safe moves belong to `x9-obsidian`. Without Obsidian, an agent answers "what is active now" from the same properties on request.
- **Git.** Local history only. Ignore media and app project files. A remote is the user's separate decision.

## Schema version

Current: `1`. The block records the version it was written for. A later model version lists here what changed and how to migrate a vault written for an earlier one.
