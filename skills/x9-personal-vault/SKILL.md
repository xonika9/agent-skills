---
name: x9-personal-vault
description: Use when organizing one person's scattered notes and documents into a personal vault, or restructuring or checking a vault built this way — inbox, one topic folder per matter grouped by a property, staged streams inside topics, archive — «организуй мою папку», «собери мои папки в одно хранилище», «заведи новый поток», «проверь хранилище», "set up my personal vault". Not for everyday notes inside a set-up vault (its AGENTS.md rules cover that), link audits or Obsidian link, Bases, or Canvas mechanics (x9-obsidian), or repository documentation (x9-context-files-generator).
---

# Personal vault

This package-owned skill is model-invoked in Claude Code and Codex. Its portable claim is structural Agent Skills compatibility only, not proven invocation behavior. Its file script supports macOS and Linux.

It turns a folder, plus any other folders the user names, into a personal vault built on [the vault model](references/model.md), and leaves the daily rules inside the vault. Ordinary agent sessions then keep the vault in order without this skill; the skill is needed again only when the structure changes.

## Select the action

- **Set up:** the vault has no `x9-personal-vault` block in its `AGENTS.md`, including a folder that already has its own structure. Follow [setup](references/setup.md).
- **Change structure:** add an `area` value or a stream, rename, merge, or remove a topic or stream, or change the vault's rules. Follow [changes](references/changes.md).
- **Check:** report where the vault drifted from its rules. Follow [changes](references/changes.md#check).

Infer the action from the request and the folder's state.

## Ownership

- This skill owns the vault model, the vault's templates and how-to note, and the block between `<!-- x9-personal-vault:start -->` and `<!-- x9-personal-vault:end -->` in the vault's `AGENTS.md` and, when the agent starts in a parent folder, in that folder's `AGENTS.md`, written per [agents-block](references/agents-block.md). Text outside the markers belongs to the user.
- `x9-obsidian` owns link-preserving moves inside an Obsidian vault and Bases files; use it for those when Obsidian is in use.
- `x9-okf-docs` owns the OKF header of every note outside the vault's [exclusions](references/model.md#properties) and its own block in the vault's `AGENTS.md`.
- A file that the vault's `AGENTS.md` assigns to another skill, or that belongs to another app, is placed or linked, never rewritten.

## Boundaries

- Inspection, the conversation, and the plan change nothing. Changes start only after the user approves the plan or names the exact change.
- Read only the target folder, its parent's `AGENTS.md` and `CLAUDE.md` when the agent starts there, and the paths the user names.
- Deleting a user's file needs its own confirmation naming that file or folder, after the user has seen its verified copy. Merging an inbox note into its place is a move, not a deletion.
- Offer Git as local-only. A remote, sync service, or sharing setup is the user's separate decision; a vault with health or financial records stays private.
- Human-facing files are written in the user's language; the `AGENTS.md` block is written in English.

## Done

- Set up: the condition in [setup](references/setup.md#done) holds.
- Change structure, Check: the condition in [changes](references/changes.md#done) holds.

The [onboarding declaration](references/onboarding.json) lists external prerequisites.
