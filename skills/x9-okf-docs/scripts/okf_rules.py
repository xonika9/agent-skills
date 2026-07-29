#!/usr/bin/env python3
"""Shared OKF v0.1/v0.2 document selection and metadata rules."""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path

from okf_yaml import inspect_yaml

BOM = b"\xef\xbb\xbf"
RESERVED_FILES = {"index.md", "log.md"}
ONBOARDING_FILES = {"AGENTS.md", "CLAUDE.md", "GEMINI.md", "README.md"}
DEFAULT_EXCLUDES = {
    "raw", "transcripts", "summaries", "artifacts", "archive", "node_modules",
    ".git", ".obsidian", "dist", "build", "vendor",
}
CURATED_REQUIRED = {"type", "title", "description", "tags"}
TAG_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
ACTOR_RE = re.compile(r"(?:human:[^\s]+|process:[^\s]+|[^\s/]+/[^\s/]+)\Z")


def markdown_files(
    root: Path,
    excludes: set[str],
    include_readme: bool = False,
    whole_bundle: bool = False,
):
    excluded_files = set(ONBOARDING_FILES)
    if include_readme:
        excluded_files.discard("README.md")
    return sorted(
        path for path in root.rglob("*.md")
        if path.name not in excluded_files
        and (whole_bundle or not path.name.startswith("."))
        and (
            not any(
                part == ".git" or part in excludes
                for part in path.relative_to(root).parts[:-1]
            )
            if whole_bundle
            else not any(
                part.startswith(".") or part in DEFAULT_EXCLUDES or part in excludes
                for part in path.relative_to(root).parts[:-1]
            )
        )
    )


def concept_files(
    root: Path,
    excludes: set[str],
    include_readme: bool = False,
    whole_bundle: bool = False,
):
    return [
        path for path in markdown_files(root, excludes, include_readme, whole_bundle)
        if path.name not in RESERVED_FILES
    ]


def reserved_files(root: Path, excludes: set[str], whole_bundle: bool = False):
    return [
        path for path in markdown_files(root, excludes, whole_bundle=whole_bundle)
        if path.name in RESERVED_FILES
    ]


def partition_markdown_files(
    root: Path,
    excludes: set[str],
    include_readme: bool = False,
    whole_bundle: bool = False,
):
    selected = markdown_files(root, excludes, include_readme, whole_bundle)
    concepts = [path for path in selected if path.name not in RESERVED_FILES]
    reserved = [path for path in selected if path.name in RESERVED_FILES]
    return concepts, reserved


def split_document(data: bytes):
    bom = data.startswith(BOM)
    raw = data[len(BOM):] if bom else data
    lines = raw.splitlines(keepends=True)
    if not lines or lines[0].rstrip(b"\r\n") != b"---":
        return None, raw, bom, "missing"
    end = next(
        (index for index, line in enumerate(lines[1:], 1) if line.rstrip(b"\r\n") == b"---"),
        None,
    )
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


def valid_datetime(value, raw_value=None):
    candidate = raw_value if isinstance(raw_value, str) else value
    if not isinstance(candidate, str) or not candidate.strip():
        return False
    try:
        return datetime.fromisoformat(candidate.replace("Z", "+00:00")).tzinfo is not None
    except ValueError:
        return False


def valid_date(value, raw_value=None):
    candidate = raw_value if isinstance(raw_value, str) else value
    if not isinstance(candidate, str):
        if isinstance(candidate, (date, datetime)):
            return True
        return False
    try:
        date.fromisoformat(candidate)
        return True
    except ValueError:
        return False


def valid_actor(value):
    return isinstance(value, str) and bool(ACTOR_RE.fullmatch(value))


def validate_event(event, name: str):
    issues = []
    if not isinstance(event, dict):
        return [f"{name} must be a mapping"]
    if not valid_actor(event.get("by")):
        issues.append(f"{name}.by must follow the OKF actor convention")
    if "at" not in event or not valid_datetime(event.get("at")):
        issues.append(f"{name}.at must be ISO 8601 with timezone")
    return issues


def validate_sources(fields: dict):
    issues = []
    sources = fields.get("sources")
    if sources is None:
        return issues
    if not isinstance(sources, list):
        return ["sources must be a list"]
    ids = []
    for index, source in enumerate(sources):
        name = f"sources[{index}]"
        if not isinstance(source, dict):
            issues.append(f"{name} must be a mapping")
            continue
        if not isinstance(source.get("resource"), str) or not source["resource"].strip():
            issues.append(f"{name}.resource must be a non-empty string")
        if "id" in source:
            if not isinstance(source["id"], str) or not source["id"].strip():
                issues.append(f"{name}.id must be a non-empty string")
            else:
                ids.append(source["id"])
        if "usage_count" in source and (
            not isinstance(source["usage_count"], int) or isinstance(source["usage_count"], bool)
            or source["usage_count"] < 0
        ):
            issues.append(f"{name}.usage_count must be a non-negative integer")
        if "last_modified" in source and not valid_date(source["last_modified"]):
            issues.append(f"{name}.last_modified must be YYYY-MM-DD")
    if len(ids) != len(set(ids)):
        issues.append("sources ids must be unique")
    return issues


