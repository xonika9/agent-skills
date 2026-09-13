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
[core status model](../SKILL.md#status-model). Dependency checks do not inspect raw
configuration.

## Configuration

Use `profiles/opencode.json` with the single existing user file at
`~/.config/opencode/opencode.jsonc` or `~/.config/opencode/opencode.json`. Inspect the
current OpenCode V2 schema and live model, agent, MCP, and provider catalogs before
proposing profile paths. Never use `opencode debug config` or another command that emits
the merged configuration: provider and MCP credentials may be included in its output.

The bundled wildcard `permissions` rule allows every action and resource without a
runtime permission boundary. State that consequence. Add model-specific agents only
when their exact provider, model, and effort variant are available. The Exa MCP entry
contains only an environment reference; applying it never proves that the variable is
set or that Exa is ready. State that `websearch.provider = "exa"` sends future search
queries to that external provider.

After approval, merge supported paths under the
[shared configuration contract](configuration.md), preserving JSONC comments and
unrelated entries. Validate through a JSONC-aware parser or a silent runtime validation
surface; do not validate with a command that prints resolved configuration or headers.

## Guidance

| `guidance_id` | Manual step | Expected safe evidence |
| --- | --- | --- |
| `install-skill` | Install or update the named skill using OpenCode's current documented flow. | Live skill catalog lists the named skill. |
| `install-command` | Install the named command using its vendor documentation. | Safe command discovery reports the command present. |
| `create-agent` | Create or enable the required agent through OpenCode's current interface. | Live agent catalog lists the declared component. |
| `configure-mcp` | Configure the required MCP component manually through OpenCode's documented interface. | Live component catalog lists MCP without exposing configuration. |
| `enable-runtime-feature` | Enable the declared OpenCode feature through its current documented interface. | Live catalog or schema exposes the feature. |
| `complete-user-action` | Complete the declared authorization, profile, provider, or other human-only action outside this skill. | User confirms completion, then a safe follow-up fact is available. |
