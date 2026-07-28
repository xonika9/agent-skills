#!/usr/bin/env python3
"""Reject secrets, personal paths, and private-project naming patterns."""

from pathlib import Path
import re
import subprocess


PATTERNS = {
    "private key": re.compile(
        r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"
    ),
    "AWS access key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "GitHub token": re.compile(
        r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{20,})\b"
    ),
    "API key": re.compile(
        r"\b(?:sk-(?:proj-)?|sk-ant-|AIza)[A-Za-z0-9_-]{20,}\b"
    ),
    "JWT": re.compile(
        r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"
    ),
    "personal macOS home": re.compile(r"/Users/(?!<)[A-Za-z0-9._-]+(?:/|\b)"),
    "personal Linux home": re.compile(r"/home/(?!<)[A-Za-z0-9._-]+(?:/|\b)"),
    "private project naming pattern": re.compile(r"\bagent-for-[a-z0-9-]+\b"),
    "email address": re.compile(
        r"(?<![\w.+-])[\w.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?![\w.-])"
    ),
}


def tracked_files() -> list[Path]:
    output = subprocess.check_output(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"]
    )
    return [Path(item.decode()) for item in output.split(b"\0") if item]


def scan_files() -> list[str]:
    problems = []
    for path in tracked_files():
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in PATTERNS.items():
            for match in pattern.finditer(text):
                value = match.group(0)
                if label == "email address" and value.endswith(
                    "@users.noreply.github.com"
                ):
                    continue
                line = text.count("\n", 0, match.start()) + 1
                problems.append(f"{path}:{line}: {label}")
    return problems


def main() -> None:
    problems = scan_files()
    if problems:
        print("FAIL: public repository check")
        for problem in problems:
            print(f"- {problem}")
        raise SystemExit(1)
    print("PASS: no sensitive public data patterns found")


if __name__ == "__main__":
    main()
