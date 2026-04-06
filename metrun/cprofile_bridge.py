"""
metrun.cprofile_bridge
~~~~~~~~~~~~~~~~~~~~~~

Bridge between Python's stdlib ``cProfile`` and metrun's execution-tracing
system.  Lets you profile any callable (or code block) with cProfile and feed
the results directly into the Bottleneck Engine — no temp files required.

Typical use::

    from metrun.cprofile_bridge import CProfileBridge

    bridge = CProfileBridge()

    @bridge.profile_func
    def my_function():
        ...

    my_function()

    # Or profile a block:
    with bridge.profile_block():
        do_heavy_work()

    # Convert to metrun records and analyse:
    from metrun import analyse, print_report
    records  = bridge.to_records()
    bottlenecks = analyse(records)
    print_report(bottlenecks)

    # Save .prof for use with snakeviz / flameprof CLI:
    bridge.save("profile.prof")
"""

from __future__ import annotations

import cProfile
import functools
import io
import pstats
from contextlib import contextmanager
from typing import Callable, Dict

from metrun.profiler import FunctionRecord


class CProfileBridge:
    """
    Thin wrapper around :class:`cProfile.Profile` that exposes profiling
    results as metrun :class:`~metrun.profiler.FunctionRecord` objects.

    A single ``CProfileBridge`` instance accumulates stats across multiple
    profiling sessions (decorator calls / context-manager blocks).  Call
    :meth:`reset` to start fresh.
    """

    def __init__(self) -> None:
        self._profile = cProfile.Profile()

    # ------------------------------------------------------------------ #
    # Profiling entry-points
    # ------------------------------------------------------------------ #

    def profile_func(self, func: Callable) -> Callable:
        """Decorator: profile every call to *func* with cProfile."""

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return self._profile.runcall(func, *args, **kwargs)

        return wrapper

    @contextmanager
    def profile_block(self):
        """Context manager: profile the enclosed code block."""
        self._profile.enable()
        try:
            yield
        finally:
            self._profile.disable()

    # ------------------------------------------------------------------ #
    # Results
    # ------------------------------------------------------------------ #

    def get_stats(self) -> pstats.Stats:
        """Return a :class:`pstats.Stats` object for the accumulated profile."""
        buf = io.StringIO()
        stats = pstats.Stats(self._profile, stream=buf)
        return stats

    def to_records(self) -> Dict[str, FunctionRecord]:
        """
        Convert cProfile stats to a ``dict[name, FunctionRecord]``.

        The conversion maps ``pstats`` entries as follows:

        * ``name``        → ``"filename:lineno(funcname)"`` or just ``funcname``
        * ``total_time``  → cumulative time (``ct``) — matches metrun semantics
        * ``calls``       → number of primitive calls (``cc``)
        * ``children``    → functions *called from* this function (via callers map)
        * ``parents``     → functions that *called* this function
        """
        stats_obj = self.get_stats()
        # pstats.Stats stores data in .stats after sort
        stats_obj.sort_stats("cumulative")
        raw: dict = stats_obj.stats  # type: ignore[attr-defined]

        records: Dict[str, FunctionRecord] = {}

        def _key(entry) -> str:
            filename, lineno, name = entry
            return name

        # First pass: create records
        for entry, (cc, nc, tt, ct, callers) in raw.items():
            name = _key(entry)
            if name not in records:
                records[name] = FunctionRecord(name=name)
            rec = records[name]
            rec.total_time += ct
            rec.calls += cc

        # Second pass: build parent → child links
        for entry, (cc, nc, tt, ct, callers) in raw.items():
            child_name = _key(entry)
            child_rec = records[child_name]
            for caller_entry in callers:
                parent_name = _key(caller_entry)
                if parent_name not in records:
                    records[parent_name] = FunctionRecord(name=parent_name)
                parent_rec = records[parent_name]
                if child_name not in parent_rec.children:
                    parent_rec.children.append(child_name)
                if parent_name not in child_rec.parents:
                    child_rec.parents.append(parent_name)

        return records

    def save(self, path: str) -> None:
        """
        Dump the accumulated profile to *path* (a ``*.prof`` file).

        The resulting file can be opened with:

        * ``snakeviz profile.prof``  — interactive web viewer
        * ``flameprof profile.prof > flame.svg``  — SVG flamegraph
        * ``python -m pstats profile.prof``  — stdlib viewer
        """
        self._profile.dump_stats(path)

    def reset(self) -> None:
        """Discard all accumulated profiling data."""
        self._profile = cProfile.Profile()

    # ------------------------------------------------------------------ #
    # Context-manager protocol (for use as ``with CProfileBridge() as b:``)
    # ------------------------------------------------------------------ #

    def __enter__(self) -> "CProfileBridge":
        self._profile.enable()
        return self

    def __exit__(self, *_) -> None:
        self._profile.disable()
