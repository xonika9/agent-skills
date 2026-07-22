# Agent Skills repository

This is the public source of truth for the `x9-*` Agent Skills. The package targets the open Agent Skills format; Claude Code and Codex also have native plugin manifests in this repository.

## Source ownership

- Treat every directory under `skills/` as canonical. Do not create runtime-specific copies of a skill.
- Keep platform-specific behavior inside a clearly named adapter or reference. Do not claim portability for a route that depends on a missing runtime tool.
- The published global-instruction files live in `global-files/`. They are examples for users, not instructions for work on this repository.
- Preserve unrelated and user-owned changes. Never commit, push, create a tag, or publish a release unless the user explicitly requests it.

## README and public copy

- Write the README in natural Russian. Explain skills through the problem they solve and the result a user gets.
- Keep the Telegram call to action near the top and keep the `x9-` prefix explanation discoverable.
- Do not hard-code the number of skills in prose; the contents of `skills/` change over time.
- After editing README, run the `humanizer-ru` scanner. If its optional Python packages are unavailable, use an ephemeral environment rather than changing global Python state.
- Keep sensitive data, personal paths, credentials, browser profiles, cookies, and tokens out of the repository.

## Plugin metadata

- Keep `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` on the same semantic version.
- Keep the plugin name `x9-agent-skills` and marketplace name `xonika9` synchronized with `scripts/check_package.py`.
- Run `claude plugin validate .` and the Codex plugin validator after changing manifests or marketplace files.

## Changelog and releases

- Update `CHANGELOG.md` for every user-visible change. Describe the outcome, not the implementation steps.
- Before a release, set the release date, bump both plugin manifests to the same `X.Y.Z`, and make sure the changelog has a matching version heading.
- After the explicitly authorized release commit has been pushed, create annotated tag `vX.Y.Z` on that exact commit and push the tag. Do not tag routine or unfinished pushes.
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
claude plugin validate .
npx skills add . --list
git diff --check
```

Confirm that root `CLAUDE.md` contains exactly `@AGENTS.md` plus a final newline.
