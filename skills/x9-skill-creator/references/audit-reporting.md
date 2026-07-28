# Audit reporting

Use this contract for every Audit handoff. Full evidence may live in persistent reports, but the user-facing response must remain useful without opening those files.

## Contents

- [Report language](#report-language)
- [Finding lifecycle](#finding-lifecycle)
- [Required findings table](#required-findings-table)
- [Why these changes help](#why-these-changes-help)
- [Single-target handoff](#single-target-handoff)
- [Batch handoff](#batch-handoff)
- [Filtered findings](#filtered-findings)

## Report language

Select one BCP 47 report-language tag before producing audit output. Use, in order: the language explicitly requested by the user; the primary carrier language of the audit request; the current conversation language. Ask one short question only when those signals still leave a genuinely ambiguous choice. Never derive the report language from the audited skill, its source files, or the repository's documentation language.

The main auditor selects the tag for a single-target audit. In batch mode, the orchestrator selects it once and passes the same exact `Report language: <tag>` to every worker. Record that line in every persistent report under `docs/skill-audits/`.

Write headings, table labels, findings, impact, recommendations, rationale, checklist answers, decisions, deferred evidence, and filtered-finding explanations in the selected language. Localize the human-facing labels of the findings table and final verdict block while preserving their field order and meaning.

Keep exact identifiers, status and severity tokens, paths, commands, code, source quotations, and validator output unchanged. Keep the worker-response protocol literal so the orchestrator can validate it mechanically.

End every persistent per-target report with localized labels for exactly these four semantic fields: `Status`, `Decided here`, `Needs your decision`, and `Remaining/deferred`. For an Audit action, the localized `Decided here` value is normally the equivalent of `None — Audit only`; do not add, remove, or reorder fields.

## Finding lifecycle

A finding begins as a raw auditor or worker claim. Before the final response, the responsible main agent must review its cited evidence, impact, severity, proposed fix, and fit with the skill's declared intent and current user or repository policy.

Classify each raw finding as:

- **Retained — fix recommended:** evidence and impact hold; no load-bearing choice is required.
- **Retained — user decision:** evidence holds, but intent or policy must be chosen before a fix is safe.
- **Filtered out:** the claim is unsupported, duplicate, outside scope, contradicted by an explicit intentional contract, only a style preference without operational impact, or claims behavior beyond the selected evidence tier.

Do not filter a finding merely because it is Minor, inconvenient, or expensive. Merge duplicate findings into the clearest evidence-backed formulation and keep the strongest justified severity. Audit never implies that a retained recommendation was applied.

## Required findings table

Use one row per retained finding and include all severities. Use this schema for both single-target and batch handoffs:

```text
| Skill | Status | Severity | Area | Finding | Evidence / impact | Recommendation | Decision | Full report |
```

Rules:

- `Severity` is `Blocker`, `Important`, or `Minor`.
- `Decision` is `Fix recommended` or `User decision`.
- `Full report` links the persistent report when one exists; use `—` when a single-target audit did not create one.
- When a skill has no retained findings, include one accounting row with `Severity`, `Area`, `Recommendation`, and `Decision` set to `—`, and `Finding` set to `No retained findings`.
- Prefix every retained `Finding` with a stable identifier such as `F1`, `F2`, and so on. Preserve that identifier in the explanation section and any persistent report.
- Keep cells concise. Evidence should name the exact source path/line or observable behavior and why it matters; detailed logs stay in the full report.

After QA, recompute status from retained findings:

- `clean`: no retained findings;
- `needs your decision`: at least one retained finding has `User decision`;
- `work remaining`: retained findings exist and none require a user decision.
- `degraded`: a required audit route or dependency was unavailable, even if the remaining checks completed.

`degraded` takes precedence over the finding-derived statuses. Keep any user decisions visible in their own section even when the overall audit is degraded.

## Why these changes help

After the table, include one explanation for every retained finding, keyed by its identifier. Use no more than two short sentences: state the practical improvement rather than repeating the finding, evidence, or recommendation; add the material cost or trade-off when the change affects dependencies, compatibility, authority, runtime behavior, or scope. Omit this section when there are no retained findings.

## Single-target handoff

The main auditor owns both the raw audit and final QA. Return:

1. The required findings table.
2. `Why these changes help` when retained findings exist.
3. `Action`, selected evidence tier, instruction-rubric result (`applied`, `not applicable`, or `degraded`), and validation result.
4. A short `Needs your decision` section only when table rows use `User decision`; include the recommended default and concrete alternatives.
5. `Decided here` for a Fix action: the safe reasoned changes already applied.
6. `Remaining/deferred`, including `NOT_PROVEN` behavioral claims without presenting the deferral as a finding.

Do not return only the Verdict block or bury Minor findings in prose.

## Batch handoff

Workers produce raw per-target reports. The orchestrator does not repeat every full rubric audit, but it owns cross-report QA and the final judgment:

1. Read every complete worker report.
2. Check each finding against its cited source and the declared skill intent, current user decisions, and repository policy.
3. Challenge every proposed Blocker and Important severity; verify Minor evidence rather than dropping it.
4. Merge duplicates and filter unsupported or non-operational recommendations.
5. Recompute every target status from retained findings.
6. Write the consolidated report required by [batch-audit.md](batch-audit.md).
7. Return the complete findings table in chat, followed by `Why these changes help`, decisions, instruction-rubric coverage, evidence/deferred scope, and the consolidated-report link.

The final chat table contains every retained Blocker, Important, and Minor finding. `Needs your decision` never determines whether a finding is shown.

## Filtered findings

Keep filtered findings out of the user-facing findings table so it stays actionable. For auditability, the batch consolidated report includes a short `Filtered out by orchestrator QA` appendix with finding identifier, target, and one concrete dismissal reason. Do not copy the full rejected analysis.
