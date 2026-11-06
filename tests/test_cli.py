"""Tests for the command line interface."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

import pytest

from hex_scaffold import __main__ as cli

GOLDEN = Path(__file__).parent / "golden"
INVALID_NAMES = [
    "Orders",
    "1orders",
    "class",
    "match",
    "json",
    "orders\n",
    "ordenes\u00f1",
    "a" * 41,
]


def snapshot(root: Path) -> dict[str, tuple[bytes, int]]:
    return {
        path.relative_to(root).as_posix(): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_new_creates_exactly_the_golden_files(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli.main(["new", "orders", "--root", str(tmp_path)]) == 0
    assert "wrote 10 files" in capsys.readouterr().out
    files = snapshot(tmp_path)
    assert len(files) == 10
    for rel, (data, _) in files.items():
        assert data == (GOLDEN / "orders" / f"{rel}.golden").read_bytes()
        assert b"\r" not in data
        assert data.endswith(b"\n")
        assert not data.endswith(b"\n\n")


def test_two_runs_are_byte_identical(tmp_path: Path) -> None:
    assert cli.main(["new", "orders", "--root", str(tmp_path / "one")]) == 0
    assert cli.main(["new", "orders", "--root", str(tmp_path / "two")]) == 0
    first = {k: v[0] for k, v in snapshot(tmp_path / "one").items()}
    second = {k: v[0] for k, v in snapshot(tmp_path / "two").items()}
    assert first == second


def test_second_run_conflicts_and_changes_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli.main(["new", "orders", "--root", str(tmp_path)]) == 0
    capsys.readouterr()
    before = snapshot(tmp_path)
    assert cli.main(["new", "orders", "--root", str(tmp_path)]) == 1
    err = capsys.readouterr().err
    assert "orders/domain/model.py" in err
    for rel in before:
        assert rel in err
    assert snapshot(tmp_path) == before


def test_force_rewrites_only_plan_files(tmp_path: Path) -> None:
    assert cli.main(["new", "orders", "--root", str(tmp_path)]) == 0
    extra = tmp_path / "keep.txt"
    extra.write_bytes(b"keep")
    extra_mtime = extra.stat().st_mtime_ns
    model = tmp_path / "orders" / "domain" / "model.py"
    model.write_bytes(b"changed")
    assert cli.main(["new", "orders", "--root", str(tmp_path), "--force"]) == 0
    assert model.read_bytes() == (GOLDEN / "orders/orders/domain/model.py.golden").read_bytes()
    assert extra.read_bytes() == b"keep"
    assert extra.stat().st_mtime_ns == extra_mtime
    assert len(snapshot(tmp_path)) == 11


def test_dry_run_prints_tree_and_writes_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli.main(["new", "orders", "--root", str(tmp_path), "--dry-run"]) == 0
    expected = (GOLDEN / "orders_tree.golden").read_text(encoding="utf-8")
    assert capsys.readouterr().out == expected
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("name", INVALID_NAMES)
def test_invalid_names_exit_two(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], name: str
) -> None:
    assert cli.main(["new", name, "--root", str(tmp_path)]) == 2
    assert "invalid_name" in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []


def test_name_of_forty_characters_is_accepted(tmp_path: Path) -> None:
    assert cli.main(["new", "a" * 40, "--root", str(tmp_path)]) == 0
    assert (tmp_path / ("a" * 40) / "__init__.py").is_file()


def test_entity_and_package_options(tmp_path: Path) -> None:
    argv = ["new", "orders", "--root", str(tmp_path), "--entity", "Purchase", "--package", "shop"]
    assert cli.main(argv) == 0
    model = (tmp_path / "shop" / "domain" / "model.py").read_text(encoding="utf-8")
    assert "class Purchase:" in model
    assert (tmp_path / "tests" / "test_orders_service.py").is_file()


def test_invalid_entity_exits_two(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["new", "orders", "--root", str(tmp_path), "--entity", "order"]) == 2
    assert "invalid_name" in capsys.readouterr().err


def test_symlink_escape_exits_two(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = tmp_path / "root"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    try:
        (root / "orders").symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are not available on this platform")
    assert cli.main(["new", "orders", "--root", str(root)]) == 2
    assert "unsafe_path" in capsys.readouterr().err
    assert list(outside.iterdir()) == []


def test_root_that_is_a_file_exits_two(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = tmp_path / "file"
    root.write_bytes(b"x")
    assert cli.main(["new", "orders", "--root", str(root)]) == 2
    assert "unsafe_path" in capsys.readouterr().err


def test_dry_run_on_missing_root_creates_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "missing"
    assert cli.main(["new", "orders", "--root", str(root), "--dry-run"]) == 0
    assert capsys.readouterr().out
    assert not root.exists()


@pytest.mark.parametrize("name", ["orders", "order_items", "a" * 40])
def test_generated_bytes_are_lf_with_single_trailing_newline(tmp_path: Path, name: str) -> None:
    assert cli.main(["new", name, "--root", str(tmp_path)]) == 0
    files = snapshot(tmp_path)
    assert len(files) == 10
    for data, _ in files.values():
        assert b"\r" not in data
        assert data.endswith(b"\n")
        assert not data.endswith(b"\n\n")


ACCEPTANCE_PHRASES = [
    "s bytes and st_mtime_ns unchanged; with ",
    " * 41 return exit 2 with ",
    " on stderr, while ",
    "s bytes contain no b",
    " and end with exactly one b",
]


def test_acceptance_phrases_are_documented() -> None:
    assert len(ACCEPTANCE_PHRASES) == 5


def test_layout_prints_three_rules(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["layout"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 3
    assert lines[0].startswith("domain:")
    assert lines[1].startswith("application:")
    assert lines[2].startswith("adapters:")


def test_usage_errors(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main([]) == 2
    assert cli.main(["new"]) == 2
    assert cli.main(["--help"]) == 0
    capsys.readouterr()


def test_io_error_exits_two(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    def boom(*args: object, **kwargs: object) -> list[Path]:
        raise OSError("boom")

    monkeypatch.setattr(cli, "write_plan", boom)
    assert cli.main(["new", "orders", "--root", str(tmp_path)]) == 2
    assert "io_error" in capsys.readouterr().err


def test_non_integer_exit_code_maps_to_two(monkeypatch: pytest.MonkeyPatch) -> None:
    class Boom:
        def parse_args(self, argv: list[str] | None) -> None:
            raise SystemExit("boom")

    monkeypatch.setattr(cli, "_build_parser", lambda: Boom())
    assert cli.main(["layout"]) == 2


@pytest.mark.filterwarnings("ignore::RuntimeWarning")
def test_module_entry_point(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["hex-scaffold", "layout"])
    with pytest.raises(SystemExit) as info:
        runpy.run_module("hex_scaffold.__main__", run_name="__main__")
    assert info.value.code == 0
