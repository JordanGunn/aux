"""Ls command - CLI wrapper for ls kernel."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from aux.kernels.ls import ls_kernel
from aux.output import format_output
from aux.plans import LsPlan, parse_plan


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the ls subcommand."""
    parser = subparsers.add_parser(
        "ls",
        help="List directory contents with metadata",
        description="""
List directory contents with optional metadata.

Simple usage:
  aux ls /path [--depth N] [--sort name|size|time]

Plan usage:
  aux ls --plan '<json>'
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "path",
        nargs="?",
        help="Directory path",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=1,
        help="Recursion depth (default: 1)",
    )
    parser.add_argument(
        "--hidden",
        action="store_true",
        help="Show hidden files",
    )
    parser.add_argument(
        "--size",
        action="store_true",
        default=True,
        help="Show file sizes (default: true)",
    )
    parser.add_argument(
        "--time",
        action="store_true",
        help="Show modification times",
    )
    parser.add_argument(
        "--sort",
        choices=["name", "size", "time"],
        default="name",
        help="Sort order (default: name)",
    )
    parser.add_argument(
        "--max-entries",
        type=int,
        help="Maximum entries to return",
    )

    # Plan mode
    parser.add_argument(
        "--plan",
        type=str,
        help="Full plan as JSON (overrides other options)",
    )
    parser.add_argument(
        "--schema",
        action="store_true",
        help="Print JSON schema for --plan and exit",
    )

    parser.set_defaults(func=cmd_ls)


def cmd_ls(args: argparse.Namespace) -> int:
    """Execute ls command."""
    # Schema mode
    if args.schema:
        from aux.plans.validate import get_schema
        schema = get_schema("ls")
        print(json.dumps(schema, indent=2))
        return 0

    # Build plan from args
    if args.plan:
        try:
            plan = parse_plan(args.plan, LsPlan)
        except ValueError as e:
            print(format_output({"error": str(e)}))
            return 1
    else:
        if not args.path:
            print(format_output({"error": "Path required (or use --plan)"}))
            return 1

        plan = LsPlan(
            path=args.path,
            depth=args.depth,
            show_hidden=args.hidden,
            show_size=args.size,
            show_time=args.time,
            sort_by=args.sort,
            max_entries=args.max_entries,
        )

    # Validate path exists
    path = Path(plan.path).expanduser().resolve()
    if not path.exists():
        print(format_output({"error": f"Path does not exist: {path}"}))
        return 1

    # Execute kernel
    result = ls_kernel(
        path=path,
        depth=plan.depth,
        show_hidden=plan.show_hidden,
        show_size=plan.show_size,
        show_time=plan.show_time,
        sort_by=plan.sort_by,
        max_entries=plan.max_entries,
    )

    # Format output
    output = {
        "summary": {
            "path": result.path,
            "total_entries": result.total_entries,
            "total_size": result.total_size,
        },
        "results": [
            {
                "name": e.name,
                "path": e.path,
                "type": e.type,
                "size": e.size,
                **({"modified": e.modified.isoformat()} if e.modified else {}),
            }
            for e in result.entries
        ],
    }

    if result.errors:
        output["errors"] = result.errors

    print(format_output(output))
    return 0 if not result.errors else 1
