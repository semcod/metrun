CONSTANT_3 = 3.0
MIN_5 = 5.0
CONSTANT_7 = 7.0
'Tests for metrun.bottleneck — BottleneckEngine.'
from metrun.profiler import FunctionRecord
from metrun.bottleneck import analyse, LOOP_THRESHOLD, DEP_THRESHOLD

def _make_record(name: str, total_time: float=0.1, calls: int=1, children: list | None=None, parents: list | None=None) -> FunctionRecord:
    rec = FunctionRecord(name=name, total_time=total_time, calls=calls, children=children or [], parents=parents or [])
    return rec

def test_analyse_empty_records() -> None:
    result = analyse({})
    assert result == []

def test_analyse_single_function() -> None:
    records = {'foo': _make_record('foo', total_time=1.0, calls=10)}
    result = analyse(records)
    assert len(result) == 1
    b = result[0]
    assert b.name == 'foo'
    assert b.calls == 10
    assert b.score > 0

def test_analyse_sorted_by_score_descending() -> None:
    records = {'fast': _make_record('fast', total_time=0.01, calls=1), 'slow': _make_record('slow', total_time=5.0, calls=1)}
    result = analyse(records)
    assert result[0].name == 'slow'
    assert result[0].score >= result[1].score

def test_time_pct_sums_to_100_for_roots() -> None:
    records = {'a': _make_record('a', total_time=3.0, calls=1), 'b': _make_record('b', total_time=7.0, calls=1)}
    result = analyse(records)
    total_pct = sum((b.time_pct for b in result))
    assert abs(total_pct - 100.0) < 0.5

def test_diagnosis_loop_hotspot() -> None:
    records = {'hot_loop': _make_record('hot_loop', total_time=0.5, calls=LOOP_THRESHOLD)}
    result = analyse(records)
    assert 'loop hotspot' in result[0].diagnosis

def test_diagnosis_dependency_bottleneck() -> None:
    children = [f'child_{i}' for i in range(DEP_THRESHOLD)]
    records = {'parent': _make_record('parent', total_time=1.0, calls=1, children=children)}
    for child in children:
        records[child] = _make_record(child, total_time=0.1, calls=1, parents=['parent'])
    result = analyse(records)
    parent_result = next((b for b in result if b.name == 'parent'))
    assert 'dependency bottleneck' in parent_result.diagnosis

def test_diagnosis_slow_execution() -> None:
    records = {'slow_fn': _make_record('slow_fn', total_time=1.0, calls=1)}
    result = analyse(records)
    assert 'slow execution' in result[0].diagnosis

def test_diagnosis_nominal() -> None:
    records = {'nominal_fn': _make_record('nominal_fn', total_time=0.001, calls=1)}
    records['dominant'] = _make_record('dominant', total_time=10.0, calls=2)
    result = analyse(records)
    nominal = next((b for b in result if b.name == 'nominal_fn'))
    assert nominal.diagnosis == '✅ nominal'

def test_score_increases_with_calls() -> None:
    low = _make_record('low', total_time=0.5, calls=10)
    high = _make_record('high', total_time=0.5, calls=LOOP_THRESHOLD)
    records_low = {'low': low}
    records_high = {'high': high}
    score_low = analyse(records_low)[0].score
    score_high = analyse(records_high)[0].score
    assert score_high > score_low

def test_score_increases_with_more_children() -> None:
    few_children = _make_record('few', total_time=1.0, calls=1, children=['c1'])
    many_children = _make_record('many', total_time=1.0, calls=1, children=[f'c{i}' for i in range(DEP_THRESHOLD + 2)])
    score_few = analyse({'few': few_children})[0].score
    score_many = analyse({'many': many_children})[0].score
    assert score_many > score_few

def test_bottleneck_preserves_children_and_parents() -> None:
    records = {'parent': _make_record('parent', total_time=1.0, calls=1, children=['child']), 'child': _make_record('child', total_time=0.5, calls=5, parents=['parent'])}
    result = analyse(records)
    parent_b = next((b for b in result if b.name == 'parent'))
    child_b = next((b for b in result if b.name == 'child'))
    assert 'child' in parent_b.children
    assert 'parent' in child_b.parents