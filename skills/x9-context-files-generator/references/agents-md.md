# Agent-file contract

Use for repository `AGENTS.md` and `CLAUDE.md`, not global personal files.

## Include

- Commands verified from manifests, scripts, CI, or a successful local run.
- Constraints an agent cannot infer cheaply from code: destructive commands, mutable linters, production-data risks, generated-file rules, branch/release requirements.
- Nonstandard architecture boundaries or rationale only when they materially affect implementation choices.
- Observable verification required after common changes.
- Links to canonical deeper documents instead of copied explanations.

## Preserve

Read the live file immediately before editing. Existing rules may encode incidents that are invisible in code. Merge surgically; a full replacement requires explicit user intent and a before/after review.

Use one canonical owner per fact. A concise summary may appear in another audience file when omitting it would cause a different action.

## Avoid

- Generic advice the model already follows.
- File-tree inventories and architecture descriptions derivable from a quick search.
- Guessed commands or environment variables.
- Global model/browser/tool mechanics; those belong to global instructions and runtime adapters.

## Personal cross-runtime convention

In the user's personal repositories, root `AGENTS.md` is the single canonical source of local agent instructions. Root `CLAUDE.md` must contain exactly:

```text
@AGENTS.md
```

Keep the final newline. Add and update local rules only in `AGENTS.md` so Codex and Claude Code read the same instructions without duplicate maintenance.

Before replacing an existing `CLAUDE.md` with the import, merge every unique local rule into `AGENTS.md` and verify the combined meaning. If a rule appears genuinely Claude-only or the runtime does not support the import, stop and ask whether this repository is an explicit exception; do not silently retain duplication or delete the rule.

## Verification

- Run safe documented commands or mark them unverified.
- For a personal repository without an explicit exception, compare `CLAUDE.md` byte-for-byte with `@AGENTS.md\n` and confirm unique pre-existing rules survived in `AGENTS.md`.
- Check that a fresh-context agent can locate setup, constraints, and the relevant completion command.
- Diff against the pre-edit file to prove no user rule disappeared silently.
