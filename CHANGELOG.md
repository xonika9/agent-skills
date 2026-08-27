# Changelog

## Unreleased

### Highlights

- Telegram tasks now default to the authenticated Telegram Web session instead of the macOS app or Computer Use, while explicit desktop-app requests remain supported.
- `x9-opencode-sessions` now preserves large Sessions API responses instead of receiving truncated JSON when the OpenCode CLI writes to a captured pipe.
- Added `x9-decision-map` for durable, pre-plan records of material decisions, sharp open questions, fog, dependencies, and the next evidence-gathering frontier.
- Added `x9-task-graph` for turning an approved implementation-ready plan into dependency-aware, tracker-ready vertical work items with complete source coverage.
- Added `x9-architecture-scout` for read-only architecture reports that compare plausible directions and expose boundaries, ownership, coupling, and change hotspots.
- Added `x9-explain-again` for repairing explicit confusion about the immediately preceding substantive answer without turning a new explanation request into a false reference.
- `x9-agent-instructions` now requires completion bars to account for known enumerable sets and makes branch-specific context pointers conditional and testable.
- `x9-skill-creator` now classifies invocation separately for every claimed runtime and checks the ownership boundary before it creates or judges a skill owner.
- `x9-context-files-generator` now keeps root-local rules in root `AGENTS.md` while assigning branch-specific procedures to profile documents with verified conditional pointers.
- `x9-agent-instructions` and `x9-context-files-generator` now distinguish model invocation in each supported runtime from portable structural compatibility.

### Install / update

- Update `x9-opencode-sessions` to apply the large-transcript fix; its command interface is unchanged.
- Full-plugin users receive the four new skills on update. Selective installations can add only the process that matches the problem; `x9-task-graph` still requires an approved plan.

### Compatibility

- Long OpenCode sessions can now be inspected without transcript degradation caused by the CLI pipe buffer.
- The new skills are structurally compatible with Claude Code and Codex; their stated boundaries remain in force: decision maps are not implementation plans, task graphs do not publish or implement work, architecture scouting is read-only, and explanation repair needs a recoverable immediately previous answer.

### Breaking changes

None.

## 3.0.0 - 2026-08-24

### Highlights

- Native worker briefs now use English across OpenCode, Claude Code, and Codex while preserving load-bearing source wording and returning user-facing results in the user's language.
- Global instructions now carry a compact worker-brief contract that requires non-derivable context, proportional evidence, scope fidelity, and specialist-prompt precedence without loading the full `x9-agent-instructions` skill before dispatch.
- Applied the August repository audits: package metadata now stays synchronized across Claude Code and Codex, published global cores are checked in CI, installed global files are checked byte-for-byte before release, and documented package checks match the automated gate.
- Hardened `x9-opencode-sessions` metadata filtering so session locations remain available for precise selection while internal skill text stays private.
- Documented the repository-wide package validation and release gates, including their evidence, blocking conditions, and known coverage gaps.
- `x9-idea-critic` now runs every selected Opus and GPT critic at `high` effort, assigns every `full` critic its declared lens, and uses sealed evidence packets instead of broad source access. Claude CLI routes disable inherited customizations and tools, Codex sealed runs reject re-enabled hooks, and native routes distinguish accepted controls from unavailable post-run telemetry.
- `x9-idea-critic` now ends critiques with any load-bearing questions followed by a direct decision, one immediate action, and an observable condition for proceeding, revising, or stopping.
- Added `x9-onboarding` to check whether installed or updated `x9-*` skills are ready, distinguish check coverage from readiness, and provide a manual checklist without changing the environment.
- Added an OpenCode route to `x9-idea-critic`, combining fresh Claude CLI sessions for Opus critics with explicitly identified native GPT subagents.
- Added `x9-opencode-sessions` for bounded OpenCode V2 session discovery, text-only message inspection, activity and completion checks, and preview-first cross-branch coordination.
- Split the installable global instructions into dedicated OpenCode, Codex, and Claude Code files while preserving their shared personal core.

### Install / update

