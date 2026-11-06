"""Typed errors raised by the library."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Literal

ErrorCode = Literal["invalid_name", "conflict", "unsafe_path"]

_MAX_MESSAGE = 200


class ScaffoldError(Exception):
    """Base class of every error raised by hex_scaffold.

    Attributes:
        code: stable machine-readable error code.
        paths: relative POSIX paths the error is about (may be empty).
    """

    def __init__(self, code: ErrorCode, message: str, paths: Iterable[str] = ()) -> None:
        super().__init__(message[:_MAX_MESSAGE])
        self.code: ErrorCode = code
        self.paths: tuple[str, ...] = tuple(paths)
