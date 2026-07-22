# Codex CLI delegation adapter

Run `codex exec --help` and `codex exec resume --help` before relying on the examples below. The CLI surface can change independently of this skill.

## One-shot execution

Read-only:

```bash
codex exec -s read-only --skip-git-repo-check "<self-contained prompt>" </dev/null
```

Write-capable:

```bash
codex exec -s workspace-write -o /tmp/codex-last.md - <"$PROMPT_FILE"
```

- Use `-c 'model_reasoning_effort="medium"'` when an explicit effort override is required. Plain `codex exec` has no `--effort` flag.
- Use `-m <model>` only when the user explicitly requests an available model; otherwise inherit `~/.codex/config.toml`.
- `--skip-git-repo-check` is appropriate for a read-only one-shot outside a repository. Do not use it to bypass a task's repository contract.

## Resume

Resume the same session only for a real follow-up. `resume` does not share the normal `exec` flag surface: it accepts `-c`, `-m`, `--last`, `--all`, image, output, and persistence options, but not `-s/--sandbox`. Verify its live help before copying flags or changing sandbox behavior.
