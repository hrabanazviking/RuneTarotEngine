# RuneTarot — AI Contributor Guide

## Key Principles

1. **No hardcoded data** — All card meanings, correspondences, spread definitions, and settings live in `data/` YAML files
2. **Modular architecture** — Each subsystem in `src/` is self-contained with clear interfaces
3. **Fault-tolerant** — Every subsystem wrapped in try/except, graceful degradation
4. **File-location agnostic** — Uses `pathlib` and `get_project_root()`, no absolute paths
5. **GD-first** — Default to Golden Dawn numbering (Justice=8, Strength=11)
6. **Never modify base data** — Session changes stored in `session/`

## Initialization Order (engine.py)

1. ConfigLoader
2. GoldenDawnEngine (no dependencies)
3. TarotDeck (data dir only)
4. SpreadManager (data dir only)
5. TarotReader (depends on GD engine)
6. AIReader (depends on GD engine + config)
7. CardRenderer (depends on GD engine)
8. SessionManager (session dir only)

## File Structure

- `data/*.yaml` — Static data (NEVER modified at runtime)
- `src/*.py` — Core engine modules
- `tui/app.py` — Main Textual application
- `tui/screens/*.py` — TUI screen classes
- `tui/widgets/*.py` — TUI widget classes
- `session/*.yaml` — Runtime reading data
- `exports/*` — Exported readings

## Adding a New Spread

1. Add spread definition to `data/spreads.yaml`
2. Include positions with row/col for TUI layout
3. Add GD meaning for each position
4. No code changes needed — SpreadManager loads from YAML

## Adding a New Card Correspondence

1. Modify the appropriate YAML file in `data/`
2. Never modify code to add correspondence data
3. The GoldenDawnEngine loads all correspondences from `data/gd_correspondences.yaml`

## Coding Standards

- PEP 8 with 4-space indents
- Type hints extensively
- Use `safe_get()` from utils instead of direct dict access
- Logger from `comprehensive_logging.py` — never `print()`
- Norse/Hermetic comments encouraged (e.g., `# Huginn scouts for relevant threads`)
