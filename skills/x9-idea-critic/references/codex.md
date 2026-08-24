# Codex adapter

Use this adapter only when `x9-idea-critic` runs from Codex. Inspect the live Claude CLI help and native worker schema before dispatch because flags, model aliases, and worker parameters can change.

## Opus route

Run every Opus critic in a fresh non-persistent Claude CLI session. Live discovery must confirm equivalents for non-persistent print execution, explicit Opus-family model selection, `high` effort, and sealed-brief input; if any load-bearing control is unavailable, the route failed. Do not inherit the user's configured Claude model or effort.

When the live CLI accepts the brief on stdin, materialize only the sealed brief in an OS temporary file created with `mktemp`, restrict it to the current user, and pass it through stdin rather than argv. Install cleanup with a shell trap or equivalent `finally` block before writing the brief, never place the transport file in the repository or logs, and treat verified deletion after success, failure, or interruption as part of route completion.

## GPT route

Follow the active global subagent contract, then use the native worker interface with `fork_turns: "none"`. Select a supported GPT-family model through the live schema and set its effort to `high`. If a GPT-family model cannot be selected or `high` effort cannot be enforced, the route failed rather than falling back to another provider.
