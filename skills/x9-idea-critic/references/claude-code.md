# Claude Code adapter

Use this adapter only when `x9-idea-critic` runs from Claude Code. Inspect the live worker tools and supported model selectors before dispatch because model aliases and delegation schemas can change.

## Opus route

Resolve a currently available Opus-family model and select it explicitly for every Opus critic. Give each fresh worker only its sealed brief and the read surfaces required by that brief. If no Opus-family model can be selected, the route failed; do not substitute the current configured model or another Claude family.

## GPT route

Load `x9-codex-delegation`; it owns current Codex invocation, model selection, transport, and delegation-log mechanics. A failed or unavailable Codex route remains a GPT-route failure under the core skill's degradation rules.
