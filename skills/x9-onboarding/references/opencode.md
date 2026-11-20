# OpenCode adapter

Use this adapter only from OpenCode. First inspect the current session's live skill,
agent, and tool catalogs. Their names, schemas, and availability are runtime facts; do
not derive them from files, remembered commands, or a package directory scan.

Check requirements under [Runtime Checks and Guidance](declarations.md#runtime-checks-and-guidance).

## Configuration

Use `profiles/opencode.json` with the single existing user file at
`~/.config/opencode/opencode.jsonc` or `~/.config/opencode/opencode.json`. Inspect the
current OpenCode V2 schema and live model, agent, MCP, and provider catalogs before
proposing profile paths. Never use `opencode debug config` or another command that emits
the merged configuration: provider and MCP credentials may be included in its output.

Add model-specific agents only when their exact provider, model, and effort variant are
available. The Exa MCP entry contains only an environment reference; applying it never
proves that the variable is set or that Exa is ready. State that `websearch.provider = "exa"` sends future search
queries to that external provider.

After approval, merge supported paths under the
[shared configuration contract](configuration.md), preserving JSONC comments and
unrelated entries. Validate through a JSONC-aware parser or a silent runtime validation
surface; do not validate with a command that prints resolved configuration or headers.
