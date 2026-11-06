"""Command line interface: ``hex-scaffold new <name>`` and ``hex-scaffold layout``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from hex_scaffold.errors import ScaffoldError
from hex_scaffold.planner import plan_module
from hex_scaffold.tree import render_tree
from hex_scaffold.writer import write_plan

LAYER_RULES = (
    "domain: imports nothing from application or adapters.",
    "application: depends only on the domain and on its own port Protocol, never on adapters.",
    "adapters: implement the ports; they may import the domain and the application.",
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hex-scaffold", description="Generate a hexagonal Python module."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    new = commands.add_parser("new", help="generate a module")
    new.add_argument("name", help="module name, e.g. orders")
    new.add_argument("--root", default=".", help="directory to write into (default: .)")
    new.add_argument("--entity", default=None, help="entity class name (default: derived)")
    new.add_argument("--package", default=None, help="package name (default: the module name)")
    new.add_argument("--dry-run", action="store_true", help="print the file tree only")
    new.add_argument("--force", action="store_true", help="overwrite existing files")
    commands.add_parser("layout", help="print the three layer rules")
    return parser


def _report(error: ScaffoldError) -> int:
    print(f"error: {error.code}: {error}", file=sys.stderr)
    for path in error.paths:
        print(f"  {path}", file=sys.stderr)
    return 1 if error.code == "conflict" else 2


def _run_new(args: argparse.Namespace) -> int:
    try:
        plan = plan_module(args.name, entity=args.entity, package=args.package)
        if args.dry_run:
            print(render_tree(plan))
            return 0
        written = write_plan(plan, Path(args.root), force=args.force)
    except ScaffoldError as error:
        return _report(error)
    except OSError as error:
        print(f"error: io_error: {type(error).__name__}", file=sys.stderr)
        return 2
    print(f"wrote {len(written)} files")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and return the exit code (0 ok, 1 conflict, 2 usage/name/path error)."""
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2
    if args.command == "layout":
        for rule in LAYER_RULES:
            print(rule)
        return 0
    return _run_new(args)


if __name__ == "__main__":
    sys.exit(main())
