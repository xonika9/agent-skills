# Adapter — Codex

Before relying on load-bearing Codex discovery, metadata, or invocation details, check the current official documentation or installed runtime surface.

Only what is specific to Codex: placement, metadata, init/validate. Method and quality checks live in the core and [quality-rubric.md](quality-rubric.md).

Paths to native `.system` tooling below can drift with Codex updates — if a script is missing, locate it with `find ~/.codex/skills -name <script>` before doing the step by hand.

## Placement

- Codex reads the source-of-truth folder under `~/.agents/skills/` **natively** — discovery needs no copy, no symlink, and no config entry.
- `~/.codex/config.toml` is only for **disabling** a skill (all are enabled by default):
  ```toml
  [[skills.config]]
  path = "/Users/<...>/.agents/skills/<name>/SKILL.md"
  enabled = false
  ```

## Frontmatter

- `name` and `description` are required. Usually add no other fields; if a short UI label is needed, `metadata.short-description` is allowed.
- The description frames when to use the skill (all the "when" goes here, not in the body); do not turn it into a process summary (see rubric dimension 1).

## agents/openai.yaml (optional)

- This is UI metadata for lists and chips, **not** for the agent. Personal skills usually do not carry it.
- Add it only if UI chips are needed. Then use the native generator, do not write your own:
  ```bash
  ~/.codex/skills/.system/skill-creator/scripts/generate_openai_yaml.py <skill-folder> --interface key=value
  ```
- Fields and constraints — in `~/.codex/skills/.system/skill-creator/references/openai_yaml.md`.

## Init and validate

- Scaffold, if wanted, with the native `init_skill.py` (`~/.codex/skills/.system/skill-creator/scripts/`); then delete placeholders.
- Validate with this skill's `scripts/validate.py --runtime codex`; add `--runtime portable` when the same file also claims Agent Skills portability. Run the matrix in [evals.md](evals.md) only when behavioral evidence is selected; structural success does not prove behavior.

## Invocation

- Via `$<name>`.
