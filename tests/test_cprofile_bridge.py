"""Tests for metrun.cprofile_bridge — CProfileBridge."""

import time
import pytest
from metrun.cprofile_bridge import CProfileBridge
from metrun.profiler import FunctionRecord


# ---------------------------------------------------------------------------
# profile_func decorator
# ---------------------------------------------------------------------------

def test_profile_func_records_call():
    bridge = CProfileBridge()

    @bridge.profile_func
    def add(a, b):
        return a + b

    result = add(1, 2)
    assert result == 3

    records = bridge.to_records()
    assert any("add" in name for name in records)


def test_profile_func_preserves_return_value():
    bridge = CProfileBridge()

    @bridge.profile_func
    def multiply(x, y):
        return x * y

    assert multiply(3, 4) == 12


def test_profile_func_multiple_calls():
    bridge = CProfileBridge()

    @bridge.profile_func
    def noop():
        pass

    for _ in range(5):
        noop()

    records = bridge.to_records()
    noop_records = {k: v for k, v in records.items() if "noop" in k}
    assert noop_records
    total_calls = sum(r.calls for r in noop_records.values())
    assert total_calls >= 5


# ---------------------------------------------------------------------------
# profile_block context manager
# ---------------------------------------------------------------------------

def test_profile_block_records_section():
    bridge = CProfileBridge()

    with bridge.profile_block():
        time.sleep(0.01)

    records = bridge.to_records()
    assert records  # at least some functions recorded


def test_profile_block_exception_still_disables():
    bridge = CProfileBridge()
    with pytest.raises(ValueError):
        with bridge.profile_block():
            raise ValueError("intentional error")
    # Bridge should still produce records (profile was disabled in finally)
    records = bridge.to_records()
    assert isinstance(records, dict)


# ---------------------------------------------------------------------------
# Context-manager protocol  (``with CProfileBridge() as b:``)
# ---------------------------------------------------------------------------

def test_context_manager_protocol():
    with CProfileBridge() as bridge:
        x = sum(range(1000))

    records = bridge.to_records()
    assert isinstance(records, dict)


# ---------------------------------------------------------------------------
# to_records structure
# ---------------------------------------------------------------------------

def test_to_records_returns_function_records():
    bridge = CProfileBridge()

    @bridge.profile_func
    def dummy():
        return 42

    dummy()
    records = bridge.to_records()
    assert all(isinstance(v, FunctionRecord) for v in records.values())


def test_to_records_has_positive_time():
    bridge = CProfileBridge()

    @bridge.profile_func
    def slow_dummy():
        time.sleep(0.01)

    slow_dummy()
    records = bridge.to_records()
    total = sum(r.total_time for r in records.values())
    assert total > 0


def test_to_records_builds_parent_child():
    bridge = CProfileBridge()

    def child():
        pass

    @bridge.profile_func
    def parent():
        child()

    parent()

    records = bridge.to_records()
    parent_rec = next((v for k, v in records.items() if "parent" in k), None)
    assert parent_rec is not None
    assert len(parent_rec.children) >= 1


# ---------------------------------------------------------------------------
# get_stats
# ---------------------------------------------------------------------------

def test_get_stats_returns_pstats():
    import pstats
    bridge = CProfileBridge()

    @bridge.profile_func
    def fn():
        pass

    fn()
    stats = bridge.get_stats()
    assert isinstance(stats, pstats.Stats)


# ---------------------------------------------------------------------------
# save
# ---------------------------------------------------------------------------

def test_save_creates_prof_file(tmp_path):
    bridge = CProfileBridge()

    @bridge.profile_func
    def fn():
        pass

    fn()
    out = str(tmp_path / "profile.prof")
    bridge.save(out)

    import os
    assert os.path.exists(out)
    assert os.path.getsize(out) > 0


# ---------------------------------------------------------------------------
# reset
# ---------------------------------------------------------------------------

def test_reset_discards_data():
    bridge = CProfileBridge()

    @bridge.profile_func
    def fn():
        time.sleep(0.005)

    fn()
    bridge.reset()

    @bridge.profile_func
    def fresh():
        pass

    fresh()

    records = bridge.to_records()
    # After reset, the old fn data should not be present
    assert not any("fn" in k for k in records)
