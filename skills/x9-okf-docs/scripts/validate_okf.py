#!/usr/bin/env python3
"""Check x9 OKF metadata: type, title, description, and tags are required."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from okf_rules import (
    line_endings,
    load_scope,
    markdown_files,
    nfc,
    parse_headers,
    partition,
    resolve_named,
    split_document,
    validate_fields,
    validate_reserved,
)


def load_records(path: Path):
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SystemExit(f"cannot read inventory: {exc}") from None
    files = raw.get("files") if isinstance(raw, dict) else None
    if not isinstance(files, dict) or any(not isinstance(record, dict) for record in files.values()):
        raise SystemExit("unsupported inventory; recreate it with insert_frontmatter.py --inventory-out")
    return {nfc(rel): record for rel, record in files.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--paths", nargs="+", metavar="PATH", help="check only these documents")
    parser.add_argument("--missing", action="store_true", help="list documents that need metadata work")
    parser.add_argument("--inventory", type=Path, help="also confirm bodies match this pre-edit inventory")
    parser.add_argument("--exclude", nargs="*", default=[])
    parser.add_argument("--include-readme", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.is_dir():
        raise SystemExit(f"not a directory: {root}")
    scope = load_scope(root, args.exclude, args.include_readme)
    files = markdown_files(scope)
    if args.paths:
        files = {rel: files[rel] for rel in resolve_named(files, args.paths, root)}
    concepts, reserved = partition(files)
    records = load_records(args.inventory) if args.inventory else None

    problems, warnings, worklist = [], [], []
    descriptions = defaultdict(list)
    headed = []
    for rel, path in concepts.items():
        data = path.read_bytes()
        try:
            header, body, bom, split_error = split_document(data)
        except UnicodeDecodeError as exc:
            problems.append((rel, f"frontmatter is not UTF-8: {exc}"))
            worklist.append(rel)
            continue
        if split_error:
            problems.append((rel, "no frontmatter" if split_error == "missing" else split_error))
            worklist.append(rel)
        else:
            headed.append((rel, header))
        if records is not None:
            before = records.get(rel)
            if before is None:
                warnings.append((rel, "new since the inventory, so its body was not compared"))
            else:
                current = {
                    "body_sha256": hashlib.sha256(body).hexdigest(),
                    "bom": bom,
                    "line_endings": line_endings(body),
                }
                for key, value in current.items():
                    if before.get(key) != value:
                        problems.append((rel, f"body changed since the inventory ({key})"))

    for (rel, _), (result, error) in zip(headed, parse_headers([header for _, header in headed])):
        issues = [error] if error else validate_fields(result["value"])
        problems.extend((rel, issue) for issue in issues)
        if issues:
            worklist.append(rel)
        elif isinstance(result["value"].get("description"), str):
            descriptions[result["value"]["description"]].append(rel)

    if records is not None and not args.paths:
        for rel in sorted(set(records) - set(concepts)):
            problems.append((rel, "missing since the inventory"))

    for rel, path in reserved.items():
        problems.extend((rel, issue) for issue in validate_reserved(rel, path.read_bytes()))

    for description, paths in descriptions.items():
        if len(paths) > 1:
            warnings.append((", ".join(paths), f"same description: {description}"))

    if args.missing:
        for rel in sorted(set(worklist)):
            print(rel)
        raise SystemExit(0)

    print(scope.describe())
    for rel, issue in sorted(problems):
        print(f"FAIL {rel}: {issue}")
    for rel, issue in warnings:
        print(f"WARN {rel}: {issue}")
    print(f"checked: {len(concepts)} documents, {len(reserved)} index/log files; problems: {len(problems)}")
    raise SystemExit(1 if problems else 0)


if __name__ == "__main__":
    main()
