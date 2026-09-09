---
name: x9-obsidian
description: Use when working with an Obsidian vault or its notes, links, embeds, properties, Bases, or Canvas — «найди заметку в Obsidian», «переименуй заметку и сохрани ссылки», "edit this vault", "fix this .base", "update this .canvas". Do not use for ordinary Markdown outside Obsidian, choosing a personal productivity system, research itself, or generic diagram design.
---

# Obsidian

Operate on the intended vault while preserving its links, structure, and local conventions. This package-owned skill is model-invoked in Claude Code, Codex, and OpenCode. Portable compatibility means Agent Skills structure; invocation and app behavior need separate runtime evidence. The [onboarding declaration](references/onboarding.json) describes optional app access and required local access.

## Target and authority

Resolve the vault from the user's request, workspace, and available local configuration. A parent directory may contain several vaults, independent Git repositories, and different sharing boundaries; establish the actual vault root and target file before operating. Discover applicable nested instructions when entering a target subtree outside the already-loaded workspace context. Ask only if the remaining ambiguity changes the target or authority.

A read or audit request authorizes a report. An edit request authorizes its safe local changes; broader reorganization, deletion, publication, plugin installation, and sync configuration require their own authorization. Do not turn an approved edit into another approval ritual. If permission is pending, prepare the concrete diff or move map and continue independent authorized work; elapsed time is not approval. Never delete archives or history as an organizational shortcut.

Keep personal facts, folder choices, task systems, and sharing policies in the vault's instructions or configuration. Do not impose a taxonomy, new metadata scheme, or folder migration. Git exclusions do not establish sync exclusions. A move across vaults or sharing boundaries needs an explicit destination and access scope; do not infer those from a shared parent path.

## Find and read

Start with filenames, a relevant index, or bounded search results, then read the matching notes and necessary neighbors. Do not load every note or attachment to answer a local question. Search results are candidates: distinguish an actual link or property from examples in code, quotations, and archived versions.

Use the [CLI adapter](references/cli.md) when Obsidian can supply resolved links or app-visible behavior. Filesystem tools remain suitable for bounded search and text edits. Resolve duplicate basenames with exact vault-relative paths; an alias is display metadata, not evidence that two files are interchangeable. Preserve the established Markdown-link or wikilink style.

## Edit notes

Read the current target immediately before a write. Use a narrow patch against that content, preserve unrelated properties and formatting, and detect intervening changes before replacing a whole file. If the user or sync changed the source, rebase the edit on the fresh version; do not overwrite a conflict copy or dismiss it as a duplicate. A failed write with an uncertain result requires a fresh read before retrying, especially for append operations.

Load [Markdown and properties](references/markdown.md) for link, embed, heading, block, or property edits. Keep heading and block identifiers stable unless changing them is part of the task: callers can depend on those anchors. Requested prose edits do not authorize wholesale metadata normalization.

For a rename or move, load [link-preserving moves](references/moves.md) before mutation. For `.base` views or `.canvas` scenes, use [structured formats](references/formats.md). Those formats are not ordinary Markdown files.

## Ownership and evidence

Use `x9-okf-docs` for an existing OKF requirement, `x9-research` for research, and `x9-diagrams` for other diagram formats or diagram-design work. Browser access belongs to `x9-browser-session`. These are conditional owners, not prerequisites for a plain note edit.

Return the resulting file paths, the requested change, and the evidence that matters for it: fresh content and diff for text; resolved affected references for moves; parsing plus app display or query results for structured formats. Distinguish local file success from sync delivery and structural validity from rendered behavior. When the app route is unavailable, state exactly what filesystem evidence establishes and what remains unverified. Stop dependent mutations on unresolved target ambiguity or repeated failure with the same cause; report the prerequisite instead of retrying blindly.
