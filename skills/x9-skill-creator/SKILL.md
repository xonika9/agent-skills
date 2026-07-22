---
name: x9-skill-creator
description: Use when creating, auditing, fixing, or improving an Agent Skill for Claude Code or Codex — «создай скилл», «проверь скилл», «почини скилл», «улучши скилл», "create a skill", "audit skill". Do not use for ordinary code, non-skill prose, global agent instructions, or merely running an existing skill.
---

# Skill creator

Create and audit skills through one cross-runtime quality contract: precise triggering, appropriate freedom, safe authority, progressive disclosure, and evidence proportional to maturity and risk.

Write machine-facing skill prose in English for token efficiency. Keep literal user triggers, UI labels, domain terms, and quotations in their native language where the exact text matters.

## Select action and evidence

Choose the action first:

- **Create:** the target skill does not exist or the user requests a new one.
- **Audit:** inspect an existing skill, read the complete skill and reachable resources, validate structure, and report findings without changing files.
- **Fix:** apply explicitly authorized improvements to an existing skill, then recheck the changed contract.

Choose the evidence tier separately:

- **Static (default):** inspect files, run structural validation, and judge contracts and dependencies without live model invocations.
- **Behavioral (optional):** run clean-context scenarios from [references/evals.md](references/evals.md) when the user requests live evaluation or a stable/shared/high-risk skill needs behavioral proof for a load-bearing claim.

Ask only when a missing answer is load-bearing. A fully specified request does not need an interview ritual.

## Common workflow

1. Determine placement and target runtimes. Personal cross-runtime skills default to `~/.agents/skills/<name>/`; package-owned skills stay in their package. Read [references/claude.md](references/claude.md) or [references/codex.md](references/codex.md) for current adapter details.
2. Check for an existing skill with overlapping triggers before creating another.
3. Read [references/quality-rubric.md](references/quality-rubric.md) before writing or judging. Use [references/patterns.md](references/patterns.md) as examples, not templates.
4. Match freedom to fragility: flexible judgment in prose, repeatable deterministic work in scripts, heavy knowledge in references, output assets in assets.
5. Preserve the skill's intent and user-owned resources. Escalate only irreversible or materially scope-changing decisions.
6. Run structural validation and state the evidence tier. Run [behavioral evaluation](references/evals.md) only when behavioral evidence is selected; otherwise record behavioral claims as unverified without treating that deferral as a defect by itself.

Audit one target directly. For multiple targets, or when the user explicitly requests a batch audit, read [references/batch-audit.md](references/batch-audit.md) and delegate bounded groups to fresh workers. Batch execution changes only coordination and aggregation; every target still uses the same Audit action, evidence tier, rubric, validation, and verdict contract defined here.

For a genuinely underspecified new skill, use the focused questions in [references/interview.md](references/interview.md). Stop once triggers, non-triggers, runtime, input/output, authority, and success evidence are clear.

## Structural check

```bash
python3 scripts/validate.py ~/.agents/skills/<name>
python3 scripts/test_validate.py
```

The validator checks the shared structural contract; it cannot prove triggering, runtime-specific semantics, or output quality. Verify platform-specific metadata in the target runtime during behavioral evaluation.

## Optional behavioral check

When behavioral evidence is selected, run in a fresh context:

- a positive trigger;
- a near-miss that must not trigger;
- one ambiguity or authority boundary;
- one tool-failure/degraded-result scenario when tools are part of the contract;
- one observable completion assertion.

For stable or release-gated substantive changes, compare old/new or with-skill/without-skill behavior on the same prompts. Record evidence, not the evaluator's impression. Rapidly changing personal skills may defer this until real use exposes a stable scenario worth retaining.

## Done

- Structural validation exits 0 without unexplained warnings.
- The judge checklist in the rubric passes.
- The handoff states the action and evidence tier and does not claim evidence outside that scope.
- If behavioral evidence was selected, representative scenarios show correct trigger, boundary, failure, and completion behavior.
- Static evidence may support a `clean` audit without live evaluation; unverified behavioral claims remain explicit follow-up evidence, not an automatic finding.
