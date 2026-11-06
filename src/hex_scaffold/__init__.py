"""Generate byte-stable hexagonal (ports and adapters) Python modules."""

from __future__ import annotations

import logging

from hex_scaffold.errors import ErrorCode, ScaffoldError
from hex_scaffold.models import PlannedFile
from hex_scaffold.planner import plan_module
from hex_scaffold.tree import render_tree
from hex_scaffold.writer import write_plan

__all__ = [
    "ErrorCode",
    "PlannedFile",
    "ScaffoldError",
    "__version__",
    "plan_module",
    "render_tree",
    "write_plan",
]

__version__ = "0.1.0"

logging.getLogger(__name__).addHandler(logging.NullHandler())
