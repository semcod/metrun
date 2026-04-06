"""
metrun.suggestions
~~~~~~~~~~~~~~~~~~

Fix Suggestion Engine — turns bottleneck diagnoses into actionable, specific
code-improvement advice.

Each :class:`~metrun.bottleneck.Bottleneck` diagnosis is mapped to a set of
concrete suggestions that name the relevant Python tools/techniques with
copy-pasteable mini-examples where applicable.

Typical use::

    from metrun import analyse, get_records
    from metrun.suggestions import suggest, format_suggestions

    bottlenecks = analyse(get_records())
    for b in bottlenecks:
        tips = suggest(b)
        print(format_suggestions(b.name, tips))
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from metrun.bottleneck import Bottleneck

# ---------------------------------------------------------------------------
# Suggestion catalogue
# ---------------------------------------------------------------------------

@dataclass
class Suggestion:
    """A single actionable fix suggestion."""

    title: str
    detail: str
    library: str = ""       # relevant library / tool name
    example: str = ""       # short code snippet (optional)


# Map keywords found in a diagnosis string to a list of Suggestion objects.
_DIAGNOSIS_SUGGESTIONS: dict[str, List[Suggestion]] = {
    "loop hotspot": [
        Suggestion(
            title="Cache repeated results with lru_cache",
            detail=(
                "If the function is called many times with the same arguments, "
                "memoization can eliminate redundant work instantly."
            ),
            library="functools",
            example="from functools import lru_cache\n\n@lru_cache(maxsize=None)\ndef my_func(x): ...",
        ),
        Suggestion(
            title="Vectorise the loop with NumPy",
            detail=(
                "Python loops over numeric data are 10–100× slower than NumPy "
                "array operations.  Replace element-wise loops with vectorised "
                "expressions."
            ),
            library="numpy",
            example="import numpy as np\nresult = np.sum(arr ** 2)  # instead of: sum(x**2 for x in arr)",
        ),
        Suggestion(
            title="Accelerate with Numba JIT",
            detail=(
                "Numba compiles Python/NumPy functions to native machine code "
                "on the first call.  Ideal for tight numeric loops that cannot "
                "be easily vectorised."
            ),
            library="numba",
            example="from numba import jit\n\n@jit(nopython=True)\ndef my_loop(arr): ...",
        ),
    ],
    "dependency bottleneck": [
        Suggestion(
            title="Run independent child calls concurrently",
            detail=(
                "When child functions are independent (no shared state), execute "
                "them in parallel to overlap their wall time."
            ),
            library="concurrent.futures",
            example=(
                "from concurrent.futures import ThreadPoolExecutor\n\n"
                "with ThreadPoolExecutor() as ex:\n"
                "    results = list(ex.map(child_func, items))"
            ),
        ),
        Suggestion(
            title="Use asyncio for I/O-bound child calls",
            detail=(
                "If child functions are blocked on I/O (network, disk), rewrite "
                "them as async coroutines and await them concurrently."
            ),
            library="asyncio",
            example=(
                "import asyncio\n\nasync def fetch_all(urls):\n"
                "    tasks = [fetch(u) for u in urls]\n"
                "    return await asyncio.gather(*tasks)"
            ),
        ),
        Suggestion(
            title="Reduce fan-out with batching",
            detail=(
                "Many small calls to the same child (e.g. individual DB queries) "
                "can often be replaced by a single batched call, cutting "
                "round-trip overhead."
            ),
            library="",
            example="# Instead of: for id in ids: db.get(id)\nresults = db.get_many(ids)",
        ),
    ],
    "slow execution": [
        Suggestion(
            title="Profile deeper with cProfile + snakeviz",
            detail=(
                "The function is slow but the root cause is not yet clear.  "
                "Use cProfile to drill into sub-call timings and snakeviz for "
                "an interactive flame view."
            ),
            library="cProfile / snakeviz",
            example=(
                "import cProfile\ncProfile.run('my_func()', 'profile.prof')\n"
                "# then: snakeviz profile.prof"
            ),
        ),
        Suggestion(
            title="Check algorithmic complexity",
            detail=(
                "A single slow call often hides an O(n²) or O(n³) algorithm.  "
                "Review loops, sorting, and lookups; switch lists to sets/dicts "
                "for O(1) membership tests."
            ),
            library="",
            example="# O(n) lookup — use a set:\nlookup = set(items)\nif value in lookup: ...",
        ),
        Suggestion(
            title="Cache pure function results",
            detail=(
                "If the slow function always returns the same result for the "
                "same inputs, wrap it with lru_cache or joblib.Memory."
            ),
            library="joblib",
            example=(
                "from joblib import Memory\nmemory = Memory('/tmp/cache')\n\n"
                "@memory.cache\ndef slow_pure_func(x): ..."
            ),
        ),
    ],
}

# Score-based tier suggestions (appended when score is very high)
_HIGH_SCORE_SUGGESTIONS: List[Suggestion] = [
    Suggestion(
        title="Profile memory with Scalene",
        detail=(
            "Scalene provides CPU, GPU and memory profiling at line-level "
            "precision — it can reveal hidden allocation costs that slow "
            "execution."
        ),
        library="scalene",
        example="# pip install scalene\n# python -m scalene my_script.py",
    ),
    Suggestion(
        title="Visualise with VizTracer",
        detail=(
            "VizTracer records a full execution trace with microsecond "
            "precision and renders an interactive HTML flamegraph — great for "
            "understanding nested call patterns."
        ),
        library="viztracer",
        example=(
            "from viztracer import VizTracer\n\n"
            "with VizTracer(output_file='trace.json'):\n"
            "    my_func()\n"
            "# then: vizviewer trace.json"
        ),
    ),
]

# Score threshold above which high-score suggestions are appended
_HIGH_SCORE_THRESHOLD = 8.0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def suggest(bottleneck: "Bottleneck") -> List[Suggestion]:
    """
    Return a list of :class:`Suggestion` objects for a single bottleneck.

    Parameters
    ----------
    bottleneck:
        A :class:`~metrun.bottleneck.Bottleneck` entry (from
        :func:`metrun.analyse`).

    Returns
    -------
    list[Suggestion]
        Ordered list of actionable tips; empty list if no matching suggestions.
    """
    tips: List[Suggestion] = []
    diag = bottleneck.diagnosis.lower()

    for keyword, suggestions in _DIAGNOSIS_SUGGESTIONS.items():
        if keyword in diag:
            tips.extend(suggestions)

    if bottleneck.score >= _HIGH_SCORE_THRESHOLD:
        tips.extend(_HIGH_SCORE_SUGGESTIONS)

    return tips


def format_suggestions(name: str, suggestions: List[Suggestion]) -> str:
    """
    Render suggestions for a single function as a human-readable string.

    Parameters
    ----------
    name:
        Function name (used as section header).
    suggestions:
        List from :func:`suggest`.

    Returns
    -------
    str
        Multi-line string ready to ``print()``.
    """
    if not suggestions:
        return f"  {name}: ✅ no specific suggestions"

    lines: List[str] = [f"  💡 Fix suggestions for: {name}"]
    for i, tip in enumerate(suggestions, 1):
        lib_tag = f" [{tip.library}]" if tip.library else ""
        lines.append(f"     {i}. {tip.title}{lib_tag}")
        lines.append(f"        {tip.detail}")
        if tip.example:
            for line in tip.example.splitlines():
                lines.append(f"           {line}")
        lines.append("")
    return "\n".join(lines)


def print_suggestions(name: str, suggestions: List[Suggestion]) -> None:
    """Print suggestions for a single function to stdout."""
    print(format_suggestions(name, suggestions))
