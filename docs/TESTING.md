# Testing

## Running

```sh
uv run pytest --cov=hex_scaffold   # tests with coverage report
uv run python scripts/check.py      # every gate, as CI and the factory run it
```

## Existing tests

- `tests/test_cli.py`: exercises `hex_scaffold.__main__.main`. It covers the `new` command for the golden output of `orders` (exactly the 10 files, byte-equal to the files under `tests/golden/orders`), the `--dry-run` tree output (which must create no files), the conflict exit code 1 without `--force`, invalid names exiting with 2, and the `layout` command.
- Golden files are stored with a `.golden` suffix so pytest does not collect them.

The generated test module (`tests/test_<name>_service.py`) is produced by the generator and is verified against the golden files; its own tests use only the in-memory adapter.

## Policy

- Branch coverage of `src/hex_scaffold` must stay at or above 80 %; the gate fails below it.
- Tests exercise the public API (`import hex_scaffold`) and assert observable effects: return values, raised exceptions and their messages.
- Each bug fix starts with a failing test that reproduces it.
- Tests are deterministic: no network, no wall clock, no dependence on test order.

## Layout

`tests/test_<module>.py` mirrors each public module; `tests/golden/` holds the expected generated output.
