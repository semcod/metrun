<!-- code2docs:start --># metrun

![version](https://img.shields.io/badge/version-0.1.0-blue) ![python](https://img.shields.io/badge/python-%3E%3D3.9-blue) ![coverage](https://img.shields.io/badge/coverage-unknown-lightgrey) ![functions](https://img.shields.io/badge/functions-47-green)
> **47** functions | **8** classes | **11** files | CC̄ = 2.8

> Auto-generated project documentation from source code analysis.

**Author:** Tom Softreck <tom@sapletta.com>  
**License:** Apache License 2.0[(LICENSE)](./LICENSE)  
**Repository:** [https://github.com/semcod/metrun](https://github.com/semcod/metrun)

## Installation

### From PyPI

```bash
pip install metrun
```

### From Source

```bash
git clone https://github.com/semcod/metrun
cd metrun
pip install -e .
```

### Optional Extras

```bash
pip install metrun[flamegraph]    # flamegraph features
pip install metrun[dev]    # development tools
```

## Quick Start

### CLI Usage

```bash
# Generate full documentation for your project
metrun ./my-project

# Only regenerate README
metrun ./my-project --readme-only

# Preview what would be generated (no file writes)
metrun ./my-project --dry-run

# Check documentation health
metrun check ./my-project

# Sync — regenerate only changed modules
metrun sync ./my-project
```

### Python API

```python
from metrun import generate_readme, generate_docs, Code2DocsConfig

# Quick: generate README
generate_readme("./my-project")

# Full: generate all documentation
config = Code2DocsConfig(project_name="mylib", verbose=True)
docs = generate_docs("./my-project", config=config)
```

## Generated Output

When you run `metrun`, the following files are produced:

```
<project>/
├── README.md                 # Main project README (auto-generated sections)
├── docs/
│   ├── api.md               # Consolidated API reference
│   ├── modules.md           # Module documentation with metrics
│   ├── architecture.md      # Architecture overview with diagrams
│   ├── dependency-graph.md  # Module dependency graphs
│   ├── coverage.md          # Docstring coverage report
│   ├── getting-started.md   # Getting started guide
│   ├── configuration.md    # Configuration reference
│   └── api-changelog.md    # API change tracking
├── examples/
│   ├── quickstart.py       # Basic usage examples
│   └── advanced_usage.py   # Advanced usage examples
├── CONTRIBUTING.md         # Contribution guidelines
└── mkdocs.yml             # MkDocs site configuration
```

## Configuration

Create `metrun.yaml` in your project root (or run `metrun init`):

```yaml
project:
  name: my-project
  source: ./
  output: ./docs/

readme:
  sections:
    - overview
    - install
    - quickstart
    - api
    - structure
  badges:
    - version
    - python
    - coverage
  sync_markers: true

docs:
  api_reference: true
  module_docs: true
  architecture: true
  changelog: true

examples:
  auto_generate: true
  from_entry_points: true

sync:
  strategy: markers    # markers | full | git-diff
  watch: false
  ignore:
    - "tests/"
    - "__pycache__"
```

## Sync Markers

metrun can update only specific sections of an existing README using HTML comment markers:

```markdown
<!-- metrun:start -->
# Project Title
... auto-generated content ...
<!-- metrun:end -->
```

Content outside the markers is preserved when regenerating. Enable this with `sync_markers: true` in your configuration.

## Architecture

```
metrun/
├── project├── metrun/├── demo    ├── cli    ├── suggestions    ├── report    ├── critical_path    ├── flamegraph    ├── bottleneck    ├── profiler    ├── cprofile_bridge```

## API Overview

### Classes

- **`Suggestion`** — A single actionable fix suggestion.
- **`CriticalPathNode`** — A single node in the critical path.
- **`CriticalPath`** — The result of a critical-path analysis.
- **`Bottleneck`** — A single bottleneck entry produced by the engine.
- **`BottleneckEngine`** — Analyse a dict of FunctionRecords and return a ranked list of Bottlenecks.
- **`FunctionRecord`** — Aggregated stats for a single function (or call-site).
- **`ExecutionTracer`** — Thread-local call-stack tracer.
- **`CProfileBridge`** — Thin wrapper around :class:`cProfile.Profile` that exposes profiling

### Functions

- `slow_query(n)` — —
- `handler(items)` — —
- `cli()` — metrun — Execution Intelligence Tool.
- `profile(script, top, flame, ascii_flame)` — Profile SCRIPT and display the bottleneck report.
- `inspect(script, top, flame)` — Enhanced profile of SCRIPT: bottlenecks + critical path + suggestions.
- `flame(prof_file, output, width)` — Convert an existing .prof file to an SVG flamegraph.
- `main()` — —
- `suggest(bottleneck)` — Return a list of :class:`Suggestion` objects for a single bottleneck.
- `format_suggestions(name, suggestions)` — Render suggestions for a single function as a human-readable string.
- `print_suggestions(name, suggestions)` — Print suggestions for a single function to stdout.
- `generate_report(bottlenecks)` — Render a human-readable performance report.
- `print_report(bottlenecks)` — Print the performance report to stdout.
- `find_critical_path(records)` — Find the critical (hottest) execution path through the call graph.
- `format_critical_path(path)` — Render a :class:`CriticalPath` as a human-readable string.
- `print_critical_path(path)` — Print the critical path to stdout.
- `render_ascii(bottlenecks)` — Render an ASCII flamegraph as a multi-line string.
- `print_ascii(bottlenecks)` — Print the ASCII flamegraph to stdout.
- `render_svg(stats, output_path)` — Generate an SVG flamegraph from a ``pstats.Stats`` object and write it to
- `render_svg_string(stats)` — Like :func:`render_svg` but return the SVG markup as a string instead of
- `analyse(records)` — Convenience function: run the engine and return ranked bottlenecks.
- `trace(func)` — Decorator using the default (or supplied) tracer.
- `section(name)` — Context manager using the default (or supplied) tracer.
- `get_records()` — Return all collected records from the default (or supplied) tracer.
- `reset()` — Reset all collected records in the default (or supplied) tracer.


## Project Structure

📄 `demo` (2 functions)
📦 `metrun`
📄 `metrun.bottleneck` (6 functions, 2 classes)
📄 `metrun.cli` (6 functions)
📄 `metrun.cprofile_bridge` (9 functions, 1 classes)
📄 `metrun.critical_path` (3 functions, 2 classes)
📄 `metrun.flamegraph` (4 functions)
📄 `metrun.profiler` (12 functions, 2 classes)
📄 `metrun.report` (2 functions)
📄 `metrun.suggestions` (3 functions, 1 classes)
📄 `project`

## Requirements

- Python >= >=3.9
- click >=7.0- goal >=2.1.0- costs >=0.1.20- pfix >=0.1.60

## Contributing

**Contributors:**
- copilot-swe-agent[bot] <198982749+Copilot@users.noreply.github.com>
- Tom Sapletta <tom-sapletta-com@users.noreply.github.com>

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/semcod/metrun
cd metrun

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

## Documentation

- 📖 [Full Documentation](https://github.com/semcod/metrun/tree/main/docs) — API reference, module docs, architecture
- 🚀 [Getting Started](https://github.com/semcod/metrun/blob/main/docs/getting-started.md) — Quick start guide
- 📚 [API Reference](https://github.com/semcod/metrun/blob/main/docs/api.md) — Complete API documentation
- 🔧 [Configuration](https://github.com/semcod/metrun/blob/main/docs/configuration.md) — Configuration options
- 💡 [Examples](./examples) — Usage examples and code samples

### Generated Files

| Output | Description | Link |
|--------|-------------|------|
| `README.md` | Project overview (this file) | — |
| `docs/api.md` | Consolidated API reference | [View](./docs/api.md) |
| `docs/modules.md` | Module reference with metrics | [View](./docs/modules.md) |
| `docs/architecture.md` | Architecture with diagrams | [View](./docs/architecture.md) |
| `docs/dependency-graph.md` | Dependency graphs | [View](./docs/dependency-graph.md) |
| `docs/coverage.md` | Docstring coverage report | [View](./docs/coverage.md) |
| `docs/getting-started.md` | Getting started guide | [View](./docs/getting-started.md) |
| `docs/configuration.md` | Configuration reference | [View](./docs/configuration.md) |
| `docs/api-changelog.md` | API change tracking | [View](./docs/api-changelog.md) |
| `CONTRIBUTING.md` | Contribution guidelines | [View](./CONTRIBUTING.md) |
| `examples/` | Usage examples | [Browse](./examples) |
| `mkdocs.yml` | MkDocs configuration | — |

<!-- code2docs:end -->