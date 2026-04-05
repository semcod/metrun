"""Tests for metrun.critical_path — CriticalPath analysis."""

import pytest
from metrun.profiler import FunctionRecord
from metrun.critical_path import (
    find_critical_path,
    format_critical_path,
    print_critical_path,
    CriticalPath,
    CriticalPathNode,
)


def _rec(name, total_time=1.0, calls=1, children=None, parents=None):
    return FunctionRecord(
        name=name,
        total_time=total_time,
        calls=calls,
        children=children or [],
        parents=parents or [],
    )


# ---------------------------------------------------------------------------
# find_critical_path
# ---------------------------------------------------------------------------

class TestFindCriticalPath:

    def test_empty_records(self):
        path = find_critical_path({})
        assert path.length == 0
        assert path.total_time == 0.0
        assert path.root is None
        assert path.leaf is None

    def test_single_node(self):
        records = {"root": _rec("root", total_time=1.5)}
        path = find_critical_path(records)
        assert path.length == 1
        assert path.root == "root"
        assert path.leaf == "root"
        assert path.total_time == pytest.approx(1.5)

    def test_linear_chain(self):
        records = {
            "a": _rec("a", total_time=3.0, children=["b"]),
            "b": _rec("b", total_time=2.0, children=["c"], parents=["a"]),
            "c": _rec("c", total_time=1.0, parents=["b"]),
        }
        path = find_critical_path(records)
        names = [n.name for n in path.nodes]
        assert names == ["a", "b", "c"]
        assert path.root == "a"
        assert path.leaf == "c"

    def test_chooses_hotter_branch(self):
        # root → hot_child (1.0s) vs root → cold_child (0.1s)
        records = {
            "root": _rec("root", total_time=1.5, children=["hot_child", "cold_child"]),
            "hot_child": _rec("hot_child", total_time=1.0, parents=["root"]),
            "cold_child": _rec("cold_child", total_time=0.1, parents=["root"]),
        }
        path = find_critical_path(records)
        assert path.leaf == "hot_child"
        assert path.total_time == pytest.approx(1.0)

    def test_depth_assignment(self):
        records = {
            "a": _rec("a", total_time=2.0, children=["b"]),
            "b": _rec("b", total_time=1.0, children=["c"], parents=["a"]),
            "c": _rec("c", total_time=0.5, parents=["b"]),
        }
        path = find_critical_path(records)
        depths = {n.name: n.depth for n in path.nodes}
        assert depths["a"] == 0
        assert depths["b"] == 1
        assert depths["c"] == 2

    def test_multiple_roots(self):
        records = {
            "root1": _rec("root1", total_time=1.0, children=["shared"]),
            "root2": _rec("root2", total_time=0.5, children=["shared"]),
            "shared": _rec("shared", total_time=0.8, parents=["root1", "root2"]),
        }
        path = find_critical_path(records)
        assert path.length >= 1

    def test_no_cycles(self):
        """Guard against infinite loops on cyclic graphs."""
        records = {
            "a": _rec("a", total_time=1.0, children=["b"]),
            "b": _rec("b", total_time=0.5, children=["a"], parents=["a"]),
        }
        # Should not hang — just return a path
        path = find_critical_path(records)
        assert path.length >= 1

    def test_returns_critical_path_object(self):
        records = {"f": _rec("f", total_time=1.0)}
        path = find_critical_path(records)
        assert isinstance(path, CriticalPath)
        assert all(isinstance(n, CriticalPathNode) for n in path.nodes)


# ---------------------------------------------------------------------------
# format_critical_path
# ---------------------------------------------------------------------------

class TestFormatCriticalPath:

    def test_returns_string(self):
        records = {"f": _rec("f", total_time=1.0)}
        path = find_critical_path(records)
        result = format_critical_path(path)
        assert isinstance(result, str)

    def test_contains_header(self):
        records = {"f": _rec("f", total_time=1.0)}
        path = find_critical_path(records)
        result = format_critical_path(path)
        assert "Critical Path" in result

    def test_contains_function_names(self):
        records = {
            "parent": _rec("parent", total_time=2.0, children=["child"]),
            "child": _rec("child", total_time=1.0, parents=["parent"]),
        }
        path = find_critical_path(records)
        result = format_critical_path(path)
        assert "parent" in result
        assert "child" in result

    def test_hottest_leaf_marker(self):
        records = {
            "a": _rec("a", total_time=2.0, children=["b"]),
            "b": _rec("b", total_time=1.0, parents=["a"]),
        }
        path = find_critical_path(records)
        result = format_critical_path(path)
        assert "hottest leaf" in result

    def test_empty_path_message(self):
        path = find_critical_path({})
        result = format_critical_path(path)
        assert "no path found" in result

    def test_single_node_no_hottest_marker(self):
        """A single-node path has no inline per-node 'hottest leaf' arrow."""
        records = {"solo": _rec("solo", total_time=1.0)}
        path = find_critical_path(records)
        result = format_critical_path(path)
        # The header mentions "hottest leaf" as a summary stat,
        # but the per-node inline arrow "← 🔥 hottest leaf" should not appear
        # when root == leaf (length == 1).
        assert "← 🔥 hottest leaf" not in result

    def test_print_critical_path_produces_output(self, capsys):
        records = {"f": _rec("f", total_time=1.0)}
        path = find_critical_path(records)
        print_critical_path(path)
        captured = capsys.readouterr()
        assert len(captured.out) > 0
