#!/usr/bin/env python3
"""Validate the deterministic contract of an x9 architecture HTML report."""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path


TAILWIND_URL = "https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4.3.3"
MERMAID_URL = "https://cdn.jsdelivr.net/npm/mermaid@11.17.1/dist/mermaid.esm.min.mjs"
REQUIRED_SECTIONS = (
    "decision-question",
    "statuses",
    "conclusion",
    "comparison",
    "evidence",
    "diagrams",
    "risks",
    "next-step",
)
STATUS_ALLOWED_VALUES = {
    "method status": {"PASS", "DEGRADED", "BLOCKED"},
    "structure status": {"PASS", "FAIL"},
    "render status": {"PASS", "DEGRADED", "NOT_PROVEN"},
}
STATUS_LABELS = tuple(STATUS_ALLOWED_VALUES)
MERMAID_START = re.compile(
    r"^\s*(?:flowchart|graph|sequenceDiagram|classDiagram|stateDiagram(?:-v2)?|"
    r"erDiagram|C4Context|C4Container|C4Component|architecture-beta)\b",
    re.MULTILINE,
)
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
UNSAFE_ELEMENTS = {
    "applet", "audio", "base", "button", "datalist", "details", "dialog", "embed", "form",
    "frame", "frameset", "iframe", "img", "input", "object", "option", "optgroup", "select",
    "summary", "textarea", "video",
}
NETWORK_CAPABLE_ATTRIBUTES = {
    "action", "archive", "attributionsrc", "background", "cite", "classid", "codebase", "data",
    "dynsrc", "formaction", "href", "icon", "imagesrcset", "longdesc", "lowsrc", "manifest", "ping",
    "poster", "profile", "src", "srcset", "usemap", "xlink:href",
}
FALLBACK_CLASSES = {"mermaid-source", "diagram-text-equivalent"}
MERMAID_MODULE_TEMPLATE = (
    f'import mermaid from "{MERMAID_URL}"; '
    "mermaid.initialize({ startOnLoad: true });"
)


def class_set(attrs: dict[str, str]) -> set[str]:
    return set(attrs.get("class", "").split())


def allowed_anchor_href(value: str) -> bool:
    return bool(re.fullmatch(r"#[^\s]*|https://[^\s]+", value))


