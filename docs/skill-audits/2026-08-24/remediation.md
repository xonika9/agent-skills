# August audit remediation

Date: 2026-08-24

This note reconciles the two Claude Code, Codex, and OpenCode repository-audit runs. Findings
were rechecked against the current worktree before changes were applied.

## Fixed

| Area | Resolution |
|---|---|
| OpenCode session metadata | `x9-opencode-sessions` now preserves `location.directory`, `location.workspaceID`, and `subpath` while excluding top-level text from internal `skill` messages. |
| Shared plugin metadata | `check_package.py` now compares every shared Claude Code/Codex manifest field, validates keywords, and pins each marketplace's schema-specific category value. A regression test covers drift. |
| Global instruction scope | `x9-agent-instructions` and `check_globals.py` now include OpenCode alongside Claude Code and Codex. |
| Published and installed globals | CI checks the three published shared cores. The local release gate additionally requires each installed global file to match its corresponding published source byte-for-byte. |
| Validation documentation | `CONTRIBUTING.md` now lists the deterministic CI tests and distinguishes local external-CLI smoke tests from repository-owned gates. |
| Private release skill | Its metadata now satisfies the validator, CI validates it for Claude Code and Codex, and its candidate inventory includes the installed OpenCode global file. |
| Changelog coverage | Production package/release scripts, workflows, and the release contract are now release-relevant; test-only and auxiliary files remain exempt. The repository instructions describe both tagged-development and untagged-release behavior. |
| Global-file installation | Both READMEs name the standard destination for each harness and retain the warning against overwriting existing machine-specific instructions. |

## Kept by design

| Finding | Decision |
|---|---|
| Claude and Codex marketplace category casing differs | The two schemas use different values. Both are now validated explicitly instead of forced to match. |
| Claude validators and `npx skills add . --list` are absent from CI | They remain local compatibility smoke tests because those external CLIs are not repository dependencies. |
| Installed personal globals cannot be checked in CI | CI checks repository-owned files; the full installed/published comparison remains a maintainer release gate. |
| Release-note semantic coverage is manual | `prepare_release.py` supplies the changed-file audit, while the release skill owns the meaning-level reconciliation. Automating prose completeness would create false confidence. |
| Existing GitHub Release exits before checking the tag against the new head SHA | This is intentional: later `main` commits still use the already released version, whose tag must remain on the historical release commit. |
| Root `CLAUDE.md` is not plugin context | It is the repository-local import of `AGENTS.md`, not a file intended for plugin distribution. |
| Branch protection is not proven by workflow files | GitHub rulesets are external state and remain outside repository-only evidence. |

## Verification

- `x9-opencode-sessions`: 16 unit tests.
- Shared package metadata regression tests and `check_package.py`.
- Changelog coverage tests and `prepare_release.py --check`.
- `x9-agent-instructions` regression tests and the three-runtime installed global check.
- Portable skill validation for the public package plus Claude Code/Codex validation for the private release skill.
