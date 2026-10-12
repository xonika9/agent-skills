# Delivery presets

These are starting points for new diagrams, not mandatory sizes or promises of renderer support. Explicit dimensions win. Keep an existing diagram's orientation and composition unless redesign is authorized, per [the design method](design-method.md#start-with-one-question-and-one-path).

| Destination | Starting SVG viewBox | Body / relationship labels | Outer margin |
| --- | --- | --- | --- |
| Document or article | `0 0 960 600` | 14 / 12 units | 32 units |
| 16:9 slide | `0 0 1280 720` | 20 / 16 units | 48 units |
| A4 landscape, inside 10 mm page margins | `0 0 1120 792` | 16 / 14 units | 40 units |

SVG units become CSS pixels only at 1:1 display scale. A larger canvas or higher raster export resolution does not by itself make labels more readable. For other formats, transfer the intended reading size and spacing rather than copying SVG units into a renderer with different metrics.

Choose the delivery mode using [the shared method](design-method.md#compose-for-the-delivery-viewport). For a whole view, lay out against the actual destination width; if scaling makes required text illegible, increase the text scale and simplify or split. For an explicitly scrollable canvas, keep normal-size text and validate the consecutive viewport regions. Do not introduce scrolling into a slide or printed page.

Use the slide's actual content rectangle after its header/footer areas. Inspect the complete slide at its intended presentation size; a documentation-sized font ramp on a larger canvas is not a slide preset.

For print, declare the physical placement size as well as the viewBox. The A4 starting frame above fits inside a 277 × 190 mm content rectangle while preserving aspect ratio; its 14-unit labels render at about 9.5 pt at the limiting height. Confirm the actual print or PDF scale and clipping rather than inferring them from a screen preview. [The SVG wrapper](svg.md#html-wrapper) owns print CSS. A print check is needed only when print is part of the deliverable.

Detail level and audience are independent: destination controls frame and reading scale, audience controls explanatory vocabulary, and simplification controls what survives. A size preset does not authorize dropping content. Conversions remain governed by [the preservation and loss-ledger contract](../SKILL.md#convert-and-review).
