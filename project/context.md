# System Architecture Analysis

## Overview

- **Project**: /home/tom/github/semcod/metrun
- **Primary Language**: python
- **Languages**: python: 13, shell: 1
- **Analysis Mode**: static
- **Total Functions**: 88
- **Total Classes**: 8
- **Modules**: 14
- **Entry Points**: 37

## Architecture by Module

### metrun.records_io
- **Functions**: 20
- **File**: `records_io.py`

### metrun.profiler
- **Functions**: 12
- **Classes**: 2
- **File**: `profiler.py`

### metrun.cprofile_bridge
- **Functions**: 11
- **Classes**: 1
- **File**: `cprofile_bridge.py`

### metrun.report
- **Functions**: 9
- **File**: `report.py`

### metrun.cli
- **Functions**: 7
- **File**: `cli.py`

### metrun.bottleneck
- **Functions**: 6
- **Classes**: 2
- **File**: `bottleneck.py`

### metrun.toon
- **Functions**: 4
- **File**: `toon.py`

### metrun.suggestions
- **Functions**: 4
- **Classes**: 1
- **File**: `suggestions.py`

### metrun.flamegraph
- **Functions**: 4
- **File**: `flamegraph.py`

### project
- **Functions**: 3
- **File**: `project.sh`

### examples.profile.basic_app
- **Functions**: 3
- **File**: `basic_app.py`

### metrun.critical_path
- **Functions**: 3
- **Classes**: 2
- **File**: `critical_path.py`

### demo
- **Functions**: 2
- **File**: `demo.py`

## Key Entry Points

Main execution flows into the system:

### metrun.cli.inspect
> Enhanced profile of SCRIPT or records file: bottlenecks + critical path + suggestions.

SCRIPT is the path to a Python file to profile unless --record
- **Calls**: cli.command, click.argument, click.option, click.option, click.option, click.option, click.option, click.option

### metrun.cli.scan
> Auto-profile SCRIPT and generate a metrun.toon.yaml metric tree.

Profiles the given Python script (or loads --records) and writes a
compact TOON-form
- **Calls**: cli.command, click.argument, click.option, click.option, click.option, click.option, click.option, metrun.bottleneck.BottleneckEngine.analyse

### metrun.cprofile_bridge.CProfileBridge.to_records
> Convert cProfile stats to a ``dict[name, FunctionRecord]``.

The conversion maps ``pstats`` entries as follows:

* ``name``        → ``"filename:linen
- **Calls**: self.get_stats, stats_obj.sort_stats, raw.items, raw.items, list, metrun.cprofile_bridge._is_user_code, _key, _key

### metrun.cli.profile
> Profile SCRIPT and display the bottleneck report.

SCRIPT is the path to a Python file to profile.
- **Calls**: cli.command, click.argument, click.option, click.option, click.option, click.option, click.option, click.echo

### metrun.cli.flame
> Convert an existing .prof file to an SVG flamegraph.

