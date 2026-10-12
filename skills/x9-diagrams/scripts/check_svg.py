#!/usr/bin/env python3
"""Validate a standalone SVG diagram against the x9-diagrams SVG adapter contract.

Contract errors (document, accessibility, self-containment and inertness, layers,
semantic markup) exit 1. Geometry problems are reported as WARN lines computed
from the declared coordinates, and items whose geometry cannot be computed as
NOTE lines; --strict-geometry turns both into errors. Text overflow is an
estimate from character count, font size, and an average glyph width. Exit 2
means the input could not be read, was too large, or was rejected before
parsing (internal DTD subset or entity declarations).
"""

from __future__ import annotations

import argparse
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.parsers import expat
from typing import Iterator

SVG_NS = "http://www.w3.org/2000/svg"
LAYERS = ("boundaries", "edges", "nodes", "labels")

# Distance in user units within which a connector endpoint counts as "on" the
# bounding-box edge of its node, and within which two endpoints count as the
# same point.
ENDPOINT_TOLERANCE = 6.0
SHARED_POINT_TOLERANCE = ENDPOINT_TOLERANCE
# Node boxes shrink by this much before the connector-crossing test so a
# connector that merely touches a node edge is not reported.
OBSTACLE_INSET = 2.0
# Label masks closer than this to a node or to each other do not count as overlap.
OVERLAP_EPSILON = 0.5
# Estimated glyph advance as a fraction of the font size.
AVERAGE_CHAR_WIDTH_FACTOR = 0.6
DEFAULT_FONT_SIZE = 16.0
VIEWBOX_EPSILON = 1e-6
# Inputs larger than this are rejected before parsing (exit 2).
MAX_INPUT_BYTES = 20 * 1024 * 1024
# Public SVG DTD location the optional DOCTYPE may name.
SVG_DTD_PREFIX = "http://www.w3.org/Graphics/SVG/"

SHAPE_TAGS = {"rect", "ellipse", "circle", "polygon", "path"}
EDGE_TAGS = {"path", "line", "polyline"}
# SVG animation elements (and mpath, which only exists inside animateMotion).
ANIMATION_TAGS = {
    "animate", "animateColor", "animateMotion", "animateTransform", "set", "discard", "mpath",
}
# Elements whose geometry the checks cannot follow when they sit inside a layer.
FORBIDDEN_IN_LAYERS = ("svg", "use")
SKIPPED_CONTAINERS = {"defs", "marker", "clipPath", "mask", "pattern", "symbol"}
KIND_ATTRS = {
    "data-node": "node",
    "data-boundary": "boundary",
    "data-edge": "edge",
    "data-label-for": "label",
}
KIND_LAYER = {
    "node": "nodes",
    "boundary": "boundaries",
    "edge": "edges",
    "label": "labels",
}

NUMBER = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"
_NUMBER_RE = re.compile(NUMBER)
_LENGTH_RE = re.compile(rf"^\s*({NUMBER})(?:px)?\s*$")
_URL_RE = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.IGNORECASE | re.DOTALL)
_LOCAL_URL_RE = re.compile(r"^#[^\s'\"()]+$")
_EVENT_ATTR_RE = re.compile(r"^on[a-z]+$", re.IGNORECASE)
_CSS_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
_TRANSFORM_RE = re.compile(r"\s*([A-Za-z]+)\s*\(([^)]*)\)\s*,?")
_CSS_TRANSFORM_RE = re.compile(r"(?:^|;)\s*transform\s*:", re.IGNORECASE)

Point = tuple[float, float]
Box = tuple[float, float, float, float]


class GeometryUnsupported(Exception):
    """Geometry for one item cannot be computed from declared coordinates."""


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------


def _local(name: str) -> str:
    return name.rsplit("}", 1)[-1]


def _svg_name(element: ET.Element) -> str:
    """Local name for an element in the SVG namespace, else an empty string."""
    tag = element.tag
    if isinstance(tag, str) and tag.startswith(f"{{{SVG_NS}}}"):
        return tag[len(SVG_NS) + 2 :]
    return ""


def _fmt(value: float) -> str:
    return f"{value:.1f}".rstrip("0").rstrip(".")


def _point_text(point: Point) -> str:
    return f"({_fmt(point[0])}, {_fmt(point[1])})"


def _box_text(box: Box) -> str:
    return f"({_fmt(box[0])}, {_fmt(box[1])})-({_fmt(box[2])}, {_fmt(box[3])})"


def _text_of(element: ET.Element) -> str:
    return "".join(element.itertext())


def _strip_css_comments(text: str) -> str:
    return _CSS_COMMENT_RE.sub("", text)


def _parse_viewbox(value: str | None) -> tuple[Box | None, str | None]:
    if value is None:
        return None, "root <svg> needs a viewBox attribute"
    parts = [part for part in re.split(r"[\s,]+", value.strip()) if part]
    try:
        numbers = [float(part) for part in parts]
    except ValueError:
        return None, f"viewBox must be four numbers, got {value!r}"
    if len(numbers) != 4 or not all(math.isfinite(number) for number in numbers):
        return None, f"viewBox must be four finite numbers, got {value!r}"
    min_x, min_y, width, height = numbers
    if width <= 0 or height <= 0:
        return None, f"viewBox width and height must be positive, got {value!r}"
    return (min_x, min_y, min_x + width, min_y + height), None


def _own_descendants(group: ET.Element) -> Iterator[ET.Element]:
    """Descendants of a semantic group, not entering nested semantic groups."""
    stack = list(reversed(list(group)))
    while stack:
        element = stack.pop()
        if _svg_name(element) in SKIPPED_CONTAINERS:
            continue
        if any(attribute in element.attrib for attribute in KIND_ATTRS):
            continue
        yield element
        stack.extend(reversed(list(element)))


# --------------------------------------------------------------------------
# Geometry: numbers, transforms, shapes, paths
# --------------------------------------------------------------------------


