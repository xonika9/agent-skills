# Codex CLI delegation adapter

Run `codex exec --help` and `codex exec resume --help` before relying on the examples below. The CLI surface can change independently of this skill.

## One-shot execution

Read-only:

```bash
codex exec --disable hooks -s read-only --skip-git-repo-check --ephemeral "<self-contained prompt>" </dev/null
```

Write-capable:

```bash
codex exec -s workspace-write - <"$DELEGATION_PROMPT_FILE"
```

The last-message output normally returns through stdout; do not create a separate output artifact unless the caller explicitly needs one.

For a multiline or sensitive brief, create the transport file outside the repository with this lifecycle before writing its contents:

```bash
umask 077
DELEGATION_TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/x9-codex.XXXXXX")" || exit 1
DELEGATION_PROMPT_FILE="$DELEGATION_TMP_DIR/prompt.md"
cleanup_delegation_files() {
  rm -f -- "$DELEGATION_PROMPT_FILE"
  rmdir -- "$DELEGATION_TMP_DIR" 2>/dev/null || true
}
trap cleanup_delegation_files EXIT
trap 'exit 130' HUP INT TERM
chmod 700 "$DELEGATION_TMP_DIR" || exit 1
: >"$DELEGATION_PROMPT_FILE" || exit 1
chmod 600 "$DELEGATION_PROMPT_FILE" || exit 1
```

Write the brief only after the trap and user-only permissions are in place. Pass it through stdin rather than argv. After `codex exec` returns, let the trap remove it and verify that the temporary directory no longer exists. Never reuse a fixed `/tmp` path or leave transport/output files in the repository, logs, or user artifacts.

Use `--ephemeral` when the brief must not create a resumable Codex session; omit it only when continuity is required. This protects local transport and session history, not provider-side processing or retention. Do not put credentials or secret values in the brief. Refer to a local credential source that the authorized task can read instead.

For a sealed self-contained run, disable hooks through the live CLI feature control and inspect startup warnings. A shell shim or wrapper may re-enable them after argument parsing; if the run reports enabled hooks, stop rather than treating that invocation as sealed.

- Use `-c 'model_reasoning_effort="<level>"'` when the caller requires an explicit effort override. Plain `codex exec` has no `--effort` flag: take valid levels from `codex debug models`, then require the run's `reasoning effort:` report to match because unsupported values may be accepted silently.
- Use `-m <model>` only when the user explicitly requests an available model or the calling skill requires a confirmed model family; otherwise inherit `~/.codex/config.toml`.
- `--skip-git-repo-check` is appropriate for a read-only one-shot outside a repository. Do not use it to bypass a task's repository contract.

## Resume

Resume the same session only for a real follow-up. `resume` does not share the normal `exec` flag surface: it accepts `-c`, `-m`, `--last`, `--all`, image, output, and persistence options, but not `-s/--sandbox`. Verify its live help before copying flags or changing sandbox behavior.
