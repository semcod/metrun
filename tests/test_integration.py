"""
Integration test: full pipeline from tracing to report generation.
"""

import time

import pytest

import metrun
from metrun import trace, section, get_records, reset, analyse, print_report, generate_report


@pytest.fixture(autouse=True)
def clean_default_tracer():
    """Ensure the default tracer is clean before and after each test."""
    reset()
    yield
    reset()


# ---------------------------------------------------------------------------
# End-to-end: decorator → analyse → report
# ---------------------------------------------------------------------------

def test_full_pipeline_decorator():
    @trace
    def compute():
        total = 0
        for i in range(100):
            total += i
        return total

    compute()

    records = get_records()
    assert records

    bottlenecks = analyse(records)
    assert bottlenecks
    report = generate_report(bottlenecks)
    assert "compute" in report or any("compute" in b.name for b in bottlenecks)


def test_full_pipeline_section():
    with section("data_load"):
        time.sleep(0.01)

    records = get_records()
    assert "data_load" in records

    bottlenecks = analyse(records)
    assert any(b.name == "data_load" for b in bottlenecks)


def test_full_pipeline_parent_child_relationship():
    @trace
    def db_query():
        time.sleep(0.001)

    @trace
    def handler():
        for _ in range(3):
            db_query()

    handler()

    records = get_records()
    bottlenecks = analyse(records)

    names = [b.name for b in bottlenecks]
    assert any("handler" in n for n in names)
    assert any("db_query" in n for n in names)


def test_full_pipeline_report_output(capsys):
    @trace
    def slow_function():
        time.sleep(0.02)

    slow_function()

    bottlenecks = analyse(get_records())
    print_report(bottlenecks)

    captured = capsys.readouterr()
    assert "METRUN PERFORMANCE REPORT" in captured.out
    assert "slow_function" in captured.out


def test_multiple_calls_in_loop():
    """Verify loop hotspot detection triggers correctly."""
    from metrun.profiler import ExecutionTracer
    from metrun.bottleneck import LOOP_THRESHOLD

    tracer = ExecutionTracer()

    @tracer.trace
    def hot():
        pass

    for _ in range(LOOP_THRESHOLD):
        hot()

    bottlenecks = analyse(tracer.records)
    assert bottlenecks
    assert "loop hotspot" in bottlenecks[0].diagnosis


def test_dependency_bottleneck_integration():
    """Build a fan-out structure and verify dependency bottleneck detection."""
    from metrun.profiler import ExecutionTracer
    from metrun.bottleneck import DEP_THRESHOLD

    tracer = ExecutionTracer()

    # Create child functions as proper top-level-style callables
    def make_child(name):
        def child():
            pass
        child.__name__ = name
        child.__qualname__ = name
        return tracer.trace(child)

    child_funcs = [make_child(f"child_{i}") for i in range(DEP_THRESHOLD + 1)]

    @tracer.trace
    def root():
        for cf in child_funcs:
            cf()

    root()

    bottlenecks = analyse(tracer.records)
    root_b = next(b for b in bottlenecks if b.name == root.__qualname__)
    assert "dependency bottleneck" in root_b.diagnosis
