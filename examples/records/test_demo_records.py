from pathlib import Path

from click.testing import CliRunner

from metrun.cli import cli


RECORDS = Path(__file__).with_name("demo.jsonl")


def test_records_example_scans_to_toon(tmp_path):
    runner = CliRunner()
    out_dir = tmp_path / "scan"
    result = runner.invoke(cli, ["scan", "--records", str(RECORDS), "-o", str(out_dir)])
    assert result.exit_code == 0, result.output

    toon_path = out_dir / "metrun.toon.yaml"
    assert toon_path.exists()

    content = toon_path.read_text(encoding="utf-8")
    assert "SUMMARY:" in content
    assert "BOTTLENECKS[" in content
    assert "ENDPOINTS[" in content
    assert "handler" in content
    assert "slow_query" in content
