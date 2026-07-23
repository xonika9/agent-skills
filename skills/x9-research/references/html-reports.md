# HTML research presentation

Read this reference after [delivery routing](delivery-modes.md) selects HTML creation or update. Delivery routing owns persistence intent, OKF discovery, target selection, pair identity, and Markdown lifecycle. This reference owns only the reader-facing HTML presentation and its verification.

## Contents

- [HTML is the reader presentation](#html-is-the-reader-presentation)
- [Russian editing pipeline](#russian-editing-pipeline)
- [Validate the pair](#validate-the-pair)
- [HTML failure behavior](#html-failure-behavior)

## HTML is the reader presentation

Start with the answer, decision, or most useful finding. Make freshness, confidence, critical limitations, and source trace easy to see. After that, choose the sections and visual forms the topic needs: narrative explanation, comparison table, timeline, cards, decision map, or another suitable structure.

Use [the editorial theme asset](../assets/editorial-theme.css) for shared visual tokens and optional components:

- light theme only;
- warm near-white background, dark readable text, restrained green accent;
- editorial display type with a quiet sans-serif reading face;
- responsive layout and comfortable line lengths;
- horizontal anchor navigation that can scroll on narrow screens;
- visible verification date;
- optional `<details>` blocks for secondary methodology, caveats, or long examples;
- print rules;
- inline CSS and no external fonts, libraries, trackers, images, or network dependencies;
- no JavaScript by default.

The asset contains no HTML skeleton and defines no required section order. Design the document structure from the research question, then inline only the relevant theme rules into the standalone HTML. Reuse the palette, font roles, moderate type scale, spacing, navigation, tables, and optional surfaces so reports share a family resemblance without receiving the same composition. Do not recreate the deleted placeholder layout or inflate headings to fill a preset grid.

Keep the main conclusion, confidence, and verdict-changing limitations expanded. Collapse only secondary material. Put source links near the claims they support; a source list at the end is supplementary, not a substitute for claim-level traceability.

## Russian editing pipeline

Apply this ordered pipeline to visible Russian prose in the HTML only:

1. Draft from the checked Markdown evidence, preserving exact facts and uncertainty.
2. Record a fact lock: names, numbers, dates, units, official titles, quotations, qualifiers, confidence, and claim-to-source links.
3. Make Russian the carrier language. Replace avoidable English exposition with natural Russian. Preserve exact English where spelling matters: official product names, identifiers, commands, code, paths, literal configuration values, URLs, quotations, and necessary domain terms. Visually separate dense exact-name clusters from narrative prose.
4. Load `humanizer-ru` and apply its full-editing workflow only to visible Russian prose. Do not edit HTML/CSS syntax, IDs, URLs, code, quotations, official names, or the Markdown file.
5. Recheck every item in the fact lock against the Markdown evidence and opened sources. Restore any changed fact, qualifier, confidence statement, or citation target.
6. Repeat the carrier-language check because stylistic editing can reintroduce English-heavy phrasing.

If `humanizer-ru` is unavailable, do not imply it ran. Perform the best manual Russian edit, label the HTML result `DEGRADED`, and name the missing dependency in the handoff.

## Validate the pair

Before reporting completion:

- confirm both same-basename files exist beside each other;
- parse the HTML and check that every internal anchor resolves;
- remove placeholder tokens and accidental chat/tool citation markers;
- confirm there are no external runtime assets or scripts;
- confirm `<html lang="ru">`, UTF-8, viewport metadata, light color scheme, responsive rules, and print rules;
- verify links preserve the researched source URLs;
- render the real HTML in a clean local browser at a wide and narrow viewport;
- inspect hierarchy, overflow, tables, navigation, and `<details>`;
- report if rendering was unavailable rather than claiming visual verification.

Structural parsing cannot prove readable design, factual fidelity, or successful humanization. Those require the real rendered artifact, the fact lock, and an honest dependency report.

## HTML failure behavior

- Humanizer unavailable: deliver `DEGRADED` with the manual language pass.
- Browser rendering unavailable: keep the valid pair but report that visual verification was not completed.
- Load-bearing research evidence unavailable: follow the core research failure state; polished HTML must not disguise `BLOCKED/NOT_PROVEN`.
