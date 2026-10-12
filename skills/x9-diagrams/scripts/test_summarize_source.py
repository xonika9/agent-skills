#!/usr/bin/env python3
"""Regression tests for summarize_source.py."""

from __future__ import annotations

import base64
import contextlib
import html
import io
import json
import re
import tempfile
import unittest
import urllib.parse
import zlib
from pathlib import Path
from unittest import mock

import summarize_source
from summarize_source import main, summarize


def run(path: Path, *args: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main([str(path), *args])
    return code, out.getvalue(), err.getvalue()


class TempCase(unittest.TestCase):
    def setUp(self):
        self._directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._directory.cleanup)
        self.dir = Path(self._directory.name)

    def write(self, name: str, content: str | dict) -> Path:
        path = self.dir / name
        text = content if isinstance(content, str) else json.dumps(content)
        path.write_text(text, encoding="utf-8")
        return path

    def digest_md(self, path: Path, *args: str) -> str:
        code, out, err = run(path, *args)
        self.assertEqual(code, 0, err)
        return out


# ------------------------------------------------------------------ Excalidraw


def el(element_id: str, element_type: str, x=0, y=0, w=100, h=50, **extra) -> dict:
    base = {
        "id": element_id, "type": element_type, "x": x, "y": y, "width": w,
        "height": h, "isDeleted": False, "groupIds": [], "frameId": None,
        "boundElements": None, "link": None, "strokeStyle": "solid",
    }
    base.update(extra)
    return base


def label(element_id: str, container: str, text: str, **extra) -> dict:
    return el(element_id, "text", text=text, originalText=text,
              containerId=container, **extra)


def arrow(element_id: str, start, end, **extra) -> dict:
    binding = lambda target: (
        {"elementId": target, "fixedPoint": [0.5, 0.5], "mode": "orbit"}
        if target else None
    )
    data = {
        "startBinding": binding(start), "endBinding": binding(end),
        "startArrowhead": None, "endArrowhead": "arrow", "points": [[0, 0], [10, 0]],
    }
    data.update(extra)
    return el(element_id, "arrow", **data)


def excalidraw_scene(*extra_elements: dict) -> dict:
    elements = [
        el("F", "frame", -20, -20, 600, 300, name="Backend"),
        el("A", "rectangle", 0, 0, groupIds=["g1"], link="https://example.com/x"),
        label("A-t", "A", "Client"),
        el("B", "rectangle", 200, 0, groupIds=["g1"], frameId="F"),
        label("B-t", "B", "API"),
        el("C", "ellipse", 400, 0, frameId="F"),
        label("C-t", "C", "DB"),
        arrow("ab", "A", "B"),
        arrow("bc", "B", "C", strokeStyle="dashed"),
        label("bc-t", "bc", "query"),
        arrow("loose", "A", None),
        el("note", "text", 0, 200, text="Note", originalText="Note"),
        el("gone", "rectangle", isDeleted=True),
        el("ink", "freedraw"),
        el("pic", "image"),
        el("web", "embeddable"),
        el("odd", "hologram"),
    ]
    elements.extend(extra_elements)
    return {"type": "excalidraw", "version": 2, "elements": elements,
            "appState": {}, "files": {}}


