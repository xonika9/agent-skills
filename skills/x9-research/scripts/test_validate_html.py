#!/usr/bin/env python3
"""Regression tests for validate_html.py."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from validate_html import validate_pair


SOURCE = "https://example.com/source?item=1&view=full"


def valid_html(*, language: str = "en") -> str:
    return f"""<!doctype html>
<html lang="{language}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Checked research</title>
  <style>
    :root {{ color-scheme: light; }}
    @media (max-width: 760px) {{ main {{ width: 100%; }} }}
    @media print {{ nav {{ display: none; }} }}
  </style>
</head>
<body>
  <nav><a href="#finding">Finding</a></nav>
  <main id="finding">
    <h1>Checked finding</h1>
    <p><a href="{SOURCE.replace('&', '&amp;')}">Primary source</a></p>
  </main>
</body>
</html>
"""


class ValidateHtmlTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp_dir.name)
        self.markdown = self.directory / "report.md"
        self.html = self.directory / "report.html"
        self.markdown.write_text(f"[Primary source]({SOURCE})\n", encoding="utf-8")
        self.html.write_text(valid_html(), encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def errors(self, *, language: str = "en") -> list[str]:
        return validate_pair(self.markdown, self.html, language=language)

    def test_accepts_valid_pair(self) -> None:
        self.assertEqual(self.errors(), [])

    def test_rejects_wrong_language(self) -> None:
        self.assertTrue(any("html lang" in error for error in self.errors(language="ru")))

    def test_rejects_unresolved_anchor(self) -> None:
        self.html.write_text(
            valid_html().replace('href="#finding"', 'href="#missing"'),
            encoding="utf-8",
        )
        self.assertTrue(
            any("unresolved internal anchors" in error for error in self.errors())
        )

    def test_rejects_external_runtime_asset(self) -> None:
        self.html.write_text(
            valid_html().replace("</head>", '<script src="app.js"></script></head>'),
            encoding="utf-8",
        )
        self.assertTrue(any("<script>" in error for error in self.errors()))

    def test_rejects_missing_markdown_source(self) -> None:
        self.html.write_text(
            valid_html().replace(SOURCE.replace("&", "&amp;"), "https://example.com"),
            encoding="utf-8",
        )
        self.assertTrue(
            any("missing Markdown source URLs" in error for error in self.errors())
        )

    def test_rejects_chat_citation_marker(self) -> None:
        self.html.write_text(
            valid_html().replace("Checked finding", "Checked finding turn1search2"),
            encoding="utf-8",
        )
        self.assertTrue(any("chat/tool citation" in error for error in self.errors()))

    def test_rejects_visible_placeholder(self) -> None:
        self.html.write_text(
            valid_html().replace("Checked finding", "TODO: add the final finding"),
            encoding="utf-8",
        )
        self.assertTrue(any("placeholder token" in error for error in self.errors()))

    def test_allows_todo_as_research_subject(self) -> None:
        self.html.write_text(
            valid_html().replace("Checked finding", "How TODO comments are indexed"),
            encoding="utf-8",
        )
        self.assertEqual(self.errors(), [])

    def test_rejects_non_matching_pair(self) -> None:
        other = self.directory / "other.html"
        other.write_text(valid_html(), encoding="utf-8")
        errors = validate_pair(self.markdown, other, language="en")
        self.assertTrue(any("same basename" in error for error in errors))

    def test_preserves_source_url_with_parentheses(self) -> None:
        source = "https://example.com/article_(research)"
        self.markdown.write_text(f"[Source]({source})\n", encoding="utf-8")
        self.html.write_text(
            valid_html().replace(SOURCE.replace("&", "&amp;"), source),
            encoding="utf-8",
        )
        self.assertEqual(self.errors(), [])

    def test_allows_non_runtime_link_metadata(self) -> None:
        self.html.write_text(
            valid_html().replace(
                "</head>",
                '<link rel="canonical" href="https://example.com/report"></head>',
            ),
            encoding="utf-8",
        )
        self.assertEqual(self.errors(), [])

    def test_rejects_malformed_structure(self) -> None:
        self.html.write_text(
            valid_html().replace("</main>", "</section>"),
            encoding="utf-8",
        )
        self.assertTrue(
            any("does not match" in error for error in self.errors())
        )

    def test_rejects_self_closed_non_void_element(self) -> None:
        self.html.write_text(
            valid_html().replace("<h1>Checked finding</h1>", "<h1/>"),
            encoding="utf-8",
        )
        self.assertTrue(
            any("non-void element" in error for error in self.errors())
        )


if __name__ == "__main__":
    unittest.main()
