#!/usr/bin/env python3
"""Validate deterministic parts of an x9-research Markdown/HTML pair."""

from __future__ import annotations

import argparse
import re
import sys
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote


LANGUAGE_TAG = re.compile(r"^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*$")
MARKDOWN_AUTOLINK = re.compile(r"<(https?://[^>\s]+)>")
PLACEHOLDER = re.compile(
    r"(?im)^\s*(?:TODO|TBD|FIXME|PLACEHOLDER)(?:\s*:.*)?\s*$"
    r"|\{\{[^}\n]*(?:TODO|TBD|FIXME|PLACEHOLDER)[^}\n]*\}\}"
    r"|\[\[[^\]\n]*(?:TODO|TBD|FIXME|PLACEHOLDER)[^\]\n]*\]\]"
)
CHAT_CITATION = re.compile(
    r"(?:turn\d+(?:search|fetch|view|open)\d+|cite[^]+|【\d+†[^】]+】)"
)
NETWORK_CSS = re.compile(r"(?:@import\s+|url\(\s*[\"']?https?://)", re.IGNORECASE)
FORBIDDEN_RUNTIME_TAGS = {
    "script",
    "img",
    "iframe",
    "embed",
    "object",
    "video",
    "audio",
    "source",
}
RUNTIME_LINK_RELATIONS = {
    "stylesheet",
    "preload",
    "modulepreload",
    "prefetch",
    "preconnect",
    "dns-prefetch",
    "icon",
    "manifest",
}
VOID_TAGS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "source",
    "track",
    "wbr",
}


class ReportParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: set[str] = set()
        self.tag_counts: dict[str, int] = {}
        self.open_tags: list[str] = []
        self.structure_errors: list[str] = []
        self.ids: set[str] = set()
        self.duplicate_ids: set[str] = set()
        self.hrefs: set[str] = set()
        self.internal_hrefs: list[str] = []
        self.html_language: str | None = None
        self.has_utf8 = False
        self.has_viewport = False
        self.runtime_dependencies: list[str] = []
        self.style_depth = 0
        self.style_chunks: list[str] = []
        self.text_chunks: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        self._handle_tag(tag, attrs)
        tag = tag.lower()
        if tag not in VOID_TAGS:
            self.open_tags.append(tag)
        if tag == "style":
            self.style_depth += 1

    def handle_startendtag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        self._handle_tag(tag, attrs)
        if tag.lower() not in VOID_TAGS:
            self.structure_errors.append(
                f"non-void element <{tag.lower()}/> must use an explicit closing tag"
            )

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in VOID_TAGS:
            self.structure_errors.append(f"void element </{tag}> must not be closed")
        elif not self.open_tags:
            self.structure_errors.append(f"unexpected closing tag </{tag}>")
        elif self.open_tags[-1] != tag:
            self.structure_errors.append(
                f"closing tag </{tag}> does not match <{self.open_tags[-1]}>"
            )
        else:
            self.open_tags.pop()
        if tag == "style" and self.style_depth:
            self.style_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.style_depth:
            self.style_chunks.append(data)
        else:
            self.text_chunks.append(data)

    def _handle_tag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        tag = tag.lower()
        values = {name.lower(): value or "" for name, value in attrs}
        self.tags.add(tag)
        self.tag_counts[tag] = self.tag_counts.get(tag, 0) + 1

        element_id = values.get("id")
        if element_id:
            if element_id in self.ids:
                self.duplicate_ids.add(element_id)
            self.ids.add(element_id)

        if tag == "html":
            self.html_language = values.get("lang") or None

        if tag == "meta":
            if values.get("charset", "").lower() == "utf-8":
                self.has_utf8 = True
            if (
                values.get("http-equiv", "").lower() == "content-type"
                and "charset=utf-8" in values.get("content", "").lower()
            ):
                self.has_utf8 = True
            if (
                values.get("name", "").lower() == "viewport"
                and "width=device-width" in values.get("content", "").lower()
            ):
                self.has_viewport = True

        href = values.get("href")
        if tag == "a" and href:
            self.hrefs.add(href)
            if href.startswith("#"):
                self.internal_hrefs.append(href)

        if tag in FORBIDDEN_RUNTIME_TAGS:
            self.runtime_dependencies.append(f"<{tag}>")
        if tag == "link" and (
            set(values.get("rel", "").lower().split()) & RUNTIME_LINK_RELATIONS
        ):
            self.runtime_dependencies.append("<link>")


