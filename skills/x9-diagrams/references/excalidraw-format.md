# Current Excalidraw format notes

This reference contains volatile implementation facts. It was verified on 2026-07-28 against Excalidraw commit [`1acf66edabc2ac5bbd4aed0714aed7dca7cc2aab`](https://github.com/excalidraw/excalidraw/tree/1acf66edabc2ac5bbd4aed0714aed7dca7cc2aab). Re-open the linked source before relying on these values after an Excalidraw update or when a scene fails to import.

## Contents

- [Font serialization](#font-serialization)
- [Native file envelope](#native-file-envelope)
- [Filesystem and clipboard route](#filesystem-and-clipboard-route)
- [Current basic element contract](#current-basic-element-contract)
- [Text normalization](#text-normalization)
- [Current arrow bindings](#current-arrow-bindings)
- [Wrapper schemas are adapters](#wrapper-schemas-are-adapters)
- [Structural verification](#structural-verification)

## Font serialization

Native text elements serialize `fontFamily` as a number. The current [`FONT_FAMILY`](https://github.com/excalidraw/excalidraw/blob/1acf66edabc2ac5bbd4aed0714aed7dca7cc2aab/packages/common/src/constants.ts#L130-L141) values include:

| Family | `fontFamily` |
| --- | ---: |
| Virgil | `1` |
| Helvetica | `2` |
| Cascadia | `3` |
| historical reserved slot | `4` |
| Excalifont | `5` |
| Nunito | `6` |

For new mixed Russian and Latin content, prefer Excalifont `5` for short display text and Nunito `6` for prose, identifiers, and connector labels; a simple scene may need only one family. Preserve another supported family when revising an existing diagram unless restyling is in scope. The checker accepts current families `1`, `2`, `3`, `5`, and `6` and rejects the reserved slot `4`.

The official [Excalifont font source](https://github.com/excalidraw/excalidraw/blob/1acf66edabc2ac5bbd4aed0714aed7dca7cc2aab/packages/excalidraw/fonts/Excalifont/index.ts) includes a Cyrillic range, and the [Nunito source](https://github.com/excalidraw/excalidraw/blob/1acf66edabc2ac5bbd4aed0714aed7dca7cc2aab/packages/excalidraw/fonts/Nunito/index.ts) registers Cyrillic and Cyrillic Extended faces. This makes both suitable for mixed Russian and Latin content, subject to checking the actual render for fallback or metric changes.

## Native file envelope

The official [`serializeAsJSON`](https://github.com/excalidraw/excalidraw/blob/1acf66edabc2ac5bbd4aed0714aed7dca7cc2aab/packages/excalidraw/data/json.ts) writes:

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "<export source>",
  "elements": [],
  "appState": {},
  "files": {}
}
```

It serializes the current element array, cleans `appState` for export, filters unreferenced binary files for local saves, and formats the result with `JSON.stringify(..., null, 2)`. A permissive importer accepting a minimal object is not proof that a hand-written scene matches current serialized element types.

## Filesystem and clipboard route

For a new named-path deliverable, write native JSON or the output of an official helper directly to the requested `.excalidraw` path. For a revision, follow [the native-source preservation rule](../SKILL.md#preserve-the-native-source). Prefer current helpers such as `convertToExcalidrawElements`; use `exportToSvg` for rendering evidence when available.

When `excalidraw.com` is the available faithful renderer, pass the scene through the system clipboard instead of file import. The current [clipboard parser](https://github.com/excalidraw/excalidraw/blob/1acf66edabc2ac5bbd4aed0714aed7dca7cc2aab/packages/excalidraw/clipboard.ts#L526-L554) recognizes this envelope; reuse the file's `elements` and `files` without manually rewriting them:

```json
{
  "type": "excalidraw/clipboard",
  "elements": [],
  "files": {}
}
```

Use a task-owned blank tab or scene; never clear or reuse a canvas that may contain unsaved work. Copy the serialized envelope with an available controller or local clipboard command, paste it once, and inspect the result before selecting or editing anything. Preserve and restore the user's system clipboard without logging its contents when the runtime supports that safely; otherwise use a local renderer or report `DEGRADED`. If normalized output is needed, copy all elements back through the clipboard, restore the native file envelope, and treat that result as a candidate.

Do not trigger Import, Download, Save as, or another browser action that opens an operating-system file or directory chooser unless the active controller can finish that chooser end to end without user action. If one opens unexpectedly, dismiss it without saving and switch routes; if neither clipboard transfer nor a compatible local renderer is available, report `DEGRADED`. A file produced through that stranded route or later found in Downloads is not autonomous completion evidence and never becomes the canonical source implicitly.

## Current basic element contract

The current [`packages/element/src/types.ts`](https://github.com/excalidraw/excalidraw/blob/1acf66edabc2ac5bbd4aed0714aed7dca7cc2aab/packages/element/src/types.ts) defines common serialized fields including:

```text
id, type, x, y, width, height, angle,
strokeColor, backgroundColor, fillStyle, strokeWidth, strokeStyle,
roundness, roughness, opacity, seed, version, versionNonce, index,
isDeleted, groupIds, frameId, boundElements, updated, link, locked
```

Text additionally carries:

```text
fontSize, fontFamily, text, originalText, textAlign, verticalAlign,
containerId, autoResize, lineHeight
```

`originalText` owns authored content and semantic hard line breaks; `text` owns the current rendered content. They normally match for unbound, auto-resizing text. For bound text or unbound text with `autoResize: false`, the target Excalidraw version wraps `originalText` to the available width, so `text` may contain additional visual line breaks. Never copy wrapped `text` back into `originalText`.

Use `containerId` for native bound labels; the container's `boundElements` must contain the reciprocal `{ "id": "<text-id>", "type": "text" }` reference. Current Excalidraw recalculates bound `text` from `originalText`; prefer its target-version converter or dimension refresh over hand-authored visual wraps.

Construct multiline strings with actual control characters before JSON serialization and let the serializer escape them. After parsing, a line break is LF (`U+000A`); a literal `\n` remains a backslash plus `n` and Excalidraw renders both characters. The checker rejects literal `\n`, `\r`, and `\t` tokens in `text` or `originalText` by default. Use `--allow-literal-escapes-in <element-id>` only when a text element intentionally displays those tokens.

For unbound text, the checker also rejects LF in `originalText` because width-driven wrapping belongs to Excalidraw. Use `--allow-hard-line-breaks-in <element-id>` only for a semantic boundary such as a heading/body split. Repeat either allowance for multiple elements.

For direct JSON, `height` must cover the rendered `text` block rather than merely fit inside the surrounding shape. As a lower bound, use `text line count × fontSize × lineHeight`, then verify the actual metrics in Excalidraw.

Current stable enumerations used by the bundled checker are:

```text
fillStyle: hachure | cross-hatch | solid | zigzag
strokeStyle: solid | dashed | dotted
textAlign: left | center | right
verticalAlign: top | middle | bottom
```

Do not copy extra fill values from a wrapper or an older guide into native JSON without verifying them against the current type.

## Text normalization

Generated or changed text geometry is provisional until the target Excalidraw version recalculates it with the actual fonts loaded. Use the target version's `restoreElements` dimension refresh, element converter, or equivalent editor API, then serialize the resulting elements. Do not treat hand-calculated `x`, `y`, `width`, or `height` as final text metrics.

Normalization is complete only when it is stable, not merely when one pass produced a plausible picture:

1. Wait for the target fonts, normalize the candidate with the target Excalidraw version, and serialize that result as the proposed final scene.
2. Apply the same normalizer once more to the proposed final scene.
3. Compare the two scenes by stable element ID. For every active element compare `x`, `y`, `width`, `height`, and `angle`; also compare text content and metrics for text elements, and points plus endpoint bindings for linear elements.
4. Any difference means the proposed final scene is not normalized and must not replace the canonical source.

The bundled checker performs step 3 when given the second-pass artifact as shown under [structural verification](#structural-verification). It requires this proof whenever active bound text exists. Use `--structural-only` only while iterating; its success is not final completion evidence.

`text != originalText` is not itself a defect for bound or fixed-width text: Excalidraw may store width-derived wrapping in `text`. It is a risk marker, so the checker reports when structural validation alone has not proved normalization. Authored semantic breaks must exist in `originalText`; width-only wraps must not be copied there.

A static SVG export uses the currently serialized `text` and cannot prove stability. Render the exact final candidate from a clean state and inspect it before selecting, clicking, editing, or resizing any element. Programmatic second-pass normalization is preferred. If it is unavailable, interact with every changed bound text element—not a representative sample—and reserialize the scene; any change in wrapping, dimensions, position, container size, or connected-arrow geometry is failure. If neither proof route is possible, report `DEGRADED`.

## Current arrow bindings

At the verified commit, native `startBinding` and `endBinding` use:

```json
{
  "elementId": "node-id",
  "fixedPoint": [1, 0.5],
  "mode": "orbit"
}
```

`fixedPoint` is a proportional point in the bound element's local coordinates. `mode` is `inside`, `orbit`, or `skip`. This replaces the legacy `{ "elementId", "focus", "gap" }` shape still shown in many public skills and old files.

Every bound endpoint also needs a reciprocal `{ "id": "<arrow-id>", "type": "arrow" }` entry in the target element's `boundElements`. Arrow `points` are local to the arrow's own `x` and `y`; the first point is normally `[0, 0]`.

Current arrowheads include:

```text
arrow, bar, circle, circle_outline, triangle, triangle_outline,
diamond, diamond_outline,
cardinality_one, cardinality_many, cardinality_one_or_many,
cardinality_exactly_one, cardinality_zero_or_one, cardinality_zero_or_many
```

An arrow also carries `elbowed`; elbow arrows have additional routing fields. Prefer the target version's element converter for non-trivial elbow routing.

After text dimensions are normalized, keep arrow labels in clear route space without overlapping either endpoint.

## Wrapper schemas are adapters

Canvas servers and MCP tools may accept convenient payloads such as:

```json
{
  "type": "rectangle",
  "text": "Service",
  "startElementId": "a",
  "endElementId": "b"
}
```

REST wrappers may instead use `label`, `start`, and `end`, and may encode enums as strings. Those are tool inputs, not evidence of the native file schema. Keep the adapter payload inside the runtime route, export a `.excalidraw` scene, and validate the exported artifact.

## Structural verification

The bundled checker deliberately covers the basic diagram subset: `rectangle`, `diamond`, `ellipse`, `text`, `line`, and `arrow`. Use the target Excalidraw version to validate scenes containing frames, images, embeds, freehand elements, or other types.

For an intermediate structural check, run:

```bash
python3 ../scripts/check_scene.py diagram.excalidraw \
  --structural-only \
  --viewport-width 1600 \
  --viewport-height 900
```

Add `--require-font-family 5` or `--require-font-family 6` only when the diagram's assigned text roles require that family; repeat the option when both roles are present.

For final evidence, replace `--structural-only` with `--normalization-result <second-pass.excalidraw>` whenever the scene contains active bound text:

```bash
python3 ../scripts/check_scene.py diagram.excalidraw \
  --normalization-result diagram.normalized-again.excalidraw
```

Use `--viewport-width` plus `--viewport-height` only for a whole-view delivery. For an explicitly scrollable canvas, use `--viewport-width` as a width diagnostic and inspect consecutive normal-zoom regions instead of failing the scene because its complete height does not fit.

Use the actual content viewport of the rendered proof, not the nominal browser-window dimensions. Then open or faithfully render the scene. Without `--normalization-result`, the checker cannot prove target-version text stability; in either mode it cannot prove z-order appearance, connector paths, contrast, or composition.
