# Delegation log

Read the current table header of `~/.local/share/x9/codex-delegation-log.md` before writing and keep each row to minimal non-sensitive telemetry: route, actual model/effort when observable, wall-clock time, Codex tokens, whether rework was needed, and a generic success/failure outcome. Never record task content, secrets, repository names, or personal paths. Use `н/д` for unavailable data and `?` when rework is not known yet; never invent telemetry. Do not replace an existing file or follow a symlink; report that logging was skipped instead.

The log is optional permanent operational history, not a completion gate. A missing or unwritable log must not fail the delegated task.
