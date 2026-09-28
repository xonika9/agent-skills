---
name: x9-appsec
description: Secure development and source-based review for public websites and web-facing services, including API-only backends, workers, data stores, and deployment. Use for security-sensitive changes and pre-release audits; active testing of running targets requires separate authorization and scope.
---

# Web security

This package-owned skill is model-invoked in Claude Code and Codex. Its portable claim is structural Agent Skills compatibility. Review the whole application path, including server code and supporting services when they exist, regardless of stack. A clean review is bounded evidence, not a guarantee of security.

## Select the work

- **Development:** for a feature or fix, identify the trust boundary it changes, implement the smallest sound control at the trusted decision point, and run focused checks that exercise the security property. Safe in-scope local edits and tests follow the user's implementation request.
- **Review:** for a question, diff, or component, inspect source and configuration without changing them. Research surrounding code to understand the path, but report the requested scope and any dependencies needed to establish it. Apply fixes only when requested.
- **Pre-release audit:** cover the deployed architecture and material entry points across the project. Give each relevant surface an evidence-backed disposition: checked, finding, hypothesis needing validation, or not covered. Ask only for missing deployment facts that could change a decision; keep reviewing independent source in the meantime.

Map who can act (anonymous visitor, user, tenant, administrator, service, provider), what they can affect, and where authority changes: browser to server, endpoint to worker or queue, service to data store, service to service, build to release, and application to provider. Include non-HTTP inputs such as queued jobs, scheduled tasks, files, and provider events when present. Trace the concrete path from an untrusted value or action through validation and authorization to its effect. Check the relevant lenses in [trust surfaces](references/trust-surfaces.md); skip lenses without a corresponding feature or exposure. Use current framework and provider documentation when their behavior matters, rather than assuming defaults.

For routine development, stay with the changed path and its immediately affected controls. For a pre-release audit, expand to exposed routes and operations, backend jobs and integrations, identities and data stores, dependencies and build inputs, production configuration and deployment, and availability and recovery. Record what source cannot establish, such as gateway policy, hosted identity settings, secret rotation, backups, or live headers. An absent repository setting does not prove an absent deployed control.

## Evidence and action boundary

Source inspection, configuration review, local diff/history review, and read-only dependency or secret scanning are source review. Keep scans local unless the user authorizes sending source or manifests to an external service. Redact credential values in outputs and reports. A scanner result or pattern match is a lead: validate the affected version, reachable path, configuration, and compensating control before calling it a vulnerability. If a scanner is unavailable, report its coverage gap and continue with review possible from source. Do not install or run untrusted dependencies merely to complete an audit.

Local tests with dummy fixtures may support a source finding when they stay inside the authorized workspace and cannot reach shared or external systems. Running a target-controlled build, test, or server may have side effects; inspect its scripts and required services first. Prefer bounded tests of the security invariant over a broad scan.

**Active testing of any running application component** includes crafted attack requests to a site or API, crawling, fuzzing, authentication trials, replaying webhooks or queue messages, changing records, and load or availability tests, even on staging or localhost. Before it starts, obtain explicit authorization for that activity plus the exact target and environment, allowed paths and accounts, prohibited actions and data, and practical rate/time limits. Ownership of a URL or a request to review code is not that authorization. If any boundary is missing, do source review and provide a proposed test plan; ask for the missing scope before sending attack traffic. Never target third-party services, real payment flows, other users' data, or availability without explicit inclusion. Stop on unexpected impact or scope drift.

## Findings and completion

Confirm a finding only when evidence establishes a lower-trust actor or input, the missing or defeated control, the affected resource, and a credible consequence under observed conditions. Cite a source location, configuration value, safe local reproduction, or authorized test result. Separate what was observed from what depends on an unknown deployed setting. Do not turn missing best practices, unexercised scanner alerts, or a plausible exploit story into confirmed vulnerabilities.

For each confirmed finding report: **problem and affected resource; evidence and conditions; possible harm; priority with reason; smallest effective fix at the trusted decision point; verification of the fix or a bounded way to verify it**. Order by demonstrated impact and practical exploitability. Keep unverified hypotheses in a separate section with the decisive missing fact and safe validation path. End with coverage, untested areas, checks run and their results, and residual risk. For a release review, state whether the checked evidence supports release, what blocks it, and what remains an owner decision; never label the whole system safe.
