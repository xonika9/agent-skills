#!/usr/bin/env python3
"""Verify that every public skill is linked into the personal skill directories.

Run locally from the repository, or on another machine by piping this file to
`python3 -` with `--names` so the expected set comes from the local candidate.
"""

import argparse
import os
from pathlib import Path


AGENTS_DIR = Path.home() / ".agents/skills"
CLAUDE_DIR = Path.home() / ".claude/skills"
# Skills that must not be exposed to Claude Code, with the reason.
CLAUDE_EXCLUDED = {"x9-opencode-sessions": "OpenCode V2 only"}


def repo_skills_root() -> Path:
    return Path(__file__).resolve().parents[4] / "skills"


def discover_root() -> Path:
    """Infer the canonical skills root from existing x9-* links."""
    roots = {
        entry.resolve().parent
        for entry in AGENTS_DIR.glob("x9-*")
        if entry.is_symlink() and (entry.resolve() / "SKILL.md").is_file()
    }
    if len(roots) != 1:
        found = ", ".join(sorted(map(str, roots))) or "none"
        raise SystemExit(f"FAIL: cannot infer one skills root from {AGENTS_DIR} (found: {found})")
    return roots.pop()


def uses_relative_links(directory: Path) -> bool:
    for entry in directory.glob("x9-*"):
        if entry.is_symlink():
            return not os.path.isabs(os.readlink(entry))
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--names", nargs="+", help="Expected skill names; implies root discovery")
    parser.add_argument("--skills-root", type=Path, help="Canonical skills directory")
    parser.add_argument("--fix", action="store_true", help="Create missing links; never replace entries")
    args = parser.parse_args()

    if args.skills_root:
        root = args.skills_root.resolve()
    elif args.names:
        root = discover_root()
    else:
        root = repo_skills_root()
    names = sorted(args.names or (p.name for p in root.iterdir() if (p / "SKILL.md").is_file()))

    expected = {
        AGENTS_DIR: {name: root / name for name in names},
        CLAUDE_DIR: {
            name: AGENTS_DIR / name for name in names if name not in CLAUDE_EXCLUDED
        },
    }
    problems, created = [], []

    for directory, targets in expected.items():
        relative = uses_relative_links(directory)
        for name, target in targets.items():
            entry = directory / name
            if os.path.lexists(entry):
                if entry.resolve() != (root / name).resolve() or not (entry / "SKILL.md").is_file():
                    problems.append(f"{entry}: does not resolve to {root / name}")
                continue
            if not (root / name / "SKILL.md").is_file():
                problems.append(f"{entry}: missing, and {root / name} is absent (sync pending?)")
            elif args.fix:
                directory.mkdir(parents=True, exist_ok=True)
                link = os.path.relpath(target, directory) if relative else str(target)
                entry.symlink_to(link)
                created.append(f"{entry} -> {link}")
            else:
                problems.append(f"{entry}: missing")

        for entry in sorted(directory.glob("x9-*")):
            if directory == CLAUDE_DIR and entry.name in CLAUDE_EXCLUDED:
                problems.append(
                    f"{entry}: excluded from Claude Code ({CLAUDE_EXCLUDED[entry.name]})"
                )
                continue
            if entry.name in targets or not entry.is_symlink():
                continue
            if not entry.exists():
                problems.append(f"{entry}: broken link")
            elif entry.resolve().parent == root and entry.name not in names:
                problems.append(f"{entry}: points to a skill that is no longer published")

    for line in created:
        print(f"CREATED: {line}")
    if problems:
        print("FAIL: personal skill links are incomplete:")
        for problem in problems:
            print(f"- {problem}")
        raise SystemExit(1)
    print(f"PASS: {len(names)} skills linked from {AGENTS_DIR} and {CLAUDE_DIR} (Claude Code excludes: {', '.join(CLAUDE_EXCLUDED)})")


if __name__ == "__main__":
    main()