def _length(element: ET.Element, name: str, default: float = 0.0) -> float:
    value = element.get(name)
    if value is None:
        return default
    match = _LENGTH_RE.match(value)
    if not match:
        raise GeometryUnsupported(f"non-numeric {name}={value!r} on <{_svg_name(element)}>")
    return float(match.group(1))


def _translate_of(element: ET.Element) -> Point:
    style = element.get("style")
    if style and _CSS_TRANSFORM_RE.search(style):
        raise GeometryUnsupported("unsupported CSS transform")
    value = element.get("transform")
    if value is None or not value.strip():
        return 0.0, 0.0
    dx = dy = 0.0
    position = 0
    text = value.strip()
    while position < len(text):
        match = _TRANSFORM_RE.match(text, position)
        if not match:
            raise GeometryUnsupported(f"unparseable transform {value!r}")
        name, args = match.group(1), match.group(2)
        if name != "translate":
            raise GeometryUnsupported(f"unsupported transform {name}()")
        numbers = [part for part in re.split(r"[\s,]+", args.strip()) if part]
        try:
            values = [float(part) for part in numbers]
        except ValueError:
            raise GeometryUnsupported(f"unparseable transform {value!r}") from None
        if len(values) not in (1, 2) or not all(math.isfinite(v) for v in values):
            raise GeometryUnsupported(f"unparseable transform {value!r}")
        dx += values[0]
        dy += values[1] if len(values) == 2 else 0.0
        position = match.end()
    return dx, dy


def _absolute_offset(element: ET.Element, parents: dict[ET.Element, ET.Element]) -> Point:
    """Sum of translate() on the element and all ancestors, in root user space."""
    dx = dy = 0.0
    current: ET.Element | None = element
    while current is not None:
        tx, ty = _translate_of(current)
        dx += tx
        dy += ty
        current = parents.get(current)
    return dx, dy


def _bounds(points: list[Point]) -> Box:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return min(xs), min(ys), max(xs), max(ys)


def _shift_box(box: Box, offset: Point) -> Box:
    return box[0] + offset[0], box[1] + offset[1], box[2] + offset[0], box[3] + offset[1]


def _shift_point(point: Point, offset: Point) -> Point:
    return point[0] + offset[0], point[1] + offset[1]


def _parse_points(value: str | None) -> list[Point]:
    numbers = [float(n) for n in _NUMBER_RE.findall(value or "")]
    if len(numbers) < 2 or len(numbers) % 2:
        raise GeometryUnsupported(f"unparseable points {value!r}")
    return [(numbers[i], numbers[i + 1]) for i in range(0, len(numbers), 2)]


class _PathScanner:
    def __init__(self, text: str) -> None:
        self.text = text
        self.index = 0

    def skip_separators(self) -> None:
        while self.index < len(self.text) and self.text[self.index] in " \t\r\n,":
            self.index += 1

    def done(self) -> bool:
        self.skip_separators()
        return self.index >= len(self.text)

    def peek(self) -> str:
        return self.text[self.index]

    def at_number(self) -> bool:
        self.skip_separators()
        return self.index < len(self.text) and self.text[self.index] in "+-.0123456789"

    def number(self) -> float:
        self.skip_separators()
        match = _NUMBER_RE.match(self.text, self.index)
        if not match:
            raise GeometryUnsupported("unparseable path data")
        self.index = match.end()
        return float(match.group(0))

    def flag(self) -> float:
        self.skip_separators()
        if self.index < len(self.text) and self.text[self.index] in "01":
            self.index += 1
            return float(self.text[self.index - 1])
        raise GeometryUnsupported("unparseable path data")


class _Polyline:
    def __init__(
        self,
        points: list[Point],
        segments: list[tuple[Point, Point]],
        extremes: list[Point] | None = None,
    ) -> None:
        self.points = points
        self.segments = segments
        # Points plus the axis extremes of any arcs: the true bounding-box inputs.
        self.bounds_points = points + (extremes or [])
        self.start = points[0]
        self.end = segments[-1][1] if segments else points[-1]


# Number of arguments per command for the coordinates we do not need to track.
_ARG_COUNT = {"M": 2, "L": 2, "H": 1, "V": 1, "Z": 0, "A": 7, "Q": 4, "C": 6, "S": 4, "T": 2}


def _arc_extremes(
    start: Point, radius_x: float, radius_y: float, rotation: float,
    large_arc: bool, sweep: bool, end: Point,
) -> list[Point]:
    """Points where an SVG elliptical arc touches its own axis-aligned bounding box."""
    rx, ry = abs(radius_x), abs(radius_y)
    if rx == 0 or ry == 0 or start == end:
        return []
    phi = math.radians(rotation)
    cos_phi, sin_phi = math.cos(phi), math.sin(phi)
    half_dx, half_dy = (start[0] - end[0]) / 2, (start[1] - end[1]) / 2
    x1p = cos_phi * half_dx + sin_phi * half_dy
    y1p = -sin_phi * half_dx + cos_phi * half_dy
    scale = x1p * x1p / (rx * rx) + y1p * y1p / (ry * ry)
    if scale > 1:
        rx, ry = rx * math.sqrt(scale), ry * math.sqrt(scale)
    denominator = rx * rx * y1p * y1p + ry * ry * x1p * x1p
    numerator = rx * rx * ry * ry - denominator
    coefficient = math.sqrt(max(0.0, numerator / denominator))
    if large_arc == sweep:
        coefficient = -coefficient
    cxp = coefficient * rx * y1p / ry
    cyp = -coefficient * ry * x1p / rx
    center_x = cos_phi * cxp - sin_phi * cyp + (start[0] + end[0]) / 2
    center_y = sin_phi * cxp + cos_phi * cyp + (start[1] + end[1]) / 2
    theta1 = math.atan2((y1p - cyp) / ry, (x1p - cxp) / rx)
    theta2 = math.atan2((-y1p - cyp) / ry, (-x1p - cxp) / rx)
    delta = theta2 - theta1
    if sweep and delta < 0:
        delta += 2 * math.pi
    elif not sweep and delta > 0:
        delta -= 2 * math.pi

    theta_x = math.atan2(-ry * sin_phi, rx * cos_phi)
    theta_y = math.atan2(ry * cos_phi, rx * sin_phi)
    points: list[Point] = []
    for base in (theta_x, theta_y):
        for theta in (base, base + math.pi):
            along = (theta - theta1) % (2 * math.pi) if delta >= 0 else (theta1 - theta) % (2 * math.pi)
            if along <= abs(delta):
                points.append(
                    (
                        center_x + rx * math.cos(theta) * cos_phi - ry * math.sin(theta) * sin_phi,
                        center_y + rx * math.cos(theta) * sin_phi + ry * math.sin(theta) * cos_phi,
                    )
                )
    return points


