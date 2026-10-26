# Runtime mechanics

Use the active runtime's exposed goal, task, and subagent primitives. Discover
current capabilities and the installed skill name before relying on them; do not
invent tools or assume that a plugin and a direct installation use the same
invocation spelling. The examples below describe invocation forms, not proof
that a particular installation exposes them.

### Launch defaults

For every top-level chat this skill launches, and every prompt it prepares for
the owner to launch, read `.x9-cto.json` at the repository root. Each field the
user names for that launch replaces the file's field; a field absent from both
inherits the launching agent's value, and without the file every field does.
The file covers only those chats and the subagent route written into their
prompts. This chat's own subagents keep the runtime's routing, and a launched
chat that loads this skill follows the route its prompt carries instead of
applying the `chat_*` fields to its own subagents. The file is flat JSON:

| Field | Meaning |
|---|---|
| `chat_provider` | provider instance for the chat, such as `claudeAgent` or `codex` |
| `chat_model` | an exact model ID, or a family alias such as `opus` or `sonnet`: the model of that family with the highest version in the chosen provider's live catalog at launch |
| `chat_effort` | value of the provider's effort option (in T3 Code, `effort` for Claude and `reasoningEffort` for Codex) |
| `subagent_runtime` | `opencode`, or `native` for the chat runtime's own routing, in which case `subagent_model` is ignored |
| `subagent_model` | for `opencode`: `default`, or an exact `<providerID>/<model>` with an optional `#<variant>` that maps to the runtime's variant option (in T3 Code, the `variant` option) |
| `bakeoff_native_model`, `bakeoff_native_count` | candidates of a `ce-bakeoff` run as the runtime's own subagents: model or family alias, and how many |
| `bakeoff_opencode_model`, `bakeoff_opencode_count` | candidates of a `ce-bakeoff` run on OpenCode: `default` or an exact model as for `subagent_model`, and how many |

Resolve the chat model in the live catalog (in T3 Code,
`orchestrator_capabilities` with a search for the alias) and pass the resolved
ID; when the catalog has no match, report that instead of substituting another
model. Write the subagent route into the prompt, because the launched chat does
not read this file; the route covers every subagent of that chat, including
reviews. For `default`, the prompt tells the chat to run its subagents on
OpenCode with the default model and variant of the OpenCode
configuration in effect, read from `opencode debug config` and passed
explicitly. Whenever an agent using this skill, including a launched chat,
runs `ce-bakeoff` and the user named no candidate models, it passes the
`bakeoff_*` candidates; the bake-off's own rules choose its judge. The
repository's own rules own what may be launched; this file only chooses
providers, models, and runtimes.

### Cross-model subagents in T3 Code

Applies only when running inside T3 Code (its `t3-code` orchestration tools
are present) and the user asks for subagents on a model or provider other than
the head agent's, for example "orchestrate on Opus, subagents on GPT". The
chosen route covers every delegated unit, including research and review,
until the user changes it, and overrides the default subagent model policy.
Choose the provider, model, and options from `orchestrator_capabilities`.
When the user asks for subagents on OpenCode without naming a model, use the
`opencode` provider instance with the default model of the OpenCode
configuration in effect, read from `opencode debug config` and passed as
`<providerID>/<model>`, with the variant that configuration names and none
otherwise; a model or variant the user names replaces this default. If no
default is configured, the catalog does not list the chosen model, or it marks
the instance unable to run child tasks, report that instead of substituting
another model. The
T3 orchestration instructions and its tool descriptions own the delegation,
continuation, and review-round mechanics; follow them rather than this file.
A child result is text: verify its files, checks, and commits in the tree
before integrating. What may be sent to another provider follows the
repository's cross-provider rule in `AGENTS.md`.

Judge, Grounding, autonomous CE run, Prompt, and Pilot invocations are also runtime-native:

| Runtime | Manual Judge | Automatic Judge | Grounding | Autonomous CE run | Prompt | Pilot |
|---|---|---|---|---|---|---|
| OpenCode | — | — | `/x9-cto ground` | `/x9-cto auto` | `/x9-cto prompt` | `/x9-cto pilot start\|stop\|report` |
| Codex | `$x9-cto judge` | `$x9-cto auto-judge` | `$x9-cto ground` | `$x9-cto auto` | `$x9-cto prompt` | `$x9-cto pilot start\|stop\|report` |
| Claude Code | `/x9-cto judge` | `/x9-cto auto-judge` | `/x9-cto ground` | `/x9-cto auto` | `/x9-cto prompt` | `/x9-cto pilot start\|stop\|report` |

An exact invocation means the installed entry point for the active runtime plus
the whole mode token. A plugin may expose a qualified name. Resolve it from the
active catalog rather than manufacturing an alias. A missing route is reported
as unavailable; writing a prompt does not establish that a chat was launched.

