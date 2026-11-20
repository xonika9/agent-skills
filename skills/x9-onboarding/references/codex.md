# Codex adapter

Use this adapter only from Codex. First inspect Codex's live skill, agent, and tool
interfaces. Do not rely on remembered CLI flags, models, configuration shapes, or
filesystem discovery as runtime evidence.

Check requirements under [Runtime Checks and Guidance](declarations.md#runtime-checks-and-guidance).

## Configuration

Use `profiles/codex.toml` with `~/.codex/config.toml`. Confirm current keys, accepted
values, profiles, and precedence in the official Codex configuration reference before
making a recommendation; the installed app or CLI schema may provide additional live
evidence. Do not inspect project `.codex/config.toml` files or enumerate `[projects]`
entries encountered while parsing the user file.

Check configured model and feature availability through the current live catalog before
proposing those paths.

After approval, merge the supported paths into the user file under the
[shared configuration contract](configuration.md). Validate TOML with a parser that does
not echo values. A current session may retain old values until Codex restarts; report
that state instead of restarting it.