def validate_fields(
    fields: dict,
    raw_scalars: dict,
    target_version: str = "0.2",
    profile: str = "okf",
    catalog: set[str] | None = None,
):
    issues = []
    concept_type = fields.get("type")
    if not isinstance(concept_type, str) or not concept_type.strip():
        issues.append("type must be a non-empty string")
    if catalog and isinstance(concept_type, str) and concept_type not in catalog:
        issues.append(f"type outside local profile catalog: {concept_type}")

    for key in ("title", "description", "resource"):
        if key in fields and (not isinstance(fields[key], str) or not fields[key].strip()):
            issues.append(f"{key} must be a non-empty string when present")
    if isinstance(fields.get("description"), str) and ("\n" in fields["description"] or "\r" in fields["description"]):
        issues.append("description must be one line")

    tags = fields.get("tags")
    if tags is not None and (
        not isinstance(tags, list)
        or any(not isinstance(tag, str) or not tag.strip() for tag in tags)
    ):
        issues.append("tags must be a list of non-empty strings")

    if "timestamp" in fields and not valid_datetime(fields["timestamp"], raw_scalars.get("timestamp")):
        issues.append("timestamp must be ISO 8601 with timezone")

    if target_version == "0.2":
        generated = fields.get("generated")
        if generated is not None:
            if not isinstance(generated, dict):
                issues.append("generated must be a mapping")
            else:
                if not valid_actor(generated.get("by")):
                    issues.append("generated.by must follow the OKF actor convention")
                if "at" in generated and not valid_datetime(generated["at"]):
                    issues.append("generated.at must be ISO 8601 with timezone")

        verified = fields.get("verified")
        if verified is not None:
            events = verified if isinstance(verified, list) else [verified]
            if not events:
                issues.append("verified must not be empty")
            for index, event in enumerate(events):
                issues.extend(validate_event(event, f"verified[{index}]"))

        if "status" in fields and fields["status"] not in {"draft", "stable", "deprecated"}:
            issues.append("status must be draft, stable, or deprecated")
        if "stale_after" in fields and not valid_date(fields["stale_after"], raw_scalars.get("stale_after")):
            issues.append("stale_after must be YYYY-MM-DD")
        issues.extend(validate_sources(fields))

        if concept_type == "Attested Computation":
            if not isinstance(fields.get("runtime"), str) or not fields["runtime"].strip():
                issues.append("runtime is required for Attested Computation")

    if profile == "curated":
        version_field = "generated" if target_version == "0.2" else "timestamp"
        missing = sorted((CURATED_REQUIRED | {version_field}) - set(fields))
        if missing:
            issues.append(f"missing curated fields: {', '.join(missing)}")
        if isinstance(tags, list):
            if not 2 <= len(tags) <= 5:
                issues.append("curated tags must contain 2-5 values")
            elif len(tags) != len(set(tags)) or any(not TAG_RE.fullmatch(tag) for tag in tags):
                issues.append("curated tags must be unique English kebab-case strings")
        generated = fields.get("generated")
        if target_version == "0.2" and isinstance(generated, dict) and "at" not in generated:
            issues.append("curated generated.at is required")

    return issues


def validate_index(
    path: Path,
    root: Path,
    header: str | None,
    body: bytes,
    split_error: str | None,
    target_version: str,
    ignore_version_declaration: bool = False,
):
    issues = []
    is_root = path.parent.resolve() == root.resolve()
    if split_error is None and not is_root:
        issues.append("nested index.md must not contain frontmatter")
    elif split_error is None:
        fields, _, yaml_error = strict_yaml(header)
        if yaml_error:
            issues.append(yaml_error)
        elif set(fields) != {"okf_version"}:
            issues.append("root index.md frontmatter may contain only okf_version")
        elif not ignore_version_declaration and fields["okf_version"] != target_version:
            issues.append(f"root index.md declares OKF {fields['okf_version']!r}, expected {target_version}")
    elif split_error != "missing":
        issues.append(split_error)
    text = body.decode("utf-8", errors="replace")
    if not re.search(r"(?m)^#\s+\S", text):
        issues.append("index.md must contain a section heading")
    if not re.search(r"(?m)^\*\s+\[[^\]]+\]\([^)]+\)\s+-\s+\S", text):
        issues.append("index.md must contain '* [Title](path) - description' entries")
    return issues


def validate_log(body: bytes, split_error: str | None):
    issues = []
    if split_error is None:
        issues.append("log.md must not contain frontmatter")
    elif split_error != "missing":
        issues.append(split_error)
    text = body.decode("utf-8", errors="replace")
    dates = re.findall(r"(?m)^##\s+(\d{4}-\d{2}-\d{2})\s*$", text)
    if not dates:
        issues.append("log.md must contain ISO date headings")
    elif any(not valid_date(value) for value in dates):
        issues.append("log.md contains an invalid date heading")
    elif dates != sorted(dates, reverse=True):
        issues.append("log.md date headings must be newest first")
    return issues


def validate_reserved(
    path: Path,
    root: Path,
    data: bytes,
    target_version: str,
    ignore_version_declaration: bool = False,
):
    try:
        header, body, _, split_error = split_document(data)
    except UnicodeDecodeError as exc:
        return [f"frontmatter is not UTF-8: {exc}"]
    if path.name == "index.md":
        return validate_index(
            path,
            root,
            header,
            body,
            split_error,
            target_version,
            ignore_version_declaration,
        )
    return validate_log(body, split_error)
