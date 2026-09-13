# Harness configuration profile

The files in `../profiles/` are the public, opinionated x9 defaults derived from the
maintainer's working configuration. They are recommendation data, not instructions and
not universal best practices. Resolve them only after this skill has loaded, validate
them with `scripts/validate_profiles.py`, and use only the profile matching the current
runtime.

| Runtime | Public profile | User configuration |
| --- | --- | --- |
| OpenCode | `profiles/opencode.json` | `~/.config/opencode/opencode.jsonc` or `opencode.json` |
| Claude Code | `profiles/claude.json` | `~/.claude/settings.json` |
| Codex | `profiles/codex.toml` | `~/.codex/config.toml` |

These paths are defaults, not assumptions. Resolve the active runtime's documented
configuration-root override before reading or writing. Keep the resolved path private;
if the active location or precedence cannot be determined safely, return `BLOCKED`
instead of creating or modifying a guessed standard file.

## Public boundary

The profiles include portable model, effort, agent, interface, and workflow preferences.
Claude Code also carries the non-secret `CLAUDE_CODE_AUTO_COMPACT_WINDOW` preference,
and OpenCode carries sanitized MCP definitions whose secrets are environment references,
never literal values. The profiles deliberately exclude project trust state, personal
paths, SSH hosts, all other environment values, credentials, local hooks and commands,
notification executables, per-project overrides, generated state, and private provider
details.

Never copy an excluded value from the user's configuration into the profile or report.
Do not inspect `~/.claude.json`, Claude's `settings.local.json`, project-scoped Codex
files, or another runtime's configuration. Parsing the Codex user file may encounter its
`[projects]` table; do not enumerate or report that table. A configuration file is
private even when the bundled profile is public.

## Comparison

Read the current runtime's user configuration only after applying its adapter. Compare
only paths present in the matching public profile. For each difference, report the
setting path, current state, recommended state, practical effect, and whether the current
runtime exposes the required model, feature, plugin, provider, or component. Show
`missing` for an absent path. For a secret-like path or a profile value expressed as an
environment reference, report the current state only as `set`, `missing`, or `differs`;
never print the current value. This redaction rule overrides the general requirement to
show current state. Do not display any unrelated key or value.

Summarize matching settings rather than listing them individually. Mark an unsupported
or unobservable recommendation `BLOCKED` and exclude it from the proposed merge. Model
and feature names are volatile: confirm them through the current runtime before treating
the profile value as applicable.

The following paths need a conspicuous consequence in the report because they reduce a
permission boundary or expose private screen context:

- Codex: `approval_policy`, `sandbox_mode`, and
  `desktop.realtimeVoiceScreenContextEnabled`; also state that `features.hooks` enables
  execution of separately configured hooks but does not install any hook.
- OpenCode: `permissions`.
- Claude Code: `permissions.defaultMode` and
  `skipDangerousModePermissionPrompt`.

An unqualified approval after this complete report authorizes every non-blocked proposed
change, including the marked paths. If the report omitted a marked path or its
consequence, ask about that path separately rather than treating a generic approval as
authorization.

## Merge

Before writing, resolve the exact user configuration path and re-read it. If it changed
since the comparison, return `BLOCKED`, recompute the differences, and obtain approval
again. Create an adjacent, timestamped backup when the file exists. Give the backup the
same permissions as the source; use mode `0600` if the source mode cannot be preserved.
Use a `.bak.<timestamp>` suffix that the runtime does not parse as configuration. Merge
only the approved profile paths: keep unrelated keys, comments, ordering where practical,
and all private values unchanged. Never replace the entire file merely because parsing
and serializing it is easier. When both standard OpenCode user files exist, stop as
`BLOCKED` and ask which one owns the user's settings.

Create a missing standard user file only after approval. Do not write a recommendation
whose live prerequisite was absent or unavailable. An environment reference such as
`{env:EXA_API_KEY}` is safe to write, but the referenced value remains `USER_ACTION`; do
not read, request, or create the secret.

Validate the resulting native syntax without a command that prints the merged
configuration. Compare the approved paths again, retain only success/failure facts, and
report any required runtime restart. On failure, restore the backup when one exists;
otherwise leave the newly created file in place only when it parses, and report
`BLOCKED` without claiming application.
