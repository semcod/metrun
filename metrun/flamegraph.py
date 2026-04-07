
CONSTANT_20 = 20
PORT_24 = 24
CONSTANT_32 = 32
CONSTANT_72 = 72
CONSTANT_1200 = 1200

"""
metrun.flamegraph
~~~~~~~~~~~~~~~~~

Flamegraph generators for metrun execution data.

Two backends are provided:


if __name__ == "__main__":
    ASCII (built-in, zero dependencies)
    A terminal-friendly horizontal bar chart rendered with plain characters.
    Works everywhere — no external packages required.

    SVG / HTML  (requires ``flameprof``)
    Uses the ``flameprof`` library to generate a proper interactive SVG
    flamegraph from a ``cProfile`` / ``pstats.Stats`` object.
    Install: ``pip install flameprof``

Typical use::

    from metrun import trace, get_records, analyse
    from metrun.flamegraph import render_ascii, render_svg

    @trace
    def slow(): ...

    slow()
    bottlenecks = analyse(get_records())

    # ASCII — always available
    print(render_ascii(bottlenecks))

    # SVG — needs flameprof + a cProfile run
    from metrun.cprofile_bridge import CProfileBridge
    bridge = CProfileBridge()
    with bridge.profile_block():
        slow()
    render_svg(bridge.get_stats(), "flame.svg")
"""
import io
from typing import TYPE_CHECKING, Any, List, Optional

if TYPE_CHECKING:
    import pstats
    from metrun.bottleneck import Bottleneck

DEFAULT_ASCII_WIDTH = 72
MAX_LABEL_WIDTH = 32
DEFAULT_SVG_WIDTH = 1200
DEFAULT_SVG_ROW_HEIGHT = 24
DEFAULT_SVG_THRESHOLD = 0.001
_BAR_CHARS = '█'
_EMPTY_CHAR = '░'

def _require_flameprof() -> Any:
    try:
        import flameprof
    except ImportError as exc:
        raise ImportError('flameprof is required for SVG flamegraphs.\nInstall it with:  pip install flameprof') from exc
    return flameprof

def render_ascii(bottlenecks: 'List[Bottleneck]', *, width: int=DEFAULT_ASCII_WIDTH, top_n: Optional[int]=None, title: str='Flamegraph') -> str:
    """
    Render an ASCII flamegraph as a multi-line string.

    Each function is drawn as a labelled bar whose width is proportional to
    its ``time_pct`` share of total execution time.

    Parameters
    ----------
    bottlenecks:
        Ranked list from :func:`metrun.bottleneck.analyse`.
    width:
        Total bar area width in characters (default 72).
    top_n:
        Show only the top *n* functions by score.
    title:
        Header line for the chart.

    Returns
    -------
    str
        Multi-line ASCII flamegraph ready to ``print()``.
    """
    if top_n is not None:
        bottlenecks = bottlenecks[:top_n]
    lines: List[str] = []
    lines.append(f'🔥 {title}')
    lines.append('─' * (width + 20))
    if not bottlenecks:
        lines.append('  (no data)')
        return '\n'.join(lines)
    label_width = max((len(b.name) for b in bottlenecks))
    label_width = min(label_width, MAX_LABEL_WIDTH)
    for b in bottlenecks:
        filled = int(round(b.time_pct / 100.0 * width))
        empty = width - filled
        bar = f'{_BAR_CHARS * filled}{_EMPTY_CHAR * empty}'
        label = b.name[:label_width].ljust(label_width)
        pct = f'{b.time_pct:5.1f}%'
        lines.append(f'  {label}  {bar}  {pct}  score={b.score}')
    lines.append('─' * (width + 20))
    return '\n'.join(lines)

def print_ascii(bottlenecks: 'List[Bottleneck]', *, width: int=72, top_n: Optional[int]=None, title: str='Flamegraph') -> None:
    """Print the ASCII flamegraph to stdout."""
    print(render_ascii(bottlenecks, width=width, top_n=top_n, title=title))

def render_svg(stats: 'pstats.Stats', output_path: str, *, width: int=DEFAULT_SVG_WIDTH, row_height: int=DEFAULT_SVG_ROW_HEIGHT, threshold: float=DEFAULT_SVG_THRESHOLD) -> None:
    """
    Generate an SVG flamegraph from a ``pstats.Stats`` object and write it to
    *output_path*.

    Requires ``flameprof`` (``pip install flameprof``).

    Parameters
    ----------
    stats:
        A :class:`pstats.Stats` object — obtain one from
        :class:`~metrun.cprofile_bridge.CProfileBridge` or directly from
        ``cProfile.Profile``.
    output_path:
        Destination file path (e.g. ``"flame.svg"``).
    width:
        SVG canvas width in pixels.
    row_height:
        Height of each flamegraph row in pixels.
    threshold:
        Minimum fraction of total time to include a function (0–1).
        Functions below this threshold are filtered out.

    Example
    -------
    ::

        import cProfile, pstats
        from metrun.flamegraph import render_svg

        pr = cProfile.Profile()
        pr.runcall(my_function)
        stats = pstats.Stats(pr)
        render_svg(stats, "flame.svg")

    Then open ``flame.svg`` in a browser for the interactive flamegraph.
    """
    flameprof = _require_flameprof()
    with open(output_path, 'w', encoding='utf-8') as fout:
        flameprof.render(stats.stats, fout, fmt='svg', threshold=threshold, width=width, row_height=row_height)

def render_svg_string(stats: 'pstats.Stats', *, width: int=DEFAULT_SVG_WIDTH, row_height: int=DEFAULT_SVG_ROW_HEIGHT, threshold: float=DEFAULT_SVG_THRESHOLD) -> str:
    """
    Like :func:`render_svg` but return the SVG markup as a string instead of
    writing to a file.

    Useful for embedding flamegraphs in HTML reports or Jupyter notebooks.

    Requires ``flameprof`` (``pip install flameprof``).
    """
    flameprof = _require_flameprof()
    buf = io.StringIO()
    flameprof.render(stats.stats, buf, fmt='svg', threshold=threshold, width=width, row_height=row_height)
    return buf.getvalue()