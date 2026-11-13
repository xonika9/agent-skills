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

Contributors add user-visible changes to `Unreleased`. Releases use calendar versions
`YY.M.D.N`, for example `26.11.3.1`: the date in `Europe/Moscow`, followed by
a positive sequence starting at 1 each day. The year has two digits; month, day,
and sequence have no leading zeros. Compatibility changes do not determine the number.

After fetching public tags, `python3 scripts/prepare_release.py --next-version`
prints the next number. A release request authorizes automatic number selection
without a separate confirmation. Both plugin manifests, the changelog, and the
`v`-prefixed tag use that number; the workflow owns tag creation. Historical
semantic-version releases remain unchanged. Describe incompatible changes and
required migration under `Breaking changes` and `Install / update`.

Release metadata and publication are enforced by [`scripts/prepare_release.py`](scripts/prepare_release.py), the [validation workflow](.github/workflows/validate.yml), and the [release workflow](.github/workflows/release.yml).

## Validation

Run the focused tests for your change. Before submitting a package-wide change, run:

```bash
for skill in skills/*; do
  python3 skills/x9-skill-creator/scripts/validate.py \
    --runtime portable --runtime claude --runtime codex "$skill"
done
python3 skills/x9-skill-creator/scripts/validate.py \
  --runtime claude --runtime codex .claude/skills/release

python3 skills/x9-skill-creator/scripts/test_validate.py
python3 skills/x9-onboarding/scripts/test_validate_onboarding.py
python3 skills/x9-onboarding/scripts/validate_onboarding.py skills
python3 skills/x9-onboarding/scripts/test_validate_profiles.py
python3 skills/x9-onboarding/scripts/validate_profiles.py
python3 skills/x9-opencode-sessions/scripts/test_opencode_sessions.py
python3 skills/x9-agent-instructions/scripts/test_check_globals.py
python3 skills/x9-diagrams/scripts/test_check_scene.py
python3 skills/x9-diagrams/scripts/test_check_svg.py
python3 skills/x9-diagrams/scripts/test_summarize_source.py
python3 skills/x9-okf-docs/scripts/test_okf.py
python3 skills/x9-personal-vault/scripts/test_apply_plan.py
python3 skills/x9-research/scripts/test_validate_html.py
python3 skills/x9-architecture-scout/scripts/test_validate_report.py
python3 .claude/skills/release/scripts/check_global_files.py --published-only
printf '@AGENTS.md\n' | cmp - CLAUDE.md
python3 scripts/test_check_package.py
python3 scripts/check_package.py
python3 scripts/check_public.py
python3 scripts/test_prepare_release.py
python3 scripts/prepare_release.py --check
claude plugin validate .claude-plugin/marketplace.json
claude plugin validate .claude-plugin/plugin.json
npx skills add . --list
git diff --check
```

CI runs the same deterministic package checks plus Gitleaks over the full Git history. The
Claude validators and `npx skills add . --list` remain local compatibility smoke tests because
their CLIs are not repository dependencies.

`scripts/check_package.py` is the repository-level gate for shared Claude Code and Codex metadata, marketplace policy, and declared assets. A runtime-bundled Codex validator is a useful additional check, but is not a repository dependency.

## Pull requests

A useful pull request includes:

- a short, outcome-focused title;
- the reason for the change;
- exact checks or live scenarios run;
- known limitations and runtime-specific behavior;
- screenshots or recordings only when they are real, sanitized, and relevant.

By participating, you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