- Full-plugin users receive `x9-opencode-sessions` on update. Individual installations require Python 3 and the OpenCode V2 `opencode2` CLI.
- Full-plugin users receive `x9-onboarding` on update. Selective installations should include it when the user wants an installation-readiness check.
- Existing users can link each harness to its matching file under `global-files/<harness>/`; back up local global instructions before replacing them with links.

### Compatibility

- Changes to production package/release gates and release workflows now require `Unreleased` coverage, while test-only and auxiliary files remain exempt.
- Skill validation accepts a YAML boolean only for `metadata.internal`; string values and booleans on other metadata keys are rejected.
- Onboarding declarations now reject requirement runtimes that are not listed in their owning skill's `supported_runtimes`.
- `x9-idea-critic` now supports independent OpenCode routes when Claude CLI exposes the required Opus controls or the live subagent catalog explicitly identifies a GPT-family agent; default and full runs still require every selected route for a complete result.
- `x9-opencode-sessions` is OpenCode V2 only. It uses native `subagent` for the current parent session's children and the V2 Sessions API for other OpenCode branches; Claude Code, Codex, and cross-harness sessions are unsupported.
- `x9-browser-session` now supports OpenCode through the live `chrome-devtools` MCP, with the same task-page, private-surface, and unattended fallback safeguards as its existing routes.
- `x9-onboarding` has read-only adapters for OpenCode, Claude Code, and Codex. Other runtimes report `PARTIAL` coverage and `BLOCKED` readiness; it never installs dependencies, authorizes accounts, changes files or configuration, or restarts a runtime.
- The former top-level `global-files/AGENTS.md` and `global-files/CLAUDE.md` paths were replaced by harness-specific paths.

### Breaking changes

- `x9-onboarding` introduces no breaking changes.
- Skills that declare `metadata.internal` must use the YAML boolean `true` instead of the string `"true"`.
- Consumers of the published global files must update references to the new harness-specific paths.

## 2.4.0 - 2026-08-17

### Highlights

- Made `x9-browser-session` serialize Avito browsing across agents and controllers,
  reuse captured listing data, passively re-inspect transient IP or security checks
  after five seconds, and stop without escalating controller fallbacks when the check
  persists or Avito returns an explicit throttling or access-control signal.
- Synchronized the published Codex global-instruction example with the current safe
  reconciliation rules for non-idempotent task creation.

### Install / update

- Full-plugin users can update in place. Selective installations should update
  `x9-browser-session`; no skill-name or configuration migration is required.

### Compatibility

- Browser routing outside Avito is unchanged. Avito work now runs serially and returns
  `DEGRADED` instead of switching controllers when throttling or access controls persist.
- Existing global-instruction examples remain opt-in references; the new Codex task
  reconciliation rules do not modify personal runtime configuration automatically.

### Breaking changes

None.

## 2.3.0 - 2026-08-02

### Highlights

- Added an extensible `chrome-devtools` MCP allowlist, initially containing `avito.ru`; matching domains bypass the browser extension in both runtimes and preserve `agent-edge` only as the unattended fallback.
- Synchronized the published global-instruction examples with the current question-format and browser-retrieval fallback rules while keeping their shared core byte-identical.
- Made `x9-idea-critic` turn upheld criticism into a self-contained stronger proposal, with a change map and verdict-specific handling for revised, surviving, killed, or unproven ideas.
- Hardened `x9-loop-engineering` with conditional patterns for authoritative derived state, recoverable public lifecycle mutations, version-scoped continuity, task-first self-repair, and evidence-bound realized execution traces.
- Made repository-backed diagram creation source-first, preserve existing structure and supported fonts until rendered proof passes, and use a clipboard round trip for faithful browser verification.
- Tightened Excalidraw structure checks for escaped control tokens, native soft wrapping, semantic hard breaks, deleted bindings, and target-version normalization.
- Strengthened rendered diagram evidence with content-viewport fit checks, post-normalization stability, explicit whole-view versus scrollable delivery, and protection from blocking native choosers.

### Install / update

- Full-plugin users can update in place; no data or skill-name migration is required.
- Selective Codex installations that use an allowlisted browser target need the `chrome-devtools` MCP route from the `x9-browser-session` setup guide.

### Compatibility

