#!/usr/bin/env python3
"""Strict structural validator for Agent Skills.

Usage: validate.py [--runtime portable|claude|codex] <skill-directory>
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

RUNTIMES = ("portable", "claude", "codex")
JUNK = {
    ".DS_Store",
    "Thumbs.db",
    "desktop.ini",
    "README.md",
    "CHANGELOG.md",
    "INSTALLATION_GUIDE.md",
    "QUICK_REFERENCE.md",
}
RESOURCE_DIRS = {"references", "scripts", "assets", "agents"}
PORTABLE_KEYS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}
CLAUDE_KEYS = PORTABLE_KEYS | {
    "version",
    "when_to_use",
    "argument-hint",
    "arguments",
    "disable-model-invocation",
    "user-invocable",
    "allowed-tools",
    "disallowed-tools",
    "model",
    "effort",
    "context",
    "agent",
    "background",
    "hooks",
    "paths",
    "shell",
}
CODEX_KEYS = PORTABLE_KEYS
RUNTIME_KEYS = {
    "portable": PORTABLE_KEYS,
    "claude": CLAUDE_KEYS,
    "codex": CODEX_KEYS,
}
RUNTIME_REQUIRED = {
    "portable": {"name", "description"},
    "claude": set(),
    "codex": {"description"},
}
BOOL_KEYS = {"disable-model-invocation", "user-invocable", "background"}
STRING_KEYS = {
    "name",
    "description",
    "license",
    "version",
    "compatibility",
    "when_to_use",
    "argument-hint",
    "model",
    "effort",
    "context",
    "agent",
    "shell",
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
require "psych"
require "json"

def check_duplicates(node, path = [])
  if node.is_a?(Psych::Nodes::Mapping)
    seen = {}
    node.children.each_slice(2) do |key_node, value_node|
      key = key_node.respond_to?(:value) ? key_node.value.to_s : key_node.to_yaml
      location = (path + [key]).join(".")
      raise "duplicate YAML key: #{location}" if seen.key?(key)
      seen[key] = true
      check_duplicates(value_node, path + [key])
    end
  elsif node.respond_to?(:children)
    Array(node.children).each { |child| check_duplicates(child, path) }
  end
end

begin
  source = STDIN.read
  stream = Psych.parse_stream(source)
  check_duplicates(stream)
  value = Psych.safe_load(source, permitted_classes: [], permitted_symbols: [], aliases: false)
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
    try:
        proc = subprocess.run(
            ["ruby", "-e", RUBY_YAML],
            input=raw,
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError:
        return None, None, "Ruby/Psych is required for strict YAML validation"
    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError:
        detail = proc.stderr.strip().splitlines()
        if detail:
            return None, None, f"Ruby/Psych failed: {detail[-1]}"
        return None, None, "Ruby/Psych returned invalid output"
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


def validate(root: Path, runtimes=("portable",)):
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

    for runtime in runtimes:
        unsupported = sorted(set(fm) - RUNTIME_KEYS[runtime])
        if unsupported:
            errors.append(
                f"frontmatter: unsupported for {runtime}: {', '.join(unsupported)}"
            )
        missing = sorted(RUNTIME_REQUIRED[runtime] - set(fm))
        if missing:
            errors.append(
                f"frontmatter: required for {runtime}: {', '.join(missing)}"
            )

    portable_or_codex = any(runtime in {"portable", "codex"} for runtime in runtimes)
    name = fm.get("name")
    if name is not None:
        if not isinstance(name, str) or not name.strip():
            errors.append("frontmatter: name must be a non-empty string")
        elif portable_or_codex and not re.fullmatch(
            r"[a-z0-9]+(?:-[a-z0-9]+)*", name
        ):
            errors.append("frontmatter: name must be hyphen-case")
        elif portable_or_codex and len(name) > MAX_NAME:
            errors.append(f"frontmatter: name exceeds {MAX_NAME} characters")
        elif "portable" in runtimes and name != root.name:
            errors.append(f"frontmatter: name '{name}' does not match folder '{root.name}'")

    description = fm.get("description")
    if description is not None:
        if not isinstance(description, str) or not description.strip():
            errors.append("frontmatter: description must be a non-empty string")
        elif portable_or_codex and len(description) > MAX_DESCRIPTION:
            errors.append(f"frontmatter: description exceeds {MAX_DESCRIPTION} characters")
        elif "codex" in runtimes and ("<" in description or ">" in description):
            errors.append("frontmatter: description must not contain angle brackets")

    compatibility = fm.get("compatibility")
    if compatibility is not None:
        if not isinstance(compatibility, str) or not compatibility.strip():
            errors.append("frontmatter: compatibility must be a non-empty string")
        elif len(compatibility) > 500:
            errors.append("frontmatter: compatibility exceeds 500 characters")

    metadata = fm.get("metadata")
    if metadata is not None:
        if not isinstance(metadata, dict):
            errors.append("frontmatter: metadata must be a mapping")
        else:
            for key, value in metadata.items():
                if not isinstance(key, str) or (
                    key != "internal" and not isinstance(value, str)
                ):
                    errors.append("frontmatter: metadata keys and values must be strings")
                elif key == "internal" and type(value) is not bool:
                    errors.append("frontmatter: metadata.internal must be boolean")

    hooks = fm.get("hooks")
    if hooks is not None and not isinstance(hooks, dict):
        errors.append("frontmatter: hooks must be a mapping")

    for key in BOOL_KEYS:
        if key in fm and not isinstance(fm[key], bool):
            errors.append(f"frontmatter: {key} must be boolean")

    for key in STRING_KEYS - {"name", "description", "compatibility"}:
        if key in fm and not isinstance(fm[key], str):
            errors.append(f"frontmatter: {key} must be a string")

    if "allowed-tools" in fm:
        allowed_tools = fm["allowed-tools"]
        if portable_or_codex and not isinstance(allowed_tools, str):
            errors.append(
                "frontmatter: allowed-tools must be a string for portable and codex"
            )
        elif not isinstance(allowed_tools, (str, list)):
            errors.append("frontmatter: allowed-tools must be a string or list")
        elif isinstance(allowed_tools, list) and any(
            not isinstance(item, str) for item in allowed_tools
        ):
            errors.append("frontmatter: allowed-tools list items must be strings")

    for key in {"disallowed-tools", "paths", "arguments"}:
        if key not in fm:
            continue
        value = fm[key]
        if not isinstance(value, (str, list)):
            errors.append(f"frontmatter: {key} must be a string or list")
        elif isinstance(value, list) and any(not isinstance(item, str) for item in value):
            errors.append(f"frontmatter: {key} list items must be strings")

    if "context" in fm and fm["context"] != "fork":
        errors.append("frontmatter: context must be 'fork'")
    if "shell" in fm and fm["shell"] not in {"bash", "powershell"}:
        errors.append("frontmatter: shell must be 'bash' or 'powershell'")
    if (
        any(key in fm for key in {"agent", "background"})
        and fm.get("context") != "fork"
    ):
        warnings.append("frontmatter: agent/background has no effect without context: fork")
    if "when_to_use" in fm and isinstance(description, str):
        combined = f"{description} {fm['when_to_use']}"
        if len(combined) > 1536:
            warnings.append(
                "frontmatter: description + when_to_use exceeds Claude's "
                "1536-character listing budget"
            )

    if not body.strip():
        errors.append("SKILL.md body is empty")

    files = list(all_files(root))
    for path in files:
        rel = path.relative_to(root)
        if path.name in JUNK:
            errors.append(f"junk file not allowed: {rel.as_posix()}")
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
    direct_targets = defaultdict(set)
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
            if resolved.is_file():
                direct_targets[path].add(resolved)
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

    reachable_text = "\n".join(texts[path] for path in reachable)
    linked_resources = set()
    for path in reachable:
        linked_resources.update(direct_targets.get(path, set()))
    resources = {
        path
        for path in files
        if path.relative_to(root).parts[0] in RESOURCE_DIRS
        and not (path.suffix.lower() == ".md" and ref_dir in path.parents)
    }
    linked_resources.update(
        resource
        for resource in resources
        if resource.relative_to(root).as_posix() in reachable_text
    )
    pending = list(linked_resources & resources)
    while pending:
        source = pending.pop()
        if source.suffix.lower() not in {
            ".py",
            ".sh",
            ".md",
            ".toml",
            ".yaml",
            ".yml",
            ".json",
        }:
            continue
        source_text = source.read_text(encoding="utf-8", errors="replace")
        for candidate in resources - linked_resources:
            rel = candidate.relative_to(root).as_posix()
            identifiers = {rel, candidate.name}
            if candidate.suffix == ".py":
                identifiers.add(candidate.stem)
            if any(identifier in source_text for identifier in identifiers):
                linked_resources.add(candidate)
                pending.append(candidate)

    for resource in resources:
        rel = resource.relative_to(root).as_posix()
        runtime_metadata = rel == "agents/openai.yaml"
        maintainer_test = (
            resource.parent.name == "scripts" and resource.name.startswith("test_")
        )
        if resource not in linked_resources and not runtime_metadata and not maintainer_test:
            errors.append(f"orphan resource not reachable from SKILL.md: {rel}")

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
    parser.add_argument(
        "--runtime",
        action="append",
        choices=RUNTIMES,
        dest="runtimes",
        help="validation profile; repeat to require compatibility with several runtimes",
    )
    parser.add_argument("skill", type=Path)
    args = parser.parse_args()
    runtimes = tuple(dict.fromkeys(args.runtimes or ("portable",)))
    errors, warnings = validate(args.skill.resolve(), runtimes)
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
