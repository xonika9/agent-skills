# OpenCode adapter

Use this adapter only when `x9-idea-critic` runs from OpenCode. Before dispatching a selected route, inspect only its live interface: `claude --help` for Opus or the subagent catalog for GPT. Available agents and model assignments can change.

## Opus route

Follow [the shared Claude CLI route](claude-cli.md).

## GPT route

Only the user-facing root session may launch a native OpenCode subagent for a GPT critic. Use `sol-high` only when its live catalog entry explicitly confirms a GPT-family model at `high` effort; do not infer either property from the agent name. Each critic runs in a fresh child session with only the sealed packet and an explicit instruction to use no tools and execute directly without further delegation. The absence of per-call tool or file ACLs is a runtime limitation, not route failure, because source content is already bounded by the packet.

Record the catalog assignment as control evidence; missing post-run effective-model or effort telemetry is `NOT_PROVEN`, not route failure. If `sol-high` is unavailable or its live catalog entry does not confirm both properties, the route failed under the core skill's degradation rules; do not substitute another agent or provider family.
