---
name: release
description: Use for this repository when the maintainer asks to prepare or publish a release — «подготовь релиз», «выпусти релиз», "prepare a release", "publish the release". Do not use for ordinary changelog edits, package validation, commits, pushes, or pull requests that are not explicitly a release.
metadata:
  internal: true
---

# Release

Prepare or publish a version of `x9-agent-skills` from the complete repository state. The latest public tag, the diff to the release candidate, `CHANGELOG.md`, both plugin manifests, the validation workflow, and the release workflow are the sources of truth; do not infer release scope from the current conversation or recent commits alone.

This is a private repository-local skill for Claude Code and Codex. Its canonical source is `.claude/skills/release`; `.agents/skills` exposes that source through a repository-relative symlink. Do not add it to the public `skills/` package or its manifests and READMEs.

## Select the mode

- **Prepare** applies when the request is to prepare a release. Propose the version, wait for maintainer confirmation, update release files, and run the release gate. Stop before commit, push, tag, or GitHub Release.
- **Publish** applies only when the maintainer explicitly asks to publish or release. It includes preparation, a release commit, a push to `main`, and monitoring until the matching GitHub Release is visible or a concrete failure is reported.

An ordinary request to commit, push, merge, edit the changelog, or validate the package is not release authority. Never create or move a tag manually; `.github/workflows/release.yml` owns tag and GitHub Release creation after the pushed `main` commit passes validation.

## Establish the candidate

Resolve the repository root from this skill's location, then inspect:

- the worktree, current branch, remotes, and latest public `v*` tag;
- the complete diff and commit range from that tag to the candidate, including uncommitted and untracked files;
- `README.md`, `README.ru.md`, `CHANGELOG.md`, `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`;
- the installed personal `~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md` plus the published examples in `global-files/`;
- `scripts/prepare_release.py`, `.github/workflows/validate.yml`, and `.github/workflows/release.yml`.

Preserve unrelated and user-owned changes. If the candidate cannot be separated from unrelated work, the current branch cannot safely produce the intended `main` release, or the remote state conflicts with the local history, stop and report the exact blocker instead of rewriting history, discarding files, merging, or force-pushing.

Reconcile every user-visible change since the latest public tag with the release notes. Treat the `AUDIT` file list from `python3 scripts/prepare_release.py --check` as a backstop, not a substitute for reading the semantic diff.

## Prevent README drift

Read both READMEs completely and trace every public skill, installation route, compatibility claim, renamed concept, and removed behavior in the candidate to its documentation. A changed public contract must have an accurate corresponding section or an explicit, evidence-backed determination that the change has no README impact. Do not infer coverage from whether a README file appears in the diff.

Keep `README.md` as the canonical English presentation and `README.ru.md` materially equivalent. Plan corrections before proposing the version; after confirmation, update the English structure and facts first, then synchronize the Russian localization. Preserve verified commands, identifiers, links, and claims. Do not document this private release skill in either README.

Load the installed `humanizer-ru` skill for the final Russian text. Apply its documentation-level editing rules without changing meaning or manufacturing facts, then run its bundled scanner against the complete `README.ru.md`, even when the file did not require a release-specific edit. Resolve the skill and scanner from the live runtime rather than a personal absolute path. If optional packages are missing, use an ephemeral environment instead of changing global Python state. Treat scanner findings as evidence to review, not permission to damage technical accuracy for a score.

## Synchronize global instruction examples

Load `x9-agent-instructions`, then compare the installed personal global files with `global-files/AGENTS.md` and `global-files/CLAUDE.md`. The repository files are sanitized published examples: update them from the current personal contracts, preserving the byte-identical shared core and keeping Codex-only and Claude Code-only behavior in their respective runtime adapters.

Never copy credentials, personal paths, machine-specific state, private project names, or unverified runtime observations into `global-files/`. Replace local installation details with discoverable public instructions and retain the meaning of authority and safety boundaries. Keep the README descriptions of the global files accurate in both languages.

Release authority permits reading the personal global files and updating their repository examples; it does not permit editing files under `~/.claude/` or `~/.codex/`. If the personal shared cores disagree or their intended public form is ambiguous, mark preparation `BLOCKED` instead of choosing a source or modifying home-directory files.

## Choose and confirm the version

Propose the version from the strongest change in the full candidate and cite the changes that determine the bump:

- Before `1.0.0`, use `PATCH` for backward-compatible corrections that do not intentionally change a skill's capability, trigger, workflow, output contract, installation route, or supported runtime behavior; use `MINOR` for a new capability or any intentional change to those public contracts.
- Use `1.0.0` only after an explicit maintainer decision that public names, installation and update routes, and supported behavior are stable enough for normal compatibility guarantees.
- After `1.0.0`, use `MAJOR` for incompatible public-contract changes, `MINOR` for backward-compatible capabilities, and `PATCH` for backward-compatible fixes.
- A mixed release takes the highest applicable bump.

Obtain the maintainer's confirmation through the runtime's structured question tool as defined in [version-confirmation.md](references/version-confirmation.md), even when the initial request names a version. Never use a plain chat question for this gate. If the proposed version already has a public tag or GitHub Release, stop; a released version is immutable and must be corrected with a new version.

## Prepare release files

After version confirmation:

- move the populated `Unreleased` content into `## X.Y.Z - YYYY-MM-DD`;
- leave a new empty `Unreleased` template with `Highlights`, `Install / update`, `Compatibility`, and `Breaking changes`;
- make the release notes concise and outcome-oriented, cover the complete candidate, and write `None.` explicitly when there are no breaking changes;
- apply the identified README corrections, keeping the English and Russian versions materially equivalent;
- synchronize the sanitized examples in `global-files/` with the current personal global contracts;
- set the same `X.Y.Z` in both plugin manifests.

Do not include private paths, credentials, tokens, cookies, fabricated evidence, or changes outside the confirmed candidate.

## Release gate

Run the complete command set in [checks.md](references/checks.md). A failed command blocks preparation and publication until it is fixed or the maintainer explicitly changes scope; never present a partial gate as a successful release.

Preparation is complete when the release diff contains the confirmed version and date, both manifests agree, `Unreleased` is reset, the notes cover the tag-to-candidate diff, every public change is accurately represented in both READMEs or has a justified no-impact determination, the global examples match the sanitized current personal contracts, and every required check passes.

## Publish

Publication requires all preparation conditions plus explicit publish authority. Commit the coherent release candidate without absorbing unrelated changes, push the release commit to `main` without force, and monitor the repository's validation and release workflows.

Publication is complete only when the GitHub Release for `vX.Y.Z` is visible and points to the released commit. If a workflow fails, the tag points elsewhere, GitHub is unreachable, or the release does not appear after the workflows terminate, report the concrete state and stop without manufacturing or moving the tag.
