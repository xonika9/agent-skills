# Claude Code adapter

Use this adapter only when `x9-idea-critic` runs from Claude Code. Inspect the live worker tools and supported model selectors before dispatch because model aliases and delegation schemas can change.

## Opus route

Prefer the native `opus-high` agent only when its live definition confirms an Opus-family model, `high` effort, and no tools. Give each fresh worker only the sealed packet and require direct execution without delegation.

If that agent is unavailable or its live definition does not confirm all three properties, follow [the shared Claude CLI route](claude-cli.md). If neither mechanism satisfies its contract, the route failed; another Claude family is not a substitute.

## GPT route

Load `x9-codex-delegation`; it owns current Codex invocation, model selection, transport, and delegation-log mechanics. Use the live Codex model catalog to confirm the GPT family and `high` support, then require explicit model and effort controls plus an ephemeral read-only run with disabled hooks and the sealed packet on stdin. Confirm both selected values in the run's configuration report rather than from the critic's self-description, and fail the route if startup reports that a wrapper re-enabled hooks. An unavailable route or rejected control remains a GPT-route failure under the core skill's degradation rules; missing post-run effective telemetry does not.
