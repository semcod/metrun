"""
metrun.cli
~~~~~~~~~~

Command-line interface for metrun.

Commands
--------

``metrun profile``
    Profile a Python script with cProfile, display the metrun Bottleneck
    report, and optionally generate an SVG flamegraph.

``metrun flame``
    Generate an SVG flamegraph from an existing ``*.prof`` file.

``metrun inspect``
    Profile a script and show the full enhanced report: bottlenecks +
    critical path + fix suggestions.

``metrun scan``
    Profile a script (or load records) and generate a ``metrun.toon.yaml``
    metric tree describing project bottlenecks in TOON format.

Usage examples::

    # Profile a script and print the bottleneck report
    metrun profile my_script.py

    # Profile and save a flamegraph
    metrun profile my_script.py --flame flame.svg

    # Profile and show the full enhanced report
    metrun inspect my_script.py --top 10

    # Auto-scan and generate metrun.toon.yaml
    metrun scan my_script.py --output project/

    # Scan from pre-collected records
    metrun scan --records profile.json --output project/

    # Convert an existing .prof to SVG flamegraph
    metrun flame profile.prof -o flame.svg

Install CLI entry-point::

    pip install metrun
    # then use:
    metrun --help
"""

from __future__ import annotations

import io
import runpy
from contextlib import redirect_stdout
from typing import Optional

import click

from metrun.bottleneck import analyse
from metrun.cprofile_bridge import CProfileBridge
from metrun.flamegraph import print_ascii, render_svg
from metrun.records_io import load_records_file, save_records_json
from metrun.report import print_report
from metrun.toon import generate_toon, save_toon


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_script(script_path: str) -> CProfileBridge:
    """Run *script_path* under a CProfileBridge and return the bridge."""
    bridge = CProfileBridge()
    with bridge.profile_block(), redirect_stdout(io.StringIO()):
        runpy.run_path(script_path, run_name="__main__")
    return bridge


# ---------------------------------------------------------------------------
# CLI group
# ---------------------------------------------------------------------------

@click.group()
@click.version_option(package_name="metrun")
def cli():
    """metrun — Execution Intelligence Tool.

    Profiles Python scripts and surfaces bottlenecks with human-readable
    diagnosis and actionable fix suggestions.
    """


# ---------------------------------------------------------------------------
# profile
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("script", type=click.Path(exists=True))
@click.option(
    "--top", "-n",
    default=10,
    show_default=True,
    help="Number of top bottlenecks to display.",
)
@click.option(
    "--flame",
    default=None,
    metavar="FILE",
    help="Generate an SVG flamegraph and save to FILE.",
)
@click.option(
    "--ascii-flame",
    "ascii_flame",
    is_flag=True,
    default=False,
    help="Print an ASCII flamegraph to the terminal.",
)
@click.option(
    "--include-stdlib",
    "include_stdlib",
    is_flag=True,
    default=False,
    help="Include Python stdlib / C-builtin functions in the report.",
)
@click.option(
    "--export-records",
    default=None,
    metavar="FILE",
    help="Save the collected records as language-neutral JSON.",
)
def profile(
    script: str,
    top: int,
    flame: Optional[str],
    ascii_flame: bool,
    include_stdlib: bool,
    export_records: Optional[str],
) -> None:
    """Profile SCRIPT and display the bottleneck report.

    SCRIPT is the path to a Python file to profile.
    """
    click.echo(f"🔍 Profiling: {script}")
    bridge = _run_script(script)
    records = bridge.to_records(exclude_stdlib=not include_stdlib)

    if not records:
        click.echo("⚠️  No profiling data collected.")
        return

    if export_records:
        save_records_json(records, export_records)
        click.echo(f"🧾 Records saved → {export_records}")

    bottlenecks = analyse(records)
    print_report(bottlenecks, top_n=top)

    if ascii_flame:
        print_ascii(bottlenecks, top_n=top)

    if flame:
        stats = bridge.get_stats()
        render_svg(stats, flame)
        click.echo(f"🔥 Flamegraph saved → {flame}")


