# Auditing an existing project

The audit answers: which changes would most improve this project's correctness, safety, and maintainability, measured against the template where the project uses the same tools and against the principles where it does not?

## Classify each layer

Inspect manifests, lockfiles, configuration, CI, Dockerfiles, and representative code. For each layer in the [stack table](stack.md#core) record the project's tool and one of:

- **Same:** the project uses the template's tool. Judge it against the template form of each rule and the [library notes](library-notes.md).
- **Different:** another tool fills the role. Judge it against the principles only; a **(convention)** rule is a finding only when the project has no consistent convention of its own, and an existing consistent one is never replaced. Recommend replacing the tool only for a concrete defect: unmaintained or archived, an open security problem, or a capability the project needs and the tool cannot provide. State the migration cost beside the benefit.
- **Absent:** the role is unfilled. A finding only when the project needs it now: a core layer that the product depends on, or an on-demand item whose trigger has happened.

When most layers are Same, the audit converges on the template. When most are Different, it improves the project in its own terms. Never recommend switching languages, frameworks, or databases for alignment with the template alone.

## Findings

Check each applicable rule in [rules.md](rules.md) against evidence. A finding needs:

- the rule ID and the file and line, configuration value, or command output that shows the gap;
- the practical consequence in this project;
- the smallest fix, with effort (minutes, hours, days) and whether it changes behaviour for users or data.

Rank by consequence: data loss or exposure, then broken releases or deploys, then defects that slip past verification, then maintainability. Group trivially related findings. Keep unconfirmed suspicions in a separate list with the fact that would decide them.

Security is checked at the level of the rules here. A deeper review of trust boundaries belongs to `x9-appsec`; a comparison of architectural directions belongs to `x9-architecture-scout`. Mention when the evidence suggests either is warranted.

## Report

1. Stack map: each layer, the project's tool, Same / Different / Absent.
2. Findings, ranked, numbered for selection.
3. What already matches, in one short paragraph.
4. Not checked, and why (no access to deployment, no database to run tests, and so on).
5. Whether to write or update the `AGENTS.md` rules block.

Run the project's own lint, typecheck, and tests when they are local and side-effect-free; report their results as evidence. Do not run migrations, deploys, or anything against shared or remote services.

## Applying fixes

Apply only the findings the user selects. After the change, run the project's verify command or the closest available checks and report the result per finding. A fix that turns out larger than reported, or touches data or deployment, goes back to the user before it continues.
