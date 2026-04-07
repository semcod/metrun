# metrun — Execution Intelligence Tool

## AI Cost Tracking

![PyPI](https://img.shields.io/badge/pypi-costs-blue) ![Version](https://img.shields.io/badge/version-0.1.10-blue) ![Python](https://img.shields.io/badge/python-3.9+-blue) ![License](https://img.shields.io/badge/license-Apache--2.0-green)
![AI Cost](https://img.shields.io/badge/AI%20Cost-$1.35-orange) ![Human Time](https://img.shields.io/badge/Human%20Time-6.6h-blue) ![Model](https://img.shields.io/badge/Model-openrouter%2Fqwen%2Fqwen3--coder--next-lightgrey)

- 🤖 **LLM usage:** $1.3500 (9 commits)
- 👤 **Human dev:** ~$657 (6.6h @ $100/h, 30min dedup)

Generated on 2026-04-07 using [openrouter/qwen/qwen3-coder-next](https://openrouter.ai/qwen/qwen3-coder-next)

---

> **metrun** doesn't just show you data — it tells you *what the problem is and how to fix it.*

## What is metrun?

`metrun` is a Python performance analysis library that turns raw profiling data into an **intelligible execution report**: bottleneck scores, dependency graphs, critical path highlighting, and actionable fix suggestions — all in one tool.

```
❌ traditional profilers → "here is your data"
✅ metrun               → "here is your problem and why it exists"
```

---

## Features

| Feature | Description |
|---|---|
| 🧠 **Bottleneck Engine** | Builds an execution graph, computes `score = time + calls + nested amplification`, ranks hotspots |
| 📊 **Human Report Generator** | Emoji-annotated report with time %, call count, score and diagnosis per function |
| 🧨 **Critical Path** | Finds the hottest nested call chain root → leaf |
| 💡 **Fix Suggestion Engine** | Library-specific advice per diagnosis: `lru_cache`, `asyncio`, `numba`, `viztracer`, `scalene` … |
| 🔥 **ASCII Flamegraph** | Terminal-friendly proportional bar chart, zero extra dependencies |
| 🖼️ **SVG Flamegraph** | Interactive SVG via [`flameprof`](https://pypi.org/project/flameprof/) |
| 🔌 **cProfile Bridge** | Use stdlib `cProfile` as the profiling backend; feed results into the Bottleneck Engine |
| 📋 **TOON Metric Tree** | `metrun scan` auto-profiles and generates `metrun.toon.yaml` — compact bottleneck map for the TOON ecosystem |
| ⌨️ **CLI** | `metrun profile`, `metrun inspect`, `metrun scan`, `metrun flame` commands |

---

## Installation

```bash
pip install metrun            # core (click included)
pip install metrun[flamegraph] # + SVG flamegraph support (flameprof)
```

---

## Quick Start

### Decorator tracing

```python
from metrun import trace, get_records, analyse, print_report

@trace
def slow_query(n):
    return sum(i * i for i in range(n))

@trace
def handler(items):
    return [slow_query(i) for i in items]

handler(list(range(100)))

bottlenecks = analyse(get_records())
print_report(bottlenecks)
```

### Context-manager tracing

```python
from metrun import section, get_records, analyse, print_report

with section("data_load"):
    data = load_from_db()

with section("transform"):
    result = process(data)

print_report(analyse(get_records()))
```

### Full enhanced report

```python
from metrun import analyse, get_records, print_report

records = get_records()
bottlenecks = analyse(records)

print_report(
    bottlenecks,
    show_graph=True,           # dependency graph
    show_critical_path=True,   # hottest call chain
    records=records,
    show_suggestions=True,     # fix advice
)
```

---

## Example output

```
🔥 METRUN PERFORMANCE REPORT
=============================

🔴 slow_query
   → time:      0.8200s  (78.2%)
   → calls:     12,430
   → score:     12.9
   → diagnosis: 🔥 loop hotspot

── Critical Path ─────────────────────────────
🧨 Critical Path  (depth=2, hottest leaf: 0.8200s)

  handler  [1.0500s, 1 calls]
    └─ slow_query  [0.8200s, 12430 calls]   ← 🔥 hottest leaf (0.8200s)

── Fix Suggestions ───────────────────────────
  💡 Fix suggestions for: slow_query
     1. Cache repeated results with lru_cache [functools]
           from functools import lru_cache

           @lru_cache(maxsize=None)
           def slow_query(x): ...

     2. Vectorise the loop with NumPy [numpy]
           import numpy as np
           result = np.sum(arr ** 2)
```

---

## Auto-diagnosis labels

| Label | Trigger |
|---|---|
| 🔥 `loop hotspot` | `calls ≥ 1 000` |
| 🌲 `dependency bottleneck` | `≥ 3 direct children` in the execution graph |
| 🐢 `slow execution` | `≥ 30 %` of total wall time (`time_pct ≥ 0.30`), low calls |
| ✅ `nominal` | below all thresholds |

**Score formula:**

```
score = (total_time / max_time) × 10  +  log10(calls + 1)  +  n_children × 0.5
```

---

## ASCII Flamegraph

```python
from metrun import render_ascii, print_ascii

print_ascii(bottlenecks, title="My App Flamegraph")
```

```
🔥 My App Flamegraph
────────────────────────────────────────────────────────
  slow_query    ████████████████████████████████████████  78.2%  score=12.9
  handler       █████████████████████████████████████████ 100.0%  score=9.4
  serialize     ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   5.1%  score=2.1
────────────────────────────────────────────────────────
```

---

## SVG Flamegraph (via `flameprof`)

```python
from metrun.cprofile_bridge import CProfileBridge
from metrun import render_svg

bridge = CProfileBridge()
with bridge.profile_block():
    my_function()

render_svg(bridge.get_stats(), "flame.svg")
# Open flame.svg in a browser for the interactive flamegraph
```

---

## cProfile Bridge

Integrate with stdlib `cProfile` or any existing `.prof` dump:

```python
from metrun.cprofile_bridge import CProfileBridge
from metrun import analyse, print_report

bridge = CProfileBridge()

@bridge.profile_func
def my_function():
    ...

my_function()

# Analyse with the Bottleneck Engine
bottlenecks = analyse(bridge.to_records())
print_report(bottlenecks)

# Save for snakeviz / flameprof CLI
bridge.save("profile.prof")
```

Compatible with these popular tools (no code changes needed):

| Tool | Command |
|---|---|
| **snakeviz** — interactive web viewer | `snakeviz profile.prof` |
| **flameprof** — SVG flamegraph | `flameprof profile.prof > flame.svg` |
| **py-spy** — sampling profiler | `py-spy record -o flame.svg -- python script.py` |
| **viztracer** — full trace + HTML flamegraph | see below |
| **scalene** — line-level CPU+memory | `python -m scalene script.py` |

---

## Language-neutral records interchange

`metrun` can export and import normalised profiling data as JSON.

- `metrun profile my_script.py --export-records profile.json`
  - saves the collected records as language-neutral JSON.
- `metrun inspect --records profile.json`
  - loads a JSON or JSONL records file produced by `metrun` or another runtime.
- `metrun inspect --records profile.json --export-records normalized.json`
  - loads records, normalises them, and writes them back out as language-neutral JSON.

The importer accepts top-level `records`, `functions`, `nodes`, or `items` collections, plus single-record objects and mapping-of-records payloads. The `language` field is preserved when present.

Example payload:

```json
{
  "schema_version": 1,
  "language": "javascript",
  "records": [
    {
      "name": "root",
      "total_time": 1.0,
      "calls": 1,
      "children": ["child"],
      "parents": [],
      "language": "javascript"
    },
    {
      "name": "child",
      "total_time": 0.25,
      "calls": 4,
      "children": [],
      "parents": ["root"],
      "language": "javascript"
    }
  ]
}
```

For JSONL, write one record per line:

```jsonl
{"name":"root","total_time":1.0,"calls":1,"children":["child"],"language":"javascript"}
{"name":"child","total_time":0.25,"calls":4,"parents":["root"],"language":"javascript"}
```

---

## VizTracer integration

```python
# pip install viztracer
from viztracer import VizTracer

with VizTracer(output_file="trace.json"):
    my_function()

# vizviewer trace.json  →  opens interactive HTML flamegraph
```

---

## Critical Path

```python
from metrun import find_critical_path, print_critical_path, get_records

path = find_critical_path(get_records())
print_critical_path(path)
```

```
🧨 Critical Path  (depth=3, hottest leaf: 0.4200s)

  handler  [0.9100s, 1 calls]
    └─ db_query  [0.6300s, 50 calls]
      └─ serialize  [0.4200s, 50 calls]   ← 🔥 hottest leaf (0.4200s)
```

---

## Fix Suggestion Engine

```python
from metrun import analyse, get_records, suggest, format_suggestions

for b in analyse(get_records()):
    tips = suggest(b)
    print(format_suggestions(b.name, tips))
```

Suggestion catalogue per diagnosis:

| Diagnosis | Suggestions |
|---|---|
| 🔥 loop hotspot | `functools.lru_cache`, `numpy` vectorisation, `numba @jit` |
| 🌲 dependency bottleneck | `concurrent.futures`, `asyncio.gather`, batching |
| 🐢 slow execution | `cProfile + snakeviz`, algorithmic review, `joblib.Memory` |
| Score ≥ 8 (any) | `scalene`, `viztracer` |

---

## CLI

```bash
# Profile a script — bottleneck report (user code only, stdlib filtered)
metrun profile my_script.py

# Profile + ASCII flamegraph in terminal
metrun profile my_script.py --ascii-flame

# Profile + save SVG flamegraph
metrun profile my_script.py --flame flame.svg

# Full enhanced report: bottlenecks + critical path + suggestions
metrun inspect my_script.py

# Export normalised records for another runtime or later analysis
metrun profile my_script.py --export-records profile.json

# Analyse language-neutral JSON or JSONL records
metrun inspect --records profile.json
metrun inspect --records profile.jsonl

# Load, normalise, and re-export language-neutral records
metrun inspect --records profile.json --export-records normalized.json

# Include Python stdlib / C-builtins in the report
metrun profile my_script.py --include-stdlib
metrun inspect my_script.py --include-stdlib

# Auto-scan and generate metrun.toon.yaml metric tree
metrun scan my_script.py --output project/

# Scan from pre-collected records
metrun scan --records profile.json --output project/

# Convert existing .prof dump to SVG
metrun flame profile.prof -o flame.svg
```

---

## Automatic project scanning & TOON output

`metrun scan` profiles a Python script (or loads pre-collected records) and
generates a `metrun.toon.yaml` file containing a compact metric tree that
describes the project's performance bottlenecks.

### How it works

1. **Endpoint recognition** — metrun identifies *root* functions (entry points)
   as any function with no recorded callers.  In decorator mode these are the
   top-level `@trace`-d functions; in cProfile mode they are the call-tree
   roots after stdlib filtering.
2. **Profiling** — the script is executed under `cProfile` (via
   `CProfileBridge`) and the resulting call tree is converted to
   `FunctionRecord` entries.
3. **Bottleneck analysis** — the `BottleneckEngine` scores every function and
   assigns a diagnosis label.
4. **Critical path** — a DFS walk finds the hottest root→leaf chain.
5. **TOON rendering** — all results are formatted into a compact
   `.toon.yaml` file with sections: `SUMMARY`, `BOTTLENECKS`, `CRITICAL-PATH`,
   `SUGGESTIONS`, `ENDPOINTS`, and `TREE`.

### Example output

```yaml
# metrun | 2b | top: handler 🌲 | python | 2026-04-07

SUMMARY:
  bottlenecks: 2
  top_score: 11.3
  top_name: handler
  top_diagnosis: 🌲 dependency bottleneck
  total_time: 1.5500s
  total_calls: 101

BOTTLENECKS[2]:
  🌲 handler                        score=11.3   time=0.8000s (51.6%)  calls=1       dependency bottleneck
  🐢 slow_query                     score=10.3   time=0.7500s (48.4%)  calls=100     slow execution

CRITICAL-PATH (depth=2, leaf=0.7500s):
  handler → slow_query ← 🔥

SUGGESTIONS[2]:
  handler: Run independent child calls concurrently [concurrent.futures]
  slow_query: Profile deeper with cProfile + snakeviz [cProfile / snakeviz]

ENDPOINTS[1]:
  handler  calls=1  time=0.8000s  children=1

TREE:
  🌲 handler  0.8000s  ×1
  │ ├─ 🐢 slow_query  0.7500s  ×100
```

### Python API

```python
from metrun import analyse, get_records, generate_toon, save_toon

bottlenecks = analyse(get_records())
toon = generate_toon(bottlenecks, get_records())
save_toon(toon, "project/metrun.toon.yaml")
```

### Integration with project.sh

```bash
metrun scan demo.py --output project/
```

The generated `metrun.toon.yaml` sits alongside other TOON files
(`analysis.toon.yaml`, `duplication.toon.yaml`, `validation.toon.yaml`, etc.)
and gives a performance perspective on the project.

---

## Architecture

```
  @trace / section()          cProfile.Profile
       │                            │
       ▼                            ▼
 ExecutionTracer              CProfileBridge
  (FunctionRecord)             .to_records()
       │                            │
       └──────────┬─────────────────┘
                  ▼
         BottleneckEngine.analyse()
          score + diagnosis + rank
                  │
       ┌──────────┼──────────────┐
       ▼          ▼              ▼
  print_report  find_critical  suggest()
  (report.py)    _path()      (suggestions.py)
                            
  ASCII/SVG flamegraph ← flamegraph.py
```

The two tracing backends (`ExecutionTracer` for decorator/section API and `CProfileBridge` for cProfile API) both produce the same `Dict[str, FunctionRecord]` structure consumed by the engine.

## Module overview

```
metrun/
├── profiler.py        # ExecutionTracer — decorator + context-manager tracing
├── bottleneck.py      # BottleneckEngine — score, diagnosis, ranking
├── report.py          # Human Report Generator
├── critical_path.py   # Critical path analysis (DFS on call graph)
├── suggestions.py     # Fix Suggestion Engine
├── flamegraph.py      # ASCII + SVG (flameprof) flamegraphs
├── cprofile_bridge.py # cProfile ↔ metrun bridge
├── toon.py            # TOON metric-tree generator (metrun.toon.yaml)
└── cli.py             # Click CLI entry-point
```

## Known limitations

| Limitation | Detail |
|---|---|
| **Name collisions in cProfile mode** | `CProfileBridge.to_records()` uses function name only as key (no file:lineno) — functions with the same name in different modules are merged |
| **Decorator tracing is opt-in** | Only functions decorated with `@trace` or wrapped in `section()` appear in `get_records()` — not the full call tree |
| **Thread-local call stack** | Each thread has an independent call stack; cross-thread parent→child links are not recorded |
| **No async support** | `asyncio` coroutines are not automatically traced by the decorator backend |

## cProfile filtering

By default `CProfileBridge.to_records()` and the CLI commands strip Python stdlib, C-builtins, anonymous entries (`<module>`, `<genexpr>`, etc.) and metrun's own internals — so the report focuses on **user code only**.  Call graph connectivity is maintained through bridging: filtered intermediate nodes (e.g. decorator wrappers) are transparently traversed when rebuilding parent→child links.

```python
records = bridge.to_records()                    # user code only (default)
records = bridge.to_records(exclude_stdlib=False) # full call tree
```

## License

Licensed under Apache-2.0.
