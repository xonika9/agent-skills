#!/usr/bin/env python3
"""Shared scope, parsing, and field rules for the x9 OKF contract."""

from __future__ import annotations

import json
import os
import re
import unicodedata
from datetime import date
from pathlib import Path

from okf_yaml import inspect_many, inspect_yaml

BOM = b"\xef\xbb\xbf"
RESERVED_FILES = {"index.md", "log.md"}
INSTRUCTION_KEYS = {"agents.md", "claude.md", "gemini.md"}
DEFAULT_EXCLUDES = {
    "raw", "transcripts", "summaries", "artifacts", "archive", "node_modules",
    "dist", "build", "vendor",
}
POLICY_FILE = ".x9-okf.json"
FIELDS = ("type", "title", "description", "tags")
REQUIRED = FIELDS
MAX_TAGS = 5
TAG_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
DATE_HEADING_RE = re.compile(r"(?m)^##[ \t]+(.+?)[ \t]*\r?$")


def nfc(text: str):
    return unicodedata.normalize("NFC", text)


def name_key(text: str):
    """Comparison key that ignores case and Unicode composition."""
    return nfc(text).casefold()


def rel_key(rel: str):
    parts = [part for part in nfc(rel).replace("\\", "/").split("/") if part not in ("", ".")]
    return "/".join(name_key(part) for part in parts)


class Scope:
    def __init__(self, root: Path, excludes, include_readme: bool, policy_path, includes=()):
        self.root = root
        self.includes = {rel_key(item) for item in includes if rel_key(item)}
        self.include_readme = include_readme
        self.policy_path = policy_path
        self.names = {name_key(item) for item in DEFAULT_EXCLUDES}
        self.paths = set()
        self.explicit_names = set()
        for item in excludes:
            key = rel_key(item)
            if not key:
                continue
            if "/" in item.replace("\\", "/"):
                self.paths.add(key)
            else:
                self.names.add(key)
                self.explicit_names.add(key)

    def excluded_dir(self, rel_parts):
        key = "/".join(name_key(part) for part in rel_parts)
        if any(key == path or key.startswith(path + "/") for path in self.paths):
            return True
        if name_key(rel_parts[-1]) in self.explicit_names:
            return True
        on_include = any(
            key == path or key.startswith(path + "/") or path.startswith(key + "/") for path in self.includes
        )
        if self.includes and not on_include:
            return True
        explicit = any(key == path or path.startswith(key + "/") for path in self.includes)
        if not explicit and (rel_parts[-1].startswith(".") or name_key(rel_parts[-1]) in self.names):
            return True
        return False

    def excluded_file(self, rel_parts):
        key = "/".join(name_key(part) for part in rel_parts)
        return name_key(rel_parts[-1]) in self.names or key in self.paths

    def included_file(self, rel_parts):
        if not self.includes:
            return True
        key = "/".join(name_key(part) for part in rel_parts)
        return any(key.startswith(path + "/") for path in self.includes)

    def describe(self):
        source = self.policy_path.name if self.policy_path else "defaults"
        readme = "README.md included" if self.include_readme else "README.md excluded"
        return f"scope: {source}; {readme}"


