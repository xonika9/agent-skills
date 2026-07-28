#!/usr/bin/env python3
"""Regression tests for check_scene.py."""

from __future__ import annotations

import copy
import unittest

from check_scene import validate_scene


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

    def test_rejects_virgil(self):
        candidate = scene()
        candidate["elements"][1]["fontFamily"] = 1
        errors, _ = validate_scene(candidate)
        self.assertTrue(any("Excalifont" in error for error in errors))

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
        self.assertTrue(any("fit-to-view" in error for error in errors))

    def test_rejects_invalid_font_metrics_without_crashing_fit_view(self):
        candidate = scene()
        candidate["elements"][1]["fontSize"] = "20"
        errors, _ = validate_scene(candidate, viewport_width=1600)
        self.assertTrue(any("fontSize must be a finite number" in error for error in errors))

    def test_rejects_explicit_lines_that_exceed_text_height(self):
        candidate = scene()
        candidate["elements"][1]["text"] = "Client\napplication"
        candidate["elements"][1]["originalText"] = "Client\napplication"
        errors, _ = validate_scene(candidate)
        self.assertTrue(any("clips 2 explicit text lines" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
