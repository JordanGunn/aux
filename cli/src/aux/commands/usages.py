"""Usages command - symbol cross-reference (definitions + references)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from aux.kernels.usages import UsagesResult, usages_kernel
from aux.output import format_output
from aux.plans import UsagesPlan, parse_plan


CAPABILITY: dict = {
    "name": "usages",
    "description": "Symbol cross-reference: all definitions and all references in one call.",
    "category": "analysis",
    "intent_signals": [
        "find all references to a symbol",
        "check impact before renaming a function or class",
        "locate where a symbol is defined across a codebase",
    ],
    "requires": ["root", "symbol"],
    "optional_deps": ["tree-sitter"],
    "compose_with": ["replace", "rename"],
    "mutates": False,
    "schema_cmd": "aux usages --schema",
}


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the usages subcommand."""
    parser = subparsers.add_parser(
        "usages",
        help="Symbol cross-reference: find all definitions and references in one call",
        description="""
Find all definitions and references of a symbol across a codebase.

Uses ripgrep for exhaustive text matches (language-agnostic), enriched by
tree-sitter AST queries to tag definition entries with symbol_type.
Tree-sitter is optional — without it all matches are tagged "reference".

Simple usage:
  aux usages DataProcessor --root /path --glob "**/*.py"

Plan usage:
  aux usages --plan '<json>'

Schema:
  aux usages --schema
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Simple mode
    parser.add_argument(
        "symbol",
        nargs="?",
        help="Exact symbol name to search (literal string, not regex)",
    )
    parser.add_argument(
        "--root",
        type=str,
        help="Search root directory (required in simple mode)",
    )
    parser.add_argument(
        "--glob",
        action="append",
        dest="globs",
        default=[],
        metavar="PATTERN",
        help="Include files matching glob (repeatable)",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        dest="excludes",
        default=[],
        metavar="PATTERN",
        help="Exclude files matching glob (repeatable)",
    )
    parser.add_argument(
        "--language",
        type=str,
        help="Tree-sitter language override for definition detection",
    )
    parser.add_argument(
        "--no-definitions",
        action="store_true",
        help="Skip AST definition tagging (faster; all matches tagged 'reference')",
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
        metavar="N",
        help="Maximum total results to return",
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

    parser.set_defaults(func=cmd_usages)


def cmd_usages(args: argparse.Namespace) -> int:
    """Execute usages command."""
    # Schema mode
    if args.schema:
        from aux.plans.validate import get_schema
        schema = get_schema("usages")
        print(json.dumps(schema, indent=2))
        return 0

    # Build plan
    if args.plan:
        try:
            plan = parse_plan(args.plan, UsagesPlan)
        except ValueError as e:
            print(format_output({"error": str(e)}))
            return 1
    else:
        if not args.symbol:
            print(format_output({"error": "Symbol required (positional) or use --plan"}))
            return 1
        if not args.root:
            print(format_output({"error": "--root required"}))
            return 1

        try:
            plan = UsagesPlan(
                root=args.root,
                symbol=args.symbol,
                globs=args.globs,
                excludes=args.excludes,
                language=args.language,
                definitions=not args.no_definitions,
                hidden=args.hidden,
                no_ignore=args.no_ignore,
                max_results=args.max_results,
            )
        except Exception as e:
            print(format_output({"error": str(e)}))
            return 1

    root = Path(plan.root).expanduser().resolve()
    if not root.exists():
        print(format_output({"error": f"Root does not exist: {root}"}))
        return 1

    result = usages_kernel(
        root=root,
        symbol=plan.symbol,
        globs=plan.globs or None,
        excludes=plan.excludes or None,
        language=plan.language,
        include_definitions=plan.definitions,
        hidden=plan.hidden,
        no_ignore=plan.no_ignore,
        max_results=plan.max_results,
    )

    print(format_output(_format_result(result)))
    return 0 if not result.errors else 1


def _format_result(result: UsagesResult) -> dict:
    """Format usages result as output dict."""
    all_entries = result.definitions + result.references
    files_seen: set[str] = {e.file for e in all_entries}

    summary: dict = {
        "symbol": result.symbol,
        "definitions": len(result.definitions),
        "references": len(result.references),
        "files": len(files_seen),
        "files_searched": result.files_searched,
    }
    if result.truncated:
        summary["truncated"] = True

    results = []
    for entry in result.definitions:
        item: dict = {
            "kind": "definition",
            "file": entry.file,
            "line": entry.line,
            "content": entry.content,
        }
        if entry.symbol_type is not None:
            item["symbol_type"] = entry.symbol_type
            item["col"] = entry.col
        results.append(item)

    for entry in result.references:
        results.append({
            "kind": "reference",
            "file": entry.file,
            "line": entry.line,
            "content": entry.content,
        })

    output: dict = {
        "summary": summary,
        "results": results,
    }
    if result.errors:
        output["errors"] = result.errors

    return output
