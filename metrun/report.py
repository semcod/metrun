"""
metrun.report
~~~~~~~~~~~~~

Human Report Generator: turns ranked Bottleneck entries into a readable,
emoji-annotated performance report that explains *why* a problem exists.

The report can optionally include:

* **Dependency graph** — parent → child call links
* **Critical path** — the hottest execution chain
* **Fix suggestions** — actionable tips per bottleneck (from the Suggestion
  Engine)
"""

from typing import TYPE_CHECKING, Dict, List, Optional

from metrun.bottleneck import Bottleneck

if TYPE_CHECKING:
    from metrun.profiler import FunctionRecord


def _severity_icon(diagnosis: str) -> str:
    """Return emoji icon based on diagnosis severity."""
    if "loop hotspot" in diagnosis:
        return "🔴"
    if "dependency bottleneck" in diagnosis:
        return "🟠"
    if "slow execution" in diagnosis:
        return "🟡"
    return "🟢"


def _format_bottleneck_entry(b: Bottleneck) -> List[str]:
    """Format a single bottleneck entry for the report."""
    lines: List[str] = []
    icon = _severity_icon(b.diagnosis)
    lines.append(f"{icon} {b.name}")
    lines.append(f"   → time:      {b.total_time:.4f}s  ({b.time_pct:.1f}%)")
    lines.append(f"   → calls:     {b.calls:,}")
    lines.append(f"   → score:     {b.score}")
    lines.append(f"   → diagnosis: {b.diagnosis}")
    if b.parents:
        lines.append(f"   → called by: {', '.join(b.parents)}")
    lines.append("")
    return lines


def _format_dependency_graph(bottlenecks: List[Bottleneck]) -> List[str]:
    """Format dependency graph section if there are nodes with children."""
    lines: List[str] = []
    nodes_with_children = [b for b in bottlenecks if b.children]
    if nodes_with_children:
        lines.append("── Dependency Graph ──────────────────────────")
        for b in nodes_with_children:
            for child in b.children:
                lines.append(f"   {b.name}  →  {child}")
        lines.append("")
    return lines


def _format_critical_path_section(
    records: Optional[Dict[str, "FunctionRecord"]],
) -> List[str]:
    """Format critical path section if records are provided."""
    lines: List[str] = []
    if records is not None:
        from metrun.critical_path import find_critical_path, format_critical_path
        path = find_critical_path(records)
        if path.length > 0:
            lines.append("── Critical Path ─────────────────────────────")
            lines.append(format_critical_path(path))
            lines.append("")
    return lines


def _format_suggestions_section(bottlenecks: List[Bottleneck]) -> List[str]:
    """Format fix suggestions section for all bottlenecks."""
    lines: List[str] = []
    lines.append("── Fix Suggestions ───────────────────────────")
    from metrun.suggestions import suggest, format_suggestions
    for b in bottlenecks:
        tips = suggest(b)
        if tips:
            lines.append(format_suggestions(b.name, tips))
    return lines


def _format_summary(worst: Bottleneck) -> List[str]:
    """Format summary footer section."""
    return [
        "── Summary ───────────────────────────────────",
        f"   Top bottleneck : {worst.name}",
        f"   Score          : {worst.score}",
        f"   Diagnosis      : {worst.diagnosis}",
        "",
    ]


def _shared_language(bottlenecks: List[Bottleneck]) -> Optional[str]:
    languages = {b.language.strip().lower() for b in bottlenecks if b.language.strip()}
    if len(languages) == 1:
        language = next(iter(languages))
        return None if language == "python" else language
    return None


def generate_report(
    bottlenecks: List[Bottleneck],
    *,
    title: str = "METRUN PERFORMANCE REPORT",
    top_n: Optional[int] = None,
    show_graph: bool = True,
    show_suggestions: bool = False,
    records: Optional[Dict[str, "FunctionRecord"]] = None,
    show_critical_path: bool = False,
) -> str:
    """
    Render a human-readable performance report.

    Parameters
    ----------
    bottlenecks:
        Ranked list returned by :func:`metrun.bottleneck.analyse`.
    title:
        Report header title.
    top_n:
        If given, only show the *top_n* entries by score.
    show_graph:
        When True, append a simple dependency section listing
        parent → child relationships.
    show_suggestions:
        When True, append fix suggestions from the Suggestion Engine for each
        hotspot.
    records:
        Original :class:`~metrun.profiler.FunctionRecord` dict.  Required when
        *show_critical_path* is True.
    show_critical_path:
        When True (and *records* is provided), append the critical execution
        path to the report.

    Returns
    -------
    str
        Multi-line string ready to print or log.
    """
    if top_n is not None:
        bottlenecks = bottlenecks[:top_n]

    language = _shared_language(bottlenecks)
    lines: List[str] = ["", f"🔥 {title}"]
    if language:
        lines.append(f"   language: {language}")
    lines.extend(["=" * (len(title) + 4), ""])

    if not bottlenecks:
        lines.extend(["  ✅ No hotspots detected.", ""])
        return "\n".join(lines)

    for b in bottlenecks:
        lines.extend(_format_bottleneck_entry(b))

    if show_graph:
        lines.extend(_format_dependency_graph(bottlenecks))

    if show_critical_path:
        lines.extend(_format_critical_path_section(records))

    if show_suggestions:
        lines.extend(_format_suggestions_section(bottlenecks))

    lines.extend(_format_summary(bottlenecks[0]))

    return "\n".join(lines)


def print_report(
    bottlenecks: List[Bottleneck],
    *,
    title: str = "METRUN PERFORMANCE REPORT",
    top_n: Optional[int] = None,
    show_graph: bool = True,
    show_suggestions: bool = False,
    records: Optional[Dict[str, "FunctionRecord"]] = None,
    show_critical_path: bool = False,
) -> None:
    """Print the performance report to stdout."""
    print(
        generate_report(
            bottlenecks,
            title=title,
            top_n=top_n,
            show_graph=show_graph,
            show_suggestions=show_suggestions,
            records=records,
            show_critical_path=show_critical_path,
        )
    )