class ExcalidrawTests(TempCase):
    def scene(self, *extra: dict) -> dict:
        path = self.write("flow.excalidraw", excalidraw_scene(*extra))
        return summarize(path)["scenes"][0]

    def test_counts_and_discarded(self):
        scene = self.scene()
        counts = scene["metrics"]["counts"]
        self.assertEqual(counts["nodes"], 4)  # A, B, C, standalone note
        self.assertEqual(counts["text_nodes"], 1)
        self.assertEqual(counts["containers"], 1)
        self.assertEqual(counts["edges"], 3)
        self.assertEqual(counts["labeled_edges"], 1)
        self.assertEqual(counts["dangling_edges"], 1)
        self.assertEqual(
            scene["discarded"],
            {"deleted": 1, "freedraw": 1, "image": 1, "embeds": 1, "unknown": 1,
             "element_links": 1, "dangling_edges": 1},
        )

    def test_labels_frame_membership_and_groups(self):
        scene = self.scene()
        nodes = {n["id"]: n for n in scene["nodes"]}
        self.assertEqual(nodes["A"]["label"], "Client")
        self.assertEqual(nodes["B"]["parent"], "F")
        self.assertEqual(nodes["F"]["label"], "Backend")
        self.assertTrue(nodes["F"]["container"])
        self.assertEqual(nodes["C"]["kind"], "ellipse")
        self.assertNotIn("A-t", nodes)
        self.assertEqual(scene["clusters"], [{"id": "g1", "members": ["A", "B"]}])
        members = scene["metrics"]["container_members"][0]
        self.assertEqual([m["id"] for m in members["members"]], ["B", "C"])
        self.assertEqual(scene["metrics"]["containment_depth"], 1)

    def test_edges_style_direction_and_graph_roles(self):
        scene = self.scene()
        edges = {e["id"]: e for e in scene["edges"]}
        self.assertEqual(edges["bc"]["style"], "dashed")
        self.assertEqual(edges["bc"]["label"], "query")
        self.assertEqual(edges["ab"]["directed"], "forward")
        self.assertTrue(edges["loose"]["dangling"])
        metrics = scene["metrics"]
        self.assertEqual([h["id"] for h in metrics["hubs"]][0], "B")
        self.assertEqual(metrics["hubs"][0]["degree"], 2)
        self.assertEqual([n["id"] for n in metrics["entry_points"]], ["A"])
        self.assertEqual([n["id"] for n in metrics["terminals"]], ["C"])
        self.assertEqual(metrics["unconnected"], [])
        self.assertFalse(metrics["has_cycle"])

    def test_cycle_and_arrowhead_directions(self):
        backward = self.scene(
            arrow("ac", "C", "A", startArrowhead="arrow", endArrowhead=None),
        )
        edges = {e["id"]: e for e in backward["edges"]}
        self.assertEqual(edges["ac"]["directed"], "backward")  # means A -> C
        self.assertFalse(backward["metrics"]["has_cycle"])
        scene = self.scene(arrow("ca", "C", "A"))
        self.assertTrue(scene["metrics"]["has_cycle"])  # A->B->C->A

    def test_undirected_line_has_no_cycle_or_entry(self):
        scene = self.scene(
            arrow("plain", "C", "A", endArrowhead=None),
        )
        edges = {e["id"]: e for e in scene["edges"]}
        self.assertEqual(edges["plain"]["directed"], "none")
        self.assertFalse(scene["metrics"]["has_cycle"])

    def test_markdown_digest_sections(self):
        path = self.write("flow.excalidraw", excalidraw_scene())
        out = self.digest_md(path)
        for expected in (
            "# Diagram digest: flow.excalidraw",
            "Directed cycle: no",
            "Budget: nodes 3/9 ok, edges 3/12 ok",
            "Hubs: API (B) [2]",
            "Entry points: Client (A)",
            "Container Backend (F): API (B), DB (C)",
            "Discarded: deleted 1, freedraw 1, image 1, embeds 1, unknown 1, "
            "element links 1, dangling edges 1",
            "### Nodes",
            "### Edges",
        ):
            self.assertIn(expected, out)
        self.assertIn("| Client | ? | — | solid | forward |", out)  # dangling target

    def test_budget_flags(self):
        extra = [el(f"n{i}", "rectangle") for i in range(10)]
        scene = self.scene(*extra)
        self.assertTrue(scene["metrics"]["budget"]["nodes"]["exceeded"])
        self.assertFalse(scene["metrics"]["budget"]["edges"]["exceeded"])
        self.assertEqual(len(scene["metrics"]["unconnected"]), 10)

    def test_rejects_non_scene(self):
        path = self.write("bad.excalidraw", {"hello": 1})
        code, _, err = run(path)
        self.assertEqual(code, 2)
        self.assertIn("elements", err)
        broken = self.write("broken.excalidraw", "{nope")
        self.assertEqual(run(broken)[0], 2)

    def test_malformed_identifiers_do_not_crash(self):
        cases = {
            "container": [{"id": "t", "type": "text", "containerId": ["x"], "text": "hi"}],
            "frame": [el("r", "rectangle", frameId={"a": 1})],
            "binding": [el("a", "arrow", startBinding={"elementId": ["q"]},
                           endBinding={"elementId": {"k": 1}})],
            "huge float": [el("r", "rectangle", x=1e308, w=1e308)],
            "huge int": [el("r", "rectangle", x=10**400)],
        }
        for name, elements in cases.items():
            with self.subTest(name):
                code, out, err = run(
                    self.write("m.excalidraw", {"elements": elements})
                )
                self.assertEqual((code, err), (0, ""), name)

    def test_unparseable_numbers_exit_with_source_error(self):
        path = self.write("big.excalidraw",
                          '{"elements":[{"id":"r","type":"rectangle","x":' + "1" * 5000 + "}]}")
        code, out, err = run(path)
        self.assertEqual((code, out), (2, ""))
        self.assertTrue(err.startswith("ERROR:"), err)
        self.assertNotIn("Traceback", err)

    def test_unexpected_type_errors_become_source_errors(self):
        path = self.write("a.excalidraw", excalidraw_scene())
        with mock.patch.object(summarize_source, "parse_excalidraw",
                               side_effect=TypeError("boom")):
            code, out, err = run(path)
        self.assertEqual((code, out), (2, ""))
        self.assertIn("malformed", err)


