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
CURRENT_FONT_FAMILIES = {1, 2, 3, 5, 6}
BASIC_ELEMENT_TYPES = {"rectangle", "diamond", "ellipse", "text", "line", "arrow"}
LITERAL_CONTROL_ESCAPES = {
    "\\n": "LF (U+000A)",
    "\\r": "CR (U+000D)",
    "\\t": "TAB (U+0009)",
}
NORMALIZATION_LAYOUT_FIELDS = ("x", "y", "width", "height", "angle")
NORMALIZATION_TEXT_FIELDS = (
    "text",
    "originalText",
    "fontSize",
    "fontFamily",
    "lineHeight",
    "containerId",
    "autoResize",
)
NORMALIZATION_LINEAR_FIELDS = (
    "points",
    "startBinding",
    "endBinding",
)


def _number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _normalization_values_match(left: Any, right: Any, tolerance: float) -> bool:
    if _number(left) and _number(right):
        return math.isclose(left, right, rel_tol=0.0, abs_tol=tolerance)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(
            _normalization_values_match(a, b, tolerance)
            for a, b in zip(left, right)
        )
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(
            _normalization_values_match(left[key], right[key], tolerance)
            for key in left
        )
    return left == right


def compare_normalization_stability(
    scene: Any,
    normalization_result: Any,
    *,
    tolerance: float = 1e-6,
) -> tuple[list[str], list[str]]:
    """Compare a final scene with the same scene normalized one more time."""
    errors: list[str] = []
    notes: list[str] = []
    if not isinstance(scene, dict) or not isinstance(normalization_result, dict):
        return ["normalization comparison requires two scene objects"], notes

    def active_by_id(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
        elements = data.get("elements")
        if not isinstance(elements, list):
            return {}
        return {
            element["id"]: element
            for element in elements
            if isinstance(element, dict)
            and isinstance(element.get("id"), str)
            and not element.get("isDeleted")
        }

    before = active_by_id(scene)
    after = active_by_id(normalization_result)
    for element_id in sorted(before.keys() - after.keys()):
        errors.append(
            f"normalization removed or deleted active element {element_id!r}"
        )
    for element_id in sorted(after.keys() - before.keys()):
        errors.append(
            f"normalization added or restored active element {element_id!r}"
        )

    for element_id in sorted(before.keys() & after.keys()):
        candidate = before[element_id]
        normalized = after[element_id]
        if candidate.get("type") != normalized.get("type"):
            errors.append(
                f"normalization changed {element_id}.type from "
                f"{candidate.get('type')!r} to {normalized.get('type')!r}"
            )
            continue

        fields = list(NORMALIZATION_LAYOUT_FIELDS)
        if candidate.get("type") == "text":
            fields.extend(NORMALIZATION_TEXT_FIELDS)
        if candidate.get("type") in {"line", "arrow"}:
            fields.extend(NORMALIZATION_LINEAR_FIELDS)
        for field in fields:
            if not _normalization_values_match(
                candidate.get(field),
                normalized.get(field),
                tolerance,
            ):
                errors.append(
                    f"normalization changed {element_id}.{field}; "
                    "the final scene is not interaction-stable"
                )

    if not errors:
        notes.append(
            f"normalization stability: PASS for {len(before)} active element(s)"
        )
    return errors, notes


def _binding_errors(
    binding: Any,
    element_id: str,
    endpoint: str,
    by_id: dict[str, dict[str, Any]],
) -> list[str]:
    if binding is None:
        return []
    prefix = f"{element_id}.{endpoint}Binding"
    if not isinstance(binding, dict):
        return [f"{prefix} must be an object or null"]

    errors: list[str] = []
    target = binding.get("elementId")
    target_element = by_id.get(target) if isinstance(target, str) else None
    if target_element is None or target_element.get("isDeleted"):
        errors.append(
            f"{prefix}.elementId does not resolve to an active element: {target!r}"
        )

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
    viewport_height: float | None = None,
    minimum_effective_font: float = 12.0,
    required_fonts: set[int] | None = None,
    allowed_literal_escape_ids: set[str] | None = None,
    allowed_hard_line_break_ids: set[str] | None = None,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    notes: list[str] = []
    allowed_literal_escape_ids = allowed_literal_escape_ids or set()
    allowed_hard_line_break_ids = allowed_hard_line_break_ids or set()

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
    renderer_wrapped_text_ids: list[str] = []

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
        if element_type not in BASIC_ELEMENT_TYPES:
            errors.append(
                f"{element_id}.type is outside the supported basic subset: "
                f"{element_type!r}"
            )
        for field in ("x", "y", "width", "height", "angle", "strokeWidth",
                      "roughness", "opacity", "seed", "version",
                      "versionNonce", "updated"):
            if field in element and not _number(element[field]):
                errors.append(f"{element_id}.{field} must be a finite number")

        for field in ("strokeColor", "backgroundColor"):
            if field in element and not isinstance(element[field], str):
                errors.append(f"{element_id}.{field} must be a string")
        for field in ("isDeleted", "locked"):
            if field in element and type(element[field]) is not bool:
                errors.append(f"{element_id}.{field} must be a boolean")
        for field in ("frameId", "link"):
            if (
                field in element
                and element[field] is not None
                and not isinstance(element[field], str)
            ):
                errors.append(f"{element_id}.{field} must be a string or null")

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
                if font not in CURRENT_FONT_FAMILIES:
                    errors.append(
                        f"{element_id}.fontFamily is not a current serialized "
                        f"family: {font}"
                    )
            for field in ("fontSize", "lineHeight"):
                if not _number(element.get(field)):
                    errors.append(f"{element_id}.{field} must be a finite number")
            if not isinstance(element.get("autoResize"), bool):
                errors.append(f"{element_id}.autoResize must be a boolean")
            for field in ("text", "originalText"):
                if not isinstance(element.get(field), str):
                    errors.append(f"{element_id}.{field} must be a string")
            text = element.get("text")
            original_text = element.get("originalText")
            may_wrap = (
                bool(element.get("containerId"))
                or element.get("autoResize") is False
            )
            if (
                isinstance(text, str)
                and isinstance(original_text, str)
                and not may_wrap
                and text != original_text
            ):
                errors.append(
                    f"{element_id}.text and originalText must match for "
                    "unwrapped text"
                )
            if (
                isinstance(text, str)
                and isinstance(original_text, str)
                and bool(element.get("containerId"))
                and text != original_text
                and not element.get("isDeleted")
            ):
                renderer_wrapped_text_ids.append(element_id)
            if element_id not in allowed_literal_escape_ids:
                for token, control_character in LITERAL_CONTROL_ESCAPES.items():
                    escaped_fields = [
                        field
                        for field in ("text", "originalText")
                        if isinstance(element.get(field), str)
                        and token in element[field]
                    ]
                    if escaped_fields:
                        fields = " and ".join(escaped_fields)
                        verb = "contains" if len(escaped_fields) == 1 else "contain"
                        errors.append(
                            f"{element_id}.{fields} {verb} literal escape token "
                            f"{token!r}; use {control_character} before JSON "
                            "serialization or allow this element explicitly"
                        )
            if (
                isinstance(original_text, str)
                and "\n" in original_text
                and element.get("containerId") is None
                and element_id not in allowed_hard_line_break_ids
            ):
                errors.append(
                    f"{element_id}.originalText contains a hard line break in "
                    "unbound text; let Excalidraw wrap by width "
                    "or allow this element explicitly"
                )
            if (
                isinstance(text, str)
                and _number(element.get("fontSize"))
                and _number(element.get("lineHeight"))
                and _number(element.get("height"))
            ):
                explicit_lines = text.count("\n") + 1
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
            container = by_id.get(container_id) if isinstance(container_id, str) else None
            if container_id is not None and (
                container is None or container.get("isDeleted")
            ):
                errors.append(
                    f"{element_id}.containerId does not resolve to an active "
                    f"element: {container_id!r}"
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
                        by_id,
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
            bound_type = bound.get("type")
            if bound_type not in {"arrow", "text"}:
                errors.append(
                    f"{element_id}.boundElements type must be 'arrow' or 'text'"
                )
            elif target is not None and target.get("type") != bound_type:
                errors.append(
                    f"{element_id}.boundElements declares {bound.get('id')!r} "
                    f"as {bound_type!r}, but the target type is "
                    f"{target.get('type')!r}"
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

    for element_id in sorted(allowed_literal_escape_ids):
        target = by_id.get(element_id)
        if target is None:
            errors.append(
                f"literal-escape allowance does not resolve to an element: "
                f"{element_id!r}"
            )
        elif target.get("type") != "text":
            errors.append(
                f"literal-escape allowance requires a text element, got "
                f"{target.get('type')!r}: {element_id!r}"
            )

    for element_id in sorted(allowed_hard_line_break_ids):
        target = by_id.get(element_id)
        if target is None:
            errors.append(
                f"hard-line-break allowance does not resolve to an element: "
                f"{element_id!r}"
            )
        elif target.get("type") != "text":
            errors.append(
                f"hard-line-break allowance requires a text element, got "
                f"{target.get('type')!r}: {element_id!r}"
            )

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
            fit_label = f"fit-to-width {viewport_width:g}px"
            if viewport_height is not None and height > 0:
                scale = min(scale, viewport_height / height)
                fit_label = (
                    f"fit-to-{viewport_width:g}×{viewport_height:g}px viewport"
                )
            effective = min(text["fontSize"] * scale for text in active_text)
            notes.append(f"{fit_label} minimum text size: {effective:.1f}px")
            if effective < minimum_effective_font:
                errors.append(
                    f"{fit_label} minimum text size {effective:.1f}px is below "
                    f"{minimum_effective_font:g}px"
                )

    notes.append(
        "font families used: "
        + (", ".join(str(font) for font in sorted(used_fonts)) or "none")
    )
    if renderer_wrapped_text_ids:
        notes.append(
            "normalization not proven: renderer-derived wrapping appears in "
            f"{len(renderer_wrapped_text_ids)} active bound text element(s) "
            f"({', '.join(sorted(renderer_wrapped_text_ids))}); static validation "
            "cannot certify interaction stability"
        )
    return errors, notes


def active_bound_text_ids(data: Any) -> list[str]:
    if not isinstance(data, dict) or not isinstance(data.get("elements"), list):
        return []
    return sorted(
        element["id"]
        for element in data["elements"]
        if isinstance(element, dict)
        and element.get("type") == "text"
        and isinstance(element.get("id"), str)
        and element.get("containerId")
        and not element.get("isDeleted")
    )


def _summarize_ids(ids: list[str], limit: int = 5) -> str:
    shown = ", ".join(ids[:limit])
    if len(ids) > limit:
        shown += f", … +{len(ids) - limit} more"
    return shown


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scene", type=Path)
    parser.add_argument(
        "--viewport-width",
        type=float,
        help="fail when fit-to-width text becomes too small",
    )
    parser.add_argument(
        "--viewport-height",
        type=float,
        help="also constrain fit-to-view by height; requires --viewport-width",
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
    parser.add_argument(
        "--allow-literal-escapes-in",
        action="append",
        default=[],
        metavar="ELEMENT_ID",
        help=(
            "allow literal backslash-n, backslash-r, or backslash-t in one text "
            "element; repeat as needed"
        ),
    )
    parser.add_argument(
        "--allow-hard-line-breaks-in",
        action="append",
        default=[],
        metavar="ELEMENT_ID",
        help=(
            "allow semantic LF line breaks in one unbound text element; "
            "repeat as needed"
        ),
    )
    parser.add_argument(
        "--normalization-result",
        type=Path,
        help=(
            "scene produced by applying the target Excalidraw normalizer once "
            "more to the final scene; fail if interaction-relevant fields changed"
        ),
    )
    parser.add_argument(
        "--normalization-tolerance",
        type=float,
        default=1e-6,
        help="absolute numeric tolerance for normalization comparison (default: 1e-6)",
    )
    parser.add_argument(
        "--structural-only",
        action="store_true",
        help=(
            "allow an intermediate structural pass without normalization proof; "
            "not valid as final completion evidence"
        ),
    )
    args = parser.parse_args(argv)
    if args.viewport_height is not None and args.viewport_width is None:
        parser.error("--viewport-height requires --viewport-width")
    if (
        not math.isfinite(args.normalization_tolerance)
        or args.normalization_tolerance < 0
    ):
        parser.error("--normalization-tolerance must be finite and not negative")
    for option, value in (
        ("--viewport-width", args.viewport_width),
        ("--viewport-height", args.viewport_height),
        ("--minimum-effective-font", args.minimum_effective_font),
    ):
        if value is not None and (not math.isfinite(value) or value <= 0):
            parser.error(f"{option} must be finite and positive")
    if args.structural_only and args.normalization_result is not None:
        parser.error(
            "--structural-only cannot be combined with --normalization-result"
        )
    return args


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
        viewport_height=args.viewport_height,
        minimum_effective_font=args.minimum_effective_font,
        required_fonts=set(args.require_font_family),
        allowed_literal_escape_ids=set(args.allow_literal_escapes_in),
        allowed_hard_line_break_ids=set(args.allow_hard_line_breaks_in),
    )
    bound_text_ids = active_bound_text_ids(data)
    if (
        bound_text_ids
        and args.normalization_result is None
        and not args.structural_only
    ):
        errors.append(
            f"normalization proof is required for {len(bound_text_ids)} active "
            f"bound text element(s) ({_summarize_ids(bound_text_ids)}); "
            "provide --normalization-result "
            "or use --structural-only for an intermediate check"
        )
    if args.normalization_result is not None:
        try:
            normalization_result = json.loads(
                args.normalization_result.read_text(encoding="utf-8")
            )
        except FileNotFoundError:
            print(
                f"ERROR: file not found: {args.normalization_result}",
                file=sys.stderr,
            )
            return 2
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            print(
                f"ERROR: cannot parse {args.normalization_result}: {error}",
                file=sys.stderr,
            )
            return 2
        normalized_errors, _ = validate_scene(
            normalization_result,
            required_fonts=set(args.require_font_family),
            allowed_literal_escape_ids=set(args.allow_literal_escapes_in),
            allowed_hard_line_break_ids=set(args.allow_hard_line_breaks_in),
        )
        errors.extend(
            f"normalization result: {error}" for error in normalized_errors
        )
        stability_errors, stability_notes = compare_normalization_stability(
            data,
            normalization_result,
            tolerance=args.normalization_tolerance,
        )
        errors.extend(stability_errors)
        notes.extend(stability_notes)
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
