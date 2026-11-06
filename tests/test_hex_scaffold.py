"""Tests for plan_module, write_plan and render_tree."""

from __future__ import annotations

import importlib.util
import logging
import re
import sys
from pathlib import Path, PurePosixPath

import pytest

from hex_scaffold import (
    PlannedFile,
    ScaffoldError,
    __version__,
    plan_module,
    render_tree,
    write_plan,
)
from hex_scaffold.models import MAX_FILE_BYTES, MAX_PATH_DEPTH, MAX_PLAN_FILES
from hex_scaffold.planner import derive_entity

GOLDEN = Path(__file__).parent / "golden"
EXPECTED_PATHS = [
    "orders/__init__.py",
    "orders/adapters/__init__.py",
    "orders/adapters/in_memory.py",
    "orders/application/__init__.py",
    "orders/application/ports.py",
    "orders/application/service.py",
    "orders/domain/__init__.py",
    "orders/domain/errors.py",
    "orders/domain/model.py",
    "tests/test_orders_service.py",
]
INVALID_NAMES = [
    "Orders",
    "1orders",
    "class",
    "match",
    "json",
    "orders\n",
    "ordenes\u00f1",
    "a" * 41,
    "",
    "_orders",
    "orders-x",
    "async",
    "case",
]
INVALID_ENTITIES = [
    "order",
    "Order-X",
    "",
    "A" * 41,
    "None",
    "Exception",
    "Protocol",
    "Sequence",
    "NotFoundError",
    "Order\n",
    "1Order",
]


def entity_of(plan: list[PlannedFile]) -> str:
    model = next(f for f in plan if f.path.as_posix().endswith("domain/model.py"))
    match = re.search(r"^class (\w+):", model.content, re.MULTILINE)
    assert match is not None
    return match.group(1)


def run_generated_tests(
    root: Path, package: str, name: str, monkeypatch: pytest.MonkeyPatch
) -> int:
    monkeypatch.syspath_prepend(str(root))
    path = root / "tests" / f"test_{name}_service.py"
    spec = importlib.util.spec_from_file_location(f"generated_{name}_tests", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    count = 0
    try:
        spec.loader.exec_module(module)
        for attr, value in vars(module).items():
            if attr.startswith("test_") and callable(value):
                value()
                count += 1
    finally:
        for loaded in [m for m in sys.modules if m == package or m.startswith(f"{package}.")]:
            del sys.modules[loaded]
    return count


def make_symlink(link: Path, target: Path) -> None:
    try:
        link.symlink_to(target, target_is_directory=target.is_dir())
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are not available on this platform")


def test_version_and_null_handler() -> None:
    assert __version__ == "0.1.0"
    handlers = logging.getLogger("hex_scaffold").handlers
    assert any(isinstance(handler, logging.NullHandler) for handler in handlers)


def test_error_message_is_capped_and_carries_code() -> None:
    error = ScaffoldError("conflict", "x" * 500, ["a", "b"])
    assert error.code == "conflict"
    assert error.paths == ("a", "b")
    assert len(str(error)) == 200


def test_plan_matches_golden_files() -> None:
    plan = plan_module("orders")
    assert [file.path.as_posix() for file in plan] == EXPECTED_PATHS
    assert len(list((GOLDEN / "orders").rglob("*.golden"))) == 10
    for file in plan:
        golden = GOLDEN / "orders" / f"{file.path.as_posix()}.golden"
        assert file.content.encode("utf-8") == golden.read_bytes()


def test_plan_is_deterministic() -> None:
    assert plan_module("orders") == plan_module("orders")


@pytest.mark.parametrize("name", ["orders", "order_items", "categories"])
def test_bytes_have_lf_only_and_one_trailing_newline(name: str) -> None:
    for file in plan_module(name):
        data = file.content.encode("utf-8")
        assert b"\r" not in data
        assert data.endswith(b"\n")
        assert not data.endswith(b"\n\n")


@pytest.mark.parametrize(
    "name",
    ["orders", "categories", "status", "a", "orders_", "order_items", "a" * 40, "series"],
)
def test_generated_files_compile(name: str) -> None:
    for file in plan_module(name):
        compile(file.content, file.path.as_posix(), "exec")


@pytest.mark.parametrize(
    ("name", "package", "entity"),
    [
        ("orders", None, None),
        ("categories", None, None),
        ("order_items", "shop", None),
        ("a", None, "Purchase"),
        ("a" * 40, None, None),
    ],
)
def test_generated_tests_pass(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    package: str | None,
    entity: str | None,
) -> None:
    plan = plan_module(name, entity=entity, package=package)
    write_plan(plan, tmp_path)
    assert run_generated_tests(tmp_path, package or name, name, monkeypatch) == 3


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("orders", "Order"),
        ("categories", "Category"),
        ("status", "Status"),
        ("address", "Address"),
        ("analysis", "Analysis"),
        ("order_items", "OrderItem"),
        ("series", "Sery"),
        ("a", "A"),
        ("s", "S"),
        ("ies", "Ie"),
        ("data", "Data"),
        ("orders_", "Orders"),
        ("order__items", "OrderItem"),
    ],
)
def test_entity_derivation(name: str, expected: str) -> None:
    assert derive_entity(name) == expected
    assert entity_of(plan_module(name)) == expected


