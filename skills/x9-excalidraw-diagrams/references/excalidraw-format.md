# Current Excalidraw format notes

This reference contains volatile implementation facts. It was verified on 2026-07-28 against Excalidraw commit [`1acf66edabc2ac5bbd4aed0714aed7dca7cc2aab`](https://github.com/excalidraw/excalidraw/tree/1acf66edabc2ac5bbd4aed0714aed7dca7cc2aab). Re-open the linked source before relying on these values after an Excalidraw update or when a scene fails to import.

## Contents

- [Font serialization](#font-serialization)
- [Native file envelope](#native-file-envelope)
- [Current basic element contract](#current-basic-element-contract)
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

This skill emits new human-facing diagram text with Excalifont `5` and Nunito `6`; it treats Virgil `1` as legacy input to replace. Excalifont is also the current application default.

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

Prefer current official helpers such as `convertToExcalidrawElements` and `exportToSvg` when available. If the scene is hand-authored, round-trip it through the target Excalidraw version and inspect the exported file.

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

For generated text, keep `text` and `originalText` equal. Use `containerId` for native bound labels; the container's `boundElements` must contain the reciprocal `{ "id": "<text-id>", "type": "text" }` reference.

For direct JSON, `height` must cover the rendered text block rather than merely fit inside the surrounding shape. As a lower bound for explicit line breaks, use `line count × fontSize × lineHeight`, then verify the actual metrics in Excalidraw.

Current stable enumerations used by the bundled checker are:

```text
fillStyle: hachure | cross-hatch | solid | zigzag
strokeStyle: solid | dashed | dotted
textAlign: left | center | right
verticalAlign: top | middle | bottom
```

Do not copy extra fill values from a wrapper or an older guide into native JSON without verifying them against the current type.

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

Run the bundled checker for the basic diagram subset:

```bash
python3 ../scripts/check_scene.py diagram.excalidraw \
  --viewport-width 1600 \
  --require-font-family 5 \
  --require-font-family 6
```

Then open or faithfully render the scene. The checker cannot prove text metrics, z-order appearance, connector paths, contrast, or composition.
