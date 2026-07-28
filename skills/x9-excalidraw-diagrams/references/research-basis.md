# Research basis

The method was synthesized from ten independently authored public Agent Skills, current Excalidraw source, and three provided failure examples. Sources were opened at the commits below on 2026-07-28. The synthesis is paraphrased; no source's substantial wording or templates were copied. Sources without a repository license were treated as evidence to study, not text to reuse.

## Public skill corpus

| ID | Skill and source | Repository / author | Verified commit | License observed | Useful contribution |
| --- | --- | --- | --- | --- | --- |
| S1 | [`excalidraw-diagram-generator`](https://github.com/github/awesome-copilot/blob/9933dcad5be5caeb288cebcd370eeeb2fc2f1685/skills/excalidraw-diagram-generator/SKILL.md) | `github/awesome-copilot` | `9933dcad5be5caeb288cebcd370eeeb2fc2f1685` | MIT | Diagram-type routing, semantic extraction, practical element-count limits, wide connector gutters, split-on-complexity rule |
| S2 | [`excalidraw-diagram`](https://github.com/coleam00/excalidraw-diagram-skill/blob/8646fcc9f74f38539c6cdb4c969723336a96ddcd/SKILL.md) | `coleam00/excalidraw-diagram-skill` | `8646fcc9f74f38539c6cdb4c969723336a96ddcd` | No repository license found | Visual-argument framing, multi-zoom hierarchy, container discipline, whitespace as hierarchy, rendered composition review |
| S3 | [`excalidraw-diagram`](https://github.com/axtonliu/axton-obsidian-visual-skills/blob/1265976d9746a84858b4b7b42fb86a215aa93de9/excalidraw-diagram/SKILL.md) | `axtonliu/axton-obsidian-visual-skills` | `1265976d9746a84858b4b7b42fb86a215aa93de9` | MIT | Diagram-type selection, font-size floors, canvas margins, title centering against content, contrast and long-label warnings |
| S4 | [`excalidraw-skill`](https://github.com/lingzhi227/agent-research-skills/blob/9e6c085d65e313e475e921fdfe795ac11eb7589e/skills/excalidraw-skill/SKILL.md) | `lingzhi227/agent-research-skills` | `9e6c085d65e313e475e921fdfe795ac11eb7589e` | No repository license found | Screenshot feedback loop, overlap and truncation gates, zone padding, waypoint routing, honest degraded behavior |
| S5 | [`excalidraw`](https://github.com/davila7/claude-code-templates/blob/e3744adb7654df443f12927f3e001252b3a26b6d/cli-tool/components/skills/creative-design/excalidraw/SKILL.md) | `davila7/claude-code-templates` | `e3744adb7654df443f12927f3e001252b3a26b6d` | MIT | Compact semantic extraction from verbose scenes and isolation of high-volume JSON work |
| S6 | [`excalidraw-diagram`](https://github.com/xstongxue/best-skills/blob/fd28854edc4b1aa9c991003a8b7928474cb669c4/skills/excalidraw-diagram/SKILL.md) | `xstongxue/best-skills` | `fd28854edc4b1aa9c991003a8b7928474cb669c4` | Apache-2.0 | Layered coordinate planning, semantic grouping, dominant flow direction, aggregation when nodes become dense |
| S7 | [`diagram-maker`](https://github.com/openclaw/openclaw/blob/ca48f6c0fb5ab6f12b0eaa9ba27df29a59c74bd5/skills/diagram-maker/SKILL.md) | `openclaw/openclaw` | `ca48f6c0fb5ab6f12b0eaa9ba27df29a59c74bd5` | MIT | Output-format boundary, five-to-nine primary-element target, short labels, semantic palette, minimum text and node sizes |
| S8 | [`excalidraw`](https://github.com/djalmajr/skills/blob/7dea72539f19a9915affc41ce064a41a1b830379/skills/excalidraw/SKILL.md) | `djalmajr/skills` | `7dea72539f19a9915affc41ce064a41a1b830379` | No repository license found | Official-library conversion and faithful rendering, reciprocal binding, paint order, groups, geometry linting |
| S9 | [`excalidraw-design-guide`](https://github.com/opencoredev/excalidraw-cli/blob/7d26c3aeb175be646e97134ef45c4918737bb8a0/skills/excalidraw-design-guide/SKILL.md) | `opencoredev/excalidraw-cli` | `7d26c3aeb175be646e97134ef45c4918737bb8a0` | MIT | Consistent peer sizing, grid rhythm, limited palette, solid/dashed/dotted semantics, radial balance, anti-pattern checklist |
| S10 | [`excalidraw`](https://github.com/edwingao28/excalidraw-skill/blob/c3eb67e013102d422726bbda39fe6ad1f302bbfb/plugins/excalidraw/skills/excalidraw/SKILL.md) | `edwingao28/excalidraw-skill` | `c3eb67e013102d422726bbda39fe6ad1f302bbfb` | MIT | Whole-batch binding, explicit z-order, geometric plus visual critique, labelled-connector spacing, zones and three-column data-flow layout |

`softaworks/agent-toolkit@excalidraw` was excluded because its `SKILL.md` was byte-identical to S5 at the inspected commits. Catalog entries missing from current repository `HEAD`, renderer-only tools, and MCP-server construction guides were not counted.

## Contradictions resolved

The corpus disagrees on fonts: S1 and S3 require Excalifont for everything, S2 uses Cascadia, S7 and older format notes use Virgil, and S8 documents the former three-family model. None owns current font IDs. The official constants and font registrations therefore own the values, while the role matrix is a design decision: expressive Excalifont for display hierarchy, readable Nunito for prose and technical text.

The corpus also mixes native JSON with MCP/REST convenience payloads. S4, S9, and S10 supply useful operational patterns, but their `label`, `startElementId`, or string-enum fields remain adapter inputs. Native structure follows the current official element types and serializer.

Hard character-count formulas differ substantially between S3, S4, S9, and S10 and break across Cyrillic, Latin, identifiers, and font families. The method therefore prefers rendered measurement and retains only padding ranges as a fallback.

## Failure examples

Three provided examples were inspected without modification:

- E1, a very tall comparison scene: 199 elements across roughly 4376 × 6333 canvas units, 72 free text elements averaging about 147 characters, 54 unbound arrows, 13 rectangle fill colors, and body text that becomes too small at a normal whole-scene width.
- E2, a wide architecture scene: 101 elements, 63 free text elements, mixed legacy Virgil and Helvetica, 16 unbound arrows, many font sizes, and dense explanatory panels competing with the primary flow.
- E3, an editor screenshot: Virgil was selected for a Russian node label, and the canvas showed a large node beside a much smaller peer with inconsistent internal density.

These are not file-specific defects to patch. They expose general failure classes: no font-role system, legacy fonts, prose-heavy nodes, missing native bindings, too many simultaneous encodings, poor fit-to-view legibility, and mass/whitespace imbalance.

## Rule trace

| New rule | Evidence |
| --- | --- |
| Choose topology from the relationship and set one reading direction | S1, S3, S6, S7, S10 |
| Keep five-to-nine primary elements where possible; split competing stories | S1, S7, S10, E1, E2 |
| Use scale, whitespace, and selective containers for hierarchy | S2, S8, E1, E3 |
| Measure text, preserve padding, and separate long labels from explanation | S3, S4, S9, S10, E1, E2 |
| Route through gutters; use short labels and semantic line styles | S4, S8, S9, S10, E1, E2 |
| Keep zones quiet, padded, and behind their children | S2, S4, S6, S9, S10 |
| Limit palette and decoration; keep peer roles consistent | S1, S3, S7, S8, S9, S10, E1 |
| Bind endpoints and labels reciprocally for editability | S8, official element types, E1, E2 |
| Use Excalifont `5` and Nunito `6`; reject Virgil in new output | Official constants and font registrations, E2, E3 |
| Validate native structure separately from wrapper input | S4, S8, S9, S10, official serializer and element types |
| Render and visually inspect both whole and working views | S2, S4, S8, S10, E1, E2, E3 |

The current-format evidence is maintained in [excalidraw-format.md](excalidraw-format.md); universal guidance remains in [design-method.md](design-method.md).
