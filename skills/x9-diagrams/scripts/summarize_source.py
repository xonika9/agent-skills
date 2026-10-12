#!/usr/bin/env python3
"""Summarize an existing diagram source into a compact semantic digest.

Supports Excalidraw scenes, draw.io files, and semantic SVG (standalone or inline
in HTML). The source is untrusted data: nothing is fetched, executed, rendered,
or followed; links, embeds, and scripts are only counted.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import html
import html.entities
import json
import math
import re
import sys
import urllib.parse
import zlib
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape as xml_escape
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterator

from check_svg import _css_rules, _resolved_property


MAX_FILE_BYTES = 20 * 1024 * 1024
MAX_ELEMENTS = 100_000
NODE_BUDGET = 9
EDGE_BUDGET = 12
DEFAULT_MAX_ROWS = 40
HUB_LIMIT = 3
LIST_LIMIT = 12
MAX_LABEL_CHARS = 1000
MD_LABEL_CHARS = 100

FORMATS = ("excalidraw", "drawio", "svg", "html", "mermaid")
MERMAID_MESSAGE = (
    "Mermaid source is already text: read it directly and check it with its "
    "renderer; this script does not summarize it"
)
DISCARD_ORDER = (
    "deleted",
    "freedraw",
    "image",
    "images",
    "embeds",
    "polygons",
    "unknown",
    "element_links",
    "dangling_edges",
    "scripts",
    "foreign_objects",
    "external_refs",
    "event_handlers",
    "orphan_labels",
)
MARKDOWN_SPECIAL = re.compile(r"([\\|*_`\[\]<>#&~])")
MARKDOWN_AUTOLINK = re.compile(r"://|\b(www)\.", re.IGNORECASE)  # group 1: www
ENTITY_DECLARATION = re.compile(r"<!\s*ENTITY", re.IGNORECASE)
DOCTYPE_START = re.compile(r"<!\s*DOCTYPE", re.IGNORECASE)
_QUOTED = r"""(?:"[^"]*"|'[^']*')"""
# A DOCTYPE without an internal subset: name, then optional PUBLIC/SYSTEM ids, then ">".
PLAIN_DOCTYPE = re.compile(
    rf"<!DOCTYPE\s+[\w:.\-]+(?:\s+PUBLIC\s+{_QUOTED}\s+{_QUOTED}|\s+SYSTEM\s+{_QUOTED})?\s*>"
)
XML_PREDEFINED_ENTITIES = {"amp", "lt", "gt", "quot", "apos"}
HTML_ENTITY = re.compile(r"&([A-Za-z][A-Za-z0-9]*);")
DRAWIO_CONTENT = re.compile(r"\s*<(?:mxfile|mxGraphModel)\b")
XML_DECLARATION = re.compile(r"^\s*<\?xml[^>]*\?>")


class SourceError(Exception):
    """The input cannot be summarized; the CLI reports it and exits 2."""


@dataclass
class Node:
    id: str
    label: str = ""
    kind: str = "rect"
    parent: str | None = None
    container: bool = False
    role: str | None = None
    layer: str | None = None


@dataclass
class Edge:
    id: str
    source: str | None
    target: str | None
    label: str = ""
    style: str = "solid"
    directed: str = "forward"  # forward | backward | both | none
    dangling: bool = False


@dataclass
class Scene:
    name: str
    bounds: dict[str, float] | None = None
    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    layers: list[dict[str, Any]] = field(default_factory=list)
    clusters: list[dict[str, Any]] = field(default_factory=list)
    discarded: dict[str, int] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    semantic: bool | None = None
    raw_counts: dict[str, int] | None = None
    source_kind: str | None = None

    def discard(self, key: str, count: int = 1) -> None:
        if count > 0:
            self.discarded[key] = self.discarded.get(key, 0) + count


# ---------------------------------------------------------------- shared helpers