def _parse_path(data: str | None) -> _Polyline:
    """Parse path data; curves and arcs are approximated by their chord.

    Arc axis extremes are collected separately so a path node made only of arcs
    still gets a real bounding box."""
    scanner = _PathScanner(data or "")
    current: Point = (0.0, 0.0)
    subpath_start: Point = (0.0, 0.0)
    points: list[Point] = []
    segments: list[tuple[Point, Point]] = []
    extremes: list[Point] = []
    command: str | None = None

    while not scanner.done():
        if scanner.peek().isalpha():
            command = scanner.peek()
            scanner.index += 1
            if command.upper() not in _ARG_COUNT:
                raise GeometryUnsupported(f"unknown path command {command!r}")
            if not points and command.upper() != "M":
                raise GeometryUnsupported("path data must start with a moveto")
            if command.upper() == "Z":
                if current != subpath_start:
                    segments.append((current, subpath_start))
                    current = subpath_start
                continue
        elif command is None or command.upper() == "Z":
            raise GeometryUnsupported("unparseable path data")

        assert command is not None
        upper, relative = command.upper(), command.islower()
        first_set = True
        while first_set or scanner.at_number():
            ox, oy = current if relative else (0.0, 0.0)
            if upper == "H":
                end = (ox + scanner.number(), current[1])
            elif upper == "V":
                end = (current[0], oy + scanner.number())
            elif upper in ("M", "L", "T"):
                end = (ox + scanner.number(), oy + scanner.number())
            elif upper == "Q" or upper == "S":
                scanner.number()
                scanner.number()
                end = (ox + scanner.number(), oy + scanner.number())
            elif upper == "C":
                for _ in range(4):
                    scanner.number()
                end = (ox + scanner.number(), oy + scanner.number())
            else:  # A
                arc_rx, arc_ry, arc_rotation = scanner.number(), scanner.number(), scanner.number()
                large_arc, sweep = scanner.flag(), scanner.flag()
                end = (ox + scanner.number(), oy + scanner.number())
                extremes.extend(
                    _arc_extremes(current, arc_rx, arc_ry, arc_rotation, bool(large_arc), bool(sweep), end)
                )

            if upper == "M" and first_set:
                subpath_start = end
                points.append(end)
                current = end
                first_set = False
                # Remaining coordinate pairs after a moveto are implicit linetos.
                command = "l" if relative else "L"
                upper = "L"
                if not scanner.at_number():
                    break
                continue
            segments.append((current, end))
            points.append(end)
            current = end
            first_set = False

    if not points:
        raise GeometryUnsupported("empty path data")
    return _Polyline(points, segments, extremes)


def _shape_box(shape: ET.Element) -> Box:
    """Bounding box of a node or boundary shape in its own coordinates."""
    name = _svg_name(shape)
    if name == "rect":
        x, y = _length(shape, "x"), _length(shape, "y")
        width, height = _length(shape, "width"), _length(shape, "height")
        return min(x, x + width), min(y, y + height), max(x, x + width), max(y, y + height)
    if name == "circle":
        cx, cy, r = _length(shape, "cx"), _length(shape, "cy"), abs(_length(shape, "r"))
        return cx - r, cy - r, cx + r, cy + r
    if name == "ellipse":
        cx, cy = _length(shape, "cx"), _length(shape, "cy")
        rx, ry = abs(_length(shape, "rx")), abs(_length(shape, "ry"))
        return cx - rx, cy - ry, cx + rx, cy + ry
    if name == "polygon":
        return _bounds(_parse_points(shape.get("points")))
    if name == "path":
        return _bounds(_parse_path(shape.get("d")).bounds_points)
    raise GeometryUnsupported(f"unsupported shape <{name}>")


def _connector_geometry(shape: ET.Element) -> _Polyline:
    name = _svg_name(shape)
    if name == "line":
        start = (_length(shape, "x1"), _length(shape, "y1"))
        end = (_length(shape, "x2"), _length(shape, "y2"))
        return _Polyline([start, end], [(start, end)])
    if name == "polyline":
        points = _parse_points(shape.get("points"))
        return _Polyline(points, list(zip(points, points[1:])))
    if name == "path":
        return _parse_path(shape.get("d"))
    raise GeometryUnsupported(f"unsupported connector <{name}>")


def _shift_polyline(line: _Polyline, offset: Point) -> _Polyline:
    return _Polyline(
        [_shift_point(p, offset) for p in line.points],
        [(_shift_point(a, offset), _shift_point(b, offset)) for a, b in line.segments],
    )


def _segment_hits_interior(start: Point, end: Point, box: Box) -> bool:
    """True when the segment passes through the open interior of the box."""
    x0, y0, x1, y1 = box
    dx, dy = end[0] - start[0], end[1] - start[1]
    t0, t1 = 0.0, 1.0
    for p, q in (
        (-dx, start[0] - x0),
        (dx, x1 - start[0]),
        (-dy, start[1] - y0),
        (dy, y1 - start[1]),
    ):
        if p == 0:
            if q <= 0:
                return False
            continue
        t = q / p
        if p < 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
        if t0 >= t1:
            return False
    return True


