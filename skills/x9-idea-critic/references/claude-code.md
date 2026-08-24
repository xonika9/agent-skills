# Claude Code adapter

Use this adapter only when `x9-idea-critic` runs from Claude Code. Inspect the live worker tools and supported model selectors before dispatch because model aliases and delegation schemas can change.

## Opus route

Prefer the native `opus-high` agent only when its live definition confirms both an Opus-family model and `high` effort. Give each fresh worker only its sealed brief and the read surfaces required by that brief.

If that agent is unavailable or its live definition does not confirm both properties, use a fresh non-persistent Claude CLI session only when the live interface supports explicit Opus-family selection, `high` effort, and sealed-brief input. If neither mechanism can enforce both model family and effort, the route failed; asking for `high` in the brief is not enforcement, and another Claude family is not a substitute.

## GPT route

Load `x9-codex-delegation`; it owns current Codex invocation, model selection, transport, and delegation-log mechanics. Confirm that the effective configured model belongs to the GPT family, or use its explicit model override to select a live-confirmed GPT model. Require its Codex configuration override for `high` reasoning effort rather than inheriting effort from user configuration. An unavailable route, an unconfirmed GPT-family model, or inability to enforce `high` effort remains a GPT-route failure under the core skill's degradation rules.
