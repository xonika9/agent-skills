# Claude Code adapter

Use this adapter only from Claude Code. First inspect Claude Code's live skill, agent,
and tool interfaces. Do not rely on remembered CLI flags, models, configuration shapes, or
filesystem discovery as runtime evidence.

Check requirements under [Runtime Checks and Guidance](declarations.md#runtime-checks-and-guidance).

## Configuration

Use `profiles/claude.json` with `~/.claude/settings.json`. Confirm current setting names,
scope, precedence, model aliases, and installed plugin identifiers through Claude Code's
official settings documentation and live interfaces before proposing profile paths. Do
not read or edit `~/.claude.json`, `settings.local.json`, project settings, managed
settings, SSH data, unrelated environment values, hooks, or status-line commands.

The sole environment path in the public profile is
`env.CLAUDE_CODE_AUTO_COMPACT_WINDOW`. Compare and merge that exact path without reading,
reporting, or modifying any other environment entry.

Apply an `enabledPlugins` entry only when the exact plugin is already installed; this
skill does not install plugins or marketplaces.

After approval, merge supported paths under the
[shared configuration contract](configuration.md). Validate the result as JSON without
echoing values. Report when a new Claude Code session is required; do not start one.
