"""Tests for metrun.suggestions — Fix Suggestion Engine."""

import pytest

from metrun.bottleneck import Bottleneck
from metrun.suggestions import (
    Suggestion,
    suggest,
    format_suggestions,
    print_suggestions,
    _HIGH_SCORE_THRESHOLD,
)


def _make_bottleneck(
    name: str = "func",
    score: float = 5.0,
    diagnosis: str = "🐢 slow execution",
) -> Bottleneck:
    return Bottleneck(
        name=name,
        total_time=1.0,
        calls=1,
        score=score,
        time_pct=50.0,
        diagnosis=diagnosis,
    )


# ---------------------------------------------------------------------------
# suggest()
# ---------------------------------------------------------------------------

class TestSuggest:

    def test_returns_list(self):
        b = _make_bottleneck()
        result = suggest(b)
        assert isinstance(result, list)

    def test_loop_hotspot_suggestions(self):
        b = _make_bottleneck(diagnosis="🔥 loop hotspot")
        tips = suggest(b)
        assert tips
        titles = [t.title for t in tips]
        assert any("lru_cache" in t or "vectori" in t.lower() or "Numba" in t for t in titles)

    def test_dependency_bottleneck_suggestions(self):
        b = _make_bottleneck(diagnosis="🌲 dependency bottleneck")
        tips = suggest(b)
        assert tips
        libraries = [t.library for t in tips]
        assert any("concurrent" in lib or "asyncio" in lib for lib in libraries)

    def test_slow_execution_suggestions(self):
        b = _make_bottleneck(diagnosis="🐢 slow execution")
        tips = suggest(b)
        assert tips
        assert any("profile" in t.detail.lower() or "cache" in t.detail.lower() for t in tips)

    def test_nominal_no_suggestions(self):
        b = _make_bottleneck(diagnosis="✅ nominal", score=1.0)
        tips = suggest(b)
        assert tips == []

    def test_high_score_appends_extra_suggestions(self):
        b = _make_bottleneck(
            diagnosis="🔥 loop hotspot",
            score=_HIGH_SCORE_THRESHOLD + 1.0,
        )
        low_b = _make_bottleneck(
            diagnosis="🔥 loop hotspot",
            score=1.0,
        )
        high_tips = suggest(b)
        low_tips = suggest(low_b)
        assert len(high_tips) > len(low_tips)

    def test_high_score_includes_scalene_or_viztracer(self):
        b = _make_bottleneck(
            diagnosis="🐢 slow execution",
            score=_HIGH_SCORE_THRESHOLD + 1.0,
        )
        tips = suggest(b)
        libraries = [t.library.lower() for t in tips]
        assert any("scalene" in lib or "viztracer" in lib for lib in libraries)

    def test_suggestion_has_required_fields(self):
        b = _make_bottleneck(diagnosis="🔥 loop hotspot")
        for tip in suggest(b):
            assert isinstance(tip, Suggestion)
            assert tip.title
            assert tip.detail


# ---------------------------------------------------------------------------
# format_suggestions()
# ---------------------------------------------------------------------------

class TestFormatSuggestions:

    def test_returns_string(self):
        b = _make_bottleneck(diagnosis="🔥 loop hotspot")
        result = format_suggestions(b.name, suggest(b))
        assert isinstance(result, str)

    def test_contains_function_name(self):
        b = _make_bottleneck(name="hot_func", diagnosis="🔥 loop hotspot")
        result = format_suggestions(b.name, suggest(b))
        assert "hot_func" in result

    def test_contains_tip_title(self):
        b = _make_bottleneck(diagnosis="🔥 loop hotspot")
        tips = suggest(b)
        result = format_suggestions(b.name, tips)
        assert tips[0].title in result

    def test_contains_library_tag(self):
        b = _make_bottleneck(diagnosis="🔥 loop hotspot")
        tips = [t for t in suggest(b) if t.library]
        result = format_suggestions(b.name, tips)
        assert tips[0].library in result

    def test_contains_example(self):
        b = _make_bottleneck(diagnosis="🔥 loop hotspot")
        tips = [t for t in suggest(b) if t.example]
        result = format_suggestions(b.name, tips)
        # At least one line from the example should appear
        first_example_line = tips[0].example.splitlines()[0]
        assert first_example_line in result

    def test_no_suggestions_message(self):
        result = format_suggestions("clean_func", [])
        assert "no specific suggestions" in result

    def test_print_suggestions_produces_output(self, capsys):
        b = _make_bottleneck(diagnosis="🔥 loop hotspot")
        print_suggestions(b.name, suggest(b))
        captured = capsys.readouterr()
        assert len(captured.out) > 0
