# Codex adapter

Use this adapter only from Codex. First inspect Codex's live skill, agent, and tool
interfaces. Do not rely on remembered CLI flags, models, configuration shapes, or
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

Use `profiles/codex.toml` with `~/.codex/config.toml`. Confirm current keys, accepted
values, profiles, and precedence in the official Codex configuration reference before
making a recommendation; the installed app or CLI schema may provide additional live
evidence. Do not inspect project `.codex/config.toml` files or enumerate `[projects]`
entries encountered while parsing the user file.

Check configured model and feature availability through the current live catalog before
proposing those paths. The bundled `approval_policy = "never"` and
`sandbox_mode = "danger-full-access"` remove routine runtime approval and sandbox
boundaries. Enabling `desktop.realtimeVoiceScreenContextEnabled` allows screen context
during an active voice call. State those consequences in the comparison.

After approval, merge the supported paths into the user file under the
[shared configuration contract](configuration.md). Validate TOML with a parser that does
not echo values. A current session may retain old values until Codex restarts; report
that state instead of restarting it.

## Guidance

| `guidance_id` | Manual step | Expected safe evidence |
| --- | --- | --- |
| `install-skill` | Install or update the named skill using Codex's current documented flow. | Live skill catalog lists the named skill. |
| `install-command` | Install the named command using its vendor documentation. | Safe command discovery reports the command present. |
| `create-agent` | Create or enable the required agent through Codex's current interface. | Live agent catalog lists the declared component. |
| `configure-mcp` | Configure the required MCP component manually through Codex's documented interface. | Live component catalog lists MCP without exposing configuration. |
| `enable-runtime-feature` | Enable the declared Codex feature through its current documented interface. | Live catalog or schema exposes the feature. |
| `complete-user-action` | Complete the declared authorization, profile, provider, or other human-only action outside this skill. | User confirms completion, then a safe follow-up fact is available. |