- Browser routing outside entries in the `chrome-devtools` MCP allowlist is unchanged; the list currently routes `avito.ru` through MCP in Codex as well as Claude Code.
- Existing `x9-idea-critic` modes and provider routes are unchanged; successful critiques now include an evidence-grounded next version of the idea.
- Existing simple and linear workflow guidance is unchanged; the new loop recovery, versioning, self-repair, and lineage patterns apply only when those mechanisms exist.
- Existing Excalidraw scenes remain supported, but invalid control text, dangling bindings, unstable wrapping, or unsupported hard line breaks now fail the stricter checker until corrected or explicitly allowed.

### Breaking changes

None.

## 2.2.0 - 2026-07-29

### Highlights

- Renamed `x9-okf-adapt` to `x9-okf-docs` and reduced its always-loaded instructions to a short route selector; maintenance, adoption, and migration details now load only when needed.
- Updated the skill for OKF v0.2 with separate official and curated validation profiles, reserved-file handling, truthful `generated` metadata, and read-only-by-default v0.1 migration.
- Added incremental `--touch` migration so substantively edited documents converge to OKF v0.2 without scanning or rewriting the rest of a repository.
- Made `x9-okf-docs` the canonical owner of version-specific OKF rules. On the first OKF write, it replaces a copied version, field contract, or former skill name in `AGENTS.md` while preserving repository-specific scope.
- Made durable research read `generated.at` first while retaining `timestamp` as a legacy fallback.

### Install / update

- Existing OKF v0.1 repositories require no immediate rewrite. Normal work can migrate named documents through `--touch` and lazily repair stale repository instructions; bulk audit remains optional.
- Full-plugin users receive `x9-okf-docs` on update. Individual-skill users must remove `x9-okf-adapt`, install `x9-okf-docs`, and may leave repository instructions to self-repair on the first OKF write.

### Compatibility

- OKF v0.1 remains readable through documented fallbacks. Incremental migration keeps `timestamp` synchronized by default and requires Python 3, Ruby/Psych, and an explicit actor.

### Breaking changes

- The curated profile now writes `generated.by` and `generated.at` instead of creating legacy `timestamp`; callers applying manifests must pass `--actor`. Official OKF validation is available separately through `--profile okf`.
- The discoverable skill name changed from `x9-okf-adapt` to `x9-okf-docs`; the former name is not retained as a duplicate alias.

## 2.1.0 - 2026-07-29

### Highlights

- Renamed `x9-excalidraw-diagrams` to `x9-diagrams` and expanded it into one research-backed method for choosing, creating, reviewing, and converting native Excalidraw, Mermaid, and draw.io diagrams.
- Added format-specific Mermaid and draw.io adapters while preserving the native Excalidraw checker, current font/binding rules, and regression tests.
- Kept the distributed skill focused on operational guidance by removing the maintainer-only research ledger.
- Added a constraint-based format matrix, explicit ownership boundary with specialized Mermaid-only skills, and separate structural plus rendered completion gates for all supported formats.
- Split completion evidence by selection, creation, conversion, and review; tightened degraded-result reporting and the Excalidraw basic-subset checker without requiring both supported fonts in every scene.

### Install / update

- Full-plugin users can update in place and invoke `x9-diagrams`. Individual-skill users must remove `x9-excalidraw-diagrams` and install `x9-diagrams`; the old name is not retained as an alias.

### Compatibility

- `x9-diagrams` remains portable across Claude Code and Codex. Complete proof requires Python 3 plus a faithful Excalidraw renderer, a target-compatible Mermaid renderer, or a compatible diagrams.net editor/exporter for the selected format; missing visual proof is reported as `DEGRADED`.

### Breaking changes

- The public skill name and path changed from `x9-excalidraw-diagrams` to `x9-diagrams`. Direct invocations, selective-install records, and local symbolic links using the old name must migrate to the new name.

## 2.0.0 - 2026-07-28

### Highlights