def clean_label(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    text = value.strip()
    if len(text) > MAX_LABEL_CHARS:
        text = text[: MAX_LABEL_CHARS - 1] + "…"
    return text


def _number(value: Any) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:  # an integer too large for a float
        return False


def _round(value: float) -> float | int:
    rounded = round(value, 1)
    return int(rounded) if rounded == int(rounded) else rounded


def _identifier(value: Any) -> str | None:
    """Return the value only when it is a usable string identifier."""
    return value if isinstance(value, str) and value else None


def _bounds(
    rects: list[tuple[float, float, float, float]],
) -> dict[str, float] | None:
    try:
        boxes = [tuple(float(v) for v in r) for r in rects]
    except OverflowError:
        return None
    boxes = [r for r in boxes if all(math.isfinite(v) for v in r)]
    if not boxes:
        return None
    min_x = min(r[0] for r in boxes)
    min_y = min(r[1] for r in boxes)
    max_x = max(r[0] + r[2] for r in boxes)
    max_y = max(r[1] + r[3] for r in boxes)
    result = (min_x, min_y, max_x - min_x, max_y - min_y)
    if not all(math.isfinite(v) for v in result):
        return None  # coordinates too large to describe
    return dict(zip(("x", "y", "width", "height"), map(_round, result)))


def local_name(tag: Any) -> str:
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def check_xml_declarations(text: str, what: str) -> None:
    """Allow a plain DOCTYPE; refuse an internal subset or any entity declaration."""
    unsafe = ENTITY_DECLARATION.search(text) is not None or any(
        PLAIN_DOCTYPE.match(text, match.start()) is None
        for match in DOCTYPE_START.finditer(text)
    )
    if unsafe:
        raise SourceError(
            f"{what} contains an internal <!DOCTYPE ... [ subset or an <!ENTITY "
            "declaration; refusing to parse (entity expansion risk)"
        )


def html_entities_to_text(text: str) -> str:
    """Replace HTML named entities (other than the XML five) with their characters."""

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if name in XML_PREDEFINED_ENTITIES:
            return match.group(0)
        value = html.entities.html5.get(name + ";")
        if value is None:
            return match.group(0)
        return xml_escape(value, {'"': "&quot;", "'": "&apos;"})

    return HTML_ENTITY.sub(replace, text)


def parse_xml(text: str, what: str) -> ET.Element:
    check_xml_declarations(text, what)
    try:
        return ET.fromstring(XML_DECLARATION.sub("", text, count=1))
    except ET.ParseError as error:
        raise SourceError(f"{what} is not well-formed XML: {error}") from None
    except RecursionError:
        raise SourceError(f"{what} is nested too deeply") from None


def check_element_count(count: int, what: str) -> None:
    if count > MAX_ELEMENTS:
        raise SourceError(
            f"{what} has {count} elements; the limit is {MAX_ELEMENTS}"
        )


# -------------------------------------------------------------------- Excalidraw

EXCALIDRAW_SHAPES = {"rectangle": "rect", "ellipse": "ellipse", "diamond": "rhombus"}
EXCALIDRAW_FRAMES = {"frame", "magicframe"}
EXCALIDRAW_DROPPED = {
    "freedraw": "freedraw",
    "image": "image",
    "embeddable": "embeds",
    "iframe": "embeds",
}


def _arrowheads(directed_start: bool, directed_end: bool) -> str:
    if directed_start and directed_end:
        return "both"
    if directed_end:
        return "forward"
    if directed_start:
        return "backward"
    return "none"


def parse_excalidraw(data: Any) -> list[Scene]:
    if not isinstance(data, dict) or not isinstance(data.get("elements"), list):
        raise SourceError("not an Excalidraw scene: top-level `elements` array is missing")
    elements = data["elements"]
    check_element_count(len(elements), "Excalidraw scene")

    scene = Scene(name="scene")
    live: list[dict[str, Any]] = []
    for element in elements:
        if not isinstance(element, dict):
            scene.discard("unknown")
        elif element.get("isDeleted"):
            scene.discard("deleted")
        elif not isinstance(element.get("id"), str) or not isinstance(
            element.get("type"), str
        ):
            scene.discard("unknown")
        else:
            live.append(element)
    by_id = {element["id"]: element for element in live}

    rects = []
    for element in live:
        if all(_number(element.get(key)) for key in ("x", "y", "width", "height")):
            rects.append(
                (element["x"], element["y"], element["width"], element["height"])
            )
        if isinstance(element.get("link"), str) and element["link"].strip():
            scene.discard("element_links")
    scene.bounds = _bounds(rects)
    if rects and scene.bounds is None:
        scene.notes.append("canvas bounds are unknown: coordinates are too large to measure")

    def text_of(element: dict[str, Any]) -> str:
        value = element.get("originalText")
        if not isinstance(value, str):
            value = element.get("text")
        return clean_label(value)

    bound_labels: dict[str, list[str]] = defaultdict(list)
    folded: set[str] = set()
    for element in live:
        if element["type"] != "text":
            continue
        container_id = _identifier(element.get("containerId"))
        container = by_id.get(container_id) if container_id else None
        if container is not None and (
            container["type"] in EXCALIDRAW_SHAPES or container["type"] == "arrow"
        ):
            folded.add(element["id"])
            text = text_of(element)
            if text:
                bound_labels[container["id"]].append(text)

    frame_ids = {e["id"] for e in live if e["type"] in EXCALIDRAW_FRAMES}
    groups: dict[str, list[str]] = {}

    def register_groups(element: dict[str, Any]) -> None:
        group_ids = element.get("groupIds")
        if isinstance(group_ids, list):
            for group_id in group_ids:
                if isinstance(group_id, str):
                    groups.setdefault(group_id, []).append(element["id"])

    def parent_of(element: dict[str, Any]) -> str | None:
        frame_id = _identifier(element.get("frameId"))
        return frame_id if frame_id in frame_ids and frame_id != element["id"] else None

    for element in live:
        element_id, element_type = element["id"], element["type"]
        if element_id in folded:
            continue
        if element_type in EXCALIDRAW_SHAPES:
            scene.nodes.append(
                Node(
                    element_id,
                    " ".join(bound_labels.get(element_id, [])),
                    EXCALIDRAW_SHAPES[element_type],
                    parent_of(element),
                )
            )
        elif element_type in EXCALIDRAW_FRAMES:
            name = element.get("name")
            scene.nodes.append(
                Node(
                    element_id,
                    clean_label(name) if isinstance(name, str) else "",
                    "frame",
                    parent_of(element),
                    container=True,
                )
            )
        elif element_type == "text":
            scene.nodes.append(
                Node(element_id, text_of(element), "text", parent_of(element))
            )
        elif element_type in ("arrow", "line"):
            if element_type == "line" and element.get("polygon") is True:
                scene.discard("polygons")
                continue
            start = element.get("startBinding")
            end = element.get("endBinding")
            default_end = "arrow" if element_type == "arrow" else None
            style = element.get("strokeStyle")
            scene.edges.append(
                Edge(
                    element_id,
                    _identifier(start.get("elementId")) if isinstance(start, dict) else None,
                    _identifier(end.get("elementId")) if isinstance(end, dict) else None,
                    " ".join(bound_labels.get(element_id, [])),
                    style if style in ("dashed", "dotted") else "solid",
                    _arrowheads(
                        bool(element.get("startArrowhead")),
                        bool(element.get("endArrowhead", default_end)),
                    ),
                )
            )
        elif element_type in EXCALIDRAW_DROPPED:
            scene.discard(EXCALIDRAW_DROPPED[element_type])
            continue
        else:
            scene.discard("unknown")
            continue
        register_groups(element)

    scene.clusters = [
        {"id": group_id, "members": members}
        for group_id, members in groups.items()
        if len(members) >= 2
    ]
    return [scene]


# ----------------------------------------------------------------------- draw.io


def parse_style(style: str | None) -> tuple[list[str], dict[str, str]]:
    flags: list[str] = []
    props: dict[str, str] = {}
    for token in (style or "").split(";"):
        token = token.strip()
        if not token:
            continue
        if "=" in token:
            key, value = token.split("=", 1)
            props[key.strip()] = value.strip()
        else:
            flags.append(token.lower())
    return flags, props


DRAWIO_BARE_SHAPES = {
    "triangle", "hexagon", "parallelogram", "cloud", "trapezoid", "step", "note",
    "card", "document", "process", "actor", "line", "label", "group", "image",
}


def drawio_kind(flags: list[str], props: dict[str, str]) -> str:
    shape = props.get("shape", "").lower()
    first = flags[0] if flags else ""
    for name in ("swimlane", "ellipse", "rhombus", "text"):
        if name in flags[:1] or shape == name:
            return name
    if "swimlane" in flags:
        return "swimlane"
    if shape.startswith("cylinder") or first.startswith("cylinder"):
        return "store"
    if shape:
        return re.sub(r"[^\w.\-]", "", shape)[:40] or "rect"
    if first in DRAWIO_BARE_SHAPES:
        return first
    return "rect"


def html_to_text(value: Any) -> str:
    if not isinstance(value, str) or not value:
        return ""
    text = re.sub(r"<br\s*/?>|</(?:div|p|li|tr|h[1-6])\s*>", " ", value, flags=re.I)
    text = re.sub(r"<[^>]*>", "", text)
    text = html.unescape(text)
    return clean_label(re.sub(r"\s+", " ", text))


def inflate_drawio(payload: str) -> str:
    payload = payload.strip()
    if payload.startswith("<"):
        return payload
    if payload[:3].upper() == "%3C":
        return urllib.parse.unquote(payload)
    try:
        raw = base64.b64decode(payload)
        decoder = zlib.decompressobj(-15)
        out = decoder.decompress(raw, MAX_FILE_BYTES + 1)
    except (binascii.Error, zlib.error, ValueError):
        raise SourceError(
            "draw.io page content is neither XML nor valid compressed data"
        ) from None
    if len(out) > MAX_FILE_BYTES or decoder.unconsumed_tail:
        raise SourceError(
            f"draw.io page expands beyond {MAX_FILE_BYTES} bytes; refusing to inflate"
        )
    text = urllib.parse.unquote(out.decode("utf-8", errors="replace")).strip()
    if not text.startswith("<"):
        raise SourceError(
            "draw.io page content is neither XML nor valid compressed data"
        )
    return text


def _float(value: str | None) -> float | None:
    try:
        number = float(value) if value is not None else None
    except ValueError:
        return None
    return number if number is not None and math.isfinite(number) else None


@dataclass
class _Cell:
    id: str
    value: str
    style: str
    vertex: bool
    edge: bool
    parent: str | None
    source: str | None
    target: str | None
    link: bool
    geometry: tuple[float, float, float | None, float | None] | None


def _read_cells(model: ET.Element) -> list[_Cell]:
    root = next((c for c in model if local_name(c.tag) == "root"), None)
    if root is None:
        return []
    check_element_count(len(root), "draw.io page")
    cells = []
    for child in root:
        tag = local_name(child.tag)
        if tag == "mxCell":
            cell, wrapper = child, None
        elif tag in ("object", "UserObject"):
            cell = next((c for c in child if local_name(c.tag) == "mxCell"), None)
            wrapper = child
            if cell is None:
                continue
        else:
            continue
        cell_id = (wrapper if wrapper is not None else cell).get("id")
        if not cell_id:
            continue
        value = (
            wrapper.get("label", cell.get("value", ""))
            if wrapper is not None
            else cell.get("value", "")
        )
        geometry_el = next((c for c in cell if local_name(c.tag) == "mxGeometry"), None)
        geometry = None
        if geometry_el is not None:
            x, y = _float(geometry_el.get("x")), _float(geometry_el.get("y"))
            geometry = (
                x or 0.0,
                y or 0.0,
                _float(geometry_el.get("width")),
                _float(geometry_el.get("height")),
            )
        cells.append(
            _Cell(
                cell_id,
                value,
                cell.get("style", ""),
                cell.get("vertex") == "1",
                cell.get("edge") == "1",
                cell.get("parent"),
                cell.get("source"),
                cell.get("target"),
                bool(wrapper is not None and (wrapper.get("link") or "").strip()),
                geometry,
            )
        )
    return cells


def parse_drawio_page(name: str, model: ET.Element) -> Scene:
    scene = Scene(name=name)
    cells = _read_cells(model)
    if not cells:
        scene.notes.append("page has no cells")
        return scene
    by_id: dict[str, _Cell] = {}
    for cell in cells:
        by_id.setdefault(cell.id, cell)

    edge_ids = {c.id for c in cells if c.edge}
    root_ids = {c.id for c in cells if c.parent is None} or {"0"}
    layer_cells = [
        c for c in cells
        if not c.vertex and not c.edge and c.parent in root_ids
    ]
    layer_ids = {c.id for c in layer_cells}
    scene.layers = [
        {"id": c.id, "name": html_to_text(c.value) or c.id, "nodes": 0}
        for c in layer_cells
    ]
    layer_by_id = {layer["id"]: layer for layer in scene.layers}
    for cell in cells:
        if cell.link:
            scene.discard("element_links")
        if (
            not cell.vertex
            and not cell.edge
            and cell.id not in layer_ids
            and cell.parent is not None
        ):
            scene.discard("unknown")

    label_cells = [c for c in cells if c.vertex and c.parent in edge_ids]
    vertices = [c for c in cells if c.vertex and c.parent not in edge_ids]
    vertex_ids = {c.id for c in vertices}
    parents = {c.parent for c in vertices if c.parent in vertex_ids}

    def layer_of(cell: _Cell) -> str | None:
        seen: set[str] = set()
        current: _Cell | None = cell
        while current is not None and current.id not in seen:
            seen.add(current.id)
            if current.parent in layer_ids:
                return current.parent
            current = by_id.get(current.parent) if current.parent else None
        return None

    for cell in vertices:
        flags, props = parse_style(cell.style)
        kind = drawio_kind(flags, props)
        container = (
            cell.id in parents
            or props.get("container") == "1"
            or kind in ("swimlane", "group")
        )
        layer = layer_of(cell)
        if layer in layer_by_id:
            layer_by_id[layer]["nodes"] += 1
        scene.nodes.append(
            Node(
                cell.id,
                html_to_text(cell.value),
                kind,
                cell.parent if cell.parent in vertex_ids else None,
                container,
                layer=layer,
            )
        )

    edge_labels: dict[str, list[str]] = defaultdict(list)
    for cell in label_cells:
        text = html_to_text(cell.value)
        if text and cell.parent:
            edge_labels[cell.parent].append(text)
    for cell in cells:
        if not cell.edge:
            continue
        flags, props = parse_style(cell.style)
        end_head = props.get("endArrow", "classic") != "none"
        start_head = props.get("startArrow", "none") != "none"
        style = "solid"
        if props.get("dashed") == "1":
            pattern = [_float(p) for p in props.get("dashPattern", "").split()]
            style = (
                "dotted"
                if pattern and all(p is not None and p <= 2 for p in pattern)
                else "dashed"
            )
        parts = [p for p in [html_to_text(cell.value), *edge_labels.get(cell.id, [])] if p]
        scene.edges.append(
            Edge(
                cell.id,
                cell.source,
                cell.target,
                clean_label(" / ".join(parts)),
                style,
                _arrowheads(start_head, end_head),
            )
        )

    absolute: list[tuple[float, float, float, float]] = []
    for cell in vertices:
        if cell.geometry is None or cell.geometry[2] is None or cell.geometry[3] is None:
            continue
        x, y = cell.geometry[0], cell.geometry[1]
        seen = {cell.id}
        parent = by_id.get(cell.parent) if cell.parent else None
        while parent is not None and parent.id in vertex_ids and parent.id not in seen:
            seen.add(parent.id)
            if parent.geometry is not None:
                x += parent.geometry[0]
                y += parent.geometry[1]
            parent = by_id.get(parent.parent) if parent.parent else None
        absolute.append((x, y, cell.geometry[2], cell.geometry[3]))
    scene.bounds = _bounds(absolute)
    return scene


def parse_drawio(text: str) -> list[Scene]:
    root = parse_xml(text, "draw.io file")
    tag = local_name(root.tag)
    if tag == "mxGraphModel":
        return [parse_drawio_page("page", root)]
    if tag != "mxfile":
        raise SourceError(
            f"not a draw.io file: root element is <{tag}>, expected <mxfile>"
        )
    diagrams = [c for c in root if local_name(c.tag) == "diagram"]
    if not diagrams:
        raise SourceError("draw.io file has no <diagram> pages")
    check_element_count(sum(1 for _ in root.iter()), "draw.io file")
    scenes = []
    for index, diagram in enumerate(diagrams, start=1):
        name = diagram.get("name") or f"page {index}"
        model = next((c for c in diagram if local_name(c.tag) == "mxGraphModel"), None)
        if model is None:
            payload = (diagram.text or "").strip()
            if not payload:
                empty = Scene(name=name)
                empty.notes.append("page has no content")
                scenes.append(empty)
                continue
            model = parse_xml(inflate_drawio(payload), f"draw.io page {index}")
            if local_name(model.tag) != "mxGraphModel":
                raise SourceError(
                    f"draw.io page {index} does not contain an <mxGraphModel>"
                )
        scenes.append(parse_drawio_page(name, model))
    return scenes


# --------------------------------------------------------------------------- SVG

SVG_SHAPES = {"rect": "rect", "circle": "ellipse", "ellipse": "ellipse",
              "polygon": "polygon", "path": "path"}
SVG_RAW_TAGS = ("rect", "circle", "ellipse", "polygon", "line", "polyline",
                "path", "text", "g", "image")
SEMANTIC_ATTRIBUTES = ("data-node", "data-boundary", "data-edge", "data-label-for")


def extract_inline_svg(text: str) -> tuple[str, int]:
    """Return the first top-level <svg>…</svg> text and the count of later ones."""
    token = re.compile(r"<svg\b|</svg\s*>", re.IGNORECASE)
    start = None
    depth = 0
    extra = 0
    end = 0
    for match in token.finditer(text):
        opening = not match.group(0).startswith("</")
        if opening:
            if depth == 0:
                if start is None:
                    start = match.start()
                elif end:
                    extra += 1
            depth += 1
        elif depth > 0:
            depth -= 1
            if depth == 0 and start is not None and not end:
                end = match.end()
    if start is None:
        raise SourceError("no inline <svg> element found")
    if not end:
        raise SourceError("the inline <svg> element is never closed")
    return text[start:end], extra


def _walk_own(group: ET.Element, foreign: set[int]) -> Iterator[ET.Element]:
    """Yield group and its descendants in document order, skipping nested semantic groups."""
    stack = [group]
    while stack:
        element = stack.pop()
        if element is not group and id(element) in foreign:
            continue
        yield element
        stack.extend(reversed(list(element)))


def _own_text(group: ET.Element, foreign: set[int]) -> str:
    pieces = []
    for element in _walk_own(group, foreign):
        if local_name(element.tag) == "text":
            words = [s.strip() for s in element.itertext() if s.strip()]
            if words:
                pieces.append(" ".join(words))
    if not pieces:
        for child in group:
            if local_name(child.tag) == "title":
                title = " ".join(s.strip() for s in child.itertext() if s.strip())
                if title:
                    pieces.append(title)
    return clean_label(" ".join(pieces))


def _svg_bounds(root: ET.Element) -> dict[str, float] | None:
    parts = re.split(r"[\s,]+", root.get("viewBox", "").strip())
    values = [_float(p) for p in parts]
    if len(values) == 4 and all(v is not None for v in values):
        return {
            "x": _round(values[0]), "y": _round(values[1]),
            "width": _round(values[2]), "height": _round(values[3]),
        }
    sizes = []
    for key in ("width", "height"):
        match = re.fullmatch(r"\s*([0-9.]+)(?:px)?\s*", root.get(key, ""))
        sizes.append(_float(match.group(1)) if match else None)
    if all(s is not None for s in sizes):
        return {"x": 0, "y": 0, "width": _round(sizes[0]), "height": _round(sizes[1])}
    return None


def _svg_discards(elements: list[ET.Element]) -> dict[str, int]:
    found: dict[str, int] = defaultdict(int)
    for element in elements:
        tag = local_name(element.tag)
        if tag == "script":
            found["scripts"] += 1
        elif tag == "foreignObject":
            found["foreign_objects"] += 1
        elif tag == "image":
            found["images"] += 1
        for key, value in element.attrib.items():
            name = local_name(key)
            if name.startswith("on") and name != "on":
                found["event_handlers"] += 1
            elif name == "href" and not value.strip().startswith("#"):
                found["external_refs"] += 1
    return dict(found)


def _drawio_from_svg(
    root: ET.Element, elements: list[ET.Element], content: str, notes: list[str]
) -> list[Scene]:
    """Summarize the draw.io model a draw.io SVG export carries in `content`."""
    scenes = parse_drawio(content.strip())
    drawing = _svg_discards(elements)
    unread = ", ".join(f"{k.replace('_', ' ')} {v}" for k, v in drawing.items())
    for scene in scenes:
        scene.source_kind = "draw.io SVG export (model read from the root content attribute)"
        scene.notes[:0] = notes
    scenes[0].notes.append(
        "the rendered SVG drawing was not read; only the embedded draw.io model was"
        + (f" (the drawing contains: {unread})" if unread else "")
    )
    return scenes


def parse_svg(text: str, *, from_html: bool = False) -> list[Scene]:
    notes = []
    if from_html:
        text, extra = extract_inline_svg(text)
        text = html_entities_to_text(text)
        if extra:
            notes.append(f"{extra} further top-level <svg> element(s) in the HTML were not read")
    root = parse_xml(text, "SVG")
    if local_name(root.tag) != "svg":
        raise SourceError(f"not an SVG document: root element is <{local_name(root.tag)}>")
    elements = list(root.iter())
    check_element_count(len(elements), "SVG")

    embedded = root.get("content", "")
    if DRAWIO_CONTENT.match(embedded):
        return _drawio_from_svg(root, elements, embedded, notes)

    scene = Scene(name="svg", bounds=_svg_bounds(root), notes=notes)
    for child in root:
        if local_name(child.tag) == "title":
            scene.name = clean_label(" ".join(child.itertext())) or scene.name
            break

    for key, count in _svg_discards(elements).items():
        scene.discard(key, count)

    semantic_elements = [
        e for e in elements if any(a in e.attrib for a in SEMANTIC_ATTRIBUTES)
    ]
    scene.semantic = bool(semantic_elements)
    counts: dict[str, int] = defaultdict(int)
    for element in elements:
        tag = local_name(element.tag)
        if tag in SVG_RAW_TAGS:
            counts[tag] += 1
    scene.raw_counts = {tag: counts[tag] for tag in SVG_RAW_TAGS if counts[tag]}
    if not scene.semantic:
        scene.notes.append(
            "no semantic markup (data-node / data-boundary / data-edge): the "
            "diagram model must be inferred from geometry and text"
        )
        return [scene]

    foreign = {id(e) for e in semantic_elements}
    parents = {child: parent for parent in elements for child in parent}
    css = []
    for style in elements:
        if local_name(style.tag) == "style":
            css.extend(_css_rules("".join(style.itertext())))
    edge_ids = set()
    label_texts: dict[str, list[str]] = defaultdict(list)
    for element in semantic_elements:
        if "data-label-for" in element.attrib:
            label_texts[element.get("data-label-for", "")].append(
                _own_text(element, foreign)
            )

    seen_ids: set[str] = set()
    duplicates = 0
    for element in semantic_elements:
        for attribute, container in (("data-node", False), ("data-boundary", True)):
            if attribute not in element.attrib:
                continue
            node_id = element.get(attribute, "").strip()
            if not node_id:
                scene.notes.append(f"{attribute} with an empty id was skipped")
                continue
            if node_id in seen_ids:
                duplicates += 1
            seen_ids.add(node_id)
            kind = "rect"
            for inner in _walk_own(element, foreign):
                shape = SVG_SHAPES.get(local_name(inner.tag))
                if shape:
                    kind = shape
                    break
            parent = element.get("data-parent", "").strip() or None
            scene.nodes.append(
                Node(
                    node_id,
                    _own_text(element, foreign),
                    kind,
                    parent,
                    container,
                    role=element.get("data-role", "").strip() or None,
                )
            )
        if "data-edge" in element.attrib:
            edge_id = element.get("data-edge", "").strip()
            if not edge_id:
                scene.notes.append("data-edge with an empty id was skipped")
                continue
            edge_ids.add(edge_id)
            start = end = False
            dashes = None
            for inner in _walk_own(element, foreign):
                if local_name(inner.tag) not in ("path", "line", "polyline"):
                    continue
                first = _resolved_property(inner, "marker-start", parents, css)
                last = _resolved_property(inner, "marker-end", parents, css)
                start = start or (first is not None and first.lower() not in ("", "none"))
                end = end or (last is not None and last.lower() not in ("", "none"))
                dash = _resolved_property(inner, "stroke-dasharray", parents, css)
                if dash is not None and dash.lower() not in ("", "none", "0") and dashes is None:
                    dashes = dash
            style = "solid"
            if dashes is not None:
                values = [_float(v) for v in re.split(r"[\s,]+", dashes.strip()) if v]
                style = (
                    "dotted"
                    if values and all(v is not None and v <= 2 for v in values)
                    else "dashed"
                )
            scene.edges.append(
                Edge(
                    edge_id,
                    element.get("data-from", "").strip() or None,
                    element.get("data-to", "").strip() or None,
                    "",
                    style,
                    _arrowheads(start, end),
                )
            )

    for edge in scene.edges:
        texts = [t for t in label_texts.get(edge.id, []) if t]
        edge.label = clean_label(" / ".join(texts))
    orphans = sum(len(v) for k, v in label_texts.items() if k not in edge_ids)
    scene.discard("orphan_labels", orphans)
    if duplicates:
        scene.notes.append(f"{duplicates} duplicate semantic id(s)")
    return [scene]


# ---------------------------------------------------------------------- analysis


def finalize(scene: Scene) -> None:
    ids = {node.id for node in scene.nodes}
    unknown_parents = 0
    for node in scene.nodes:
        if node.parent is not None and (node.parent not in ids or node.parent == node.id):
            unknown_parents += 1
            node.parent = None
    if unknown_parents:
        scene.notes.append(f"{unknown_parents} node(s) named an unknown parent")
    dangling = 0
    for edge in scene.edges:
        edge.dangling = edge.source not in ids or edge.target not in ids
        dangling += edge.dangling
    scene.discard("dangling_edges", dangling)


def is_note(node: Node) -> bool:
    """A draw.io note: listed like standalone text, never a budgeted node."""
    return re.fullmatch(r"note\d*", node.kind) is not None


def analyze(scene: Scene) -> dict[str, Any]:
    nodes = {node.id: node for node in scene.nodes}
    incoming: dict[str, int] = defaultdict(int)
    outgoing: dict[str, int] = defaultdict(int)
    undirected: dict[str, int] = defaultdict(int)
    arcs: list[tuple[str, str]] = []
    for edge in scene.edges:
        if edge.dangling:
            continue
        source, target = edge.source, edge.target
        if edge.directed == "none":
            undirected[source] += 1
            undirected[target] += 1
            continue
        pairs = {
            "forward": [(source, target)],
            "backward": [(target, source)],
            "both": [(source, target), (target, source)],
        }[edge.directed]
        for tail, head in pairs:
            outgoing[tail] += 1
            incoming[head] += 1
            arcs.append((tail, head))

    def degree(node_id: str) -> int:
        return incoming[node_id] + outgoing[node_id] + undirected[node_id]

    remaining = {node_id: incoming[node_id] for node_id in nodes}
    successors: dict[str, list[str]] = defaultdict(list)
    for tail, head in arcs:
        successors[tail].append(head)
    ready = [node_id for node_id, count in remaining.items() if count == 0]
    removed = 0
    while ready:
        current = ready.pop()
        removed += 1
        for head in successors[current]:
            remaining[head] -= 1
            if remaining[head] == 0:
                ready.append(head)
    has_cycle = removed < len(nodes)

    depth = 0
    for node in scene.nodes:
        level, seen, current = 0, {node.id}, node
        while current.parent is not None and current.parent not in seen:
            seen.add(current.parent)
            current = nodes[current.parent]
            level += 1
        depth = max(depth, level)

    def ref(node: Node) -> dict[str, str]:
        return {"id": node.id, "label": node.label}

    kinds: dict[str, int] = defaultdict(int)
    for node in scene.nodes:
        kinds[node.kind] += 1
    leaf_nodes = [
        n for n in scene.nodes if not n.container and n.kind != "text" and not is_note(n)
    ]
    structural = [n for n in scene.nodes if not is_note(n)]
    hubs = sorted(
        (n for n in structural if degree(n.id) > 0),
        key=lambda n: -degree(n.id),
    )[:HUB_LIMIT]
    members: dict[str, list[Node]] = defaultdict(list)
    for node in scene.nodes:
        if node.parent is not None:
            members[node.parent].append(node)
    return {
        "counts": {
            "nodes": sum(1 for n in scene.nodes if not n.container),
            "text_nodes": sum(1 for n in scene.nodes if n.kind == "text"),
            "notes": sum(1 for n in scene.nodes if is_note(n)),
            "containers": sum(1 for n in scene.nodes if n.container),
            "edges": len(scene.edges),
            "labeled_edges": sum(1 for e in scene.edges if e.label),
            "dangling_edges": sum(1 for e in scene.edges if e.dangling),
        },
        "kinds": dict(sorted(kinds.items(), key=lambda kv: (-kv[1], kv[0]))),
        "containment_depth": depth,
        "has_cycle": has_cycle,
        "budget": {
            "nodes": {
                "count": len(leaf_nodes),
                "limit": NODE_BUDGET,
                "exceeded": len(leaf_nodes) > NODE_BUDGET,
            },
            "edges": {
                "count": len(scene.edges),
                "limit": EDGE_BUDGET,
                "exceeded": len(scene.edges) > EDGE_BUDGET,
            },
        },
        "hubs": [{**ref(n), "degree": degree(n.id)} for n in hubs],
        "entry_points": [
            ref(n) for n in structural if incoming[n.id] == 0 and outgoing[n.id] > 0
        ],
        "terminals": [
            ref(n) for n in structural if outgoing[n.id] == 0 and incoming[n.id] > 0
        ],
        "unconnected": [ref(n) for n in leaf_nodes if degree(n.id) == 0],
        "container_members": [
            {**ref(n), "members": [ref(m) for m in members[n.id]]}
            for n in scene.nodes
            if n.container
        ],
        "degrees": {
            n.id: {
                "in": incoming[n.id],
                "out": outgoing[n.id],
                "undirected": undirected[n.id],
            }
            for n in scene.nodes
        },
    }


def scene_to_dict(scene: Scene, index: int) -> dict[str, Any]:
    metrics = analyze(scene)
    degrees = metrics.pop("degrees")
    labels = {n.id: n.label for n in scene.nodes}
    nodes = [{**asdict(n), **{f"{k}_degree": v for k, v in degrees[n.id].items()}}
             for n in scene.nodes]
    edges = [
        {
            **asdict(e),
            "source_label": labels.get(e.source, ""),
            "target_label": labels.get(e.target, ""),
            "source_resolved": e.source in labels,
            "target_resolved": e.target in labels,
        }
        for e in scene.edges
    ]
    return {
        "index": index,
        "name": scene.name,
        "bounds": scene.bounds,
        "semantic": scene.semantic,
        "source_kind": scene.source_kind,
        "raw_counts": scene.raw_counts,
        "metrics": metrics,
        "layers": scene.layers,
        "clusters": scene.clusters,
        "discarded": {
            **{k: scene.discarded[k] for k in DISCARD_ORDER if k in scene.discarded},
            # a produced key missing from DISCARD_ORDER must still be reported
            **{k: v for k, v in sorted(scene.discarded.items()) if k not in DISCARD_ORDER},
        },
        "notes": scene.notes,
        "nodes": nodes,
        "edges": edges,
    }


# --------------------------------------------------------------------- rendering


def md(value: Any, limit: int = MD_LABEL_CHARS) -> str:
    text = re.sub(r"[\x00-\x1f\x7f\s]+", " ", str(value if value is not None else "")).strip()
    if len(text) > limit:
        text = text[: limit - 1] + "…"
    text = MARKDOWN_SPECIAL.sub(r"\\\1", text)
    return MARKDOWN_AUTOLINK.sub(
        lambda m: "\\://" if m.group(1) is None else m.group(1) + "\\.", text
    )


def _ref(item: dict[str, Any]) -> str:
    label = item.get("label") or ""
    return f"{md(label)} ({md(item['id'])})" if label else md(item["id"])


def _list(items: list[dict[str, Any]], extra: str = "") -> str:
    if not items:
        return "none"
    shown = ", ".join(_ref(i) + (extra.format(**i) if extra else "") for i in items[:LIST_LIMIT])
    if len(items) > LIST_LIMIT:
        shown += f", … {len(items) - LIST_LIMIT} more"
    return shown


def _table(headers: list[str], rows: list[list[str]], max_rows: int) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(" --- " for _ in headers) + "|"]
    lines += ["| " + " | ".join(row) + " |" for row in rows[:max_rows]]
    if len(rows) > max_rows:
        lines += ["", f"… {len(rows) - max_rows} more"]
    return lines


