"""Diff command - CLI wrapper for diff kernel."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from aux.kernels.diff import diff_kernel
from aux.output import format_output
from aux.plans import DiffPlan, parse_plan


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the diff subcommand."""
    parser = subparsers.add_parser(
        "diff",
        help="Compare files or directories",
        description="""
Compare files or directories and show differences.

Simple usage:
  aux diff /path/a /path/b [--context N]

Plan usage:
  aux diff --plan '<json>'
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "path_a",
        nargs="?",
        help="First path to compare",
    )
    parser.add_argument(
        "path_b",
        nargs="?",
        help="Second path to compare",
    )
    parser.add_argument(
        "--context",
        type=int,
        default=3,
        help="Lines of context (default: 3)",
    )
    parser.add_argument(
        "--ignore-whitespace",
        action="store_true",
        help="Ignore whitespace changes",
    )
    parser.add_argument(
        "--ignore-case",
        action="store_true",
        help="Ignore case differences",
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

    parser.set_defaults(func=cmd_diff)


def cmd_diff(args: argparse.Namespace) -> int:
    """Execute diff command."""
    # Schema mode
    if args.schema:
        from aux.plans.validate import get_schema
        schema = get_schema("diff")
        print(json.dumps(schema, indent=2))
        return 0

    # Build plan from args
    if args.plan:
        try:
            plan = parse_plan(args.plan, DiffPlan)
        except ValueError as e:
            print(format_output({"error": str(e)}))
            return 1
    else:
        if not args.path_a or not args.path_b:
            print(format_output({"error": "Two paths required (or use --plan)"}))
            return 1

        plan = DiffPlan(
            path_a=args.path_a,
            path_b=args.path_b,
            context_lines=args.context,
            ignore_whitespace=args.ignore_whitespace,
            ignore_case=args.ignore_case,
        )

    # Validate paths exist
    path_a = Path(plan.path_a).expanduser().resolve()
    path_b = Path(plan.path_b).expanduser().resolve()

    if not path_a.exists():
        print(format_output({"error": f"Path does not exist: {path_a}"}))
        return 1
    if not path_b.exists():
        print(format_output({"error": f"Path does not exist: {path_b}"}))
        return 1

    # Execute kernel
    result = diff_kernel(
        path_a=path_a,
        path_b=path_b,
        context_lines=plan.context_lines,
        ignore_whitespace=plan.ignore_whitespace,
        ignore_case=plan.ignore_case,
    )

    # Format output
    output = {
        "summary": {
            "files": result.total_files,
            "additions": result.total_additions,
            "deletions": result.total_deletions,
        },
        "results": [
            {
                "path_a": f.path_a,
                "path_b": f.path_b,
                "binary": f.binary,
                "hunks": [
                    {
                        "old_start": h.old_start,
                        "old_count": h.old_count,
                        "new_start": h.new_start,
                        "new_count": h.new_count,
                        "lines": h.lines,
                    }
                    for h in f.hunks
                ],
            }
            for f in result.files
        ],
    }

    if result.errors:
        output["errors"] = result.errors

    print(format_output(output))
    return 0 if not result.errors else 1
