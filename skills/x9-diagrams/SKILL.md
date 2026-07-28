---
name: x9-diagrams
description: Use when the user explicitly invokes x9-diagrams, needs a choice between diagram formats, converts or reviews diagrams across formats, or needs one visual method with native creation and verification in Excalidraw, Mermaid, or draw.io/diagrams.net. Also use for requests such as “choose the right diagram format”, “convert this Mermaid diagram to editable draw.io”, «выбери формат схемы», «проверь и улучши диаграмму». A Mermaid-only syntax request may remain with an installed specialized Mermaid skill. Do not use for data charts, UI mockups, raster illustration, or unsupported diagram formats.
compatibility: Native checks require Python 3 for Excalidraw, a target-compatible Mermaid renderer, or a compatible diagrams.net tool for draw.io.
---

# Diagrams

Design, create, review, and convert diagrams while keeping the visual argument and the native source independently correct.

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

## Convert and review

Across conversions preserve semantic identity: node meaning, relationship direction, sequence, containment, boundaries, cardinality, and exact technical tokens. Preserve pages, layers, and container identity when both source and target support them. State losses such as automatic-layout changes, unsupported shape libraries, or flattened styling; never promise pixel parity.

For review-only work, inspect and report without rewriting. Check the native structure separately from the rendered composition: a parse success does not prove legibility, and a plausible picture does not prove editability.

## Trigger boundary

This skill owns explicit `x9-diagrams` calls, format selection, cross-format conversion, the shared visual method, and combined structural plus visual verification. A request limited to ordinary Mermaid syntax can stay with an installed specialized `mermaid-diagrams` skill. This skill remains self-contained for users who do not have that third-party skill.

When trigger ownership is ambiguous, use `x9-diagrams` only if the task needs its broader decision or verification contract. Do not invoke both skills merely because Mermaid appears in the request.

## Completion gate

The result is complete only when:

1. the chosen view answers the stated question for the intended audience;
2. the requested native source parses or opens and remains editable;
3. a compatible renderer or editor produced the actual view;
4. that view was inspected at delivery size for legibility, hierarchy, crossings, clipping, and misleading structure;
5. important semantics survived any conversion.

If step 2 or 3 cannot be performed, report `DEGRADED` with the exact missing validator, renderer, or editor. Excalidraw checker regression tests live in `scripts/test_check_scene.py`.
