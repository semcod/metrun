"""Test standalone example works."""
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).with_name("standalone.py")


def test_standalone_example_runs():
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "Processed 1000 items" in result.stdout
    assert "METRUN PERFORMANCE REPORT" in result.stdout
