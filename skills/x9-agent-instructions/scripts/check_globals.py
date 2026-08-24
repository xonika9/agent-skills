#!/usr/bin/env python3
"""Verify that the bounded shared personal core is identical across runtimes."""

from pathlib import Path
import sys

START = b"<!-- BEGIN SHARED PERSONAL CORE -->"
END = b"<!-- END SHARED PERSONAL CORE -->"
FILES = (
    Path.home() / ".config/opencode/AGENTS.md",
    Path.home() / ".claude/CLAUDE.md",
    Path.home() / ".codex/AGENTS.md",
)


def extract(path: Path):
    data = path.read_bytes()
    if data.count(START) != 1 or data.count(END) != 1:
        raise ValueError(f"{path}: expected exactly one shared-core marker pair")
    start = data.index(START)
    end = data.index(END, start) + len(END)
    return data[start:end]


def main():
    try:
        blocks = [extract(path) for path in FILES]
    except (OSError, ValueError) as exc:
        print(f"FAIL: {exc}")
        raise SystemExit(1)
    if any(block != blocks[0] for block in blocks[1:]):
        print("FAIL: shared personal core differs across OpenCode, Claude Code, and Codex")
        raise SystemExit(1)
    print("PASS: shared personal core is byte-identical")


if __name__ == "__main__":
    main()
