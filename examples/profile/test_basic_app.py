import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).with_name("basic_app.py")


def test_basic_profile_example_runs_and_prints_report():
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "METRUN PERFORMANCE REPORT" in result.stdout
    assert "handler" in result.stdout
    assert "slow_query" in result.stdout
    assert "Dependency Graph" in result.stdout
