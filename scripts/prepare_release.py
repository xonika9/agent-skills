#!/usr/bin/env python3
"""Validate release metadata and extract notes for the current plugin version."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
REQUIRED_SECTIONS = (
    "Highlights",
    "Install / update",
    "Compatibility",
    "Breaking changes",
)


def load_version(path: Path) -> str:
    with path.open(encoding="utf-8") as handle:
        version = json.load(handle)["version"]
    if not isinstance(version, str) or not SEMVER.fullmatch(version):
        raise SystemExit(f"Invalid release version in {path.relative_to(ROOT)}: {version!r}")
    return version


def section_body(markdown: str, heading: str) -> str:
    match = re.search(rf"^### {re.escape(heading)}\s*$", markdown, re.MULTILINE)
    if match is None:
        raise SystemExit(f"Missing changelog section '### {heading}'")
    start = match.end()
    next_heading = re.search(r"^#{2,3} ", markdown[start:], re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(markdown)
    return markdown[start:end].strip()


def validate_new_release(changelog: str, notes: str) -> None:
    for heading in REQUIRED_SECTIONS:
        if not section_body(notes, heading):
            raise SystemExit(f"Release section '### {heading}' is empty")

    unreleased_match = re.search(r"^## Unreleased\s*$", changelog, re.MULTILINE)
    if unreleased_match is None:
        raise SystemExit("CHANGELOG.md has no '## Unreleased' section")
    start = unreleased_match.end()
    next_heading = re.search(r"^## ", changelog[start:], re.MULTILINE)
    unreleased = changelog[start : start + next_heading.start()] if next_heading else changelog[start:]
    for heading in REQUIRED_SECTIONS:
        if section_body(unreleased, heading):
            raise SystemExit(
                f"Unreleased section '### {heading}' must be empty before publication"
            )


def tag_exists(tag: str) -> bool:
    return subprocess.run(
        ["git", "show-ref", "--verify", "--quiet", f"refs/tags/{tag}"],
        cwd=ROOT,
        check=False,
    ).returncode == 0


def changelog_notes(version: str) -> tuple[str, str]:
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
    return changelog, notes + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--notes-out", type=Path)
    parser.add_argument("--github-output", type=Path)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate release metadata without writing release notes",
    )
    args = parser.parse_args()
    if not args.check and args.notes_out is None:
        parser.error("--notes-out is required unless --check is used")

    claude_version = load_version(ROOT / ".claude-plugin/plugin.json")
    codex_version = load_version(ROOT / ".codex-plugin/plugin.json")
    if claude_version != codex_version:
        raise SystemExit(
            "Plugin versions differ: "
            f"Claude={claude_version}, Codex={codex_version}"
        )

    tag = f"v{claude_version}"
    changelog, notes = changelog_notes(claude_version)
    if not tag_exists(tag):
        validate_new_release(changelog, notes)
    if args.notes_out is not None:
        args.notes_out.write_text(notes, encoding="utf-8")

    if args.github_output:
        with args.github_output.open("a", encoding="utf-8") as handle:
            handle.write(f"version={claude_version}\n")
            handle.write(f"tag={tag}\n")

    print(f"PASS: release metadata for {tag}")


if __name__ == "__main__":
    main()
