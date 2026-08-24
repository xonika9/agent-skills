# Codex adapter

Use this adapter only when `x9-idea-critic` runs from Codex. Inspect only the selected route's live interface before dispatch because model aliases and worker parameters can change.

## Opus route

Follow [the shared Claude CLI route](claude-cli.md).

## GPT route

Follow the active global subagent contract, then use the native worker interface with `fork_turns: "none"`. Select a supported GPT-family model through the live schema, set its effort to `high`, pass only the sealed packet, and require direct execution without tools or delegation. `fork_turns: "none"` removes the parent conversation, not system, developer, or repository instructions. Record accepted selectors as control evidence; missing post-run effective telemetry is `NOT_PROVEN`, not route failure. If either selector is unavailable or rejected, the route failed rather than falling back to another provider.
