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


if __name__ == "__main__":
    bottlenecks = analyse(get_records())
    for b in bottlenecks:
        tips = suggest(b)
        print(format_suggestions(b.name, tips))
"""
from dataclasses import dataclass
from typing import List, TYPE_CHECKING
if TYPE_CHECKING:
    from metrun.bottleneck import Bottleneck


@dataclass
class _SuggestionTemplate:
    title: str
    detail: str
    library: str = ''
    example: str = ''


Suggestion = _SuggestionTemplate


class Suggestion:
    """A single actionable fix suggestion."""

    def __init__(self, title: str, detail: str, library: str = '', example: str = '') -> None:
        self.title = title
        self.detail = detail
        self.library = library
        self.example = example
    _PYTHON_DIAGNOSIS_SUGGESTIONS: dict[str, List[Suggestion]] = {'loop hotspot': [Suggestion(title='Cache repeated results with lru_cache', detail='If the function is called many times with the same arguments, memoization can eliminate redundant work instantly.', library='functools', example='from functools import lru_cache\n\n@lru_cache(maxsize=None)\ndef my_func(x): ...'), Suggestion(title='Vectorise the loop with NumPy', detail='Python loops over numeric data are 10–100× slower than NumPy array operations.  Replace element-wise loops with vectorised expressions.', library='numpy', example='import numpy as np\nresult = np.sum(arr ** 2)  # instead of: sum(x**2 for x in arr)'), Suggestion(title='Accelerate with Numba JIT', detail='Numba compiles Python/NumPy functions to native machine code on the first call.  Ideal for tight numeric loops that cannot be easily vectorised.', library='numba', example='from numba import jit\n\n@jit(nopython=True)\ndef my_loop(arr): ...')], 'dependency bottleneck': [Suggestion(title='Run independent child calls concurrently', detail='When child functions are independent (no shared state), execute them in parallel to overlap their wall time.', library='concurrent.futures', example='from concurrent.futures import ThreadPoolExecutor\n\nwith ThreadPoolExecutor() as ex:\n    results = list(ex.map(child_func, items))'), Suggestion(title='Use asyncio for I/O-bound child calls', detail='If child functions are blocked on I/O (network, disk), rewrite them as async coroutines and await them concurrently.', library='asyncio', example='import asyncio\n\nasync def fetch_all(urls):\n    tasks = [fetch(u) for u in urls]\n    return await asyncio.gather(*tasks)'), Suggestion(title='Reduce fan-out with batching', detail='Many small calls to the same child (e.g. individual DB queries) can often be replaced by a single batched call, cutting round-trip overhead.', library='', example='# Instead of: for id in ids: db.get(id)\nresults = db.get_many(ids)')], 'slow execution': [Suggestion(title='Profile deeper with cProfile + snakeviz', detail='The function is slow but the root cause is not yet clear.  Use cProfile to drill into sub-call timings and snakeviz for an interactive flame view.', library='cProfile / snakeviz', example="import cProfile\ncProfile.run('my_func()', 'profile.prof')\n# then: snakeviz profile.prof"), Suggestion(title='Check algorithmic complexity', detail='A single slow call often hides an O(n²) or O(n³) algorithm.  Review loops, sorting, and lookups; switch lists to sets/dicts for O(1) membership tests.', library='', example='# O(n) lookup — use a set:\nlookup = set(items)\nif value in lookup: ...'), Suggestion(title='Cache pure function results', detail='If the slow function always returns the same result for the same inputs, wrap it with lru_cache or joblib.Memory.', library='joblib', example="from joblib import Memory\nmemory = Memory('/tmp/cache')\n\n@memory.cache\ndef slow_pure_func(x): ...")]}
    _PYTHON_HIGH_SCORE_SUGGESTIONS: List[Suggestion] = [Suggestion(title='Profile memory with Scalene', detail='Scalene provides CPU, GPU and memory profiling at line-level precision — it can reveal hidden allocation costs that slow execution.', library='scalene', example='# pip install scalene\n# python -m scalene my_script.py'), Suggestion(title='Visualise with VizTracer', detail='VizTracer records a full execution trace with microsecond precision and renders an interactive HTML flamegraph — great for understanding nested call patterns.', library='viztracer', example="from viztracer import VizTracer\n\nwith VizTracer(output_file='trace.json'):\n    my_func()\n# then: vizviewer trace.json")]
    _HIGH_SCORE_THRESHOLD = 8.0
    _GENERIC_DIAGNOSIS_SUGGESTIONS: dict[str, List[Suggestion]] = {'loop hotspot': [Suggestion(title='Cache repeated work', detail='Repeated inputs often mean the same work is being recomputed. Memoization or lookup tables can remove that overhead.', library='', example='# Cache expensive pure results instead of recomputing them'), Suggestion(title='Reduce nested iteration', detail='Nested loops amplify cost quickly. Flatten the data flow, precompute lookups, or batch operations where possible.', library='', example='# Prefer one batched pass over many tiny passes'), Suggestion(title='Move work off the hot path', detail='If the loop is CPU-heavy, consider parallelism, vectorization, or moving the work into a lower-level primitive.', library='', example='# Run the tight loop in a worker / native helper if needed')], 'dependency bottleneck': [Suggestion(title='Run independent work concurrently', detail='If child operations do not depend on each other, overlapping them can reduce wall-clock time dramatically.', library='', example='# Start independent tasks in parallel and join the results'), Suggestion(title='Batch fan-out calls', detail='Many small downstream calls are often slower than one batched call that amortises request, scheduling, or serialization overhead.', library='', example='# Replace many tiny requests with a single bulk request'), Suggestion(title='Reduce shared-state contention', detail='A bottleneck around dependencies is often caused by locks, queues, or shared mutable state. Split the state or reduce contention.', library='', example='# Minimise lock hold time and avoid needless synchronisation')], 'slow execution': [Suggestion(title='Profile deeper with a runtime profiler', detail='Use the profiler native to the runtime to locate the true hot path inside the slow function.', library='', example='# Run the language/runtime profiler and inspect the hottest stack'), Suggestion(title='Review algorithmic complexity', detail='A slow leaf is frequently hiding an O(n²) or O(n³) algorithm. Check loops, lookups, and repeated scans first.', library='', example='# Switch repeated linear membership checks to a hash-based lookup'), Suggestion(title='Cache pure results or precompute data', detail='If the same expensive calculation is performed many times, memoize it or precompute the result once and reuse it.', library='', example='# Store expensive derived values instead of recalculating them')]}
    _JAVASCRIPT_DIAGNOSIS_SUGGESTIONS: dict[str, List[Suggestion]] = {'loop hotspot': [Suggestion(title='Memoize repeated work with Map', detail='JavaScript loops often repeat the same lookups or transforms. A Map-backed cache can eliminate redundant work quickly.', library='Map', example='const cache = new Map();\nif (cache.has(key)) return cache.get(key);'), Suggestion(title='Use typed arrays or vector-style operations', detail='Hot numeric loops are usually faster when data is stored in typed arrays and transformed in bulk rather than item by item.', library='TypedArray', example='const values = new Float64Array(input);'), Suggestion(title='Offload CPU-heavy loops to workers', detail='If the loop blocks the event loop, move it to Worker Threads or a Web Worker so the UI and I/O stay responsive.', library='worker_threads', example="const { Worker } = require('node:worker_threads');")], 'dependency bottleneck': [Suggestion(title='Use Promise.all for independent async work', detail='Independent async operations should run together instead of one after another. Promise.all is the simplest way to overlap them.', library='Promise.all', example='const results = await Promise.all(tasks);'), Suggestion(title='Batch backend or storage calls', detail='Many small fetches, DB queries, or RPC calls usually cost more than a single batched request.', library='', example='// replace many small requests with one bulk endpoint call'), Suggestion(title='Move blocking work off the event loop', detail='CPU-bound fan-out often looks like dependency latency because the event loop is busy. Use worker threads or native addons.', library='worker_threads', example="const { Worker } = require('node:worker_threads');")], 'slow execution': [Suggestion(title='Profile with Node.js --prof or Clinic Flame', detail='Node-specific profilers show the V8 hot path and make it easier to see whether the slowdown is in JavaScript, native code, or I/O.', library='node --prof', example='node --prof app.js\nclinic flame -- node app.js'), Suggestion(title='Check V8 allocations and hidden-class churn', detail='A slow function can be slowed down by repeated allocations, object shape changes, or excessive serialization/deserialization.', library='V8', example='// keep object shapes stable and reuse buffers where possible'), Suggestion(title='Prefer streaming and typed structures', detail='Large in-memory transformations are often slower than streaming the data or using typed arrays and buffers.', library='Buffer', example='const buf = Buffer.allocUnsafe(size);')]}
    _RUST_DIAGNOSIS_SUGGESTIONS: dict[str, List[Suggestion]] = {'loop hotspot': [Suggestion(title='Prefer iterators and pre-allocation', detail='Rust loops often speed up when you avoid repeated reallocations and use iterator adapters to keep the hot path lean.', library='Vec::with_capacity', example='let mut out = Vec::with_capacity(n);'), Suggestion(title='Parallelise data-heavy loops with rayon', detail="Independent items can usually be processed in parallel, which is a good fit for rayon's parallel iterators.", library='rayon', example='items.par_iter().map(process).collect::<Vec<_>>();'), Suggestion(title='Avoid repeated clones and allocations', detail='Excessive cloning or per-iteration allocation can dominate a loop. Reuse buffers and borrow data where possible.', library='std::borrow', example='// pass references instead of cloning large values')], 'dependency bottleneck': [Suggestion(title='Use rayon for independent work', detail='If child tasks do not depend on each other, rayon can fan them out across threads with little boilerplate.', library='rayon', example='items.par_iter().for_each(process);'), Suggestion(title='Join async tasks with tokio::join!', detail='For async I/O, independent futures should be polled together so the runtime can overlap their waits.', library='tokio', example='let (a, b) = tokio::join!(task_a(), task_b());'), Suggestion(title='Reduce lock contention and batch I/O', detail='A dependency bottleneck can be caused by hot locks or many tiny I/O operations. Batch requests and shorten critical sections.', library='std::sync', example='// keep the locked section as small as possible')], 'slow execution': [Suggestion(title='Profile with cargo flamegraph or perf', detail='Rust applications often need a sampling profiler to show where CPU time is really spent inside the binary.', library='cargo-flamegraph', example='cargo flamegraph'), Suggestion(title='Benchmark the hot path with criterion', detail='A focused benchmark helps separate one-off startup costs from the steady-state performance of the hot function.', library='criterion', example='// add a criterion benchmark for the hot function'), Suggestion(title='Inspect allocations, copies, and lock contention', detail='Slow Rust code is often spending time allocating, cloning, or waiting on synchronisation rather than on pure compute.', library='', example='// use flamegraphs and allocator profiling to confirm the hot spot')]}
    _GENERIC_HIGH_SCORE_SUGGESTIONS: List[Suggestion] = [Suggestion(title='Use a sampling profiler and flamegraph view', detail='When the score is very high, a sampled call-graph view is usually the fastest way to separate hot leaf work from scheduling overhead.', library='', example='# Capture a flamegraph for the slow path and inspect the hottest stack'), Suggestion(title='Benchmark the bottleneck in isolation', detail='A focused benchmark removes unrelated noise and helps confirm whether the hotspot is algorithmic, I/O-bound, or allocation-heavy.', library='', example='# Measure only the hot function with representative input sizes')]
    _JAVASCRIPT_HIGH_SCORE_SUGGESTIONS: List[Suggestion] = [Suggestion(title='Run Node.js profiling or Clinic Flame', detail='For very hot Node paths, the V8 profiler and flamegraph tooling show whether the issue is JavaScript, native calls, or event-loop pressure.', library='node --prof', example='node --prof app.js\nclinic flame -- node app.js'), Suggestion(title='Consider worker threads for CPU-bound work', detail='If the hot path keeps the event loop busy, moving it to workers can restore responsiveness and overlap compute with I/O.', library='worker_threads', example="const { Worker } = require('node:worker_threads');")]
    _RUST_HIGH_SCORE_SUGGESTIONS: List[Suggestion] = [Suggestion(title='Generate a cargo flamegraph', detail='A flamegraph gives the clearest picture of where a Rust binary spends CPU time across its full call tree.', library='cargo-flamegraph', example='cargo flamegraph'), Suggestion(title='Add a criterion benchmark', detail='A microbenchmark helps validate the hot path after each optimisation and keeps regression checks honest.', library='criterion', example='// add a criterion benchmark for the hot function')]
    _LANGUAGE_ALIASES = {'': 'generic', 'generic': 'generic', 'unknown': 'generic', 'py': 'python', 'python': 'python', 'js': 'javascript', 'javascript': 'javascript', 'node': 'javascript', 'nodejs': 'javascript', 'ts': 'typescript', 'tsx': 'typescript', 'typescript': 'typescript', 'rs': 'rust', 'rust': 'rust'}
    _LANGUAGE_DIAGNOSIS_SUGGESTIONS: dict[str, dict[str, List[Suggestion]]] = {'generic': _GENERIC_DIAGNOSIS_SUGGESTIONS, 'python': _PYTHON_DIAGNOSIS_SUGGESTIONS, 'javascript': _JAVASCRIPT_DIAGNOSIS_SUGGESTIONS, 'typescript': _JAVASCRIPT_DIAGNOSIS_SUGGESTIONS, 'rust': _RUST_DIAGNOSIS_SUGGESTIONS}
    _LANGUAGE_HIGH_SCORE_SUGGESTIONS: dict[str, List[Suggestion]] = {'generic': _GENERIC_HIGH_SCORE_SUGGESTIONS, 'python': _PYTHON_HIGH_SCORE_SUGGESTIONS, 'javascript': _JAVASCRIPT_HIGH_SCORE_SUGGESTIONS, 'typescript': _JAVASCRIPT_HIGH_SCORE_SUGGESTIONS, 'rust': _RUST_HIGH_SCORE_SUGGESTIONS}


def _promote_suggestion(template: _SuggestionTemplate) -> Suggestion:
    return Suggestion(template.title, template.detail, template.library, template.example)


def _promote_catalog(catalog):
    if isinstance(catalog, dict):
        return {key: [_promote_suggestion(item) for item in value] for key, value in catalog.items()}
    return [_promote_suggestion(item) for item in catalog]


_PYTHON_DIAGNOSIS_SUGGESTIONS = _promote_catalog(Suggestion._PYTHON_DIAGNOSIS_SUGGESTIONS)
_PYTHON_HIGH_SCORE_SUGGESTIONS = _promote_catalog(Suggestion._PYTHON_HIGH_SCORE_SUGGESTIONS)
_HIGH_SCORE_THRESHOLD = Suggestion._HIGH_SCORE_THRESHOLD
_GENERIC_DIAGNOSIS_SUGGESTIONS = _promote_catalog(Suggestion._GENERIC_DIAGNOSIS_SUGGESTIONS)
_JAVASCRIPT_DIAGNOSIS_SUGGESTIONS = _promote_catalog(Suggestion._JAVASCRIPT_DIAGNOSIS_SUGGESTIONS)
_RUST_DIAGNOSIS_SUGGESTIONS = _promote_catalog(Suggestion._RUST_DIAGNOSIS_SUGGESTIONS)
_GENERIC_HIGH_SCORE_SUGGESTIONS = _promote_catalog(Suggestion._GENERIC_HIGH_SCORE_SUGGESTIONS)
_JAVASCRIPT_HIGH_SCORE_SUGGESTIONS = _promote_catalog(Suggestion._JAVASCRIPT_HIGH_SCORE_SUGGESTIONS)
_RUST_HIGH_SCORE_SUGGESTIONS = _promote_catalog(Suggestion._RUST_HIGH_SCORE_SUGGESTIONS)
_LANGUAGE_ALIASES = Suggestion._LANGUAGE_ALIASES
_LANGUAGE_DIAGNOSIS_SUGGESTIONS = {
    language: _promote_catalog(catalog)
    for language, catalog in Suggestion._LANGUAGE_DIAGNOSIS_SUGGESTIONS.items()
}
_LANGUAGE_HIGH_SCORE_SUGGESTIONS = {
    language: _promote_catalog(catalog)
    for language, catalog in Suggestion._LANGUAGE_HIGH_SCORE_SUGGESTIONS.items()
}

def _normalise_language(language: str) -> str:
    return _LANGUAGE_ALIASES.get((language or '').strip().lower(), 'generic')

def suggest(bottleneck: 'Bottleneck') -> List[Suggestion]:
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
    language = _normalise_language(getattr(bottleneck, 'language', ''))
    diagnosis_catalog = _LANGUAGE_DIAGNOSIS_SUGGESTIONS.get(language, _GENERIC_DIAGNOSIS_SUGGESTIONS)
    high_score_suggestions = _LANGUAGE_HIGH_SCORE_SUGGESTIONS.get(language, _GENERIC_HIGH_SCORE_SUGGESTIONS)
    for keyword, suggestions in diagnosis_catalog.items():
        if keyword in diag:
            tips.extend(suggestions)
    if bottleneck.score >= _HIGH_SCORE_THRESHOLD:
        tips.extend(high_score_suggestions)
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
        return f'  {name}: ✅ no specific suggestions'
    lines: List[str] = [f'  💡 Fix suggestions for: {name}']
    for i, tip in enumerate(suggestions, 1):
        lib_tag = f' [{tip.library}]' if tip.library else ''
        lines.append(f'     {i}. {tip.title}{lib_tag}')
        lines.append(f'        {tip.detail}')
        if tip.example:
            for line in tip.example.splitlines():
                lines.append(f'           {line}')
        lines.append('')
    return '\n'.join(lines)

def print_suggestions(name: str, suggestions: List[Suggestion]) -> None:
    """Print suggestions for a single function to stdout."""
    print(format_suggestions(name, suggestions))