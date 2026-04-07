"""Tests for metrun.suggestions — Fix Suggestion Engine."""
from metrun.bottleneck import Bottleneck
from metrun.suggestions import Suggestion, suggest, format_suggestions, print_suggestions, _HIGH_SCORE_THRESHOLD

def _make_bottleneck(name: str='func', score: float=5.0, diagnosis: str='🐢 slow execution', language: str='python') -> Bottleneck:
    return Bottleneck(name=name, total_time=1.0, calls=1, score=score, time_pct=50.0, diagnosis=diagnosis, language=language)

class TestSuggest:

    def test_returns_list(self) -> None:
        b = _make_bottleneck()
        result = suggest(b)
        assert isinstance(result, list)

    def test_loop_hotspot_suggestions(self) -> None:
        b = _make_bottleneck(diagnosis='🔥 loop hotspot')
        tips = suggest(b)
        assert tips
        titles = [t.title for t in tips]
        assert any(('lru_cache' in t or 'vectori' in t.lower() or 'Numba' in t for t in titles))

    def test_dependency_bottleneck_suggestions(self) -> None:
        b = _make_bottleneck(diagnosis='🌲 dependency bottleneck')
        tips = suggest(b)
        assert tips
        libraries = [t.library for t in tips]
        assert any(('concurrent' in lib or 'asyncio' in lib for lib in libraries))

    def test_slow_execution_suggestions(self) -> None:
        b = _make_bottleneck(diagnosis='🐢 slow execution')
        tips = suggest(b)
        assert tips
        assert any(('profile' in t.detail.lower() or 'cache' in t.detail.lower() for t in tips))

    def test_nominal_no_suggestions(self) -> None:
        b = _make_bottleneck(diagnosis='✅ nominal', score=1.0)
        tips = suggest(b)
        assert tips == []

    def test_high_score_appends_extra_suggestions(self) -> None:
        b = _make_bottleneck(diagnosis='🔥 loop hotspot', score=_HIGH_SCORE_THRESHOLD + 1.0)
        low_b = _make_bottleneck(diagnosis='🔥 loop hotspot', score=1.0)
        high_tips = suggest(b)
        low_tips = suggest(low_b)
        assert len(high_tips) > len(low_tips)

    def test_high_score_includes_scalene_or_viztracer(self) -> None:
        b = _make_bottleneck(diagnosis='🐢 slow execution', score=_HIGH_SCORE_THRESHOLD + 1.0)
        tips = suggest(b)
        libraries = [t.library.lower() for t in tips]
        assert any(('scalene' in lib or 'viztracer' in lib for lib in libraries))

    def test_suggestion_has_required_fields(self) -> None:
        b = _make_bottleneck(diagnosis='🔥 loop hotspot')
        for tip in suggest(b):
            assert isinstance(tip, Suggestion)
            assert tip.title
            assert tip.detail

    def test_javascript_catalogue_is_language_aware(self) -> None:
        b = _make_bottleneck(diagnosis='🌲 dependency bottleneck', language='javascript')
        tips = suggest(b)
        libraries = {tip.library for tip in tips}
        assert any(('Promise.all' in lib or 'worker_threads' in lib for lib in libraries))
        assert not any(('functools' in lib or 'numpy' in lib or 'numba' in lib for lib in libraries))

    def test_rust_catalogue_is_language_aware(self) -> None:
        b = _make_bottleneck(diagnosis='🐢 slow execution', score=_HIGH_SCORE_THRESHOLD + 1.0, language='rust')
        tips = suggest(b)
        libraries = {tip.library for tip in tips}
        assert any(('cargo-flamegraph' in lib or 'criterion' in lib for lib in libraries))

class TestFormatSuggestions:

    def test_returns_string(self) -> None:
        b = _make_bottleneck(diagnosis='🔥 loop hotspot')
        result = format_suggestions(b.name, suggest(b))
        assert isinstance(result, str)

    def test_contains_function_name(self) -> None:
        b = _make_bottleneck(name='hot_func', diagnosis='🔥 loop hotspot')
        result = format_suggestions(b.name, suggest(b))
        assert 'hot_func' in result

    def test_contains_tip_title(self) -> None:
        b = _make_bottleneck(diagnosis='🔥 loop hotspot')
        tips = suggest(b)
        result = format_suggestions(b.name, tips)
        assert tips[0].title in result

    def test_contains_library_tag(self) -> None:
        b = _make_bottleneck(diagnosis='🔥 loop hotspot')
        tips = [t for t in suggest(b) if t.library]
        result = format_suggestions(b.name, tips)
        assert tips[0].library in result

    def test_contains_example(self) -> None:
        b = _make_bottleneck(diagnosis='🔥 loop hotspot')
        tips = [t for t in suggest(b) if t.example]
        result = format_suggestions(b.name, tips)
        first_example_line = tips[0].example.splitlines()[0]
        assert first_example_line in result

    def test_no_suggestions_message(self) -> None:
        result = format_suggestions('clean_func', [])
        assert 'no specific suggestions' in result

    def test_print_suggestions_produces_output(self, capsys) -> None:
        b = _make_bottleneck(diagnosis='🔥 loop hotspot')
        print_suggestions(b.name, suggest(b))
        captured = capsys.readouterr()
        assert len(captured.out) > 0