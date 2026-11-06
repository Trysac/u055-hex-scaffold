"""Behavior tests for the public API of hex_scaffold."""

from __future__ import annotations

import pytest

import hex_scaffold


def test_normalize_trims_and_lowercases() -> None:
    assert hex_scaffold.normalize("  Hello World ") == "hello world"


@pytest.mark.parametrize("value", ["", "   ", "\t\n"])
def test_normalize_rejects_blank_input(value: str) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        hex_scaffold.normalize(value)


def test_version_is_semver() -> None:
    parts = hex_scaffold.__version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)