def test_entity_override() -> None:
    plan = plan_module("orders", entity="Purchase")
    assert entity_of(plan) == "Purchase"
    assert any("PurchaseService" in file.content for file in plan)
    assert not any("OrderService" in file.content for file in plan)


def test_package_override() -> None:
    plan = plan_module("orders", package="shop")
    paths = [file.path.as_posix() for file in plan]
    assert "shop/domain/model.py" in paths
    assert "tests/test_orders_service.py" in paths
    test_file = next(file for file in plan if file.path.name == "test_orders_service.py")
    assert "from shop.domain.model import Order" in test_file.content
    assert "orders." not in test_file.content


@pytest.mark.parametrize("name", INVALID_NAMES)
def test_invalid_names_are_rejected(name: str) -> None:
    with pytest.raises(ScaffoldError) as info:
        plan_module(name)
    assert info.value.code == "invalid_name"


def test_name_of_forty_characters_is_accepted() -> None:
    plan = plan_module("a" * 40)
    assert plan[0].path.parts[0] == "a" * 40


def test_non_string_name_is_rejected() -> None:
    with pytest.raises(ScaffoldError) as info:
        plan_module(123)  # type: ignore[arg-type]
    assert info.value.code == "invalid_name"


def test_huge_name_message_is_short() -> None:
    with pytest.raises(ScaffoldError) as info:
        plan_module("x" * 5000 + "!")
    assert len(str(info.value)) <= 200
    assert "x" * 100 not in str(info.value)


@pytest.mark.parametrize("entity", INVALID_ENTITIES)
def test_invalid_entities_are_rejected(entity: str) -> None:
    with pytest.raises(ScaffoldError) as info:
        plan_module("orders", entity=entity)
    assert info.value.code == "invalid_name"


def test_non_string_entity_and_package_are_rejected() -> None:
    with pytest.raises(ScaffoldError):
        plan_module("orders", entity=5)  # type: ignore[arg-type]
    with pytest.raises(ScaffoldError):
        plan_module("orders", package=5)  # type: ignore[arg-type]


@pytest.mark.parametrize("name", ["nones", "exceptions"])
def test_derived_entity_that_collides_is_rejected(name: str) -> None:
    with pytest.raises(ScaffoldError) as info:
        plan_module(name)
    assert info.value.code == "invalid_name"
    assert entity_of(plan_module(name, entity="Nothing")) == "Nothing"


@pytest.mark.parametrize("package", ["Orders", "json", "class", "tests", "a" * 41])
def test_invalid_packages_are_rejected(package: str) -> None:
    with pytest.raises(ScaffoldError) as info:
        plan_module("orders", package=package)
    assert info.value.code == "invalid_name"


def test_write_plan_creates_files(tmp_path: Path) -> None:
    root = tmp_path / "out"
    written = write_plan(plan_module("orders"), root)
    assert written == [root.resolve() / path for path in EXPECTED_PATHS]
    for path in written:
        assert path.is_file()


def test_write_plan_empty_plan(tmp_path: Path) -> None:
    assert write_plan([], tmp_path) == []


def test_conflict_reports_every_path_and_writes_nothing(tmp_path: Path) -> None:
    plan = plan_module("orders")
    write_plan(plan, tmp_path)
    with pytest.raises(ScaffoldError) as info:
        write_plan(plan, tmp_path)
    assert info.value.code == "conflict"
    assert info.value.paths == tuple(EXPECTED_PATHS)


def test_partial_conflict_writes_nothing(tmp_path: Path) -> None:
    model = tmp_path / "orders" / "domain" / "model.py"
    model.parent.mkdir(parents=True)
    model.write_bytes(b"mine")
    with pytest.raises(ScaffoldError) as info:
        write_plan(plan_module("orders"), tmp_path)
    assert info.value.paths == ("orders/domain/model.py",)
    assert model.read_bytes() == b"mine"
    assert not (tmp_path / "tests").exists()


def test_force_rewrites_only_plan_files(tmp_path: Path) -> None:
    plan = plan_module("orders")
    write_plan(plan, tmp_path)
    extra = tmp_path / "keep.txt"
    extra.write_bytes(b"keep")
    model = tmp_path / "orders" / "domain" / "model.py"
    model.write_bytes(b"changed")
    write_plan(plan, tmp_path, force=True)
    assert model.read_bytes() == plan[8].content.encode("utf-8")
    assert extra.read_bytes() == b"keep"


