---
name: x9-excalidraw-diagrams
description: Use when creating, editing, reviewing, or converting a native Excalidraw scene — “make an .excalidraw diagram”, “fix this Excalidraw”, «сделай диаграмму Excalidraw», «улучши .excalidraw». Also use when an existing .excalidraw needs visual, layout, or structural quality review. Do not use for Mermaid, draw.io, SVG-only diagrams, or manual Excalidraw UI operation unless the deliverable is a native .excalidraw scene.
compatibility: Requires Python 3 for the bundled scene checker and an Excalidraw-compatible renderer or editor for visual verification.
---

# Excalidraw diagrams

Create editable `.excalidraw` scenes that remain clear when viewed as a whole and structurally sound when a person moves or edits their elements.

## Own the visual argument

Settle the diagram's question, audience, reading direction, and delivery viewport before choosing coordinates. Select the topology that best exposes the relationship:

- sequence or state change → flowchart, timeline, or sequence layout;
- ownership or system boundaries → layered architecture or zones;
- transfer or transformation → data-flow or pipeline;
- hierarchy → tree;
- comparison → matched side-by-side views;
- one concept with independent branches → hub-and-spoke or mind map.

Use one dominant reading direction. If the content needs unrelated stories, conflicting directions, or detail that disappears at fit-to-view, split it into an overview and focused views instead of enlarging one canvas indefinitely.

Read [the design method](references/design-method.md) before designing or materially revising a scene. It owns hierarchy, spacing, typography, containers, arrows, palette, long labels, density, split criteria, and visual pass/fail signals.

## Separate meaning from file mechanics

Model the scene as semantic nodes, groups, and directed relationships before emitting elements. Preserve exact technical identifiers and user-supplied facts, but shorten prose labels and move explanations into secondary text or focused views.

Read [the current format notes](references/excalidraw-format.md) before writing native JSON or judging its structural correctness. They own volatile font IDs, enumerations, binding shapes, serialization, and the distinction between native files and wrapper APIs. Re-check the official Excalidraw source when the installed version rejects the documented shape or a load-bearing value may have changed.

Prefer an official Excalidraw conversion/export API or a runtime tool that exports a native scene. Wrapper fields such as `label`, `startElementId`, or server-specific string enums are not native `.excalidraw` fields; export and inspect the resulting file rather than copying the wrapper payload into it.

## Build for editing

- Use Excalifont for display hierarchy and short human-facing labels; use Nunito for explanatory prose, technical identifiers, and connector labels. Do not use Virgil.
- Give every element a stable unique ID. Bind shape labels and arrows where the current format supports it, and keep reciprocal references valid.
- Keep zones behind connectors, connectors behind foreground nodes, and text above the shapes it labels.
- Size from rendered text, not character count alone. Separate mixed-role text into grouped elements because one text element cannot carry two font families.
- Route connectors through dedicated gutters. A relationship that crosses an unrelated node or makes its label ambiguous is not finished.

For direct JSON work, run:

```bash
python3 <skill-directory>/scripts/check_scene.py <scene.excalidraw> \
  --viewport-width 1600 \
  --require-font-family 5 \
  --require-font-family 6
```

The checker validates the current basic-scene contract, font policy, IDs, enumerations, bindings, and fit-to-view text size. It does not prove visual quality or replace a faithful render.

## Render, inspect, and revise

Render the real scene with Excalidraw or a renderer backed by the official library. Inspect both:

- the whole diagram at its delivery size for entry point, reading order, balance, density, and effective text size;
- a normal working zoom for clipping, overlaps, container padding, connector routing, labels, and contrast.

Fix the scene and render again when either view fails. If no faithful render or editor is available, return `DEGRADED`, name the missing visual evidence, and do not claim the composition passed.

The result is done only when the native file parses, the checker passes, the rendered scene has been visually inspected, every important relationship is unambiguous, text remains legible at the intended whole-diagram size, and the requested output opens as an editable Excalidraw scene.

For the evidence behind these rules and for future retuning, read [the research basis](references/research-basis.md). Maintainer regression tests for the checker live in `scripts/test_check_scene.py`.
