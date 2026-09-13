# OpenCode adapter

Use this adapter only from OpenCode. First inspect the current session's live skill,
agent, and tool catalogs. Their names, schemas, and availability are runtime facts; do
not derive them from files, remembered commands, or a package directory scan.

For `skill-present`, accept only a catalog entry whose resolved physical path remains
under the package `skills` root. For `command-present`, a safe shell discovery such as
`command -v` may establish presence without starting the discovered program; retain only
the command name and present/absent result. Check `agent`, `mcp`,
`active-skill-catalog`, and `native-subagents` only through a live catalog or schema.
Classify unavailable interfaces, private-data boundaries, and restart evidence with the
[core status model](../SKILL.md#status-model); do not inspect raw configuration.

## Guidance

| `guidance_id` | Manual step | Expected safe evidence |
| --- | --- | --- |
| `install-skill` | Install or update the named skill using OpenCode's current documented flow. | Live skill catalog lists the named skill. |
| `install-command` | Install the named command using its vendor documentation. | Safe command discovery reports the command present. |
| `create-agent` | Create or enable the required agent through OpenCode's current interface. | Live agent catalog lists the declared component. |
| `configure-mcp` | Configure the required MCP component manually through OpenCode's documented interface. | Live component catalog lists MCP without exposing configuration. |
| `enable-runtime-feature` | Enable the declared OpenCode feature through its current documented interface. | Live catalog or schema exposes the feature. |
| `complete-user-action` | Complete the declared authorization, profile, provider, or other human-only action outside this skill. | User confirms completion, then a safe follow-up fact is available. |