def _endpoint_gap(point: Point, box: Box) -> tuple[str, float]:
    x, y = point
    x0, y0, x1, y1 = box
    if x0 <= x <= x1 and y0 <= y <= y1:
        return "inside", min(x - x0, x1 - x, y - y0, y1 - y)
    return "short", math.hypot(max(x0 - x, 0.0, x - x1), max(y0 - y, 0.0, y - y1))


Ellipse = tuple[float, float, float, float]


def _ellipse_of(shape: ET.Element) -> Ellipse | None:
    """(cx, cy, rx, ry) of a circle or ellipse in its own coordinates, else None."""
    name = _svg_name(shape)
    if name == "circle":
        r = abs(_length(shape, "r"))
        return _length(shape, "cx"), _length(shape, "cy"), r, r
    if name == "ellipse":
        return (
            _length(shape, "cx"),
            _length(shape, "cy"),
            abs(_length(shape, "rx")),
            abs(_length(shape, "ry")),
        )
    return None


def _ellipse_gap(point: Point, ellipse: Ellipse) -> tuple[str, float]:
    """Side and distance of a point relative to the ellipse outline."""
    cx, cy, rx, ry = ellipse
    dx, dy = point[0] - cx, point[1] - cy
    inside = (dx / rx) ** 2 + (dy / ry) ** 2 < 1
    side = "inside" if inside else "short"
    if math.isclose(rx, ry):
        return side, abs(math.hypot(dx, dy) - rx)
    # Nearest outline point in the first quadrant by sampling, then a ternary refinement.
    ax, ay = abs(dx), abs(dy)

    def squared(t: float) -> float:
        return (rx * math.cos(t) - ax) ** 2 + (ry * math.sin(t) - ay) ** 2

    steps = 360
    quarter = math.pi / 2
    best = min(range(steps + 1), key=lambda i: squared(quarter * i / steps))
    low = quarter * max(best - 1, 0) / steps
    high = quarter * min(best + 1, steps) / steps
    for _ in range(60):
        a, b = low + (high - low) / 3, high - (high - low) / 3
        if squared(a) < squared(b):
            high = b
        else:
            low = a
    return side, math.sqrt(squared((low + high) / 2))


def _boxes_overlap(a: Box, b: Box) -> bool:
    return (
        min(a[2], b[2]) - max(a[0], b[0]) > OVERLAP_EPSILON
        and min(a[3], b[3]) - max(a[1], b[1]) > OVERLAP_EPSILON
    )


# --------------------------------------------------------------------------
# Text width estimate
# --------------------------------------------------------------------------


def _css_font_sizes(style_text: str) -> dict[str, float]:
    """Font sizes from simple `.class` and `text` rules; ignores at-rule blocks."""
    css = _strip_css_comments(style_text)
    css = re.sub(r"@[\w-]+[^{;]*\{(?:[^{}]*\{[^{}]*\})*[^{}]*\}", "", css)
    sizes: dict[str, float] = {}
    for selectors, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        size = _declared_size(body)
        if size is None:
            continue
        for selector in selectors.split(","):
            selector = selector.strip()
            simple = re.fullmatch(r"(?:text|tspan)?(\.[\w-]+)", selector)
            if simple:
                sizes[simple.group(1)] = size
            elif selector in ("text", "tspan"):
                sizes["text"] = size
    return sizes


def _css_rules(style_text: str) -> list[tuple[str | None, str | None, dict[str, str]]]:
    """Simple `tag`, `.class`, and `tag.class` rules in source order; at-rule blocks are ignored."""
    css = _strip_css_comments(style_text)
    css = re.sub(r"@[\w-]+[^{;]*\{(?:[^{}]*\{[^{}]*\})*[^{}]*\}", "", css)
    rules: list[tuple[str | None, str | None, dict[str, str]]] = []
    for selectors, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        declarations = _declarations(body)
        for selector in selectors.split(","):
            simple = re.fullmatch(r"([A-Za-z][\w-]*)?(?:\.([\w-]+))?", selector.strip())
            if simple and (simple.group(1) or simple.group(2)):
                rules.append((simple.group(1), simple.group(2), declarations))
    return rules


def _declarations(body: str) -> dict[str, str]:
    """Declarations of one rule or style attribute; `marker` expands to start, mid, and end."""
    result: dict[str, str] = {}
    for declaration in body.split(";"):
        name, separator, value = declaration.partition(":")
        if not separator:
            continue
        name = name.strip().lower()
        value = re.sub(r"\s*!important\s*$", "", value.strip(), flags=re.IGNORECASE)
        if name == "marker":
            for part in ("marker-start", "marker-mid", "marker-end"):
                result[part] = value
        else:
            result[name] = value
    return result


def _resolved_marker(
    element: ET.Element,
    prop: str,
    parents: dict[ET.Element, ET.Element],
    rules: list[tuple[str | None, str | None, dict[str, str]]],
) -> bool:
    """True when the marker property resolves to something other than `none`.

    Precedence per element: attribute, then class rules, then inline style; the
    property is inherited from the nearest ancestor that declares it."""
    current: ET.Element | None = element
    while current is not None:
        value = current.get(prop)
        classes = (current.get("class") or "").split()
        best: tuple[int, int, int] | None = None
        for order, (tag, class_name, declarations) in enumerate(rules):
            if prop not in declarations:
                continue
            if tag and tag != _svg_name(current):
                continue
            if class_name and class_name not in classes:
                continue
            rank = (1 if class_name else 0, 1 if tag else 0, order)
            if best is None or rank > best:
                best, value = rank, declarations[prop]
        inline = _declarations(current.get("style") or "")
        if prop in inline:
            value = inline[prop]
        if value is not None and value.strip().lower() != "inherit":
            return value.strip().lower() not in ("", "none")
        current = parents.get(current)
    return False


