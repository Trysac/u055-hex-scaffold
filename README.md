# hex-scaffold

[![PyPI version](https://img.shields.io/pypi/v/trysac-hex-scaffold)](https://pypi.org/project/trysac-hex-scaffold/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-hex-scaffold)](LICENSE)
[![CI](https://github.com/Trysac/u055-hex-scaffold/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u055-hex-scaffold/actions/workflows/ci.yml)

CLI that generates a hexagonal module (domain, port, application service, in-memory adapter, tests) as byte-stable, importable Python

## Problem

Describe in two or three sentences the concrete problem this utility solves, who hits it, and what
they do today without it. Replace this paragraph when the first real feature lands.

## Install

```sh
pip install trysac-hex-scaffold
# or
uv add trysac-hex-scaffold
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
import hex_scaffold

# normalize() trims surrounding whitespace and lower-cases the text.
print(hex_scaffold.normalize("  Hello World "))  # -> "hello world"

# Blank input is rejected explicitly instead of returning an empty string.
try:
    hex_scaffold.normalize("   ")
except ValueError as exc:
    print(f"rejected: {exc}")
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) and [decisions](docs/decisions/)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)
- [Changelog](CHANGELOG.md) and [contributing guide](CONTRIBUTING.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
