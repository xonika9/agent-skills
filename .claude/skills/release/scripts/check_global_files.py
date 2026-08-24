#!/usr/bin/env python3
"""Verify shared-core and installed-file synchronization across runtimes."""

import argparse
from pathlib import Path


START = b"<!-- BEGIN SHARED PERSONAL CORE -->"
END = b"<!-- END SHARED PERSONAL CORE -->"
ROOT = Path(__file__).resolve().parents[4]
PUBLISHED_FILES = (
    ROOT / "global-files/opencode/AGENTS.md",
    ROOT / "global-files/claude/CLAUDE.md",
    ROOT / "global-files/codex/AGENTS.md",
)
INSTALLED_FILES = (
    Path.home() / ".config/opencode/AGENTS.md",
    Path.home() / ".claude/CLAUDE.md",
    Path.home() / ".codex/AGENTS.md",
)


def extract(path: Path) -> bytes:
    data = path.read_bytes()
    if data.count(START) != 1 or data.count(END) != 1:
        raise ValueError(f"{path}: expected exactly one shared-core marker pair")
    start = data.index(START)
    end = data.index(END, start) + len(END)
    return data[start:end]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--published-only",
        action="store_true",
        help="Check only the three repository-owned global files",
    )
    args = parser.parse_args()
    files = PUBLISHED_FILES if args.published_only else INSTALLED_FILES + PUBLISHED_FILES
    try:
        blocks = {path: extract(path) for path in files}
    except (OSError, ValueError) as exc:
        print(f"FAIL: {exc}")
        raise SystemExit(1)

    baseline = blocks[files[0]]
    drifted = [path for path, block in blocks.items() if block != baseline]
    if drifted:
        print("FAIL: shared personal core is not synchronized:")
        for path in drifted:
            print(f"- {path}")
        raise SystemExit(1)

    if not args.published_only:
        mismatched = [
            (installed, published)
            for installed, published in zip(INSTALLED_FILES, PUBLISHED_FILES)
            if installed.read_bytes() != published.read_bytes()
        ]
        if mismatched:
            print("FAIL: installed global files differ from their published sources:")
            for installed, published in mismatched:
                print(f"- {installed} != {published}")
            raise SystemExit(1)

    if args.published_only:
        print("PASS: published shared cores are byte-identical")
    else:
        print("PASS: installed globals match published files and all shared cores are byte-identical")


if __name__ == "__main__":
    main()
