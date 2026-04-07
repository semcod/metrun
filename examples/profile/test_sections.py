"""Test minimal section example."""
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).with_name("sections.py")


def test_sections_example_runs():
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "METRUN PERFORMANCE REPORT" in result.stdout
    assert "data_load" in result.stdout