# --------------------------------------------------------------------- draw.io


def drawio_model(extra: str = "") -> str:
    return (
        '<mxGraphModel dx="800" dy="600"><root>'
        '<mxCell id="0"/><mxCell id="1" parent="0"/>'
        '<mxCell id="grp" value="Platform &lt;b&gt;core&lt;/b&gt; &amp;amp; co" '
        'style="swimlane;startSize=20" vertex="1" parent="1">'
        '<mxGeometry x="100" y="100" width="400" height="200" as="geometry"/></mxCell>'
        '<mxCell id="web" value="Web&lt;br&gt;app" style="rounded=1;" vertex="1" '
        'parent="grp"><mxGeometry x="20" y="40" width="80" height="40" as="geometry"/></mxCell>'
        '<mxCell id="db" value="Orders DB" style="shape=cylinder3;" vertex="1" parent="grp">'
        '<mxGeometry x="200" y="40" width="60" height="60" as="geometry"/></mxCell>'
        '<mxCell id="ok" value="OK?" style="rhombus;" vertex="1" parent="1">'
        '<mxGeometry x="600" y="100" width="60" height="60" as="geometry"/></mxCell>'
        '<mxCell id="e1" value="reads" style="endArrow=classic;dashed=1;" edge="1" '
        'parent="1" source="web" target="db"><mxGeometry relative="1" as="geometry"/></mxCell>'
        '<mxCell id="e2" style="endArrow=none;startArrow=none;" edge="1" parent="1" '
        'source="db" target="ok"><mxGeometry relative="1" as="geometry"/></mxCell>'
        '<mxCell id="e2l" value="&lt;i&gt;check&lt;/i&gt;" style="edgeLabel;html=1;" '
        'vertex="1" connectable="0" parent="e2">'
        '<mxGeometry relative="1" as="geometry"/></mxCell>'
        '<mxCell id="e3" edge="1" parent="1" source="web"/>'
        + extra +
        "</root></mxGraphModel>"
    )


def compress_drawio(model: str) -> str:
    quoted = urllib.parse.quote(model, safe="").encode()
    compressor = zlib.compressobj(wbits=-15)
    raw = compressor.compress(quoted) + compressor.flush()
    return base64.b64encode(raw).decode()


PAGE_TWO = (
    '<mxGraphModel><root><mxCell id="0"/><mxCell id="1" parent="0"/>'
    '<mxCell id="x" value="Solo" vertex="1" parent="1"/></root></mxGraphModel>'
)


