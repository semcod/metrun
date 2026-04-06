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

# Profile demo.py with full report
$VENV/bin/metrun inspect demo.py > project/metrun-demo.txt 2>&1 || true

# Profile with ASCII flamegraph
$VENV/bin/metrun profile demo.py --ascii-flame > project/metrun-flame.txt 2>&1 || true

# Profile CLI endpoints using cProfile bridge
$VENV/bin/python -c "
import sys
sys.path.insert(0, '.')
from metrun.cprofile_bridge import CProfileBridge
from metrun import analyse, print_report

bridge = CProfileBridge()

# Profile 'metrun profile' command
with bridge.profile_block():
    import subprocess
    subprocess.run([sys.executable, '-m', 'metrun', 'profile', 'demo.py'], 
                   capture_output=True, timeout=30)
bottlenecks = analyse(bridge.to_records())
print('=== CLI: metrun profile ===')
print_report(bottlenecks)
" > project/metrun-cli-profile.txt 2>&1 || true

echo "✓ Performance reports saved to project/metrun-*.txt"