def _budget(entry: dict[str, Any], name: str) -> str:
    state = "OVER" if entry["exceeded"] else "ok"
    return f"{name} {entry['count']}/{entry['limit']} {state}"


def render_scene(scene: dict[str, Any], total: int, fmt: str, max_rows: int) -> list[str]:
    word = "Page" if fmt == "drawio" or scene.get("source_kind") else "Scene"
    heading = f"{word} {scene['index']} of {total}: " if total > 1 else f"{word}: "
    lines = [f"## {heading}{md(scene['name'])}", ""]
    metrics = scene["metrics"]
    counts = metrics["counts"]
    bounds = scene["bounds"]
    if scene.get("source_kind"):
        lines.append(f"- Source kind: {md(scene['source_kind'], 200)}")
    lines.append(
        "- Canvas: "
        + (
            f"{bounds['width']} × {bounds['height']} at ({bounds['x']}, {bounds['y']})"
            if bounds
            else "unknown"
        )
    )
    if scene["semantic"] is False:
        lines.append(
            "- Semantic markup: none. The model must be inferred from geometry and text."
        )
        raw = scene["raw_counts"] or {}
        lines.append(
            "- Raw elements: "
            + (", ".join(f"{k} {v}" for k, v in raw.items()) or "none")
        )
    else:
        if scene["semantic"]:
            lines.append("- Semantic markup: yes")
        notes_count = counts.get("notes", 0)
        lines.append(
            f"- Nodes: {counts['nodes']} (standalone text {counts['text_nodes']}"
            + (f", notes {notes_count}" if notes_count else "")
            + ") · "
            f"containers: {counts['containers']} · edges: {counts['edges']} "
            f"(labeled {counts['labeled_edges']}, dangling {counts['dangling_edges']})"
        )
        kinds = ", ".join(f"{md(k)} {v}" for k, v in metrics["kinds"].items())
        lines.append(f"- Shape kinds: {kinds or 'none'}")
        lines.append(f"- Containment depth: {metrics['containment_depth']}")
        lines.append(f"- Directed cycle: {'yes' if metrics['has_cycle'] else 'no'}")
        budget = metrics["budget"]
        lines.append(
            f"- Budget: {_budget(budget['nodes'], 'nodes')}, "
            f"{_budget(budget['edges'], 'edges')} "
            "(nodes exclude containers, standalone text, and notes)"
        )
        lines.append("- Hubs: " + _list(metrics["hubs"], " [{degree}]"))
        lines.append("- Entry points: " + _list(metrics["entry_points"]))
        lines.append("- Terminals: " + _list(metrics["terminals"]))
        lines.append("- Unconnected: " + _list(metrics["unconnected"]))
        if len(scene["layers"]) > 1:
            lines.append(
                "- Layers: "
                + ", ".join(f"{md(l['name'])} (nodes {l['nodes']})" for l in scene["layers"][:LIST_LIMIT])
            )
        if scene["clusters"]:
            labels = {n["id"]: n["label"] for n in scene["nodes"]}
            labels.update({e["id"]: e["label"] for e in scene["edges"]})
            clusters = [
                f"{md(c['id'])}: "
                + _list([{"id": m, "label": labels.get(m, "")} for m in c["members"]])
                for c in scene["clusters"][:LIST_LIMIT]
            ]
            lines.append("- Groups: " + "; ".join(clusters))
        for container in metrics["container_members"][:LIST_LIMIT]:
            lines.append(
                f"- Container {_ref(container)}: " + _list(container["members"])
            )
        if len(metrics["container_members"]) > LIST_LIMIT:
            lines.append(f"- … {len(metrics['container_members']) - LIST_LIMIT} more containers")
    discarded = scene["discarded"]
    lines.append(
        "- Discarded: "
        + (", ".join(f"{k.replace('_', ' ')} {v}" for k, v in discarded.items()) or "none")
    )
    for note in scene["notes"]:
        lines.append(f"- Note: {md(note, 300)}")

    if scene["semantic"] is not False and scene["nodes"]:
        lines += ["", "### Nodes", ""]
        rows = []
        for n in scene["nodes"]:
            kind = md(n["kind"]) + (" (container)" if n["container"] else "")
            if n["role"]:
                kind += f" ({md(n['role'], 30)})"
            rows.append(
                [md(n["id"]), md(n["label"]) or "—", kind, md(n["parent"]) or "—",
                 str(n["in_degree"]), str(n["out_degree"])]
            )
        lines += _table(["id", "label", "kind", "parent", "in", "out"], rows, max_rows)
    if scene["semantic"] is not False and scene["edges"]:
        lines += ["", "### Edges", ""]
        rows = []
        for e in scene["edges"]:
            def end(key: str) -> str:
                if e[f"{key}_resolved"]:
                    return md(e[f"{key}_label"] or e[key])
                return f"? ({md(e[key])})" if e[key] else "?"

            rows.append(
                [end("source"), end("target"), md(e["label"]) or "—", e["style"], e["directed"]]
            )
        lines += _table(["source", "target", "label", "style", "directed"], rows, max_rows)
    return lines


