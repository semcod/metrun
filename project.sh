#!/usr/bin/env bash
set -e
clear

VENV="venv"
PIP="$VENV/bin/pip"

if [ ! -f "$PIP" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV"
elif ! head -1 "$PIP" | grep -q "$(pwd)"; then
    echo "Virtual environment has broken paths (moved from another location). Recreating..."
    rm -rf "$VENV"
    python3 -m venv "$VENV"
fi

#$PIP install -e . --quiet
$PIP install regix --upgrade --quiet
#$PIP install pyqual --upgrade --quiet
$PIP install prefact --upgrade --quiet
$PIP install vallm --upgrade --quiet
$PIP install redup --upgrade --quiet
$PIP install glon --upgrade --quiet
$PIP install goal --upgrade --quiet
$PIP install code2logic --upgrade --quiet
$PIP install code2llm --upgrade --quiet
$VENV/bin/code2llm ./ -f all -o ./project --no-chunk
rm -f project/analysis.json
rm -f project/analysis.yaml

$PIP install code2docs --upgrade --quiet
$VENV/bin/code2docs ./ --readme-only
$VENV/bin/redup scan . --format toon --output ./project
$VENV/bin/vallm batch . --recursive --format toon --output ./project
$VENV/bin/prefact -a --skip-examples

echo ""
echo "=== metrun performance profiling ==="
$PIP install -e ".[dev]" --quiet

# Enhanced report: bottlenecks + critical path + suggestions
$VENV/bin/metrun inspect demo.py > project/metrun-cli-inspect.txt 2>&1 || true

# Profile with ASCII flamegraph
$VENV/bin/metrun profile demo.py --ascii-flame > project/metrun-flame.txt 2>&1 || true

# SVG flamegraph
CLI_FLAME_LOG="$(mktemp /tmp/metrun-cli-flame-XXXX.log)"
$VENV/bin/metrun profile demo.py --flame project/metrun-cli-flame.svg > "$CLI_FLAME_LOG" 2>&1 || true
tail -n 1 "$CLI_FLAME_LOG" > project/metrun-cli-flame.txt
rm -f "$CLI_FLAME_LOG"

# Measure the CLI endpoint flows themselves with metrun's own tracer
$VENV/bin/python - <<'PY' > project/metrun-cli-flows.txt 2>&1 || true
import cProfile
import contextlib
import io
import runpy
import tempfile
from pathlib import Path

from click.testing import CliRunner

from metrun import analyse, get_records, print_report, reset, section
from metrun.cli import cli

reset()
runner = CliRunner()
demo_path = Path("demo.py").resolve()

with tempfile.TemporaryDirectory(prefix="metrun-cli-") as tmpdir:
    tmpdir = Path(tmpdir)
    prof_path = tmpdir / "demo.prof"
    svg_path = tmpdir / "flame.svg"

    profiler = cProfile.Profile()
    with contextlib.redirect_stdout(io.StringIO()):
        profiler.runcall(runpy.run_path, str(demo_path), run_name="__main__")
    profiler.dump_stats(str(prof_path))

    with section("cli.profile"):
        profile_result = runner.invoke(cli, ["profile", str(demo_path)], catch_exceptions=False)
        if profile_result.exit_code != 0:
            raise SystemExit(profile_result.exit_code)

    with section("cli.inspect"):
        inspect_result = runner.invoke(cli, ["inspect", str(demo_path)], catch_exceptions=False)
        if inspect_result.exit_code != 0:
            raise SystemExit(inspect_result.exit_code)

    with section("cli.flame"):
        flame_result = runner.invoke(
            cli,
            ["flame", str(prof_path), "--output", str(svg_path)],
            catch_exceptions=False,
        )
        if flame_result.exit_code != 0:
            raise SystemExit(flame_result.exit_code)

bottlenecks = analyse(get_records())
print("=== metrun CLI endpoint flows ===")
print_report(bottlenecks)
PY

echo "✓ Performance reports saved to project/metrun-*.txt"

# Generate metrun.toon.yaml with the scan command
$VENV/bin/metrun scan demo.py --output project/ 2>&1 || true

echo ""
echo "=== metrun example tests ==="
$VENV/bin/python -m pytest examples/ -v --tb=short 2>&1 | tail -10 || true

echo ""
echo "✓ All tasks completed"