def load_scope(root: Path, extra_excludes=(), include_readme: bool = False):
    policy_path = root / POLICY_FILE
    excludes = list(extra_excludes)
    if policy_path.is_symlink():
        raise SystemExit(f"{POLICY_FILE} must be a regular file, not a link")
    if policy_path.is_file():
        try:
            policy = json.loads(policy_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise SystemExit(f"cannot read {POLICY_FILE}: {exc}") from None
        if not isinstance(policy, dict) or set(policy) - {"include", "exclude", "include_readme"}:
            raise SystemExit(f"{POLICY_FILE} may contain only 'include', 'exclude', and 'include_readme'")
        for key in ("include", "exclude"):
            value = policy.get(key, [])
            if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
                raise SystemExit(f"{POLICY_FILE}: '{key}' must be a list of folder names or paths")
        listed = policy.get("exclude", [])
        includes = policy.get("include", [])
        if not isinstance(policy.get("include_readme", False), bool):
            raise SystemExit(f"{POLICY_FILE}: 'include_readme' must be true or false")
        excludes.extend(listed)
        include_readme = include_readme or policy.get("include_readme", False)
    else:
        policy_path = None
        includes = []
    return Scope(root, excludes, include_readme, policy_path, includes)


def markdown_files(scope: Scope):
    """Return {nfc relative path: Path} for Markdown files in scope; links are never followed."""
    found = {}
    for current, dirs, files in os.walk(scope.root, followlinks=False):
        base = Path(current)
        rel_base = [nfc(part) for part in base.relative_to(scope.root).parts]
        dirs[:] = sorted(
            name for name in dirs
            if not (base / name).is_symlink() and not scope.excluded_dir(rel_base + [nfc(name)])
        )
        for name in sorted(files):
            path = base / name
            if (
                not name.lower().endswith(".md")
                or name.startswith(".")
                or path.is_symlink()
                or name.casefold() in INSTRUCTION_KEYS
                or (name.casefold() == "readme.md" and not scope.include_readme)
                or not scope.included_file(rel_base + [nfc(name)])
                or scope.excluded_file(rel_base + [nfc(name)])
            ):
                continue
            found["/".join(rel_base + [nfc(name)])] = path
    return dict(sorted(found.items()))


def partition(files: dict):
    concepts = {rel: path for rel, path in files.items() if path.name.casefold() not in RESERVED_FILES}
    reserved = {rel: path for rel, path in files.items() if path.name.casefold() in RESERVED_FILES}
    return concepts, reserved


def root_relative(root: Path, raw: str):
    """Accept a path relative to the root, relative to the current folder, or absolute."""
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        if (root / candidate).exists() or not (Path.cwd() / candidate).exists():
            return raw
        candidate = Path.cwd() / candidate
    for base in (Path(os.path.abspath(candidate)), candidate.parent.resolve() / candidate.name):
        try:
            return base.relative_to(root).as_posix()
        except ValueError:
            continue
    return raw


def resolve_named(files: dict, names, root: Path):
    """Map user-supplied paths to scoped files, ignoring case and Unicode form."""
    index = {}
    for rel in files:
        index.setdefault(rel_key(rel), []).append(rel)
    resolved = []
    for raw in names:
        matches = index.get(rel_key(root_relative(root, raw)), [])
        if not matches:
            raise SystemExit(f"not an OKF document in scope (paths are relative to {root}): {raw}")
        if len(matches) > 1:
            raise SystemExit(f"ambiguous path, several files differ only by case: {raw}")
        if matches[0] not in resolved:
            resolved.append(matches[0])
    return resolved


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
        return None, raw, bom, "unclosed frontmatter"
    header = b"".join(lines[1:end]).decode("utf-8", errors="strict")
    body = b"".join(lines[end + 1:])
    return header, body, bom, None


def parse_header(header: str):
    result, error = inspect_yaml(header)
    if error:
        return None, None, error
    return result["value"], result["top_keys"], None


def parse_headers(headers):
    """Read many headers with one YAML process; each item is (result, error)."""
    return inspect_many(headers)


def line_endings(data: bytes):
    crlf = data.count(b"\r\n")
    return {"crlf": crlf, "lf": data.count(b"\n") - crlf, "cr": data.count(b"\r") - crlf}


def field_issue(key: str, value):
    """Return the problem with one contract field value, or None."""
    if key in ("type", "title", "description"):
        if not isinstance(value, str) or not value.strip():
            return f"{key} must be a non-empty string"
        if key == "description" and ("\n" in value or "\r" in value):
            return "description must be one line"
        return None
    if key == "tags":
        if not isinstance(value, list) or not value:
            return "tags must be a non-empty list"
        if len(value) > MAX_TAGS:
            return f"tags must contain at most {MAX_TAGS} values"
        if any(isinstance(tag, bool) for tag in value):
            return "tags: a bare yes, no, on, or off is read as true or false; quote it or choose another word"
        if any(not isinstance(tag, str) or not TAG_RE.fullmatch(tag) for tag in value):
            return "tags must be English kebab-case words, such as health or video-ideas"
        if len(set(value)) != len(value):
            return "tags must be unique"
        return None
    raise ValueError(f"not a contract field: {key}")


def validate_fields(fields: dict):
    issues = [f"missing {key}" for key in REQUIRED if key not in fields]
    for key in FIELDS:
        if key in fields:
            issue = field_issue(key, fields[key])
            if issue:
                issues.append(issue)
    return issues


def validate_reserved(rel: str, data: bytes):
    try:
        header, body, _, split_error = split_document(data)
    except UnicodeDecodeError as exc:
        return [f"frontmatter is not UTF-8: {exc}"]
    issues = []
    if rel.rsplit("/", 1)[-1].casefold() == "index.md":
        if split_error is None:
            fields, _, error = parse_header(header)
            if "/" in rel:
                issues.append("a nested index.md must not have frontmatter")
            elif error:
                issues.append(error)
            elif set(fields) != {"okf_version"} or not isinstance(fields["okf_version"], str):
                issues.append('root index.md frontmatter may hold only okf_version as a quoted string, such as "0.2"')
        elif split_error != "missing":
            issues.append(split_error)
        return issues
    if split_error != "missing":
        issues.append("log.md must not have frontmatter")
    text = body.decode("utf-8", errors="replace")
    headings = DATE_HEADING_RE.findall(text)
    for heading in headings:
        try:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", heading):
                raise ValueError(heading)
            date.fromisoformat(heading)
        except ValueError:
            issues.append(f"log.md heading is not a YYYY-MM-DD date: {heading}")
            return issues
    if headings != sorted(headings, reverse=True):
        issues.append("log.md dates must go newest first")
    return issues
