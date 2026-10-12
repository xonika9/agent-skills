#!/usr/bin/env python3
"""Regression tests for check_scene.py."""

from __future__ import annotations

import copy
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from check_scene import (
    compare_normalization_stability,
    geometry_warnings,
    main,
    parse_args,
    validate_scene,
)


def common(element_id: str, element_type: str, x: int, y: int, width: int, height: int):
    return {
        "id": element_id,
        "type": element_type,
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "angle": 0,
        "strokeColor": "#1e1e1e",
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 2,
        "strokeStyle": "solid",
        "roundness": None,
        "roughness": 0,
        "opacity": 100,
        "seed": 1,
        "version": 1,
        "versionNonce": 1,
        "index": None,
        "isDeleted": False,
        "groupIds": [],
        "frameId": None,
        "boundElements": None,
        "updated": 1,
        "link": None,
        "locked": False,
    }


def scene() -> dict:
    left = common("left", "rectangle", 0, 0, 180, 80)
    left["boundElements"] = [
        {"id": "left-label", "type": "text"},
        {"id": "flow", "type": "arrow"},
    ]
    right = common("right", "rectangle", 360, 0, 180, 80)
    right["boundElements"] = [
        {"id": "right-label", "type": "text"},
        {"id": "flow", "type": "arrow"},
    ]

    left_label = common("left-label", "text", 25, 25, 130, 25)
    left_label.update(
        {
            "fontSize": 20,
            "fontFamily": 5,
            "text": "Client",
            "originalText": "Client",
            "textAlign": "center",
            "verticalAlign": "middle",
            "containerId": "left",
            "autoResize": True,
            "lineHeight": 1.25,
        }
    )
    right_label = common("right-label", "text", 385, 25, 130, 25)
    right_label.update(
        {
            "fontSize": 16,
            "fontFamily": 6,
            "text": "order-service",
            "originalText": "order-service",
            "textAlign": "center",
            "verticalAlign": "middle",
            "containerId": "right",
            "autoResize": True,
            "lineHeight": 1.25,
        }
    )

    arrow = common("flow", "arrow", 180, 40, 180, 0)
    arrow.update(
        {
            "points": [[0, 0], [180, 0]],
            "startBinding": {
                "elementId": "left",
                "fixedPoint": [1, 0.5],
                "mode": "orbit",
            },
            "endBinding": {
                "elementId": "right",
                "fixedPoint": [0, 0.5],
                "mode": "orbit",
            },
            "startArrowhead": None,
            "endArrowhead": "arrow",
            "elbowed": False,
        }
    )

    return {
        "type": "excalidraw",
        "version": 2,
        "source": "test",
        "elements": [left, left_label, right, right_label, arrow],
        "appState": {"viewBackgroundColor": "#ffffff"},
        "files": {},
    }


def label(element_id: str, container_id, x: int, y: int, width: int = 60, height: int = 25):
    element = common(element_id, "text", x, y, width, height)
    element.update(
        {
            "fontSize": 20,
            "fontFamily": 5,
            "text": "txt",
            "originalText": "txt",
            "textAlign": "center",
            "verticalAlign": "middle",
            "containerId": container_id,
            "autoResize": True,
            "lineHeight": 1.25,
        }
    )
    return element


def add_flow_label(candidate: dict, element_id: str, x: int, y: int) -> dict:
    text = label(element_id, "flow", x, y)
    flow = next(item for item in candidate["elements"] if item["id"] == "flow")
    flow["boundElements"] = (flow["boundElements"] or []) + [
        {"id": element_id, "type": "text"}
    ]
    candidate["elements"].append(text)
    return text


def run_cli(*arguments: str) -> tuple[int, str, str]:
    stdout, stderr = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = main(list(arguments))
    return code, stdout.getvalue(), stderr.getvalue()


