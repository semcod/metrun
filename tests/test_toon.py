"""Tests for metrun.toon — TOON format generator."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from metrun.bottleneck import Bottleneck, analyse
from metrun.profiler import FunctionRecord
from metrun.toon import generate_toon, save_toon


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _sample_records() -> dict[str, FunctionRecord]:
    return {
        "handler": FunctionRecord(
            name="handler",
            total_time=0.8,
            calls=1,
            children=["slow_query"],
            parents=[],
        ),
        "slow_query": FunctionRecord(
            name="slow_query",
            total_time=0.75,
            calls=100,
            children=[],
            parents=["handler"],
        ),
    }


def _sample_bottlenecks(records: dict[str, FunctionRecord] | None = None):
    if records is None:
        records = _sample_records()
    return analyse(records)


# ---------------------------------------------------------------------------
# generate_toon
# ---------------------------------------------------------------------------

class TestGenerateToon:
    def test_returns_string(self):
        result = generate_toon(_sample_bottlenecks(), _sample_records())
        assert isinstance(result, str)

    def test_header_contains_metrun(self):
        result = generate_toon(_sample_bottlenecks(), _sample_records())
        assert result.startswith("# metrun")

    def test_header_contains_date(self):
        result = generate_toon(
            _sample_bottlenecks(), _sample_records(), date="2026-04-07"
        )
        assert "2026-04-07" in result

    def test_summary_section_present(self):
        result = generate_toon(_sample_bottlenecks(), _sample_records())
        assert "SUMMARY:" in result
        assert "bottlenecks:" in result
        assert "top_score:" in result
        assert "top_name:" in result
        assert "total_calls:" in result

    def test_bottlenecks_section_present(self):
        result = generate_toon(_sample_bottlenecks(), _sample_records())
        assert "BOTTLENECKS[" in result

    def test_critical_path_section_present(self):
        records = _sample_records()
        result = generate_toon(_sample_bottlenecks(records), records)
        assert "CRITICAL-PATH" in result

    def test_critical_path_absent_without_records(self):
        result = generate_toon(_sample_bottlenecks())
        assert "CRITICAL-PATH" not in result

    def test_suggestions_section_present(self):
        result = generate_toon(_sample_bottlenecks(), _sample_records())
        assert "SUGGESTIONS[" in result

    def test_endpoints_section_present(self):
        records = _sample_records()
        result = generate_toon(_sample_bottlenecks(records), records)
        assert "ENDPOINTS[" in result
        assert "handler" in result

    def test_tree_section_present(self):
        records = _sample_records()
        result = generate_toon(_sample_bottlenecks(records), records)
        assert "TREE:" in result

    def test_empty_bottlenecks(self):
        result = generate_toon([], {})
        assert "BOTTLENECKS[0]: none detected" in result
        assert "bottlenecks: 0" in result

    def test_top_n_limits_output(self):
        records = _sample_records()
        bns = _sample_bottlenecks(records)
        result = generate_toon(bns, records, top_n=1)
        # Only one bottleneck detail line, but SUMMARY still shows total
        assert "bottlenecks: 2" in result  # total count

    def test_language_tag_non_python(self):
        records = {
            "main": FunctionRecord(
                name="main", total_time=1.0, calls=1,
                children=[], parents=[], language="javascript",
            ),
        }
        bns = analyse(records)
        result = generate_toon(bns, records)
        assert "javascript" in result


# ---------------------------------------------------------------------------
# save_toon
# ---------------------------------------------------------------------------

class TestSaveToon:
    def test_writes_file(self):
        content = generate_toon(_sample_bottlenecks(), _sample_records())
        with tempfile.TemporaryDirectory() as tmpdir:
            path = save_toon(content, Path(tmpdir) / "metrun.toon.yaml")
            assert path.exists()
            assert path.read_text(encoding="utf-8") == content

    def test_creates_parent_dirs(self):
        content = "# test"
        with tempfile.TemporaryDirectory() as tmpdir:
            path = save_toon(content, Path(tmpdir) / "sub" / "metrun.toon.yaml")
            assert path.exists()


# ---------------------------------------------------------------------------
# CLI scan command
# ---------------------------------------------------------------------------

class TestScanCLI:
    def test_scan_demo_script(self, tmp_path):
        from click.testing import CliRunner
        from metrun.cli import cli

        demo = Path(__file__).resolve().parent.parent / "demo.py"
        if not demo.exists():
            pytest.skip("demo.py not found")

        runner = CliRunner()
        out_dir = str(tmp_path)
        result = runner.invoke(cli, ["scan", str(demo), "-o", out_dir])
        assert result.exit_code == 0, result.output
        toon_file = tmp_path / "metrun.toon.yaml"
        assert toon_file.exists()
        content = toon_file.read_text()
        assert "# metrun" in content
        assert "SUMMARY:" in content
        assert "BOTTLENECKS[" in content

    def test_scan_records_file(self, tmp_path):
        from click.testing import CliRunner
        from metrun.cli import cli
        from metrun.records_io import save_records_json

        records = _sample_records()
        rec_file = tmp_path / "records.json"
        save_records_json(records, str(rec_file))

        runner = CliRunner()
        out_dir = str(tmp_path / "out")
        result = runner.invoke(
            cli, ["scan", "--records", str(rec_file), "-o", out_dir]
        )
        assert result.exit_code == 0, result.output
        toon_file = Path(out_dir) / "metrun.toon.yaml"
        assert toon_file.exists()

    def test_scan_no_args_errors(self):
        from click.testing import CliRunner
        from metrun.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["scan"])
        assert result.exit_code != 0
