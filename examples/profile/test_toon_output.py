"""Test TOON output example."""
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).with_name("toon_output.py")


def test_toon_example_runs():
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "TOON output saved" in result.stdout
    assert "metrun" in result.stdout.lower()