class ValidateSceneTests(unittest.TestCase):
    def test_valid_current_scene(self):
        errors, notes = validate_scene(
            scene(),
            viewport_width=1600,
            required_fonts={5, 6},
        )
        self.assertEqual(errors, [])
        self.assertTrue(any("font families used: 5, 6" in note for note in notes))

    def test_accepts_current_virgil_for_existing_scenes(self):
        candidate = scene()
        candidate["elements"][1]["fontFamily"] = 1
        errors, _ = validate_scene(candidate)
        self.assertEqual(errors, [])

    def test_list_valued_identifiers_are_errors_not_crashes(self):
        candidate = scene()
        candidate["elements"][1]["containerId"] = ["left"]
        candidate["elements"][-1]["startBinding"]["elementId"] = ["left"]
        candidate["elements"][-1]["endBinding"]["elementId"] = {"id": "right"}
        candidate["elements"][0]["boundElements"] = [{"id": ["x"], "type": "text"}]
        errors, _ = validate_scene(candidate)
        self.assertTrue(any("containerId does not resolve" in e for e in errors), errors)
        self.assertTrue(
            any("Binding.elementId does not resolve" in e for e in errors), errors
        )
        self.assertTrue(
            any("boundElements reference does not resolve" in e for e in errors), errors
        )
        warnings, _ = geometry_warnings(candidate)  # must not raise
        self.assertIsInstance(warnings, list)

    def test_rejects_reserved_font_slot(self):
        candidate = scene()
        candidate["elements"][1]["fontFamily"] = 4
        errors, _ = validate_scene(candidate)
        self.assertTrue(any("not a current serialized family" in error for error in errors))

    def test_rejects_unknown_element_type(self):
        candidate = scene()
        candidate["elements"][0]["type"] = "definitely-not-an-excalidraw-type"
        errors, _ = validate_scene(candidate)
        self.assertTrue(any("supported basic subset" in error for error in errors))

    def test_rejects_invalid_common_scalar_types(self):
        invalid_fields = {
            "strokeColor": 42,
            "backgroundColor": False,
            "isDeleted": "false",
            "locked": "false",
            "frameId": 42,
            "link": 42,
        }
        for field, invalid_value in invalid_fields.items():
            with self.subTest(field=field):
                candidate = scene()
                candidate["elements"][0][field] = invalid_value
                errors, _ = validate_scene(candidate)
                self.assertTrue(
                    any(f"left.{field} must be" in error for error in errors),
                    errors,
                )

    def test_rejects_nonfinite_or_invalid_cli_numeric_bounds(self):
        cases = (
            ("--normalization-tolerance", "inf"),
            ("--normalization-tolerance", "nan"),
            ("--normalization-tolerance", "-1"),
            ("--viewport-width", "inf"),
            ("--viewport-width", "0"),
            ("--viewport-height", "nan", "--viewport-width", "1600"),
            ("--viewport-height", "0", "--viewport-width", "1600"),
            ("--minimum-effective-font", "inf"),
            ("--minimum-effective-font", "0"),
        )
        for arguments in cases:
            with self.subTest(arguments=arguments):
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit):
                        parse_args(["scene.excalidraw", *arguments])

    def test_rejects_bound_element_type_mismatch(self):
        candidate = scene()
        candidate["elements"][0]["boundElements"].append(
            {"id": "right", "type": "text"}
        )
        errors, _ = validate_scene(candidate)
        self.assertTrue(any("target type is 'rectangle'" in error for error in errors))

    def test_rejects_legacy_binding(self):
        candidate = scene()
        candidate["elements"][-1]["startBinding"] = {
            "elementId": "left",
            "focus": 0,
            "gap": 4,
        }
        errors, _ = validate_scene(candidate)
        self.assertTrue(any("fixedPoint" in error for error in errors))
        self.assertTrue(any(".mode" in error for error in errors))

    def test_rejects_one_way_binding(self):
        candidate = scene()
        candidate["elements"][0]["boundElements"] = [
            {"id": "left-label", "type": "text"}
        ]
        errors, _ = validate_scene(candidate)
        self.assertTrue(any("not reciprocal" in error for error in errors))

    def test_rejects_active_arrow_bound_to_deleted_element(self):
        candidate = scene()
        candidate["elements"][0]["isDeleted"] = True
        errors, _ = validate_scene(candidate)
        self.assertTrue(
            any(
                "startBinding.elementId does not resolve to an active element"
                in error
                for error in errors
            )
        )

    def test_rejects_active_text_bound_to_deleted_container(self):
        candidate = scene()
        candidate["elements"][0]["isDeleted"] = True
        candidate["elements"][-1]["startBinding"] = None
        errors, _ = validate_scene(candidate)
        self.assertTrue(
            any(
                "containerId does not resolve to an active element" in error
                for error in errors
            )
        )

    def test_rejects_too_small_fit_view(self):
        candidate = copy.deepcopy(scene())
        candidate["elements"].append(
            common("far-away", "rectangle", 5000, 0, 180, 80)
        )
        errors, _ = validate_scene(
            candidate,
            viewport_width=1600,
            minimum_effective_font=12,
        )
        self.assertTrue(any("fit-to-width" in error for error in errors))

    def test_rejects_too_tall_fit_view(self):
        candidate = copy.deepcopy(scene())
        candidate["elements"].append(
            common("far-below", "rectangle", 0, 5000, 180, 80)
        )
        errors, _ = validate_scene(
            candidate,
            viewport_width=1600,
            viewport_height=900,
            minimum_effective_font=12,
        )
        self.assertTrue(any("1600×900" in error for error in errors))

    def test_accepts_tall_scene_when_only_width_is_requested(self):
        candidate = copy.deepcopy(scene())
        candidate["elements"].append(
            common("far-below", "rectangle", 0, 5000, 180, 80)
        )
        errors, notes = validate_scene(candidate, viewport_width=1600)
        self.assertEqual(errors, [])
        self.assertTrue(any("fit-to-width" in note for note in notes))

    def test_rejects_invalid_font_metrics_without_crashing_fit_view(self):
        candidate = scene()
        candidate["elements"][1]["fontSize"] = "20"
        errors, _ = validate_scene(candidate, viewport_width=1600)
        self.assertTrue(any("fontSize must be a finite number" in error for error in errors))

    def test_rejects_explicit_lines_that_exceed_text_height(self):
        candidate = scene()
        candidate["elements"][1]["text"] = "Client\napplication"
        candidate["elements"][1]["originalText"] = "Client application"
        errors, _ = validate_scene(candidate)
        self.assertTrue(any("clips 2 explicit text lines" in error for error in errors))

    def test_accepts_wrapped_bound_text_when_height_is_sufficient(self):
        candidate = scene()
        candidate["elements"][1]["text"] = "Client\napplication"
        candidate["elements"][1]["originalText"] = "Client application"
        candidate["elements"][1]["height"] = 50
        errors, notes = validate_scene(candidate)
        self.assertEqual(errors, [])
        self.assertTrue(any("normalization not proven" in note for note in notes))

    def test_rejects_scene_changed_by_target_normalization(self):
        candidate = scene()
        candidate["elements"][1].update(
            {
                "text": "0 · READINESS\nnow\nGate: external access is safe",
                "originalText": (
                    "0 · READINESS now Gate: external access is safe"
                ),
                "height": 75,
            }
        )
        normalized_again = copy.deepcopy(candidate)
        normalized_again["elements"][1].update(
            {
                "text": (
                    "0 · READINESS now\nGate: external access is safe"
                ),
                "height": 50,
                "y": 30,
            }
        )

        structural_errors, notes = validate_scene(candidate)
        stability_errors, _ = compare_normalization_stability(
            candidate,
            normalized_again,
        )

        self.assertEqual(structural_errors, [])
        self.assertTrue(any("normalization not proven" in note for note in notes))
        self.assertTrue(
            any("left-label.text" in error for error in stability_errors)
        )
        self.assertTrue(
            any("left-label.height" in error for error in stability_errors)
        )
        self.assertTrue(
            any("left-label.y" in error for error in stability_errors)
        )

    def test_accepts_scene_stable_under_repeated_normalization(self):
        candidate = scene()
        candidate["elements"][1]["text"] = "Client\napplication"
        candidate["elements"][1]["originalText"] = "Client application"
        candidate["elements"][1]["height"] = 50
        normalized_again = copy.deepcopy(candidate)
        normalized_again["elements"][1]["version"] += 1
        normalized_again["elements"][1]["versionNonce"] += 1
        normalized_again["elements"][1]["updated"] += 1

        errors, notes = compare_normalization_stability(
            candidate,
            normalized_again,
        )

        self.assertEqual(errors, [])
        self.assertTrue(any("normalization stability: PASS" in note for note in notes))

    def test_semantic_original_text_breaks_can_be_normalization_stable(self):
        candidate = scene()
        candidate["elements"][1]["text"] = "Heading\nExplanation"
        candidate["elements"][1]["originalText"] = "Heading\nExplanation"
        candidate["elements"][1]["height"] = 50

        errors, _ = compare_normalization_stability(
            candidate,
            copy.deepcopy(candidate),
        )

        self.assertEqual(errors, [])

    def test_cli_requires_normalization_proof_for_bound_text(self):
        with tempfile.TemporaryDirectory() as directory:
            scene_path = Path(directory) / "scene.excalidraw"
            scene_path.write_text(json.dumps(scene()), encoding="utf-8")

            self.assertEqual(main([str(scene_path)]), 1)
            self.assertEqual(
                main([str(scene_path), "--structural-only"]),
                0,
            )

    def test_cli_accepts_stable_second_normalization(self):
        with tempfile.TemporaryDirectory() as directory:
            scene_path = Path(directory) / "scene.excalidraw"
            normalized_path = Path(directory) / "normalized.excalidraw"
            serialized = json.dumps(scene())
            scene_path.write_text(serialized, encoding="utf-8")
            normalized_path.write_text(serialized, encoding="utf-8")

            self.assertEqual(
                main(
                    [
                        str(scene_path),
                        "--normalization-result",
                        str(normalized_path),
                    ]
                ),
                0,
            )

    def test_rejects_mismatched_unbound_auto_resizing_text(self):
        candidate = scene()
        candidate["elements"][0]["boundElements"] = [
            {"id": "flow", "type": "arrow"},
        ]
        candidate["elements"][1]["containerId"] = None
        candidate["elements"][1]["originalText"] = "Customer"
        errors, _ = validate_scene(candidate)
        self.assertTrue(any("must match for unwrapped text" in error for error in errors))

    def test_rejects_literal_newline_escape(self):
        candidate = scene()
        candidate["elements"][1]["text"] = r"Client\napplication"
        candidate["elements"][1]["originalText"] = r"Client\napplication"
        errors, _ = validate_scene(candidate)
        self.assertTrue(any("literal escape token '\\\\n'" in error for error in errors))

    def test_rejects_literal_newline_escape_in_original_text(self):
        candidate = scene()
        candidate["elements"][1]["text"] = "Client\napplication"
        candidate["elements"][1]["originalText"] = r"Client\napplication"
        candidate["elements"][1]["height"] = 50
        errors, _ = validate_scene(candidate)
        self.assertTrue(any("originalText" in error for error in errors))
        self.assertTrue(any("literal escape token '\\\\n'" in error for error in errors))

    def test_rejects_manual_hard_line_break_in_auto_resizing_text(self):
        candidate = scene()
        candidate["elements"][0]["boundElements"] = [
            {"id": "flow", "type": "arrow"},
        ]
        candidate["elements"][1]["containerId"] = None
        candidate["elements"][1]["text"] = "Client\napplication"
        candidate["elements"][1]["originalText"] = "Client\napplication"
        candidate["elements"][1]["height"] = 50
        errors, _ = validate_scene(candidate)
        self.assertTrue(any("hard line break" in error for error in errors))

    def test_rejects_manual_hard_line_break_in_fixed_width_text(self):
        candidate = scene()
        candidate["elements"][0]["boundElements"] = [
            {"id": "flow", "type": "arrow"},
        ]
        candidate["elements"][1]["containerId"] = None
        candidate["elements"][1]["autoResize"] = False
        candidate["elements"][1]["text"] = "Client\napplication"
        candidate["elements"][1]["originalText"] = "Client\napplication"
        candidate["elements"][1]["height"] = 50
        errors, _ = validate_scene(candidate)
        self.assertTrue(any("hard line break" in error for error in errors))

    def test_allows_semantic_hard_line_break_by_element_id(self):
        candidate = scene()
        candidate["elements"][0]["boundElements"] = [
            {"id": "flow", "type": "arrow"},
        ]
        candidate["elements"][1]["containerId"] = None
        candidate["elements"][1]["text"] = "Heading\nExplanation"
        candidate["elements"][1]["originalText"] = "Heading\nExplanation"
        candidate["elements"][1]["height"] = 50
        errors, _ = validate_scene(
            candidate,
            allowed_hard_line_break_ids={"left-label"},
        )
        self.assertEqual(errors, [])

    def test_allows_intentional_literal_escape_by_element_id(self):
        candidate = scene()
        candidate["elements"][1]["text"] = r"Client\napplication"
        candidate["elements"][1]["originalText"] = r"Client\napplication"
        errors, _ = validate_scene(
            candidate,
            allowed_literal_escape_ids={"left-label"},
        )
        self.assertEqual(errors, [])

    def test_rejects_unknown_literal_escape_allowance(self):
        errors, _ = validate_scene(
            scene(),
            allowed_literal_escape_ids={"missing-label"},
        )
        self.assertTrue(any("allowance does not resolve" in error for error in errors))

    def test_rejects_literal_escape_allowance_for_non_text_element(self):
        errors, _ = validate_scene(
            scene(),
            allowed_literal_escape_ids={"left"},
        )
        self.assertTrue(any("requires a text element" in error for error in errors))

    def test_rejects_unknown_hard_line_break_allowance(self):
        errors, _ = validate_scene(
            scene(),
            allowed_hard_line_break_ids={"missing-label"},
        )
        self.assertTrue(any("allowance does not resolve" in error for error in errors))


