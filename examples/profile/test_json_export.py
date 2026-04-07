"""Test JSON export example."""
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).with_name("json_export.py")


def test_json_export_example_runs():
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "records to" in result.stdout
    assert "Top bottleneck" in result.stdout
