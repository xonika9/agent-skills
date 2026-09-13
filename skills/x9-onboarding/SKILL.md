---
name: x9-onboarding
description: Use after installing or updating `x9-*` skills to check their readiness and compare the current harness with the bundled x9 configuration profile — «проверь готовность x9-скиллов», «настрой Codex как у автора», "check installed x9 skills", "apply the recommended harness settings". Do not use for general environment diagnosis, account authorization, or unrelated configuration editing.
compatibility: Supports OpenCode, Claude Code, and Codex through runtime adapters. Other runtimes report PARTIAL coverage and BLOCKED readiness because no safe adapter is available.
---

# X9 onboarding

This package-owned skill is model-invoked in OpenCode, Claude Code, and Codex. Its
portable claim is structural Agent Skills compatibility only, not proven invocation
behavior. It owns both installed-skill readiness and the opt-in x9 harness profile; it
does not install dependencies, authorize accounts, or edit global agent instructions.

Check only the user-named `x9-*` skills, or use the current runtime's active skill
catalog when the user did not name targets. Resolve every selected skill's physical path
against this loaded skill's package `skills` root. Read a declaration only when its
resolved path remains below that root; never read an external path or symlink target.
Report an untrusted target as `PARTIAL` and `BLOCKED` with that reason. If neither an
explicit target nor a safe active catalog is available, report scope as `PARTIAL` and
`BLOCKED` and ask for skill names rather than scanning directories.

Read [the declaration contract](references/declarations.md) for trusted
`references/onboarding.json` data. A missing declaration means that skill has no
declared external requirements or runtime restriction: report `COMPLETE` and `READY`;
never infer a requirement from prose. An unreadable or invalid declaration is `PARTIAL`
and `BLOCKED`; report only its package-relative source and contract failure, not its
contents. If the current runtime is absent from `supported_runtimes`, report `COMPLETE`
and `BLOCKED` before requirement filtering. Otherwise filter a declaration to the
current runtime before checking it.

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

Collapse requirements with the same `group` into one required alternative before
aggregating a skill. A `COMPLETE` and `READY` member makes its group `COMPLETE` and
`READY`, regardless of unresolved unused alternatives. With no ready member, choose
group readiness in this order: `PENDING_RESTART`, `NEEDS_SETUP`, `USER_ACTION`,
`BLOCKED`; choose group coverage as `PARTIAL` when any member is partial, otherwise
`EXPLICIT` when any member is explicit, otherwise `COMPLETE`.

Compute skill coverage over the collapsed groups and every ungrouped row, including
optional rows: `PARTIAL` when any unit is partial, otherwise `EXPLICIT` when any unit is
explicit, otherwise `COMPLETE`; an empty set is `COMPLETE`. Compute base readiness from
required ungrouped rows and required groups only, with precedence `BLOCKED`,
`USER_ACTION`, `PENDING_RESTART`, `NEEDS_SETUP`, `READY`; an empty set is `READY`.
Optional rows remain visible and affect coverage without blocking base readiness. Never
present a `READY` base result as overall readiness when coverage is `PARTIAL` or
`EXPLICIT`.

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
the adapter's static `guidance_id` step only when the row is not `READY` and is not an
unused member of a `READY` group. In preparation mode, group those next actions by
`guidance_id` and include their expected safe evidence. This checklist stays
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
