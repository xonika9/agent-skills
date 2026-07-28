# Contributing to x9 Agent Skills

Thanks for helping make the skills more reliable. Focused fixes, reproducible compatibility findings, clearer instructions, and well-scoped new skills are welcome.

## Before opening an issue

- Search existing issues and the [changelog](CHANGELOG.md).
- Confirm which agent, version, operating system, and installation model you used.
- Remove tokens, cookies, personal paths, private repository names, browser-profile data, and proprietary content from logs and examples.
- Use [private vulnerability reporting](https://github.com/xonika9/agent-skills/security/advisories/new) for sensitive security findings.

## Proposing a change

Keep each pull request focused on one outcome. Explain the problem, the observable behavior before and after, runtime assumptions, and how you verified the result.

For a new or changed skill:

- Keep its canonical source under `skills/<skill-name>/`.
- Use the `x9-` prefix and lowercase hyphen-case.
- State when the skill should and should not trigger.
- Put long reference material in `references/` and deterministic helpers in `scripts/`.
- Do not claim cross-agent compatibility you have not checked.
- Update both READMEs and `CHANGELOG.md` when public behavior changes.

## Versioning

Contributors add user-visible changes to `Unreleased`; the maintainer confirms the release version. The strongest change since the latest public tag determines the bump:

- `PATCH`: backward-compatible fixes and corrections only.
- `MINOR` while the project is `0.x`: new capabilities or any intentional change to public behavior or contracts, including incompatible pre-1.0 changes.
- `1.0.0`: an explicit maintainer declaration that the public contracts are stable.
- After `1.0.0`, `MAJOR`: incompatible public-contract changes; `MINOR`: backward-compatible capabilities; `PATCH`: backward-compatible fixes.

Release metadata and publication are enforced by [`scripts/prepare_release.py`](scripts/prepare_release.py), the [validation workflow](.github/workflows/validate.yml), and the [release workflow](.github/workflows/release.yml).

## Validation

Run the focused tests for your change. Before submitting a package-wide change, run:

```bash
for skill in skills/*; do
  python3 skills/x9-skill-creator/scripts/validate.py "$skill"
done

python3 skills/x9-skill-creator/scripts/test_validate.py
python3 skills/x9-okf-adapt/scripts/test_okf.py
python3 scripts/check_package.py
python3 scripts/check_public.py
python3 scripts/prepare_release.py --check
claude plugin validate .claude-plugin/marketplace.json
claude plugin validate .claude-plugin/plugin.json
npx skills add . --list
git diff --check
```

`scripts/check_package.py` is the repository-level gate for shared Claude Code and Codex metadata, marketplace policy, and declared assets. A runtime-bundled Codex validator is a useful additional check, but is not a repository dependency.

## Pull requests

A useful pull request includes:

- a short, outcome-focused title;
- the reason for the change;
- exact checks or live scenarios run;
- known limitations and runtime-specific behavior;
- screenshots or recordings only when they are real, sanitized, and relevant.

By participating, you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