class GeometryWarningTests(unittest.TestCase):
    @staticmethod
    def with_obstacle() -> dict:
        candidate = scene()
        candidate["elements"].append(common("block", "rectangle", 220, -20, 100, 120))
        return candidate

    def test_valid_scene_has_no_warnings(self):
        self.assertEqual(geometry_warnings(scene()), ([], []))

    def test_validate_scene_signature_is_unchanged(self):
        result = validate_scene(self.with_obstacle())
        self.assertEqual(len(result), 2)

    def test_connector_through_unrelated_shape_warns(self):
        warnings, notes = geometry_warnings(self.with_obstacle())
        self.assertEqual(len(warnings), 1, warnings)
        self.assertIn("flow", warnings[0])
        self.assertIn("block", warnings[0])
        self.assertEqual(notes, [])

    def test_connector_touching_shape_edge_does_not_warn(self):
        candidate = scene()
        # Top edge at y=40 coincides with the arrow's path.
        candidate["elements"].append(common("edge", "rectangle", 220, 40, 100, 60))
        self.assertEqual(geometry_warnings(candidate)[0], [])

    def test_unbound_line_through_shape_warns(self):
        candidate = self.with_obstacle()
        line = common("rule", "line", 200, 0, 0, 200)
        line.update(
            {
                "points": [[0, -50], [0, 150]],
                "startBinding": None,
                "endBinding": None,
                "startArrowhead": None,
                "endArrowhead": None,
                "polygon": False,
            }
        )
        candidate["elements"].append(line)
        warnings, _ = geometry_warnings(candidate)
        self.assertEqual(sum("rule" in warning for warning in warnings), 0)
        line["x"] = 250
        warnings, _ = geometry_warnings(candidate)
        self.assertTrue(any("line rule" in warning for warning in warnings), warnings)

    def test_containing_boundary_shape_is_not_an_obstacle(self):
        candidate = scene()
        candidate["elements"].append(common("zone", "rectangle", -50, -50, 640, 200))
        self.assertEqual(geometry_warnings(candidate), ([], []))

    def test_container_of_only_unrelated_shape_is_still_an_obstacle(self):
        candidate = scene()
        # Contains neither bound endpoint element, only the arrow's middle.
        candidate["elements"].append(common("middle", "rectangle", 190, 20, 160, 40))
        warnings, _ = geometry_warnings(candidate)
        self.assertEqual(len(warnings), 1, warnings)

    def test_shared_attach_point_warns(self):
        candidate = scene()
        third = common("third", "rectangle", 360, 200, 180, 80)
        third["boundElements"] = [{"id": "flow2", "type": "arrow"}]
        flow2 = common("flow2", "arrow", 180, 40, 180, 200)
        flow2.update(
            {
                "points": [[0, 0], [180, 200]],
                "startBinding": {
                    "elementId": "left",
                    "fixedPoint": [1, 0.51],
                    "mode": "orbit",
                },
                "endBinding": {
                    "elementId": "third",
                    "fixedPoint": [0, 0.5],
                    "mode": "orbit",
                },
                "startArrowhead": None,
                "endArrowhead": "arrow",
                "elbowed": False,
            }
        )
        candidate["elements"][0]["boundElements"].append(
            {"id": "flow2", "type": "arrow"}
        )
        candidate["elements"].extend([third, flow2])
        warnings, _ = geometry_warnings(candidate)
        self.assertEqual(len(warnings), 1, warnings)
        self.assertIn("flow.start", warnings[0])
        self.assertIn("flow2.start", warnings[0])
        self.assertIn("left", warnings[0])

        flow2["startBinding"]["fixedPoint"] = [1, 0.8]
        self.assertEqual(geometry_warnings(candidate)[0], [])

    def test_connector_label_over_shape_warns(self):
        candidate = scene()
        candidate["elements"].append(common("block", "rectangle", 200, 100, 140, 80))
        add_flow_label(candidate, "flow-label", 240, 85)
        warnings, _ = geometry_warnings(candidate)
        self.assertEqual(len(warnings), 1, warnings)
        self.assertIn("flow-label", warnings[0])
        self.assertIn("block", warnings[0])

    def test_connector_label_in_clear_space_does_not_warn(self):
        candidate = scene()
        add_flow_label(candidate, "flow-label", 240, 5)
        self.assertEqual(geometry_warnings(candidate), ([], []))

    def test_overlapping_connector_labels_warn(self):
        candidate = scene()
        add_flow_label(candidate, "label-a", 240, 5)
        add_flow_label(candidate, "label-b", 260, 10)
        warnings, _ = geometry_warnings(candidate)
        self.assertEqual(len(warnings), 1, warnings)
        self.assertIn("label-a", warnings[0])
        self.assertIn("label-b", warnings[0])

    def test_connector_label_and_standalone_text_overlap_warns(self):
        candidate = scene()
        add_flow_label(candidate, "flow-label", 240, 5)
        candidate["elements"].append(label("note", None, 250, 10))
        warnings, _ = geometry_warnings(candidate)
        self.assertEqual(len(warnings), 1, warnings)
        self.assertIn("flow-label", warnings[0])
        self.assertIn("note", warnings[0])

    def test_overlapping_standalone_texts_warn(self):
        candidate = scene()
        candidate["elements"].append(label("note-a", None, 240, 5))
        candidate["elements"].append(label("note-b", None, 260, 10))
        warnings, _ = geometry_warnings(candidate)
        self.assertEqual(len(warnings), 1, warnings)
        self.assertIn("note-a", warnings[0])
        self.assertIn("note-b", warnings[0])

    def test_separate_standalone_texts_do_not_warn(self):
        candidate = scene()
        candidate["elements"].append(label("note-a", None, 240, 5))
        candidate["elements"].append(label("note-b", None, 240, 150))
        self.assertEqual(geometry_warnings(candidate), ([], []))

    def test_standalone_text_partially_over_shape_warns(self):
        candidate = scene()
        candidate["elements"].append(common("block", "rectangle", 200, 100, 140, 80))
        candidate["elements"].append(label("note", None, 300, 150, 100, 25))
        warnings, _ = geometry_warnings(candidate)
        self.assertEqual(len(warnings), 1, warnings)
        self.assertIn("note", warnings[0])

    def test_standalone_text_fully_inside_shape_does_not_warn(self):
        candidate = scene()
        candidate["elements"].append(common("zone", "rectangle", 200, 100, 140, 80))
        candidate["elements"].append(label("note", None, 220, 130, 100, 25))
        self.assertEqual(geometry_warnings(candidate), ([], []))

    def test_rotated_element_is_noted_and_not_checked(self):
        candidate = self.with_obstacle()
        candidate["elements"][-1]["angle"] = 0.5
        warnings, notes = geometry_warnings(candidate)
        self.assertEqual(warnings, [])
        self.assertEqual(len(notes), 1, notes)
        self.assertIn("block", notes[0])
        self.assertIn("not checked", notes[0])

    def test_deleted_obstacle_is_ignored(self):
        candidate = self.with_obstacle()
        candidate["elements"][-1]["isDeleted"] = True
        self.assertEqual(geometry_warnings(candidate), ([], []))

    def test_malformed_input_does_not_crash(self):
        self.assertEqual(geometry_warnings([]), ([], []))
        self.assertEqual(geometry_warnings({"elements": [1, {"id": 3}]}), ([], []))
        candidate = self.with_obstacle()
        candidate["elements"][-2]["points"] = "bad"
        self.assertEqual(geometry_warnings(candidate)[0], [])

    def test_cli_warnings_do_not_change_exit_code(self):
        with tempfile.TemporaryDirectory() as directory:
            scene_path = Path(directory) / "scene.excalidraw"
            scene_path.write_text(json.dumps(self.with_obstacle()), encoding="utf-8")
            code, stdout, stderr = run_cli(str(scene_path), "--structural-only")
        self.assertEqual(code, 0, stderr)
        warn_lines = [line for line in stdout.splitlines() if line.startswith("WARN: ")]
        self.assertEqual(len(warn_lines), 1, stdout)
        self.assertIn("block", warn_lines[0])
        lines = stdout.splitlines()
        last_note = max(i for i, line in enumerate(lines) if line.startswith("NOTE: "))
        self.assertGreater(lines.index(warn_lines[0]), last_note)
        self.assertEqual(stderr, "")

    def test_cli_strict_geometry_turns_warnings_into_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            scene_path = Path(directory) / "scene.excalidraw"
            scene_path.write_text(json.dumps(self.with_obstacle()), encoding="utf-8")
            code, stdout, stderr = run_cli(
                str(scene_path), "--structural-only", "--strict-geometry"
            )
        self.assertEqual(code, 1)
        self.assertNotIn("WARN:", stdout)
        self.assertIn("ERROR: geometry:", stderr)
        self.assertIn("block", stderr)

    def test_cli_oversized_integer_is_a_parse_error_not_a_crash(self):
        with tempfile.TemporaryDirectory() as directory:
            scene_path = Path(directory) / "scene.excalidraw"
            scene_path.write_text('{"elements": [{"x": ' + "1" * 5000 + "}]}", encoding="utf-8")
            code, _, stderr = run_cli(str(scene_path), "--structural-only")
        self.assertEqual(code, 2)
        self.assertIn("ERROR: cannot parse", stderr)

    def test_cli_strict_geometry_passes_clean_scene(self):
        with tempfile.TemporaryDirectory() as directory:
            scene_path = Path(directory) / "scene.excalidraw"
            scene_path.write_text(json.dumps(scene()), encoding="utf-8")
            code, stdout, _ = run_cli(
                str(scene_path), "--structural-only", "--strict-geometry"
            )
        self.assertEqual(code, 0)
        self.assertNotIn("WARN:", stdout)

    def test_cli_rotated_note_does_not_fail_strict_geometry(self):
        candidate = self.with_obstacle()
        candidate["elements"][-1]["angle"] = 0.5
        with tempfile.TemporaryDirectory() as directory:
            scene_path = Path(directory) / "scene.excalidraw"
            scene_path.write_text(json.dumps(candidate), encoding="utf-8")
            code, stdout, _ = run_cli(
                str(scene_path), "--structural-only", "--strict-geometry"
            )
        self.assertEqual(code, 0)
        self.assertIn("NOTE: geometry not checked for rotated element block", stdout)


if __name__ == "__main__":
    unittest.main()
