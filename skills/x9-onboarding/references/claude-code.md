# Claude Code adapter

Use this adapter only from Claude Code. First inspect Claude Code's live skill, agent,
and tool interfaces. Do not rely on remembered CLI flags, models, configuration shapes, or
filesystem discovery as runtime evidence.

For `skill-present`, accept only a live catalog entry whose resolved physical path remains
under the package `skills` root. For `command-present`, a safe shell discovery such as
`command -v` may establish presence without launching the command; retain only its name
and present/absent result. Check `agent`, `mcp`, `active-skill-catalog`, and
`native-subagents` exclusively through an available live catalog or schema. Classify
unavailable interfaces, private-data boundaries, and restart evidence with the
[core status model](../SKILL.md#status-model). Dependency checks do not inspect raw
configuration.

## Configuration

Use `profiles/claude.json` with `~/.claude/settings.json`. Confirm current setting names,
scope, precedence, model aliases, and installed plugin identifiers through Claude Code's
official settings documentation and live interfaces before proposing profile paths. Do
not read or edit `~/.claude.json`, `settings.local.json`, project settings, managed
settings, SSH data, unrelated environment values, hooks, or status-line commands.

The sole environment path in the public profile is
`env.CLAUDE_CODE_AUTO_COMPACT_WINDOW`. Compare and merge that exact path without reading,
reporting, or modifying any other environment entry.

The bundled `permissions.defaultMode = "bypassPermissions"` bypasses normal permission
prompts. `skipDangerousModePermissionPrompt = true` also suppresses its warning. State
both consequences. Apply an `enabledPlugins` entry only when the exact plugin is already
installed; this skill does not install plugins or marketplaces.

After approval, merge supported paths under the
[shared configuration contract](configuration.md). Validate the result as JSON without
echoing values. Report when a new Claude Code session is required; do not start one.

## Guidance

| `guidance_id` | Manual step | Expected safe evidence |
| --- | --- | --- |
| `install-skill` | Install or update the named skill using Claude Code's current documented flow. | Live skill catalog lists the named skill. |
| `install-command` | Install the named command using its vendor documentation. | Safe command discovery reports the command present. |
| `create-agent` | Create or enable the required agent through Claude Code's current interface. | Live agent catalog lists the declared component. |
| `configure-mcp` | Configure the required MCP component manually through Claude Code's documented interface. | Live component catalog lists MCP without exposing configuration. |
| `enable-runtime-feature` | Enable the declared Claude Code feature through its current documented interface. | Live catalog or schema exposes the feature. |
| `complete-user-action` | Complete the declared authorization, profile, provider, or other human-only action outside this skill. | User confirms completion, then a safe follow-up fact is available. |
