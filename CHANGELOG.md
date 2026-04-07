# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.10] - 2026-04-07

### Fixed
- Fix unused-imports issues (ticket-5bf06f1a)

## [0.1.10] - 2026-04-06

### Fixed
- Fix string-concat issues (ticket-669afa97)
- Fix unused-imports issues (ticket-dd81ce1e)
- Fix llm-generated-code issues (ticket-ec51eda5)
- Fix smart-return-type issues (ticket-03bfe0c1)
- Fix ai-boilerplate issues (ticket-fc2aa2e5)
- Fix smart-return-type issues (ticket-667355b7)
- Fix unused-imports issues (ticket-5ac10040)
- Fix magic-numbers issues (ticket-237fc1a2)
- Fix ai-boilerplate issues (ticket-f6603825)
- Fix unused-imports issues (ticket-193291c9)
- Fix smart-return-type issues (ticket-dcb20d6a)
- Fix unused-imports issues (ticket-d11fa4f0)
- Fix string-concat issues (ticket-b89ad96e)
- Fix unused-imports issues (ticket-ee310602)
- Fix duplicate-imports issues (ticket-f7d49f28)
- Fix magic-numbers issues (ticket-7fdeaa6a)
- Fix smart-return-type issues (ticket-af2e7bd7)
- Fix unused-imports issues (ticket-afd4a21d)
- Fix string-concat issues (ticket-dbe250cc)
- Fix unused-imports issues (ticket-cf926a5c)
- Fix unused-imports issues (ticket-c579906e)

## [Unreleased]

### Added
- `metrun.toon` module — TOON-format metric tree generator (`generate_toon`, `save_toon`).
- `metrun scan` CLI command — auto-profile a script and generate `metrun.toon.yaml` with bottlenecks, critical path, suggestions, endpoints, and call tree.
- TOON output includes sections: `SUMMARY`, `BOTTLENECKS`, `CRITICAL-PATH`, `SUGGESTIONS`, `ENDPOINTS`, `TREE`.
- 18 new tests for the toon module and scan CLI.

### Fixed
- `CProfileBridge` now filters user site-packages (`~/.local/lib/…`) alongside system site-packages.
- Import-machinery functions (`find_spec`, `_path_hook`, `exec_module`, etc.) are excluded from reports.

### Docs
- Document language-neutral record export/import and re-export examples in the README and generated docs.
- Document automatic project scanning, endpoint recognition, and TOON output in the README.

## [0.1.8] - 2026-04-07

### Docs
- Update README.md

### Other
- Update examples/conftest.py
- Update examples/profile/basic_app.py
- Update examples/profile/test_basic_app.py
- Update examples/records/demo.jsonl
- Update examples/records/test_demo_records.py

## [0.1.7] - 2026-04-07

### Docs
- Update CHANGELOG.md
- Update README.md
- Update TODO.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md

### Test
- Update tests/test_toon.py

### Other
- Update .pyqual/pipeline.db
- Update metrun/__init__.py
- Update metrun/cli.py
- Update metrun/cprofile_bridge.py
- Update metrun/toon.py
- Update project.sh
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- ... and 15 more files

## [0.1.6] - 2026-04-07

### Docs
- Update CHANGELOG.md
- Update README.md
- Update TODO.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md

### Test
- Update tests/test_records_io.py
- Update tests/test_suggestions.py

### Other
- Update metrun/__init__.py
- Update metrun/bottleneck.py
- Update metrun/cli.py
- Update metrun/cprofile_bridge.py
- Update metrun/profiler.py
- Update metrun/records_io.py
- Update metrun/report.py
- Update metrun/suggestions.py
- Update planfile.yaml
- Update project/analysis.toon.yaml
- ... and 18 more files

## [0.1.5] - 2026-04-06

### Docs
- Update README.md

### Other
- Update metrun/cprofile_bridge.py

## [0.1.4] - 2026-04-06

### Docs
- Update CHANGELOG.md
- Update README.md
- Update TODO.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md

### Test
- Update tests/test_cprofile_bridge.py

### Other
- Update .gitignore
- Update .pyqual/pipeline.db
- Update metrun/bottleneck.py
- Update metrun/cli.py
- Update metrun/cprofile_bridge.py
- Update planfile.yaml
- Update prefact.yaml
- Update project.sh
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- ... and 18 more files

## [0.1.3] - 2026-04-06

### Docs
- Update README.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md

### Other
- Update ai_costs.csv
- Update project.sh
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- ... and 8 more files

## [0.1.2] - 2026-04-06

### Docs
- Update README.md

### Other
- Update metrun/report.py
- Update project/validation.toon.yaml

## [0.1.1] - 2026-04-06

### Docs
- Update README.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md

### Other
- Update .gitignore
- Update .idea/.gitignore
- Update .pyqual/pipeline.db
- Update demo.py
- Update metrun/bottleneck.py
- Update metrun/cli.py
- Update metrun/cprofile_bridge.py
- Update metrun/report.py
- Update metrun/suggestions.py
- Update project.sh
- ... and 14 more files

