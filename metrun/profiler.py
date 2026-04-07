"""
metrun.profiler
~~~~~~~~~~~~~~~

Lightweight execution tracer that records per-function timing, call counts,
and parent→child relationships for the Bottleneck Engine.
"""

import time
import functools
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterator, List, Optional


@dataclass
class FunctionRecord:
    """Aggregated stats for a single function (or call-site)."""

    name: str
    total_time: float = 0.0
    calls: int = 0
    # Names of functions called *from* this function (children)
    children: List[str] = field(default_factory=list)
    # Names of functions that called *this* function (parents)
    parents: List[str] = field(default_factory=list)
    language: str = "python"

    @property
    def avg_time(self) -> float:
        return self.total_time / self.calls if self.calls else 0.0


class ExecutionTracer:
    """
    Thread-local call-stack tracer.

    Usage — decorator:
        tracer = ExecutionTracer()

        @tracer.trace
        def my_func(): ...

    Usage — context manager:
        with tracer.section("my_section"):
            heavy_work()

    Collect results:
        records = tracer.records   # dict[name, FunctionRecord]
    """

    def __init__(self) -> None:
        self._records: Dict[str, FunctionRecord] = {}
        self._lock = threading.Lock()
        self._local = threading.local()

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _get_stack(self) -> List[str]:
        if not hasattr(self._local, "stack"):
            self._local.stack = []
        return self._local.stack

    def _ensure_record(self, name: str) -> FunctionRecord:
        if name not in self._records:
            self._records[name] = FunctionRecord(name=name)
        return self._records[name]

    def _enter(self, name: str) -> None:
        stack = self._get_stack()
        with self._lock:
            record = self._ensure_record(name)
            if stack:
                parent_name = stack[-1]
                parent = self._ensure_record(parent_name)
                if name not in parent.children:
                    parent.children.append(name)
                if parent_name not in record.parents:
                    record.parents.append(parent_name)
        stack.append(name)

    def _exit(self, name: str, elapsed: float) -> None:
        stack = self._get_stack()
        if stack and stack[-1] == name:
            stack.pop()
        with self._lock:
            record = self._ensure_record(name)
            record.total_time += elapsed
            record.calls += 1

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    @property
    def records(self) -> Dict[str, FunctionRecord]:
        return dict(self._records)

    def reset(self) -> None:
        with self._lock:
            self._records.clear()

    def trace(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """Decorator: trace every call to *func*."""

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            self._enter(func.__qualname__)
            t0 = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                elapsed = time.perf_counter() - t0
                self._exit(func.__qualname__, elapsed)

        return wrapper

    @contextmanager
    def section(self, name: str) -> Iterator[None]:
        """Context manager: trace a named code section."""
        self._enter(name)
        t0 = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - t0
            self._exit(name, elapsed)


# ---------------------------------------------------------------------------
# Module-level default tracer (convenience)
# ---------------------------------------------------------------------------


_default_tracer = ExecutionTracer()


def trace(func: Optional[Callable[..., Any]] = None, *, tracer: Optional[ExecutionTracer] = None) -> Any:
    """
    Decorator using the default (or supplied) tracer.

    Can be used with or without parentheses:
        @trace
        def foo(): ...

        @trace(tracer=my_tracer)
        def foo(): ...
    """
    _tracer = tracer or _default_tracer

    if func is not None:
        # Used as @trace without arguments
        return _tracer.trace(func)

    # Used as @trace(...) with keyword arguments
    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        return _tracer.trace(f)

    return decorator


def section(name: str, *, tracer: Optional[ExecutionTracer] = None) -> Any:
    """Context manager using the default (or supplied) tracer."""
    _tracer = tracer or _default_tracer
    return _tracer.section(name)


def get_records(*, tracer: Optional[ExecutionTracer] = None) -> Dict[str, FunctionRecord]:
    """Return all collected records from the default (or supplied) tracer."""
    _tracer = tracer or _default_tracer
    return _tracer.records


def reset(*, tracer: Optional[ExecutionTracer] = None) -> None:
    """Reset all collected records in the default (or supplied) tracer."""
    _tracer = tracer or _default_tracer
    _tracer.reset()
