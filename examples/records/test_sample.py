"""Test records example works with CLI."""
from pathlib import Path

from click.testing import CliRunner

from metrun.cli import cli


RECORDS = Path(__file__).with_name("sample.jsonl")


def test_cli_scan_records():
    runner = CliRunner()
    result = runner.invoke(cli, ["scan", "--records", str(RECORDS), "-o", "/tmp"])
    assert result.exit_code == 0, result.output
    assert "Scanning records" in result.output
