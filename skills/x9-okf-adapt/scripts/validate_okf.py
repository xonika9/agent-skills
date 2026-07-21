#!/usr/bin/env python3
"""Validate OKF v0.1 metadata and optional pre-edit body inventory."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from okf_yaml import inspect_yaml

BOM = b"\xef\xbb\xbf"
REQUIRED = {"type", "title", "description", "tags", "timestamp"}
DEFAULT_TYPES = {"Dossier", "Research Note", "Analysis", "Plan", "Playbook", "Reference"}
DEFAULT_EXCLUDES = {
    "raw", "transcripts", "summaries", "artifacts", "archive", "node_modules",
    ".git", ".obsidian", "dist", "build", "vendor",
}
EXCLUDED_FILES = {"AGENTS.md", "CLAUDE.md", "GEMINI.md", "README.md"}
TAG_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
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
        return None, raw, bom, "missing"
    end = next((i for i, line in enumerate(lines[1:], 1) if line.rstrip(b"\r\n") == b"---"), None)
    if end is None:
        return None, raw, bom, "unclosed"
    header = b"".join(lines[1:end]).decode("utf-8", errors="strict")
    body = b"".join(lines[end + 1:])
    return header, body, bom, None


def strict_yaml(header: str):
    result, error = inspect_yaml(header)
    return (None, None, error) if error else (result["value"], result["top_scalars"], None)


def line_endings(data: bytes):
    crlf = data.count(b"\r\n")
    return {"crlf": crlf, "lf": data.count(b"\n") - crlf, "cr": data.count(b"\r") - crlf}


def validate_fields(fields: dict, catalog: set[str], raw_scalars: dict):
    issues = []
    missing = sorted(REQUIRED - set(fields))
    if missing:
        issues.append(f"missing fields: {', '.join(missing)}")
    for key in ("type", "title", "description", "timestamp"):
        if key in fields and (not isinstance(fields[key], str) or not fields[key].strip()):
            issues.append(f"{key} must be a non-empty string")
    if isinstance(fields.get("description"), str) and "\n" in fields["description"]:
        issues.append("description must be one line")
    if isinstance(fields.get("type"), str) and fields["type"] not in catalog:
        issues.append(f"type outside catalog: {fields['type']}")
    tags = fields.get("tags")
    if tags is not None:
        if not isinstance(tags, list) or not 2 <= len(tags) <= 5:
            issues.append("tags must be a list of 2-5 values")
        elif len(tags) != len(set(tags)) or any(not isinstance(tag, str) or not TAG_RE.fullmatch(tag) for tag in tags):
            issues.append("tags must be unique English kebab-case strings")
    timestamp = fields.get("timestamp")
    raw_timestamp = raw_scalars.get("timestamp", timestamp)
    if isinstance(timestamp, str) and isinstance(raw_timestamp, str):
        try:
            parsed = datetime.fromisoformat(raw_timestamp.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                raise ValueError
        except ValueError:
            issues.append("timestamp must be ISO 8601 with timezone")
    return issues


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--missing", action="store_true")
    parser.add_argument("--inventory", type=Path)
    parser.add_argument("--types")
    parser.add_argument("--exclude", nargs="*", default=[])
    parser.add_argument("--include-readme", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        raise SystemExit(f"not a directory: {root}")
    catalog = set(args.types.split(",")) if args.types else DEFAULT_TYPES
    inventory = json.loads(args.inventory.read_text()) if args.inventory else None
    records = inventory.get("files", {}) if inventory else {}
    problems = []
    descriptions = defaultdict(list)
    type_counts = Counter()
    worklist = []
    seen = set()

    selected = candidates(root, DEFAULT_EXCLUDES | set(args.exclude), args.include_readme)
    for path in selected:
        rel = path.relative_to(root).as_posix()
        seen.add(rel)
        data = path.read_bytes()
        try:
            header, body, bom, split_error = split_document(data)
        except UnicodeDecodeError as exc:
            problems.append((rel, f"frontmatter is not UTF-8: {exc}"))
            continue
        if split_error:
            worklist.append(rel)
            problems.append((rel, split_error))
            continue
        fields, raw_scalars, yaml_error = strict_yaml(header)
        if yaml_error:
            worklist.append(rel)
            problems.append((rel, yaml_error))
            continue
        issues = validate_fields(fields, catalog, raw_scalars)
        if issues:
            worklist.append(rel)
            problems.extend((rel, issue) for issue in issues)
        else:
            descriptions[fields["description"]].append(rel)
            type_counts[fields["type"]] += 1
        if inventory:
            before = records.get(rel)
            if before is None:
                problems.append((rel, "missing from pre-edit inventory"))
            else:
                current = {
                    "body_sha256": hashlib.sha256(body).hexdigest(),
                    "bom": bom,
                    "line_endings": line_endings(body),
                }
                for key, value in current.items():
                    if before.get(key) != value:
                        problems.append((rel, f"body {key} changed"))

    if inventory:
        for rel in sorted(set(records) - seen):
            problems.append((rel, "file missing after pre-edit inventory"))

    for description, paths in descriptions.items():
        if len(paths) > 1:
            problems.append((", ".join(paths), f"duplicate description: {description}"))

    if args.missing:
        for rel in sorted(set(worklist)):
            print(rel)
        raise SystemExit(0)

    for rel, issue in problems:
        print(f"FAIL {rel}: {issue}")
    print(f"checked: {len(selected)}  problems: {len(problems)}")
    for kind, count in type_counts.most_common():
        print(f"  {count:4d}  {kind}")
    raise SystemExit(1 if problems else 0)


if __name__ == "__main__":
    main()
