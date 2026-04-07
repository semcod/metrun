
CONSTANT_5 = 5.0
CONSTANT_9 = 9.87
CONSTANT_20 = 20
CONSTANT_50 = 50.0
CONSTANT_75 = 75.0
CONSTANT_80 = 80
CONSTANT_500 = 500

"""Tests for metrun.flamegraph — ASCII + SVG flamegraph generators."""

import io
import os
import cProfile
import pstats
import pytest

from metrun.bottleneck import Bottleneck
from metrun.flamegraph import render_ascii, print_ascii, render_svg, render_svg_string


def _make_bottleneck(
    name: str = "func",
    total_time: float = 1.0,
    calls: int = 100,
    score: float = 5.0,
    time_pct: float = 50.0,
    diagnosis: str = "🐢 slow execution",
) -> Bottleneck:
    return Bottleneck(
        name=name,
        total_time=total_time,
        calls=calls,
        score=score,
        time_pct=time_pct,
        diagnosis=diagnosis,
    )


def _make_stats() -> pstats.Stats:
    """Create a real pstats.Stats object with a multi-function call hierarchy."""

    def level_c():
        return sum(range(500))

    def level_b():
        return level_c() + level_c()

    def level_a():
        return level_b() + level_b() + level_b()

    pr = cProfile.Profile()
    pr.enable()
    level_a()
    pr.disable()
    buf = io.StringIO()
    stats = pstats.Stats(pr, stream=buf)
    stats.sort_stats("cumulative")
    return stats


# ---------------------------------------------------------------------------
# ASCII flamegraph
# ---------------------------------------------------------------------------

class TestAsciiFlameGraph:

    def test_returns_string(self):
        b = _make_bottleneck()
        result = render_ascii([b])
        assert isinstance(result, str)

    def test_contains_title(self):
        b = _make_bottleneck()
        result = render_ascii([b], title="MY FLAME")
        assert "MY FLAME" in result

    def test_contains_function_name(self):
        b = _make_bottleneck(name="hot_loop")
        result = render_ascii([b])
        assert "hot_loop" in result

    def test_contains_percentage(self):
        b = _make_bottleneck(time_pct=75.0)
        result = render_ascii([b])
        assert "75.0%" in result

    def test_contains_score(self):
        b = _make_bottleneck(score=9.87)
        result = render_ascii([b])
        assert "9.87" in result

    def test_bar_proportional_to_pct(self):
        full = _make_bottleneck(name="full", time_pct=100.0)
        half = _make_bottleneck(name="half", time_pct=50.0)

        line_full = [l for l in render_ascii([full]).splitlines() if "full" in l][0]
        line_half = [l for l in render_ascii([half]).splitlines() if "half" in l][0]

        filled_full = line_full.count("█")
        filled_half = line_half.count("█")
        assert filled_full > filled_half

    def test_empty_returns_no_data_message(self):
        result = render_ascii([])
        assert "no data" in result.lower()

    def test_top_n_limits_entries(self):
        bottlenecks = [_make_bottleneck(name=f"f{i}") for i in range(5)]
        result = render_ascii(bottlenecks, top_n=2)
        assert "f0" in result
        assert "f1" in result
        assert "f2" not in result

    def test_custom_width(self):
        b = _make_bottleneck(time_pct=100.0)
        result_narrow = render_ascii([b], width=20)
        result_wide = render_ascii([b], width=80)
        assert len(result_narrow) < len(result_wide)

    def test_print_ascii_produces_output(self, capsys):
        b = _make_bottleneck()
        print_ascii([b])
        captured = capsys.readouterr()
        assert len(captured.out) > 0


# ---------------------------------------------------------------------------
# SVG flamegraph (requires flameprof)
# ---------------------------------------------------------------------------

class TestSvgFlamegraph:

    def test_render_svg_creates_file(self, tmp_path):
        stats = _make_stats()
        out = str(tmp_path / "flame.svg")
        render_svg(stats, out)
        assert os.path.exists(out)
        assert os.path.getsize(out) > 0

    def test_render_svg_content_is_svg(self, tmp_path):
        stats = _make_stats()
        out = str(tmp_path / "flame.svg")
        render_svg(stats, out)
        with open(out) as fh:
            content = fh.read()
        assert "<svg" in content

    def test_render_svg_string_returns_svg(self):
        stats = _make_stats()
        svg = render_svg_string(stats)
        assert isinstance(svg, str)
        assert "<svg" in svg

    def test_render_svg_without_flameprof_raises(self, monkeypatch):
        import sys
        # Temporarily hide flameprof
        monkeypatch.setitem(sys.modules, "flameprof", None)
        stats = _make_stats()
        with pytest.raises(ImportError, match="flameprof"):
            render_svg(stats, "/tmp/should_not_exist.svg")

    def test_render_svg_string_without_flameprof_raises(self, monkeypatch):
        import sys
        monkeypatch.setitem(sys.modules, "flameprof", None)
        stats = _make_stats()
        with pytest.raises(ImportError, match="flameprof"):
            render_svg_string(stats)