class DrawioTests(TempCase):
    def test_two_pages_uncompressed(self):
        xml = (
            '<mxfile><diagram name="Main" id="d1">' + drawio_model() + "</diagram>"
            '<diagram name="Second" id="d2">' + PAGE_TWO + "</diagram></mxfile>"
        )
        digest = summarize(self.write("a.drawio", xml))
        self.assertEqual([s["name"] for s in digest["scenes"]], ["Main", "Second"])
        main_scene = digest["scenes"][0]
        nodes = {n["id"]: n for n in main_scene["nodes"]}
        self.assertTrue(nodes["grp"]["container"])
        self.assertEqual(nodes["grp"]["kind"], "swimlane")
        self.assertEqual(nodes["grp"]["label"], "Platform core & co")
        self.assertEqual(nodes["web"]["label"], "Web app")
        self.assertEqual(nodes["web"]["parent"], "grp")
        self.assertEqual(nodes["db"]["kind"], "store")
        self.assertEqual(nodes["ok"]["kind"], "rhombus")
        self.assertNotIn("e2l", nodes)
        edges = {e["id"]: e for e in main_scene["edges"]}
        self.assertEqual(edges["e1"]["label"], "reads")
        self.assertEqual(edges["e1"]["style"], "dashed")
        self.assertEqual(edges["e2"]["label"], "check")
        self.assertEqual(edges["e2"]["directed"], "none")
        self.assertTrue(edges["e3"]["dangling"])
        counts = main_scene["metrics"]["counts"]
        self.assertEqual((counts["nodes"], counts["containers"], counts["edges"]), (3, 1, 3))
        self.assertEqual(main_scene["discarded"], {"dangling_edges": 1})
        self.assertEqual(main_scene["layers"], [{"id": "1", "name": "1", "nodes": 4}])
        self.assertEqual(main_scene["bounds"], {"x": 100, "y": 100, "width": 560, "height": 200})
        self.assertEqual([n["id"] for n in digest["scenes"][1]["nodes"]], ["x"])

    def test_compressed_page_matches_uncompressed(self):
        plain = '<mxfile><diagram name="Main">' + drawio_model() + "</diagram></mxfile>"
        packed = (
            '<mxfile><diagram name="Main">' + compress_drawio(drawio_model())
            + "</diagram></mxfile>"
        )
        left = summarize(self.write("plain.drawio", plain))["scenes"]
        right = summarize(self.write("packed.drawio.xml", packed))["scenes"]
        self.assertEqual(left, right)

    def test_wrapper_object_label_and_link(self):
        extra = (
            '<object label="Wrapped" id="w" link="https://example.com"><mxCell vertex="1" '
            'parent="1"><mxGeometry as="geometry"/></mxCell></object>'
        )
        xml = '<mxfile><diagram name="P">' + drawio_model(extra) + "</diagram></mxfile>"
        scene = summarize(self.write("w.drawio", xml))["scenes"][0]
        self.assertIn("Wrapped", [n["label"] for n in scene["nodes"]])
        self.assertEqual(scene["discarded"]["element_links"], 1)

    def test_markdown_reports_per_page(self):
        xml = (
            '<mxfile><diagram name="Main">' + drawio_model() + "</diagram>"
            "<diagram name=\"Second\">" + PAGE_TWO + "</diagram></mxfile>"
        )
        out = self.digest_md(self.write("a.drawio", xml))
        self.assertIn("## Page 1 of 2: Main", out)
        self.assertIn("## Page 2 of 2: Second", out)
        self.assertNotIn("Layers:", out)  # a single default layer is not reported

    def test_multiple_layers_are_reported(self):
        extra = (
            '<mxCell id="L2" value="Overlay" parent="0"/>'
            '<mxCell id="o" value="Pin" vertex="1" parent="L2"/>'
        )
        xml = '<mxfile><diagram name="P">' + drawio_model(extra) + "</diagram></mxfile>"
        out = self.digest_md(self.write("l.drawio", xml))
        self.assertIn("Layers: 1 (nodes 4), Overlay (nodes 1)", out)

    def test_notes_are_listed_but_not_budgeted(self):
        note = (
            '<mxCell id="n1" value="Legacy" style="shape=note;whiteSpace=wrap;" '
            'vertex="1" parent="1"><mxGeometry x="0" y="400" width="80" height="40" '
            'as="geometry"/></mxCell>'
            '<mxCell id="n2" value="Bare" style="note;size=10;" vertex="1" parent="1"/>'
            '<mxCell id="en" edge="1" parent="1" source="n1" target="web" '
            'style="dashed=1;endArrow=none;"/>'
        )
        xml = '<mxfile><diagram name="P">' + drawio_model(note) + "</diagram></mxfile>"
        scene = summarize(self.write("n.drawio", xml))["scenes"][0]
        metrics = scene["metrics"]
        self.assertEqual(metrics["counts"]["notes"], 2)
        self.assertEqual(metrics["budget"]["nodes"]["count"], 3)  # web, db, ok
        listed = [n["id"] for n in scene["nodes"]]
        self.assertIn("n1", listed)
        self.assertIn("n2", listed)
        everywhere = (
            [h["id"] for h in metrics["hubs"]]
            + [n["id"] for n in metrics["entry_points"]]
            + [n["id"] for n in metrics["terminals"]]
            + [n["id"] for n in metrics["unconnected"]]
        )
        self.assertNotIn("n1", everywhere)
        self.assertNotIn("n2", everywhere)
        out = self.digest_md(self.write("n.drawio", xml))
        self.assertIn("notes 2", out)

    def test_rejects_non_drawio_and_bad_payload(self):
        self.assertEqual(run(self.write("a.drawio", "<svg/>"))[0], 2)
        bad = '<mxfile><diagram name="P">AAAA!!</diagram></mxfile>'
        code, _, err = run(self.write("b.drawio", bad))
        self.assertEqual(code, 2)
        self.assertIn("compressed", err)

    def test_rejects_decompression_bomb(self):
        compressor = zlib.compressobj(wbits=-15)
        raw = compressor.compress(b"a" * 5000) + compressor.flush()
        xml = f'<mxfile><diagram name="P">{base64.b64encode(raw).decode()}</diagram></mxfile>'
        with mock.patch.object(summarize_source, "MAX_FILE_BYTES", 1000):
            # the 5000-byte payload expands past the patched limit
            code, _, err = run(self.write("bomb.drawio", xml))
        self.assertEqual(code, 2)
        self.assertIn("expands", err)


# -------------------------------------------------------------------------- SVG