- Made `x9-idea-critic` select the promised provider family explicitly, isolate volatile Claude Code and Codex mechanics in runtime adapters, and declare a reproducible lens/provider matrix for `full` mode.
- Made `x9-research` leave an inspectable independent-review disposition, assign browser and delivery rules to one owner, support correct HTML language metadata, and validate deterministic Markdown/HTML requirements with a bundled regression-tested checker.
- Made `x9-skill-creator` structural validation runtime-aware for portable Agent Skills, Claude Code, and Codex, with stricter frontmatter constraints, duplicate-key detection, and complete bundled-resource reachability checks.
- Updated the Claude Code adapter for current trigger and frontmatter behavior, and removed duplicated judge-checklist cardinality from batch audits.
- Made `x9-agent-instructions` reviews report-first, pair every retained change with a concise practical rationale, and apply only explicitly approved recommendations.
- Made `x9-skill-creator` load `x9-agent-instructions` as the required rubric for agent-facing prose while keeping skill-audit reporting self-contained.
- Made `x9-agent-instructions` reference installed skills by discoverable name, reject machine-specific `SKILL.md` paths, and omit redundant requests to read repository context already injected by the runtime.
- Made `x9-context-files-generator` load `x9-agent-instructions` as a bounded companion rubric for agent-facing prose while keeping repository structure, preservation, and README work under its own contract.
- Added the Excalidraw workflow now published as `x9-diagrams`, with fit-to-view legibility, role-based typography, controlled routing, a render-and-inspect completion gate, and structural detection of clipped explicit text lines.
- Made persistent `x9-skill-creator` audit reports follow the user's requested or request-carrier language through one batch-wide `Report language` tag while preserving exact technical literals, source quotations, and validator output.

### Install / update

- Existing `x9-idea-critic` and `x9-research` users can update in place; no dossier migration is required.
- Structural validation now accepts repeatable `--runtime portable|claude|codex` flags; omitting the flag keeps the portable profile as the default.
- The full plugin already installs both required skills. Users who copy individual skills should install `x9-skill-creator` together with `x9-agent-instructions`.
- Users who copy `x9-context-files-generator` individually should install `x9-agent-instructions` alongside it for complete agent-file creation and review.
- The diagram skill is included in the full plugin and can also be installed individually as `x9-diagrams`.

### Compatibility

- `x9-idea-critic` still supports Claude Code and Codex, but unavailable provider-family selection now fails the affected route instead of silently substituting another model.
- `x9-research` HTML delivery now requires Python 3 for deterministic pair validation and accepts the document's actual BCP 47 language tag instead of forcing Russian metadata.
- `x9-skill-creator` now declares its existing Python 3 and Ruby/Psych validation dependency explicitly. Existing portable skills remain valid, while runtime-specific frontmatter must be checked with the matching profile.
- Without `x9-agent-instructions`, `x9-skill-creator` can still run structural checks but reports full Create, Audit, and Fix work on agent-facing prose as degraded.
- Without `x9-agent-instructions`, `x9-context-files-generator` keeps README, repository-evidence, and structural work available but reports agent-file instruction quality as degraded.
- `x9-diagrams` is portable across Claude Code and Codex. Its Excalidraw structural checker requires Python 3; visual proof requires a faithful renderer or editor and is reported as degraded when neither is available.

### Breaking changes

- `x9-research` HTML delivery now requires Python 3; without it the Markdown evidence remains usable, but HTML validation is reported as degraded instead of complete.
- Validation is intentionally stricter: unsupported runtime fields, non-string portable metadata values, overlong `compatibility`, and unreachable bundled resources now fail instead of passing silently.
- A standalone `x9-skill-creator` installation now requires `x9-agent-instructions` before it can claim a complete instruction-quality review.
- A standalone `x9-context-files-generator` installation now requires `x9-agent-instructions` before it can claim a complete or clean agent-file result; README-only work is unchanged.
- No diagram-skill breaking changes were introduced in this release.

## 1.6.0 - 2026-07-28

### Highlights

- Aligned the English and Russian README copy for Codex skill discovery, browser setup, context-file generation, idea review, delegation limits, and prompt-engineering references.
- Synchronized the published global instruction examples with the audited Claude Code and Codex policies, including shared skill routing and a self-directed execution contract.
- Made the Codex example retain undocumented subagent capabilities only after bounded live probes, and aligned its routing claims with verified `agent_type`, `fork_turns`, and `service_tier` behavior.
- Made `x9-browser-session` the canonical owner of browser route selection and removed its circular dependency on global Claude Code instructions.

