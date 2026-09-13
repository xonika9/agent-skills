#!/usr/bin/env python3
"""Regression checks for x9-architecture-scout's report validator."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


VALIDATOR = Path(__file__).with_name("validate_report.py")
TAILWIND_URL = "https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4.3.3"
MERMAID_URL = "https://cdn.jsdelivr.net/npm/mermaid@11.17.1/dist/mermaid.esm.min.mjs"
COMPARISON_TABLE = """<table class="comparison-table"><caption>Candidate comparison</caption><thead><tr><th scope="col">Criterion</th><th scope="col">Extract</th></tr></thead><tbody><tr><th scope="row">Coupling</th><td>Lower</td></tr></tbody></table>"""


def diagram_figure(
    diagram: str,
    *,
    include_renderable: bool = True,
    renderable_in_container: bool = True,
    empty_renderable_inside: bool = False,
    extra_invalid_renderable: bool = False,
    renderable_with_code: bool = False,
    source_outside_container: bool = True,
    source_diagram: str | None = None,
    extra_source: bool = False,
) -> str:
    renderable_contents = f"<code>{diagram}</code>" if renderable_with_code else diagram
    renderable = f'<pre class="mermaid">{renderable_contents}</pre>' if include_renderable else ""
    source = f'<pre class="mermaid-source"><code>{source_diagram if source_diagram is not None else diagram}</code></pre>'
    container_contents = ""
    outside_contents = ""
    if empty_renderable_inside:
        container_contents += '<pre class="mermaid"></pre>'
    if extra_invalid_renderable:
        container_contents += '<pre class="mermaid">not a Mermaid declaration</pre>'
    if renderable_in_container:
        container_contents += renderable
    else:
        outside_contents += renderable
    if source_outside_container:
        outside_contents += source
        if extra_source:
            outside_contents += source
    else:
        container_contents += source
    return f"""<figure class="diagram"><figcaption>Dependency direction</figcaption><div class="diagram-container">{container_contents}</div>{outside_contents}<p class="diagram-text-equivalent">Client depends on Service; no reverse dependency exists.</p></figure>"""


def report(*, tailwind: str = TAILWIND_URL, mermaid: str = MERMAID_URL, module_body: str | None = None, extra: str = "", extra_body: str = "", evidence: str = "const html = &lt;main&gt;safe&lt;/main&gt;;", diagram: str = "flowchart LR\n  A[Client] --> B[Service]", comparison: str = COMPARISON_TABLE, diagram_contents: str | None = None, structure_status: str = "PASS") -> str:
    diagram_contents = diagram_figure(diagram) if diagram_contents is None else diagram_contents
    module_body = module_body or f'import mermaid from "{mermaid}"; mermaid.initialize({{ startOnLoad: true }});'
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
.report-grid {{ display:grid; grid-template-columns: 2fr 1fr; }}
.diagram-container {{ overflow-x: auto; }}
@media (max-width: 600px) {{ .report-grid {{ grid-template-columns: 1fr; }} .comparison-table {{ display:block; }} }}
</style><script src="{tailwind}"></script><script type="module">{module_body}</script>{extra}</head>
<body><main class="report-grid"><h1>Architecture audit</h1>
<section id="decision-question"><h2>Decision question</h2><p>Which boundary should change?</p></section>
<section id="statuses"><h2>Status</h2><dl><dt>Method status</dt><dd>DEGRADED</dd><dt>Structure status</dt><dd>{structure_status}</dd><dt>Render status</dt><dd>NOT_PROVEN</dd></dl></section>
<section id="conclusion"><h2>Conclusion</h2><p>Extract the adapter. Confidence: medium.</p></section>
<section id="comparison"><h2>Comparison</h2>{comparison}</section>
<section id="evidence"><h2>Evidence</h2><pre data-repository-evidence="true"><code>{evidence}</code></pre></section>
<section id="diagrams"><h2>Diagram</h2>{diagram_contents}</section>{extra_body}
<section id="risks"><h2>Risks</h2><p>More modules may increase coordination.</p></section>
<section id="next-step"><h2>Next step</h2><p>Plan the selected candidate.</p></section>
</main></body></html>"""


