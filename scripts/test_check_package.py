#!/usr/bin/env python3
"""Regression tests for shared plugin metadata checks."""

from copy import deepcopy
from pathlib import Path
import struct
import tempfile

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


def expect_interface_failure(codex: dict, field: str) -> None:
    try:
        check_package.validate_codex_interface(codex)
    except SystemExit as error:
        assert field in str(error), str(error)
        return
    raise AssertionError(f"expected invalid {field} to fail")


def test_capabilities_contract() -> None:
    original = check_package.load_json(".codex-plugin/plugin.json")
    valid_empty = deepcopy(original)
    valid_empty["interface"]["capabilities"] = []
    check_package.validate_codex_interface(valid_empty)
    absent = deepcopy(original)
    del absent["interface"]["capabilities"]
    expect_interface_failure(absent, "capabilities")
    for value in (42, "Read", [""], [42]):
        malformed = deepcopy(original)
        malformed["interface"]["capabilities"] = value
        expect_interface_failure(malformed, "capabilities")


def test_declared_png_geometry() -> None:
    valid = (check_package.ROOT / "assets/x9-icon.png").read_bytes()
    with tempfile.TemporaryDirectory() as directory:
        asset = Path(directory) / "icon.png"
        for data in (
            b"This is not a PNG.\n",
            valid[:16] + struct.pack(">II", 48, 49) + valid[24:],
            valid[:16] + struct.pack(">II", 47, 47) + valid[24:],
            valid[:16] + struct.pack(">II", 4097, 4097) + valid[24:],
            valid + b"x" * (5 * 1024 * 1024),
        ):
            asset.write_bytes(data)
            try:
                check_package.validate_png_asset(asset, "icon")
            except SystemExit as error:
                assert "icon" in str(error)
            else:
                raise AssertionError("expected invalid icon to fail")
        asset.write_bytes(valid)
        check_package.validate_png_asset(asset, "icon")


def main() -> None:
    check_package.validate_shared_metadata(manifest(), manifest())
    for field in manifest():
        expect_mismatch(field)
    test_capabilities_contract()
    test_declared_png_geometry()
    print("PASS: shared plugin metadata regression scenarios")


if __name__ == "__main__":
    main()
