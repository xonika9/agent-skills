---
name: x9-skill-creator
description: Create, audit, fix, or improve Agent Skills for Claude Code or Codex. Excludes running existing skills and editing global agent instructions.
compatibility: Requires Python 3 and Ruby with Psych for structural validation. Full Create, Audit, and Fix work on agent-facing prose also requires x9-agent-instructions.
---

# Skill creator

Create and audit skills through one cross-runtime quality contract: precise triggering, appropriate freedom, safe authority, progressive disclosure, and evidence proportional to maturity and risk.

The [machine-readable onboarding contract](references/onboarding.json) lists external prerequisites.

The body of a skill and some reachable resources are agent instructions. For every Create, Audit, or Fix, load and apply `x9-agent-instructions` before writing or judging any agent-facing instructional prose in `SKILL.md` or reachable resources. It is a subordinate rubric, not the primary skill-authoring workflow, and it owns language, prescription, duplication, and what earns a line. This skill owns what makes the instruction a skill: triggering metadata, placement and runtime adapters, resource layout and progressive disclosure, evidence tier, structural validation, and the audit handoff.

If `x9-agent-instructions` is unavailable, continue only the remaining skill checks, record the instruction rubric as `degraded`, and do not claim that instruction quality was reviewed. A full skill audit cannot be `clean` in that state. Work whose explicit scope contains no agent-facing prose may record the rubric as `not applicable`.

## Select action and evidence

Choose the action first:

- **Create:** the target skill does not exist or the user requests a new one.
- **Audit:** inspect an existing skill, read the complete skill and reachable resources, validate structure, and report findings without changing files.
- **Fix:** apply explicitly authorized improvements to an existing skill, then recheck the changed contract.

Choose the evidence tier separately:

- **Static (default):** inspect files, run structural validation, and judge contracts and dependencies without live model invocations.
- **Behavioral (optional):** run clean-context scenarios from [references/evals.md](references/evals.md) when the user requests live evaluation or a stable/shared/high-risk skill needs behavioral proof for a load-bearing claim.

Ask only when a missing answer is load-bearing. A fully specified request does not need an interview ritual.

## Invocation and ownership

Before writing frontmatter, apply the [runtime classification](references/quality-rubric.md#2-runtime-and-placement-jb) and [ownership boundary](references/quality-rubric.md#ownership-boundary-j). The claimed runtime's adapter owns the supported frontmatter mechanics.

## Invariants

- No skill is written or judged except against [the rubric](references/quality-rubric.md). [patterns.md](references/patterns.md) supplies examples, not templates.
- No new skill exists while another skill's triggers overlap it; extend the owner instead.
- Placement and target runtimes are settled before the first file exists. Personal cross-runtime skills live in `~/.agents/skills/<name>/`; package-owned skills stay in their package. Adapter details: [claude.md](references/claude.md), [codex.md](references/codex.md).
- Rigidity matches fragility: flexible judgment in prose, repeatable deterministic work in scripts, heavy knowledge in references, output assets in assets.
- The skill's intent and user-owned resources survive the change. Escalate only irreversible or materially scope-changing decisions.
- No claim outruns its evidence tier. [Behavioral evaluation](references/evals.md) runs only when behavioral evidence is selected; an unverified behavioral claim is recorded as unverified rather than treated as a defect.
- Every Audit handoff follows [audit reporting](references/audit-reporting.md).

Audit one target directly. For multiple targets, or when the user explicitly requests a batch audit, read [references/batch-audit.md](references/batch-audit.md) and delegate bounded groups to fresh workers. Batch execution changes only coordination and aggregation; every target still uses the same Audit action, evidence tier, rubric, validation, and verdict contract defined here.

For a genuinely underspecified new skill, use the focused questions in [references/interview.md](references/interview.md). Stop once triggers, non-triggers, runtime, input/output, authority, and success evidence are clear.

## Structural check

```bash
python3 <resolved-x9-skill-creator-directory>/scripts/validate.py \
  --runtime <portable|claude|codex> \
  <absolute-target-skill-directory>
python3 <resolved-x9-skill-creator-directory>/scripts/test_validate.py
```

Use one `--runtime` per target runtime; repeat it to require one file to satisfy several runtimes. `portable` enforces the Agent Skills specification and is the default when the flag is omitted. Resolve the creator directory from the loaded skill resource and the target from the actual project/personal source under review; do not substitute a globally installed copy for a package-owned target. The first command validates that target. The second checks validator regression scenarios and is not a substitute for target validation. Structural checks cannot prove triggering, runtime-specific semantics, or output quality; verify platform-specific metadata in the target runtime during behavioral evaluation.

## Done

- Structural validation exits 0 without unexplained warnings.
- The handoff records the instruction rubric as `applied`, `not applicable`, or `degraded`; a full skill audit is not `clean` when it is `degraded`.
- The judge checklist in the rubric passes.
- The handoff states the action and evidence tier, does not claim evidence outside that scope, and follows the single or batch table contract in [audit reporting](references/audit-reporting.md).
- In batch mode, the orchestrator has quality-checked worker findings and removed unsupported or duplicate recommendations before presenting them.
- If behavioral evidence was selected, representative scenarios show correct trigger, boundary, failure, and completion behavior.
- Static evidence may support a `clean` audit without live evaluation; unverified behavioral claims remain explicit follow-up evidence, not an automatic finding.
