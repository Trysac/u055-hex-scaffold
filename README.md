# hex-scaffold

[![PyPI version](https://img.shields.io/pypi/v/trysac-hex-scaffold)](https://pypi.org/project/trysac-hex-scaffold/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-hex-scaffold)](LICENSE)
[![CI](https://github.com/Trysac/u055-hex-scaffold/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u055-hex-scaffold/actions/workflows/ci.yml)

CLI and library that generates a hexagonal Python module (domain, port, application service, in-memory adapter, tests) as byte-stable, importable Python, using only the standard library.

## Problem

Teams adopting hexagonal architecture copy an old module and rename it by hand, dragging along mistakes and inconsistent layering. The boilerplate for entity, repository port, service and a fake adapter is the same every time. hex-scaffold produces the same tested starting point from one name, so the output is identical on every run.

## Install

```sh
pip install trysac-hex-scaffold
# or
uv add trysac-hex-scaffold
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
from pathlib import Path

from hex_scaffold import plan_module, render_tree, write_plan

plan = plan_module("orders")
print(render_tree(plan))
written = write_plan(plan, Path("out"))
print(len(written), "files written")
```

Command line:

```sh
hex-scaffold new orders --root out
hex-scaffold layout
```

## Public API

- `plan_module(name, *, entity=None, package=None) -> list[PlannedFile]`: validates the names and plans the files without writing them. The entity is derived from the name when omitted.
- `PlannedFile`: frozen dataclass with `path: PurePosixPath` (relative to the root) and `content: str`.
- `write_plan(plan, root, *, force=False) -> list[Path]`: writes the plan below `root` and returns the paths in plan order.
- `render_tree(plan) -> str`: sorted ASCII tree of the planned paths, without a trailing newline.
- `ScaffoldError`: raised on failure, with `code` (`invalid_name`, `conflict` or `unsafe_path`) and `paths` (tuple of relative POSIX paths).
- `hex_scaffold.__main__.main(argv) -> int`: CLI entry point.

CLI options of `new <name>`: `--root DIR` (default `.`), `--entity NAME`, `--package NAME`, `--dry-run` (print the tree, write nothing) and `--force` (overwrite existing plan files only).

Exit codes: `0` success, `1` conflict with existing files, `2` usage error, invalid name or unsafe path.

Names must match `[a-z][a-z0-9_]{0,39}` (ASCII), must not be a Python keyword or a standard library module name. Entity names must match `[A-Z][A-Za-z0-9]{0,39}` and must not collide with builtins or generated names. The package name `tests` is rejected.

Derivation of the entity: a trailing `ies` becomes `y`; names ending in `ss`, `us` or `is` stay whole; otherwise one trailing `s` is dropped. Known misfits such as `series` (giving `Sery`) are corrected with `--entity`.

Generated layout under the root: `<pkg>/__init__.py`, `domain/{__init__,model,errors}.py`, `application/{__init__,ports,service}.py`, `adapters/{__init__,in_memory}.py` and `tests/test_<name>_service.py`.

Limits: plans are capped at 256 files, each file at 1 MiB, and paths at 32 components. Exceeding these limits raises `unsafe_path`. The check that targets stay inside the root is resolve-then-write and is subject to TOCTOU races. Output is written as UTF-8 with LF newlines.

## Security

See [docs/SECURITY.md](docs/SECURITY.md) for the threat model and its limits.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
