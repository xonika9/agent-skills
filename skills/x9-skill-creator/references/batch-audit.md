# Batch audit orchestration

Use this reference when several project-owned skills must be audited against one installed `x9-skill-creator` contract. It changes only how audits are discovered, delegated, persisted, and summarized. It does not define a second audit contract.

Each worker applies the Audit action, selected evidence tier, [quality rubric](quality-rubric.md), validator, and verdict rules from the installed skill. Proposed fixes remain report-only until the user starts a separate Fix action and approves the relevant changes.

## Contents

- [Invocation](#invocation)
- [Target resolution](#target-resolution)
- [Orchestrator contract](#orchestrator-contract)
- [Worker contract](#worker-contract)
- [Report contract](#report-contract)
- [Worker response](#worker-response)
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

Do not audit a globally installed copy merely because it is reachable from the project. The installed `x9-skill-creator` is the audit contract; the resolved project directories are the audit subjects.

## Orchestrator contract

The orchestrator does not audit target skills itself. It must:

- select `Audit` and one evidence tier for the whole batch;
- split the resolved targets into bounded groups sized so each worker can read every relevant reachable resource;
- assign every group to a fresh worker and use the parent agent's current model unless the user explicitly selected another;
- keep chat context lean by requiring only one Verdict block per target from each worker;
- wait for every group, verify that every expected report exists, and verify that every returned Verdict contains all required fields;
- retry a failed or non-compliant bounded group with a fresh worker rather than silently omitting a target;
- stop with an explicit degraded or blocked result when the same underlying failure prevents complete coverage after a reasonable retry.

Full evidence belongs in report files, not worker chat. Workers may write only the authorized audit reports; they must not modify target skills or their resources.

## Worker contract

For every assigned target, the worker must:

1. Load the installed `x9-skill-creator/SKILL.md` and resolve its installation directory from the loaded resource. Do not assume a home-directory location or resolve its scripts relative to the caller's working directory.
2. Read `references/quality-rubric.md` completely. When the selected tier is `Behavioral`, also read and follow `references/evals.md`.
3. Read the target `SKILL.md` completely and inspect every reachable resource relevant to its declared contract.
4. Run `python3 <resolved-x9-skill-creator-directory>/scripts/validate.py <absolute-target-skill-directory>` and record the command, exit status, and relevant output.
5. Audit all 10 rubric dimensions and complete all 8 judge-checklist items.
6. Keep claims within the selected evidence tier. Under `Static`, mark behavioral claims `NOT_PROVEN` where relevant without treating the absence of live evaluation as a finding by itself. Under `Behavioral`, record scenarios, assertions, and evidence paths; report an unavailable required route as `DEGRADED`.
7. Do not modify the audited skill or any of its resources. Describe proposed fixes only in the report and put irreversible or load-bearing choices under `Needs your decision`.
8. Write the full report and return only its final Verdict block in chat.

## Report contract

Write one report per target to:

```text
docs/skill-audits/<local-date-yyyy-mm-dd>/<skill-name>.md
```

If two targets have the same skill name, add the shortest project-relative parent segment needed to make their report filenames unique. If a destination already exists, preserve it and choose a non-colliding filename unless the user explicitly authorized updating that report.

Each report must identify the project-relative target and selected evidence tier, then contain:

- the validator command, exit status, and relevant output;
- one section for each of the 10 rubric dimensions, containing either `ok` or concrete findings;
- severity, evidence, impact, and a concrete proposed fix for every finding;
- the complete 8-item judge checklist, with `yes` or `no` and a concrete fix for every `no`;
- a final Verdict block with exactly these fields:

```text
Status:
Decided here:
Needs your decision:
Remaining/deferred:
```

Because the action is Audit, `Decided here` is normally `None — Audit only`. Use the status meanings defined by the quality rubric. Failed required structural validation is a blocker, and a target cannot be `clean` when required evidence could not be collected.

## Worker response

Return only this block for each assigned target:

```text
<project-relative-target>
Status:
Decided here:
Needs your decision:
Remaining/deferred:
```

Do not return analysis, summaries, validator logs, or report contents in worker chat.

## Final response

After all targets are accounted for, return only:

1. A table with `Skill | Status | Full report`.
2. One consolidated `Needs your decision` list with links to the corresponding reports. Write `None` when the list is empty.

Do not imply that proposed fixes were applied. Applying approved changes is a separate `Fix` action.