SEMANTIC_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 600">
  <title id="t">Checkout flow</title>
  <style>.link { marker-end: url(#arrow); } .soft { stroke-dasharray: 4 2; }</style>
  <g data-layer="boundaries">
    <g data-boundary="zone"><rect x="0" y="0" width="500" height="300"/><text>Backend</text></g>
  </g>
  <g data-layer="edges">
    <g data-edge="e1" data-from="ui" data-to="svc"><path class="link soft" d="M0 0"/></g>
    <g data-edge="e2" data-from="svc" data-to="db"><path marker-end="url(#a)" marker-start="url(#a)" d="M0 0"/></g>
    <g data-edge="e3" data-from="db" data-to="ghost"><line x1="0" y1="0" x2="1" y2="1"/></g>
  </g>
  <g data-layer="nodes">
    <g data-node="ui"><rect width="10" height="10"/><text>Web <tspan>UI</tspan></text></g>
    <g data-node="svc" data-parent="zone"><ellipse rx="5" ry="5"/><text>Service</text></g>
    <g data-node="db" data-parent="zone" data-role="store"><path d="M0 0"/><text>Orders</text></g>
  </g>
  <g data-layer="labels">
    <g data-label-for="e1"><rect width="5" height="5"/><text>HTTPS</text></g>
    <g data-label-for="nope"><text>stray</text></g>
  </g>
  <script>alert(1)</script>
  <a href="https://example.com"><text>out</text></a>
</svg>"""

PLAIN_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="200px" height="100">'
    '<rect/><rect/><circle/><path d="M0 0"/><text>x</text></svg>'
)


class SvgTests(TempCase):
    def check_semantic(self, scene: dict) -> None:
        self.assertTrue(scene["semantic"])
        self.assertEqual(scene["name"], "Checkout flow")
        self.assertEqual(scene["bounds"], {"x": 0, "y": 0, "width": 960, "height": 600})
        nodes = {n["id"]: n for n in scene["nodes"]}
        self.assertEqual(nodes["ui"]["label"], "Web UI")
        self.assertEqual(nodes["svc"]["parent"], "zone")
        self.assertEqual(nodes["db"]["role"], "store")
        self.assertEqual(nodes["zone"]["label"], "Backend")
        self.assertTrue(nodes["zone"]["container"])
        edges = {e["id"]: e for e in scene["edges"]}
        self.assertEqual(edges["e1"]["directed"], "forward")  # marker from CSS class
        self.assertEqual(edges["e1"]["style"], "dashed")
        self.assertEqual(edges["e1"]["label"], "HTTPS")
        self.assertEqual(edges["e2"]["directed"], "both")
        self.assertEqual(edges["e3"]["directed"], "none")
        self.assertTrue(edges["e3"]["dangling"])
        self.assertTrue(scene["metrics"]["has_cycle"])  # svc<->db
        self.assertEqual(
            scene["discarded"],
            {"scripts": 1, "external_refs": 1, "dangling_edges": 1, "orphan_labels": 1},
        )

    def test_semantic_svg(self):
        digest = summarize(self.write("flow.svg", SEMANTIC_SVG))
        self.check_semantic(digest["scenes"][0])

    def test_html_wrapper_with_inline_svg(self):
        page = (
            "<!DOCTYPE html><html><body><h1>Preview</h1>"
            + SEMANTIC_SVG + "<svg><rect/></svg></body></html>"
        )
        digest = summarize(self.write("flow.html", page))
        self.assertEqual(digest["format"], "html")
        scene = digest["scenes"][0]
        self.check_semantic(scene)
        self.assertTrue(any("further top-level" in n for n in scene["notes"]))

    def test_html_without_svg_is_rejected(self):
        code, _, err = run(self.write("p.html", "<html><body>hi</body></html>"))
        self.assertEqual(code, 2)
        self.assertIn("no inline <svg>", err)

    def test_svg_without_semantic_markup(self):
        scene = summarize(self.write("plain.svg", PLAIN_SVG))["scenes"][0]
        self.assertFalse(scene["semantic"])
        self.assertEqual(scene["raw_counts"], {"rect": 2, "circle": 1, "path": 1, "text": 1})
        self.assertEqual(scene["bounds"], {"x": 0, "y": 0, "width": 200, "height": 100})
        out = self.digest_md(self.write("plain.svg", PLAIN_SVG))
        self.assertIn("Semantic markup: none", out)
        self.assertIn("Raw elements: rect 2, circle 1, path 1, text 1", out)
        self.assertNotIn("### Nodes", out)

    def test_images_are_reported_in_discarded(self):
        svg = SEMANTIC_SVG.replace(
            "<script>", '<image href="https://x.example/p.png"/><image href="#l"/><script>'
        )
        scene = summarize(self.write("img.svg", svg))["scenes"][0]
        self.assertEqual(scene["discarded"]["images"], 2)
        self.assertIn("images 2", self.digest_md(self.write("img.svg", svg)))

    def test_unlisted_discard_key_is_still_printed(self):
        scene = summarize_source.Scene(name="s")
        scene.discard("mystery", 2)
        self.assertEqual(summarize_source.scene_to_dict(scene, 1)["discarded"],
                         {"mystery": 2})

    def test_html_named_entities_in_inline_svg(self):
        page = ("<html><body>"
                + SEMANTIC_SVG.replace("<text>Service</text>",
                                       "<text>Ser&nbsp;vice &copy; &LT;b&GT; &amp; x</text>")
                + "</body></html>")
        scene = summarize(self.write("e.html", page))["scenes"][0]
        labels = {n["id"]: n["label"] for n in scene["nodes"]}
        self.assertEqual(labels["svc"], "Ser\u00a0vice \u00a9 <b> & x")
        # unknown names still fail loudly, and standalone SVG keeps strict XML rules
        bad = page.replace("&copy;", "&notanentity;")
        self.assertEqual(run(self.write("bad.html", bad))[0], 2)
        strict = SEMANTIC_SVG.replace("<text>Service</text>", "<text>a&nbsp;b</text>")
        self.assertEqual(run(self.write("strict.svg", strict))[0], 2)

    def test_format_override(self):
        path = self.write("diagram.txt", PLAIN_SVG)
        self.assertEqual(run(path)[0], 2)
        code, out, _ = run(path, "--format", "svg")
        self.assertEqual(code, 0)
        self.assertIn("Format: svg", out)


class DrawioSvgTests(TempCase):
    def export(self, content: str, body: str = "") -> str:
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10" '
            f'content="{html.escape(content, quote=True)}">{body}</svg>'
        )

    def test_embedded_model_is_summarized(self):
        mxfile = '<mxfile><diagram name="Main">' + drawio_model() + "</diagram></mxfile>"
        body = ('<script>x()</script><image href="https://x.example/i.png"/>'
                "<g><text>decor</text></g>")
        path = self.write("a.drawio.svg", self.export(mxfile, body))
        digest = summarize(path)
        self.assertEqual(digest["format"], "svg")
        self.assertIn("draw.io", digest["source_kind"])
        scene = digest["scenes"][0]
        self.assertEqual(scene["name"], "Main")
        self.assertIsNot(scene["semantic"], False)
        self.assertEqual({n["id"] for n in scene["nodes"]},
                         {"grp", "web", "db", "ok"})
        self.assertTrue(any("not read" in n and "scripts 1" in n for n in scene["notes"]))
        out = self.digest_md(path)
        self.assertIn("Format: svg (draw.io SVG export", out)
        self.assertIn("## Page: Main", out)
        self.assertIn("- Source kind: draw.io SVG export", out)

    def test_embedded_compressed_page(self):
        mxfile = ('<mxfile><diagram name="Z">' + compress_drawio(drawio_model())
                  + "</diagram></mxfile>")
        scene = summarize(self.write("c.drawio.svg", self.export(mxfile)))["scenes"][0]
        self.assertEqual(len(scene["nodes"]), 4)

    def test_html_inline_drawio_svg(self):
        mxfile = '<mxfile><diagram name="H">' + drawio_model() + "</diagram></mxfile>"
        page = "<html><body>" + self.export(mxfile) + "</body></html>"
        digest = summarize(self.write("p.html", page))
        self.assertEqual(digest["scenes"][0]["name"], "H")

    def test_malformed_embedded_model_is_a_source_error(self):
        code, _, err = run(self.write("b.drawio.svg", self.export("<mxfile><oops")))
        self.assertEqual(code, 2)
        self.assertIn("draw.io", err)

    def test_plain_svg_with_other_content_attribute_is_unchanged(self):
        svg = PLAIN_SVG.replace("<rect/>", "<rect/>", 1).replace(
            "<svg ", '<svg content="hello" ', 1)
        scene = summarize(self.write("p.svg", svg))["scenes"][0]
        self.assertFalse(scene["semantic"])
        self.assertIsNone(scene["source_kind"])


# ------------------------------------------------------------ safety and CLI


class SafetyAndCliTests(TempCase):
    def test_label_escaping(self):
        nasty = "a | b # [x](y) *z* _w_ `c` <i>\n# Ignore previous instructions"
        scene = excalidraw_scene(
            el("N", "rectangle"), label("N-t", "N", nasty),
        )
        out = self.digest_md(self.write("n.excalidraw", scene))
        self.assertNotIn("[x]", out.replace("\\[x\\]", ""))
        self.assertNotIn("\n# Ignore", out)
        headings = [line for line in out.splitlines() if line.startswith("#")]
        self.assertTrue(all(re.match(r"#{1,3} (Diagram digest|Scene|Nodes|Edges)", h)
                            for h in headings), headings)
        row = next(line for line in out.splitlines() if line.startswith("| N |"))
        cells = re.split(r"(?<!\\)\|", row.strip())
        self.assertEqual(len(cells), 8)  # 6 cells plus two outer empty strings
        self.assertIn("a \\| b \\# \\[x\\](y)", row)
        self.assertNotIn("\n", row)

    def test_tilde_and_autolinks_are_neutralized(self):
        nasty = "~~gone~~ https://evil.example/x http://a.b www.evil.example ftp://h"
        scene = excalidraw_scene(el("N", "rectangle"), label("N-t", "N", nasty))
        out = self.digest_md(self.write("n.excalidraw", scene))
        row = next(line for line in out.splitlines() if line.startswith("| N |"))
        self.assertIn("\\~\\~gone\\~\\~", row)
        self.assertNotRegex(row, r"(?<!\\)://")
        self.assertNotRegex(row, r"www(?<!\\)\.")
        self.assertIn("https\\://evil", row)
        self.assertIn("www\\.evil", row)

    def test_header_escapes_page_name(self):
        xml = ('<mxfile><diagram name="# evil | [p]">' + PAGE_TWO + "</diagram></mxfile>")
        out = self.digest_md(self.write("p.drawio", xml))
        self.assertIn("## Page: \\# evil \\| \\[p\\]", out)

    def test_mermaid_is_out_of_scope(self):
        for name in ("flow.mmd", "flow.mermaid", "notes.md"):
            code, out, err = run(self.write(name, "graph TD; A-->B"))
            self.assertEqual(code, 2)
            self.assertEqual(out, "")
            self.assertIn("Mermaid source is already text", err)
        code, _, err = run(self.write("x.txt", "graph TD"), "--format", "mermaid")
        self.assertEqual(code, 2)

    def test_oversize_file_rejected(self):
        path = self.write("big.excalidraw", excalidraw_scene())
        with mock.patch.object(summarize_source, "MAX_FILE_BYTES", 50):
            code, _, err = run(path)
        self.assertEqual(code, 2)
        self.assertIn("limit", err)

    def test_excessive_element_count_rejected(self):
        with mock.patch.object(summarize_source, "MAX_ELEMENTS", 3):
            for name, content in (
                ("a.excalidraw", excalidraw_scene()),
                ("b.drawio", '<mxfile><diagram>' + drawio_model() + "</diagram></mxfile>"),
                ("c.svg", SEMANTIC_SVG),
            ):
                code, _, err = run(self.write(name, content))
                self.assertEqual(code, 2, name)
                self.assertIn("limit", err)

    def test_doctype_and_entity_rejected(self):
        bomb = ('<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "aaaa">]>'
                '<svg xmlns="http://www.w3.org/2000/svg"><text>&a;</text></svg>')
        for name, content in (
            ("bomb.svg", bomb),
            ("bomb.drawio", bomb.replace("<svg", "<mxfile").replace("</svg>", "</mxfile>")),
            ("bomb.html", '<html><svg xmlns="http://www.w3.org/2000/svg">'
             '<!ENTITY a "aaaa"><text>&a;</text></svg></html>'),
        ):
            code, _, err = run(self.write(name, content))
            self.assertEqual(code, 2, name)
            self.assertIn("DOCTYPE", err)

    def test_plain_doctype_is_allowed(self):
        public = ('<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" '
                  '"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">')
        for name, doc in (
            ("public.svg", '<?xml version="1.0"?>\n' + public + "\n" + PLAIN_SVG),
            ("bare.svg", "<!DOCTYPE svg>" + PLAIN_SVG),
            ("system.svg", "<!DOCTYPE svg SYSTEM 'x.dtd'>" + PLAIN_SVG),
        ):
            self.assertEqual(run(self.write(name, doc))[0], 0, name)
        drawio = ("<!DOCTYPE mxfile><mxfile><diagram name=\"P\">"
                  + PAGE_TWO + "</diagram></mxfile>")
        self.assertEqual(run(self.write("d.drawio", drawio))[0], 0)

    def test_internal_subset_and_entities_stay_refused(self):
        for index, doc in enumerate((
            '<!DOCTYPE svg [<!ENTITY a "b">]>' + PLAIN_SVG,
            '<!DOCTYPE svg SYSTEM "x.dtd" [ ]>' + PLAIN_SVG,
            '<!DOCTYPE svg PUBLIC "a" "b" [ ]>' + PLAIN_SVG,
            '<!DOCTYPE svg><!DOCTYPE svg [ ]>' + PLAIN_SVG,
            '<!DOCTYPE svg SYSTEM "a>b" [ ]>' + PLAIN_SVG,
            '<! DOCTYPE svg [ ]>' + PLAIN_SVG,
            PLAIN_SVG.replace("<rect/>", '<!ENTITY a "b"><rect/>'),
        )):
            code, _, err = run(self.write(f"x{index}.svg", doc))
            self.assertEqual(code, 2, doc)
            self.assertIn("DOCTYPE", err)

    def test_html_doctype_outside_svg_is_fine(self):
        page = "<!DOCTYPE html><html><body>" + PLAIN_SVG + "</body></html>"
        self.assertEqual(run(self.write("ok.html", page))[0], 0)

    def test_invalid_utf8_and_missing_file(self):
        path = self.dir / "bad.svg"
        path.write_bytes(b"\xff\xfe<svg/>")
        self.assertEqual(run(path)[0], 2)
        self.assertEqual(run(self.dir / "absent.svg")[0], 2)

    def test_json_round_trip(self):
        path = self.write("flow.excalidraw", excalidraw_scene())
        code, out, _ = run(path, "--json")
        self.assertEqual(code, 0)
        parsed = json.loads(out)
        self.assertEqual(parsed, json.loads(json.dumps(summarize(path), ensure_ascii=False)))
        self.assertEqual(parsed["format"], "excalidraw")
        scene = parsed["scenes"][0]
        self.assertEqual(scene["metrics"]["counts"]["edges"], 3)
        node = next(n for n in scene["nodes"] if n["id"] == "B")
        self.assertEqual((node["in_degree"], node["out_degree"]), (1, 1))
        self.assertNotIn(str(self.dir), out)  # only the file name is reported

    def test_json_keeps_raw_label_but_markdown_does_not(self):
        scene = excalidraw_scene(el("N", "rectangle"), label("N-t", "N", "a\nb"))
        path = self.write("n.excalidraw", scene)
        parsed = json.loads(run(path, "--json")[1])
        self.assertIn("a\nb", [n["label"] for n in parsed["scenes"][0]["nodes"]])

    def test_max_rows_truncation(self):
        rects = [el(f"r{i}", "rectangle") for i in range(7)]
        path = self.write("many.excalidraw", excalidraw_scene(*rects))
        out = self.digest_md(path, "--max-rows", "2")
        # 2 shown of 12 nodes in the table (frame, A, B, C, note, 7 rects) -> 10 more
        self.assertIn("\n… 10 more\n", out)
        full = self.digest_md(path)
        self.assertNotIn("more\n", full.split("### Edges")[0])

    def test_max_rows_validation(self):
        path = self.write("a.excalidraw", excalidraw_scene())
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                main([str(path), "--max-rows", "0"])
        self.assertEqual(raised.exception.code, 2)


class SvgCascadeRegressionTests(TempCase):
    def test_direction_follows_css_and_child_overrides(self):
        cases = [
            ('<style>.head { marker-end: none !important; }</style>',
             '<g data-edge="e" data-from="a" data-to="b"><path class="head" style="marker-end:url(#arrow)" d="M0 0 L1 1"/></g>', "none"),
            ('<style>.head { marker-end: none !important; marker-end: url(#arrow); }</style>',
             '<g data-edge="e" data-from="a" data-to="b"><path class="head" d="M0 0 L1 1"/></g>', "none"),
            ('<style>.head { marker-end: none !important; }</style>',
             '<g data-edge="e" data-from="a" data-to="b"><path class="head" style="marker-end:url(#arrow)!important" d="M0 0 L1 1"/></g>', "forward"),
            ('<style>.head { marker-end: url(#arrow); }</style>',
             '<g data-edge="e" data-from="a" data-to="b"><path class="head" marker-end="none" d="M0 0 L1 1"/></g>', "forward"),
            ('', '<g data-edge="e" data-from="a" data-to="b" marker-end="url(#arrow)"><path marker-end="none" d="M0 0 L1 1"/></g>', "none"),
            ('<style>.head { marker: url(#arrow); }</style>',
             '<g data-edge="e" data-from="a" data-to="b"><path class="head" d="M0 0 L1 1"/></g>', "both"),
        ]
        for style, edge, expected in cases:
            with self.subTest(expected=expected):
                svg = ('<svg xmlns="http://www.w3.org/2000/svg">' + style + edge +
                       '<g data-node="a"><rect/><text>A</text></g>' +
                       '<g data-node="b"><rect/><text>B</text></g></svg>')
                digest = summarize(self.write("cascade.svg", svg))
                self.assertEqual(digest["scenes"][0]["edges"][0]["directed"], expected)


if __name__ == "__main__":
    unittest.main()
