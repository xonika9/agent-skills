#!/usr/bin/env python3
"""Regression tests for shared plugin metadata checks."""

from copy import deepcopy

import check_package


def manifest() -> dict:
    return {
        "name": "x9-agent-skills",
        "version": "2.4.0",
        "description": "Shared description",
        "author": {"name": "xonika9", "url": "https://example.com"},
        "homepage": "https://example.com",
        "repository": "https://example.com/repository",
        "license": "MIT",
        "keywords": ["agent-skills"],
        "skills": "./skills/",
    }


def expect_mismatch(field: str) -> None:
    claude = manifest()
    codex = deepcopy(claude)
    codex[field] = "different" if field != "keywords" else ["different"]
    try:
        check_package.validate_shared_metadata(claude, codex)
    except SystemExit as error:
        assert field in str(error)
        return
    raise AssertionError(f"expected {field} mismatch to fail")


def main() -> None:
    check_package.validate_shared_metadata(manifest(), manifest())
    for field in check_package.SHARED_MANIFEST_FIELDS:
        expect_mismatch(field)
    print("PASS: shared plugin metadata regression scenarios")


if __name__ == "__main__":
    main()
