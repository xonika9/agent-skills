#!/usr/bin/env python3
"""Public-data checks must inspect their repository from any working directory."""

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        scripts = root / "scripts"
        scripts.mkdir()
        source = Path(__file__).with_name("check_public.py")
        script = scripts / source.name
        shutil.copy2(source, script)
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        sample = root / "sample.md"
        sample.write_text("private path: " + "/Users/" + "fixture/private\n")
        for cwd in (root, scripts):
            result = subprocess.run(
                [sys.executable, "-B", str(script)],
                cwd=cwd,
                capture_output=True,
                text=True,
                check=False,
            )
            assert result.returncode == 1, (cwd.name, result.stdout, result.stderr)
            assert "sample.md:1: personal macOS home" in result.stdout
            assert str(root) not in result.stdout
        sample.write_text("placeholder: /Users/<user>/private\n")
        result = subprocess.run(
            [sys.executable, "-B", str(script)],
            cwd=scripts,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, (result.stdout, result.stderr)
    print("PASS: public-data repository scope regression scenarios")


if __name__ == "__main__":
    main()
