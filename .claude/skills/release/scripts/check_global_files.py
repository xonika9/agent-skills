#!/usr/bin/env python3
"""Verify shared-core synchronization across personal and published global files."""

from pathlib import Path


START = b"<!-- BEGIN SHARED PERSONAL CORE -->"
END = b"<!-- END SHARED PERSONAL CORE -->"
ROOT = Path(__file__).resolve().parents[4]
FILES = (
    Path.home() / ".config/opencode/AGENTS.md",
    Path.home() / ".claude/CLAUDE.md",
    Path.home() / ".codex/AGENTS.md",
    ROOT / "global-files/opencode/AGENTS.md",
    ROOT / "global-files/claude/CLAUDE.md",
    ROOT / "global-files/codex/AGENTS.md",
)


def extract(path: Path) -> bytes:
    data = path.read_bytes()
    if data.count(START) != 1 or data.count(END) != 1:
        raise ValueError(f"{path}: expected exactly one shared-core marker pair")
    start = data.index(START)
    end = data.index(END, start) + len(END)
    return data[start:end]


def main() -> None:
    try:
        blocks = {path: extract(path) for path in FILES}
    except (OSError, ValueError) as exc:
        print(f"FAIL: {exc}")
        raise SystemExit(1)

    baseline = blocks[FILES[0]]
    drifted = [path for path, block in blocks.items() if block != baseline]
    if drifted:
        print("FAIL: shared personal core is not synchronized:")
        for path in drifted:
            print(f"- {path}")
        raise SystemExit(1)

    print("PASS: personal and published shared cores are byte-identical")


if __name__ == "__main__":
    main()