# ---------------------------------------------------------------------------
# inspect  (enhanced report: bottlenecks + critical path + suggestions)
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("script", required=False, type=click.Path(exists=True))
@click.option(
    "--top", "-n",
    default=10,
    show_default=True,
    help="Number of top bottlenecks to display.",
)
@click.option(
    "--flame",
    default=None,
    metavar="FILE",
    help="Also generate an SVG flamegraph and save to FILE.",
)
@click.option(
    "--records",
    "records_file",
    default=None,
    metavar="FILE",
    help="Load language-neutral JSON records produced by another runtime.",
)
@click.option(
    "--ascii-flame",
    "ascii_flame",
    is_flag=True,
    default=False,
    help="Print an ASCII flamegraph to the terminal.",
)
@click.option(
    "--include-stdlib",
    "include_stdlib",
    is_flag=True,
    default=False,
    help="Include Python stdlib / C-builtin functions in the report.",
)
@click.option(
    "--export-records",
    default=None,
    metavar="FILE",
    help="Save the normalised records as language-neutral JSON.",
)
def inspect(
    script: Optional[str],
    top: int,
    flame: Optional[str],
    records_file: Optional[str],
    ascii_flame: bool,
    include_stdlib: bool,
    export_records: Optional[str],
) -> None:
    """Enhanced profile of SCRIPT or records file: bottlenecks + critical path + suggestions.

    SCRIPT is the path to a Python file to profile unless --records is provided.
    """
    if script and not records_file:
        lowered = script.lower()
        if lowered.endswith(".json") or lowered.endswith(".jsonl"):
            records_file = script
            script = None

    if bool(script) == bool(records_file):
        raise click.UsageError("Provide exactly one SCRIPT or --records FILE.")

    bridge: Optional[CProfileBridge] = None
    if records_file:
        click.echo(f"🔍 Inspecting records: {records_file}")
        records = load_records_file(records_file)
        if flame:
            click.echo("⚠️  SVG flamegraphs require a cProfile .prof source; skipping --flame.")
            flame = None
    else:
        click.echo(f"🔍 Inspecting: {script}")
        bridge = _run_script(script)
        records = bridge.to_records(exclude_stdlib=not include_stdlib)

    if export_records:
        save_records_json(records, export_records)
        click.echo(f"🧾 Records saved → {export_records}")

    if not records:
        click.echo("⚠️  No profiling data collected.")
        return

    bottlenecks = analyse(records)

    # Full report with critical path and suggestions
    print_report(
        bottlenecks,
        top_n=top,
        show_graph=True,
        show_critical_path=True,
        records=records,
        show_suggestions=True,
    )

    if ascii_flame:
        print_ascii(bottlenecks, top_n=top)

    if flame:
        if bridge is None:
            raise click.UsageError("SVG flamegraphs require a Python script profile.")
        stats = bridge.get_stats()
        render_svg(stats, flame)
        click.echo(f"🔥 Flamegraph saved → {flame}")


# ---------------------------------------------------------------------------
# scan  (auto-profile + TOON metric tree)
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("script", required=False, type=click.Path(exists=True))
@click.option(
    "--records",
    "records_file",
    default=None,
    metavar="FILE",
    help="Load language-neutral JSON/JSONL records instead of profiling a script.",
)
@click.option(
    "--output", "-o",
    default=".",
    show_default=True,
    help="Output directory for metrun.toon.yaml.",
)
@click.option(
    "--top", "-n",
    default=10,
    show_default=True,
    help="Number of top bottlenecks to include.",
)
@click.option(
    "--include-stdlib",
    "include_stdlib",
    is_flag=True,
    default=False,
    help="Include Python stdlib / C-builtin functions.",
)
@click.option(
    "--export-records",
    default=None,
    metavar="FILE",
    help="Also save the collected records as language-neutral JSON.",
)
def scan(
    script: Optional[str],
    records_file: Optional[str],
    output: str,
    top: int,
    include_stdlib: bool,
    export_records: Optional[str],
) -> None:
    """Auto-profile SCRIPT and generate a metrun.toon.yaml metric tree.

    Profiles the given Python script (or loads --records) and writes a
    compact TOON-format file describing bottlenecks, critical path,
    endpoints, and the metric tree.  The output integrates with the
    project-level TOON ecosystem (code2llm, redup, vallm).
    """
    if script and not records_file:
        lowered = script.lower()
        if lowered.endswith(".json") or lowered.endswith(".jsonl"):
            records_file = script
            script = None

    if bool(script) == bool(records_file):
        raise click.UsageError("Provide exactly one SCRIPT or --records FILE.")

    if records_file:
        click.echo(f"🔍 Scanning records: {records_file}")
        records = load_records_file(records_file)
    else:
        click.echo(f"🔍 Scanning: {script}")
        bridge = _run_script(script)
        records = bridge.to_records(exclude_stdlib=not include_stdlib)

    if not records:
        click.echo("⚠️  No profiling data collected.")
        return

    if export_records:
        save_records_json(records, export_records)
        click.echo(f"🧾 Records saved → {export_records}")

    bottlenecks = analyse(records)
    toon_content = generate_toon(bottlenecks, records, top_n=top)

    from pathlib import Path
    out_dir = Path(output)
    toon_path = save_toon(toon_content, out_dir / "metrun.toon.yaml")
    click.echo(f"✅ {toon_path}")


# ---------------------------------------------------------------------------
# flame  (convert existing .prof to SVG)
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("prof_file", type=click.Path(exists=True))
@click.option(
    "--output", "-o",
    default="flame.svg",
    show_default=True,
    help="Output SVG file path.",
)
@click.option("--width", default=1200, show_default=True, help="SVG canvas width (px).")
def flame(prof_file: str, output: str, width: int):
    """Convert an existing .prof file to an SVG flamegraph.

    PROF_FILE is the path to a cProfile .prof dump
    (created with cProfile.dump_stats or ``metrun profile --save-prof``).
    """
    import pstats

    stats = pstats.Stats(prof_file)
    render_svg(stats, output, width=width)
    click.echo(f"🔥 Flamegraph saved → {output}")


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------

def main():
    cli()


if __name__ == "__main__":
    main()
