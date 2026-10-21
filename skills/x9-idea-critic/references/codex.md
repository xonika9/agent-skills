# Codex adapter

Use this adapter only when `x9-idea-critic` runs from Codex. Inspect only the selected route's live interface before dispatch because model aliases and worker parameters can change.

## Claude route

Follow [the shared Claude CLI route](claude-cli.md).

## GPT route

Follow the active global subagent contract and discover the permitted worker interfaces and live model catalog. Confirm `gpt_model` and `gpt_effort` from the core configuration and apply both as explicit execution settings. Use a native worker with `fork_turns: "none"` only when that route is permitted and can apply both settings; otherwise use an available permitted orchestrator-owned fresh worker route. Pass only the sealed packet and require direct execution without tools or delegation. A fresh worker omits the parent conversation, not necessarily system, developer, or repository instructions. Record accepted selectors under the core telemetry rules. If no permitted route can apply both settings, the GPT route failed rather than falling back to another model, effort, or provider.

## Project scout

Run `codex exec` with the model and effort from the scout's isolation rule, `-s read-only`, `--ephemeral`, hooks disabled through the live feature control, the repository root as working directory, and the [scout brief](project-scout.md) on stdin through the transport lifecycle in [the Claude CLI route](claude-cli.md). Confirm the read-only sandbox and the selected model in the run's configuration report. The sandbox denies writes but does not confine reads, so the brief's credential rule and the removal of secret values before anything reaches the Claude critic carry that protection. A native worker does not qualify, because it inherits the session's write permissions.
