"""Find command - CLI wrapper for find kernel."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from aux.kernels.find import find_kernel
from aux.output import format_output
from aux.plans import FindPlan, parse_plan


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the find subcommand."""
    parser = subparsers.add_parser(
        "find",
        help="Locate files by name/glob using fd",
        description="""
Find files matching criteria using fd.

Simple usage:
  aux find --root /path [--glob GLOB] [--type file|directory]

Plan usage:
  aux find --plan '<json>'
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--root",
        type=str,
        help="Search root directory (required)",
    )
    parser.add_argument(
        "--glob",
        action="append",
        dest="globs",
        default=[],
        help="Include files matching glob (repeatable)",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        dest="excludes",
        default=[],
        help="Exclude files matching glob (repeatable)",
    )
    parser.add_argument(
        "--type",
        choices=["file", "directory", "any"],
        default="file",
        help="Entry type filter (default: file)",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        help="Maximum search depth",
    )
    parser.add_argument(
        "--hidden",
        action="store_true",
        help="Include hidden files",
    )
    parser.add_argument(
        "--no-ignore",
        action="store_true",
        help="Don't respect gitignore",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        help="Maximum results to return",
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

    parser.set_defaults(func=cmd_find)


def cmd_find(args: argparse.Namespace) -> int:
    """Execute find command."""
    # Schema mode
    if args.schema:
        from aux.plans.validate import get_schema
        schema = get_schema("find")
        print(json.dumps(schema, indent=2))
        return 0

    # Build plan from args
    if args.plan:
        try:
            plan = parse_plan(args.plan, FindPlan)
        except ValueError as e:
            print(format_output({"error": str(e)}))
            return 1
    else:
        if not args.root:
            print(format_output({"error": "--root required"}))
            return 1

        plan = FindPlan(
            root=args.root,
            globs=args.globs,
            excludes=args.excludes,
            type=args.type,
            max_depth=args.max_depth,
            hidden=args.hidden,
            no_ignore=args.no_ignore,
            max_results=args.max_results,
        )

    # Validate root exists
    root = Path(plan.root).expanduser().resolve()
    if not root.exists():
        print(format_output({"error": f"Root does not exist: {root}"}))
        return 1

    # Execute kernel
    result = find_kernel(
        root=root,
        globs=plan.globs,
        excludes=plan.excludes,
        type_filter=plan.type,
        max_depth=plan.max_depth,
        hidden=plan.hidden,
        no_ignore=plan.no_ignore,
        max_results=plan.max_results,
    )

    # Format output
    output = {
        "summary": {
            "total": result.total_found,
            "returned": len(result.entries),
        },
        "results": [
            {"path": e.path, "type": e.type}
            for e in result.entries
        ],
    }

    if result.errors:
        output["errors"] = result.errors

    print(format_output(output))
    return 0 if not result.errors else 1
