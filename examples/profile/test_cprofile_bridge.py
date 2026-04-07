"""Test cProfile bridge example."""
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).with_name("cprofile_bridge.py")


def test_cprofile_bridge_example_runs():
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "METRUN PERFORMANCE REPORT" in result.stdout
    assert "compute" in result.stdout