def _declared_size(declarations: str) -> float | None:
    """Font size from `font-size: N` or a `font: ... Npx ...` shorthand."""
    match = re.search(r"(?:^|[;\s])font-size\s*:\s*([^;}]+)", declarations)
    if match:
        return _parse_font_size(match.group(1))
    match = re.search(rf"(?:^|[;\s])font\s*:[^;}}]*?(?<![\w.])({NUMBER})px", declarations)
    return _parse_font_size(match.group(1)) if match else None


def _parse_font_size(value: str) -> float | None:
    match = re.fullmatch(rf"\s*({NUMBER})(?:px)?\s*(?:!important)?\s*", value)
    if not match:
        return None
    size = float(match.group(1))
    return size if size > 0 else None


def _font_size(
    text: ET.Element,
    parents: dict[ET.Element, ET.Element],
    css_sizes: dict[str, float],
) -> float:
    current: ET.Element | None = text
    while current is not None:
        size = _declared_font_size(current, css_sizes)
        if size is not None:
            return size
        current = parents.get(current)
    return DEFAULT_FONT_SIZE


def _declared_font_size(element: ET.Element, css_sizes: dict[str, float]) -> float | None:
    style = element.get("style")
    if style:
        size = _declared_size(style)
        if size is not None:
            return size
    for class_name in reversed((element.get("class") or "").split()):
        if f".{class_name}" in css_sizes:
            return css_sizes[f".{class_name}"]
    if _svg_name(element) in ("text", "tspan") and "text" in css_sizes:
        return css_sizes["text"]
    value = element.get("font-size")
    return _parse_font_size(value) if value is not None else None


def _text_lines(text: ET.Element) -> list[str]:
    """Visual lines of a <text>: each <tspan x="..."> starts a new line."""
    lines: list[str] = []
    current = text.text or ""
    for child in text:
        if _svg_name(child) == "tspan" and "x" in child.attrib:
            if current.strip():
                lines.append(current)
            current = ""
        current += _text_of(child) + (child.tail or "")
    if current.strip():
        lines.append(current)
    return [" ".join(line.split()) for line in lines]


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------


def _screen_doctype(data: str | bytes) -> list[str]:
    """Reject DTD internal subsets and entity declarations before the real parse.

    Raises ValueError for them (the CLI exits 2). Returns contract errors for a
    DOCTYPE that points anywhere but the public SVG DTD. Malformed XML is left
    for the main parse to report."""
    errors: list[str] = []

    def start_doctype(name: str, system_id: str | None, public_id: str | None, subset: int) -> None:
        if subset:
            raise ValueError(
                "DOCTYPE with an internal subset is not allowed: entity declarations "
                "can expand without bound"
            )
        if system_id and not system_id.startswith(SVG_DTD_PREFIX):
            errors.append(f"DOCTYPE may only name the public SVG DTD, got {system_id!r}")

    def entity_decl(name: str, *_: object) -> None:
        raise ValueError(f"<!ENTITY {name}> declarations are not allowed")

    parser = expat.ParserCreate()
    parser.StartDoctypeDeclHandler = start_doctype
    parser.EntityDeclHandler = entity_decl
    try:
        parser.Parse(data, True)
    except expat.ExpatError:
        pass
    return errors


def validate_svg(
    data: str | bytes, *, strict_geometry: bool = False
) -> tuple[list[str], list[str], list[str]]:
    """Return (errors, warnings, notes).

    Raises ET.ParseError on malformed XML and ValueError for input that is too
    large or declares a DTD internal subset or entities. With strict_geometry,
    warnings and notes (geometry that could not be checked) become errors."""
    if len(data) > MAX_INPUT_BYTES:
        raise ValueError(f"input is larger than {MAX_INPUT_BYTES} bytes")
    errors: list[str] = _screen_doctype(data)
    root = ET.fromstring(data)
    warnings: list[str] = []
    notes: list[str] = []

    if root.tag != f"{{{SVG_NS}}}svg":
        return errors + [
            f"root element must be <svg> in the {SVG_NS} namespace, got {root.tag!r}"
        ], [], []

    viewbox, viewbox_error = _parse_viewbox(root.get("viewBox"))
    if viewbox_error:
        errors.append(viewbox_error)

    parents = {child: parent for parent in root.iter() for child in parent}
    elements = list(root.iter())
    ids: dict[str, list[ET.Element]] = {}
    for element in elements:
        element_id = element.get("id")
        if element_id:
            ids.setdefault(element_id, []).append(element)

    _check_accessibility(root, errors)
    _check_self_containment(elements, ids, errors)
    for element_id, owners in ids.items():
        if len(owners) > 1:
            errors.append(f"duplicate id {element_id!r} ({len(owners)} elements)")
    _check_layers(root, elements, errors)
    css_rules: list[tuple[str | None, str | None, dict[str, str]]] = []
    for style in root.iter(f"{{{SVG_NS}}}style"):
        css_rules.extend(_css_rules(_text_of(style)))
    model = _check_semantics(root, elements, parents, css_rules, errors)

    _check_geometry(root, parents, viewbox, model, warnings, notes)

    if strict_geometry:
        errors.extend(f"geometry (strict): {warning}" for warning in warnings)
        errors.extend(f"geometry (strict): {note}" for note in notes)
        warnings, notes = [], []
    return errors, warnings, notes


def _check_accessibility(root: ET.Element, errors: list[str]) -> None:
    if root.get("role") != "img":
        errors.append(f"root <svg> must have role=\"img\", got {root.get('role')!r}")

    children = list(root)
    if not children or _svg_name(children[0]) != "title":
        errors.append("<title> must be the first element child of <svg>")
    title = next((c for c in children if _svg_name(c) == "title"), None)
    desc = next((c for c in children if _svg_name(c) == "desc"), None)
    if title is not None and not _text_of(title).strip():
        errors.append("<title> must not be empty")
    if desc is None:
        errors.append("root <svg> needs a <desc> child")
    elif not _text_of(desc).strip():
        errors.append("<desc> must not be empty")

    labelledby = root.get("aria-labelledby")
    if labelledby is None or not labelledby.split():
        errors.append("root <svg> needs aria-labelledby pointing at the <title> and <desc> ids")
        return
    tokens = labelledby.split()
    for label, element in (("title", title), ("desc", desc)):
        if element is None:
            continue
        element_id = element.get("id")
        if not element_id:
            errors.append(f"<{label}> needs an id referenced by aria-labelledby")
        elif element_id not in tokens:
            errors.append(f"aria-labelledby does not reference the <{label}> id {element_id!r}")


