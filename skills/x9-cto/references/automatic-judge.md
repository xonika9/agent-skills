# Automatic Judge mode

## Contents

- [Required input](#required-input)
- [Classify before writing](#classify-before-writing)
- [Write and verify](#write-and-verify)
- [Result](#result)
- [Manual-mode compatibility](#manual-mode-compatibility)

Triggered only by the exact installed invocation with the whole mode token
`auto-judge` under [runtime mechanics](runtime.md). This includes a qualified
plugin entry point when that is what the active catalog exposes. It is not an
alias for manual Judge and is never selected merely because a review report is
present.

## Required input

Invoke the installed skill with `auto-judge`, then supply:

```yaml
target_document: <one repo-relative ordinary file>
settled_contract: <immutable contract path or exact settled-contract excerpt>
review_report: <full report with stable finding IDs and evidence references>
```

The target must resolve inside the repository and be the only substantive write. The
only additional permitted path is the canonical companion `log.md` when repository rules
require a mechanical entry for the target edit. The settled contract must explicitly fix
scope, decisions, completion bar, and authority. Canon and evidence may be read but not
edited. Load and follow a repository-mandated document owner such as `x9-okf-docs` when
it applies; it does not expand this mode's write set. Do not invoke an implementation
workflow, commit, external action, or another mutating workflow that expands the scope or
permitted paths.

## Classify before writing

Read and classify the entire report before changing the target. A finding is
automatically applicable only when its correction has one unambiguous form inside the
settled contract:

- a technical error such as a wrong path, command, or existing component name;
- an internal contradiction, ambiguity, duplication, formatting defect, or typo;
- an evidence error such as a wrong reference or a claim not supported by the supplied
  evidence;
- missing technical detail whose only correct value follows directly from repository
  canon.

An evidence correction may say `not run` or `NOT_PROVEN`; it must not waive a required
check or weaken the completion bar.

If any finding requires a decision about product or visible behavior, UI/UX, scope,
non-goals, architecture, service boundaries, completion bar, degraded acceptance,
authority, canon, or a choice between real alternatives, return
`NEEDS_HUMAN_DECISION` without edits. The same atomic stop applies when any correction
requires another substantive file. A mandatory OKF `log.md` entry is the sole mechanical
exception; it records the applied target correction and must not carry a new decision. Do
not apply the safe findings from a mixed report.

Return `NOT_PROVEN` without edits when the settled contract or evidence is insufficient,
the target is missing, is a symlink, escapes the repository, more than one target is
supplied, or user-owned changes cannot be separated. If the source changes during the
operation or readback cannot prove the exact write set, stop and report the actual
remaining changes under the result contract below.

## Write and verify

For an applicable report:

1. Record the target bytes or hash and current repository status.
2. Apply only the classified findings to the one target.
3. Inspect the diff and read the file back.
4. Run the repository-mandated checks that apply to the target, including documentation
   format and link checks when the target is curated documentation.
5. Return `UPDATED` only when every applied finding is verified and the changed paths
   created by this mode are `target_document`, optionally plus its canonically required
   companion `log.md`.

Do not remove or roll back an unexpected foreign change. Stop and report the actual
write set as `NOT_PROVEN`.

## Result

Return exactly one YAML block:

```yaml
status: PASS | UPDATED | NEEDS_HUMAN_DECISION | NOT_PROVEN
target_document: <path>
changed_paths: []
applied_finding_ids: []
decision_items: []
evidence_checked: []
verification: <diff, hash, and readback result>
summary: <short outcome>
```

`PASS` means no edit was needed. `UPDATED` requires `changed_paths` to contain the target
and, only when required, its mechanical companion log, with every applicable
repository-mandated check passing. `NEEDS_HUMAN_DECISION` requires no edit by this mode
and `changed_paths: []`. For `NOT_PROVEN`, list this mode's actual remaining changes in
`changed_paths` and its applied finding IDs, or use empty lists when nothing was applied.
Explain failed or unavailable verification in the existing evidence and verification
fields; an applied finding is not thereby verified. Report unexpected foreign changes
honestly without claiming them as this mode's edits or rolling them back.

## Manual-mode compatibility

The exact installed invocation with the whole token `judge` continues to use
[judge.md](judge.md), make no document edits, and follow its adaptive response
contract.
