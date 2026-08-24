# Agent Skills repository

This is the public source of truth for the `x9-*` Agent Skills. The package targets the open Agent Skills format; Claude Code and Codex also have native plugin manifests in this repository. Never create branches — always commit and work directly on `main`.


## Source ownership

- Treat every directory under `skills/` as canonical. Do not create runtime-specific copies of a skill.
- Keep platform-specific behavior inside a clearly named adapter or reference. Do not claim portability for a route that depends on a missing runtime tool.
- The installable global-instruction files live under `global-files/<harness>/`. They do not govern work on this repository; the root `AGENTS.md` remains canonical here.
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

- Keep `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` synchronized across all shared metadata, including the semantic version.
- Keep the plugin name `x9-agent-skills` and marketplace name `xonika9` synchronized across both plugin manifests and `.claude-plugin/marketplace.json` plus `.agents/plugins/marketplace.json`, as enforced by `scripts/check_package.py`.
- Run `claude plugin validate .claude-plugin/marketplace.json`, `claude plugin validate .claude-plugin/plugin.json`, and `python3 scripts/check_package.py` after changing manifests or marketplace files. The repository script is the reproducible Claude/Codex package gate; a runtime-bundled Codex validator may be used as an additional local check.

## Changelog

- Update `CHANGELOG.md` in the same task as every user-visible change, before reporting completion. Describe the outcome, not the implementation steps. Do not defer changelog reconstruction to release day.
- Keep an `Unreleased` section with `Highlights`, `Install / update`, `Compatibility`, and `Breaking changes`.
- While the current version tag exists, `scripts/prepare_release.py --check` blocks release-relevant changes when `Unreleased` is empty. For a new untagged version, it instead requires complete dated release notes and an empty `Unreleased` template.

## Verification

Run the focused checks for the files changed.
Confirm that root `CLAUDE.md` contains exactly `@AGENTS.md` plus a final newline.