def _check_self_containment(
    elements: list[ET.Element], ids: dict[str, list[ET.Element]], errors: list[str]
) -> None:
    def check_urls(text: str, where: str) -> None:
        for match in _URL_RE.finditer(text):
            target = match.group(2).strip()
            if not _LOCAL_URL_RE.match(target):
                errors.append(f"{where}: url({target}) must point to a local #id")
            elif target[1:] not in ids:
                errors.append(f"{where}: url({target}) does not resolve to an id")

    for element in elements:
        name = _local(element.tag) if isinstance(element.tag, str) else ""
        label = f"<{name}>" + (f" #{element.get('id')}" if element.get("id") else "")
        if name in ("script", "foreignObject"):
            errors.append(f"{label} is not allowed in a self-contained SVG")
        if name in ANIMATION_TAGS:
            errors.append(f"{label} is not allowed: animation elements make the SVG non-inert")
        if name == "style":
            if "\\" in _text_of(element):
                errors.append("<style> must not contain CSS escapes (backslash)")
            css = _strip_css_comments(_text_of(element))
            if re.search(r"@import\b", css, re.IGNORECASE):
                errors.append("<style> must not use @import")
            check_urls(css, "<style>")
        for attribute, value in element.attrib.items():
            attribute_name = _local(attribute)
            if attribute_name == "style" and "\\" in value:
                errors.append(f"{label} style must not contain CSS escapes (backslash)")
            if _EVENT_ATTR_RE.match(attribute_name):
                errors.append(f"{label} has event-handler attribute {attribute_name!r}")
            if attribute_name == "href":
                if not value.startswith("#"):
                    errors.append(f"{label} href {value!r} must start with '#'")
                elif value[1:] not in ids:
                    errors.append(f"{label} href {value!r} does not resolve to an id")
            if attribute_name == "aria-labelledby":
                for token in value.split():
                    if token not in ids:
                        errors.append(f"{label} aria-labelledby id {token!r} does not resolve")
            check_urls(value, f"{label} {attribute_name}")


def _check_layers(root: ET.Element, elements: list[ET.Element], errors: list[str]) -> None:
    direct = [child for child in root if "data-layer" in child.attrib]
    for element in elements:
        if element is not root and "data-layer" in element.attrib and element not in direct:
            errors.append(
                f"data-layer {element.get('data-layer')!r} must be a direct child of the root <svg>"
            )
    names = [child.get("data-layer") for child in direct]
    for name in dict.fromkeys(names):
        if name not in LAYERS:
            errors.append(f"unknown data-layer {name!r}; expected {', '.join(LAYERS)}")
        elif names.count(name) > 1:
            errors.append(f"data-layer {name!r} appears {names.count(name)} times; expected once")
    for name in LAYERS:
        if name not in names:
            errors.append(f"missing data-layer {name!r}")
    for child in direct:
        if _svg_name(child) != "g":
            errors.append(f"data-layer {child.get('data-layer')!r} must be a <g> element")
    for child in direct:
        for element in child.iter():
            name = _local(element.tag) if isinstance(element.tag, str) else ""
            if element is not child and name in FORBIDDEN_IN_LAYERS:
                errors.append(
                    f"<{name}> is not allowed inside data-layer {child.get('data-layer')!r}: "
                    "checks and summaries cannot follow its geometry"
                )
    known = [name for name in dict.fromkeys(names) if name in LAYERS]
    if len(known) == len(LAYERS) and tuple(known) != LAYERS:
        errors.append(
            f"data-layer order must be {', '.join(LAYERS)}; found {', '.join(str(n) for n in names)}"
        )


class _Model:
    def __init__(self) -> None:
        self.nodes: dict[str, ET.Element] = {}
        self.boundaries: dict[str, ET.Element] = {}
        self.edges: dict[str, ET.Element] = {}
        self.labels: list[tuple[str, ET.Element]] = []


