"""Test minimal example works with installed metrun."""
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).with_name("minimal.py")


def test_minimal_example_runs():
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "METRUN PERFORMANCE REPORT" in result.stdout
    assert "handler" in result.stdout
