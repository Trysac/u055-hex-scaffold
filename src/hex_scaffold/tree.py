"""ASCII tree rendering of a plan."""

from __future__ import annotations

from collections.abc import Sequence

from hex_scaffold.errors import ScaffoldError
from hex_scaffold.models import MAX_PATH_DEPTH, MAX_PLAN_FILES, PlannedFile


class _Node:
    __slots__ = ("children",)

    def __init__(self) -> None:
        self.children: dict[str, _Node] = {}


def _render(node: _Node, prefix: str, lines: list[str]) -> None:
    names = sorted(node.children)
    for index, name in enumerate(names):
        child = node.children[name]
        last = index == len(names) - 1
        connector = "`-- " if last else "|-- "
        label = name + "/" if child.children else name
        lines.append(f"{prefix}{connector}{label}")
        _render(child, prefix + ("    " if last else "|   "), lines)


def render_tree(plan: Sequence[PlannedFile]) -> str:
    """Render the paths of ``plan`` as a sorted ASCII tree without a trailing newline.

    Raises:
        ScaffoldError: ``unsafe_path`` when the plan is too large or a path too deep.
    """
    if len(plan) > MAX_PLAN_FILES:
        raise ScaffoldError("unsafe_path", f"plan has more than {MAX_PLAN_FILES} files")
    root = _Node()
    for entry in plan:
        parts = entry.path.parts
        if len(parts) > MAX_PATH_DEPTH:
            raise ScaffoldError("unsafe_path", "path is too deep")
        node = root
        for part in parts:
            node = node.children.setdefault(part, _Node())
    lines = ["."]
    _render(root, "", lines)
    return "\n".join(lines)