def _check_semantics(
    root: ET.Element,
    elements: list[ET.Element],
    parents: dict[ET.Element, ET.Element],
    css_rules: list[tuple[str | None, str | None, dict[str, str]]],
    errors: list[str],
) -> _Model:
    model = _Model()
    counts: dict[str, dict[str, int]] = {kind: {} for kind in KIND_LAYER}
    items: list[tuple[str, str, ET.Element]] = []

    def layer_of(element: ET.Element) -> str | None:
        current = element
        while parents.get(current) is not None and parents[current] is not root:
            current = parents[current]
        return current.get("data-layer") if parents.get(current) is root else None

    for element in elements:
        present = [attribute for attribute in KIND_ATTRS if attribute in element.attrib]
        if not present:
            continue
        if len(present) > 1:
            errors.append(f"element carries more than one semantic kind: {', '.join(present)}")
        for attribute in present:
            kind = KIND_ATTRS[attribute]
            value = (element.get(attribute) or "").strip()
            if not value:
                errors.append(f"{attribute} must not be empty")
                continue
            if layer_of(element) != KIND_LAYER[kind]:
                errors.append(f"{kind} {value!r} must be inside the {KIND_LAYER[kind]!r} layer")
            counts[kind][value] = counts[kind].get(value, 0) + 1
            items.append((kind, value, element))
            if kind == "node":
                model.nodes.setdefault(value, element)
            elif kind == "boundary":
                model.boundaries.setdefault(value, element)
            elif kind == "edge":
                model.edges.setdefault(value, element)
            else:
                model.labels.append((value, element))

    for kind in ("node", "boundary", "edge"):
        for value, count in counts[kind].items():
            if count > 1:
                errors.append(f"duplicate {kind} id {value!r} ({count} groups)")
    for value in sorted(set(counts["node"]) & set(counts["boundary"])):
        errors.append(f"id {value!r} is used by both a node and a boundary")

    endpoints = set(model.nodes) | set(model.boundaries)
    for kind, value, element in items:
        if kind in ("node", "boundary"):
            shapes = [e for e in _own_descendants(element) if _svg_name(e) in SHAPE_TAGS]
            if len(shapes) != 1:
                errors.append(
                    f"{kind} {value!r} must contain exactly one shape "
                    f"(rect, ellipse, circle, polygon, or path), found {len(shapes)}"
                )
            if kind == "node" and not any(
                _svg_name(e) == "text" and _text_of(e).strip() for e in _own_descendants(element)
            ):
                errors.append(f"node {value!r} must contain a <text> with visible text")
            parent_id = element.get("data-parent")
            if parent_id is not None and parent_id not in model.boundaries:
                errors.append(f"{kind} {value!r} data-parent {parent_id!r} is not a boundary")
        elif kind == "edge":
            connectors = [e for e in _own_descendants(element) if _svg_name(e) in EDGE_TAGS]
            if len(connectors) != 1:
                errors.append(
                    f"edge {value!r} must contain exactly one path, line, or polyline, "
                    f"found {len(connectors)}"
                )
            elif _resolved_marker(connectors[0], "marker-start", parents, css_rules) and not (
                _resolved_marker(connectors[0], "marker-end", parents, css_rules)
            ):
                errors.append(
                    f"edge {value!r} has marker-start but no marker-end; the arrowhead must sit "
                    "at data-to, so swap data-from and data-to and use marker-end"
                )
            for attribute in ("data-from", "data-to"):
                target = element.get(attribute)
                if target is None or not target.strip():
                    errors.append(f"edge {value!r} needs {attribute}")
                elif target not in endpoints:
                    errors.append(
                        f"edge {value!r} {attribute} {target!r} is not a node or boundary"
                    )
        elif kind == "label":
            if value not in model.edges:
                errors.append(f"label for {value!r} does not resolve to an edge")
            inner = list(_own_descendants(element))
            if not any(_svg_name(e) == "rect" for e in inner):
                errors.append(f"label for {value!r} must contain an opaque mask <rect>")
            if not any(_svg_name(e) == "text" and _text_of(e).strip() for e in inner):
                errors.append(f"label for {value!r} must contain a <text> with visible text")

    parent_of = {
        boundary_id: element.get("data-parent")
        for boundary_id, element in model.boundaries.items()
        if element.get("data-parent") in model.boundaries
    }
    reported: set[str] = set()
    for start in parent_of:
        seen = [start]
        current = parent_of.get(start)
        while current is not None and current not in seen:
            seen.append(current)
            current = parent_of.get(current)
        if current == start and start not in reported:
            reported.update(seen)
            errors.append("data-parent cycle among boundaries: " + " -> ".join(seen + [start]))
    return model


# --------------------------------------------------------------------------
# Geometry warnings
# --------------------------------------------------------------------------


