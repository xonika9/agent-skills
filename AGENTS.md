# Agent Skills repository

This is the public source of truth for the `x9-*` Agent Skills. The package targets the open Agent Skills format; Claude Code and Codex also have native plugin manifests in this repository.

## Source ownership

- Treat every directory under `skills/` as canonical. Do not create runtime-specific copies of a skill.
- Keep platform-specific behavior inside a clearly named adapter or reference. Do not claim portability for a route that depends on a missing runtime tool.
- The published global-instruction files live in `global-files/`. They are examples for users, not instructions for work on this repository.
- Preserve unrelated and user-owned changes. Never commit, push, create a tag, or publish a release unless the user explicitly requests it.

## README and public copy

- Keep `README.md` as the canonical English presentation and `README.ru.md` as its Russian localization. Update the English structure first, then keep the Russian version materially equivalent.
- Explain skills through the problem they solve and the result a user gets. Keep the first screen useful before adding detail.
- Keep the Telegram call to action near the top of both READMEs and keep the `x9-` prefix explanation discoverable.
- Do not hard-code the number of skills in prose; the contents of `skills/` change over time.
- Do not publish placeholder screenshots or fabricated demos. Keep recording instructions under `docs/` until a real, sanitized capture is ready.
- Keep the repository hero and social preview at `assets/x9-agent-skills-hero.jpg` in a 2:1 layout. Keep plugin identity assets under `assets/` and validate every path declared in a manifest.
- GitHub social preview is a repository setting, not a README side effect. After an explicitly authorized visual update, upload the hero in Settings and verify the rendered repository card.
- After editing Russian public copy, run the `humanizer-ru` scanner. If its optional Python packages are unavailable, use an ephemeral environment rather than changing global Python state.
- Keep sensitive data, personal paths, credentials, browser profiles, cookies, and tokens out of the repository.

## Plugin metadata

- Keep `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` on the same semantic version.
- Keep the plugin name `x9-agent-skills` and marketplace name `xonika9` synchronized with `scripts/check_package.py`.
- Run `claude plugin validate .claude-plugin/marketplace.json`, `claude plugin validate .claude-plugin/plugin.json`, and `python3 scripts/check_package.py` after changing manifests or marketplace files. The repository script is the reproducible Claude/Codex package gate; a runtime-bundled Codex validator may be used as an additional local check.

## Changelog and releases

- Update `CHANGELOG.md` in the same task as every user-visible change, before reporting completion. Describe the outcome, not the implementation steps. Do not defer changelog reconstruction to release day.
- Keep an `Unreleased` section with `Highlights`, `Install / update`, `Compatibility`, and `Breaking changes`. When preparing a release, an agent must turn that section into concise release notes, state `None` explicitly when there are no breaking changes, and restore an empty `Unreleased` template.
- Before preparing a release, compare the complete diff from the latest public tag to `HEAD` with the candidate release notes. Reconcile every user-visible change, including changes omitted from `Unreleased`; review the `AUDIT` file list printed by `scripts/prepare_release.py --check` before publication.
- `scripts/prepare_release.py --check` also blocks post-release changes to public skills, installation surfaces, manifests, global examples, community documents, or identity assets when `Unreleased` is empty. This gate is a backstop, not a substitute for the semantic diff review.
- Choose the release version from the strongest change since the latest public tag; mixed releases use the highest applicable bump:
  - `PATCH` (`0.2.0` → `0.2.1`): backward-compatible fixes and corrections that do not intentionally change a skill's capability, trigger, workflow, output contract, installation route, or supported runtime behavior. Examples: typos, broken links, documentation corrections, and packaging or release bug fixes.
  - `MINOR` while the project is `0.x` (`0.2.0` → `0.3.0`): a new skill or capability, or any intentional change to public behavior or contracts, including triggers, workflows, outputs, installation or update routes, and runtime support. Record incompatible changes explicitly under `Breaking changes`.
  - `1.0.0`: only after an explicit maintainer decision that public skill names, installation and update routes, and supported behavior are stable enough for normal compatibility guarantees. Do not infer `1.0.0` from project age, release count, stars, or installations.
  - After `1.0.0`, use `MAJOR` for incompatible removals, renames, or changes to public skill, installation, update, or behavior contracts; use `MINOR` for backward-compatible capabilities and `PATCH` for backward-compatible fixes.
- During release preparation, the agent must propose the bump, cite the changes that determine it, and get the maintainer's confirmation before editing release versions. Scripts validate version format and consistency; they do not decide the bump.
- Treat «подготовь релиз» or an equivalent request as authorization to prepare release files only after the version is confirmed: update `CHANGELOG.md`, synchronize both plugin manifests, and run the full verification set. Stop before commit or push unless the user also requests publication.
- Treat «подготовь и выпусти релиз», «выпусти релиз», or another explicit publication request as authorization to prepare, commit, and push the release, then monitor both the validation and release workflows until the GitHub Release is visible or a concrete failure is reported.
- Before a release, set the release date, bump both plugin manifests to the same `X.Y.Z`, and make sure the changelog has a matching version heading.
- A successful push to `main` triggers `.github/workflows/release.yml` after validation. It creates annotated tag `vX.Y.Z` and the matching GitHub Release only when that version has not already been released.
- Never rewrite or move an existing public tag. Fix a released mistake with a new version.

## Verification

Run the focused checks for the files changed. Before release, run the full set:

```bash
for skill in skills/*; do
  python3 skills/x9-skill-creator/scripts/validate.py "$skill"
done

python3 skills/x9-skill-creator/scripts/test_validate.py
python3 skills/x9-okf-adapt/scripts/test_okf.py
python3 scripts/check_package.py
python3 scripts/check_public.py
python3 scripts/test_prepare_release.py
python3 scripts/prepare_release.py --check
claude plugin validate .claude-plugin/marketplace.json
claude plugin validate .claude-plugin/plugin.json
npx skills add . --list
git diff --check
```

Confirm that root `CLAUDE.md` contains exactly `@AGENTS.md` plus a final newline.
