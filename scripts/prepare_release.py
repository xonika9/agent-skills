#!/usr/bin/env python3
"""Validate release metadata and extract notes for the current plugin version."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def load_version(path: Path) -> str:
    with path.open(encoding="utf-8") as handle:
        version = json.load(handle)["version"]
    if not isinstance(version, str) or not SEMVER.fullmatch(version):
        raise SystemExit(f"Invalid release version in {path.relative_to(ROOT)}: {version!r}")
    return version


def changelog_notes(version: str) -> str:
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    heading = re.compile(
        rf"^## {re.escape(version)} - (\d{{4}}-\d{{2}}-\d{{2}})\s*$",
        re.MULTILINE,
    )
    match = heading.search(changelog)
    if match is None:
        raise SystemExit(
            f"CHANGELOG.md has no heading '## {version} - YYYY-MM-DD'"
        )

    start = match.end()
    next_heading = re.search(r"^## ", changelog[start:], re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(changelog)
    notes = changelog[start:end].strip()
    if not notes:
        raise SystemExit(f"CHANGELOG.md section {version} has no release notes")
    return notes + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--notes-out", type=Path, required=True)
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()

    claude_version = load_version(ROOT / ".claude-plugin/plugin.json")
    codex_version = load_version(ROOT / ".codex-plugin/plugin.json")
    if claude_version != codex_version:
        raise SystemExit(
            "Plugin versions differ: "
            f"Claude={claude_version}, Codex={codex_version}"
        )

    tag = f"v{claude_version}"
    args.notes_out.write_text(changelog_notes(claude_version), encoding="utf-8")

    if args.github_output:
        with args.github_output.open("a", encoding="utf-8") as handle:
            handle.write(f"version={claude_version}\n")
            handle.write(f"tag={tag}\n")

    print(f"PASS: release metadata for {tag}")


if __name__ == "__main__":
    main()
