---
name: x9-diagrams
description: Use when the user explicitly invokes x9-diagrams, needs a choice between diagram formats, converts or reviews diagrams across formats, or needs one visual method with native creation and verification in Excalidraw, Mermaid, or draw.io/diagrams.net. Also use for requests such as “choose the right diagram format”, “convert this Mermaid diagram to editable draw.io”, «выбери формат схемы», «проверь и улучши диаграмму». A Mermaid-only syntax request may remain with an installed specialized Mermaid skill. Do not use for data charts, UI mockups, raster illustration, or unsupported diagram formats.
compatibility: Native checks require Python 3 for Excalidraw, a target-compatible Mermaid renderer, or a compatible diagrams.net tool for draw.io.
---

# Diagrams

Design, create, review, and convert diagrams while keeping the visual argument and the native source independently correct.

The [machine-readable onboarding contract](references/onboarding.json) lists external prerequisites.

## Resolve two decisions

First choose the view that expresses the relationship: flowchart, sequence, state, architecture, data model, hierarchy, timeline, comparison, or another supported view. Then choose the delivery format. Do not let a familiar file format decide the diagram type.

An explicit format wins when it can express the required structure. If it creates a material limitation, explain the limitation and offer an alternative without silently changing the deliverable.

Use this matrix when the format is open:

| Constraint | Excalidraw | Mermaid | draw.io |
| --- | --- | --- | --- |
| Manual coordinate control | Strong | Weak; layout is automatic | Strong |
| Collaborative visual editing | Strong in Excalidraw | Depends on the host | Strong in diagrams.net |
| Text diff and code review | Poor | Strong | Moderate with uncompressed XML |
| Automatic layout | Manual-first | Strong | Available, but manual geometry remains explicit |
| Free spatial composition | Strong | Limited | Strong |
| Pages, layers, containers, shape libraries | Limited | Limited and renderer-dependent | Strong |
| Direct Markdown/chat rendering | Rare | Strong when supported | Rare |
| Native editability after handoff | `.excalidraw` | Mermaid source in a compatible editor | `.drawio` XML |
| Reliable validation and rendering | Needs checker plus faithful renderer | Needs target parser plus renderer | Needs XML checks plus compatible editor/exporter |

Prefer the format whose native editor, validator, and renderer are available in the delivery environment. If none can provide visual proof, produce the requested native source only when still useful and label the result `DEGRADED`.

## Own the visual argument

Settle one question, audience, delivery viewport, entry point, and dominant reading direction. Preserve exact facts and identifiers while shortening explanatory labels. Model semantic nodes, boundaries, and relationships before syntax or coordinates.

Read [the shared design method](references/design-method.md) before creating or materially revising a diagram. It owns topology, hierarchy, density, grouping, boundaries, routing, semantic shape/color/line use, split criteria, and visual acceptance.

## Use one format adapter

- For native `.excalidraw` JSON, read [the Excalidraw adapter](references/excalidraw-format.md). Run its bundled checker and inspect a faithful render.
- For Mermaid source or an in-chat Mermaid block, read [the Mermaid adapter](references/mermaid.md). Parse and render with the actual target or a compatible existing tool.
- For native `.drawio` XML, read [the draw.io adapter](references/drawio.md). Validate the XML structure, open or export it with a compatible diagrams.net tool, and inspect the result.

Format adapters own serialization, escaping, identifiers, bindings, geometry, themes, pages, layers, and renderer-specific limitations. Do not copy their volatile mechanics into this core.

## Preserve the native source

For a new named-path deliverable, the requested path becomes canonical when first written. For a revision, the existing source remains canonical while changes live in a candidate. Editors and renderers consume those artifacts; an export elsewhere never replaces the canonical source implicitly.

A revision candidate replaces the existing source only when it meets the [completion gate](#completion-gate). Otherwise report `DEGRADED`, leave the existing source unchanged, and identify the candidate as unfinished.

## Convert and review

Across conversions preserve semantic identity: node meaning, relationship direction, sequence, containment, boundaries, cardinality, and exact technical tokens. Preserve pages, layers, and container identity when both source and target support them. State losses such as automatic-layout changes, unsupported shape libraries, or flattened styling; never promise pixel parity.

For review-only work, inspect and report without rewriting. Check the native structure separately from the rendered composition: a parse success does not prove legibility, and a plausible picture does not prove editability.

## Trigger boundary

This skill owns explicit `x9-diagrams` calls, format selection, cross-format conversion, the shared visual method, and combined structural plus visual verification. A request limited to ordinary Mermaid syntax can stay with an installed specialized `mermaid-diagrams` skill. This skill remains self-contained for users who do not have that third-party skill.

When trigger ownership is ambiguous, use `x9-diagrams` only if the task needs its broader decision or verification contract. Do not invoke both skills merely because Mermaid appears in the request.

## Completion gate

Match completion evidence to the requested action:

- **Format selection:** name the view and delivery format, connect the choice to the user's constraints, state material limitations, and identify whether a compatible validator, renderer, or editor is available.
- **Creation or material revision:** the chosen view answers the stated question; the native source parses or opens and remains editable; the agent did not trigger a native file or directory chooser it could not complete itself; format-specific post-load layout is stable where applicable; a compatible renderer or editor produced the actual view from the final canonical source after its last material mutation; and that view was inspected in its declared delivery mode for legibility, hierarchy, crossings, clipping, and misleading structure.
- **Conversion:** meet the creation evidence and confirm that important semantics survived; state any loss in layout, styling, pages, layers, containers, or notation.
- **Review only:** distinguish native-structure findings from rendered-composition findings and cite the inspected evidence without rewriting the artifact.

If any evidence required for the active action cannot be obtained, report `DEGRADED` with the exact missing check, validator, renderer, editor, or source artifact. Excalidraw checker regression tests live in `scripts/test_check_scene.py`.