def render_markdown(digest: dict[str, Any], max_rows: int) -> str:
    scenes = digest["scenes"]
    lines = [
        f"# Diagram digest: {md(digest['source'], 200)}",
        "",
        f"Format: {digest['format']}"
        + (f" ({md(digest['source_kind'], 200)})" if digest.get("source_kind") else "")
        + f" · scenes: {len(scenes)}",
        "",
    ]
    for scene in scenes:
        lines += render_scene(scene, len(scenes), digest["format"], max_rows)
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


# --------------------------------------------------------------------------- CLI


def detect_format(path: Path) -> str:
    name = path.name.lower()
    if name.endswith((".excalidraw", ".excalidraw.json")):
        return "excalidraw"
    if name.endswith((".drawio", ".drawio.xml", ".xml", ".dio")):
        return "drawio"
    if name.endswith(".svg"):
        return "svg"
    if name.endswith((".html", ".htm")):
        return "html"
    if name.endswith((".mmd", ".mermaid", ".md")):
        return "mermaid"
    raise SourceError(
        f"cannot determine the format of {path.name!r} from its extension; "
        f"pass --format {{{','.join(FORMATS)}}}"
    )


def read_source(path: Path) -> str:
    try:
        size = path.stat().st_size
        if size > MAX_FILE_BYTES:
            raise SourceError(
                f"{path.name} is {size} bytes; the limit is {MAX_FILE_BYTES}"
            )
        with path.open("rb") as handle:
            raw = handle.read(MAX_FILE_BYTES + 1)
    except FileNotFoundError:
        raise SourceError(f"file not found: {path}") from None
    except OSError as error:
        raise SourceError(f"cannot read {path}: {error.strerror or error}") from None
    if len(raw) > MAX_FILE_BYTES:
        raise SourceError(f"{path.name} exceeds {MAX_FILE_BYTES} bytes")
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise SourceError(f"{path.name} is not valid UTF-8") from None


