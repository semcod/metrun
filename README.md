# metrun — Execution Intelligence Tool

## AI Cost Tracking

![AI Cost](https://img.shields.io/badge/AI%20Cost-$0.75-brightgreen) ![AI Model](https://img.shields.io/badge/AI%20Model-openrouter%2Fqwen%2Fqwen3-coder-next-lightgrey)

This project uses AI-generated code. Total cost: **$0.7500** with **5** AI commits.

Generated on 2026-04-06 using [openrouter/qwen/qwen3-coder-next](https://openrouter.ai/models/openrouter/qwen/qwen3-coder-next)

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
| ⌨️ **CLI** | `metrun profile`, `metrun inspect`, `metrun flame` commands |

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
| 🐢 `slow execution` | `≥ 30 %` of total wall time, low calls |
| ✅ `nominal` | below all thresholds |

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
# Profile a script — bottleneck report
metrun profile my_script.py

# Profile + ASCII flamegraph in terminal
metrun profile my_script.py --ascii-flame

# Profile + save SVG flamegraph
metrun profile my_script.py --flame flame.svg

# Full enhanced report: bottlenecks + critical path + suggestions
metrun inspect my_script.py

# Convert existing .prof dump to SVG
metrun flame profile.prof -o flame.svg
```

---

## Module overview

```
metrun/
├── profiler.py        # ExecutionTracer — decorator + context-manager tracing
├── bottleneck.py      # BottleneckEngine — score, diagnosis, ranking
├── report.py          # Human Report Generator
├── critical_path.py   # Critical path analysis
├── suggestions.py     # Fix Suggestion Engine
├── flamegraph.py      # ASCII + SVG (flameprof) flamegraphs
├── cprofile_bridge.py # cProfile ↔ metrun bridge
└── cli.py             # Click CLI entry-point
```


## License

Licensed under Apache-2.0.
