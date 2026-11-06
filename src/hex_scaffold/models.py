"""Data model and size limits."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath

MAX_NAME_LENGTH = 40
MAX_PLAN_FILES = 256
MAX_FILE_BYTES = 1024 * 1024
MAX_PATH_DEPTH = 32


@dataclass(frozen=True)
class PlannedFile:
    """A file to create: ``path`` relative to the root and its text ``content``."""

    path: PurePosixPath
    content: str
