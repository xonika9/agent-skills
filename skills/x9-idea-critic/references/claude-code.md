# Claude Code adapter

Use this adapter only when `x9-idea-critic` runs from Claude Code. Inspect the live worker tools and supported model selectors before dispatch because model aliases and delegation schemas can change.

## Opus route

Resolve a currently available Opus-family model and select it explicitly at `high` effort for every Opus critic. Give each fresh worker only its sealed brief and the read surfaces required by that brief. If no Opus-family model can be selected or `high` effort cannot be enforced, the route failed; do not substitute the current configured model or another Claude family.

## GPT route

Load `x9-codex-delegation`; it owns current Codex invocation, model selection, transport, and delegation-log mechanics. Confirm that the effective configured model belongs to the GPT family, or use its explicit model override to select a live-confirmed GPT model. Require its Codex configuration override for `high` reasoning effort rather than inheriting effort from user configuration. An unavailable route, an unconfirmed GPT-family model, or inability to enforce `high` effort remains a GPT-route failure under the core skill's degradation rules.
