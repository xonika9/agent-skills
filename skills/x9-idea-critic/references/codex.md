# Codex adapter

Use this adapter only when `x9-idea-critic` runs from Codex. Inspect only the selected route's live interface before dispatch because model aliases and worker parameters can change.

## Claude route

Follow [the shared Claude CLI route](claude-cli.md).

## GPT route

Follow the active global subagent contract, then use the native worker interface with `fork_turns: "none"`. Confirm the core skill's selected GPT model and `high` support in the live model catalog and worker schema, and set both explicitly rather than inheriting the parent model. Pass only the sealed packet and require direct execution without tools or delegation. `fork_turns: "none"` removes the parent conversation, not system, developer, or repository instructions. Record accepted selectors under the core telemetry rules. If either selector is unavailable or rejected, the route failed rather than falling back to another model or provider.
