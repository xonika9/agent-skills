#!/usr/bin/env python3
"""Validate the current basic Excalidraw scene contract used by this skill."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


COMMON_REQUIRED = {
    "id",
    "type",
    "x",
    "y",
    "width",
    "height",
    "angle",
    "strokeColor",
    "backgroundColor",
    "fillStyle",
    "strokeWidth",
    "strokeStyle",
    "roundness",
    "roughness",
    "opacity",
    "seed",
    "version",
    "versionNonce",
    "index",
    "isDeleted",
    "groupIds",
    "frameId",
    "boundElements",
    "updated",
    "link",
    "locked",
}
TEXT_REQUIRED = {
    "fontSize",
    "fontFamily",
    "text",
    "originalText",
    "textAlign",
    "verticalAlign",
    "containerId",
    "autoResize",
    "lineHeight",
}
LINEAR_REQUIRED = {
    "points",
    "startBinding",
    "endBinding",
    "startArrowhead",
    "endArrowhead",
}

FILL_STYLES = {"hachure", "cross-hatch", "solid", "zigzag"}
STROKE_STYLES = {"solid", "dashed", "dotted"}
TEXT_ALIGNS = {"left", "center", "right"}
VERTICAL_ALIGNS = {"top", "middle", "bottom"}
BIND_MODES = {"inside", "orbit", "skip"}
ARROWHEADS = {
    "arrow",
    "bar",
    "circle",
    "circle_outline",
    "triangle",
    "triangle_outline",
    "diamond",
    "diamond_outline",
    "cardinality_one",
    "cardinality_many",
    "cardinality_one_or_many",
    "cardinality_exactly_one",
    "cardinality_zero_or_one",
    "cardinality_zero_or_many",
}
SKILL_FONTS = {5, 6}


def _number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _binding_errors(
    binding: Any, element_id: str, endpoint: str, ids: set[str]
) -> list[str]:
    if binding is None:
        return []
    prefix = f"{element_id}.{endpoint}Binding"
    if not isinstance(binding, dict):
        return [f"{prefix} must be an object or null"]

    errors: list[str] = []
    target = binding.get("elementId")
    if not isinstance(target, str) or target not in ids:
        errors.append(f"{prefix}.elementId does not resolve: {target!r}")

    point = binding.get("fixedPoint")
    if (
        not isinstance(point, list)
        or len(point) != 2
        or not all(_number(value) for value in point)
    ):
        errors.append(f"{prefix}.fixedPoint must be a numeric [x, y] pair")

    if binding.get("mode") not in BIND_MODES:
        errors.append(
            f"{prefix}.mode must be one of {sorted(BIND_MODES)}, "
            f"got {binding.get('mode')!r}"
        )
    return errors


def validate_scene(
    data: Any,
    *,
    viewport_width: float | None = None,
    minimum_effective_font: float = 12.0,
    required_fonts: set[int] | None = None,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    notes: list[str] = []

    if not isinstance(data, dict):
        return ["top-level JSON value must be an object"], notes
    if data.get("type") != "excalidraw":
        errors.append("top-level type must be 'excalidraw'")
    if data.get("version") != 2:
        errors.append("top-level version must be 2")
    if not isinstance(data.get("source"), str) or not data["source"]:
        errors.append("top-level source must be a non-empty string")
    if not isinstance(data.get("appState"), dict):
        errors.append("top-level appState must be an object")
    if not isinstance(data.get("files"), dict):
        errors.append("top-level files must be an object")

    elements = data.get("elements")
    if not isinstance(elements, list):
        return errors + ["top-level elements must be an array"], notes

    ids: set[str] = set()
    by_id: dict[str, dict[str, Any]] = {}
    for position, element in enumerate(elements):
        if not isinstance(element, dict):
            errors.append(f"elements[{position}] must be an object")
            continue
        element_id = element.get("id")
        if not isinstance(element_id, str) or not element_id:
            errors.append(f"elements[{position}].id must be a non-empty string")
            continue
        if element_id in ids:
            errors.append(f"duplicate element id: {element_id}")
        ids.add(element_id)
        by_id[element_id] = element

    used_fonts: set[int] = set()
    active_bounds: list[tuple[float, float, float, float]] = []
    active_text: list[dict[str, Any]] = []

    for position, element in enumerate(elements):
        if not isinstance(element, dict):
            continue
        element_id = element.get("id")
        if not isinstance(element_id, str) or not element_id:
            element_id = f"elements[{position}]"

        missing = sorted(COMMON_REQUIRED - element.keys())
        if missing:
            errors.append(f"{element_id} missing common fields: {', '.join(missing)}")

        element_type = element.get("type")
        for field in ("x", "y", "width", "height", "angle", "strokeWidth",
                      "roughness", "opacity", "seed", "version",
                      "versionNonce", "updated"):
            if field in element and not _number(element[field]):
                errors.append(f"{element_id}.{field} must be a finite number")

        if _number(element.get("width")) and element["width"] < 0:
            errors.append(f"{element_id}.width must not be negative")
        if _number(element.get("height")) and element["height"] < 0:
            errors.append(f"{element_id}.height must not be negative")
        if element.get("fillStyle") not in FILL_STYLES:
            errors.append(
                f"{element_id}.fillStyle is not current: {element.get('fillStyle')!r}"
            )
        if element.get("strokeStyle") not in STROKE_STYLES:
            errors.append(
                f"{element_id}.strokeStyle is not current: "
                f"{element.get('strokeStyle')!r}"
            )
        if not isinstance(element.get("groupIds"), list):
            errors.append(f"{element_id}.groupIds must be an array")
        if element.get("boundElements") is not None and not isinstance(
            element.get("boundElements"), list
        ):
            errors.append(f"{element_id}.boundElements must be an array or null")
        if element.get("index") is not None and not isinstance(
            element.get("index"), str
        ):
            errors.append(f"{element_id}.index must be a string or null")

        if element_type == "text":
            text_missing = sorted(TEXT_REQUIRED - element.keys())
            if text_missing:
                errors.append(
                    f"{element_id} missing text fields: {', '.join(text_missing)}"
                )
            font = element.get("fontFamily")
            if not isinstance(font, int) or isinstance(font, bool):
                errors.append(f"{element_id}.fontFamily must be an integer")
            else:
                used_fonts.add(font)
                if font not in SKILL_FONTS:
                    errors.append(
                        f"{element_id}.fontFamily must be 5 (Excalifont) or "
                        f"6 (Nunito), got {font}"
                    )
            for field in ("fontSize", "lineHeight"):
                if not _number(element.get(field)):
                    errors.append(f"{element_id}.{field} must be a finite number")
            if not isinstance(element.get("autoResize"), bool):
                errors.append(f"{element_id}.autoResize must be a boolean")
            for field in ("text", "originalText"):
                if not isinstance(element.get(field), str):
                    errors.append(f"{element_id}.{field} must be a string")
            if element.get("text") != element.get("originalText"):
                errors.append(f"{element_id}.text and originalText must match")
            if (
                isinstance(element.get("text"), str)
                and _number(element.get("fontSize"))
                and _number(element.get("lineHeight"))
                and _number(element.get("height"))
            ):
                explicit_lines = element["text"].count("\n") + 1
                minimum_height = (
                    explicit_lines * element["fontSize"] * element["lineHeight"]
                )
                if element["height"] + 1 < minimum_height:
                    errors.append(
                        f"{element_id}.height {element['height']:g} clips "
                        f"{explicit_lines} explicit text lines; expected at least "
                        f"{minimum_height:g}"
                    )
            if element.get("textAlign") not in TEXT_ALIGNS:
                errors.append(
                    f"{element_id}.textAlign must be one of {sorted(TEXT_ALIGNS)}"
                )
            if element.get("verticalAlign") not in VERTICAL_ALIGNS:
                errors.append(
                    f"{element_id}.verticalAlign must be one of "
                    f"{sorted(VERTICAL_ALIGNS)}"
                )
            container_id = element.get("containerId")
            if container_id is not None and container_id not in ids:
                errors.append(
                    f"{element_id}.containerId does not resolve: {container_id!r}"
                )
            if not element.get("isDeleted") and _number(element.get("fontSize")):
                active_text.append(element)

        if element_type in {"line", "arrow"}:
            linear_missing = sorted(LINEAR_REQUIRED - element.keys())
            if linear_missing:
                errors.append(
                    f"{element_id} missing linear fields: {', '.join(linear_missing)}"
                )
            points = element.get("points")
            if (
                not isinstance(points, list)
                or len(points) < 2
                or not all(
                    isinstance(point, list)
                    and len(point) == 2
                    and all(_number(value) for value in point)
                    for point in points
                )
            ):
                errors.append(f"{element_id}.points must contain numeric [x, y] pairs")
            for endpoint in ("start", "end"):
                errors.extend(
                    _binding_errors(
                        element.get(f"{endpoint}Binding"),
                        element_id,
                        endpoint,
                        ids,
                    )
                )
            for field in ("startArrowhead", "endArrowhead"):
                arrowhead = element.get(field)
                if arrowhead is not None and arrowhead not in ARROWHEADS:
                    errors.append(
                        f"{element_id}.{field} is not current: {arrowhead!r}"
                    )
            if element_type == "arrow" and not isinstance(
                element.get("elbowed"), bool
            ):
                errors.append(f"{element_id}.elbowed must be a boolean")
            if element_type == "line" and not isinstance(
                element.get("polygon"), bool
            ):
                errors.append(f"{element_id}.polygon must be a boolean")

        if (
            not element.get("isDeleted")
            and all(_number(element.get(field)) for field in ("x", "y", "width", "height"))
        ):
            active_bounds.append(
                (
                    element["x"],
                    element["y"],
                    element["x"] + element["width"],
                    element["y"] + element["height"],
                )
            )

    for element_id, element in by_id.items():
        if element.get("isDeleted"):
            continue

        for bound in element.get("boundElements") or []:
            if not isinstance(bound, dict):
                errors.append(f"{element_id}.boundElements entries must be objects")
                continue
            target = by_id.get(bound.get("id"))
            if target is None or target.get("isDeleted"):
                errors.append(
                    f"{element_id}.boundElements reference does not resolve: "
                    f"{bound.get('id')!r}"
                )
            if bound.get("type") not in {"arrow", "text"}:
                errors.append(
                    f"{element_id}.boundElements type must be 'arrow' or 'text'"
                )

        if element.get("type") == "text" and element.get("containerId"):
            container = by_id.get(element["containerId"])
            if container and not any(
                bound.get("id") == element_id and bound.get("type") == "text"
                for bound in container.get("boundElements") or []
                if isinstance(bound, dict)
            ):
                errors.append(
                    f"{element_id} is container-bound but "
                    f"{element['containerId']}.boundElements omits it"
                )

        if element.get("type") == "arrow":
            for endpoint in ("start", "end"):
                binding = element.get(f"{endpoint}Binding")
                if not isinstance(binding, dict):
                    continue
                target = by_id.get(binding.get("elementId"))
                if target and not any(
                    bound.get("id") == element_id and bound.get("type") == "arrow"
                    for bound in target.get("boundElements") or []
                    if isinstance(bound, dict)
                ):
                    errors.append(
                        f"{element_id}.{endpoint}Binding is not reciprocal in "
                        f"{target.get('id')}.boundElements"
                    )

    if required_fonts:
        for font in sorted(required_fonts - used_fonts):
            errors.append(f"required fontFamily {font} is not used")

    if active_bounds:
        min_x = min(bound[0] for bound in active_bounds)
        min_y = min(bound[1] for bound in active_bounds)
        max_x = max(bound[2] for bound in active_bounds)
        max_y = max(bound[3] for bound in active_bounds)
        width = max_x - min_x
        height = max_y - min_y
        notes.append(
            f"active bounds: {width:.1f} × {height:.1f} "
            f"({min_x:.1f}, {min_y:.1f})–({max_x:.1f}, {max_y:.1f})"
        )

        if viewport_width is not None and width > 0 and active_text:
            scale = viewport_width / width
            effective = min(text["fontSize"] * scale for text in active_text)
            notes.append(
                f"fit-to-{viewport_width:g}px minimum text size: {effective:.1f}px"
            )
            if effective < minimum_effective_font:
                errors.append(
                    f"fit-to-view minimum text size {effective:.1f}px is below "
                    f"{minimum_effective_font:g}px"
                )

    notes.append(
        "font families used: "
        + (", ".join(str(font) for font in sorted(used_fonts)) or "none")
    )
    return errors, notes


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scene", type=Path)
    parser.add_argument(
        "--viewport-width",
        type=float,
        help="fail when fit-to-width text becomes too small",
    )
    parser.add_argument(
        "--minimum-effective-font",
        type=float,
        default=12.0,
        help="minimum allowed text size after fitting (default: 12)",
    )
    parser.add_argument(
        "--require-font-family",
        type=int,
        action="append",
        default=[],
        help="require a fontFamily value to appear; repeat as needed",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        data = json.loads(args.scene.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"ERROR: file not found: {args.scene}", file=sys.stderr)
        return 2
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        print(f"ERROR: cannot parse {args.scene}: {error}", file=sys.stderr)
        return 2

    errors, notes = validate_scene(
        data,
        viewport_width=args.viewport_width,
        minimum_effective_font=args.minimum_effective_font,
        required_fonts=set(args.require_font_family),
    )
    for note in notes:
        print(f"NOTE: {note}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"FAIL: {len(errors)} issue(s)", file=sys.stderr)
        return 1

    print(f"PASS: {args.scene}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
