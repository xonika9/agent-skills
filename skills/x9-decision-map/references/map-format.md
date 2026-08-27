# Decision map format

A decision map is a durable Markdown document. It captures pre-plan choices and uncertainty; it is not an implementation plan, task list, or workflow topology.

## Contents

- [Document structure](#document-structure)
- [Record rules](#record-rules)
- [Portable handoff brief](#portable-handoff-brief)

## Document structure

Use a repository's established document metadata and section conventions when they exist. Otherwise use the structure below. Keep IDs stable for the lifetime of the map. New records receive the next unused identifier; never renumber surviving records.

The canonical initiative ID is a durable, lowercase stable slug such as `checkout-reliability`; it is not a display title. Rename the title by adding the old and new names to aliases, while leaving the canonical ID unchanged.

```markdown
# Decision map: <initiative title>

## Initiative

- Canonical ID: `<initiative-id>`
- Aliases and former names: `<alias>`; `<former name>`
- Purpose: <outcome the initiative must achieve>
- Scope boundary: <what this map decides>
- Out of scope: <explicit exclusions>
- Current direction: <one current, qualified statement>

## Evidence

### E-001 — <short claim or source title>

- Source: <path, URL, conversation statement, experiment, or other provenance>
- Retrieved or observed: <date/time when material>
- Claim: <what this evidence supports or challenges>
- Reliability or limitation: <why it may be incomplete, stale, or weak>
- Status: `current` | `superseded` | `withdrawn`

## Decisions

### D-001 — <decision to make>

- Status: `proposed` | `accepted` | `rejected` | `invalidated` | `needs-review`
- Authority: <person, role, or agreed decision rule>
- Source: <where the decision or authority came from>
- Options:
  - `<option A>` — <consequence or trade-off>
  - `<option B>` — <consequence or trade-off>
- Current selection: <selected option, or `none`>
- Rationale and evidence: `E-001`; <brief reasoning>
- Depends on: `E-001`; `Q-001`; `D-002`
- Affects: `D-003`; `F-001`

## Sharp open questions

### Q-001 — <answerable question>

- Status: `open` | `answered` | `invalidated` | `needs-review`
- Why it matters: <decision or boundary it can resolve>
- Answer owner or source: <who can decide or where evidence should come from>
- Depends on: <record IDs>
- Affects: <record IDs>
- Answer: <answer, or `unknown`>

## Fog

### G-001 — <material uncertainty not yet reducible to one answerable question>

- Status: `present` | `reframed` | `resolved` | `needs-review`
- Why it matters: <scope, direction, or evidence risk>
- What would sharpen it: <smallest observation, source, or decision needed>
- Depends on: <record IDs>
- Affects: <record IDs>

## Frontier

### F-001 — <nearest unblocker>

- Status: `ready` | `blocked` | `complete` | `invalidated` | `needs-review`
- Unblocks: `Q-001`; `D-001`
- Owner or source: <who can provide it, or where to look>
- Completion evidence: <observable fact that makes the unblocker complete>
- Depends on: <record IDs>

## Invalidation history

### I-001 — <date> — <changed evidence or assumption>

- Trigger: `E-001` changed from `current` to `superseded` because <reason>
- Impact: `D-001`, `Q-001`, and `F-001` marked `needs-review`
- Superseded state retained at: <record IDs or section anchor>
- Resolution: <new evidence, replacement decision, or `pending`>
```

## Record rules

- A decision records the authority that may select among options. A source identifies where that authority or the decision itself was established; evidence supports the choice but does not replace authority.
- A sharp open question has a bounded answer and an explicit decision consequence. Reframe it as fog when its answer, owner, or decision consequence cannot yet be named.
- Fog describes uncertainty without pretending that it is already an answerable question. Its next step belongs on the frontier only when there is a concrete nearest unblocker.
- A frontier entry is immediate discovery or decision-unblocking work. Do not place implementation tasks, broad plans, or speculative follow-ons there.
- Dependencies and effects use record IDs. A changed or withdrawn evidence record invalidates every reachable dependent record until reviewed; record that propagation in `Invalidation history`.
- `Out of scope` is a map-level boundary. Put excluded alternatives there rather than representing them as silently abandoned decisions.

## Portable handoff brief

When no Compound Engineering handoff is available, provide:

```markdown
Initiative: <canonical ID and map path>
Current direction: <qualified statement>
Accepted decisions: <D-IDs and selections>
Invalidated or review-needed decisions: <D-IDs and reason>
Sharp open questions: <Q-IDs>
Material fog: <G-IDs>
Next frontier: <F-IDs and their completion evidence>
```
