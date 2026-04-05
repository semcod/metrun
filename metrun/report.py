"""
metrun.report
~~~~~~~~~~~~~

Human Report Generator: turns ranked Bottleneck entries into a readable,
emoji-annotated performance report that explains *why* a problem exists.
"""

from __future__ import annotations

from typing import List, Optional

from metrun.bottleneck import Bottleneck


def generate_report(
    bottlenecks: List[Bottleneck],
    *,
    title: str = "METRUN PERFORMANCE REPORT",
    top_n: Optional[int] = None,
    show_graph: bool = True,
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

    Returns
    -------
    str
        Multi-line string ready to print or log.
    """
    if top_n is not None:
        bottlenecks = bottlenecks[:top_n]

    lines: List[str] = []

    # Header
    lines.append("")
    lines.append(f"🔥 {title}")
    lines.append("=" * (len(title) + 4))
    lines.append("")

    if not bottlenecks:
        lines.append("  ✅ No hotspots detected.")
        lines.append("")
        return "\n".join(lines)

    # Severity label mapping
    def _severity_icon(diagnosis: str) -> str:
        if "loop hotspot" in diagnosis:
            return "🔴"
        if "dependency bottleneck" in diagnosis:
            return "🟠"
        if "slow execution" in diagnosis:
            return "🟡"
        return "🟢"

    # Body — one block per function
    for b in bottlenecks:
        icon = _severity_icon(b.diagnosis)
        lines.append(f"{icon} {b.name}")
        lines.append(f"   → time:      {b.total_time:.4f}s  ({b.time_pct:.1f}%)")
        lines.append(f"   → calls:     {b.calls:,}")
        lines.append(f"   → score:     {b.score}")
        lines.append(f"   → diagnosis: {b.diagnosis}")
        if b.parents:
            lines.append(f"   → called by: {', '.join(b.parents)}")
        lines.append("")

    # Dependency graph section
    if show_graph:
        nodes_with_children = [b for b in bottlenecks if b.children]
        if nodes_with_children:
            lines.append("── Dependency Graph ──────────────────────────")
            for b in nodes_with_children:
                for child in b.children:
                    lines.append(f"   {b.name}  →  {child}")
            lines.append("")

    # Summary footer
    worst = bottlenecks[0]
    lines.append("── Summary ───────────────────────────────────")
    lines.append(f"   Top bottleneck : {worst.name}")
    lines.append(f"   Score          : {worst.score}")
    lines.append(f"   Diagnosis      : {worst.diagnosis}")
    lines.append("")

    return "\n".join(lines)


def print_report(
    bottlenecks: List[Bottleneck],
    *,
    title: str = "METRUN PERFORMANCE REPORT",
    top_n: Optional[int] = None,
    show_graph: bool = True,
) -> None:
    """Print the performance report to stdout."""
    print(generate_report(bottlenecks, title=title, top_n=top_n, show_graph=show_graph))
