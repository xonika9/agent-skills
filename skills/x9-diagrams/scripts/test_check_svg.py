#!/usr/bin/env python3
"""Regression tests for check_svg.py."""

from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from check_svg import main, validate_svg


# A realistic diagram: two nodes inside a boundary, one labeled edge.
# The "api" node is positioned with translate(); everything else uses
# absolute coordinates. The connector runs from the right edge of "api" to the
# left edge of "db"; its label mask sits in the open space between them.
VALID = """\
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 320"
     role="img" aria-labelledby="sample-title sample-desc">
  <title id="sample-title">Service reads orders</title>
  <desc id="sample-desc">The API service reads orders from the database inside one platform boundary.</desc>
  <style>
    .boundary { fill: #f4f6f8; stroke: #8a94a0; stroke-width: 1.5; }
    .node { fill: #ffffff; stroke: #2f3b4a; stroke-width: 2; }
    .edge { fill: none; stroke: #2f3b4a; stroke-width: 2; }
    .mask { fill: #ffffff; }
    .heading { font: 600 14px system-ui, -apple-system, "Segoe UI", sans-serif; fill: #4a5563; }
    .title { font: 600 16px system-ui, -apple-system, "Segoe UI", sans-serif; fill: #1b2430; }
    .label { font: 13px system-ui, -apple-system, "Segoe UI", sans-serif; fill: #2f3b4a; }
  </style>
  <defs>
    <marker id="sample-arrow" viewBox="0 0 10 10" refX="9" refY="5"
            markerWidth="8" markerHeight="8" orient="auto">
      <path d="M0 0 L10 5 L0 10 z" fill="#2f3b4a"/>
    </marker>
  </defs>
  <g data-layer="boundaries">
    <g data-boundary="platform">
      <rect class="boundary" x="20" y="20" width="600" height="280" rx="12"/>
      <text class="heading" x="40" y="46">Platform</text>
    </g>
  </g>
  <g data-layer="edges">
    <g data-edge="api-reads-db" data-from="api" data-to="db">
      <path class="edge" d="M220 146 H420" marker-end="url(#sample-arrow)"/>
    </g>
  </g>
  <g data-layer="nodes">
    <g data-node="api" data-parent="platform" transform="translate(60 110)">
      <rect class="node" width="160" height="72" rx="8"/>
      <text class="title" x="80" y="42" text-anchor="middle">API service</text>
    </g>
    <g data-node="db" data-parent="platform" data-role="store">
      <rect class="node" x="420" y="110" width="160" height="72" rx="8"/>
      <text class="title" x="500" y="152" text-anchor="middle">Orders DB</text>
    </g>
  </g>
  <g data-layer="labels">
    <g data-label-for="api-reads-db">
      <rect class="mask" x="280" y="134" width="80" height="24"/>
      <text class="label" x="320" y="151" text-anchor="middle">reads</text>
    </g>
  </g>
</svg>
"""


def mutate(old: str, new: str, source: str = VALID) -> str:
    assert old in source, f"sample does not contain {old!r}"
    return source.replace(old, new, 1)


def add_to_layer(layer: str, fragment: str, source: str = VALID) -> str:
    start = source.index(f'<g data-layer="{layer}">')
    end = source.index("\n  </g>", start)
    return source[:end] + "\n" + fragment + source[end:]


def check(source: str, **kwargs):
    return validate_svg(source, **kwargs)


