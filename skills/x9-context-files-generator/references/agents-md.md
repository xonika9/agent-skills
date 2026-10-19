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

Text between another skill's markers, such as `<!-- x9-okf-docs:start -->` and `<!-- x9-okf-docs:end -->`, or `<!-- x9-cto:start -->` and `<!-- x9-cto:end -->`, belongs to that skill: never independently rewrite, paraphrase, or merge it. A refresh explicitly included in the authorized scope follows that owner's block contract; otherwise report the needed owner-specific change. Move it only as a whole block under [the ordering rule](rule-blocks.md#order). Report a conflict with it instead. This skill's own `<!-- x9-context-files-generator:<block>:start -->` blocks and their hand-maintained predecessor follow [rule-blocks.md](rule-blocks.md).

Use one canonical owner per fact. A concise summary may appear in another audience file when omitting it would cause a different action.

## Derivability test

Remove a block only when both conditions hold:

1. A fresh agent can recover it cheaply from stable repository evidence such as manifests, source, configuration, or `--help`.
2. Omitting it would not change the agent's next decision or action.

Dependency inventories, copied signatures, visible file layouts, and mechanically enforced defaults usually satisfy both conditions. Keep nonstandard commands or flags, rationale, gotchas, domain vocabulary, and constraints whose absence could lead to a different action. When uncertain, preserve the user's rule.

## Avoid

- Generic advice the model already follows.
- File-tree inventories and architecture descriptions derivable from a quick search.
- Guessed commands or environment variables.
- Generic global model/browser/tool mechanics belong to global instructions and runtime adapters. Preserve explicit user-selected workflow overrides in their owning block, including cross-provider authority and runtime dispatch when that is the requested portable policy.

## Root and profile context

Classify each repository rule by when an agent needs it. Keep a rule concise in root `AGENTS.md` when it must shape most work before the agent can select a task branch. Put a rule needed only for a recognizable branch or profile, such as a release procedure, in that profile document instead.

Root `AGENTS.md` may retain a short repository-relative pointer only when the profile would otherwise not be discoverable. The pointer names the branch condition and target document; verify that target exists. Keep the procedure body in the profile, not in both files.

## Cross-runtime convention

Agent harnesses do not share one universal repository-context filename. This convention targets Claude Code and `AGENTS.md`-aware harnesses such as Codex; verify another harness's current discovery rules before claiming compatibility. Claude Code reads `CLAUDE.md` and supports importing another file. Keeping two complete copies makes the rules drift, so use one source of truth plus a thin compatibility import when the normalization was requested or authorized.

Apply normalization immediately when the user requested it or repository policy already requires it. Otherwise propose the additional normalization and ask once before editing. Honor an explicit repository or user exception.

When no exception applies, root `AGENTS.md` is the canonical source of root-local agent instructions; each profile document owns its branch-specific procedure. Root `CLAUDE.md` must contain exactly:

```text
@AGENTS.md
```

Keep the final newline. Add and update root-local rules only in `AGENTS.md` so Claude Code follows the import while Codex and other `AGENTS.md`-aware harnesses read the canonical file directly.

Before replacing an existing `CLAUDE.md` with the import, merge every unique local rule into `AGENTS.md` and verify the combined meaning. If a rule appears Claude-only or the runtime does not support the import, resolve the exception from existing repository or user instructions; ask only when that decision remains unresolved. Do not silently retain duplication or delete the rule.

## Verification

- Run safe documented commands or mark them unverified.
- When canonical-file normalization was authorized and no exception applies, compare `CLAUDE.md` byte-for-byte with `@AGENTS.md\n` and confirm unique pre-existing rules survived in `AGENTS.md`.
- For every root pointer to a profile, resolve its repository-relative target and confirm the procedure body appears only in the profile.
- Check that a fresh-context agent can locate setup, constraints, and the relevant completion command.
- Diff against the pre-edit file to prove no user rule disappeared silently.
