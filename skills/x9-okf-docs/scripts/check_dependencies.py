#!/usr/bin/env python3
"""Check the Python and Ruby that the OKF scripts need."""

from __future__ import annotations

import shutil
import subprocess
import sys

SAMPLE = "generated: { by: human:sample, at: 2026-01-01T00:00:00Z }\n"


def main() -> int:
    if sys.version_info < (3, 9):
        print(f"BLOCKED: Python 3.9 or newer is required; this is {sys.version.split()[0]}")
        return 1
    print(f"PASS: Python {sys.version.split()[0]}")

    ruby = shutil.which("ruby")
    if ruby is None:
        print("BLOCKED: Ruby with Psych is required to read YAML frontmatter")
        return 1
    probe = subprocess.run(
        [ruby, "-e", 'require "psych"; print Psych::VERSION, " ", Psych::LIBYAML_VERSION'],
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode != 0:
        detail = probe.stderr.strip().splitlines()[-1:] or ["Psych could not be loaded"]
        print(f"BLOCKED: Ruby Psych is unavailable: {detail[0]}")
        return 1
    psych, _, libyaml = probe.stdout.partition(" ")
    print(f"PASS: Ruby Psych {psych}, libyaml {libyaml}")

    sample = subprocess.run(
        [ruby, "-ryaml", "-e", "YAML.safe_load(STDIN.read, permitted_classes: [Time])"],
        input=SAMPLE,
        capture_output=True,
        text=True,
        check=False,
    )
    if sample.returncode != 0:
        print(
            "NOTE: this libyaml cannot read an unquoted value containing ':' inside { } or [ ]; "
            "such existing headers are reported as invalid YAML until the value is quoted"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
