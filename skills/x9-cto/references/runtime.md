# Runtime mechanics

Use the active runtime's exposed goal, task, and subagent primitives. Discover
current capabilities and the installed skill name before relying on them; do not
invent tools or assume that a plugin and a direct installation use the same
invocation spelling. The examples below describe invocation forms, not proof
that a particular installation exposes them.

### Cross-model subagents in T3 Code

Applies only when running inside T3 Code (its `t3-code` orchestration tools
are present) and the user asks for subagents on a model or provider other than
the head agent's, for example "orchestrate on Opus, subagents on GPT". The
chosen route covers every delegated unit, including research and review,
until the user changes it, and overrides the default subagent model policy.
Choose the provider, model, and options from `orchestrator_capabilities`.
When the user asks for subagents on OpenCode without naming a model, use the
`opencode` provider instance with `opencode-go/deepseek-v4.1-flash` at the
`high` reasoning variant; a model or variant the user names replaces this
default. If the catalog does not list the chosen
model or marks the instance unable to run child tasks, report that instead of
substituting another model. The
T3 orchestration instructions and its tool descriptions own the delegation,
continuation, and review-round mechanics; follow them rather than this file.
A child result is text: verify its files, checks, and commits in the tree
before integrating. What may be sent to another provider follows the
repository's cross-provider rule in `AGENTS.md`.

Judge, Grounding, autonomous CE run, and Prompt invocations are also runtime-native:

| Runtime | Manual Judge | Automatic Judge | Grounding | Autonomous CE run | Prompt |
|---|---|---|---|---|---|
| OpenCode | — | — | `/x9-cto ground` | `/x9-cto auto` | `/x9-cto prompt` |
| Codex | `$x9-cto judge` | `$x9-cto auto-judge` | `$x9-cto ground` | `$x9-cto auto` | `$x9-cto prompt` |
| Claude Code | `/x9-cto judge` | `/x9-cto auto-judge` | `/x9-cto ground` | `/x9-cto auto` | `/x9-cto prompt` |

An exact invocation means the installed entry point for the active runtime plus
the whole mode token. A plugin may expose a qualified name. Resolve it from the
active catalog rather than manufacturing an alias. A missing route is reported
as unavailable; writing a prompt does not establish that a chat was launched.

