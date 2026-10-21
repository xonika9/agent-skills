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

Practical [Agent Skills](https://agentskills.io/) for Claude Code, Codex, OpenCode, and other agents. They turn a loose request into careful work: research with real sources, product picks made through your own browser, measured speed-ups, tests that actually catch bugs, and prompts agents follow.

The `x9-` prefix keeps the skills easy to find and avoids collisions with similarly named packages. In Claude Code or Codex, type `/x9` to see the installed plugin skills.

> I share field notes on AI models and developer tools in [Контролируемые галлюцинации](https://t.me/+DOZWlhI4r4EyYjgy), a Russian-language Telegram channel.

## What it looks like

You talk to the agent in your own words; the matching skill takes over.

| You say | You get |
| --- | --- |
| "Research whether this claim is true" | An answer built on current sources, with the key claims checked, counter-evidence searched for, and a clear note on what could not be confirmed. |
| "Find me a good kettle on Wildberries under 3,000 ₽" | A short list made in your logged-in session after checking the exact variant, the seller, the price per unit, fresh low ratings, and buyer photos. |
| "The catalog page is slow, find out why" | A ranked list of measured causes. A fix stays only when repeated before-and-after measurements show it helped. |

## What makes these skills different

- **They check instead of guessing.** Facts, tests, and speed-ups are backed by evidence, and anything unverified is called out as such.
- **They ask before anything risky.** Deleting, spending money, publishing, or changing your settings waits for your approval.
- **They remember earlier work.** Audits leave notes in the project, so the next run shows what was fixed and what is new, and does not raise again what you deliberately declined.
- **They work in any compatible agent.** Every skill is checked in OpenCode, Claude Code, and Codex.

## Install

```bash
npx skills add xonika9/agent-skills
```

The interactive installer lets you choose the skills, agents, and installation scope. Afterwards, ask your agent to check them; [`x9-onboarding`](skills/x9-onboarding/SKILL.md) shows what is ready and what is still missing:

```text
Check whether my installed x9 skills are ready to use
```

<details>
<summary><strong>Claude Code and Codex plugins</strong></summary>

To install the complete package as a managed plugin:

```bash
claude plugin marketplace add xonika9/agent-skills
claude plugin install x9-agent-skills@xonika9
```

```bash
codex plugin marketplace add xonika9/agent-skills
codex plugin add x9-agent-skills@xonika9
```

In Claude Code, plugin skills use the plugin namespace, for example `/x9-agent-skills:x9-research`.

</details>

<details>
<summary><strong>Installing only some skills</strong></summary>

Some skills rely on others, and the installer does not add them automatically. If you install selectively, add the companions:

| If you install | Also install |
| --- | --- |
| `x9-research` | `x9-browser-session` for browser and social sources, `x9-okf-docs` for saving research |
| `x9-wb-product-search` | `x9-browser-session` |
| `x9-architecture-scout` | `x9-diagrams` |
| `x9-context-files-generator`, `x9-skill-creator`, `x9-okf-docs` | `x9-agent-instructions` |
| `x9-personal-vault` | `x9-okf-docs`, `x9-agent-instructions`; `x9-context-files-generator` to tidy an existing `CLAUDE.md` |
| `x9-idea-critic` in Claude Code | `x9-codex-delegation` for the GPT critic |
| `x9-appsec`, `x9-test-quality` | `x9-context-files-generator` (optional) when the project has no `AGENTS.md` |

Add `x9-onboarding` if you want the readiness check. To browse the catalog without installing, run `npx skills add xonika9/agent-skills --list`.

</details>

Clone or fork the repository only when you want to maintain your own variants; you will then merge upstream changes yourself.

## Skill catalog

### Everyday work

#### [`x9-research`](skills/x9-research/SKILL.md)

Agents often pass off a plausible answer from memory as research. This skill makes them open current sources, check the claims the conclusion rests on, look for counter-evidence, and say plainly what could not be confirmed. X/Twitter is read through your logged-in browser; Reddit and forums count as lived experience, not proof. On request, the result is saved as a Markdown note or a readable HTML report and can be updated later.

**Ask:**

```text
research this
```

```text
research X and give me an HTML report
```

#### [`x9-browser-session`](skills/x9-browser-session/SKILL.md)

For a personal task the result depends on your account, region, cart, or feed, so a clean test browser gives the wrong answer. This skill lets the agent work in your logged-in browser through a separate automation profile, in its own tab, without touching yours. It stops at a CAPTCHA instead of trying to get around it.

**Ask:**

```text
open this in my browser
```

```text
use my logged-in session
```

**Needs:** one-time setup from the [setup guide](skills/x9-browser-session/references/setup.md), which you can hand to the agent; a tested recipe covers Edge on macOS.

#### [`x9-wb-product-search`](skills/x9-wb-product-search/SKILL.md)

A Wildberries rating rarely tells the whole story: reviews may belong to another variant, the seller may be questionable, and the price depends on your account and region. The skill checks the exact variant, seller, price per unit, fresh low ratings, recurring complaints, and buyer photos, and only then gives you a short list.

**Ask:**

```text
find a good kettle on Wildberries under 3,000 ₽
```

**Needs:** `x9-browser-session`; in Claude Code, a session running on Opus.

#### [`x9-video-transcripts`](skills/x9-video-transcripts/SKILL.md)

Recorded a dozen videos and can no longer remember which one covers what? The skill transcribes your video and audio on your own machine, from one file to a whole folder, into subtitles and timestamped text, and later finds the moment you said something. Nothing is uploaded, and a rerun processes only new or changed files.

**Ask:**

```text
transcribe these videos
```

```text
where in my videos did I talk about pricing?
```

**Needs:** `python3`, `ffmpeg`, and `whisper-cli`; about 875 MB of models download on first use. Tested on macOS with Apple Silicon.

#### [`x9-personal-vault`](skills/x9-personal-vault/SKILL.md)

Gathers notes and documents scattered across folders into one personal vault: an inbox, an archive, and one folder per matter, whether that is your health or a single tax question. The agent shows one plan listing every move and changes nothing until you approve it; copies are verified, and everything except a separately confirmed deletion can be undone. After that, ordinary agent sessions keep the vault in order without calling the skill.

**Ask:**

```text
organize my notes folder
```

```text
merge these folders into one vault
```

#### [`x9-obsidian`](skills/x9-obsidian/SKILL.md)

Finds, checks, and edits notes in an Obsidian vault: keeps links intact when files move, repairs broken ones, and works with properties, Bases, and Canvas. Audits are kept separate from fixes, and the skill follows your folder structure.

**Ask:**

```text
find broken links in my vault
```

```text
rename this note and keep its links
```

#### [`x9-idea-critic`](skills/x9-idea-critic/SKILL.md)

For when you want pushback, not another cheerful brainstorm. Independent Claude and GPT critics review the idea, and you get a recommendation, every problem that matters, a stronger version of the idea, and one next step with a clear go or stop signal. When the idea concerns your code, a separate scout reads the repository first, so the critics see facts nobody mentioned.

**Ask:**

```text
criticize this idea
```

```text
red-team this plan
```

**Needs:** works with one provider too, and then says there was no independent review.

#### [`x9-explain-again`](skills/x9-explain-again/SKILL.md)

Say you did not understand the previous answer, and the skill explains that same point differently: plainer words, an example, an analogy, or a step-by-step chain of causes. It does not restart the topic or inflate the answer.

**Ask:**

```text
I didn't get that, explain it differently
```

#### [`x9-diagrams`](skills/x9-diagrams/SKILL.md)

Picks the right kind of diagram, or tells you a table would work better, and produces an editable source in Excalidraw, Mermaid, draw.io, or SVG. When a diagram grows too dense, it splits it into an overview and detailed views instead of shrinking the text, and checks the result by actually rendering it.

**Ask:**

```text
draw a diagram of this flow
```

```text
convert this Mermaid diagram to draw.io
```

#### [`x9-codex-imagegen`](skills/x9-codex-imagegen/SKILL.md)

Lets Claude Code, OpenCode, or another agent generate images through your Codex subscription, with no separate image API key. Codex writes the image prompt itself, so quality does not depend on the model you are working with. You get a verified PNG together with the final prompt.

**Ask:**

```text
generate an illustration for this article with Codex
```

**Needs:** Codex with a ChatGPT login. Inside Codex itself the skill is not needed.

### Building software

#### [`x9-web-stack`](skills/x9-web-stack/SKILL.md)

A template for TypeScript web apps: the tools, how the code is organized, and the rules that keep the project in shape. Code is split into modules by product area, each with its own entry point, its own tables, and one-way dependencies, and the linter enforces these boundaries. A new project starts from a scaffold that has been built and run end to end (Bun, React, Hono, PostgreSQL), and an existing project on any stack gets an audit of its structure and rules. The rules can be written into `AGENTS.md`, so agents follow them in everyday work.

**Ask:**

```text
create a project on our stack
```

```text
audit this project's structure and stack
```

**Needs:** Python 3, Bun, Node, Git, and Docker for a new project.

#### [`x9-appsec`](skills/x9-appsec/SKILL.md)

Follows trust boundaries through the whole application: browser, API, background jobs, data stores, integrations, and deployment. During development it checks the changed path; before release it runs an audit and reports each finding with evidence, possible harm, priority, and the smallest fix. It never sends attack requests to a running service without your explicit permission and a named target.

**Ask:**

```text
check this change for security issues
```

```text
run a security audit before release
```

#### [`x9-test-quality`](skills/x9-test-quality/SKILL.md)

Agents happily add tests that raise the count but catch nothing. The skill stops such tests before they land, finds redundant and flaky ones in an existing suite, and advises how to organize testing for a project of your size. Tests, configuration, and CI change only after your approval.

**Ask:**

```text
review our tests
```

```text
our tests are flaky
```

#### [`x9-performance`](skills/x9-performance/SKILL.md)

Instead of adding a cache just in case, the agent measures where time, memory, or money actually go and keeps a change only when repeated before-and-after measurements prove it helped. An audit returns a ranked list: what can be fixed now, which decisions are yours along with their payoff and price, and where data is missing.

**Ask:**

```text
why is this page slow?
```

```text
run a performance audit
```

#### [`x9-architecture-scout`](skills/x9-architecture-scout/SKILL.md)

A read-only architecture review delivered as an HTML report: component boundaries, dependencies, ownership, risky change hotspots, and a comparison of possible directions with evidence and confidence. The code stays untouched.

**Ask:**

```text
audit this codebase's architecture
```

**Needs:** `python3` and `x9-diagrams`.

#### [`x9-cto`](skills/x9-cto/SKILL.md)

A CTO's call on product scope, architecture, or a large technical commitment, grounded in your repository. It can also lead delivery to a working user outcome and check executors' reports against real evidence instead of taking them on trust.

**Ask:**

```text
should we move to X?
```

```text
look at this as a CTO
```

**Needs:** nothing extra for a consultation; the autonomous `auto` mode needs the Compound Engineering skills `ce-plan`, `ce-work`, `ce-simplify-code`, and `ce-code-review`.

#### [`x9-decision-map`](skills/x9-decision-map/SKILL.md)

A large initiative stalls when open choices, missing facts, and nice-to-have work are mixed together. Before planning, the skill builds one decision map: what is decided, which questions remain, what depends on what, and what to find out next. A later session picks it up without starting over.

**Ask:**

```text
map the decisions before we plan
```

#### [`x9-task-graph`](skills/x9-task-graph/SKILL.md)

Turns an approved plan into connected work items ready for a tracker: dependencies, what can start right away, and a check that every requirement of the plan landed in some item. It does not reopen decisions or invent work.

**Ask:**

```text
turn this approved plan into work items
```

### Working with agents

#### [`x9-onboarding`](skills/x9-onboarding/SKILL.md)

After an install or update, checks which skills are ready and what is still missing: a command-line tool, an account, or another component. It can also compare your Claude Code, Codex, or OpenCode settings with the author's profile and merge the differences you choose, keeping a backup.

**Ask:**

```text
check whether my x9 skills are ready
```

#### [`x9-agent-instructions`](skills/x9-agent-instructions/SKILL.md)

Describe a task in your own words, even by dictation, and get a ready prompt: goal, constraints, sources, authority, deliverable, and what counts as done. It also reviews prompts and instruction files you already have, including global `AGENTS.md` and `CLAUDE.md`, and explains what each suggested change gives you.

**Ask:**

```text
write me a prompt for this task
```

```text
review these instructions
```

<details>
<summary>Sources the method is based on</summary>

- [Prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)
- [Prompting Claude Fable 5.1](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1)
- [Prompting Claude Fable 5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5)
- [Prompting Claude Opus 5.5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5)
- [Prompting Claude Opus 5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5)
- [The new rules of context engineering for Claude 5 generation models](https://claude.com/blog/the-new-rules-of-context-engineering-for-claude-5-generation-models)
- [Using GPT-6 Astra](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6-astra)
- [Using GPT-5.6](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.6)

</details>

#### [`x9-context-files-generator`](skills/x9-context-files-generator/SKILL.md)

Creates or updates a repository's `README.md`, `AGENTS.md`, and `CLAUDE.md` from its real commands, structure, and CI, not from a generated file tree and generic advice. Ready-made rule blocks for working discipline, documentation, dependency updates, and more can be added on request.

**Ask:**

```text
create AGENTS.md for this repository
```

```text
update the README
```

#### [`x9-skill-creator`](skills/x9-skill-creator/SKILL.md)

Turns a repeated process into an Agent Skill or audits one you already have: when it triggers, how it is structured, its safety boundaries, and its checks for Claude Code, Codex, and the portable format. Every audit also suggests what can be removed.

**Ask:**

```text
turn this process into a skill
```

```text
audit this skill
```

#### [`x9-loop-engineering`](skills/x9-loop-engineering/SKILL.md)

If you keep walking the agent through the same cycle by hand (explore, plan, do, check, fix), this skill designs a bounded agent loop with saved state, checkpoints, and stop conditions. `x9-skill-creator` can then package it as a skill.

**Ask:**

```text
design an agent loop for this workflow
```

#### [`x9-okf-docs`](skills/x9-okf-docs/SKILL.md)

Gives each Markdown document a short [OKF](https://github.com/GoogleCloudPlatform/open-knowledge-format) header (type, title, a one-line description, and tags), so an agent can pick the right file without opening it. Headers are added as documents are written, and a whole folder can be converted in one step without changing any document text.

**Ask:**

```text
add OKF metadata
```

```text
migrate this folder to OKF
```

#### [`x9-codex-delegation`](skills/x9-codex-delegation/SKILL.md)

Lets Claude Code hand a well-defined part of the work to Codex and then check the actual diff instead of trusting the report. Useful when Codex suits a task better or to spread work across subscription limits.

**Ask:**

```text
hand this part to Codex
```

**Needs:** Claude Code with Codex installed.

#### [`x9-opencode-sessions`](skills/x9-opencode-sessions/SKILL.md)

Finds, reads, continues, and coordinates other OpenCode chats, waits for them to finish, and collects the results. A message is sent only after you see a preview.

**Ask:**

```text
find the OpenCode session about the migration
```

```text
wait for that session to finish
```

**Needs:** OpenCode V2.

## Compatibility

The skills use the open Agent Skills format and are checked in OpenCode, Claude Code, and Codex. Three are tied to specific agents by design: `x9-codex-delegation` runs only in Claude Code, `x9-codex-imagegen` is for agents other than Codex, and `x9-opencode-sessions` runs only in OpenCode V2.

## Global instruction files

The repository also includes example global instructions for [OpenCode](global-files/opencode/AGENTS.md), [Codex](global-files/codex/AGENTS.md), and [Claude Code](global-files/claude/CLAUDE.md): language, what the agent may do on its own, preserving your changes, verifiable completion, browser routing, and subagent use. Do not overwrite your own file with them. Back it up and ask the agent:

```text
Use x9-agent-instructions to review these examples and merge only the rules that fit my setup
```

## Updates

```bash
npx skills update -g              # all globally installed skills
npx skills update x9-research -g  # one skill
```

Plugins update through your agent's marketplace. What changed in each release, and what to do when upgrading, is in [CHANGELOG.md](CHANGELOG.md).

## Contributing and security

Bug reports, focused skill improvements, and reproducible compatibility findings are welcome; read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request. Report vulnerabilities through [SECURITY.md](SECURITY.md), not a public issue. Community conduct is covered by the [Code of Conduct](CODE_OF_CONDUCT.md).

If this package saves you time, [star the repository](https://github.com/xonika9/agent-skills) so more people can find it. For new experiments and practical notes, follow [Контролируемые галлюцинации](https://t.me/+DOZWlhI4r4EyYjgy).

## License

[MIT](LICENSE). Use individual skills, adapt them, or assemble your own package.
