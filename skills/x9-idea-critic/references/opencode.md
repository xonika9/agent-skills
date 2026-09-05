# OpenCode adapter

Use this adapter only when `x9-idea-critic` runs from OpenCode. Before dispatching a selected route, inspect only its live interface: `claude --help` for Claude or the subagent/model catalogs for GPT. Available agents and model assignments can change.

## Claude route

Follow [the shared Claude CLI route](claude-cli.md).

## GPT route

Only the user-facing root session may launch a native OpenCode subagent for a GPT critic. Use the agent named in the core skill's model defaults only when its live definition explicitly confirms the selected GPT model at `high` effort; do not infer either property from the agent name. Each critic runs in a fresh child session with only the sealed packet and an explicit instruction to use no tools and execute directly without further delegation. The absence of per-call tool or file ACLs is a runtime limitation, not route failure, because source content is already bounded by the packet.

Record the catalog assignment under the core telemetry rules. If the named agent is unavailable or its live definition does not confirm the selected model and effort, the route failed under the core skill's degradation rules; do not substitute a different agent, an inherited model, or another provider.

## Agent prerequisite

An ordinary critique invocation does not change local agents; an explicit setup request authorizes this prerequisite. Consult the current [OpenCode V2 agent documentation](https://opencode.ai/v2/docs/agents) and confirm model availability. Under `agents` in the existing global configuration, use the agent ID from the core defaults, `mode: "subagent"`, and the selected provider/model with the `high` variant. Its description must identify the actual model and effort for live discovery. Preserve unrelated settings.

This general-purpose agent inherits normal runtime permissions. The sealed-packet and no-delegation constraints belong to the critic's task brief, not permanent restrictions on the agent. The effective agent definition, not the configuration text alone, is the setup evidence: later configuration can override model settings. Existing model-specific agents need not change. The Claude route uses Claude CLI and requires no OpenCode model provider or agent.
