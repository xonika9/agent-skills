#!/usr/bin/env python3
"""Strict structural validator for Agent Skills.

Usage: validate.py <skill-directory>
Behavioral quality is evaluated separately with references/evals.md.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict, deque
from pathlib import Path

MAX_NAME = 64
MAX_DESCRIPTION = 1024
MAX_BODY_LINES = 500
MAX_BODY_WORDS = 5000
TOC_THRESHOLD = 100

JUNK = {
    ".DS_Store", "Thumbs.db", "desktop.ini", "README.md", "CHANGELOG.md",
    "INSTALLATION_GUIDE.md", "QUICK_REFERENCE.md",
}
RESOURCE_DIRS = {"references", "scripts", "assets", "agents"}
ALLOWED_KEYS = {
    "name", "description", "license", "metadata", "version", "compatibility",
    "when_to_use", "argument-hint", "arguments", "disable-model-invocation",
    "user-invocable", "allowed-tools", "disallowed-tools", "model", "effort",
    "context", "agent", "hooks", "paths", "shell",
}
BOOL_KEYS = {"disable-model-invocation", "user-invocable"}
MAPPING_KEYS = {"metadata", "hooks"}
STRING_KEYS = {
    "name", "description", "license", "version", "compatibility", "when_to_use",
    "argument-hint", "model", "effort", "context", "agent", "shell",
}
REF_USE_RE = re.compile(r"!?\[([^\]]+)\]\[([^\]]*)\]")
REF_DEF_RE = re.compile(r"(?m)^\s*\[([^\]]+)\]:\s*(\S+)")
HTML_LINK_RE = re.compile(r"(?i)(?:href|src)\s*=\s*[\"']([^\"']+)[\"']")
FENCE_RE = re.compile(r"(?s)```.*?```|~~~.*?~~~")
INLINE_CODE_RE = re.compile(r"`+[^`\n]*`+")
HEADING_RE = re.compile(r"(?m)^#{1,6}\s+(.+?)\s*$")
TOC_RE = re.compile(r"(?im)^#{1,3}\s+(contents|table of contents|оглавление|содержание)\b")
SECRET_RE = re.compile(
    r"(?i)(?:api[_-]?key|token|secret|password)\s*(?:=|:)\s*[\"']?[A-Za-z0-9_\-]{16,}"
)

RUBY_YAML = r'''
require "yaml"
require "json"
begin
  value = YAML.safe_load(STDIN.read, permitted_classes: [], permitted_symbols: [], aliases: false)
  STDOUT.write(JSON.generate({"ok" => true, "value" => value}))
rescue => e
  STDOUT.write(JSON.generate({"ok" => false, "error" => e.message}))
  exit 1
end
'''


def all_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        yield path


def parse_frontmatter(data: bytes):
    text = data.decode("utf-8-sig")
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return None, None, "frontmatter must start on line 1 with ---"
    end = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), None)
    if end is None:
        return None, None, "frontmatter closing --- is missing"
    raw = "".join(lines[1:end])
    top_keys = []
    for line in raw.splitlines():
        match = re.match(r"^([A-Za-z0-9_-]+)\s*:", line)
        if match:
            top_keys.append(match.group(1))
    duplicates = sorted(key for key, count in __import__("collections").Counter(top_keys).items() if count > 1)
    if duplicates:
        return None, None, f"duplicate frontmatter key(s): {', '.join(duplicates)}"
    try:
        proc = subprocess.run(
            ["ruby", "-e", RUBY_YAML], input=raw, text=True,
            capture_output=True, check=False,
        )
    except FileNotFoundError:
        return None, None, "Ruby/Psych is required for strict YAML validation"
    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None, None, "YAML parser returned invalid output"
    if not result.get("ok"):
        return None, None, f"invalid YAML: {result.get('error', 'unknown parser error')}"
    if not isinstance(result.get("value"), dict):
        return None, None, "frontmatter must be a YAML mapping"
    return result["value"], "".join(lines[end + 1 :]), None


def slug(text: str):
    value = re.sub(r"[^\w\s-]", "", text.strip().lower(), flags=re.UNICODE)
    return re.sub(r"-+", "-", re.sub(r"\s+", "-", value)).strip("-")


def heading_slugs(text: str):
    seen = defaultdict(int)
    out = set()
    for heading in HEADING_RE.findall(FENCE_RE.sub("", text)):
        base = slug(heading)
        if base:
            suffix = seen[base]
            out.add(base if suffix == 0 else f"{base}-{suffix}")
            seen[base] += 1
    return out


def clean_markdown(text: str):
    return INLINE_CODE_RE.sub("", FENCE_RE.sub("", text))


def inline_link_targets(text: str):
    """Extract inline Markdown destinations while allowing balanced parentheses."""
    out = []
    cursor = 0
    while True:
        start = text.find("](", cursor)
        if start < 0:
            break
        i, depth, escaped = start + 2, 1, False
        while i < len(text) and depth:
            char = text[i]
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
            i += 1
        if depth == 0:
            raw = text[start + 2 : i - 1].strip()
            if raw.startswith("<") and ">" in raw:
                out.append(raw[1 : raw.index(">")])
            elif raw:
                out.append(raw.split()[0])
        cursor = max(i, start + 2)
    return out


def local_targets(path: Path, text: str):
    clean = clean_markdown(text)
    definitions = {key.casefold(): target for key, target in REF_DEF_RE.findall(clean)}
    raw_targets = inline_link_targets(clean)
    raw_targets += HTML_LINK_RE.findall(clean)
    for label, ref in REF_USE_RE.findall(clean):
        key = (ref or label).casefold()
        if key in definitions:
            raw_targets.append(definitions[key])
    return raw_targets


def is_external(target: str):
    return target.startswith(("http://", "https://", "mailto:", "data:")) or "://" in target


def validate(root: Path):
    errors, warnings = [], []
    if not root.is_dir():
        return [f"not a directory: {root}"], []
    skill = root / "SKILL.md"
    if not skill.is_file():
        return ["SKILL.md not found"], []

    data = skill.read_bytes()
    fm, body, fm_error = parse_frontmatter(data)
    if fm_error:
        errors.append(f"frontmatter: {fm_error}")
        fm, body = {}, ""

    unknown = sorted(set(fm) - ALLOWED_KEYS)
    if unknown:
        errors.append(f"frontmatter: unknown key(s): {', '.join(unknown)}")
    name = fm.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append("frontmatter: name must be a non-empty string")
    else:
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
            errors.append("frontmatter: name must be hyphen-case")
        if len(name) > MAX_NAME:
            errors.append(f"frontmatter: name exceeds {MAX_NAME} characters")
        if name != root.name:
            errors.append(f"frontmatter: name '{name}' does not match folder '{root.name}'")
    description = fm.get("description")
    if not isinstance(description, str) or not description.strip():
        errors.append("frontmatter: description must be a non-empty string")
    else:
        if len(description) > MAX_DESCRIPTION:
            errors.append(f"frontmatter: description exceeds {MAX_DESCRIPTION} characters")
        if "<" in description or ">" in description:
            errors.append("frontmatter: description must not contain angle brackets")
    for key in BOOL_KEYS:
        if key in fm and not isinstance(fm[key], bool):
            errors.append(f"frontmatter: {key} must be boolean")
    for key in MAPPING_KEYS:
        if key in fm and not isinstance(fm[key], dict):
            errors.append(f"frontmatter: {key} must be a mapping")
    for key in STRING_KEYS - {"name", "description"}:
        if key in fm and not isinstance(fm[key], str):
            errors.append(f"frontmatter: {key} must be a string")
    for key in {"allowed-tools", "disallowed-tools", "paths", "arguments"}:
        if key in fm and not isinstance(fm[key], (str, list, dict)):
            errors.append(f"frontmatter: {key} has an unsupported type")
    if not body.strip():
        errors.append("SKILL.md body is empty")

    files = list(all_files(root))
    for path in files:
        rel = path.relative_to(root)
        if path.name in JUNK:
            errors.append(f"junk file not allowed: {rel.as_posix()}")
        if len(rel.parts) > 2 and rel.parts[0] in RESOURCE_DIRS:
            errors.append(f"resource nested too deep: {rel.as_posix()}")
        if path.suffix in {".md", ".py", ".sh", ".toml", ".yaml", ".yml", ".json"}:
            text = path.read_text(encoding="utf-8", errors="replace")
            if ("[" + "TODO") in text:
                errors.append(f"template placeholder remains: {rel.as_posix()}")
            if SECRET_RE.search(text):
                errors.append(f"possible embedded secret: {rel.as_posix()}")

    for dirname in RESOURCE_DIRS:
        directory = root / dirname
        if directory.exists() and not any(all_files(directory)):
            errors.append(f"empty resource directory: {dirname}/")

    md_files = [p for p in files if p.suffix.lower() == ".md"]
    texts = {p: p.read_text(encoding="utf-8", errors="replace") for p in md_files}
    slugs = {p: heading_slugs(text) for p, text in texts.items()}
    graph = defaultdict(set)
    for path, text in texts.items():
        rel = path.relative_to(root).as_posix()
        clean = clean_markdown(text)
        definitions = {key.casefold(): target for key, target in REF_DEF_RE.findall(clean)}
        for label, ref in REF_USE_RE.findall(clean):
            if (ref or label).casefold() not in definitions:
                errors.append(f"undefined reference-style link in {rel}: [{ref or label}]")
        for target in local_targets(path, text):
            if is_external(target):
                continue
            path_part, _, fragment = target.partition("#")
            resolved = path if not path_part else (path.parent / path_part).resolve()
            try:
                resolved.relative_to(root)
            except ValueError:
                errors.append(f"local link escapes skill root in {rel}: {target}")
                continue
            if not resolved.exists():
                errors.append(f"broken local link in {rel}: {target}")
                continue
            if resolved.is_file() and resolved.suffix.lower() == ".md":
                graph[path].add(resolved)
                if fragment and fragment not in slugs.get(resolved, set()):
                    warnings.append(f"anchor not found from {rel}: {target}")

    reachable = {skill}
    queue = deque([skill])
    while queue:
        for linked in graph.get(queue.popleft(), set()):
            if linked not in reachable:
                reachable.add(linked)
                queue.append(linked)
    ref_dir = root / "references"
    if ref_dir.exists():
        for ref in (p for p in md_files if ref_dir in p.parents):
            if ref not in reachable:
                errors.append(f"orphan reference not reachable from SKILL.md: {ref.relative_to(root).as_posix()}")
            lines = texts[ref].count("\n") + 1
            if lines > TOC_THRESHOLD:
                head = "\n".join(texts[ref].splitlines()[:60])
                if not TOC_RE.search(head):
                    warnings.append(f"long reference lacks TOC: {ref.relative_to(root).as_posix()} ({lines} lines)")

    for script in (p for p in files if p.parts and "scripts" in p.parts):
        rel = script.relative_to(root).as_posix()
        if script.suffix == ".py":
            env = {**os.environ, "PYTHONPYCACHEPREFIX": "/tmp/agent-skill-validator-pycache"}
            proc = subprocess.run([sys.executable, "-m", "py_compile", str(script)], capture_output=True, text=True, env=env)
            if proc.returncode:
                errors.append(f"Python syntax error in {rel}: {proc.stderr.strip().splitlines()[-1]}")
        elif script.suffix == ".sh":
            proc = subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True)
            if proc.returncode:
                errors.append(f"shell syntax error in {rel}: {proc.stderr.strip()}")

    line_count = body.count("\n") + 1
    word_count = len(body.split())
    if line_count > MAX_BODY_LINES:
        warnings.append(f"SKILL.md exceeds line budget: {line_count}>{MAX_BODY_LINES}")
    if word_count > MAX_BODY_WORDS:
        warnings.append(f"SKILL.md exceeds word budget: {word_count}>{MAX_BODY_WORDS}")
    return sorted(set(errors)), sorted(set(warnings))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("skill", type=Path)
    args = parser.parse_args()
    errors, warnings = validate(args.skill.resolve())
    for warning in warnings:
        print(f"[WARN] {warning}")
    for error in errors:
        print(f"[ERROR] {error}")
    if errors:
        print(f"FAIL — {len(errors)} error(s), {len(warnings)} warning(s)")
        raise SystemExit(1)
    print(f"PASS — 0 errors, {len(warnings)} warning(s)")


if __name__ == "__main__":
    main()
