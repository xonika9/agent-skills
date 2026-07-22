<p align="center">
  <img src="assets/x9-agent-skills-hero.jpg" alt="" width="100%">
</p>

<p align="center">
  Language: <strong>English</strong> · <a href="README.ru.md">Русский</a>
</p>

# x9 Agent Skills

[![View x9 Agent Skills on skills.sh](https://skills.sh/b/xonika9/agent-skills)](https://skills.sh/xonika9/agent-skills)
[![Validation workflow status](https://github.com/xonika9/agent-skills/actions/workflows/validate.yml/badge.svg)](https://github.com/xonika9/agent-skills/actions/workflows/validate.yml)
[![Latest release](https://img.shields.io/github/v/release/xonika9/agent-skills?label=release)](https://github.com/xonika9/agent-skills/releases/latest)

Practical [Agent Skills](https://agentskills.io/) for work that rarely fits into one prompt: source-backed research, controlled browser sessions, skeptical idea review, and reliable multi-step workflows.

- Verify current claims instead of trusting model memory.
- Keep authenticated browser work predictable and separate from your own tabs.
- Give long-running agent workflows checkpoints, stop conditions, and evidence.

The `x9-` prefix keeps the skills easy to find and avoids collisions with similarly named packages. In Claude Code, type `/x9` to see the installed plugin skills.

> I share field notes on AI models and developer tools in [Контролируемые галлюцинации](https://t.me/+DOZWlhI4r4EyYjgy), a Russian-language Telegram channel.

## Install

Start with the interactive installer. It lets you choose the skills, target agents, and installation scope:

```bash
npx skills add xonika9/agent-skills
```

Some workflows compose multiple skills. If you install selectively, choose the companion skills named in the catalog as well; the installer does not resolve those relationships automatically.

Want to inspect the catalog first?

```bash
npx skills add xonika9/agent-skills --list
```

If you want the complete package as a managed plugin, use the native route for your agent.

<details>
<summary><strong>Claude Code plugin</strong></summary>

```bash
claude plugin marketplace add xonika9/agent-skills
claude plugin install x9-agent-skills@xonika9
```

Skills use the plugin namespace, for example `/x9-agent-skills:x9-research`.

</details>

<details>
<summary><strong>Codex plugin</strong></summary>

```bash
codex plugin marketplace add xonika9/agent-skills
codex plugin add x9-agent-skills@xonika9
```

</details>

Clone or fork the repository only when you want to maintain your own variants. You will then need to merge upstream changes yourself.

## Compatibility

The skills use the open Agent Skills format and are packaged for Claude Code and Codex. Most also work in other compatible agents. Runtime-specific exceptions are stated in the catalog and inside each skill instead of being hidden behind a broad compatibility claim.

## Skill catalog

| Skill | Use it when | Runtime note |
| --- | --- | --- |
| [`x9-research`](skills/x9-research/SKILL.md) | A decision depends on current facts, primary sources, or conflicting evidence. | Portable; browser work follows `x9-browser-session` |
| [`x9-browser-session`](skills/x9-browser-session/SKILL.md) | Browser automation must preserve authentication without taking over your tabs. | Requires a compatible browser-control route; the included setup covers Chromium via CDP |
| [`x9-wb-product-search`](skills/x9-wb-product-search/SKILL.md) | You need a defensible Wildberries shortlist based on the exact variant, seller, price, and relevant reviews. | Wildberries-specific; install `x9-browser-session`; the current Claude Code or Codex runtime executes the workflow directly |
| [`x9-idea-critic`](skills/x9-idea-critic/SKILL.md) | You explicitly want a red-team review, cheaper alternatives, and disconfirming tests. | The GPT route from Claude Code uses `x9-codex-delegation` |
| [`x9-agent-instructions`](skills/x9-agent-instructions/SKILL.md) | Global agent rules, runtime adapters, and task briefs need clear ownership. | Supports Claude Code and Codex instruction files |
| [`x9-context-files-generator`](skills/x9-context-files-generator/SKILL.md) | A repository needs a README or agent instructions grounded in its actual commands and structure. | Portable |
| [`x9-skill-creator`](skills/x9-skill-creator/SKILL.md) | You are creating, auditing, or repairing an Agent Skill and need a verifiable contract. | Portable |
| [`x9-codex-delegation`](skills/x9-codex-delegation/SKILL.md) | Claude Code should delegate a bounded task to Codex and verify the real diff and checks afterward. | Claude Code only |
| [`x9-loop-engineering`](skills/x9-loop-engineering/SKILL.md) | An evaluator/optimizer loop needs checkpoints, retry limits, recovery, and human gates. | Portable; tool adapters may vary |
| [`x9-okf-adapt`](skills/x9-okf-adapt/SKILL.md) | A Markdown knowledge base must gain OKF metadata without silently changing document bodies. | Includes deterministic Python scripts |

## Three useful starting points

### Research a current question

Ask the agent to use `x9-research` when the answer needs fresh evidence:

```text
Use x9-research to compare the current plugin installation models for Claude Code and Codex.
Prioritize primary sources, show contradictions, and label anything you could not verify.
```

The workflow identifies the claims that carry the conclusion, opens current sources, looks for disconfirming evidence, and leaves a traceable answer.

### Work in an authenticated browser session

Use `x9-browser-session` when a task needs your existing login but should not interfere with your active tabs. The skill selects one browser route, opens a dedicated work tab, and keeps the action boundary explicit. The included [setup guide](skills/x9-browser-session/references/setup.md) covers Edge on macOS and explains what can be adapted for other Chromium browsers.

### Stress-test an idea before building it

Invoke `x9-idea-critic` explicitly when you want resistance rather than encouragement:

```text
Use x9-idea-critic. Find the assumptions most likely to kill this idea,
the cheapest credible alternative, and tests that could disprove it this week.
```

For longer autonomous work, pair the result with `x9-loop-engineering` so retries, checkpoints, and stop conditions are designed before the loop starts.

## Global instruction examples

[`global-files/AGENTS.md`](global-files/AGENTS.md) and [`global-files/CLAUDE.md`](global-files/CLAUDE.md) contain the shared personal core plus sanitized runtime adapters for Claude Code and Codex. They cover language preferences, authority boundaries, preservation, uncertainty, observable completion, documentation and browser routing, and tested Codex subagent behavior. Machine-specific installation paths are intentionally replaced with skill discovery by name.

Treat them as examples, not as files to overwrite blindly. A safe request is:

```text
Use x9-agent-instructions to review these examples and merge only the rules that fit my setup.
Preserve my existing instructions, paths, tools, and repository-specific sections.
```

## What you can verify

- Every skill has one canonical source under [`skills/`](skills/); the Claude Code and Codex packages point to the same files.
- CI validates skill structure, runs deterministic regression tests, checks plugin metadata, scans public files for sensitive data, and runs Gitleaks over Git history.
- User-visible changes are recorded in the [changelog](CHANGELOG.md), and published versions use semver tags and GitHub Releases.

## Updates

Update one globally installed skill:

```bash
npx skills update x9-research -g
```

Update all globally installed skills:

```bash
npx skills update -g
```

Plugin users can update through their agent's marketplace flow. Review [CHANGELOG.md](CHANGELOG.md) before adopting a new version if your workflows depend on runtime-specific behavior.

## Contributing and security

Bug reports, focused skill improvements, and reproducible compatibility findings are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request. For vulnerabilities or sensitive reports, follow [SECURITY.md](SECURITY.md) instead of creating a public issue. Community conduct is covered by the [Code of Conduct](CODE_OF_CONDUCT.md).

If this package saves you time, [star the repository](https://github.com/xonika9/agent-skills) so more people can find it. For new experiments and practical notes, follow [Контролируемые галлюцинации](https://t.me/+DOZWlhI4r4EyYjgy).

## License

[MIT](LICENSE). Use individual skills, adapt them, or assemble your own package.
