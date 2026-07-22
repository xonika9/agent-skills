#!/usr/bin/env python3
"""Inventory Markdown bodies and deterministically insert/repair OKF headers."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
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
SEMANTIC_FIELDS = ("type", "title", "description", "tags")
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


def parsed_header(header: bytes):
    if not header:
        return {}
    try:
        parsed, error = inspect_yaml(header.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise ValueError(f"existing frontmatter is not UTF-8: {exc}") from None
    if error:
        raise ValueError(error)
    return parsed["value"]


def valid_timestamp(value):
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.tzinfo is not None
    except ValueError:
        return False


def valid_core_value(key: str, value, catalog: set[str]):
    if key in {"title", "description"}:
        return isinstance(value, str) and bool(value.strip()) and (key != "description" or "\n" not in value and "\r" not in value)
    if key == "type":
        return isinstance(value, str) and value in catalog
    if key == "tags":
        return (
            isinstance(value, list)
            and 2 <= len(value) <= 5
            and len(value) == len(set(value))
            and all(isinstance(tag, str) and TAG_RE.fullmatch(tag) for tag in value)
        )
    if key == "timestamp":
        return valid_timestamp(value)
    return False


def merge_existing_meta(
    meta: dict,
    header: bytes,
    catalog: set[str],
    replace_existing: bool,
    operation_timestamp: str,
):
    merged = dict(meta)
    preserved = []
    if not header:
        return merged, preserved
    existing = parsed_header(header)
    for key in SEMANTIC_FIELDS:
        value = existing.get(key)
        if not replace_existing and valid_core_value(key, value, catalog) and merged[key] != value:
            merged[key] = value
            preserved.append(key)
    meaning_changed = any(existing.get(key) != merged[key] for key in SEMANTIC_FIELDS)
    existing_timestamp = existing.get("timestamp")
    if valid_timestamp(existing_timestamp):
        if meaning_changed:
            merged["timestamp"] = operation_timestamp
        elif merged["timestamp"] != existing_timestamp:
            merged["timestamp"] = existing_timestamp
            preserved.append("timestamp")
    return merged, preserved


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
    if not valid_timestamp(meta["timestamp"]):
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


def source_timestamp(root: Path, path: Path, header: bytes):
    if header:
        existing = parsed_header(header).get("timestamp")
        if valid_timestamp(existing):
            return existing
    try:
        repo = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False,
        )
        repo_root = Path(repo.stdout.strip()).resolve() if repo.returncode == 0 else None
        rel = path.resolve().relative_to(repo_root).as_posix() if repo_root else None
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "log", "-1", "--format=%cI", "--", rel],
            capture_output=True,
            text=True,
            check=False,
        ) if repo_root and rel else None
        candidate = proc.stdout.strip() if proc else ""
        if proc and proc.returncode == 0 and valid_timestamp(candidate):
            return candidate
    except (FileNotFoundError, ValueError):
        pass
    return datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(timespec="seconds")


def inventory(root: Path, excludes: set[str], include_readme: bool = False):
    files = {}
    for path in candidates(root, excludes, include_readme):
        data = path.read_bytes()
        header, body, bom, had_header = split_document(data)
        files[path.relative_to(root).as_posix()] = {
            "file_sha256": hashlib.sha256(data).hexdigest(),
            "body_sha256": hashlib.sha256(body).hexdigest(),
            "bom": bom,
            "line_endings": line_endings(body),
            "had_frontmatter": had_header,
            "suggested_timestamp": source_timestamp(root, path, header),
        }
    return {"version": 3, "root": str(root), "files": files}


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
    parser.add_argument("--replace-existing-metadata", action="store_true")
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
    operation_timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    pending = []
    preserved_by_file = {}
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
        try:
            effective_meta, preserved = merge_existing_meta(
                meta,
                existing_header,
                catalog,
                args.replace_existing_metadata,
                operation_timestamp,
            )
            validate_manifest_meta(effective_meta, catalog)
        except ValueError as exc:
            raise SystemExit(f"cannot merge existing metadata for {rel}: {exc}") from None
        if preserved:
            preserved_by_file[rel] = preserved
        output = (BOM if bom else b"") + header_bytes(effective_meta, preferred_eol(body, existing_header), existing_header) + body
        if output != data:
            pending.append((rel, path, output))

    for rel, path, output in pending:
        if not args.dry_run:
            path.write_bytes(output)
        print(("would update" if args.dry_run else "updated") + f": {rel}")
    for rel, keys in preserved_by_file.items():
        print(f"preserved existing metadata: {rel} ({', '.join(keys)})")
    print(f"files changed: {len(pending)}")


if __name__ == "__main__":
    main()
