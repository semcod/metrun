"""
metrun.critical_path
~~~~~~~~~~~~~~~~~~~~

Critical Path analysis for metrun execution graphs.

The *critical path* is the chain of nested function calls that contributes
the most wall-time from a root function down to a leaf.  Knowing the critical
path tells you *where* to focus optimisation effort: every millisecond saved on
a node along the critical path directly reduces the total run time.

Algorithm
---------
1. Identify *root* nodes — functions with no recorded parents.
2. Perform a depth-first traversal, accumulating ``total_time`` along each
   path from root to leaf.
3. Return the path whose cumulative leaf time is the highest.

Because a function's ``total_time`` in metrun already represents the sum of
all its invocations, the path score is the ``total_time`` of the *deepest*
node on that path (i.e. the leaf carries the "heat" of the whole chain above
it that flows through it).

Typical use::

    from metrun import trace, get_records, analyse
    from metrun.critical_path import find_critical_path, format_critical_path

    @trace
    def a(): b()

    @trace
    def b(): c()

    @trace
    def c(): pass

    a()

    records = get_records()
    path = find_critical_path(records)
    print(format_critical_path(path))
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

from metrun.profiler import FunctionRecord


@dataclass
class CriticalPathNode:
    """A single node in the critical path."""

    name: str
    total_time: float
    calls: int
    depth: int


@dataclass
class CriticalPath:
    """The result of a critical-path analysis."""

    nodes: List[CriticalPathNode]
    total_time: float  # total_time of the leaf node with the highest total_time on the critical path
    root: Optional[str]
    leaf: Optional[str]

    @property
    def length(self) -> int:
        return len(self.nodes)


def find_critical_path(records: Dict[str, FunctionRecord]) -> CriticalPath:
    """
    Find the critical (hottest) execution path through the call graph.

    Parameters
    ----------
    records:
        Dict of :class:`~metrun.profiler.FunctionRecord` objects, as returned
        by :func:`metrun.get_records` or
        :meth:`~metrun.cprofile_bridge.CProfileBridge.to_records`.

    Returns
    -------
    CriticalPath
        The hottest path from a root function to a leaf function.
        Returns an empty :class:`CriticalPath` when *records* is empty.
    """
    if not records:
        return CriticalPath(nodes=[], total_time=0.0, root=None, leaf=None)

    # Identify root nodes (no parents in the recorded set)
    roots = [
        name
        for name, rec in records.items()
        if not any(p in records for p in rec.parents)
    ]
    if not roots:
        # Fallback: use the node with maximum total_time as the single root
        roots = [max(records, key=lambda n: records[n].total_time)]

    best_path: List[str] = []
    best_time: float = -1.0

    def _dfs(name: str, current_path: List[str], visited: set) -> None:
        nonlocal best_path, best_time
        if name in visited:
            return
        current_path.append(name)
        visited.add(name)

        rec = records[name]
        children_in_graph = [c for c in rec.children if c in records]

        if not children_in_graph:
            # Leaf node — evaluate this path
            leaf_time = rec.total_time
            if leaf_time > best_time:
                best_time = leaf_time
                best_path = list(current_path)
        else:
            for child in children_in_graph:
                _dfs(child, current_path, visited)

        current_path.pop()
        visited.discard(name)

    for root in roots:
        _dfs(root, [], set())

    if not best_path:
        # No tree structure found — return single hottest node
        hottest = max(records, key=lambda n: records[n].total_time)
        best_path = [hottest]
        best_time = records[hottest].total_time

    nodes = [
        CriticalPathNode(
            name=name,
            total_time=records[name].total_time,
            calls=records[name].calls,
            depth=depth,
        )
        for depth, name in enumerate(best_path)
    ]

    return CriticalPath(
        nodes=nodes,
        total_time=best_time,
        root=best_path[0] if best_path else None,
        leaf=best_path[-1] if best_path else None,
    )


def format_critical_path(path: CriticalPath, *, indent: int = 2) -> str:
    """
    Render a :class:`CriticalPath` as a human-readable string.

    Example output::

        🧨 Critical Path  (depth=3, hottest leaf: 0.4200s)

          handler
          └─ db_query
             └─ serialize          ← 🔥 hottest leaf (0.4200s)

    Parameters
    ----------
    path:
        Result from :func:`find_critical_path`.
    indent:
        Number of spaces per depth level.

    Returns
    -------
    str
        Multi-line string ready to ``print()``.
    """
    lines: List[str] = []
    lines.append(
        f"🧨 Critical Path  "
        f"(depth={path.length}, hottest leaf: {path.total_time:.4f}s)"
    )
    lines.append("")

    if not path.nodes:
        lines.append("  (no path found)")
        return "\n".join(lines)

    for i, node in enumerate(path.nodes):
        pad = " " * (indent * node.depth)
        connector = "└─ " if node.depth > 0 else ""
        suffix = ""
        if node.name == path.leaf and path.length > 1:
            suffix = f"   ← 🔥 hottest leaf ({node.total_time:.4f}s)"
        lines.append(
            f"  {pad}{connector}{node.name}"
            f"  [{node.total_time:.4f}s, {node.calls:,} calls]{suffix}"
        )

    return "\n".join(lines)


def print_critical_path(path: CriticalPath, *, indent: int = 2) -> None:
    """Print the critical path to stdout."""
    print(format_critical_path(path, indent=indent))