### Install / update

- Users who copied the published global instruction examples should resynchronize them after updating; plugin and skill installation routes are unchanged.

### Compatibility

- Existing browser routes, skill names, and installation routes remain compatible. Global subagent policy now distinguishes verified runtime controls from command-internal routing that the caller cannot set.

### Breaking changes

- None.

## 1.5.0 - 2026-07-28

### Highlights

- Made `x9-agent-instructions` reviews treat embedded commands as evidence rather than authority, place retained global rules by scope, and verify shared personal cores byte-for-byte.
- Made `x9-context-files-generator` remove derivable repository context only when its absence cannot change the agent's next decision or action.
- Clarified the boundary between `x9-skill-creator` and `x9-agent-instructions`, reduced duplicated audit guidance, and made symlinked source skills valid batch-audit targets.
- Corrected skill size metrics to measure the instruction body instead of frontmatter.
- Added a repository-local maintainer release workflow without exposing it through the public Skills installer.

### Install / update

- Existing users can update through their current Agent Skills, Claude Code, or Codex installation route without migration steps.

### Compatibility

- Existing skill names, triggers, installation routes, and repository-context ownership remain unchanged.

### Breaking changes

- None.

## 1.4.0 - 2026-07-26

### Highlights

- Expanded `x9-agent-instructions` from global instruction files to prompts and agent-instruction files generally. It now distinguishes writing from review, returns recommended changes with their rationale and diff, and uses one rubric for both modes.
- Refined prompt guidance around outcome-led briefs: retain facts an executor cannot derive, boundaries, required evidence, and an observable completion bar; remove redundant process scripting and generic verification padding.

### Install / update

- Existing users can update through their current Agent Skills, Claude Code, or Codex installation route without migration steps.

### Compatibility

- Existing workflows for drafting one-off prompts and reviewing global `AGENTS.md` and `CLAUDE.md` remain supported. Review now also applies to other prompt and agent-instruction files.

### Breaking changes

- None.

## 1.3.0 - 2026-07-24

### Highlights

- Clarified browser routing for both runtimes: local web development and explicit in-app requests use the runtime's in-app browser, while every other browser task uses the runtime-specific default — its Edge extension in Codex and `chrome-devtools` MCP in Claude Code — with `agent-edge` reserved as an unattended fallback.
- Expanded the `x9-browser-session` skill with sticky explicit-surface selection, shared Edge focus-safety and task-tab isolation rules, and defined runtime-specific fallback chains.
- Synchronized the sanitized global instruction examples with the runtime-specific routes and their explicit in-app browser boundaries.

### Install / update

- Existing users should keep the Edge extension and local CDP endpoint configured as described in the `x9-browser-session` setup guide. No migration steps are required.

### Compatibility

- Local web development and explicit in-app or built-in browser requests continue to use the runtime's in-app browser, and that explicit choice stays sticky through connection failures.
- Other browser work now follows a defined runtime-specific default and fallback chain instead of a generic runtime selection. The `agent-edge` route remains an unattended fallback for periods when the user is not working in Edge.

### Breaking changes

- None.

## 1.2.0 - 2026-07-23

### Highlights

- Added explicit research delivery routing: plain requests stay in chat, save or folder requests persist Markdown, and HTML requests add a same-basename reader presentation without replacing the evidence-oriented work file.
- Added OKF-frontmatter discovery for existing subject areas and research files, including automatic synchronization of an existing same-basename HTML presentation when the underlying research is updated.
- Added a reusable responsive light editorial theme without imposing one report layout, plus a Russian HTML editing pipeline with `humanizer-ru` and a post-edit fact and citation check.
- Made one-off agent briefs follow the user's language by default while preserving exact technical literals and documented target-language constraints.

### Install / update

- Existing users can update through their current Agent Skills, Claude Code, or Codex installation route without migration steps.

### Compatibility

- Existing plain research requests remain chat-only. Existing saved research remains Markdown-first; a missing HTML file is created only when HTML output is explicit, while an already paired HTML file follows later research updates automatically.
- Existing skill names and installation routes are unchanged. Standing machine-facing policy remains English by default; only one-off brief language selection was clarified.

