#!/usr/bin/env python3
"""Regression tests for check_scene.py."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from check_scene import compare_normalization_stability, main, validate_scene


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


if __name__ == "__main__":
    unittest.main()
