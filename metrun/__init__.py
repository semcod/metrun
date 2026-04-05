"""
metrun — Execution Intelligence Tool
=====================================

Quick start::

    from metrun import trace, section, analyse, print_report

    @trace
    def slow_query():
        ...

    # Run your code, then:
    from metrun import get_records
    bottlenecks = analyse(get_records())
    print_report(bottlenecks)
"""

from metrun.profiler import (
    ExecutionTracer,
    FunctionRecord,
    trace,
    section,
    get_records,
    reset,
)
from metrun.bottleneck import (
    Bottleneck,
    BottleneckEngine,
    analyse,
    LOOP_THRESHOLD,
    DEP_THRESHOLD,
    SLOW_THRESHOLD,
)
from metrun.report import generate_report, print_report

__all__ = [
    # profiler
    "ExecutionTracer",
    "FunctionRecord",
    "trace",
    "section",
    "get_records",
    "reset",
    # bottleneck
    "Bottleneck",
    "BottleneckEngine",
    "analyse",
    "LOOP_THRESHOLD",
    "DEP_THRESHOLD",
    "SLOW_THRESHOLD",
    # report
    "generate_report",
    "print_report",
]