### Breaking changes

- None.

## 1.1.0 - 2026-07-23

### Highlights

- Made idea-critique synthesis preserve every verdict-changing finding while turning upheld issues into a complete, dependency-aware revision agenda.
- Refined loop engineering around the smallest sufficient topology, hierarchical ownership, proportional contracts and evidence, durable resumption, lifecycle handling, and correctly classified retry budgets.
- Made the published global-instruction examples keep Russian as the carrier language of technical explanations while separating exact English identifiers and reference names from narrative prose.

### Install / update

- Existing users can update through their current Agent Skills, Claude Code, or Codex installation route without migration steps.

### Compatibility

- Kept existing skill names and installation routes unchanged while expanding the public guidance and output contracts for idea critique and loop engineering.

### Breaking changes

- None.

## 1.0.0 - 2026-07-22

### Highlights

- Reworked the public guide into a problem-first catalog that explains the practical role of every skill and keeps contribution, validation, and security guidance concise.
- Restored the intended contracts for social research, authenticated personal browsing, cross-provider idea critique, cross-harness context files, subscription-aware Codex delegation, and packaging recurring workflows as skills.
- Added a batch-audit workflow that discovers project-owned skills, delegates bounded fresh-context reviews, preserves raw evidence, and consolidates every retained finding through orchestrator QA.
- Expanded loop engineering with topology guidance for choosing, composing, and validating reliable multi-agent workflows.
- Hardened temporary-file and opt-in telemetry handling, context-file authority boundaries, OKF dependency checks and semantic metadata repair, single-target validation, and Wildberries search verification.

### Install / update

- Existing authenticated-browser users should add the privacy flags documented in `x9-browser-session` to their `chrome-devtools-mcp@latest` configuration, then restart Claude Code or Codex.
- Other users can update through their existing Agent Skills, Claude Code, or Codex installation route without migration steps.

### Compatibility

- Declared the public skill names, installation and update routes, and supported behavior stable enough for normal compatibility guarantees starting with 1.0.0.
- Added same-task changelog rules, release-time diff reconciliation, and a CI gate that catches release-relevant changes when `Unreleased` is empty.
- Defined deterministic release-version selection rules and replaced stale runtime facts with live `--help`, documentation, schema, and session-metadata checks.

### Breaking changes

- None.

## 0.2.0 - 2026-07-22

### Highlights

- Rebuilt the public presentation around a clear English landing page, a matching Russian version, a compact skill catalog, and a distinct visual identity.
- Added contributor, security, conduct, issue, and pull request guidance for a more predictable open-source workflow.

### Install / update

- Simplified the primary installation path to the interactive `npx skills add xonika9/agent-skills` flow while keeping native Claude Code and Codex plugin alternatives.
- Added a maintainer recording plan for a short, real product demonstration.

### Compatibility

- Clarified that the package follows the open Agent Skills format, targets Claude Code and Codex, and documents runtime-specific exceptions and companion skills.
- Added validated Codex plugin identity assets and a project brand color.
- Made the Wildberries workflow execute entirely in the current Claude Code or Codex runtime instead of delegating between them.
- Restored a portable authenticated Chromium/CDP contract while retaining the verified Microsoft Edge adapter.
- Made the global-instructions validator independent of the caller's working directory.
- Published sanitized Claude Code and Codex runtime adapters alongside the shared global-instructions core, without machine-specific installation paths.

### Breaking changes

- None.

## 0.1.0 - 2026-07-22

- Первый публичный выпуск скиллов `x9-*` для AI-агентов с поддержкой Agent Skills.
- Установка всего набора как плагина для Claude Code или Codex.
- README с проблемами, которые решают скиллы, сравнением способов установки и ссылкой на Telegram.
- Пример общего `SHARED PERSONAL CORE` для глобальных `AGENTS.md` и `CLAUDE.md`.
- Репозиторные инструкции для поддержки README, changelog, plugin manifests и release-тегов.
- Автоматический GitHub Release после успешной проверки новой версии в `main`.
- Инструкция по работе с отдельным профилем Edge через CDP и запасной маршрут `agent-edge`.
- Установка и обновление через CLI `skills`.
