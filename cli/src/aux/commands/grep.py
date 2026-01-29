"""Grep command - CLI wrapper for grep kernel."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from aux.kernels.grep import grep_kernel
from aux.output import format_output
from aux.plans import GrepPlan, Pattern, parse_plan, get_schema


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the grep subcommand."""
    parser = subparsers.add_parser(
        "grep",
        help="Search patterns in files using ripgrep",
        description="""
Search for patterns across files using ripgrep with concurrent execution.

Simple usage:
  aux grep "pattern" --root /path [--glob GLOB] [--exclude GLOB]

Plan usage:
  aux grep --plan '<json>'
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Simple mode arguments
    parser.add_argument(
        "pattern",
        nargs="?",
        help="Pattern to search for (simple mode)",
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
        "--case",
        choices=["smart", "sensitive", "insensitive"],
        default="smart",
        help="Case sensitivity (default: smart)",
    )
    parser.add_argument(
        "--context",
        type=int,
        default=0,
        help="Lines of context around matches",
    )
    parser.add_argument(
        "--fixed",
        action="store_true",
        help="Treat pattern as literal string",
    )
    parser.add_argument(
        "--hidden",
        action="store_true",
        help="Search hidden files",
    )
    parser.add_argument(
        "--no-ignore",
        action="store_true",
        help="Don't respect gitignore",
    )
    parser.add_argument(
        "--max-matches",
        type=int,
        help="Maximum matches to return",
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

    parser.set_defaults(func=cmd_grep)


def cmd_grep(args: argparse.Namespace) -> int:
    """Execute grep command."""
    # Schema mode
    if args.schema:
        from aux.plans.validate import get_schema
        schema = get_schema("grep")
        print(json.dumps(schema, indent=2))
        return 0

    # Build plan from args
    if args.plan:
        try:
            plan = parse_plan(args.plan, GrepPlan)
        except ValueError as e:
            print(format_output({"error": str(e)}))
            return 1
    else:
        # Simple mode - require pattern and root
        if not args.pattern:
            print(format_output({"error": "Pattern required (or use --plan)"}))
            return 1
        if not args.root:
            print(format_output({"error": "--root required"}))
            return 1

        plan = GrepPlan(
            root=args.root,
            patterns=[Pattern(
                kind="fixed" if args.fixed else "regex",
                value=args.pattern,
            )],
            globs=args.globs,
            excludes=args.excludes,
            case=args.case,
            context_lines=args.context,
            hidden=args.hidden,
            no_ignore=args.no_ignore,
            max_matches=args.max_matches,
        )

    # Validate root exists
    root = Path(plan.root).expanduser().resolve()
    if not root.exists():
        print(format_output({"error": f"Root does not exist: {root}"}))
        return 1

    # Execute kernel
    result = grep_kernel(
        patterns=[{"kind": p.kind, "value": p.value} for p in plan.patterns],
        root=root,
        globs=plan.globs,
        excludes=plan.excludes,
        mode=plan.mode,
        case=plan.case,
        context_lines=plan.context_lines,
        hidden=plan.hidden,
        no_ignore=plan.no_ignore,
        max_matches=plan.max_matches,
    )

    # Format output
    output = {
        "summary": {
            "files": result.files_with_matches,
            "matches": result.total_matches,
            "patterns": result.patterns_searched,
        },
        "results": [
            {
                "file": m.path,
                "line": m.line_number,
                "content": m.content,
                "pattern": m.pattern,
            }
            for m in result.matches
        ],
    }

    if result.errors:
        output["errors"] = result.errors

    print(format_output(output))
    return 0 if not result.errors else 1
