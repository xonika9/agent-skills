# Security Policy

## Reporting a vulnerability

Do not open a public issue for vulnerabilities, leaked credentials, unsafe browser behavior, or reports that contain private data.

Use [GitHub private vulnerability reporting](https://github.com/xonika9/agent-skills/security/advisories/new). Include:

- the affected skill, script, or plugin route;
- agent and runtime versions;
- the smallest reproducible example;
- realistic impact and required preconditions;
- a suggested fix, if you have one.

Remove unrelated secrets and personal data before submitting the report. The project aims to acknowledge a report within seven days. A fix or disclosure timeline depends on severity, reproducibility, and whether upstream runtimes are involved.

## Supported versions

Security fixes target the latest published release. Older versions may receive guidance, but are not maintained as separate support branches.

## Scope

Reports about this repository's skills, scripts, manifests, installation guidance, and browser-session boundaries are in scope. Vulnerabilities in Claude Code, Codex, browsers, marketplaces, or third-party CLIs should also be reported to their maintainers; this project can only address its own integration behavior.