PROF_FILE is the path to a cProfile .prof dump
(created with cProfile.dump_stats or ``metrun pro
- **Calls**: cli.command, click.argument, click.option, click.option, pstats.Stats, metrun.flamegraph.render_svg, click.echo, click.Path

### examples.profile.basic_app.main
- **Calls**: examples.profile.basic_app.handler, project.print_report, list, metrun.bottleneck.BottleneckEngine.analyse, range, metrun.profiler.get_records

### metrun.profiler.ExecutionTracer._enter
- **Calls**: self._get_stack, stack.append, self._ensure_record, self._ensure_record, parent.children.append, record.parents.append

### metrun.profiler.ExecutionTracer.trace
> Decorator: trace every call to *func*.
- **Calls**: functools.wraps, self._enter, time.perf_counter, func, self._exit, time.perf_counter

### metrun.cprofile_bridge.CProfileBridge.get_stats
> Return a :class:`pstats.Stats` object for the accumulated profile.
- **Calls**: io.StringIO, tempfile.NamedTemporaryFile, self._profile.dump_stats, pstats.Stats, os.unlink

### metrun.flamegraph.render_svg_string
> Like :func:`render_svg` but return the SVG markup as a string instead of
writing to a file.

Useful for embedding flamegraphs in HTML reports or Jupyt
- **Calls**: io.StringIO, flameprof.render, buf.getvalue, ImportError

### metrun.bottleneck.BottleneckEngine._total_wall_time
> Sum of all top-level (root) function times, or max if no roots exist.
- **Calls**: sum, max, self._records.values, self._records.values

### metrun.profiler.ExecutionTracer.section
> Context manager: trace a named code section.
- **Calls**: self._enter, time.perf_counter, self._exit, time.perf_counter

### metrun.profiler.ExecutionTracer._exit
- **Calls**: self._get_stack, stack.pop, self._ensure_record

### metrun.suggestions.print_suggestions
> Print suggestions for a single function to stdout.
- **Calls**: project.print, metrun.suggestions.format_suggestions

### metrun.report.print_report
> Print the performance report to stdout.
- **Calls**: project.print, metrun.report.generate_report

### metrun.critical_path.print_critical_path
> Print the critical path to stdout.
- **Calls**: project.print, metrun.critical_path.format_critical_path

### metrun.bottleneck.BottleneckEngine._compute_score
- **Calls**: math.log10, round

### metrun.bottleneck.analyse
> Convenience function: run the engine and return ranked bottlenecks.
- **Calls**: None.analyse, BottleneckEngine

### metrun.profiler.ExecutionTracer.__init__
- **Calls**: threading.Lock, threading.local

### metrun.profiler.trace
> Decorator using the default (or supplied) tracer.

Can be used with or without parentheses:
    @trace
    def foo(): ...

    @trace(tracer=my_tracer
- **Calls**: _tracer.trace, _tracer.trace

### metrun.cprofile_bridge.CProfileBridge.profile_func
> Decorator: profile every call to *func* with cProfile.
- **Calls**: functools.wraps, self._profile.runcall

### metrun.cprofile_bridge.CProfileBridge.profile_block
> Context manager: profile the enclosed code block.
- **Calls**: self._profile.enable, self._profile.disable

### demo.handler
- **Calls**: demo.slow_query

### metrun.cli.main
- **Calls**: metrun.cli.cli

### metrun.profiler.ExecutionTracer._get_stack
- **Calls**: hasattr

### metrun.profiler.ExecutionTracer._ensure_record
- **Calls**: FunctionRecord

### metrun.profiler.ExecutionTracer.reset
- **Calls**: self._records.clear

### metrun.profiler.section
> Context manager using the default (or supplied) tracer.
- **Calls**: _tracer.section

### metrun.profiler.reset
> Reset all collected records in the default (or supplied) tracer.
- **Calls**: _tracer.reset

### metrun.cprofile_bridge.CProfileBridge.__init__
- **Calls**: cProfile.Profile

## Process Flows

Key execution flows identified:

### Flow 1: inspect
```
inspect [metrun.cli]
```

### Flow 2: scan
```
scan [metrun.cli]
```

### Flow 3: to_records
```
to_records [metrun.cprofile_bridge.CProfileBridge]
```

### Flow 4: profile
```
profile [metrun.cli]
```

### Flow 5: flame
```
flame [metrun.cli]
```

### Flow 6: main
```
main [examples.profile.basic_app]
  └─> handler
      └─> slow_query
  └─ →> print_report
  └─ →> analyse
```

### Flow 7: _enter
```
_enter [metrun.profiler.ExecutionTracer]
```

### Flow 8: trace
```
trace [metrun.profiler.ExecutionTracer]
```

### Flow 9: get_stats
```
get_stats [metrun.cprofile_bridge.CProfileBridge]
```

### Flow 10: render_svg_string
```
render_svg_string [metrun.flamegraph]
```

## Key Classes

### metrun.profiler.ExecutionTracer
> Thread-local call-stack tracer.

Usage — decorator:
    tracer = ExecutionTracer()

    @tracer.trac
- **Methods**: 9
- **Key Methods**: metrun.profiler.ExecutionTracer.__init__, metrun.profiler.ExecutionTracer._get_stack, metrun.profiler.ExecutionTracer._ensure_record, metrun.profiler.ExecutionTracer._enter, metrun.profiler.ExecutionTracer._exit, metrun.profiler.ExecutionTracer.records, metrun.profiler.ExecutionTracer.reset, metrun.profiler.ExecutionTracer.trace, metrun.profiler.ExecutionTracer.section

### metrun.cprofile_bridge.CProfileBridge
> Thin wrapper around :class:`cProfile.Profile` that exposes profiling
results as metrun :class:`~metr
- **Methods**: 9
- **Key Methods**: metrun.cprofile_bridge.CProfileBridge.__init__, metrun.cprofile_bridge.CProfileBridge.profile_func, metrun.cprofile_bridge.CProfileBridge.profile_block, metrun.cprofile_bridge.CProfileBridge.get_stats, metrun.cprofile_bridge.CProfileBridge.to_records, metrun.cprofile_bridge.CProfileBridge.save, metrun.cprofile_bridge.CProfileBridge.reset, metrun.cprofile_bridge.CProfileBridge.__enter__, metrun.cprofile_bridge.CProfileBridge.__exit__

### metrun.bottleneck.BottleneckEngine
> Analyse a dict of FunctionRecords and return a ranked list of Bottlenecks.

Example::

    engine = 
- **Methods**: 5
- **Key Methods**: metrun.bottleneck.BottleneckEngine.__init__, metrun.bottleneck.BottleneckEngine._total_wall_time, metrun.bottleneck.BottleneckEngine._compute_score, metrun.bottleneck.BottleneckEngine._diagnose, metrun.bottleneck.BottleneckEngine.analyse

### metrun.critical_path.CriticalPath
> The result of a critical-path analysis.
- **Methods**: 1
- **Key Methods**: metrun.critical_path.CriticalPath.length

### metrun.profiler.FunctionRecord
> Aggregated stats for a single function (or call-site).
- **Methods**: 1
- **Key Methods**: metrun.profiler.FunctionRecord.avg_time

### metrun.suggestions.Suggestion
> A single actionable fix suggestion.
- **Methods**: 0

### metrun.critical_path.CriticalPathNode
> A single node in the critical path.
- **Methods**: 0

### metrun.bottleneck.Bottleneck
> A single bottleneck entry produced by the engine.
- **Methods**: 0

## Data Transformation Functions

Key functions that process and transform data:

### metrun.records_io._decode_json_payload
- **Output to**: isinstance, isinstance, payload.decode, json.loads

### metrun.suggestions.format_suggestions
> Render suggestions for a single function as a human-readable string.

Parameters
----------
name:
  
- **Output to**: enumerate, None.join, lines.append, lines.append, lines.append

### metrun.report._format_bottleneck_entry
> Format a single bottleneck entry for the report.
- **Output to**: metrun.report._severity_icon, lines.append, lines.append, lines.append, lines.append

### metrun.report._format_dependency_graph
> Format dependency graph section if there are nodes with children.
- **Output to**: lines.append, lines.append, lines.append

### metrun.report._format_critical_path_section
> Format critical path section if records are provided.
- **Output to**: metrun.critical_path.find_critical_path, lines.append, lines.append, lines.append, metrun.critical_path.format_critical_path

### metrun.report._format_suggestions_section
> Format fix suggestions section for all bottlenecks.
- **Output to**: lines.append, metrun.suggestions.suggest, lines.append, metrun.suggestions.format_suggestions

### metrun.report._format_summary
> Format summary footer section.

### metrun.critical_path.format_critical_path
> Render a :class:`CriticalPath` as a human-readable string.

Example output::

    🧨 Critical Path  (
- **Output to**: lines.append, lines.append, enumerate, None.join, lines.append

## Behavioral Patterns

### state_machine_ExecutionTracer
- **Type**: state_machine
- **Confidence**: 0.70
- **Functions**: metrun.profiler.ExecutionTracer.__init__, metrun.profiler.ExecutionTracer._get_stack, metrun.profiler.ExecutionTracer._ensure_record, metrun.profiler.ExecutionTracer._enter, metrun.profiler.ExecutionTracer._exit

### state_machine_CProfileBridge
- **Type**: state_machine
- **Confidence**: 0.70
- **Functions**: metrun.cprofile_bridge.CProfileBridge.__init__, metrun.cprofile_bridge.CProfileBridge.profile_func, metrun.cprofile_bridge.CProfileBridge.profile_block, metrun.cprofile_bridge.CProfileBridge.get_stats, metrun.cprofile_bridge.CProfileBridge.to_records

## Public API Surface

Functions exposed as public API (no underscore prefix):

- `metrun.toon.generate_toon` - 67 calls
- `metrun.cli.inspect` - 31 calls
- `metrun.cli.scan` - 27 calls
- `metrun.cprofile_bridge.CProfileBridge.to_records` - 26 calls
- `metrun.cli.profile` - 20 calls
- `metrun.report.generate_report` - 17 calls
- `metrun.critical_path.find_critical_path` - 16 calls
- `metrun.flamegraph.render_ascii` - 13 calls
- `metrun.bottleneck.BottleneckEngine.analyse` - 13 calls
- `metrun.records_io.load_records_file` - 10 calls
- `metrun.cli.flame` - 8 calls
- `metrun.suggestions.suggest` - 8 calls
- `metrun.suggestions.format_suggestions` - 7 calls
- `metrun.critical_path.format_critical_path` - 7 calls
- `metrun.records_io.records_to_payload` - 6 calls
- `examples.profile.basic_app.main` - 6 calls
- `metrun.profiler.ExecutionTracer.trace` - 6 calls
- `metrun.cprofile_bridge.CProfileBridge.get_stats` - 5 calls
- `metrun.toon.save_toon` - 4 calls
- `metrun.records_io.save_records_json` - 4 calls
- `metrun.flamegraph.render_svg_string` - 4 calls
- `metrun.profiler.ExecutionTracer.section` - 4 calls
- `metrun.records_io.load_records_json` - 3 calls
- `metrun.flamegraph.render_svg` - 3 calls
- `demo.slow_query` - 2 calls
- `metrun.cli.cli` - 2 calls
- `metrun.records_io.dump_records_json` - 2 calls
- `metrun.suggestions.print_suggestions` - 2 calls
- `examples.profile.basic_app.slow_query` - 2 calls
- `metrun.report.print_report` - 2 calls
- `metrun.critical_path.print_critical_path` - 2 calls
- `metrun.flamegraph.print_ascii` - 2 calls
- `metrun.bottleneck.analyse` - 2 calls
- `metrun.profiler.trace` - 2 calls
- `metrun.cprofile_bridge.CProfileBridge.profile_func` - 2 calls
- `metrun.cprofile_bridge.CProfileBridge.profile_block` - 2 calls
- `demo.handler` - 1 calls
- `metrun.cli.main` - 1 calls
- `metrun.records_io.record_to_payload` - 1 calls
- `examples.profile.basic_app.handler` - 1 calls

## System Interactions

How components interact:

```mermaid
graph TD
    inspect --> command
    inspect --> argument
    inspect --> option
    scan --> command
    scan --> argument
    scan --> option
    to_records --> get_stats
    to_records --> sort_stats
    to_records --> items
    to_records --> list
    profile --> command
    profile --> argument
    profile --> option
    flame --> command
    flame --> argument
    flame --> option
    flame --> Stats
    main --> handler
    main --> print_report
    main --> list
    main --> analyse
    main --> range
    _enter --> _get_stack
    _enter --> append
    _enter --> _ensure_record
    trace --> wraps
    trace --> _enter
    trace --> perf_counter
    trace --> func
    trace --> _exit
```

## Reverse Engineering Guidelines

1. **Entry Points**: Start analysis from the entry points listed above
2. **Core Logic**: Focus on classes with many methods
3. **Data Flow**: Follow data transformation functions
4. **Process Flows**: Use the flow diagrams for execution paths
5. **API Surface**: Public API functions reveal the interface

## Context for LLM

Maintain the identified architectural patterns and public API surface when suggesting changes.