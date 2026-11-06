"""Validation of names and construction of the file plan."""

from __future__ import annotations

import builtins
import keyword
import logging
import re
import sys

from hex_scaffold._templates import FILE_TEMPLATES, render
from hex_scaffold.errors import ScaffoldError
from hex_scaffold.models import MAX_NAME_LENGTH, PlannedFile

logger = logging.getLogger(__name__)

_NAME_RE = re.compile(r"[a-z][a-z0-9_]{0,39}")
_ENTITY_RE = re.compile(r"[A-Z][A-Za-z0-9]{0,39}")
_RESERVED_ENTITIES = frozenset({"Protocol", "Sequence", "NotFoundError"})
_RESERVED_PACKAGES = frozenset({"tests"})


def _clip(value: object) -> str:
    if isinstance(value, str):
        return ascii(value)[:60]
    return f"<{type(value).__name__}>"


def _check_identifier(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise ScaffoldError("invalid_name", f"{label} must be a string, got {_clip(value)}")
    if len(value) > MAX_NAME_LENGTH or _NAME_RE.fullmatch(value) is None:
        raise ScaffoldError(
            "invalid_name", f"{label} {_clip(value)} must match [a-z][a-z0-9_]{{0,39}}"
        )
    if keyword.iskeyword(value) or keyword.issoftkeyword(value):
        raise ScaffoldError("invalid_name", f"{label} {_clip(value)} is a Python keyword")
    if value in sys.stdlib_module_names:
        raise ScaffoldError(
            "invalid_name", f"{label} {_clip(value)} would shadow a standard library module"
        )
    return value


def _check_entity(value: object) -> str:
    if not isinstance(value, str):
        raise ScaffoldError("invalid_name", f"entity must be a string, got {_clip(value)}")
    if len(value) > MAX_NAME_LENGTH or _ENTITY_RE.fullmatch(value) is None:
        raise ScaffoldError(
            "invalid_name",
            f"entity {_clip(value)} must match [A-Z][A-Za-z0-9]{{0,39}}; pass an explicit entity",
        )
    if keyword.iskeyword(value) or hasattr(builtins, value) or value in _RESERVED_ENTITIES:
        raise ScaffoldError(
            "invalid_name",
            f"entity {_clip(value)} collides with a reserved name; pass an explicit entity",
        )
    return value


def derive_entity(name: str) -> str:
    """Derive the PascalCase entity class name from a module name.

    A trailing ``ies`` becomes ``y``; names ending in ``ss``, ``us`` or ``is`` stay whole;
    otherwise one trailing ``s`` is dropped. Known misfits (``series`` -> ``Sery``) are fixed
    by passing an explicit entity.
    """
    if name.endswith("ies") and len(name) > 3:
        base = name[:-3] + "y"
    elif name.endswith(("ss", "us", "is")):
        base = name
    elif name.endswith("s"):
        base = name[:-1] or name
    else:
        base = name
    return "".join(part[:1].upper() + part[1:] for part in base.split("_") if part)


def plan_module(
    name: str, *, entity: str | None = None, package: str | None = None
) -> list[PlannedFile]:
    """Plan the files of a hexagonal module; nothing is written.

    Args:
        name: module name, ``[a-z][a-z0-9_]{0,39}``, not a keyword nor a stdlib module.
        entity: entity class name; derived from ``name`` when omitted.
        package: package directory name; defaults to ``name``.

    Returns:
        The planned files sorted by POSIX path.

    Raises:
        ScaffoldError: with code ``invalid_name`` when an argument is rejected.
    """
    module_name = _check_identifier(name, "name")
    package_name = module_name if package is None else _check_identifier(package, "package")
    if package_name in _RESERVED_PACKAGES:
        raise ScaffoldError("invalid_name", f"package {_clip(package_name)} is reserved")
    entity_name = _check_entity(derive_entity(module_name) if entity is None else entity)
    files = [
        PlannedFile(
            path=PurePosixPathFactory(
                render(path, package=package_name, name=module_name, entity=entity_name)
            ),
            content=render(content, package=package_name, name=module_name, entity=entity_name),
        )
        for path, content in FILE_TEMPLATES
    ]
    files.sort(key=lambda planned: planned.path.as_posix())
    logger.debug("planned %d files", len(files))
    return files


from pathlib import PurePosixPath as PurePosixPathFactory  # noqa: E402
