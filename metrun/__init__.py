"""
metrun — Execution Intelligence Tool

if __name__ == "__main__":
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

Extended features::

    from metrun import (
        # Flamegraph (ASCII + SVG via flameprof)
        render_ascii, print_ascii, render_svg, render_svg_string,
        # Critical path
        find_critical_path, format_critical_path, print_critical_path,
        # Fix suggestions
        suggest, format_suggestions, print_suggestions,
        # cProfile bridge
        CProfileBridge,
    )
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
from metrun.cprofile_bridge import CProfileBridge
from metrun.flamegraph import (
    render_ascii,
    print_ascii,
    render_svg,
    render_svg_string,
)
from metrun.records_io import (
    record_to_payload,
    records_to_payload,
    dump_records_json,
    load_records_json,
    load_records_file,
    save_records_json,
)
from metrun.critical_path import (
    CriticalPath,
    CriticalPathNode,
    find_critical_path,
    format_critical_path,
    print_critical_path,
)
from metrun.suggestions import (
    Suggestion,
    suggest,
    format_suggestions,
    print_suggestions,
)
from metrun.toon import (
    generate_toon,
    save_toon,
)

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
    # cprofile bridge
    "CProfileBridge",
    # flamegraph
    "render_ascii",
    "print_ascii",
    "render_svg",
    "render_svg_string",
    # records I/O
    "record_to_payload",
    "records_to_payload",
    "dump_records_json",
    "load_records_json",
    "load_records_file",
    "save_records_json",
    # critical path
    "CriticalPath",
    "CriticalPathNode",
    "find_critical_path",
    "format_critical_path",
    "print_critical_path",
    # suggestions
    "Suggestion",
    "suggest",
    "format_suggestions",
    "print_suggestions",
    # toon
    "generate_toon",
    "save_toon",
]