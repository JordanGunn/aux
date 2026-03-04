"""Find command - read-only tree-sitter structural search (AST-aware)."""

from __future__ import annotations

import argparse
import json

from aux.kernels.query import AstMatch, QueryResult, query_kernel
from aux.output import format_output
from aux.plans import FindPlan, parse_plan


CAPABILITY: dict = {
    "name": "find",
    "description": "Read-only tree-sitter AST structural search: match code nodes by query pattern.",
    "category": "read",
    "intent_signals": [
        "find all function definitions using AST",
        "structural code search with tree-sitter query",
        "locate class definitions or imports by syntax",
    ],
    "requires": ["query"],
    "optional_deps": ["tree-sitter"],
    "compose_with": ["usages", "search"],
    "mutates": False,
    "schema_cmd": "aux find --schema",
}


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the find subcommand."""
    parser = subparsers.add_parser(
        "find",
        help="Read-only tree-sitter structural search (AST-aware)",
        description="""
Read-only structural search using tree-sitter AST queries.
Returns all nodes matching the given query pattern across files.

Simple usage:
  aux find "(function_definition name: (identifier) @name)" \\
      --root /path --glob "*.py"

Plan usage:
  aux find --plan '<json>'

Grammar introspection:
  aux find --languages
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Simple mode: query string positional
    parser.add_argument(
        "query",
        nargs="?",
        help="Tree-sitter query string (simple mode)",
    )
    parser.add_argument(
        "--root",
        type=str,
        help="Root directory for glob targeting",
    )
    parser.add_argument(
        "--glob",
        action="append",
        dest="globs",
        default=[],
        metavar="PATTERN",
        help="Include files matching glob (repeatable; requires --root)",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        dest="excludes",
        default=[],
        help="Exclude files matching glob (repeatable)",
    )
    parser.add_argument(
        "--file",
        action="append",
        dest="files",
        default=[],
        metavar="PATH",
        help="Explicit file to search (repeatable)",
    )
    parser.add_argument(
        "--language",
        type=str,
        help="Language override (auto-detected from extension if omitted)",
    )
    parser.add_argument(
        "--max-matches",
        type=int,
        metavar="N",
        help="Maximum total matches to return",
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

    # Grammar introspection
    parser.add_argument(
        "--languages",
        action="store_true",
        help="List available/unavailable grammar packages and exit",
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

    # Language introspection mode
    if args.languages:
        print(json.dumps(_list_languages(), indent=2))
        return 0

    # Build plan
    if args.plan:
        try:
            plan = parse_plan(args.plan, FindPlan)
        except ValueError as e:
            print(format_output({"error": str(e)}))
            return 1
    else:
        # Simple mode
        if not args.query:
            print(format_output({"error": "Query string required (positional) or use --plan"}))
            return 1
        if not args.files and not args.root:
            print(format_output({"error": "--file or --root required"}))
            return 1

        try:
            plan = FindPlan(
                query=args.query,
                files=args.files,
                root=args.root,
                globs=args.globs,
                excludes=args.excludes,
                language=args.language,
                max_matches=args.max_matches,
            )
        except Exception as e:
            print(format_output({"error": str(e)}))
            return 1

    # Resolve files
    target_files = _resolve_files(plan)

    # Execute kernel
    result = query_kernel(
        target_files,
        plan.query,
        language=plan.language,
        max_matches=plan.max_matches,
    )

    print(format_output(_format_result(result)))
    return 0 if not result.errors else 1


def _resolve_files(plan: FindPlan) -> list:
    """Resolve file list from plan."""
    from pathlib import Path

    if plan.files:
        return [Path(f).expanduser().resolve() for f in plan.files]

    from aux.kernels.find import find_kernel

    root = Path(plan.root).expanduser().resolve()  # type: ignore[arg-type]
    find_result = find_kernel(
        root=root,
        globs=plan.globs or None,
        excludes=plan.excludes or None,
    )
    return [root / entry.path for entry in find_result.entries]


def _format_result(result: QueryResult) -> dict:
    """Format query result as output dict."""
    output: dict = {
        "files_searched": result.files_searched,
        "files_with_matches": result.files_with_matches,
        "total_matches": result.total_matches,
        "matches": [_format_match(m) for m in result.matches],
    }
    if result.errors:
        output["errors"] = result.errors
    return output


def _format_match(match: AstMatch) -> dict:
    """Format a single AstMatch as an output dict."""
    return {
        "file": match.file,
        "language": match.language,
        "captures": [
            {
                "name": c.name,
                "text": c.text,
                "line": c.line,
                "col": c.col,
            }
            for c in match.captures
        ],
    }


def _list_languages() -> dict:
    """List available and unavailable grammar packages."""
    import importlib

    from aux.util.treesitter import GRAMMAR_MAP

    available = []
    unavailable = []

    for lang_name, pkg_name in sorted(GRAMMAR_MAP.items()):
        try:
            importlib.import_module(pkg_name)
            available.append(lang_name)
        except ImportError:
            unavailable.append(lang_name)

    return {
        "available": available,
        "unavailable": unavailable,
        "install": "pip install 'aux-skills[query]'",
    }
