#!/usr/bin/env python3
"""Validate official OKF v0.1/v0.2 conformance or the stricter x9 profile."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from okf_rules import (
    line_endings,
    partition_markdown_files,
    split_document,
    strict_yaml,
    validate_fields,
    validate_reserved,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--missing", action="store_true")
    parser.add_argument("--inventory", type=Path)
    parser.add_argument("--target-version", choices=("0.1", "0.2"), default="0.2")
    parser.add_argument("--profile", choices=("okf", "curated"), default="curated")
    parser.add_argument("--types", help="comma-separated local curated type catalog")
    parser.add_argument("--exclude", nargs="*", default=[])
    parser.add_argument("--include-readme", action="store_true")
    parser.add_argument("--whole-bundle", action="store_true")
    parser.add_argument("--ignore-version-declaration", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.is_dir():
        raise SystemExit(f"not a directory: {root}")
    excludes = set(args.exclude)
    catalog = set(args.types.split(",")) if args.types else None
    inventory = json.loads(args.inventory.read_text()) if args.inventory else None
    records = inventory.get("files", {}) if inventory else {}
    problems = []
    descriptions = defaultdict(list)
    type_counts = Counter()
    worklist = []
    seen = set()

    selected, selected_reserved = partition_markdown_files(
        root,
        excludes,
        include_readme=args.include_readme,
        whole_bundle=args.whole_bundle,
    )
    for path in selected:
        rel = path.relative_to(root).as_posix()
        seen.add(rel)
        data = path.read_bytes()
        try:
            header, body, bom, split_error = split_document(data)
        except UnicodeDecodeError as exc:
            problems.append((rel, f"frontmatter is not UTF-8: {exc}"))
            worklist.append(rel)
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
        issues = validate_fields(
            fields,
            raw_scalars,
            target_version=args.target_version,
            profile=args.profile,
            catalog=catalog,
        )
        if issues:
            worklist.append(rel)
            problems.extend((rel, issue) for issue in issues)
        else:
            if args.profile == "curated" and isinstance(fields.get("description"), str):
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

    for path in selected_reserved:
        rel = path.relative_to(root).as_posix()
        for issue in validate_reserved(
            path,
            root,
            path.read_bytes(),
            args.target_version,
            args.ignore_version_declaration,
        ):
            problems.append((rel, issue))

    if inventory:
        for rel in sorted(set(records) - seen):
            problems.append((rel, "file missing after pre-edit inventory"))

    if args.profile == "curated":
        for description, paths in descriptions.items():
            if len(paths) > 1:
                problems.append((", ".join(paths), f"duplicate curated description: {description}"))

    if args.missing:
        for rel in sorted(set(worklist)):
            print(rel)
        raise SystemExit(0)

    for rel, issue in problems:
        print(f"FAIL {rel}: {issue}")
    scope = "whole bundle" if args.whole_bundle else "selected scope"
    print(
        f"checked: {len(selected)} concepts  reserved: {len(selected_reserved)}  "
        f"problems: {len(problems)}  target: OKF {args.target_version}  "
        f"profile: {args.profile}  scope: {scope}"
    )
    for kind, count in type_counts.most_common():
        print(f"  {count:4d}  {kind}")
    raise SystemExit(1 if problems else 0)


if __name__ == "__main__":
    main()
