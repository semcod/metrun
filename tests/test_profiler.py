"""Tests for metrun.profiler — ExecutionTracer."""

import time
import threading

import pytest

from metrun.profiler import ExecutionTracer, FunctionRecord


# ---------------------------------------------------------------------------
# Basic tracing
# ---------------------------------------------------------------------------

def test_trace_decorator_records_call():
    tracer = ExecutionTracer()

    @tracer.trace
    def add(a, b):
        return a + b

    result = add(1, 2)
    assert result == 3

    records = tracer.records
    key = add.__qualname__
    assert key in records
    rec = records[key]
    assert rec.calls == 1
    assert rec.total_time >= 0.0


def test_trace_decorator_multiple_calls():
    tracer = ExecutionTracer()

    @tracer.trace
    def noop():
        pass

    for _ in range(5):
        noop()

    assert tracer.records[noop.__qualname__].calls == 5


def test_trace_decorator_preserves_return_value():
    tracer = ExecutionTracer()

    @tracer.trace
    def multiply(x, y):
        return x * y

    assert multiply(3, 4) == 12


def test_trace_decorator_records_exception():
    tracer = ExecutionTracer()

    @tracer.trace
    def boom():
        raise ValueError("oops")

    with pytest.raises(ValueError):
        boom()

    # Call still registered after exception
    assert tracer.records[boom.__qualname__].calls == 1


def test_section_context_manager():
    tracer = ExecutionTracer()

    with tracer.section("my_section"):
        time.sleep(0.01)

    records = tracer.records
    assert "my_section" in records
    assert records["my_section"].calls == 1
    assert records["my_section"].total_time >= 0.01


def test_section_records_exception():
    tracer = ExecutionTracer()

    with pytest.raises(RuntimeError):
        with tracer.section("bad_section"):
            raise RuntimeError("fail")

    assert tracer.records["bad_section"].calls == 1


# ---------------------------------------------------------------------------
# Parent → child relationships
# ---------------------------------------------------------------------------

def test_parent_child_relationship():
    tracer = ExecutionTracer()

    @tracer.trace
    def child():
        pass

    @tracer.trace
    def parent():
        child()

    parent()

    records = tracer.records
    parent_key = parent.__qualname__
    child_key = child.__qualname__
    assert child_key in records[parent_key].children
    assert parent_key in records[child_key].parents


def test_deep_nesting():
    tracer = ExecutionTracer()

    @tracer.trace
    def grandchild():
        pass

    @tracer.trace
    def child():
        grandchild()

    @tracer.trace
    def grandparent():
        child()

    grandparent()

    records = tracer.records
    assert child.__qualname__ in records[grandparent.__qualname__].children
    assert grandchild.__qualname__ in records[child.__qualname__].children
    assert grandparent.__qualname__ in records[child.__qualname__].parents
    assert child.__qualname__ in records[grandchild.__qualname__].parents


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------

def test_reset_clears_records():
    tracer = ExecutionTracer()

    @tracer.trace
    def func():
        pass

    func()
    assert tracer.records

    tracer.reset()
    assert tracer.records == {}


# ---------------------------------------------------------------------------
# Thread safety
# ---------------------------------------------------------------------------

def test_thread_safety():
    tracer = ExecutionTracer()

    @tracer.trace
    def worker():
        time.sleep(0.001)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert tracer.records[worker.__qualname__].calls == 10


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def test_module_level_trace_and_get_records():
    import metrun

    metrun.reset()

    @metrun.trace
    def sample():
        pass

    sample()
    sample()

    records = metrun.get_records()
    assert "test_profiler.test_module_level_trace_and_get_records.<locals>.sample" in records or \
           any("sample" in k for k in records)


def test_module_level_section():
    import metrun

    metrun.reset()

    with metrun.section("load_data"):
        pass

    records = metrun.get_records()
    assert "load_data" in records


def test_function_record_avg_time():
    rec = FunctionRecord(name="f", total_time=2.0, calls=4)
    assert rec.avg_time == 0.5


def test_function_record_avg_time_zero_calls():
    rec = FunctionRecord(name="f")
    assert rec.avg_time == 0.0
