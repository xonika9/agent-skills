# Claude Code adapter

Use this adapter only from Claude Code. First inspect Claude Code's live skill, agent,
and tool interfaces. Do not rely on remembered CLI flags, models, configuration shapes, or
filesystem discovery as runtime evidence.

For `skill-present`, accept only a live catalog entry whose resolved physical path remains
under the package `skills` root. For `command-present`, a safe shell discovery such as
`command -v` may establish presence without launching the command; retain only its name
and present/absent result. Check `agent`, `mcp`, `active-skill-catalog`, and
`native-subagents` exclusively through an available live catalog or schema. If it is not
available without reading raw configuration, return `PARTIAL` and `BLOCKED`.

Only emit `PENDING_RESTART` when a safe live interface shows a configured component while
the current catalog does not expose it. Do not turn an unknown configuration state into a
restart conclusion.

## Guidance

| `guidance_id` | Manual step | Expected safe evidence |
| --- | --- | --- |
| `install-skill` | Install or update the named skill using Claude Code's current documented flow. | Live skill catalog lists the named skill. |
| `install-command` | Install the named command using its vendor documentation. | Safe command discovery reports the command present. |
| `create-agent` | Create or enable the required agent through Claude Code's current interface. | Live agent catalog lists the declared component. |
| `configure-mcp` | Configure the required MCP component manually through Claude Code's documented interface. | Live component catalog lists MCP without exposing configuration. |
| `enable-runtime-feature` | Enable the declared Claude Code feature through its current documented interface. | Live catalog or schema exposes the feature. |
| `complete-user-action` | Complete the declared authorization, profile, provider, or other human-only action outside this skill. | User confirms completion, then a safe follow-up fact is available. |
