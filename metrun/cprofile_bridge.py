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
import os
import pstats
import sysconfig
from contextlib import contextmanager
from typing import Callable, Dict, Optional

from metrun.profiler import FunctionRecord

# ---------------------------------------------------------------------------
# Stdlib path detection (used for user-code filtering)
# ---------------------------------------------------------------------------

def _stdlib_prefixes() -> tuple:
    """Return normalised filesystem prefixes for Python's stdlib and site-packages."""
    paths = []
    for key in ("stdlib", "platstdlib", "purelib", "platlib"):
        p = sysconfig.get_path(key)
        if p:
            paths.append(os.path.normpath(p))
    # Include the *user* site-packages directory (e.g. ~/.local/lib/…)
    try:
        import site
        user_sp = site.getusersitepackages()
        if isinstance(user_sp, str) and user_sp:
            paths.append(os.path.normpath(user_sp))
    except Exception:  # pragma: no cover — site may be absent in embedded interpreters
        pass
    return tuple(dict.fromkeys(paths))  # deduplicate, preserve order


_STDLIB_PREFIXES: Optional[tuple] = None
_METRUN_PKG_DIR: str = os.path.normpath(os.path.dirname(__file__))

# Anonymous / synthetic function names that are never useful to surface
_ANON_FUNC_NAMES = frozenset(
    {"<module>", "<genexpr>", "<listcomp>", "<setcomp>", "<dictcomp>", "<lambda>"}
)

# Import-machinery function names that are never useful to surface in reports
_IMPORT_MACHINERY_NAMES = frozenset(
    {"_path_hook", "find_spec", "find_module", "find_loader",
     "_find_and_load", "_find_and_load_unlocked", "_load_unlocked",
     "_call_with_frames_cleaned_up", "exec_module", "_load",
     "module_from_spec", "create_module", "source_to_code"}
)


def _is_user_code(filename: str, funcname: str) -> bool:
    """Return True only for named functions in user / project code."""
    if funcname in _ANON_FUNC_NAMES or funcname in _IMPORT_MACHINERY_NAMES:
        return False
    if not filename or filename.startswith("<") or filename == "~":
        return False
    global _STDLIB_PREFIXES
    if _STDLIB_PREFIXES is None:
        _STDLIB_PREFIXES = _stdlib_prefixes()
    norm = os.path.normpath(filename)
    if norm.startswith(_METRUN_PKG_DIR):
        return False
    return not any(norm.startswith(prefix) for prefix in _STDLIB_PREFIXES)


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
        # Use a temporary file to avoid consuming the original profile data
        # pstats.Stats() can load from a file without modifying the original
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.prof', delete=False) as tmp:
            self._profile.dump_stats(tmp.name)
            stats = pstats.Stats(tmp.name, stream=buf)
            os.unlink(tmp.name)  # Clean up temp file
        return stats

    def to_records(
        self,
        *,
        exclude_stdlib: bool = True,
    ) -> Dict[str, FunctionRecord]:
        """
        Convert cProfile stats to a ``dict[name, FunctionRecord]``.

        The conversion maps ``pstats`` entries as follows:

        * ``name``        → ``"filename:lineno(funcname)"`` or just ``funcname``
        * ``total_time``  → cumulative time (``ct``) — matches metrun semantics
        * ``calls``       → number of primitive calls (``cc``)
        * ``children``    → functions *called from* this function (via callers map)
        * ``parents``     → functions that *called* this function

        Parameters
        ----------
        exclude_stdlib:
            When ``True`` (default) strip Python stdlib / C-builtin entries so
            that the report focuses on user code.  Pass ``False`` to see the
            full call tree including interpreter internals.
        """
        stats_obj = self.get_stats()
        # pstats.Stats stores data in .stats after sort
        stats_obj.sort_stats("cumulative")
        raw: dict = stats_obj.stats  # type: ignore[attr-defined]

        records: Dict[str, FunctionRecord] = {}

        def _key(entry) -> str:
            filename, lineno, name = entry
            return name

        def _include(entry) -> bool:
            if not exclude_stdlib:
                return True
            filename, _lineno, funcname = entry
            return _is_user_code(filename, funcname)

        # Pre-build callers map (name → set of parent names) for bridging
        callers_map: dict = {}  # child_name → set of parent_names
        for entry, (cc, nc, tt, ct, callers) in raw.items():
            child_name = _key(entry)
            if child_name not in callers_map:
                callers_map[child_name] = set()
            for caller_entry in callers:
                callers_map[child_name].add(_key(caller_entry))

        user_names: set = {_key(e) for e in raw if _include(e)}

        def _user_ancestors(name: str, seen: set) -> set:
            """Nearest user-code ancestors, bridging through filtered nodes."""
            result: set = set()
            for parent in callers_map.get(name, set()):
                if parent in seen:
                    continue
                if parent in user_names:
                    result.add(parent)
                else:
                    seen.add(parent)
                    result.update(_user_ancestors(parent, seen))
            return result

        # First pass: create records for user-code entries
        for entry, (cc, nc, tt, ct, callers) in raw.items():
            if not _include(entry):
                continue
            name = _key(entry)
            if name not in records:
                records[name] = FunctionRecord(name=name)
            rec = records[name]
            rec.total_time += ct
            rec.calls += cc

        # Second pass: build bridged parent → child links
        for name in list(records.keys()):
            rec = records[name]
            for parent_name in _user_ancestors(name, {name}):
                if parent_name not in records:
                    continue
                parent_rec = records[parent_name]
                if name not in parent_rec.children:
                    parent_rec.children.append(name)
                if parent_name not in rec.parents:
                    rec.parents.append(parent_name)

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
