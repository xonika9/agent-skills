#!/usr/bin/env python3
"""Regression tests for byte-exact shared-core extraction."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from check_globals import extract


START = b"<!-- BEGIN SHARED PERSONAL CORE -->"
END = b"<!-- END SHARED PERSONAL CORE -->"


class ExtractTests(unittest.TestCase):
    def write(self, directory: str, name: str, data: bytes) -> Path:
        path = Path(directory) / name
        path.write_bytes(data)
        return path

    def test_preserves_line_endings(self):
        with TemporaryDirectory() as directory:
            lf = self.write(directory, "lf.md", START + b"\nrule\n" + END)
            crlf = self.write(directory, "crlf.md", START + b"\r\nrule\r\n" + END)
            self.assertNotEqual(extract(lf), extract(crlf))

    def test_rejects_duplicate_marker_pairs(self):
        with TemporaryDirectory() as directory:
            path = self.write(directory, "duplicate.md", START + END + START + END)
            with self.assertRaises(ValueError):
                extract(path)


if __name__ == "__main__":
    unittest.main()
