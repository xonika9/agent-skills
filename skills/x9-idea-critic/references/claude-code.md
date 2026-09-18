# Claude Code adapter

Use this adapter only when `x9-idea-critic` runs from Claude Code. Inspect the live worker tools and supported model selectors before dispatch because model aliases and delegation schemas can change.

## Claude route

Follow [the shared Claude CLI route](claude-cli.md). No custom Claude Code agent is required.

## GPT route

Load `x9-codex-delegation`; it owns current Codex invocation, transport, and delegation-log mechanics. Supply `gpt_model` from the core skill's configuration explicitly rather than adopting that skill's configured-model preference. Use the live Codex model catalog to confirm the selected model and `high` support, then require explicit model and effort controls plus an ephemeral read-only run with disabled hooks and the sealed packet on stdin. Confirm both selected values in the run's configuration report rather than from the critic's self-description, and fail the route if startup reports that a wrapper re-enabled hooks. An unavailable route or rejected control remains a GPT-route failure under the core skill's degradation rules; apply the core telemetry rules to missing post-run evidence.