def normalized_mermaid_text(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")).strip()


def normalized_module_script(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


class ReportParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.counts: Counter[str] = Counter()
        self.stack: list[str] = []
        self.errors: list[str] = []
        self.ids: list[str] = []
        self.id_nodes: list[tuple[str, str]] = []
        self.section_stack: list[str] = []
        self.headings: list[tuple[int, str]] = []
        self.heading_level: int | None = None
        self.heading_parts: list[str] = []
        self.in_style = 0
        self.styles: list[str] = []
        self.scripts: list[dict[str, str]] = []
        self.script_stack: list[dict[str, str]] = []
        self.network_attrs: list[tuple[str, str, str]] = []
        self.status_text: list[str] = []
        self.status_depth = 0
        self.has_status_dl = False
        self.status_pairs: list[tuple[str, str]] = []
        self.pending_status_label = ""
        self.status_term_parts: list[str] | None = None
        self.status_value_parts: list[str] | None = None
        self.tables: list[dict[str, object]] = []
        self.table_stack: list[dict[str, object]] = []
        self.figures: list[dict[str, object]] = []
        self.figure_stack: list[dict[str, object]] = []
        self.diagram_container_tags: list[str] = []
        self.mermaid_source_stack: list[tuple[str, dict[str, object]]] = []
        self.mermaid_renderable_stack: list[tuple[str, dict[str, object]]] = []
        self.repo_depth = 0
        self.repo_bad_tags: list[str] = []
        self.repo_evidence_count = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        values = {name.lower(): value or "" for name, value in attrs}
        self.counts[tag] += 1
        if self.repo_depth and tag not in {"pre", "code"}:
            self.repo_bad_tags.append(tag)
        if tag not in VOID:
            self.stack.append(tag)
        if tag == "style":
            self.in_style += 1
        if tag in UNSAFE_ELEMENTS:
            self.errors.append(f"active or embedded element <{tag}> is not allowed")
        if tag == "meta" and values.get("http-equiv", "").strip().lower() == "refresh":
            self.errors.append("meta http-equiv=refresh is not allowed")
        for name, value in values.items():
            if name.startswith("on"):
                self.errors.append(f"event handler {name}= is not allowed")
            if value.strip().lower().startswith(("javascript:", "data:")):
                self.errors.append(f"unsafe URL in {name}=")
            if name in NETWORK_CAPABLE_ATTRIBUTES:
                self.network_attrs.append((tag, name, value))
            if name == "style":
                self.styles.append(value)
        classes = class_set(values)
        if classes & FALLBACK_CLASSES and ("hidden" in classes or "hidden" in values):
            self.errors.append("fallback content must not use the hidden class or attribute")
        if classes & FALLBACK_CLASSES and re.search(r"(?:display\s*:\s*none|visibility\s*:\s*hidden)", values.get("style", ""), re.IGNORECASE):
            self.errors.append("fallback content must not be hidden inline")
        if tag == "code":
            for _, renderable in self.mermaid_renderable_stack:
                renderable["nested_code"] = True

        if "id" in values:
            self.ids.append(values["id"])
            self.id_nodes.append((values["id"], tag))
        if tag == "section":
            self.section_stack.append(values.get("id", ""))
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.heading_level = int(tag[1])
            self.heading_parts = []
        if tag == "section" and values.get("id") == "statuses":
            self.status_depth = 1
        elif self.status_depth and tag not in VOID:
            self.status_depth += 1
        if tag == "dl" and self.status_depth:
            self.has_status_dl = True
        if self.status_depth and tag == "dt":
            self.status_term_parts = []
        if self.status_depth and tag == "dd":
            self.status_value_parts = []

        if tag == "script":
            values["_body"] = ""
            self.scripts.append(values)
            self.script_stack.append(values)
        if tag == "table":
            table = {
                "caption": False,
                "col_headers": 0,
                "row_headers": 0,
                "in_comparison": "comparison" in self.section_stack,
            }
            self.tables.append(table)
            self.table_stack.append(table)
        elif self.table_stack and tag == "caption":
            self.table_stack[-1]["caption"] = True
        elif self.table_stack and tag == "th":
            scope = values.get("scope", "").lower()
            if scope == "col":
                self.table_stack[-1]["col_headers"] = int(self.table_stack[-1]["col_headers"]) + 1
            if scope == "row":
                self.table_stack[-1]["row_headers"] = int(self.table_stack[-1]["row_headers"]) + 1

        if tag == "figure" and "diagram" in class_set(values):
            figure = {
                "caption": False,
                "container": False,
                "source": [],
                "renderable": [],
                "fallback": [],
                "in_diagrams": "diagrams" in self.section_stack,
            }
            self.figures.append(figure)
            self.figure_stack.append(figure)
        if self.figure_stack:
            figure = self.figure_stack[-1]
            if tag == "figcaption":
                figure["caption"] = True
            if "diagram-container" in classes:
                figure["container"] = True
            if "mermaid-source" in classes:
                source = {"parts": [], "outside_container": not self.diagram_container_tags}
                figure["source"].append(source)
                self.mermaid_source_stack.append((tag, source))
            if "mermaid" in classes:
                renderable = {
                    "parts": [],
                    "inside_container": bool(self.diagram_container_tags),
                    "nested_code": False,
                }
                figure["renderable"].append(renderable)
                self.mermaid_renderable_stack.append((tag, renderable))
            if "diagram-text-equivalent" in classes:
                figure["fallback"].append([])
            if "diagram-container" in classes:
                self.diagram_container_tags.append(tag)

        if tag == "pre" and values.get("data-repository-evidence", "").lower() == "true":
            self.repo_depth += 1
            self.repo_evidence_count += 1

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag.lower() not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in VOID:
            self.errors.append(f"void element </{tag}> must not be closed")
        elif not self.stack:
            self.errors.append(f"unexpected closing tag </{tag}>")
        elif self.stack[-1] != tag:
            self.errors.append(f"closing tag </{tag}> does not match <{self.stack[-1]}>")
        else:
            self.stack.pop()
        if tag == "style" and self.in_style:
            self.in_style -= 1
        if tag == "script" and self.script_stack:
            self.script_stack.pop()
        if tag == "dt" and self.status_term_parts is not None:
            self.pending_status_label = "".join(self.status_term_parts).strip()
            self.status_term_parts = None
        if tag == "dd" and self.status_value_parts is not None:
            self.status_pairs.append((self.pending_status_label, "".join(self.status_value_parts).strip()))
            self.status_value_parts = None
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"} and self.heading_level:
            self.headings.append((self.heading_level, "".join(self.heading_parts).strip()))
            self.heading_level = None
            self.heading_parts = []
        if self.status_depth:
            self.status_depth -= 1
        if tag == "table" and self.table_stack:
            self.table_stack.pop()
        if self.mermaid_source_stack and self.mermaid_source_stack[-1][0] == tag:
            self.mermaid_source_stack.pop()
        if self.mermaid_renderable_stack and self.mermaid_renderable_stack[-1][0] == tag:
            self.mermaid_renderable_stack.pop()
        if self.diagram_container_tags and self.diagram_container_tags[-1] == tag:
            self.diagram_container_tags.pop()
        if tag == "figure" and self.figure_stack:
            self.figure_stack.pop()
        if tag == "pre" and self.repo_depth:
            self.repo_depth -= 1
        if tag == "section" and self.section_stack:
            self.section_stack.pop()

    def handle_data(self, data: str) -> None:
        if self.in_style:
            self.styles.append(data)
        if self.script_stack:
            self.script_stack[-1]["_body"] += data
        if self.heading_level:
            self.heading_parts.append(data)
        if self.status_depth:
            self.status_text.append(data)
        if self.status_term_parts is not None:
            self.status_term_parts.append(data)
        if self.status_value_parts is not None:
            self.status_value_parts.append(data)
        for _, source in self.mermaid_source_stack:
            source["parts"].append(data)
        for _, renderable in self.mermaid_renderable_stack:
            renderable["parts"].append(data)
        if self.figure_stack:
            figure = self.figure_stack[-1]
            if figure["fallback"]:
                figure["fallback"][-1].append(data)


def css_contract_errors(css: str) -> list[str]:
    errors: list[str] = []
    if "\\" in css:
        errors.append("CSS must not contain backslash escapes")
    compact = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
    if re.search(r"@import\b|url\s*\(", compact, re.IGNORECASE):
        errors.append("CSS must not load resources or use url()")
    for selector, declarations in re.findall(r"([^{}]+)\{([^{}]*)\}", compact, re.DOTALL):
        if any(re.search(rf"\b{re.escape(class_name)}\b", selector) for class_name in FALLBACK_CLASSES) and re.search(
            r"(?:display\s*:\s*none|visibility\s*:\s*hidden)", declarations, re.IGNORECASE
        ):
            errors.append("fallback content must not be hidden by CSS")
    media = re.search(r"@media\s*\([^)]*max-width\s*:[^)]*\)\s*\{(?P<body>.*)", compact, re.IGNORECASE | re.DOTALL)
    if not media or not re.search(r"grid-template-columns\s*:\s*1fr\b", media.group("body")):
        errors.append("missing narrow one-column responsive rule")
    if not re.search(r"\.comparison-table[^}]*\{[^}]*display\s*:\s*(?:block|grid)", compact, re.IGNORECASE | re.DOTALL):
        errors.append("missing comparison reflow rule")
    if not re.search(r"\.diagram-container[^}]*\{[^}]*overflow-x\s*:\s*auto", compact, re.IGNORECASE | re.DOTALL):
        errors.append(".diagram-container must provide horizontal diagram scrolling")
    if re.search(r"(?:body|html|main)[^{]*\{[^}]*overflow(?:-x)?\s*:\s*(?:auto|scroll)", compact, re.IGNORECASE | re.DOTALL):
        errors.append("page-level scrolling must not be used for diagrams")
    return errors


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    if path.suffix.lower() != ".html":
        return ["report path must end in .html"]
    try:
        source = path.read_text(encoding="utf-8")
    except (FileNotFoundError, IsADirectoryError):
        return [f"report does not exist: {path}"]
    except UnicodeDecodeError:
        return ["report is not valid UTF-8"]

    parser = ReportParser()
    try:
        parser.feed(source)
        parser.close()
    except Exception as exc:
        return [f"HTML parsing failed: {exc}"]
    errors.extend(parser.errors)
    if parser.stack:
        errors.append("unclosed HTML elements: " + ", ".join(parser.stack))
    for tag in ("html", "head", "body"):
        if parser.counts[tag] != 1:
            errors.append(f"expected exactly one <{tag}>, found {parser.counts[tag]}")
    if parser.counts["main"] != 1:
        errors.append(f"expected exactly one <main>, found {parser.counts['main']}")
    if parser.counts["h1"] != 1:
        errors.append(f"expected exactly one <h1>, found {parser.counts['h1']}")
    for previous, current in zip(parser.headings, parser.headings[1:]):
        if current[0] > previous[0] + 1:
            errors.append(f"heading level jumps from h{previous[0]} to h{current[0]}")
    duplicate_ids = sorted({item for item, count in Counter(parser.ids).items() if count > 1})
    if duplicate_ids:
        errors.append("duplicate IDs: " + ", ".join(duplicate_ids))
    indices = []
    for section in REQUIRED_SECTIONS:
        matching_nodes = [tag for identifier, tag in parser.id_nodes if identifier == section]
        if not matching_nodes:
            errors.append(f"missing required section #{section}")
        elif "section" not in matching_nodes:
            errors.append(f"required ID #{section} must be on a <section>")
        else:
            indices.append(next(index for index, node in enumerate(parser.id_nodes) if node == (section, "section")))
    if len(indices) == len(REQUIRED_SECTIONS) and indices != sorted(indices):
        errors.append("required sections are not in contract order")

    status = " ".join(parser.status_text).casefold()
    if not parser.has_status_dl:
        errors.append("#statuses must contain a definition list")
    for label in STATUS_LABELS:
        if label not in status:
            errors.append(f"missing textual status label: {label}")
    observed_statuses = {label.casefold(): value.strip().upper() for label, value in parser.status_pairs}
    for label, allowed in STATUS_ALLOWED_VALUES.items():
        if observed_statuses.get(label) not in allowed:
            errors.append(f"{label} must have one of: {', '.join(sorted(allowed))}")
    if observed_statuses.get("structure status") != "PASS":
        errors.append("structure status must be PASS when the report validates")
    comparison_tables = [table for table in parser.tables if table["in_comparison"]]
    if not comparison_tables:
        errors.append("#comparison must contain a native table")
    elif not any(table["caption"] and table["col_headers"] and table["row_headers"] for table in comparison_tables):
        errors.append("comparison table needs caption, column headers, and row headers")

    if parser.repo_bad_tags:
        errors.append("repository evidence contains unescaped HTML: " + ", ".join(sorted(set(parser.repo_bad_tags))))
    for figure in parser.figures:
        if not figure["in_diagrams"]:
            errors.append("each figure.diagram must be inside #diagrams")
        if not figure["caption"] or not figure["container"]:
            errors.append("each .diagram figure needs figcaption and .diagram-container")
        fallback_text = " ".join("".join(parts).strip() for parts in figure["fallback"])
        if len(figure["source"]) != 1:
            errors.append("each diagram needs exactly one Mermaid source")
        if len(figure["renderable"]) != 1:
            errors.append("each diagram needs exactly one Mermaid-renderable element")
        source = figure["source"][0] if len(figure["source"]) == 1 else None
        renderable = figure["renderable"][0] if len(figure["renderable"]) == 1 else None
        source_text = normalized_mermaid_text("".join(source["parts"])) if source else ""
        render_target = normalized_mermaid_text("".join(renderable["parts"])) if renderable else ""
        if not source or not source["outside_container"] or not source_text or not MERMAID_START.search(source_text):
            errors.append("each diagram needs one separately visible supported Mermaid source outside .diagram-container")
        if not renderable or not renderable["inside_container"] or renderable["nested_code"] or not render_target or not MERMAID_START.search(render_target):
            errors.append("each diagram needs one non-empty valid Mermaid-renderable element inside .diagram-container")
        if source_text and render_target and source_text != render_target:
            errors.append("each Mermaid source must match its render target")
        if any(renderable["nested_code"] for renderable in figure["renderable"]):
            errors.append("Mermaid-renderable elements must not contain nested <code>")
        if any(not renderable["inside_container"] for renderable in figure["renderable"]):
            errors.append("Mermaid-renderable elements must be inside .diagram-container")
        if not fallback_text:
            errors.append("each diagram needs a textual equivalent")
    diagram_figures = [figure for figure in parser.figures if figure["in_diagrams"]]
    if parser.counts["section"] and "diagrams" in parser.ids and not diagram_figures:
        errors.append("#diagrams must contain at least one .diagram figure")

    if len(parser.scripts) != 2:
        errors.append("report must contain exactly Tailwind and Mermaid scripts")
    tailwind_scripts = [script for script in parser.scripts if script.get("src") == TAILWIND_URL]
    mermaid_scripts = [script for script in parser.scripts if script.get("type", "").lower() == "module"]
    if len(tailwind_scripts) != 1 or tailwind_scripts[0].get("type", "") not in {"", "text/javascript", "application/javascript"}:
        errors.append("Tailwind must use its exact pinned URL in one classic script")
    if len(mermaid_scripts) != 1:
        errors.append("Mermaid must use one module script")
    else:
        mermaid_script = mermaid_scripts[0]
        body = mermaid_script.get("_body", "")
        if mermaid_script.get("src"):
            errors.append("Mermaid module must import the pinned ESM URL and initialize it")
        if normalized_module_script(body) != MERMAID_MODULE_TEMPLATE:
            errors.append("Mermaid module must match the exact approved initialization template")
    for script in parser.scripts:
        body = script.get("_body", "")
        urls = re.findall(r"(?:(?:https?|ftp):)?//[^'\"\s)]+", body)
        imports = re.findall(r"\bimport\s*(?:[^'\";]*?\s+from\s+)?['\"]([^'\"]+)['\"]", body)
        if any(url != MERMAID_URL for url in urls) or any(url != MERMAID_URL for url in imports):
            errors.append("scripts must not reference unapproved external URLs")
    if parser.counts["link"]:
        errors.append("link elements are not allowed")
    for tag, name, value in parser.network_attrs:
        if tag == "script" and name == "src" and value == TAILWIND_URL:
            continue
        if tag == "a" and name == "href" and allowed_anchor_href(value):
            continue
        errors.append(f"unapproved URI: {tag} {name}={value}")
    script_urls = [
        *[script.get("src", "") for script in parser.scripts],
        *[
            url
            for script in parser.scripts
            for url in re.findall(r"https?://[^'\"\s)]+", script.get("_body", ""))
        ],
    ]
    if any(re.search(r"(?:@|/)latest(?:[/?#]|$)", url, re.IGNORECASE) for url in script_urls):
        errors.append("latest aliases are not allowed")
    errors.extend(css_contract_errors("\n".join(parser.styles)))
    return errors


def main(argv: list[str] | None = None) -> int:
    argument_parser = argparse.ArgumentParser(description=__doc__)
    argument_parser.add_argument("report", type=Path)
    args = argument_parser.parse_args(argv)
    errors = validate(args.report)
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: report structure and safety contract validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