def test_symlinked_directory_escaping_root_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "root"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    make_symlink(root / "orders", outside)
    with pytest.raises(ScaffoldError) as info:
        write_plan(plan_module("orders"), root)
    assert info.value.code == "unsafe_path"
    assert list(outside.iterdir()) == []
    assert not (root / "tests").exists()


def test_symlink_inside_root_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "root"
    real = root / "real"
    real.mkdir(parents=True)
    make_symlink(root / "orders", real)
    with pytest.raises(ScaffoldError) as info:
        write_plan(plan_module("orders"), root)
    assert info.value.code == "unsafe_path"
    assert list(real.iterdir()) == []


def test_dangling_symlink_at_file_location_is_rejected(tmp_path: Path) -> None:
    domain = tmp_path / "orders" / "domain"
    domain.mkdir(parents=True)
    link = domain / "model.py"
    try:
        link.symlink_to(tmp_path / "missing-target")
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are not available on this platform")
    with pytest.raises(ScaffoldError) as info:
        write_plan(plan_module("orders"), tmp_path, force=True)
    assert info.value.code == "unsafe_path"
    assert not (tmp_path / "tests").exists()


@pytest.mark.parametrize(
    "raw",
    [
        "/etc/passwd",
        "../escape.txt",
        "a/../../b.txt",
        "",
        "a" + chr(92) + "b.txt",
        "c:/x.txt",
        "a" + chr(0) + "b",
    ],
)
def test_unsafe_plan_paths_are_rejected(tmp_path: Path, raw: str) -> None:
    with pytest.raises(ScaffoldError) as info:
        write_plan([PlannedFile(PurePosixPath(raw), "x")], tmp_path)
    assert info.value.code == "unsafe_path"
    assert list(tmp_path.iterdir()) == []


def test_malformed_entries_are_rejected(tmp_path: Path) -> None:
    with pytest.raises(ScaffoldError):
        write_plan([PlannedFile("x", "y")], tmp_path)  # type: ignore[arg-type]
    with pytest.raises(ScaffoldError):
        write_plan([PlannedFile(PurePosixPath("x"), 5)], tmp_path)  # type: ignore[arg-type]


def test_size_limits(tmp_path: Path) -> None:
    deep = PurePosixPath("/".join(["d"] * (MAX_PATH_DEPTH + 1)) + "/f.txt")
    too_many = [PlannedFile(PurePosixPath(f"f{i}.txt"), "x") for i in range(MAX_PLAN_FILES + 1)]
    too_big = [PlannedFile(PurePosixPath("big.txt"), "x" * (MAX_FILE_BYTES + 1))]
    unencodable = [PlannedFile(PurePosixPath("bad.txt"), "\ud800")]
    for plan in ([PlannedFile(deep, "x")], too_many, too_big, unencodable):
        with pytest.raises(ScaffoldError) as info:
            write_plan(plan, tmp_path)
        assert info.value.code == "unsafe_path"
    assert list(tmp_path.iterdir()) == []


def test_root_that_is_a_file_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "file"
    root.write_bytes(b"x")
    with pytest.raises(ScaffoldError) as info:
        write_plan(plan_module("orders"), root)
    assert info.value.code == "unsafe_path"


def test_file_where_directory_is_expected_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "orders").write_bytes(b"x")
    with pytest.raises(ScaffoldError) as info:
        write_plan(plan_module("orders"), tmp_path)
    assert info.value.code == "unsafe_path"


def test_directory_where_file_is_expected_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "orders" / "__init__.py").mkdir(parents=True)
    with pytest.raises(ScaffoldError) as info:
        write_plan(plan_module("orders"), tmp_path, force=True)
    assert info.value.code == "unsafe_path"


def test_render_tree_matches_golden() -> None:
    expected = (GOLDEN / "orders_tree.golden").read_text(encoding="utf-8")
    plan = plan_module("orders")
    assert render_tree(plan) + "\n" == expected
    assert render_tree(list(reversed(plan))) + "\n" == expected


def test_render_tree_edge_cases() -> None:
    assert render_tree([]) == "."
    mixed = [PlannedFile(PurePosixPath("a"), ""), PlannedFile(PurePosixPath("a/b"), "")]
    assert render_tree(mixed) == ".\n`-- a/\n    `-- b"


def test_render_tree_limits() -> None:
    deep = PurePosixPath("/".join(["d"] * (MAX_PATH_DEPTH + 1)))
    with pytest.raises(ScaffoldError):
        render_tree([PlannedFile(deep, "")])
    many = [PlannedFile(PurePosixPath(f"f{i}"), "") for i in range(MAX_PLAN_FILES + 1)]
    with pytest.raises(ScaffoldError):
        render_tree(many)
