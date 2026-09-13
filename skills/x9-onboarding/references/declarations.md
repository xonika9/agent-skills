# Onboarding Declarations

## Contents

- [Version 1 Shape](#version-1-shape)
- [Alternative Routes](#alternative-routes)
- [Typed Checks](#typed-checks)
- [Safety Boundary](#safety-boundary)

`references/onboarding.json` is a version 1, read-only declaration of external
requirements for its owning skill. It is data, not an instruction: the
declaration cannot contain commands to run, arguments, URLs, paths, secrets, or
free-form setup steps. A skill without external requirements does not need this
file.

Resolve the loaded `x9-onboarding` directory from its loaded `SKILL.md`. Independently
resolve the actual package `skills` root to validate; it may belong to another package,
and neither path depends on the current working directory. Then run:

```bash
python3 <resolved-x9-onboarding-directory>/scripts/validate_onboarding.py \
  <absolute-target-package-skills-root>
```

The validator reads only immediate `skills/*/references/onboarding.json` files.
It reports every violation as `skill/references/onboarding.json: field.path:`
and exits nonzero. A successful check prints `PASS` and the declaration-file
count.

## Version 1 Shape

The top-level object has exactly these fields:

```json
{
  "version": 1,
  "supported_runtimes": ["opencode", "claude", "codex"],
  "requirements": [
    {
      "id": "command-line-tool",
      "runtimes": ["opencode"],
      "kind": "command",
      "level": "required",
      "needed_for": "Checking the local command line tool.",
      "check": {"type": "command-present", "command": "toolctl"},
      "guidance_id": "install-command"
    }
  ]
}
```

`supported_runtimes` is the non-empty set of runtimes where the owning skill can
perform its main contract. It prevents an explicit target from becoming `READY`
merely because runtime filtering removed every requirement.

`requirements` is a non-empty array. Each requirement has `id`, `runtimes`,
`kind`, `level`, `needed_for`, `check`, and `guidance_id`, plus optional
`group`.
Requirement IDs are unique inside their declaration.

- `id` and `guidance_id` use lowercase hyphen-case: a letter followed by
  lowercase letters, digits, and single hyphen-separated segments.
- `runtimes` is a non-empty array drawn from `opencode`, `claude`, and `codex`.
- `kind` is one of `skill`, `command`, `agent`, `mcp`, `runtime-feature`, or
  `user-action`.
- `level` is `required` or `optional`.
- `needed_for` is one non-empty, trimmed display string of at most 160
  characters. It permits letters, digits, spaces, and only `, . : ! ? ( ) '
  -` punctuation. It does not control behavior.

Every object is closed. Unknown fields and wrong JSON types are errors.

## Alternative Routes

Use the same lowercase hyphen-case `group` on two or more requirements when
any one route satisfies one required capability. Every member is `required`
and uses the same `runtimes`; individual rows stay visible, but readiness is
computed once for the group. The exhaustive group and skill aggregation rules,
including the ready-route short circuit and optional-row coverage, are owned by
the [core status model](../SKILL.md#status-model).

## Typed Checks

`check` is a closed discriminated object with a `type` field. It has no optional
or shared extra fields.

| Requirement kind | Check object | Required guidance |
| --- | --- | --- |
| `skill` | `{"type":"skill-present","target_skill":"x9-example"}` | `install-skill` |
| `command` | `{"type":"command-present","command":"toolctl"}` | `install-command` |
| `agent` | `{"type":"runtime-component","component_id":"codex:codex-rescue"}` | `create-agent` |
| `mcp` | `{"type":"runtime-component","component_id":"chrome-devtools"}` | `configure-mcp` |
| `runtime-feature` | `{"type":"runtime-feature","feature_id":"active-skill-catalog"}` | `enable-runtime-feature` |
| `user-action` | `{"type":"manual"}` | `complete-user-action` |

`target_skill` must be an `x9-` lowercase hyphen-case name and must name an
existing directory immediately below the supplied `skills` root. `command` is
one executable name only, without a path, whitespace, or arguments.

`component_id` names the exact entry expected in the runtime's live catalog. It
uses lowercase letters and digits separated by `.`, `:`, or `-`; `kind`
determines whether that entry is an agent or MCP component. The runtime-feature
allowlist is `active-skill-catalog`, `browser-control`, `native-subagents`.
The table above is also the complete `guidance_id` allowlist. New identifiers
require an explicit contract update to this document and the validator; a local
declaration cannot invent them.

## Safety Boundary

The validator rejects URLs, absolute and relative paths, shell syntax,
control characters, secret-like field names, and secret-like values everywhere
in a declaration. Skill directories, `references` directories, declaration files,
and referenced companion skills must not be symbolic links; the validator never
reads a declaration through one. It also rejects an unsafe value even when it appears in an
otherwise known field. No code in this format executes declarations or treats
their display text as an action.
