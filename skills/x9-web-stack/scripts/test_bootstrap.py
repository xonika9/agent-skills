#!/usr/bin/env python3
"""Bootstrap precondition regressions without package installs or subprocesses."""

import contextlib
import io
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import bootstrap


class PrerequisiteTests(unittest.TestCase):
    def test_missing_node_rejects_before_commands_or_project_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "project"
            stderr = io.StringIO()
            available = {"bun": "/tools/bun", "git": "/tools/git"}
            with patch.object(sys, "argv", ["bootstrap.py", str(target), "--bun-version", "1.4.2"]), \
                 patch.object(bootstrap.shutil, "which", side_effect=available.get), \
                 patch.object(bootstrap.subprocess, "run", side_effect=AssertionError(
                     "Missing Node must be rejected before invoking external commands"
                 )) as commands, contextlib.redirect_stderr(stderr):
                self.assertEqual(bootstrap.main(), 2)
            self.assertIn("node", stderr.getvalue().lower())
            self.assertFalse(target.exists(), "Missing Node must not leave a partial project")
            commands.assert_not_called()


@unittest.skipUnless(shutil.which("git"), "git is required")
class NestedRepositoryTests(unittest.TestCase):
    def test_target_inside_another_repository_is_rejected_before_creating_files(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory).resolve()
            subprocess.run(["git", "init", "-q", str(parent)], check=True)
            target = parent / "missing" / "project"
            stderr = io.StringIO()
            available = {"bun": "/tools/bun", "node": "/tools/node", "git": shutil.which("git")}
            with patch.object(sys, "argv", ["bootstrap.py", str(target), "--bun-version", "1.4.2"]), \
                 patch.object(bootstrap.shutil, "which", side_effect=available.get), \
                 contextlib.redirect_stderr(stderr):
                self.assertEqual(bootstrap.main(), 2)
            self.assertIn(str(parent), stderr.getvalue())
            self.assertFalse((parent / "missing").exists(), "Nothing may be created inside the parent repository")


if __name__ == "__main__":
    unittest.main()