def run_cli(*args: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(list(args))
    return code, out.getvalue(), err.getvalue()


class SvgTestCase(unittest.TestCase):
    def assertHas(self, messages: list[str], fragment: str) -> None:
        self.assertTrue(
            any(fragment in message for message in messages),
            f"{fragment!r} not found in {messages!r}",
        )

    def assertClean(self, source: str, **kwargs) -> None:
        errors, warnings, notes = check(source, **kwargs)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertEqual(notes, [])

    def assertErrors(self, source: str, fragment: str) -> list[str]:
        errors, _, _ = check(source)
        self.assertHas(errors, fragment)
        return errors

    def assertWarns(self, source: str, fragment: str) -> list[str]:
        errors, warnings, _ = check(source)
        self.assertEqual(errors, [])
        self.assertHas(warnings, fragment)
        return warnings


class ValidDocumentTests(SvgTestCase):
    def test_valid_sample_passes_without_warnings(self):
        self.assertClean(VALID)

    def test_cli_prints_pass_for_valid_sample(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.svg"
            path.write_text(VALID, encoding="utf-8")
            code, out, err = run_cli(str(path))
        self.assertEqual(code, 0)
        self.assertEqual(out, f"PASS: {path}\n")
        self.assertEqual(err, "")

    def test_cli_accepts_xml_declaration_with_encoding(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.svg"
            path.write_bytes(
                b'<?xml version="1.0" encoding="UTF-8"?>\n' + VALID.encode("utf-8")
            )
            code, _, _ = run_cli(str(path))
        self.assertEqual(code, 0)

    def test_boundary_around_connector_is_not_an_obstacle(self):
        # The connector lies entirely inside the "platform" boundary shape.
        self.assertClean(VALID)

    def test_diagonal_connector_segment_is_allowed(self):
        source = mutate('d="M220 146 H420"', 'd="M220 146 L420 160"')
        self.assertClean(source)


class ExitCodeTests(SvgTestCase):
    def test_exit_2_for_missing_file(self):
        code, out, err = run_cli("/nonexistent/diagram.svg")
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("ERROR: file not found", err)

    def test_exit_2_for_unparseable_xml(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.svg"
            path.write_text("<svg><g></svg>", encoding="utf-8")
            code, _, err = run_cli(str(path))
        self.assertEqual(code, 2)
        self.assertIn("ERROR: cannot parse", err)

    def test_exit_2_for_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            code, _, err = run_cli(directory)
        self.assertEqual(code, 2)
        self.assertIn("ERROR:", err)

    def test_malformed_xml_raises_parse_error(self):
        with self.assertRaises(ET.ParseError):
            check("<svg")

    def test_exit_1_prints_errors_and_fail_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.svg"
            path.write_text(mutate('role="img"', ""), encoding="utf-8")
            code, out, err = run_cli(str(path))
        self.assertEqual(code, 1)
        self.assertNotIn("PASS", out)
        self.assertIn("ERROR: root <svg> must have role", err)
        self.assertIn("FAIL: 1 issue(s)", err)

    def test_output_order_notes_then_warnings(self):
        source = mutate('d="M220 146 H420"', 'd="M200 146 H420"')
        source = mutate(
            'transform="translate(60 110)"', 'transform="rotate(5) translate(60 110)"', source
        )
        source = add_to_layer(
            "nodes",
            '    <g data-node="x" data-parent="platform"><rect x="500" y="250" width="200" height="40"/><text x="510" y="270">X</text></g>',
            source,
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "order.svg"
            path.write_text(source, encoding="utf-8")
            code, out, _ = run_cli(str(path))
        self.assertEqual(code, 0)
        lines = out.splitlines()
        kinds = [line.split(":", 1)[0] for line in lines]
        self.assertEqual(kinds[-1], "PASS")
        self.assertIn("NOTE", kinds)
        self.assertIn("WARN", kinds)
        self.assertLess(max(i for i, k in enumerate(kinds) if k == "NOTE"),
                        min(i for i, k in enumerate(kinds) if k == "WARN"))


class DocumentErrorTests(SvgTestCase):
    def test_wrong_root_element(self):
        errors, _, _ = check('<html xmlns="http://www.w3.org/1999/xhtml"/>')
        self.assertHas(errors, "root element must be <svg>")

    def test_root_without_svg_namespace(self):
        errors, _, _ = check('<svg viewBox="0 0 10 10"/>')
        self.assertHas(errors, "root element must be <svg>")

    def test_missing_viewbox(self):
        self.assertErrors(mutate('viewBox="0 0 640 320"', ""), "needs a viewBox")

    def test_viewbox_with_three_numbers(self):
        self.assertErrors(mutate("0 0 640 320", "0 0 640"), "viewBox must be four")

    def test_viewbox_with_non_numbers(self):
        self.assertErrors(mutate("0 0 640 320", "0 0 wide tall"), "viewBox must be four")

    def test_viewbox_with_nonfinite_number(self):
        self.assertErrors(mutate("0 0 640 320", "0 0 inf 320"), "four finite numbers")

    def test_viewbox_with_nonpositive_size(self):
        self.assertErrors(mutate("0 0 640 320", "0 0 640 0"), "must be positive")
        self.assertErrors(mutate("0 0 640 320", "0 0 -640 320"), "must be positive")

    def test_viewbox_accepts_commas(self):
        self.assertClean(mutate("0 0 640 320", "0,0,640,320"))


class AccessibilityTests(SvgTestCase):
    def test_missing_role(self):
        self.assertErrors(mutate('role="img"', ""), 'role="img"')

    def test_wrong_role(self):
        self.assertErrors(mutate('role="img"', 'role="presentation"'), 'role="img"')

    def test_missing_aria_labelledby(self):
        source = mutate('aria-labelledby="sample-title sample-desc"', "")
        self.assertErrors(source, "needs aria-labelledby")

    def test_aria_labelledby_must_reference_desc(self):
        source = mutate('aria-labelledby="sample-title sample-desc"', 'aria-labelledby="sample-title"')
        self.assertErrors(source, "does not reference the <desc> id")

    def test_aria_labelledby_must_reference_title(self):
        source = mutate('aria-labelledby="sample-title sample-desc"', 'aria-labelledby="sample-desc"')
        self.assertErrors(source, "does not reference the <title> id")

    def test_aria_labelledby_unresolved_id(self):
        source = mutate("sample-title sample-desc", "sample-title sample-desc ghost")
        self.assertErrors(source, "aria-labelledby id 'ghost' does not resolve")

    def test_title_without_id(self):
        self.assertErrors(mutate('<title id="sample-title">', "<title>"), "<title> needs an id")

    def test_title_must_be_first_child(self):
        title = '  <title id="sample-title">Service reads orders</title>\n'
        source = mutate(title, "")
        source = mutate("  <style>", title + "  <style>", source)
        self.assertErrors(source, "<title> must be the first element child")

    def test_empty_title(self):
        self.assertErrors(mutate("Service reads orders", "  "), "<title> must not be empty")

    def test_missing_desc(self):
        desc = next(line for line in VALID.splitlines() if "<desc" in line) + "\n"
        errors = self.assertErrors(mutate(desc, ""), "needs a <desc>")
        self.assertHas(errors, "aria-labelledby id 'sample-desc' does not resolve")

    def test_empty_desc(self):
        source = mutate(
            "The API service reads orders from the database inside one platform boundary.", ""
        )
        self.assertErrors(source, "<desc> must not be empty")


class SelfContainmentTests(SvgTestCase):
    def test_script_element(self):
        self.assertErrors(add_to_layer("labels", "<script>alert(1)</script>"), "<script>")

    def test_foreign_object(self):
        source = add_to_layer("labels", "<foreignObject><div/></foreignObject>")
        self.assertErrors(source, "<foreignObject>")

    def test_event_handler_attribute(self):
        source = mutate('<rect class="node" width="160"', '<rect class="node" onclick="x()" width="160"')
        self.assertErrors(source, "event-handler attribute 'onclick'")

    def test_style_import(self):
        source = mutate("<style>", '<style>@import url(#sample-arrow);')
        self.assertErrors(source, "@import")

    def test_import_inside_css_comment_is_ignored(self):
        self.assertClean(mutate("<style>", "<style>/* no @import here */"))

    def test_external_href(self):
        source = add_to_layer("labels", '<use href="https://example.com/a.svg#x"/>')
        self.assertErrors(source, "must start with '#'")

    def test_external_xlink_href(self):
        source = mutate(
            'xmlns="http://www.w3.org/2000/svg"',
            'xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"',
        )
        source = add_to_layer("labels", '<use xlink:href="other.svg#x"/>', source)
        self.assertErrors(source, "must start with '#'")

    def test_local_href_resolves(self):
        self.assertClean(add_to_layer("labels", '<a href="#sample-arrow"/>'))

    def test_unresolved_href(self):
        source = add_to_layer("labels", '<use href="#missing"/>')
        self.assertErrors(source, "href '#missing' does not resolve")

    def test_external_url_in_attribute(self):
        source = mutate('fill="#2f3b4a"/>', 'fill="url(https://example.com/p.svg#g)"/>')
        self.assertErrors(source, "must point to a local #id")

    def test_external_url_in_style_element(self):
        source = mutate(".mask { fill: #ffffff; }", ".mask { fill: url('https://x.test/a.png'); }")
        self.assertErrors(source, "must point to a local #id")

    def test_unresolved_url_reference(self):
        source = mutate("url(#sample-arrow)", "url(#missing-arrow)")
        self.assertErrors(source, "url(#missing-arrow) does not resolve")

    def test_unresolved_url_in_style_element(self):
        source = mutate(".mask { fill: #ffffff; }", ".mask { fill: url(#missing-gradient); }")
        self.assertErrors(source, "url(#missing-gradient) does not resolve")

    def test_quoted_local_url_is_accepted(self):
        self.assertClean(mutate("url(#sample-arrow)", "url('#sample-arrow')"))

    def test_duplicate_ids(self):
        source = mutate('<marker id="sample-arrow"', '<marker id="sample-title"')
        source = mutate("url(#sample-arrow)", "url(#sample-title)", source)
        self.assertErrors(source, "duplicate id 'sample-title'")


class LayerTests(SvgTestCase):
    def test_missing_layer(self):
        source = mutate('<g data-layer="labels">', '<g data-layer="notes">')
        errors = self.assertErrors(source, "missing data-layer 'labels'")
        self.assertHas(errors, "unknown data-layer 'notes'")

    def test_duplicate_layer(self):
        source = mutate('<g data-layer="edges">', '<g data-layer="nodes">')
        self.assertErrors(source, "appears 2 times")

    def test_wrong_order(self):
        source = mutate('<g data-layer="edges">', '<g data-layer="TMP">')
        source = mutate('<g data-layer="nodes">', '<g data-layer="edges">', source)
        source = mutate('<g data-layer="TMP">', '<g data-layer="nodes">', source)
        self.assertErrors(source, "data-layer order must be")

    def test_nested_layer(self):
        source = add_to_layer("labels", '<g data-layer="extra"></g>')
        self.assertErrors(source, "must be a direct child of the root")


class SemanticMarkupTests(SvgTestCase):
    def test_node_outside_nodes_layer(self):
        fragment = '<g data-node="stray"><rect width="10" height="10"/></g>'
        self.assertErrors(add_to_layer("edges", fragment), "node 'stray' must be inside the 'nodes' layer")

    def test_boundary_outside_boundaries_layer(self):
        fragment = '<g data-boundary="stray"><rect width="10" height="10"/></g>'
        self.assertErrors(
            add_to_layer("nodes", fragment), "boundary 'stray' must be inside the 'boundaries' layer"
        )

    def test_edge_outside_edges_layer(self):
        fragment = '<g data-edge="stray" data-from="api" data-to="db"><line x1="0" y1="0" x2="1" y2="1"/></g>'
        self.assertErrors(add_to_layer("labels", fragment), "edge 'stray' must be inside the 'edges' layer")

    def test_label_outside_labels_layer(self):
        fragment = '<g data-label-for="api-reads-db"><rect width="1" height="1"/></g>'
        self.assertErrors(add_to_layer("nodes", fragment), "label 'api-reads-db' must be inside the 'labels' layer")

    def test_duplicate_node_id(self):
        fragment = '<g data-node="api" data-parent="platform"><rect x="10" y="250" width="50" height="40"/></g>'
        self.assertErrors(add_to_layer("nodes", fragment), "duplicate node id 'api'")

    def test_duplicate_boundary_id(self):
        fragment = '<g data-boundary="platform"><rect x="1" y="1" width="5" height="5"/></g>'
        self.assertErrors(add_to_layer("boundaries", fragment), "duplicate boundary id 'platform'")

    def test_node_and_boundary_share_id(self):
        source = mutate('data-boundary="platform"', 'data-boundary="api"')
        source = mutate('data-parent="platform"', 'data-parent="api"', source)
        source = mutate('data-parent="api"', 'data-parent="api"', source)
        self.assertErrors(source, "used by both a node and a boundary")

    def test_edge_without_data_to(self):
        self.assertErrors(mutate(' data-to="db"', ""), "needs data-to")

    def test_edge_without_data_from(self):
        self.assertErrors(mutate(' data-from="api"', ""), "needs data-from")

    def test_edge_endpoint_does_not_resolve(self):
        self.assertErrors(mutate('data-to="db"', 'data-to="ghost"'), "data-to 'ghost' is not a node or boundary")

    def test_edge_may_target_boundary(self):
        source = mutate('data-to="db"', 'data-to="platform"')
        errors, _, _ = check(source)
        self.assertEqual(errors, [])

    def test_parent_must_be_boundary(self):
        source = mutate('data-node="db" data-parent="platform"', 'data-node="db" data-parent="api"')
        self.assertErrors(source, "data-parent 'api' is not a boundary")

    def test_parent_does_not_resolve(self):
        source = mutate('data-node="db" data-parent="platform"', 'data-node="db" data-parent="ghost"')
        self.assertErrors(source, "data-parent 'ghost' is not a boundary")

    def test_parent_cycle(self):
        outer = '<g data-boundary="a" data-parent="b"><rect x="1" y="1" width="5" height="5"/></g>'
        inner = '<g data-boundary="b" data-parent="a"><rect x="1" y="1" width="5" height="5"/></g>'
        errors = self.assertErrors(
            add_to_layer("boundaries", outer + inner), "data-parent cycle among boundaries"
        )
        self.assertEqual(sum("cycle" in error for error in errors), 1)

    def test_boundary_parent_to_itself_is_a_cycle(self):
        source = mutate('data-boundary="platform"', 'data-boundary="platform" data-parent="platform"')
        self.assertErrors(source, "data-parent cycle among boundaries")

    def test_nested_boundary_parent_is_valid(self):
        fragment = (
            '<g data-boundary="zone" data-parent="platform">'
            '<rect x="40" y="60" width="300" height="200"/></g>'
        )
        errors, _, _ = check(add_to_layer("boundaries", fragment))
        self.assertEqual(errors, [])

    def test_label_does_not_resolve_to_edge(self):
        self.assertErrors(
            mutate('data-label-for="api-reads-db"', 'data-label-for="ghost"'),
            "label for 'ghost' does not resolve to an edge",
        )

    def test_node_with_two_shapes(self):
        source = mutate(
            '<rect class="node" width="160" height="72" rx="8"/>',
            '<rect class="node" width="160" height="72" rx="8"/><circle r="4"/>',
        )
        self.assertErrors(source, "node 'api' must contain exactly one shape")

    def test_node_without_shape(self):
        source = mutate('<rect class="node" width="160" height="72" rx="8"/>', "")
        self.assertErrors(source, "node 'api' must contain exactly one shape")

    def test_boundary_without_shape(self):
        source = mutate('<rect class="boundary" x="20" y="20" width="600" height="280" rx="12"/>', "")
        self.assertErrors(source, "boundary 'platform' must contain exactly one shape")

    def test_node_shape_may_be_wrapped_in_a_plain_group(self):
        source = mutate(
            '<rect class="node" width="160" height="72" rx="8"/>',
            '<g><rect class="node" width="160" height="72" rx="8"/></g>',
        )
        self.assertClean(source)

    def test_line_is_not_a_node_shape(self):
        source = mutate(
            '<rect class="node" width="160" height="72" rx="8"/>',
            '<line x1="0" y1="0" x2="1" y2="1"/>',
        )
        self.assertErrors(source, "node 'api' must contain exactly one shape")

    def test_edge_with_two_connectors(self):
        source = mutate(
            'marker-end="url(#sample-arrow)"/>',
            'marker-end="url(#sample-arrow)"/><line x1="0" y1="0" x2="1" y2="1"/>',
        )
        self.assertErrors(source, "edge 'api-reads-db' must contain exactly one path, line, or polyline")

    def test_edge_without_connector(self):
        source = mutate('<path class="edge" d="M220 146 H420" marker-end="url(#sample-arrow)"/>', "")
        self.assertErrors(source, "edge 'api-reads-db' must contain exactly one path, line, or polyline")

    def test_element_with_two_semantic_kinds(self):
        source = mutate('data-node="db"', 'data-node="db" data-edge="db" data-from="api" data-to="api"')
        self.assertErrors(source, "more than one semantic kind")

    def test_empty_semantic_id(self):
        self.assertErrors(mutate('data-node="db"', 'data-node=""'), "data-node must not be empty")


class GeometryWarningTests(SvgTestCase):
    def test_shape_outside_viewbox(self):
        source = mutate('y="110" width="160" height="72"', 'y="110" width="400" height="72"')
        self.assertWarns(source, "node 'db' extends outside the viewBox")

    def test_connector_outside_viewbox(self):
        source = mutate("M220 146 H420", "M220 146 H700")
        self.assertWarns(source, "edge 'api-reads-db' extends outside the viewBox")

    def test_label_mask_outside_viewbox(self):
        source = mutate('x="280" y="134"', 'x="280" y="-10"')
        self.assertWarns(source, "label mask for edge 'api-reads-db' extends outside the viewBox")

    def test_boundary_outside_viewbox(self):
        source = mutate('width="600" height="280"', 'width="700" height="280"')
        self.assertWarns(source, "boundary 'platform' extends outside the viewBox")

    def test_negative_viewbox_origin_is_honored(self):
        source = mutate("0 0 640 320", "-100 0 740 320")
        self.assertClean(source)

    def test_endpoint_short_of_node(self):
        source = mutate("M220 146 H420", "M240 146 H420")
        self.assertWarns(source, "edge 'api-reads-db' start (240, 146) is 20 units short of")

    def test_end_endpoint_short_of_node(self):
        source = mutate("M220 146 H420", "M220 146 H400")
        self.assertWarns(source, "end (400, 146) is 20 units short of the bounding-box edge of 'db'")

    def test_endpoint_inside_node(self):
        source = mutate("M220 146 H420", "M220 146 H450")
        self.assertWarns(source, "end (450, 146) is 30 units inside")

    def test_endpoint_within_tolerance_is_accepted(self):
        self.assertClean(mutate("M220 146 H420", "M215 146 H425"))

    def test_endpoint_off_edge_vertically_is_short(self):
        source = mutate("M220 146 H420", "M220 80 H420")
        self.assertWarns(source, "start (220, 80) is 30 units short of")

    def test_connector_passes_through_unrelated_node(self):
        fragment = (
            '    <g data-node="cache" data-parent="platform">'
            '<rect x="290" y="120" width="40" height="52"/><text x="292" y="150">C</text></g>'
        )
        self.assertWarns(add_to_layer("nodes", fragment), "edge 'api-reads-db' passes through node 'cache'")

    def test_connector_touching_unrelated_node_edge_is_accepted(self):
        fragment = (
            '    <g data-node="cache" data-parent="platform">'
            '<rect x="230" y="146" width="40" height="52"/><text x="232" y="170">C</text></g>'
        )
        self.assertClean(add_to_layer("nodes", fragment))

    def test_connector_crossing_boundary_is_accepted(self):
        fragment = '<g data-boundary="zone" data-parent="platform"><rect x="260" y="100" width="100" height="90"/></g>'
        self.assertClean(add_to_layer("boundaries", fragment))

    def test_diagonal_segment_through_node_is_detected(self):
        fragment = (
            '    <g data-node="cache" data-parent="platform">'
            '<rect x="290" y="150" width="40" height="40"/><text x="292" y="170">C</text></g>'
        )
        source = mutate("M220 146 H420", "M220 146 L420 190")
        errors, warnings, _ = check(add_to_layer("nodes", fragment, source))
        self.assertHas(warnings, "passes through node 'cache'")

    def test_two_connectors_share_start_point_on_node(self):
        fragment = (
            '    <g data-edge="second" data-from="api" data-to="db">'
            '<path d="M220 150 H420"/></g>'
        )
        warnings = self.assertWarns(
            add_to_layer("edges", fragment),
            "edges 'api-reads-db' (start) and 'second' (start) attach at the same point",
        )
        self.assertHas(warnings, "(end) and 'second' (end)")

    def test_connectors_on_different_points_are_accepted(self):
        fragment = (
            '    <g data-edge="second" data-from="api" data-to="db">'
            '<path d="M220 170 H420"/></g>'
        )
        self.assertClean(add_to_layer("edges", fragment))

    def test_label_mask_overlaps_node(self):
        source = mutate('x="280" y="134" width="80"', 'x="200" y="134" width="80"')
        self.assertWarns(source, "label mask for edge 'api-reads-db' overlaps node 'api'")

    def test_label_mask_touching_node_is_accepted(self):
        self.assertClean(mutate('x="280" y="134" width="80"', 'x="220" y="134" width="80"'))

    def test_label_masks_overlap_each_other(self):
        second = (
            '    <g data-label-for="api-reads-db">'
            '<rect x="300" y="140" width="60" height="20"/><text x="310" y="155">r</text></g>'
        )
        self.assertWarns(add_to_layer("labels", second), "label masks for edges 'api-reads-db' and 'api-reads-db' overlap")

    def test_text_overflow_estimate(self):
        source = mutate(">API service<", ">API service with a very long descriptive name<")
        self.assertWarns(source, "text 'API service with a very long descript...' in node 'api' is estimated at 432 units")

    def test_text_overflow_uses_class_font_shorthand(self):
        # 11 characters * 0.6 * 30 = 198 > 160.
        source = mutate(".title { font: 600 16px", ".title { font: 600 30px")
        self.assertWarns(source, "text 'API service' in node 'api' is estimated at 198 units")

    def test_text_overflow_uses_class_font_size_rule(self):
        source = mutate("</style>", ".title { font-size: 30px; }\n  </style>")
        self.assertWarns(source, "(font-size 30)")

    def test_text_overflow_ignores_media_query_overrides(self):
        source = mutate(
            "</style>",
            "@media (prefers-color-scheme: dark) { .title { font-size: 40px; } }\n  </style>",
        )
        self.assertClean(source)

    def test_text_overflow_uses_attribute_font_size(self):
        source = mutate('<text class="title" x="80" y="42"', '<text x="80" y="42" font-size="40"')
        self.assertWarns(source, "text 'API service' in node 'api'")

    def test_text_overflow_uses_inline_style_font_size(self):
        source = mutate('<text class="title" x="80" y="42"', '<text x="80" y="42" style="font-size: 40px"')
        self.assertWarns(source, "text 'API service' in node 'api'")

    def test_text_overflow_defaults_to_16_without_font_size(self):
        # 20 characters * 0.6 * 16 = 192 > 160, and no font-size is declared.
        source = mutate('<text class="title" x="80" y="42"', '<text x="80" y="42"')
        source = mutate(">API service<", ">" + "A" * 20 + "<", source)
        self.assertWarns(source, "(font-size 16)")

    def test_text_that_fits_is_accepted(self):
        # 16 characters * 0.6 * 16 = 153.6 < 160.
        self.assertClean(mutate(">API service<", ">" + "A" * 16 + "<"))

    def test_tspan_with_x_is_a_separate_line(self):
        long_text = "A" * 12
        text = (
            '<text class="title" x="80" y="30" text-anchor="middle">'
            f'<tspan x="80" dy="0">{long_text}</tspan>'
            f'<tspan x="80" dy="18">{long_text}</tspan></text>'
        )
        source = mutate('<text class="title" x="80" y="42" text-anchor="middle">API service</text>', text)
        # Two 12-character lines (115 units each) fit; one 24-character line would not.
        self.assertClean(source)
        joined = text.replace('</tspan><tspan x="80" dy="18">', "")
        self.assertWarns(mutate(text, joined, source), "text '" + "A" * 24)

    def test_tspan_without_x_continues_the_line(self):
        text = (
            '<text class="title" x="80" y="30"><tspan x="80">' + "A" * 12 +
            '</tspan><tspan dy="0">' + "B" * 12 + "</tspan></text>"
        )
        source = mutate('<text class="title" x="80" y="42" text-anchor="middle">API service</text>', text)
        self.assertWarns(source, "text '" + "A" * 12 + "B" * 12)

    def test_boundary_heading_is_not_checked_for_overflow(self):
        self.assertClean(mutate(">Platform<", ">" + "Platform " * 30 + "<"))


class StrictGeometryTests(SvgTestCase):
    def test_strict_promotes_warnings_to_errors(self):
        source = mutate("M220 146 H420", "M240 146 H420")
        errors, warnings, _ = check(source, strict_geometry=True)
        self.assertEqual(warnings, [])
        self.assertHas(errors, "geometry (strict):")
        self.assertHas(errors, "20 units short of")

    def test_strict_leaves_valid_sample_clean(self):
        self.assertClean(VALID, strict_geometry=True)

    def test_cli_strict_flag_changes_exit_code(self):
        source = mutate("M220 146 H420", "M240 146 H420")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "short.svg"
            path.write_text(source, encoding="utf-8")
            default_code, default_out, default_err = run_cli(str(path))
            strict_code, strict_out, strict_err = run_cli("--strict-geometry", str(path))
        self.assertEqual(default_code, 0)
        self.assertIn("WARN: edge 'api-reads-db' start", default_out)
        self.assertIn(f"PASS: {path}", default_out)
        self.assertEqual(default_err, "")
        self.assertEqual(strict_code, 1)
        self.assertNotIn("WARN", strict_out)
        self.assertIn("FAIL: 1 issue(s)", strict_err)

    def test_strict_turns_skipped_geometry_into_errors(self):
        source = mutate('transform="translate(60 110)"', 'transform="rotate(10)"')
        errors, warnings, notes = check(source, strict_geometry=True)
        self.assertEqual((warnings, notes), ([], []))
        self.assertHas(errors, "geometry (strict): geometry skipped for node 'api'")
        self.assertHas(errors, "rotate()")
        # Without the flag the same file only produces a note.
        errors, _, notes = check(source)
        self.assertEqual(errors, [])
        self.assertHas(notes, "rotate()")

    def test_strict_fails_for_scale_matrix_and_relative_units(self):
        cases = {
            "scale": mutate('transform="translate(60 110)"', 'transform="scale(2)"'),
            "matrix": mutate('transform="translate(60 110)"', 'transform="matrix(1 0 0 1 5 5)"'),
            "em": mutate('<rect class="node" x="420" y="110" width="160"',
                         '<rect class="node" x="420" y="110" width="10em"'),
            "percent": mutate('width="600" height="280"', 'width="50%" height="280"'),
        }
        for name, source in cases.items():
            with self.subTest(case=name):
                errors, _, _ = check(source, strict_geometry=True)
                self.assertHas(errors, "geometry (strict): geometry skipped")
                self.assertEqual(check(source)[0], [])

    def test_cli_strict_exit_code_for_skipped_geometry(self):
        source = mutate('transform="translate(60 110)"', 'transform="rotate(10)"')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rotated.svg"
            path.write_text(source, encoding="utf-8")
            default_code, default_out, _ = run_cli(str(path))
            strict_code, strict_out, strict_err = run_cli("--strict-geometry", str(path))
        self.assertEqual(default_code, 0)
        self.assertIn("NOTE: geometry skipped for node 'api'", default_out)
        self.assertEqual(strict_code, 1)
        self.assertNotIn("PASS", strict_out)
        self.assertIn("geometry (strict): geometry skipped for node 'api'", strict_err)


class TransformTests(SvgTestCase):
    def test_translate_on_group_is_honored(self):
        # The "api" rect is at (0,0) locally; translate places it at (60,110).
        # Without honoring it the connector would be reported far from the node.
        self.assertClean(VALID)

    def test_translate_shifts_the_node_for_endpoint_checks(self):
        source = mutate("translate(60 110)", "translate(100 110)")
        self.assertWarns(source, "edge 'api-reads-db' start (220, 146) is 36 units inside")

    def test_translate_with_single_argument(self):
        source = mutate("translate(60 110)", "translate(60)")
        self.assertWarns(source, "start (220, 146) is 74 units short")

    def test_translate_with_comma_and_multiple_functions(self):
        source = mutate("translate(60 110)", "translate(20,10) translate(40, 100)")
        self.assertClean(source)

    def test_translate_on_shape_itself(self):
        source = mutate(
            'transform="translate(60 110)"', ""
        )
        source = mutate('<rect class="node" width="160"', '<rect class="node" transform="translate(60 110)" width="160"', source)
        self.assertClean(source)

    def test_translate_on_nested_ancestors_accumulates(self):
        source = mutate('transform="translate(60 110)"', 'transform="translate(50 100)"')
        source = mutate(
            '<rect class="node" width="160"', '<rect class="node" transform="translate(10 10)" width="160"', source
        )
        self.assertClean(source)

    def test_translate_on_layer_group_is_honored(self):
        source = mutate('<g data-layer="nodes">', '<g data-layer="nodes" transform="translate(30 0)">')
        self.assertWarns(source, "edge 'api-reads-db' start (220, 146) is 30 units inside")

    def test_unsupported_transform_on_node_emits_note_not_warning(self):
        source = mutate('transform="translate(60 110)"', 'transform="rotate(45)"')
        errors, warnings, notes = check(source)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertEqual(notes, ["geometry skipped for node 'api': unsupported transform rotate()"])

    def test_unsupported_transform_on_ancestor_layer(self):
        source = mutate('<g data-layer="nodes">', '<g data-layer="nodes" transform="scale(2)">')
        errors, warnings, notes = check(source)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertHas(notes, "node 'api': unsupported transform scale()")
        self.assertHas(notes, "node 'db': unsupported transform scale()")

    def test_matrix_and_skew_are_unsupported(self):
        for transform in ("matrix(1 0 0 1 5 5)", "skewX(10)", "translate(5 5) rotate(3)"):
            with self.subTest(transform=transform):
                source = mutate('transform="translate(60 110)"', f'transform="{transform}"')
                errors, warnings, notes = check(source)
                self.assertEqual((errors, warnings), ([], []))
                self.assertHas(notes, "geometry skipped for node 'api'")

    def test_unsupported_transform_on_edge_skips_edge_checks(self):
        source = mutate('<path class="edge" d="M220 146 H420"', '<path class="edge" transform="rotate(30)" d="M0 0 H5000"')
        errors, warnings, notes = check(source)
        self.assertEqual((errors, warnings), ([], []))
        self.assertHas(notes, "geometry skipped for edge 'api-reads-db'")

    def test_unsupported_transform_on_label_mask(self):
        source = mutate('<rect class="mask" x="280"', '<rect class="mask" transform="scale(3)" x="280"')
        errors, warnings, notes = check(source)
        self.assertEqual((errors, warnings), ([], []))
        self.assertHas(notes, "geometry skipped for label of edge 'api-reads-db'")

    def test_css_transform_is_unsupported(self):
        source = mutate('transform="translate(60 110)"', 'style="transform: rotate(5deg)"')
        _, warnings, notes = check(source)
        self.assertEqual(warnings, [])
        self.assertHas(notes, "unsupported CSS transform")

    def test_skipped_node_is_not_an_obstacle(self):
        fragment = (
            '    <g data-node="cache" data-parent="platform" transform="rotate(10)">'
            '<rect x="290" y="120" width="40" height="52"/><text x="292" y="150">C</text></g>'
        )
        errors, warnings, notes = check(add_to_layer("nodes", fragment))
        self.assertEqual((errors, warnings), ([], []))
        self.assertHas(notes, "node 'cache'")

    def test_notes_are_not_repeated(self):
        source = mutate('<g data-layer="nodes">', '<g data-layer="nodes" transform="scale(2)">')
        _, _, notes = check(source)
        self.assertEqual(len(notes), len(set(notes)))


class PathParsingTests(SvgTestCase):
    def check_path(self, data: str, fragment: str | None = None, **kwargs):
        source = mutate("M220 146 H420", data)
        if fragment is None:
            self.assertClean(source, **kwargs)
        else:
            self.assertWarns(source, fragment)

    def test_relative_commands(self):
        self.check_path("m220 146 h200")
        self.check_path("m 220,146 l 200,0")
        self.check_path("M220 146 h100 h100")

    def test_relative_vertical_and_horizontal_route(self):
        # Leaves the api node at its right edge, drops 24, runs right, rises 24 to the db edge.
        self.check_path("M220 146 h40 v24 h120 v-24 h40")

    def test_relative_endpoint_short_is_computed_from_current_point(self):
        self.check_path("m220 146 h180", "end (400, 146) is 20 units short")

    def test_absolute_h_and_v(self):
        self.check_path("M220 146 H320 V170 H420 V146")

    def test_implicit_lineto_after_moveto(self):
        self.check_path("M220 146 420 146")
        self.check_path("m220 146 100 0 100 0")

    def test_close_path(self):
        self.check_path("M220 146 H320 V160 Z", "end (220, 146)")

    def test_relative_close_path_returns_to_subpath_start(self):
        self.check_path("M220 146 h100 v10 z", "end (220, 146)")

    def test_quadratic_and_smooth_quadratic_use_chord(self):
        self.check_path("M220 146 Q320 146 420 146")
        self.check_path("M220 146 q50 0 100 0 t100 0")

    def test_cubic_and_smooth_cubic_use_chord(self):
        self.check_path("M220 146 C260 146 380 146 420 146")
        self.check_path("M220 146 c20 0 40 0 100 0 s60 0 100 0")

    def test_arc_uses_chord(self):
        self.check_path("M220 146 A100 20 0 0 1 420 146")
        self.check_path("M220 146 a100 20 0 0 1 200 0")

    def test_arc_with_compact_flags(self):
        self.check_path("M220 146 a100 20 0 01200 0")

    def test_rounded_corner_route(self):
        self.check_path("M220 146 H300 Q320 146 320 166 V190 Q320 210 340 210 H420", "end (420, 210)")

    def test_numbers_without_separators(self):
        self.check_path("M220,146h100-0h100")
        self.check_path("M220 146h100.5-.5h99.5.5")

    def test_exponent_numbers(self):
        self.check_path("M2.2e2 1.46e2 H4.2e2")

    def test_line_and_polyline_connectors(self):
        source = mutate('<path class="edge" d="M220 146 H420"', '<line class="edge" x1="220" y1="146" x2="420" y2="146"')
        self.assertClean(source)
        source = mutate(
            '<path class="edge" d="M220 146 H420"', '<polyline class="edge" points="220,146 320,146 420,146"'
        )
        self.assertClean(source)
        self.assertWarns(
            mutate('<path class="edge" d="M220 146 H420"', '<polyline class="edge" points="220,146 320,146 400,146"'),
            "end (400, 146)",
        )

    def test_malformed_path_data_is_a_note(self):
        source = mutate("M220 146 H420", "M220 146 H")
        errors, warnings, notes = check(source)
        self.assertEqual((errors, warnings), ([], []))
        self.assertHas(notes, "geometry skipped for edge 'api-reads-db'")

    def test_unknown_path_command_is_a_note(self):
        _, _, notes = check(mutate("M220 146 H420", "M220 146 X420"))
        self.assertHas(notes, "unknown path command")

    def test_path_without_moveto_is_a_note(self):
        _, _, notes = check(mutate("M220 146 H420", "H420"))
        self.assertHas(notes, "must start with a moveto")

    def test_non_numeric_coordinate_is_a_note(self):
        _, _, notes = check(mutate('width="600" height="280"', 'width="50%" height="280"'))
        self.assertHas(notes, "geometry skipped for boundary 'platform'")

    def test_node_shapes_other_than_rect(self):
        for shape in (
            '<circle cx="80" cy="36" r="36"/>',
            '<ellipse cx="80" cy="36" rx="80" ry="36"/>',
            '<polygon points="0,36 80,0 160,36 80,72"/>',
            '<path d="M0 0 H160 V72 H0 Z"/>',
        ):
            with self.subTest(shape=shape):
                source = mutate('<rect class="node" width="160" height="72" rx="8"/>', shape)
                errors, _, notes = check(source)
                self.assertEqual(errors, [])
                self.assertEqual(notes, [])


NODE_B_TEXT = '<text class="title" x="500" y="152" text-anchor="middle">Orders DB</text>'


class InertnessTests(SvgTestCase):
    def test_animation_elements_are_errors(self):
        for tag in ("animate", "set", "animateMotion", "animateTransform", "animateColor", "discard"):
            with self.subTest(tag=tag):
                source = mutate(
                    'marker-end="url(#sample-arrow)"/>', f'marker-end="url(#sample-arrow)"><{tag}/></path>'
                )
                self.assertErrors(source, f"<{tag}> is not allowed")

    def test_set_javascript_href_is_rejected(self):
        source = add_to_layer(
            "labels",
            '<a href="#sample-title"><set attributeName="href" to="javascript:alert(1)"/></a>',
        )
        self.assertErrors(source, "<set> is not allowed")

    def test_animation_outside_layers_is_rejected(self):
        self.assertErrors(
            mutate("<defs>", '<animate attributeName="x"/><defs>'), "<animate> is not allowed"
        )

    def test_css_escape_in_style_element(self):
        source = mutate("<style>", '<style>@\\69mport "https://evil.example/x.css";')
        self.assertErrors(source, "CSS escapes")

    def test_css_escape_in_style_attribute(self):
        source = mutate('<text class="title" x="80"', '<text style="fill:\\72ed" x="80"')
        self.assertErrors(source, "CSS escapes")

    def test_plain_style_attribute_is_accepted(self):
        self.assertClean(mutate('<text class="title" x="80"', '<text style="fill: red" x="80"'))

    def test_nested_svg_in_layer(self):
        source = mutate(
            NODE_B_TEXT, NODE_B_TEXT + '<svg x="1000"><rect width="5" height="5"/></svg>'
        )
        self.assertErrors(source, "<svg> is not allowed inside data-layer 'nodes'")

    def test_nested_svg_wrapping_a_node(self):
        source = add_to_layer(
            "nodes",
            '<svg x="1000"><g data-node="far"><rect width="9" height="9"/><text>F</text></g></svg>',
        )
        self.assertErrors(source, "<svg> is not allowed inside data-layer 'nodes'")

    def test_use_in_every_layer(self):
        for layer in ("boundaries", "edges", "nodes", "labels"):
            with self.subTest(layer=layer):
                source = add_to_layer(layer, '<use href="#sample-arrow"/>')
                self.assertErrors(source, f"<use> is not allowed inside data-layer '{layer}'")

    def test_use_outside_layers_is_not_a_layer_error(self):
        source = mutate("<defs>", '<use href="#sample-arrow"/><defs>')
        errors, _, _ = check(source)
        self.assertEqual(errors, [])


class DoctypeAndSizeTests(SvgTestCase):
    PUBLIC = (
        '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" '
        '"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n'
    )

    def test_public_doctype_without_subset_is_accepted(self):
        self.assertClean(self.PUBLIC + VALID)

    def test_bare_doctype_is_accepted(self):
        self.assertClean("<!DOCTYPE svg>\n" + VALID)

    def test_doctype_naming_another_dtd_is_an_error(self):
        source = '<!DOCTYPE svg SYSTEM "http://evil.example/x.dtd">\n' + VALID
        self.assertErrors(source, "DOCTYPE may only name the public SVG DTD")

    def test_internal_subset_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "internal subset"):
            check('<!DOCTYPE svg [ ]>\n' + VALID)

    def test_entity_declaration_is_rejected(self):
        source = '<!DOCTYPE svg [<!ENTITY a "x">]>\n' + mutate("Service reads orders", "&a;")
        with self.assertRaisesRegex(ValueError, "internal subset|ENTITY"):
            check(source)

    def test_cli_exit_2_for_entity_expansion_bomb(self):
        entities = '<!ENTITY a0 "aaaaaaaaaa">' + "".join(
            f'<!ENTITY a{i} "' + f"&a{i - 1};" * 10 + '">' for i in range(1, 9)
        )
        source = f"<!DOCTYPE svg [{entities}]>\n" + mutate("Service reads orders", "&a8;")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bomb.svg"
            path.write_text(source, encoding="utf-8")
            code, out, err = run_cli(str(path))
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("internal subset", err)

    def test_cli_exit_2_for_external_entity(self):
        source = '<!DOCTYPE svg [<!ENTITY x SYSTEM "file:///etc/passwd">]>\n' + VALID
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ext.svg"
            path.write_text(source, encoding="utf-8")
            code, _, err = run_cli(str(path))
        self.assertEqual(code, 2)
        self.assertIn("ERROR: cannot parse", err)

    def test_cli_exit_2_for_oversized_input(self):
        import check_svg

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "big.svg"
            path.write_text(VALID + " " * 200, encoding="utf-8")
            original = check_svg.MAX_INPUT_BYTES
            check_svg.MAX_INPUT_BYTES = len(VALID)
            try:
                code, out, err = run_cli(str(path))
            finally:
                check_svg.MAX_INPUT_BYTES = original
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("larger than", err)

    def test_validate_svg_rejects_oversized_input(self):
        import check_svg

        original = check_svg.MAX_INPUT_BYTES
        check_svg.MAX_INPUT_BYTES = 10
        try:
            with self.assertRaisesRegex(ValueError, "larger than"):
                check(VALID)
        finally:
            check_svg.MAX_INPUT_BYTES = original

    def test_size_limit_constant_is_20_mb(self):
        import check_svg

        self.assertEqual(check_svg.MAX_INPUT_BYTES, 20 * 1024 * 1024)


class ContractCompletenessTests(SvgTestCase):
    def test_label_without_rect_and_text(self):
        source = mutate(
            '<rect class="mask" x="280" y="134" width="80" height="24"/>'
            '\n      <text class="label" x="320" y="151" text-anchor="middle">reads</text>',
            "",
        )
        errors = self.assertErrors(source, "label for 'api-reads-db' must contain an opaque mask <rect>")
        self.assertHas(errors, "label for 'api-reads-db' must contain a <text>")

    def test_label_without_text(self):
        source = mutate(
            '\n      <text class="label" x="320" y="151" text-anchor="middle">reads</text>', ""
        )
        errors = self.assertErrors(source, "must contain a <text> with visible text")
        self.assertEqual(sum("opaque mask" in error for error in errors), 0)

    def test_label_without_mask_rect(self):
        source = mutate('<rect class="mask" x="280" y="134" width="80" height="24"/>', "")
        self.assertErrors(source, "must contain an opaque mask <rect>")

    def test_label_with_blank_text(self):
        self.assertErrors(mutate(">reads<", ">  <"), "must contain a <text> with visible text")

    def test_node_without_text(self):
        self.assertErrors(
            mutate('<text class="title" x="80" y="42" text-anchor="middle">API service</text>', ""),
            "node 'api' must contain a <text> with visible text",
        )

    def test_node_with_blank_text(self):
        self.assertErrors(mutate(">API service<", ">  <"), "node 'api' must contain a <text>")

    def test_node_text_may_be_in_tspan_and_wrapped_group(self):
        source = mutate(
            '<text class="title" x="80" y="42" text-anchor="middle">API service</text>',
            '<g><text class="title" x="80" y="42"><tspan x="80">API service</tspan></text></g>',
        )
        self.assertClean(source)

    def test_marker_start_only_attribute(self):
        source = mutate('marker-end="url(#sample-arrow)"', 'marker-start="url(#sample-arrow)"')
        self.assertErrors(source, "edge 'api-reads-db' has marker-start but no marker-end")

    def test_marker_start_only_message_suggests_swap(self):
        source = mutate('marker-end="url(#sample-arrow)"', 'marker-start="url(#sample-arrow)"')
        errors = self.assertErrors(source, "swap data-from and data-to")
        self.assertHas(errors, "arrowhead must sit at data-to")

    def test_marker_start_only_inline_style(self):
        source = mutate(
            'marker-end="url(#sample-arrow)"', 'style="marker-start: url(#sample-arrow)"'
        )
        self.assertErrors(source, "has marker-start but no marker-end")

    def test_marker_start_only_from_class_rule(self):
        source = mutate("</style>", ".rev { marker-start: url(#sample-arrow); }\n  </style>")
        source = mutate('class="edge" d="M220 146 H420" marker-end="url(#sample-arrow)"',
                        'class="edge rev" d="M220 146 H420"', source)
        self.assertErrors(source, "has marker-start but no marker-end")

    def test_marker_end_from_class_rule_is_accepted(self):
        source = mutate("</style>", ".head { marker-end: url(#sample-arrow); }\n  </style>")
        source = mutate('class="edge" d="M220 146 H420" marker-end="url(#sample-arrow)"',
                        'class="edge head" d="M220 146 H420"', source)
        self.assertClean(source)

    def test_marker_shorthand_in_class_rule_sets_both_ends(self):
        source = mutate("</style>", ".both { marker: url(#sample-arrow); }\n  </style>")
        source = mutate('class="edge" d="M220 146 H420" marker-end="url(#sample-arrow)"',
                        'class="edge both" d="M220 146 H420" marker-start="url(#sample-arrow)"', source)
        self.assertClean(source)

    def test_marker_end_none_in_style_does_not_count(self):
        source = mutate(
            'marker-end="url(#sample-arrow)"',
            'marker-start="url(#sample-arrow)" style="marker-end: none"',
        )
        self.assertErrors(source, "has marker-start but no marker-end")

    def test_inline_style_overrides_attribute_marker_end(self):
        source = mutate(
            'marker-end="url(#sample-arrow)"',
            'marker-start="url(#sample-arrow)" marker-end="url(#sample-arrow)" '
            'style="marker-end: none"',
        )
        self.assertErrors(source, "has marker-start but no marker-end")

    def test_marker_inherited_from_edge_group(self):
        source = mutate('data-from="api" data-to="db">', 'data-from="api" data-to="db" marker-end="url(#sample-arrow)">')
        source = mutate(
            'marker-end="url(#sample-arrow)"/>', 'marker-start="url(#sample-arrow)"/>', source
        )
        self.assertClean(source)

    def test_two_way_connector_is_accepted(self):
        self.assertClean(mutate('marker-end="url(#sample-arrow)"',
                                'marker-start="url(#sample-arrow)" marker-end="url(#sample-arrow)"'))

    def test_undirected_connector_is_accepted(self):
        self.assertClean(mutate(' marker-end="url(#sample-arrow)"', ""))

    def test_media_query_marker_rules_are_ignored(self):
        source = mutate(
            "</style>",
            "@media (prefers-color-scheme: dark) { .edge { marker-start: url(#sample-arrow); } }\n  </style>",
        )
        self.assertClean(source)


class EllipseAndArcGeometryTests(SvgTestCase):
    CIRCLE_NODE = '<rect class="node" width="160" height="72" rx="8"/>'

    def ellipse_source(self, shape: str, path: str) -> str:
        source = mutate(self.CIRCLE_NODE, shape)
        return mutate("M220 146 H420", path, source)

    def test_point_on_circle_at_45_degrees_is_accepted(self):
        # Circle centred (140, 146) with r=80 inside the translate(60 110) group:
        # local centre (80, 36). A 45 degree point is (140 + 56.5685, 146 - 56.5685).
        source = self.ellipse_source('<circle cx="80" cy="36" r="80"/>', "M196.5685 89.4315 L420 146")
        errors, warnings, _ = check(mutate("viewBox=\"0 0 640 320\"", "viewBox=\"0 -50 640 400\"", source))
        self.assertEqual(errors, [])
        self.assertFalse([w for w in warnings if "edge 'api-reads-db' start" in w], warnings)

    def test_point_inside_circle_is_reported_against_the_outline(self):
        source = self.ellipse_source('<circle cx="80" cy="36" r="36"/>', "M140 146 H420")
        self.assertWarns(source, "start (140, 146) is 36 units inside the outline of 'api'")

    def test_point_short_of_circle_is_reported_against_the_outline(self):
        # Circle r=36 centred (140, 146): the right edge is x=176; the start is 24 units short.
        source = self.ellipse_source('<circle cx="80" cy="36" r="36"/>', "M200 146 H420")
        self.assertWarns(source, "start (200, 146) is 24 units short of the outline of 'api'")

    def test_diagonal_point_off_circle_is_short_by_radial_distance(self):
        # (140+60, 146-60) is 84.85 from the centre of an r=36 circle: 48.85 short.
        source = self.ellipse_source('<circle cx="80" cy="36" r="36"/>', "M200 86 H420")
        warnings = self.assertWarns(source, "short of the outline of 'api'")
        self.assertHas(warnings, "48.9 units")

    def test_ellipse_endpoint_on_outline_is_accepted(self):
        # Ellipse centre (140,146), rx=80, ry=36; point at t=45deg.
        x = 140 + 80 * 0.70710678
        y = 146 - 36 * 0.70710678
        source = self.ellipse_source(
            '<ellipse cx="80" cy="36" rx="80" ry="36"/>', f"M{x:.4f} {y:.4f} L420 146"
        )
        _, warnings, _ = check(source)
        self.assertFalse([w for w in warnings if "start" in w and "edge 'api-reads-db'" in w], warnings)

    def test_ellipse_endpoint_distance_is_measured_to_the_outline(self):
        # On the horizontal axis the bbox and the outline agree.
        source = self.ellipse_source('<ellipse cx="80" cy="36" rx="80" ry="36"/>', "M240 146 H420")
        self.assertWarns(source, "start (240, 146) is 20 units short of the outline of 'api'")

    def test_ellipse_near_corner_of_bbox_is_not_on_the_outline(self):
        # The bbox corner (60, 110) is far from the ellipse outline.
        source = self.ellipse_source('<ellipse cx="80" cy="36" rx="80" ry="36"/>', "M60 110 H420")
        self.assertWarns(source, "short of the outline of 'api'")

    def test_translated_circle_uses_absolute_center(self):
        source = self.ellipse_source('<circle cx="80" cy="36" r="36"/>', "M176 146 H420")
        self.assertClean(mutate(">API service<", ">API<", source))

    def test_arc_only_path_node_has_real_bounding_box(self):
        circle_path = '<path d="M10 80 A40 40 0 0 1 90 80 A40 40 0 0 1 10 80 Z"/>'
        source = mutate(self.CIRCLE_NODE, circle_path)
        source = mutate("translate(60 110)", "translate(0 0)", source)
        # Circle: centre (50,80), r=40 -> bbox (10,40)-(90,120). Start the connector on the left of it.
        source = mutate("M220 146 H420", "M90 80 L420 146", source)
        self.assertClean(mutate(">API service<", ">API<", source))
        # The old chord-only box (zero height at y=80) would have put the start inside it.
        short = mutate("M90 80 L420 146", "M80 80 L420 146", source)
        self.assertWarns(mutate(">API service<", ">API<", short), "start (80, 80) is 10 units inside")

    def test_arc_only_path_bbox_via_import(self):
        from check_svg import _shape_box

        path = ET.fromstring(
            '<path xmlns="http://www.w3.org/2000/svg" '
            'd="M10 80 A40 40 0 0 1 90 80 A40 40 0 0 1 10 80 Z"/>'
        )
        box = _shape_box(path)
        for actual, expected in zip(box, (10, 40, 90, 120)):
            self.assertAlmostEqual(actual, expected, places=6)

    def test_arc_bbox_respects_sweep_and_large_arc_flags(self):
        from check_svg import _shape_box

        def box_of(data: str):
            return _shape_box(ET.fromstring(f'<path xmlns="http://www.w3.org/2000/svg" d="{data}"/>'))

        upper = box_of("M0 0 A50 50 0 0 1 100 0")
        lower = box_of("M0 0 A50 50 0 0 0 100 0")
        self.assertAlmostEqual(upper[1], -50, places=6)
        self.assertAlmostEqual(upper[3], 0, places=6)
        self.assertAlmostEqual(lower[1], 0, places=6)
        self.assertAlmostEqual(lower[3], 50, places=6)
        large = box_of("M0 0 A60 60 0 1 1 100 0")
        self.assertGreater(large[2], 100)
        self.assertLess(large[0], 0)

    def test_arc_radii_are_scaled_when_too_small(self):
        from check_svg import _shape_box

        box = _shape_box(
            ET.fromstring('<path xmlns="http://www.w3.org/2000/svg" d="M0 0 A1 1 0 0 1 100 0"/>')
        )
        self.assertAlmostEqual(box[1], -50, places=6)

    def test_rotated_ellipse_arc_extremes(self):
        from check_svg import _shape_box

        box = _shape_box(
            ET.fromstring(
                '<path xmlns="http://www.w3.org/2000/svg" '
                'd="M0 0 A50 20 90 1 1 0.001 0"/>'
            )
        )
        # A near-closed ellipse rotated 90 degrees is 40 wide and 100 tall.
        self.assertAlmostEqual(box[2] - box[0], 40, delta=0.1)
        self.assertAlmostEqual(box[3] - box[1], 100, delta=0.1)

    def test_degenerate_arcs_do_not_crash(self):
        from check_svg import _shape_box

        for data in ("M5 5 A0 10 0 0 1 20 20", "M5 5 A10 10 0 0 1 5 5", "M5 5 A10 0 0 1 1 20 20"):
            with self.subTest(data=data):
                _shape_box(ET.fromstring(f'<path xmlns="http://www.w3.org/2000/svg" d="{data}"/>'))


class StylesheetInstructionRegressionTests(SvgTestCase):
    def test_rejects_external_xml_stylesheet(self):
        source = '<?xml-stylesheet type="text/css" href="https://example.invalid/style.css"?>\n' + VALID
        self.assertErrors(source, "xml-stylesheet processing instructions are not allowed")


if __name__ == "__main__":
    unittest.main()