def markdown_urls(markdown: str) -> set[str]:
    urls = {unescape(url) for url in MARKDOWN_AUTOLINK.findall(markdown)}
    cursor = 0
    while True:
        marker = markdown.find("](", cursor)
        if marker < 0:
            break
        position = marker + 2
        while position < len(markdown) and markdown[position].isspace():
            position += 1

        if position < len(markdown) and markdown[position] == "<":
            end = markdown.find(">", position + 1)
            if end >= 0:
                candidate = markdown[position + 1 : end]
                if candidate.startswith(("http://", "https://")):
                    urls.add(unescape(candidate))
            cursor = max(position + 1, end + 1)
            continue

        start = position
        depth = 0
        while position < len(markdown):
            char = markdown[position]
            if char == "\\" and position + 1 < len(markdown):
                position += 2
                continue
            if char == "(":
                depth += 1
            elif char == ")":
                if depth == 0:
                    break
                depth -= 1
            elif char.isspace() and depth == 0:
                break
            position += 1
        candidate = markdown[start:position].replace(r"\(", "(").replace(r"\)", ")")
        if candidate.startswith(("http://", "https://")):
            urls.add(unescape(candidate))
        cursor = max(position + 1, marker + 2)
    return urls


def validate_pair(
    markdown_path: Path,
    html_path: Path,
    *,
    language: str,
) -> list[str]:
    errors: list[str] = []

    if not LANGUAGE_TAG.fullmatch(language):
        errors.append(f"invalid BCP 47 language tag: {language!r}")
    if markdown_path.suffix.lower() != ".md":
        errors.append("Markdown path must end in .md")
    if html_path.suffix.lower() != ".html":
        errors.append("HTML path must end in .html")
    if markdown_path.stem != html_path.stem:
        errors.append("Markdown and HTML files must have the same basename")
    if markdown_path.parent.resolve() != html_path.parent.resolve():
        errors.append("Markdown and HTML files must be beside each other")
    if not markdown_path.is_file():
        errors.append(f"Markdown file does not exist: {markdown_path}")
    if not html_path.is_file():
        errors.append(f"HTML file does not exist: {html_path}")
    if errors:
        return errors

    try:
        markdown = markdown_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        errors.append("Markdown file is not valid UTF-8")
        return errors
    try:
        html = html_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        errors.append("HTML file is not valid UTF-8")
        return errors

    parser = ReportParser()
    try:
        parser.feed(html)
        parser.close()
    except Exception as exc:  # HTMLParser can surface malformed entities.
        errors.append(f"HTML parsing failed: {exc}")
        return errors

    for required_tag in ("html", "head", "body"):
        count = parser.tag_counts.get(required_tag, 0)
        if count != 1:
            errors.append(f"expected exactly one <{required_tag}>, found {count}")
    errors.extend(parser.structure_errors)
    if parser.open_tags:
        errors.append("unclosed HTML elements: " + ", ".join(parser.open_tags))

    if (parser.html_language or "").lower() != language.lower():
        errors.append(
            f"html lang must be {language!r}, got {parser.html_language!r}"
        )
    if not parser.has_utf8:
        errors.append("missing UTF-8 meta declaration")
    if not parser.has_viewport:
        errors.append("missing viewport metadata with width=device-width")
    if parser.duplicate_ids:
        errors.append(f"duplicate ids: {', '.join(sorted(parser.duplicate_ids))}")

    unresolved = sorted(
        {
            unquote(href[1:])
            for href in parser.internal_hrefs
            if unquote(href[1:]) not in parser.ids
        }
    )
    if unresolved:
        errors.append(f"unresolved internal anchors: {', '.join(unresolved)}")

    if parser.runtime_dependencies:
        errors.append(
            "external/runtime asset tags are not allowed: "
            + ", ".join(sorted(set(parser.runtime_dependencies)))
        )

    css = "\n".join(parser.style_chunks)
    if not css.strip():
        errors.append("missing inline <style> rules")
    if not re.search(r"color-scheme\s*:\s*light\b", css, re.IGNORECASE):
        errors.append("inline CSS must declare color-scheme: light")
    if not re.search(r"@media[^{]*max-width", css, re.IGNORECASE):
        errors.append("inline CSS must include a responsive max-width media query")
    if not re.search(r"@media\s+print\b", css, re.IGNORECASE):
        errors.append("inline CSS must include print rules")
    if NETWORK_CSS.search(css):
        errors.append("inline CSS contains an external network dependency")

    if PLACEHOLDER.search("\n".join(parser.text_chunks)):
        errors.append("HTML contains a placeholder token")
    if CHAT_CITATION.search(html):
        errors.append("HTML contains an accidental chat/tool citation marker")

    missing_urls = sorted(markdown_urls(markdown) - parser.hrefs)
    if missing_urls:
        errors.append(
            "HTML is missing Markdown source URLs: " + ", ".join(missing_urls)
        )

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate an x9-research Markdown/HTML pair."
    )
    parser.add_argument("--language", required=True, help="Actual BCP 47 language tag")
    parser.add_argument("markdown", type=Path)
    parser.add_argument("html", type=Path)
    args = parser.parse_args(argv)

    errors = validate_pair(args.markdown, args.html, language=args.language)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("PASS — research HTML pair is structurally valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
