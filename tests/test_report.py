"""Tests for metrun.report — Human Report Generator."""
from metrun.bottleneck import Bottleneck
from metrun.report import generate_report, print_report

def _make_bottleneck(name: str='func', total_time: float=1.0, calls: int=100, score: float=5.0, time_pct: float=50.0, diagnosis: str='🐢 slow execution', children: list | None=None, parents: list | None=None) -> Bottleneck:
    return Bottleneck(name=name, total_time=total_time, calls=calls, score=score, time_pct=time_pct, diagnosis=diagnosis, children=children or [], parents=parents or [])

def test_generate_report_returns_string() -> None:
    b = _make_bottleneck()
    report = generate_report([b])
    assert isinstance(report, str)

def test_report_contains_title() -> None:
    b = _make_bottleneck()
    report = generate_report([b], title='MY REPORT')
    assert 'MY REPORT' in report

def test_report_contains_function_name() -> None:
    b = _make_bottleneck(name='slow_query')
    report = generate_report([b])
    assert 'slow_query' in report

def test_report_contains_time() -> None:
    b = _make_bottleneck(total_time=0.82, time_pct=78.2)
    report = generate_report([b])
    assert '0.8200s' in report
    assert '78.2%' in report

def test_report_contains_calls() -> None:
    b = _make_bottleneck(calls=12430)
    report = generate_report([b])
    assert '12,430' in report

def test_report_contains_score() -> None:
    b = _make_bottleneck(score=12.9)
    report = generate_report([b])
    assert '12.9' in report

def test_report_contains_diagnosis() -> None:
    b = _make_bottleneck(diagnosis='🔥 loop hotspot')
    report = generate_report([b])
    assert '🔥 loop hotspot' in report

def test_report_empty_bottlenecks() -> None:
    report = generate_report([])
    assert 'No hotspots detected' in report

def test_severity_icon_loop_hotspot() -> None:
    b = _make_bottleneck(diagnosis='🔥 loop hotspot')
    report = generate_report([b])
    assert '🔴' in report

def test_severity_icon_dependency_bottleneck() -> None:
    b = _make_bottleneck(diagnosis='🌲 dependency bottleneck')
    report = generate_report([b])
    assert '🟠' in report

def test_severity_icon_slow_execution() -> None:
    b = _make_bottleneck(diagnosis='🐢 slow execution')
    report = generate_report([b])
    assert '🟡' in report

def test_severity_icon_nominal() -> None:
    b = _make_bottleneck(diagnosis='✅ nominal')
    report = generate_report([b])
    assert '🟢' in report

def test_top_n_limits_output() -> None:
    bottlenecks = [_make_bottleneck(name=f'f{i}', score=float(10 - i)) for i in range(5)]
    report = generate_report(bottlenecks, top_n=2)
    assert 'f0' in report
    assert 'f1' in report
    assert 'f2' not in report

def test_dependency_graph_shown_when_children_exist() -> None:
    b = _make_bottleneck(name='parent', children=['child'])
    report = generate_report([b], show_graph=True)
    assert 'Dependency Graph' in report
    assert 'parent' in report
    assert 'child' in report

def test_dependency_graph_hidden_when_show_graph_false() -> None:
    b = _make_bottleneck(name='parent', children=['child'])
    report = generate_report([b], show_graph=False)
    assert 'Dependency Graph' not in report

def test_dependency_graph_not_shown_when_no_children() -> None:
    b = _make_bottleneck(name='leaf', children=[])
    report = generate_report([b], show_graph=True)
    assert 'Dependency Graph' not in report

def test_summary_contains_top_bottleneck() -> None:
    bottlenecks = [_make_bottleneck(name='worst', score=9.0), _make_bottleneck(name='ok', score=2.0)]
    report = generate_report(bottlenecks)
    assert 'worst' in report
    lines = report.splitlines()
    summary_idx = next((i for i, l in enumerate(lines) if 'Summary' in l))
    summary_section = '\n'.join(lines[summary_idx:])
    assert 'worst' in summary_section

def test_report_shows_parent_in_called_by() -> None:
    b = _make_bottleneck(name='child', parents=['parent_func'])
    report = generate_report([b])
    assert 'parent_func' in report
    assert 'called by' in report

def test_print_report_produces_output(capsys) -> None:
    b = _make_bottleneck()
    print_report([b])
    captured = capsys.readouterr()
    assert len(captured.out) > 0