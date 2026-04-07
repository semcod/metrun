# Metrun Examples

Minimal, copy-pasteable examples that work with `pip install metrun`.

## Quick Start

```bash
pip install metrun
python examples/profile/minimal.py
```

## Output Formats

| Format | Function | Use Case |
|--------|----------|----------|
| **Human Report** | `print_report()` | Interactive debugging, terminal output |
| **TOON/YAML** | `generate_toon()` + `save_toon()` | Metric trees, CI/CD, automation |

**Human Report** (`print_report`) — czytelny dla człowieka:
```
🔥 METRUN PERFORMANCE REPORT
=============================
🟡 handler   → time: 0.0001s (100.0%)  → calls: 1  → score: 10.8
```

**TOON/YAML** (`generate_toon`) — strukturalny, parsowalny:
```yaml
SUMMARY:
  bottlenecks: 2
  top_score: 10.8
  top_name: handler
BOTTLENECKS[2]:
  handler  score=10.8  time=0.0001s  calls=1
```

## Profile Examples (`examples/profile/`)

| Example | Output Format | What it shows |
|---------|---------------|---------------|
| `minimal.py` | Human report | Basic `@trace` decorator |
| `sections.py` | Human report | `section` context manager |
| `cprofile_bridge.py` | Human report | `CProfileBridge` for any callable |
| `toon_stdout.py` | **TOON/YAML** | TOON format to stdout |
| `toon_output.py` | TOON file | Saving TOON to file |
| `json_export.py` | JSON | Exporting/importing records |

## Records Examples (`examples/records/`)

| Example | What it shows |
|---------|---------------|
| `sample.jsonl` | Sample profiling data in JSONL format |
| `test_sample.py` | Testing CLI with `--records` flag |

## Usage Patterns

### 1. Human Report (terminal)
```python
from metrun import trace, analyse, get_records, print_report

@trace
def my_func():
    ...

my_func()
print_report(analyse(get_records()))  # 🔥 METRUN PERFORMANCE REPORT
```

### 2. TOON/YAML (automation)
```python
from metrun.toon import generate_toon, save_toon

toon = generate_toon(bottlenecks, records)
save_toon(toon, "output.toon.yaml")  # Structured YAML
```

### 3. Section Blocks
```python
from metrun import section

with section("database_query"):
    result = db.fetch()
```

### 4. CLI Scan (generates TOON)
```bash
metrun scan my_script.py --output project/     # Creates metrun.toon.yaml
metrun scan --records data.jsonl --output project/
```

All examples work without `sys.path` hacks when metrun is installed.
