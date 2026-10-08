# Writing the image prompt

Codex passes the prompt to the image tool verbatim, so the prompt you write is the whole specification. These rules are adapted from OpenAI's Codex `imagegen` skill (Apache-2.0).

## Shape

- For a complex request, use short labeled lines in this order: use and asset type, scene, subject, style or medium, composition and framing, lighting and mood, palette, exact text, constraints, avoid. Skip lines that add nothing.
- Name the intended use (landing hero, slide, sticker, game sprite): it sets the polish level.
- State the aspect ratio in words, such as "landscape 3:2" or "square".

## How much to add

- A specific prompt is normalized into that shape without new creative requirements.
- A generic prompt may gain framing, polish, or layout cues that clearly help.
- Never add characters, objects, brands, slogans, palettes, or story beats the user did not imply.

## Text in the image

- Quote the exact text, name its typography and placement, and require verbatim rendering with no extra characters.
- Spell an unusual word letter by letter when accuracy matters.

## Reference images and edits

- Each `--image` is attached to the Codex turn in order. Label every one by index and role in the prompt: `Image 1: edit target`, `Image 2: style reference`.
- An image given only for style, composition, or mood makes the request a generation, not an edit.
- For an edit, write `change only X; keep Y unchanged`, and repeat those invariants on every iteration.

## Transparency

Ask for a genuinely transparent background; a drawn checkerboard is not transparency.

## Iterating

Change one thing per follow-up and restate the constraints that must hold, rather than rewriting the whole prompt.
