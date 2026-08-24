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
RELEASE_RELEVANT_PREFIXES = (
    "skills/",
    "global-files/",
    "assets/",
    ".claude-plugin/",
    ".codex-plugin/",
    ".agents/plugins/",
)
RELEASE_RELEVANT_FILES = {
    "README.md",
    "README.ru.md",
    "AGENTS.md",
    "CLAUDE.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "CODE_OF_CONDUCT.md",
    "scripts/check_package.py",
    "scripts/check_public.py",
    "scripts/prepare_release.py",
    ".github/workflows/validate.yml",
    ".github/workflows/release.yml",
    ".claude/skills/release/SKILL.md",
    ".claude/skills/release/references/checks.md",
    ".claude/skills/release/references/version-confirmation.md",
    ".claude/skills/release/scripts/check_global_files.py",
}


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


def unreleased_section(changelog: str) -> str:
    match = re.search(r"^## Unreleased\s*$", changelog, re.MULTILINE)
    if match is None:
        raise SystemExit("CHANGELOG.md has no '## Unreleased' section")
    start = match.end()
    next_heading = re.search(r"^## ", changelog[start:], re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(changelog)
    return changelog[start:end]


def has_unreleased_entries(changelog: str) -> bool:
    unreleased = unreleased_section(changelog)
    return any(section_body(unreleased, heading) for heading in REQUIRED_SECTIONS)


def is_release_relevant(path: str) -> bool:
    return path in RELEASE_RELEVANT_FILES or path.startswith(RELEASE_RELEVANT_PREFIXES)


def validate_development_changelog(changelog: str, changed_paths: list[str]) -> None:
    relevant = sorted(path for path in changed_paths if is_release_relevant(path))
    if relevant and not has_unreleased_entries(changelog):
        paths = "\n".join(f"- {path}" for path in relevant)
        raise SystemExit(
            "Release-relevant files changed since the current version tag, "
            "but CHANGELOG.md Unreleased is empty:\n"
            f"{paths}\n"
            "Add a user-facing outcome to Unreleased in the same task."
        )


def validate_new_release(changelog: str, notes: str) -> None:
    for heading in REQUIRED_SECTIONS:
        if not section_body(notes, heading):
            raise SystemExit(f"Release section '### {heading}' is empty")

    unreleased = unreleased_section(changelog)
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


def changed_paths_since(ref: str, root: Path = ROOT) -> list[str]:
    output = subprocess.check_output(
        ["git", "diff", "--no-renames", "--name-only", "-z", ref, "--"],
        cwd=root,
    )
    changed = {item.decode() for item in output.split(b"\0") if item}
    untracked = subprocess.check_output(
        ["git", "ls-files", "-z", "--others", "--exclude-standard"],
        cwd=root,
    )
    changed.update(item.decode() for item in untracked.split(b"\0") if item)
    return sorted(changed)


def previous_release_tag(current_tag: str) -> str | None:
    output = subprocess.check_output(
        ["git", "tag", "--list", "v[0-9]*", "--sort=-v:refname"],
        cwd=ROOT,
        text=True,
    )
    return next((tag for tag in output.splitlines() if tag != current_tag), None)


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
    if tag_exists(tag):
        validate_development_changelog(changelog, changed_paths_since(tag))
    else:
        validate_new_release(changelog, notes)
        previous_tag = previous_release_tag(tag)
        if previous_tag:
            print(f"AUDIT: reconcile release notes with every change since {previous_tag}:")
            for path in changed_paths_since(previous_tag):
                print(f"- {path}")
    if args.notes_out is not None:
        args.notes_out.write_text(notes, encoding="utf-8")

    if args.github_output:
        with args.github_output.open("a", encoding="utf-8") as handle:
            handle.write(f"version={claude_version}\n")
            handle.write(f"tag={tag}\n")

    print(f"PASS: release metadata for {tag}")


if __name__ == "__main__":
    main()
