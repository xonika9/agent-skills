# Adapter — Claude Code

Before relying on load-bearing Claude Code discovery, metadata, or invocation details, check the current official documentation or installed runtime surface.

Only what is specific to Claude Code: placement, metadata, triggering. Method and checks live in the core and [quality-rubric.md](quality-rubric.md).

## Placement

- Claude Code discovers skills under `~/.claude/skills/`: it scans for folders with `SKILL.md`, loads metadata (`name` + `description`) always, the body on trigger, resources as needed.
- Make the skill's source-of-truth folder visible with a symlink:
  ```bash
  ln -s ../../.agents/skills/<name> ~/.claude/skills/<name>
  ```

## Scaffold

Build only the resource folders the contract needs. Prefer the runtime's current generator when one is available; otherwise create the minimal structure directly.

## Frontmatter

- `name` and `description` are required. Optional and rare: `allowed-tools`, `license`; plugin skills sometimes carry `version`.
- For a **user-invoked-only** skill (run via `/<name>`, never auto-fired), set `disable-model-invocation: true` — this drops its `description` from the model's context budget entirely. The trade-off: you must remember the skill exists to invoke it, so reserve it for skills you reach for deliberately.
- A personal skill does not need `agents/openai.yaml`.

## Triggering

- The only trigger is the `description`. Claude tends to **under**-trigger, so make the description slightly "pushy": explicit trigger phrases and contexts, plus a "when NOT". Do not summarize the process in the `description` (see dimension 1).

## Invocation

- Via the `Skill` tool or `/<name>`.

## Packaging `.skill` (optional)

- Needed only to share a skill with others, not for personal installation (a symlink is enough).
- Packager — the native `package_skill.py` from the Anthropic skill-creator (`~/.claude/plugins/marketplaces/anthropic-agent-skills/skills/skill-creator/scripts/`). Do not write your own.
- The path above can drift when the plugin updates — if it is missing, locate the script with `find ~/.claude/plugins -name package_skill.py` instead of assuming it moved for a reason.
