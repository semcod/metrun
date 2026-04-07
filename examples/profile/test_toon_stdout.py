"""Test TOON stdout example."""
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).with_name("toon_stdout.py")


def test_toon_stdout_example_runs():
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "SUMMARY:" in result.stdout
    assert "BOTTLENECKS[" in result.stdout
    assert "handler" in result.stdout
