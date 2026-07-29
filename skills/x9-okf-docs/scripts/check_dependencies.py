#!/usr/bin/env python3
"""Preflight required and optional OKF migration dependencies."""

from __future__ import annotations

import shutil
import subprocess
import sys


def main() -> int:
    ruby = shutil.which("ruby")
    if ruby is None:
        print("BLOCKED: Ruby with Psych is required for strict YAML inspection")
        return 1

    psych = subprocess.run(
        [ruby, "-e", 'require "psych"; print Psych::VERSION'],
        capture_output=True,
        text=True,
        check=False,
    )
    if psych.returncode != 0:
        detail = psych.stderr.strip() or "Psych could not be loaded"
        print(f"BLOCKED: Ruby Psych is unavailable: {detail}")
        return 1

    print(f"PASS: Python {sys.version_info.major}.{sys.version_info.minor}")
    print(f"PASS: Ruby Psych {psych.stdout.strip()}")

    git = shutil.which("git")
    if git is None:
        print("DEGRADED: Git is unavailable; generated.at inventory suggestions will use filesystem modification time")
    else:
        print(f"PASS: Git available at {git}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