def _check_geometry(
    root: ET.Element,
    parents: dict[ET.Element, ET.Element],
    viewbox: Box | None,
    model: _Model,
    warnings: list[str],
    notes: list[str],
) -> None:
    def note(message: str) -> None:
        if message not in notes:
            notes.append(message)

    def warn(message: str) -> None:
        if message not in warnings:
            warnings.append(message)

    def one_child(group: ET.Element, tags: set[str]) -> ET.Element | None:
        found = [e for e in _own_descendants(group) if _svg_name(e) in tags]
        return found[0] if len(found) == 1 else None

    ellipses: dict[str, Ellipse] = {}

    def shape_geometry(kind: str, item_id: str, group: ET.Element) -> Box | None:
        shape = one_child(group, SHAPE_TAGS)
        if shape is None:
            return None
        try:
            offset = _absolute_offset(shape, parents)
            box = _shift_box(_shape_box(shape), offset)
            ellipse = _ellipse_of(shape)
            if ellipse is not None and ellipse[2] > 0 and ellipse[3] > 0:
                ellipses[item_id] = (
                    ellipse[0] + offset[0], ellipse[1] + offset[1], ellipse[2], ellipse[3]
                )
            return box
        except GeometryUnsupported as problem:
            note(f"geometry skipped for {kind} {item_id!r}: {problem}")
            return None

    node_boxes = {n: b for n, g in model.nodes.items() if (b := shape_geometry("node", n, g))}
    boundary_boxes = {
        n: b for n, g in model.boundaries.items() if (b := shape_geometry("boundary", n, g))
    }
    target_boxes = {**boundary_boxes, **node_boxes}

    edge_lines: dict[str, _Polyline] = {}
    for edge_id, group in model.edges.items():
        connector = one_child(group, EDGE_TAGS)
        if connector is None:
            continue
        try:
            line = _connector_geometry(connector)
            edge_lines[edge_id] = _shift_polyline(line, _absolute_offset(connector, parents))
        except GeometryUnsupported as problem:
            note(f"geometry skipped for edge {edge_id!r}: {problem}")

    mask_boxes: list[tuple[str, Box]] = []
    for edge_id, group in model.labels:
        mask = one_child_rect(group)
        if mask is None:
            continue
        try:
            box = _shift_box(_shape_box(mask), _absolute_offset(mask, parents))
        except GeometryUnsupported as problem:
            note(f"geometry skipped for label of edge {edge_id!r}: {problem}")
            continue
        mask_boxes.append((edge_id, box))

    # Shapes and connectors outside the viewBox.
    if viewbox is not None:
        def outside(box: Box) -> bool:
            return (
                box[0] < viewbox[0] - VIEWBOX_EPSILON
                or box[1] < viewbox[1] - VIEWBOX_EPSILON
                or box[2] > viewbox[2] + VIEWBOX_EPSILON
                or box[3] > viewbox[3] + VIEWBOX_EPSILON
            )

        candidates = (
            [("node", n, b) for n, b in node_boxes.items()]
            + [("boundary", n, b) for n, b in boundary_boxes.items()]
            + [("edge", n, _bounds(line.points)) for n, line in edge_lines.items()]
            + [("label mask for edge", n, b) for n, b in mask_boxes]
        )
        for kind, item_id, box in candidates:
            if outside(box):
                warn(
                    f"{kind} {item_id!r} extends outside the viewBox "
                    f"(bbox {_box_text(box)}, viewBox {_box_text(viewbox)})"
                )

    # Connector endpoints against their nodes.
    endpoint_refs: dict[str, list[tuple[str, str, Point]]] = {}
    for edge_id, line in edge_lines.items():
        group = model.edges[edge_id]
        for role, attribute, point in (
            ("start", "data-from", line.start),
            ("end", "data-to", line.end),
        ):
            target = group.get(attribute)
            box = target_boxes.get(target) if target else None
            if box is None:
                continue
            if target in ellipses:
                kind, distance = _ellipse_gap(point, ellipses[target])
                reference = "the outline of"
            else:
                kind, distance = _endpoint_gap(point, box)
                reference = "the bounding-box edge of"
            if distance > ENDPOINT_TOLERANCE:
                relation = "short of" if kind == "short" else "inside"
                warn(
                    f"edge {edge_id!r} {role} {_point_text(point)} is {_fmt(distance)} units "
                    f"{relation} {reference} {target!r}"
                )
            endpoint_refs.setdefault(target, []).append((edge_id, role, point))

    # Connectors crossing unrelated nodes.
    for edge_id, line in edge_lines.items():
        group = model.edges[edge_id]
        endpoint_ids = {group.get("data-from"), group.get("data-to")}
        for node_id, box in node_boxes.items():
            if node_id in endpoint_ids:
                continue
            inner = (
                box[0] + OBSTACLE_INSET,
                box[1] + OBSTACLE_INSET,
                box[2] - OBSTACLE_INSET,
                box[3] - OBSTACLE_INSET,
            )
            if inner[0] >= inner[2] or inner[1] >= inner[3]:
                continue
            if any(_segment_hits_interior(a, b, inner) for a, b in line.segments):
                warn(f"edge {edge_id!r} passes through node {node_id!r}")

    # Connectors sharing an attachment point.
    for target, refs in endpoint_refs.items():
        for index, (edge_a, role_a, point_a) in enumerate(refs):
            for edge_b, role_b, point_b in refs[index + 1 :]:
                if edge_a != edge_b and math.dist(point_a, point_b) <= SHARED_POINT_TOLERANCE:
                    warn(
                        f"edges {edge_a!r} ({role_a}) and {edge_b!r} ({role_b}) attach at the "
                        f"same point {_point_text(point_a)} on {target!r}"
                    )

    # Label masks.
    for edge_id, mask in mask_boxes:
        for node_id, box in node_boxes.items():
            if _boxes_overlap(mask, box):
                warn(f"label mask for edge {edge_id!r} overlaps node {node_id!r}")
    for index, (edge_a, box_a) in enumerate(mask_boxes):
        for edge_b, box_b in mask_boxes[index + 1 :]:
            if _boxes_overlap(box_a, box_b):
                warn(f"label masks for edges {edge_a!r} and {edge_b!r} overlap")

    # Estimated text overflow.
    css_sizes: dict[str, float] = {}
    for style in root.iter(f"{{{SVG_NS}}}style"):
        css_sizes.update(_css_font_sizes(_text_of(style)))
    for node_id, box in node_boxes.items():
        width = box[2] - box[0]
        for text in model.nodes[node_id].iter(f"{{{SVG_NS}}}text"):
            size = _font_size(text, parents, css_sizes)
            for line in _text_lines(text):
                estimate = len(line) * size * AVERAGE_CHAR_WIDTH_FACTOR
                if estimate > width:
                    shown = line if len(line) <= 40 else line[:37] + "..."
                    warn(
                        f"text {shown!r} in node {node_id!r} is estimated at {_fmt(estimate)} "
                        f"units wide (font-size {_fmt(size)}), wider than the {_fmt(width)}-unit shape"
                    )


def one_child_rect(group: ET.Element) -> ET.Element | None:
    return next((e for e in _own_descendants(group) if _svg_name(e) == "rect"), None)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Geometry warnings are estimates from declared coordinates: connector curves and "
            "arcs are measured by their chord, only translate() is followed, and text width is "
            "an estimate (characters x font-size x "
            f"{AVERAGE_CHAR_WIDTH_FACTOR}), not a measurement. Confirm the result in a render."
        ),
    )
    parser.add_argument("svg", type=Path, help="standalone .svg diagram to check")
    parser.add_argument(
        "--strict-geometry",
        action="store_true",
        help=(
            "treat geometry warnings (including the text-width estimate) and any element "
            "whose geometry could not be checked as errors"
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        with args.svg.open("rb") as handle:
            data = handle.read(MAX_INPUT_BYTES + 1)
    except FileNotFoundError:
        print(f"ERROR: file not found: {args.svg}", file=sys.stderr)
        return 2
    except OSError as error:
        print(f"ERROR: cannot read {args.svg}: {error}", file=sys.stderr)
        return 2
    if len(data) > MAX_INPUT_BYTES:
        print(f"ERROR: {args.svg} is larger than {MAX_INPUT_BYTES} bytes", file=sys.stderr)
        return 2
    try:
        errors, warnings, notes = validate_svg(data, strict_geometry=args.strict_geometry)
    except (ET.ParseError, ValueError) as error:
        print(f"ERROR: cannot parse {args.svg}: {error}", file=sys.stderr)
        return 2

    for note in notes:
        print(f"NOTE: {note}")
    for warning in warnings:
        print(f"WARN: {warning}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"FAIL: {len(errors)} issue(s)", file=sys.stderr)
        return 1

    print(f"PASS: {args.svg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
