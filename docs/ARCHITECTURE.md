# Architecture

## Purpose

`trysac-hex-scaffold` is a small, dependency-free Python library (import name `hex_scaffold`) with a CLI that generates a hexagonal (ports and adapters) module as byte-stable, importable Python.

## Shape

```text
caller code / CLI --> hex_scaffold (public API in __init__.py)
                          |
                          +-- planner.py  (validate names, build PlannedFile list)
                          +-- _templates.py (source templates for the 10 files)
                          +-- tree.py     (ASCII tree rendering, no I/O)
                          +-- writer.py   (the only module that writes to disk)
```

- **Public API**: the names listed in `__all__` of `src/hex_scaffold/__init__.py`: `ErrorCode`, `PlannedFile`, `ScaffoldError`, `__version__`, `plan_module`, `render_tree`, `write_plan`.
- **Generated layers**: the domain imports nothing from application or adapters; the application depends only on the domain and on its port Protocol; adapters implement the ports.
- **Errors**: invalid input raises `ScaffoldError` with a stable code and, where relevant, the affected paths.
- **Logging**: `logging.getLogger(__name__)` with a `NullHandler`; the library never configures logging.
- **Side effects**: only `write_plan` touches the file system. The CLI prints to stdout and stderr.

## Decisions

Architecture decisions are recorded in [decisions/](decisions/) as numbered ADRs.
