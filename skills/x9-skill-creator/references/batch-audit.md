# Batch audit orchestration

Use this reference when several project-owned skills must be audited against one installed `x9-skill-creator` contract. It changes only how audits are discovered, delegated, persisted, and summarized. It does not define a second audit contract.

Each worker applies the Audit action, selected evidence tier, [quality rubric](quality-rubric.md), the subordinate `x9-agent-instructions` rubric for agent-facing prose, validator, and verdict rules from the installed skill. The orchestrator then applies [audit reporting](audit-reporting.md) to quality-check and consolidate the raw findings. Proposed fixes remain report-only until the user explicitly approves all or selected recommendations.

## Contents

- [Invocation](#invocation)
- [Target resolution](#target-resolution)
- [Orchestrator contract](#orchestrator-contract)
- [Worker contract](#worker-contract)
- [Report contract](#report-contract)
- [Worker response](#worker-response)
- [Orchestrator QA and consolidated report](#orchestrator-qa-and-consolidated-report)
- [Final response](#final-response)

## Invocation

Paths are optional and must not be hard-coded into the recipe. A short request is enough:

```text
Use x9-skill-creator to batch-audit the project-owned skills in this repository. Evidence: Static.
```

Supply one or more project-relative directories or glob patterns when the scope should be explicit:

```text
Use x9-skill-creator to batch-audit ./skills and ./packages/*/skills. Evidence: Static.
```

`Static` is the default. Select `Behavioral` explicitly only when live clean-context evaluation is wanted; then every worker also follows [evals.md](evals.md).

## Target resolution

Resolve targets before creating workers:

1. Find the repository root from the current working directory.
2. If the user supplied paths or glob patterns, resolve them against that root. A resolved directory containing `SKILL.md` is one target; otherwise discover descendant directories containing `SKILL.md`.
3. If no paths were supplied, discover project-owned directories containing `SKILL.md` within the repository.
4. Exclude dependencies, caches, generated output, runtime installation directories, and targets whose resolved path is outside the repository. Explicitly supplied project paths may include hidden source directories such as `.claude/skills` or `.agents/skills`.
5. Deduplicate targets by resolved directory. Ask one short question only when multiple plausible source roots make ownership or intended scope materially ambiguous.

The installed `x9-skill-creator` is the audit contract; the resolved source directories are the audit subjects. Resolve every candidate through symlinks first: a path under a runtime installation directory that resolves into a source repository is that source, not a copy. Exclude only a path that resolves to a genuinely separate installed duplicate.

## Orchestrator contract

The orchestrator does not repeat each target's full rubric audit from scratch, but it owns cross-report QA and the final judgment. It must:

- select `Audit` and one evidence tier for the whole batch;
- select one report language by the precedence in [audit reporting](audit-reporting.md) and pass its exact `Report language: <tag>` to every worker;
- split the resolved targets into bounded groups sized so each worker can read every relevant reachable resource;
- assign every group to a fresh worker and use the parent agent's current model unless the user explicitly selected another;
- keep chat context lean by requiring only the report path, finding counts, instruction-rubric result, and one Verdict block per target from each worker;
- wait for every group, verify that every expected report exists, and verify that every returned response contains the report path, the assigned report-language tag, severity counts, instruction-rubric result, and all required Verdict fields;
- retry a failed or non-compliant bounded group with a fresh worker rather than silently omitting a target;
- read every complete worker report, check every finding against its cited source and declared intent, merge duplicates, filter unsupported claims, and recompute target status from retained findings;
- retain every evidence-backed Blocker, Important, and Minor finding regardless of whether it needs a user decision;
- write the consolidated report and mirror its complete findings table in the final chat response;
- stop with an explicit degraded or blocked result when the same underlying failure prevents complete coverage after a reasonable retry.

Full evidence belongs in report files, not worker chat. Workers may write only the authorized audit reports; they must not modify target skills or their resources.

## Worker contract

For every assigned target, the worker must:

1. Load the installed `x9-skill-creator/SKILL.md` and resolve its installation directory from the loaded resource. Do not assume a home-directory location or resolve its scripts relative to the caller's working directory.
2. Use the exact assigned `Report language: <tag>` for all report prose and localized labels. Do not infer another language from the target, repository, or worker context.
3. Load and apply `x9-agent-instructions` before judging agent-facing instructional prose. If it is unavailable, continue the remaining checks, record `Instruction rubric: degraded`, and do not return a `clean` full audit; use `not applicable` only when the assigned scope contains no agent-facing prose.
4. Read `references/quality-rubric.md` completely. When the selected tier is `Behavioral`, also read and follow `references/evals.md`.
5. Read the target `SKILL.md` completely and inspect every reachable resource relevant to its declared contract.
6. Run `python3 <resolved-x9-skill-creator-directory>/scripts/validate.py --runtime <target-runtime> <absolute-target-skill-directory>` with one `--runtime` per claimed target runtime, and record the command, exit status, and relevant output.
7. Audit all rubric dimensions and complete every item in the judge checklist from [quality-rubric.md](quality-rubric.md).
8. Keep claims within the selected evidence tier. Under `Static`, mark behavioral claims `NOT_PROVEN` where relevant without treating the absence of live evaluation as a finding by itself. Under `Behavioral`, record scenarios, assertions, and evidence paths; report an unavailable required route as `DEGRADED`.
9. Do not modify the audited skill or any of its resources. Describe proposed fixes only in the report and put irreversible or load-bearing choices under `Needs your decision`.
10. Write the full report and return its path, report-language tag, severity counts, instruction-rubric result, and final Verdict block in chat.

## Report contract

Write one report per target to:

```text
docs/skill-audits/<local-date-yyyy-mm-dd>/<skill-name>.md
```

If two targets have the same skill name, add the shortest project-relative parent segment needed to make their report filenames unique. If a destination already exists, preserve it and choose a non-colliding filename unless the user explicitly authorized updating that report.

Write the report using the assigned language and the persistent-report contract in [audit reporting](audit-reporting.md). Preserve exact commands, paths, source quotations, validator output, status tokens, and severity tokens.

Each report must record `Report language: <tag>`, identify the project-relative target and selected evidence tier in that language, and contain:

- the validator command, exit status, and relevant output;
- one section for each of the 10 rubric dimensions, containing a localized no-finding statement or concrete findings;
- severity, evidence, impact, and a concrete proposed fix for every finding;
- a localized `Why these changes help` section, with the concise explanation required by [audit reporting](audit-reporting.md) for every retained finding;
- the complete judge checklist from [quality-rubric.md](quality-rubric.md), with localized yes/no answers and a concrete fix for every negative answer;
- the localized persistent-report verdict block defined by [audit reporting](audit-reporting.md).

Use the status meanings defined by [audit reporting](audit-reporting.md). Failed required structural validation is a blocker, and a target cannot be `clean` when required evidence or the required instruction rubric could not be collected.

## Worker response

Return only this block for each assigned target:

```text
Target: <project-relative-target>
Report: docs/skill-audits/<date>/<report-name>.md
Report language: <tag>
Status:
Findings: Blocker <n> | Important <n> | Minor <n>
Instruction rubric: applied|not applicable|degraded
Decided here:
Needs your decision:
Remaining/deferred:
```

Do not return analysis, summaries, validator logs, or report contents in worker chat.

## Orchestrator QA and consolidated report

After every worker report exists, the orchestrator must follow the batch QA procedure in [audit reporting](audit-reporting.md):

1. Read every complete worker report rather than relying on the Verdict block or severity counts.
2. Verify that every report records the assigned `Report language: <tag>` and uses that language for its prose and localized labels; retry a non-compliant report instead of translating it during consolidation.
3. Open the cited source for every finding and confirm that the evidence and impact support the proposed severity.
4. Compare the claim with the skill's explicit intent, current maintainer decisions, repository policy, and selected evidence tier.
5. Merge duplicate findings. Filter unsupported, non-operational, out-of-scope, or intent-contradicting recommendations; never filter solely because severity is Minor.
6. Recompute each target status from retained findings.
7. Write one consolidated report to `docs/skill-audits/<local-date-yyyy-mm-dd>/summary.md`. Preserve an existing file by choosing a non-colliding name unless the user authorized replacement.

The consolidated report contains:

- `Report language: <tag>` matching the worker assignments;
- the localized persistent-report findings table from [audit reporting](audit-reporting.md), including one accounting row for every clean target;
- a localized `Why these changes help` section, with one concise explanation for every retained finding;
- selected evidence tier and validation coverage;
- instruction-rubric coverage and any degraded targets;
- decisions requested, with a recommended default and concrete alternatives;
- deferred or unavailable behavioral evidence;
- a localized `Filtered out by orchestrator QA` appendix containing finding identifier, target, and dismissal reason.

## Final response

After all targets are accounted for and QA is complete, return:

1. The complete table below, with one row per retained Blocker, Important, and Minor finding and one accounting row for every clean skill:

```text
| Skill | Status | Severity | Area | Finding | Evidence / impact | Recommendation | Decision | Full report |
```

2. `Why these changes help`, with one concise explanation for every retained finding; omit it when there are no retained findings.
3. A concise `Needs your decision` section for rows marked `User decision`; include the recommended default and concrete alternatives. Write `None` when there are no such rows.
4. The selected evidence tier, instruction-rubric coverage, validation coverage, deferred or unavailable behavioral evidence, and a link to the consolidated report.

Do not expose only statuses or decision-required findings. Do not copy filtered findings into the chat table. Do not imply that proposed fixes were applied; apply them only after explicit user approval.
