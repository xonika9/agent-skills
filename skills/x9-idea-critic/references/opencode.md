# OpenCode adapter

Use this adapter only when `x9-idea-critic` runs from OpenCode. Before dispatching a selected route, inspect only its live interface: `claude --help` for Opus or the subagent catalog for GPT. Available agents, model assignments, and CLI flags can change.

## Opus route

Run every Opus critic in a fresh non-persistent Claude CLI session. Live discovery must confirm equivalents for non-persistent print execution, explicit Opus-family model selection, `high` effort, and sealed-brief input; if any load-bearing control is unavailable, the route failed. Do not inherit the user's configured Claude model or effort.

When the live CLI accepts the brief on stdin, materialize only the sealed brief in an OS temporary file created with `mktemp`, restrict it to the current user, and pass it through stdin rather than argv. Install cleanup with a shell trap or equivalent `finally` block before writing the brief, never place the transport file in the repository or logs, and treat verified deletion after success, failure, or interruption as part of route completion.

## GPT route

Only the user-facing root session may launch a native OpenCode subagent for a GPT critic. Use `sol-high` only when its live catalog entry explicitly confirms a GPT-family model at `high` effort; do not infer either property from the agent name. Each critic runs in a fresh child session with only the sealed brief and its explicit evidence locations, and the child executes the critique directly without further delegation.

If `sol-high` is unavailable or its live catalog entry does not confirm both properties, the route failed under the core skill's degradation rules; do not substitute another agent or provider family.
