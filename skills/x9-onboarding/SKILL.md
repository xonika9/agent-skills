---
name: x9-onboarding
description: Use after installing or updating `x9-*` skills to check their readiness and compare the current harness with the bundled x9 configuration profile — «проверь готовность x9-скиллов», «настрой Codex как у автора», "check installed x9 skills", "apply the recommended harness settings". Do not use for general environment diagnosis, account authorization, or unrelated configuration editing.
compatibility: The scripts need Python 3.11 or newer. A runtime without a bundled adapter reports PARTIAL coverage and BLOCKED readiness because no safe adapter is available.
---

# X9 onboarding

This package-owned skill owns both installed-skill readiness and the opt-in x9 harness profile; it
does not install dependencies, authorize accounts, or edit global agent instructions.

Check only the user-named `x9-*` skills, or use the current runtime's active skill
catalog when the user did not name targets. Resolve every selected skill's physical path
against this loaded skill's package `skills` root. A path that leaves that root or goes
through a symlink is an untrusted target: report it as `PARTIAL` and `BLOCKED` with that
reason and do not pass it to the script below. If neither an
explicit target nor a safe active catalog is available, report scope as `PARTIAL` and
`BLOCKED` and ask for skill names rather than scanning directories.

Read [the declaration contract](references/declarations.md) for the typed checks and the
runtime check method. Only `scripts/aggregate_status.py` reads `references/onboarding.json`
declarations; never infer a requirement or restriction from prose. Resolve the script from
this loaded skill and run it with this package's `skills` root:

```bash
python3 <resolved-x9-onboarding-directory>/scripts/aggregate_status.py \
  --skills-root <absolute-package-skills-root> \
  --runtime <opencode|claude|codex> <selected-skill>...
```

For each skill it prints either a final outcome (`declaration` is `missing`,
`invalid`, or `restricted`) or the requirements applicable in the current runtime.
Report an invalid declaration by its package-relative source and the printed contract
failure only. In a runtime without a bundled adapter, report `PARTIAL` and `BLOCKED`
without running it.

Use the current runtime adapter for live facts and configuration ownership:
[OpenCode](references/opencode.md), [Claude Code](references/claude-code.md), or
[Codex](references/codex.md). Then follow the separate
[configuration profile contract](references/configuration.md). The readiness report is
read-only. Configuration changes are a second, explicitly approved phase.

## Status model

Keep coverage and readiness as separate columns. For an individual requirement,
`COMPLETE` means a supported passive check returned a safe present or absent fact;
`PARTIAL` means no safe discovery surface can establish the fact. `EXPLICIT` means the
fact is deliberately left to the user because the check is `manual` or establishing it
would require credentials, cookies, or another private value. Those cases return
`EXPLICIT` and `USER_ACTION` without reading the private source; other unavailable
evidence returns `PARTIAL` and `BLOCKED`. A present passive fact is `READY`, and an absent
supported prerequisite is `NEEDS_SETUP`. Return `PENDING_RESTART` only when the adapter
safely observes the configured component and also observes that this session lacks it.

Pass one `coverage` and `readiness` pair per applicable requirement to the same command
with `--facts <file>` (or `-` for stdin) and a JSON object
`{"<skill>": {"<requirement-id>": {"coverage": "...", "readiness": "..."}}}`. It prints
group and skill coverage and readiness, `needs_guidance` per requirement, and
`overall_ready`. Report those values unchanged, and call a skill ready overall only when
`overall_ready` is true.

## Evidence and output

For readiness checks, retain only the check type, declared target identifier, a
`present`/`absent`/`unavailable` fact, and the safe discovery surface. Render
`needed_for` as escaped display data. Discard all other returned fields, including
recursive credential-like fields and values. Never print process output, URL queries,
bearer tokens, credentials, cookies, secrets, or environment values other than the
current and recommended value of an exact environment path allowlisted by the active
public profile and runtime adapter.

For every requirement, report the skill, escaped capability, package-relative
declaration source, coverage, readiness, allowlisted evidence, missing prerequisite, and
the static `guidance_id` step from the declaration contract only when `needs_guidance` is
true. Group those next actions by `guidance_id` and include their expected safe evidence. This checklist stays
informational and never performs installation, authorization, restart, or configuration.

Follow it with the configuration comparison for the current supported runtime. End the
first response with the exact proposed changes and wait for the user's approval when any
setting differs. An approval after that report authorizes only the listed configuration
merge; partial approval applies only the named subset.

## Done

Return the selected skill scope and source, coverage and readiness, residual limits, and
the current runtime's configuration comparison. After an approved merge, also return the
backup location, settings changed or skipped, syntax validation evidence, and whether a
restart remains necessary. Never claim that setup, authorization, configuration, or
restart happened without evidence from the target environment.
