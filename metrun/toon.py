"""
metrun.toon
~~~~~~~~~~~~

TOON format generator — renders bottleneck analysis as a compact
``metrun.toon.yaml`` metric tree that integrates with the project-level
TOON ecosystem (code2llm, redup, vallm, etc.).

The TOON (Terse Object-Oriented Notation) format uses section headers,
compact one-liners, and indented details to convey maximum information
in minimal vertical space.

Typical use::

    from metrun.toon import generate_toon, save_toon

    # From bottleneck analysis results
    toon = generate_toon(bottlenecks, records)
    save_toon(toon, "project/metrun.toon.yaml")

CLI::

    metrun scan my_script.py --output project/
    metrun scan --records profile.json --output project/
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING


if TYPE_CHECKING:
    from metrun.bottleneck import Bottleneck
    from metrun.profiler import FunctionRecord


def _summarize_bottlenecks(bottlenecks: List[Bottleneck]) -> tuple[int, float]:
    total_calls = sum((b.calls for b in bottlenecks))
    total_time = sum((b.total_time for b in bottlenecks))
    return total_calls, total_time


def _collect_language_tag(bottlenecks: List[Bottleneck]) -> str:
    languages = {b.language.strip().lower() for b in bottlenecks if b.language.strip()}
    if languages:
        return f" | {','.join(sorted(languages))}"
    return ''


def _build_top_tag(top: Bottleneck | None) -> str:
    if top:
        return f' | top: {top.name} {_severity_tag(top.diagnosis)}'
    return ''


def _append_top_details(lines: List[str], top: Bottleneck) -> None:
    lines.append(f'  top_score: {top.score}')
    lines.append(f'  top_name: {top.name}')
    lines.append(f'  top_time: {top.total_time:.4f}s')
    lines.append(f'  top_diagnosis: {top.diagnosis}')


def _build_toon_header(bottlenecks: List[Bottleneck], date: str) -> List[str]:
    total_calls, total_time = _summarize_bottlenecks(bottlenecks)
    top = bottlenecks[0] if bottlenecks else None

    lang_tag = _collect_language_tag(bottlenecks)
    top_tag = _build_top_tag(top)

    lines: List[str] = []
    lines.append(f'# metrun | {len(bottlenecks)}b{top_tag}{lang_tag} | {date}')
    lines.append('')
    lines.append('SUMMARY:')
    lines.append(f'  bottlenecks: {len(bottlenecks)}')
    if top:
        _append_top_details(lines, top)
    lines.append(f'  total_time: {total_time:.4f}s')
    lines.append(f'  total_calls: {total_calls}')
    lines.append('')
    return lines


def _severity_tag(diagnosis: str) -> str:
    """Return a compact severity marker for TOON output."""
    d = diagnosis.lower()
    if 'loop hotspot' in d:
        return '🔥'
    if 'dependency bottleneck' in d:
        return '🌲'
    if 'slow execution' in d:
        return '🐢'
    return '✅'


def _short_diagnosis(diagnosis: str) -> str:
    """Strip emoji prefix from a diagnosis string for compact output."""
    for prefix in ('🔥 ', '🌲 ', '🐢 ', '✅ '):
        if diagnosis.startswith(prefix):
            return diagnosis[len(prefix):]
    return diagnosis


def generate_toon(
    bottlenecks: List[Bottleneck],
    records: Optional[Dict[str, FunctionRecord]] = None,
    *,
    top_n: int = 10,
    date: str | None = None,
) -> str:
    """
    Render a TOON-format metric tree from bottleneck analysis results.

    Parameters
    ----------
    bottlenecks:
        Ranked list returned by :func:`metrun.bottleneck.analyse`.
    records:
        Original :class:`~metrun.profiler.FunctionRecord` dict.
        When provided, the critical path section is included.
    top_n:
        Maximum number of bottlenecks to include in the detail section.
    date:
        ISO date string for the header.  Defaults to today.

    Returns
    -------
    str
        Complete TOON-format string ready to write to a ``.toon.yaml`` file.
    """
    date = date or datetime.now().strftime('%Y-%m-%d')
    shown = bottlenecks[:top_n]
    total_calls = sum(b.calls for b in bottlenecks)
    total_time = sum(b.total_time for b in bottlenecks)

    # Determine shared language
    languages = {b.language.strip().lower() for b in bottlenecks if b.language.strip()}
    lang_tag = ''
    if languages:
        lang_tag = f" | {','.join(sorted(languages))}"

    top = bottlenecks[0] if bottlenecks else None
    top_tag = _build_top_tag(top)

    lines: List[str] = []

    # --- Header ---
    lines.append(
        f'# metrun | {len(bottlenecks)}b{top_tag}{lang_tag} | {date}'
    )
    lines.append('')

    # --- SUMMARY ---
    lines.append('SUMMARY:')
    lines.append(f'  bottlenecks: {len(bottlenecks)}')
    if top:
        _append_top_details(lines, top)
    lines.append(f'  total_time: {total_time:.4f}s')
    lines.append(f'  total_calls: {total_calls}')
    lines.append('')

    if not bottlenecks:
        lines.append('BOTTLENECKS[0]: none detected')
        lines.append('')
        return '\n'.join(lines)

    # --- BOTTLENECKS ---
    non_nominal = [b for b in shown if 'nominal' not in b.diagnosis.lower()]
    nominal = [b for b in shown if 'nominal' in b.diagnosis.lower()]

    lines.append(f'BOTTLENECKS[{len(non_nominal)}]:')
    if not non_nominal:
        lines.append('  (all nominal)')
    for b in non_nominal:
        tag = _severity_tag(b.diagnosis)
        diag = _short_diagnosis(b.diagnosis)
        lines.append(
            f'  {tag} {b.name:<30s} score={b.score:<6}  '
            f'time={b.total_time:.4f}s ({b.time_pct:>5.1f}%)  '
            f'calls={b.calls:<6}  {diag}'
        )
    if nominal:
        lines.append(f'  + {len(nominal)} nominal entries')
    lines.append('')

    # --- CRITICAL-PATH ---
    if records is not None:
        from metrun.critical_path import find_critical_path

        path = find_critical_path(records)
        if path.length > 0:
            chain = ' → '.join(n.name for n in path.nodes)
            if path.length > 1:
                chain = f'{chain} ← 🔥'
            lines.append(
                f'CRITICAL-PATH (depth={path.length}, leaf={path.total_time:.4f}s):'
            )
            lines.append(f'  {chain}')
            lines.append('')

    # --- SUGGESTIONS (compact) ---
    from metrun.suggestions import suggest

    suggestion_lines: List[str] = []
    for b in shown:
        tips = suggest(b)
        if tips:
            top_tip = tips[0]
            lib_tag = f" [{top_tip.library}]" if top_tip.library else ''
            suggestion_lines.append(
                f'  {b.name}: {top_tip.title}{lib_tag}'
            )

    if suggestion_lines:
        lines.append(f'SUGGESTIONS[{len(suggestion_lines)}]:')
        lines.extend(suggestion_lines)
        lines.append('')

    # --- ENDPOINTS (functions with no parents = entry points) ---
    if records is not None:
        endpoints = [
            name for name, rec in records.items()
            if not any(p in records for p in rec.parents)
        ]
        if endpoints:
            lines.append(f'ENDPOINTS[{len(endpoints)}]:')
            for ep in endpoints:
                rec = records[ep]
                lines.append(
                    f'  {ep}  calls={rec.calls}  time={rec.total_time:.4f}s  '
                    f'children={len(rec.children)}'
                )
            lines.append('')

    # --- TREE (metric tree from root to leaves) ---
    if records is not None:
        roots = [
            name for name, rec in records.items()
            if not any(p in records for p in rec.parents)
        ]
        if roots:
            lines.append('TREE:')
            visited: set = set()

            def _render_tree(name: str, depth: int) -> None:
                if name in visited or name not in records:
                    return
                visited.add(name)
                rec = records[name]
                prefix = f"  {'│ ' * depth}"
                connector = '├─ ' if depth > 0 else ''
                # Find bottleneck info for this node
                b_info = next((b for b in bottlenecks if b.name == name), None)
                tag = _severity_tag(b_info.diagnosis) if b_info else '·'
                lines.append(
                    f'{prefix}{connector}{tag} {name}  '
                    f'{rec.total_time:.4f}s  ×{rec.calls}'
                )
                children_in_graph = [c for c in rec.children if c in records]
                for child in children_in_graph:
                    _render_tree(child, depth + 1)

            for root in roots:
                _render_tree(root, 0)
            lines.append('')

    return '\n'.join(lines)


def save_toon(
    content: str,
    path: str | Path,
) -> Path:
    """
    Write TOON content to a file.

    Parameters
    ----------
    content:
        TOON-format string (from :func:`generate_toon`).
    path:
        Destination file path.  Parent directories are created if needed.

    Returns
    -------
    Path
        Resolved path to the written file.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding='utf-8')
    return p.resolve()