def run(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(VALIDATOR), str(path)], text=True, capture_output=True)


def expect(label: str, result: subprocess.CompletedProcess[str], passing: bool) -> None:
    if (result.returncode == 0) != passing:
        raise AssertionError(f"{label}:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}")


def main() -> int:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        cases = {
            "valid report": (report(), True),
            "missing required structure": (report().replace(' id="risks"', ' id="limitations"'), False),
            "unpinned latest URL": (report(tailwind="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@latest"), False),
            "extra external resource": (report(extra='<script src="https://example.test/extra.js"></script>'), False),
            "unsafe raw repository HTML": (report(evidence="const html = <script>alert(1)</script>;"), False),
            "missing text fallback": (report().replace('<p class="diagram-text-equivalent">Client depends on Service; no reverse dependency exists.</p>', ''), False),
            "missing Mermaid source": (report(diagram="plain text without a declaration"), False),
            "missing Mermaid-renderable element": (report(diagram_contents=diagram_figure("flowchart LR\n  A[Client] --> B[Service]", include_renderable=False)), False),
            "Mermaid-renderable element outside container": (report(diagram_contents=diagram_figure("flowchart LR\n  A[Client] --> B[Service]", renderable_in_container=False)), False),
            "empty Mermaid target inside and valid target outside": (report(diagram_contents=diagram_figure("flowchart LR\n  A[Client] --> B[Service]", renderable_in_container=False, empty_renderable_inside=True)), False),
            "second invalid Mermaid target": (report(diagram_contents=diagram_figure("flowchart LR\n  A[Client] --> B[Service]", extra_invalid_renderable=True)), False),
            "nested code in Mermaid render target": (report(diagram_contents=diagram_figure("flowchart LR\n  A[Client] --> B[Service]", renderable_with_code=True)), False),
            "Mermaid source inside container": (report(diagram_contents=diagram_figure("flowchart LR\n  A[Client] --> B[Service]", source_outside_container=False)), False),
            "Mermaid source differs from render target": (report(diagram_contents=diagram_figure("flowchart LR\n  A[Client] --> B[Service]", source_diagram="flowchart LR\n  A[Client] --> C[Other]")), False),
            "second Mermaid source": (report(diagram_contents=diagram_figure("flowchart LR\n  A[Client] --> B[Service]", extra_source=True)), False),
            "required ID on wrong tag": (report().replace('<section id="risks">', '<div id="risks">').replace('</section>\n<section id="next-step">', '</div>\n<section id="next-step">'), False),
            "comparison table outside comparison": (report(comparison="<p>No native table here.</p>", extra_body=COMPARISON_TABLE), False),
            "diagram outside diagrams": (report(diagram_contents="", extra_body=diagram_figure("flowchart LR\n  A[Client] --> B[Service]")), False),
            "protocol relative link": (report(extra_body='<a href="//example.test/evidence">Source</a>'), False),
            "http link": (report(extra_body='<a href="http://example.test/evidence">Source</a>'), False),
            "ftp link": (report(extra_body='<a href="ftp://example.test/evidence">Source</a>'), False),
            "anchor ping": (report(extra_body='<a href="https://example.test/evidence" ping="https://tracker.test/ping">Source</a>'), False),
            "protocol relative script import": (report(mermaid=MERMAID_URL + '"; import x from "//example.test/extra.mjs'), False),
            "relative fetch in Mermaid module": (report(module_body=f'import mermaid from "{MERMAID_URL}"; mermaid.initialize({{ startOnLoad: true }}); fetch("./extra.json");'), False),
            "additional Mermaid module statement": (report(module_body=f'import mermaid from "{MERMAID_URL}"; mermaid.initialize({{ startOnLoad: true }}); const extra = true;'), False),
            "meta refresh": (report(extra='<meta http-equiv="refresh" content="0">'), False),
            "active button": (report(extra_body='<button>Submit</button>'), False),
            "image element": (report(extra_body='<img alt="Unexpected">'), False),
            "whitespace in https link": (report(extra_body='<a href="https://example.test/evidence bad">Source</a>'), False),
            "relative CSS url": (report(extra='<style>.extra { background: url("diagram.svg"); }</style>'), False),
            "escaped CSS url": (report(extra='<style>.extra { background: u\\72l("diagram.svg"); }</style>'), False),
            "Mermaid source hidden by CSS": (report(extra='<style>.mermaid-source { display: none; }</style>'), False),
            "hidden diagram text equivalent": (report(extra='<style>.diagram-text-equivalent { visibility: hidden; }</style>'), False),
            "one-column rule only outside narrow media": (
                report(extra='<style>.report-grid { grid-template-columns: 1fr; }</style>').replace(
                    '.report-grid { grid-template-columns: 1fr; } .comparison-table',
                    '.report-grid { gap: 1rem; } .comparison-table',
                ),
                False,
            ),
            "one-column rule on unrelated selector inside narrow media": (
                report().replace(
                    '.report-grid { grid-template-columns: 1fr; } .comparison-table',
                    '.unrelated { grid-template-columns: 1fr; } .comparison-table',
                ),
                False,
            ),
            "one-column rule on report-grid descendant": (
                report().replace(
                    '.report-grid { grid-template-columns: 1fr; } .comparison-table',
                    '.report-grid .child { grid-template-columns: 1fr; } .comparison-table',
                ),
                False,
            ),
            "two-column rule beginning with one fraction": (
                report().replace(
                    'grid-template-columns: 1fr; } .comparison-table',
                    'grid-template-columns: 1fr 1fr; } .comparison-table',
                ),
                False,
            ),
            "simple compound report-grid selector with important": (
                report().replace(
                    '.report-grid { grid-template-columns: 1fr; } .comparison-table',
                    'main.report-grid { grid-template-columns: 1fr !important; } .comparison-table',
                ),
                True,
            ),
            "last declaration overrides narrow layout": (
                report().replace('grid-template-columns: 1fr;', 'grid-template-columns: 1fr; grid-template-columns: 1fr 1fr;'), False,
            ),
            "later stylesheet overrides narrow layout": (
                report(extra='<style>.report-grid { grid-template-columns: 1fr 1fr; }</style>'), False,
            ),
            "earlier more specific desktop rule wins": (
                report().replace('.report-grid { display:grid;', 'main.report-grid { display:grid;'), False,
            ),
            "earlier important desktop rule wins": (
                report().replace('grid-template-columns: 2fr 1fr;', 'grid-template-columns: 2fr 1fr !important;'), False,
            ),
            "important narrow declaration resists later normal declaration": (
                report().replace('grid-template-columns: 1fr;', 'grid-template-columns: 1fr !important; grid-template-columns: 2fr 1fr;'), True,
            ),
            "more specific narrow rule resists later general rule": (
                report(extra='<style>.report-grid { grid-template-columns: 2fr 1fr; }</style>').replace(
                    '.report-grid { grid-template-columns: 1fr;', 'main.report-grid { grid-template-columns: 1fr;'), True,
            ),
            "earlier declaration restored to one column": (
                report().replace('grid-template-columns: 1fr;', 'grid-template-columns: 2fr 1fr; grid-template-columns: 1fr;'), True,
            ),
            "layout shorthand resets columns": (
                report(extra='<style>.report-grid { grid: auto / 1fr 1fr; }</style>'), False,
            ),
            "inline layout overrides stylesheet": (
                report().replace('<main class="report-grid">', '<main class="report-grid" style="grid-template-columns: 1fr 1fr">'), False,
            ),
            "ordinary inline style preserves stylesheet parsing": (
                report(extra_body='<p style="color: red">Note</p>'), True,
            ),
            "inline resource remains forbidden": (
                report(extra_body='<p style="background: url(https://example.test/image)">Note</p>'), False,
            ),
            "layout hidden in unsupported at-rule": (
                report(extra='<style>@supports (display: grid) { .report-grid { grid-template-columns: 1fr 1fr; } }</style>'), False,
            ),
            "selector must match actual grid element": (
                report().replace('.report-grid { grid-template-columns: 1fr;', 'article.report-grid { grid-template-columns: 1fr;'), False,
            ),
            "selector requires absent class": (
                report().replace('.report-grid { grid-template-columns: 1fr;', '.report-grid.missing { grid-template-columns: 1fr;'), False,
            ),
            "class names remain case sensitive": (
                report().replace('.report-grid { grid-template-columns: 1fr;', '.REPORT-GRID { grid-template-columns: 1fr;'), False,
            ),
            "layout in string is not a declaration": (
                report().replace('grid-template-columns: 1fr;', 'content: "; grid-template-columns: 1fr;";'), False,
            ),
            "selector list uses matching specificity only": (
                report().replace('.report-grid { grid-template-columns: 1fr;', '#absent.report-grid, .report-grid { grid-template-columns: 1fr;').replace(
                    '.report-grid { display:grid;', 'main.report-grid { display:grid;'), False,
            ),
            "missing report-grid node": (report().replace('<main class="report-grid">', '<main>'), False),
            "unclosed stylesheet block": (report(extra='<style>.other { color: red;</style>'), False),
            "stylesheet only applies to print": (report().replace('<style>', '<style media="print">'), False),
            "stylesheet has a non-CSS type": (report().replace('<style>', '<style type="text/plain">'), False),
            "stylesheet explicitly applies to screen": (report().replace('<style>', '<style media="screen" type="text/css">'), True),
            "duplicate source conceals unapproved script": (
                report().replace(f'<script src="{TAILWIND_URL}">', f'<script src="https://example.test/unapproved.js" SRC="{TAILWIND_URL}">'), False,
            ),
            "duplicate style conceals inline columns": (
                report().replace('<main class="report-grid">', '<main class="report-grid" style="grid-template-columns: 2fr 1fr" STYLE="color:red">'), False,
            ),
            "duplicate class conceals absent report-grid": (
                report().replace('<main class="report-grid">', '<main class="other" CLASS="report-grid">'), False,
            ),
            "Mermaid source hidden by class": (report().replace('class="mermaid-source"', 'class="mermaid-source hidden"'), False),
            "Mermaid source hidden by attribute": (report().replace('class="mermaid-source"', 'class="mermaid-source" hidden'), False),
            "self-closing void metadata": (report().replace('<meta charset="utf-8">', '<meta charset="utf-8" />'), True),
            "mismatched structure status": (report(structure_status="FAIL"), False),
        }
        for condition, passing in [
            ('screen and (max-width: 760px)', True),
            ('(max-width: 390px)', True),
            ('(max-width: 760.5px)', True),
            ('print and (max-width: 760px)', False),
            ('not all and (max-width: 760px)', False),
            ('(max-width: 0px)', False),
            ('(max-width: -1px)', False),
            ('(max-width: 1px)', False),
            ('(max-width: 1280px)', False),
            ('(max-width: 40rem)', False),
            ('(min-width: 700px) and (max-width: 600px)', False),
            ('(max-width: 600px), print', False),
        ]:
            cases['media ' + condition] = (report().replace('(max-width: 600px)', condition), passing)
        for index, (label, (contents, passing)) in enumerate(cases.items()):
            path = root / f"case-{index}.html"
            path.write_text(contents, encoding="utf-8")
            expect(label, run(path), passing)
    print("PASS: validator regression fixtures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