def summarize(path: Path, fmt: str | None = None) -> dict[str, Any]:
    fmt = fmt or detect_format(path)
    if fmt == "mermaid":
        raise SourceError(MERMAID_MESSAGE)
    text = read_source(path)
    try:
        if fmt == "excalidraw":
            try:
                data = json.loads(text)
            except (ValueError, RecursionError) as error:  # includes JSONDecodeError
                raise SourceError(f"cannot parse {path.name} as JSON: {error}") from None
            scenes = parse_excalidraw(data)
        elif fmt == "drawio":
            scenes = parse_drawio(text)
        elif fmt in ("svg", "html"):
            scenes = parse_svg(text, from_html=fmt == "html")
        else:
            raise SourceError(f"unsupported format: {fmt}")
        for scene in scenes:
            finalize(scene)
        rendered = [scene_to_dict(scene, i) for i, scene in enumerate(scenes, start=1)]
    except (ValueError, TypeError, OverflowError, RecursionError) as error:
        raise SourceError(
            f"{path.name} is malformed and cannot be summarized "
            f"({type(error).__name__}: {error})"
        ) from None
    kinds = {scene.source_kind for scene in scenes if scene.source_kind}
    return {
        "source": path.name,
        "format": fmt,
        "source_kind": next(iter(kinds)) if len(kinds) == 1 else None,
        "limits": {
            "max_file_bytes": MAX_FILE_BYTES,
            "max_elements": MAX_ELEMENTS,
            "node_budget": NODE_BUDGET,
            "edge_budget": EDGE_BUDGET,
        },
        "scenes": rendered,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument(
        "--format",
        choices=FORMATS,
        help="override the format chosen from the file extension",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit the full intermediate representation instead of Markdown",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=DEFAULT_MAX_ROWS,
        help=f"rows per table before truncation (default: {DEFAULT_MAX_ROWS})",
    )
    args = parser.parse_args(argv)
    if args.max_rows < 1:
        parser.error("--max-rows must be at least 1")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        digest = summarize(args.source, args.format)
    except SourceError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(digest, ensure_ascii=False, indent=2))
    else:
        sys.stdout.write(render_markdown(digest, args.max_rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
