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

    def test_rejects_svg_resource_dependencies_and_refresh(self) -> None:
        for fragment in (
            '<svg><image href="https://example.invalid/pixel.png"></image></svg>',
            '<svg><use xlink:href="other.svg#icon"></use></svg>',
            '<svg><feImage href="//example.invalid/pixel.png"></feImage></svg>',
            '<meta http-equiv=" Refresh " content="0;url=https://example.invalid/">',
            '<svg><image href="#local"><set attributeName="href" to="https://example.invalid/pixel.png"></set></image></svg>',
            '<svg><image href="#local"><animate attributeName="href" values="#local;https://example.invalid/pixel.png"></animate></image></svg>',
        ):
            with self.subTest(fragment=fragment):
                self.html.write_text(valid_html().replace('</head>', fragment + '</head>'))
                self.assertTrue(any('external/runtime' in error for error in self.errors()))

    def test_allows_local_svg_references_and_source_links(self) -> None:
        self.html.write_text(valid_html().replace(
            '</main>', '<svg><defs><path id="icon"></path></defs>'
            '<use href="#icon" xlink:href="#icon" fill="url(#icon)" '
            'style="filter:url(#icon)"></use></svg></main>',
        ))
        self.assertEqual(self.errors(), [])

    def test_rejects_html_resource_attributes(self) -> None:
        for original, replacement in (
            ('</main>', '<input type="image" src="https://example.invalid/pixel.png"></main>'),
            ('</main>', '<input type="IMAGE" src="pixel.png"></main>'),
            ('<body>', '<body background="https://example.invalid/pixel.png">'),
            ('</main>', '<table background="pixel.png"><tr><td>Finding</td></tr></table></main>'),
            ('<html lang="en">', '<html lang="en" manifest="report.appcache">'),
            ('</main>', '<a href="https://example.com/source" ping="https://example.invalid/track">Source</a></main>'),
        ):
            with self.subTest(replacement=replacement):
                self.html.write_text(valid_html().replace(original, replacement), encoding="utf-8")
                self.assertTrue(any('external/runtime' in error for error in self.errors()))

    def test_rejects_svg_presentation_resource_dependencies(self) -> None:
        for attribute in ('fill', 'filter', 'cursor'):
            with self.subTest(attribute=attribute):
                self.html.write_text(valid_html().replace(
                    '</main>', f'<svg><path {attribute}="url(https://example.invalid/resource.svg#item)"></path></svg></main>',
                ), encoding="utf-8")
                self.assertTrue(any('external/runtime' in error for error in self.errors()))

    def test_duplicate_attributes_cannot_hide_resource_or_refresh(self) -> None:
        for fragment in (
            '<svg><image href="https://example.invalid/pixel.png" href="#local"></image></svg>',
            '<meta http-equiv="refresh" http-equiv="ignored" content="0;url=https://example.invalid/">',
        ):
            with self.subTest(fragment=fragment):
                self.html.write_text(valid_html().replace('</head>', fragment + '</head>'))
                self.assertTrue(any('duplicate attributes' in error for error in self.errors()))

    def test_rejects_missing_markdown_source(self) -> None:
        self.html.write_text(
            valid_html().replace(SOURCE.replace("&", "&amp;"), "https://example.com"),
            encoding="utf-8",
        )
        self.assertTrue(
            any("missing Markdown source URLs" in error for error in self.errors())
        )

    def test_requires_bare_source_urls(self) -> None:
        source = "https://example.com/article_(research)?item=1&view=full"
        for text in (
            f"Primary source: {source}\n",
            f"Primary source: ({source}).\n",
            f"- Primary source: {source};\n",
            f"- Primary source:\n\n    {source}\n",
            f"> Primary source:\n    {source}\n",
            f"**{source}**\n",
            f"**({source})**\n",
            f"(**{source}**)\n",
            f"*{source}*\n",
            f"_{source}_\n",
            f"__{source}__\n",
            f"~~{source}~~\n",
        ):
            with self.subTest(text=text):
                self.markdown.write_text(text, encoding="utf-8")
                self.html.write_text(valid_html(), encoding="utf-8")
                self.assertIn(f"HTML is missing Markdown source URLs: {source}", self.errors())
                self.html.write_text(valid_html().replace(SOURCE.replace("&", "&amp;"), source.replace("&", "&amp;")), encoding="utf-8")
                self.assertEqual(self.errors(), [])

    def test_isolated_backticks_cannot_hide_sources_in_later_blocks(self) -> None:
        literal = "A literal backtick: `."
        for source in (SOURCE, f"[Source]({SOURCE})"):
            for opening, before, after in (
                (literal, "\n\n", "\n\n"),
                (literal, "\n# Sources\n", "\n# Other\n"),
                (literal, "\n- Source: ", "\n- Other: "),
                (literal, "\n1. Source: ", "\n1. Other: "),
                (literal, "\n\n2. Source: ", "\n\n2. Other: "),
                (literal, "\n> Source: ", "\n> Other: "),
                (literal, "\n>> Source: ", "\n> Other: "),
                (literal, "\n---\n", "\n---\n"),
                (literal, "\n-\n", "\n=\n"),
                ("1. " + literal, "\n2. ", "\n3. "),
                ("1. Outer:\n   1. " + literal, "\n   2. ", "\n   3. "),
            ):
                with self.subTest(source=source, opening=opening, before=before, after=after):
                    text = f"{opening}{before}{source}{after}Another literal backtick: `.\n"
                    self.markdown.write_text(text, encoding="utf-8")
                    self.html.write_text(valid_html().replace(SOURCE.replace("&", "&amp;"), "https://example.com"), encoding="utf-8")
                    self.assertIn(f"HTML is missing Markdown source URLs: {SOURCE}", self.errors())
                    self.html.write_text(valid_html(), encoding="utf-8")
                    self.assertEqual(self.errors(), [])

    def test_link_labels_are_not_additional_sources(self) -> None:
        for text in (
            f"[https://example.invalid/label]({SOURCE})\n",
            f"[Claim][https://example.invalid/label]\n\n[https://example.invalid/label]: {SOURCE}\n",
        ):
            with self.subTest(text=text):
                self.markdown.write_text(text, encoding="utf-8")
                self.assertEqual(self.errors(), [])

    def test_code_urls_are_not_source_links(self) -> None:
        for snippet in (
            "`https://example.invalid/example`",
            "``code ` https://example.invalid/example ``",
            "`code spanning\nhttps://example.invalid/example`",
            "Example `one\n2. https://example.invalid/example`",
            "1. Example `one\n   2. https://example.invalid/example`",
            "Example `one\n1. \nhttps://example.invalid/example`",
            "Example `one\n+ \nhttps://example.invalid/example`",
            "```python\nurl = 'https://example.invalid/example'\n```",
            "~~~text\n[Example](https://example.invalid/example)\n~~~",
            "    https://example.invalid/example\n",
            "> # Example\n    https://example.invalid/example\n",
            "# Example `https://example.invalid/example`\n",
            "- Example `https://example.invalid/example`\n",
            "> Example `https://example.invalid/example`\n",
            "- Example `wrapped\n  https://example.invalid/example`\n",
            "> Example `wrapped\n> https://example.invalid/example`\n",
            "> ```text\n> https://example.invalid/example\n> ```\n",
            ">     https://example.invalid/example\n",
            "- Example:\n\n      https://example.invalid/example\n",
            "```text\n<https://example.invalid/example>\n[example]: https://example.invalid/reference\n```",
        ):
            with self.subTest(snippet=snippet):
                self.markdown.write_text(f"[Source]({SOURCE})\n\n{snippet}\n", encoding="utf-8")
                self.assertEqual(self.errors(), [])

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


    def test_rejects_nonlocal_css_dependencies(self):
        cases = [
            valid_html().replace("</style>", "body { background: url(//example.invalid/x.png); }</style>"),
            valid_html().replace("</style>", "body { background: url(x.png); }</style>"),
            valid_html().replace("<body>", '<body style="background:url(https://example.invalid/x.png)">'),
            valid_html().replace("</style>", r"body { background: u\72l(//example.invalid/x.png); }</style>"),
            valid_html().replace("</style>", 'body { background-image: image-set("https://example.invalid/x.png" 1x); }</style>'),
            valid_html().replace("</style>", "body { background-image: -webkit-image-set('x.png' 1x); }</style>"),
            valid_html().replace("</style>", r'body { background-image: -webkit-ima\67 e-set("//example.invalid/x.png" 1x); }</style>'),
            valid_html().replace("<body>", '<body style="background-image:IMAGE-SET(&quot;x.png&quot; 1x)">'),
        ]
        for candidate in cases:
            with self.subTest(candidate=candidate):
                self.html.write_text(candidate, encoding="utf-8")
                self.assertTrue(any("network dependency" in error for error in self.errors()))


    def test_requires_reference_definition_urls(self):
        for definition in (
            "[primary]: https://example.com/primary",
            "[primary]: <https://example.com/primary>",
            "[primary]:\n  https://example.com/primary",
        ):
            with self.subTest(definition=definition):
                self.markdown.write_text("[Claim][primary]\n\n" + definition + "\n", encoding="utf-8")
                self.assertTrue(any("https://example.com/primary" in error for error in self.errors()))
                self.html.write_text(valid_html().replace(SOURCE.replace("&", "&amp;"), "https://example.com/primary"), encoding="utf-8")
                self.assertEqual(self.errors(), [])
                self.html.write_text(valid_html(), encoding="utf-8")


    def test_rejects_script_without_script_element(self):
        cases = [
            valid_html().replace("<body>", '<body onload="document.body.dataset.audit=1">'),
            valid_html().replace("</main>", '<a href="javascript:void(0)">Extra</a></main>'),
            valid_html().replace("</main>", '<a href="java&#10;script:void(0)">Extra</a></main>'),
        ]
        for candidate in cases:
            with self.subTest(candidate=candidate):
                self.html.write_text(candidate, encoding="utf-8")
                self.assertTrue(any("event handler" in e or "JavaScript URL" in e for e in self.errors()))


if __name__ == "__main__":
    unittest.main()
