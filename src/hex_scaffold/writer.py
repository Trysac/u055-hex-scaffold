"""Safe materialisation of a plan on disk."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from pathlib import Path, PurePosixPath

from hex_scaffold.errors import ScaffoldError
from hex_scaffold.models import MAX_FILE_BYTES, MAX_PATH_DEPTH, MAX_PLAN_FILES, PlannedFile

logger = logging.getLogger(__name__)

_FORBIDDEN_CHARS = (chr(92), ":", chr(0))


def _unsafe(label: str, reason: str) -> ScaffoldError:
    clipped = label[:100]
    return ScaffoldError("unsafe_path", f"unsafe path {clipped!a}: {reason}", (clipped,))


def _prepare(entry: PlannedFile) -> tuple[tuple[str, ...], bytes]:
    path = entry.path
    if not isinstance(path, PurePosixPath):
        raise ScaffoldError("unsafe_path", "plan entry path must be a PurePosixPath")
    label = path.as_posix()
    parts = path.parts
    if not parts or path.is_absolute():
        raise _unsafe(label, "must be a non-empty relative path")
    if len(parts) > MAX_PATH_DEPTH:
        raise _unsafe(label, "path is too deep")
    for part in parts:
        if part == ".." or any(char in part for char in _FORBIDDEN_CHARS):
            raise _unsafe(label, "forbidden path component")
    if not isinstance(entry.content, str):
        raise _unsafe(label, "content must be text")
    try:
        data = entry.content.encode("utf-8")
    except UnicodeEncodeError:
        raise _unsafe(label, "content is not valid UTF-8 text") from None
    if len(data) > MAX_FILE_BYTES:
        raise _unsafe(label, "content is too large")
    return parts, data


def _check_target(root: Path, parts: tuple[str, ...], label: str) -> Path:
    current = root
    last = len(parts) - 1
    for index, part in enumerate(parts):
        current = current / part
        if current.is_symlink():
            raise _unsafe(label, "a path component is a symlink")
        if not current.exists():
            break
        if index < last:
            if not current.is_dir():
                raise _unsafe(label, "a path component is not a directory")
        elif current.is_dir():
            raise _unsafe(label, "a directory exists where a file is expected")
    target = root.joinpath(*parts)
    try:
        target.parent.resolve().relative_to(root)
    except ValueError:
        raise _unsafe(label, "resolves outside the root") from None
    return target


def write_plan(plan: Sequence[PlannedFile], root: Path, *, force: bool = False) -> list[Path]:
    """Write ``plan`` below ``root`` and return the written paths in plan order.

    Every target is checked before anything is written: each resolved parent must stay
    inside the resolved root and no existing path component may be a symlink. Existing
    files raise ``conflict`` (carrying every path) unless ``force`` is true. Files are
    written as UTF-8 bytes, so newlines are exactly those of the content (LF for generated
    code) on every platform.

    The check-then-write sequence is subject to TOCTOU races: a concurrent process that
    swaps a directory for a symlink between the check and the write is not detected.

    Raises:
        ScaffoldError: ``unsafe_path`` for escaping, symlinked, malformed or oversized
            entries; ``conflict`` for existing files without ``force``.
    """
    entries = list(plan)
    if len(entries) > MAX_PLAN_FILES:
        raise ScaffoldError("unsafe_path", f"plan has more than {MAX_PLAN_FILES} files")
    resolved_root = root.resolve()
    if resolved_root.exists() and not resolved_root.is_dir():
        raise ScaffoldError("unsafe_path", "root is not a directory")
    prepared: list[tuple[Path, bytes]] = []
    conflicts: list[str] = []
    for entry in entries:
        parts, data = _prepare(entry)
        label = entry.path.as_posix()
        target = _check_target(resolved_root, parts, label)
        if target.exists():
            conflicts.append(label)
        prepared.append((target, data))
    if conflicts and not force:
        raise ScaffoldError(
            "conflict",
            f"{len(conflicts)} file(s) already exist; use force to overwrite",
            sorted(conflicts),
        )
    logger.debug("writing %d files", len(prepared))
    written: list[Path] = []
    for target, data in prepared:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        written.append(target)
    return written
