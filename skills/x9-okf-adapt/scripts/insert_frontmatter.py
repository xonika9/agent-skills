#!/usr/bin/env python3
"""Inventory Markdown bodies and deterministically insert/repair OKF headers."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

from okf_yaml import inspect_yaml

BOM = b"\xef\xbb\xbf"
DEFAULT_EXCLUDES = {
    "raw", "transcripts", "summaries", "artifacts", "archive", "node_modules",
    ".git", ".obsidian", "dist", "build", "vendor",
}
EXCLUDED_FILES = {"AGENTS.md", "CLAUDE.md", "GEMINI.md", "README.md"}
REQUIRED = ("type", "title", "description", "tags", "timestamp")
TAG_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
DEFAULT_TYPES = {"Dossier", "Research Note", "Analysis", "Plan", "Playbook", "Reference"}


def candidates(root: Path, excludes: set[str], include_readme: bool = False):
    return sorted(
        path for path in root.rglob("*.md")
        if (path.name not in EXCLUDED_FILES or include_readme and path.name == "README.md")
        and not path.name.startswith(".")
        and not any(part.startswith(".") or part in excludes for part in path.relative_to(root).parts[:-1])
    )


def split_document(data: bytes):
    bom = data.startswith(BOM)
    raw = data[len(BOM):] if bom else data
    lines = raw.splitlines(keepends=True)
    if not lines or lines[0].rstrip(b"\r\n") != b"---":
        return b"", raw, bom, False
    end = next((i for i, line in enumerate(lines[1:], 1) if line.rstrip(b"\r\n") == b"---"), None)
    if end is None:
        raise ValueError("unclosed existing frontmatter")
    return b"".join(lines[1:end]), b"".join(lines[end + 1:]), bom, True


def line_endings(data: bytes):
    crlf = data.count(b"\r\n")
    return {"crlf": crlf, "lf": data.count(b"\n") - crlf, "cr": data.count(b"\r") - crlf}


def preferred_eol(data: bytes, fallback: bytes = b""):
    counts = line_endings(data)
    if not any(counts.values()):
        return preferred_eol(fallback) if fallback else b"\n"
    dominant = max(counts, key=counts.get)
    return {"crlf": b"\r\n", "lf": b"\n", "cr": b"\r"}[dominant]


def quote(value: str):
    return "'" + value.replace("'", "''") + "'"


def preserved_unknown_fields(header: bytes):
    """Keep raw top-level blocks whose keys are outside the OKF core."""
    if not header:
        return b""
    try:
        parsed, error = inspect_yaml(header.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise ValueError(f"existing frontmatter is not UTF-8: {exc}") from None
    if error:
        raise ValueError(error)
    lines = header.splitlines(keepends=True)
    starts = [(item["line"], item["key"]) for item in parsed["top_keys"]]
    kept = lines[: starts[0][0]] if starts else lines
    for position, (start, key) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        if key not in REQUIRED:
            kept.extend(lines[start:end])
    return b"".join(kept)


def normalize_eol(data: bytes, eol: bytes):
    if not data:
        return data
    terminated = data.endswith((b"\n", b"\r"))
    output = eol.join(data.splitlines())
    return output + eol if terminated else output


def validate_manifest_meta(meta: dict, catalog: set[str]):
    if not isinstance(meta, dict):
        raise ValueError("manifest metadata must be an object")
    missing = [key for key in REQUIRED if key not in meta]
    if missing:
        raise ValueError(f"manifest missing fields: {', '.join(missing)}")
    for key in ("type", "title", "description", "timestamp"):
        if not isinstance(meta[key], str) or not meta[key].strip():
            raise ValueError(f"manifest {key} must be a non-empty string")
    if "\n" in meta["description"] or "\r" in meta["description"]:
        raise ValueError("manifest description must be one line")
    if meta["type"] not in catalog:
        raise ValueError(f"manifest type outside catalog: {meta['type']}")
    tags = meta["tags"]
    if not isinstance(tags, list) or not 2 <= len(tags) <= 5:
        raise ValueError("manifest tags must be a list of 2-5 values")
    if len(tags) != len(set(tags)) or any(not isinstance(tag, str) or not TAG_RE.fullmatch(tag) for tag in tags):
        raise ValueError("manifest tags must be unique English kebab-case strings")
    try:
        parsed = datetime.fromisoformat(meta["timestamp"].replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError
    except ValueError:
        raise ValueError("manifest timestamp must be ISO 8601 with timezone") from None


def header_bytes(meta: dict, eol: bytes, existing_header: bytes = b""):
    lines = [
        "---", f"type: {quote(meta['type'])}", f"title: {quote(meta['title'])}",
        f"description: {quote(meta['description'])}", "tags:",
        *[f"  - {quote(tag)}" for tag in meta["tags"]],
        f"timestamp: {quote(meta['timestamp'])}",
    ]
    output = eol.join(line.encode("utf-8") for line in lines) + eol
    unknown = normalize_eol(preserved_unknown_fields(existing_header), eol)
    if unknown:
        output += unknown
        if not unknown.endswith((b"\n", b"\r")):
            output += eol
    return output + b"---" + eol


def inventory(root: Path, excludes: set[str], include_readme: bool = False):
    files = {}
    for path in candidates(root, excludes, include_readme):
        data = path.read_bytes()
        _, body, bom, had_header = split_document(data)
        files[path.relative_to(root).as_posix()] = {
            "file_sha256": hashlib.sha256(data).hexdigest(),
            "body_sha256": hashlib.sha256(body).hexdigest(),
            "bom": bom,
            "line_endings": line_endings(body),
            "had_frontmatter": had_header,
        }
    return {"version": 2, "root": str(root), "files": files}


def load_manifest(path: Path):
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return {item["path"]: {k: v for k, v in item.items() if k not in {"path", "confidence", "basis"}} for item in raw}
    if isinstance(raw, dict) and "files" in raw:
        return raw["files"]
    if isinstance(raw, dict):
        return raw
    raise ValueError("manifest must be an object, a files object, or a list with path fields")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--inventory-out", type=Path)
    action.add_argument("--manifest", type=Path)
    parser.add_argument("--inventory", type=Path)
    parser.add_argument("--exclude", nargs="*", default=[])
    parser.add_argument("--include-readme", action="store_true")
    parser.add_argument("--types")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    excludes = DEFAULT_EXCLUDES | set(args.exclude)
    catalog = set(args.types.split(",")) if args.types else DEFAULT_TYPES
    if args.inventory_out:
        args.inventory_out.write_text(json.dumps(inventory(root, excludes, args.include_readme), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"inventory: {args.inventory_out}")
        return
    if not args.inventory:
        raise SystemExit("--inventory is required when applying a manifest")
    before = json.loads(args.inventory.read_text(encoding="utf-8")).get("files", {})
    manifest = load_manifest(args.manifest)
    pending = []
    for rel, meta in manifest.items():
        try:
            validate_manifest_meta(meta, catalog)
        except ValueError as exc:
            raise SystemExit(f"invalid manifest metadata for {rel}: {exc}") from None
        if rel not in before:
            raise SystemExit(f"manifest path absent from inventory: {rel}")
        if "file_sha256" not in before[rel]:
            raise SystemExit(f"inventory lacks full-file hash; recreate it before applying: {rel}")
        path = (root / rel).resolve()
        try:
            path.relative_to(root)
        except ValueError:
            raise SystemExit(f"manifest path escapes root: {rel}")
        data = path.read_bytes()
        existing_header, body, bom, _ = split_document(data)
        if bom != before[rel]["bom"]:
            raise SystemExit(f"BOM changed since inventory: {rel}")
        current_hash = hashlib.sha256(body).hexdigest()
        if current_hash != before[rel]["body_sha256"]:
            raise SystemExit(f"body changed since inventory: {rel}")
        if hashlib.sha256(data).hexdigest() != before[rel]["file_sha256"]:
            raise SystemExit(f"frontmatter changed since inventory: {rel}")
        output = (BOM if bom else b"") + header_bytes(meta, preferred_eol(body, existing_header), existing_header) + body
        if output != data:
            pending.append((rel, path, output))

    for rel, path, output in pending:
        if not args.dry_run:
            path.write_bytes(output)
        print(("would update" if args.dry_run else "updated") + f": {rel}")
    print(f"files changed: {len(pending)}")


if __name__ == "__main__":
    main()
