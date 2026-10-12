---
name: x9-architecture-scout
description: Use when the user asks for a read-only architecture audit that compares plausible directions and makes component boundaries, dependencies, ownership, coupling, or change hotspots visible — «проведи архитектурный аудит», «покажи проблемные места архитектуры», "audit this codebase architecture". Do not use to implement a refactor, create a general implementation plan, or merely explain one file.
---

# Architecture scout

Produce a read-only architecture report for a repository or user-named subsystem. Evidence tier: static.

Inspect component boundaries, dependency direction, ownership of data and behavior, coupling, duplication, change hotspots, and seams. Treat source, configuration, tests, and version history as evidence; distinguish observed facts from inferences. Do not edit production code, refactor, install dependencies, copy an external skill, or change external systems.

## Method

Discover `codebase-design` from the live current-runtime catalog before any project or user/plugin roots that runtime declares. Resolve candidate paths symlink-aware, read the live skill version when one is found, and do not retain, reproduce, or hard-code its machine path. Use its method only to enrich the audit.

If no readable live `codebase-design` is found, perform the direct baseline audit and mark the method status `DEGRADED`. If the user requires Matt's exact method, stop with method status `BLOCKED`; do not substitute an invented version. Read [the report contract](references/report-contract.md) before creating an HTML report. Every report includes at least one architecture diagram; load `x9-diagrams` and follow its Mermaid and design references.

Follow the repository's report-location convention. When it has none, write one HTML file at `docs/architecture-reviews/YYYY-MM-DD-<stable-slug>.html`. A same-day fallback audit must not silently replace a prior report: re-read and replace a named existing report only for an explicit update; otherwise choose a non-colliding stable suffix or path, or ask one short question when the report identity matters. The report may recommend a candidate, but it does not implement it; after a selection, hand the decision to `ce-plan` when available or provide a portable planning handoff.

## Evidence and handoff

Validate the actual report using [the structural validation command](references/report-contract.md#structural-validation-boundary). Report method, structure, and rendering results separately under [the status model](references/report-contract.md#status-model).

Completion is one report that validates and makes the decision question, method/structure/render statuses, conclusion with confidence, candidate comparison, evidence, diagrams, risks, and next step inspectable without JavaScript. Report the artifact path, all three statuses, source scope, principal evidence, and the planning handoff or blocker.

The [onboarding declaration](references/onboarding.json) lists external prerequisites.
