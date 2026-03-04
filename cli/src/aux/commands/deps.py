"""Deps command - module dependency graph analysis."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from aux.kernels.deps import DepsResult, deps_kernel
from aux.output import format_output
from aux.plans import DepsPlan, parse_plan


CAPABILITY: dict = {
    "name": "deps",
    "description": "Module dependency graph: import coupling metrics, cycles, and blast radius analysis.",
    "category": "analysis",
    "intent_signals": [
        "analyze module dependencies and coupling",
        "detect import cycles in a codebase",
        "determine blast radius before changing a module",
    ],
    "requires": ["root"],
    "optional_deps": ["tree-sitter"],
    "compose_with": ["usages", "prune"],
    "mutates": False,
    "schema_cmd": "aux deps --schema",
}


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the deps subcommand."""
    parser = subparsers.add_parser(
        "deps",
        help="Module dependency graph: coupling metrics, cycles, blast radius",
        description="""
Compute module dependency topology for a codebase.

Builds an import graph from source files, computes per-file coupling metrics
(afferent Ca, efferent Ce, instability), and detects import cycles via DFS.

Uses tree-sitter AST for import extraction when available; falls back to
language-specific regex. Both produce identical ImportEdge structure.

Simple usage:
  aux deps --root /path --glob "**/*.py"
  aux deps --root /path --glob "**/*.py" --target path/to/module.py

Plan usage:
  aux deps --plan '<json>'

Schema:
  aux deps --schema
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Simple mode
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
        "--target",
        type=str,
        default=None,
        help="Focus on one file: show its imports and who imports it",
    )
    parser.add_argument(
        "--language",
        type=str,
        default=None,
        help="Tree-sitter language override (auto-detected from extension if omitted)",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=None,
        metavar="N",
        help="Transitive depth limit (reserved; not yet enforced)",
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
        default=None,
        metavar="N",
        help="Maximum files to include in output",
    )

    # Plan / schema mode
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

    parser.set_defaults(func=cmd_deps)


def cmd_deps(args: argparse.Namespace) -> int:
    """Execute deps command."""
    # Schema mode
    if args.schema:
        from aux.plans.validate import get_schema
        schema = get_schema("deps")
        print(json.dumps(schema, indent=2))
        return 0

    # Build plan
    if args.plan:
        try:
            plan = parse_plan(args.plan, DepsPlan)
        except ValueError as e:
            print(format_output({"error": str(e)}))
            return 1
    else:
        if not args.root:
            print(format_output({"error": "--root required"}))
            return 1

        try:
            plan = DepsPlan(
                root=args.root,
                globs=args.globs,
                excludes=args.excludes,
                target=args.target,
                language=args.language,
                max_depth=args.max_depth,
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

    result = deps_kernel(
        root=root,
        globs=plan.globs or None,
        excludes=plan.excludes or None,
        target=plan.target,
        language=plan.language,
        max_depth=plan.max_depth,
        hidden=plan.hidden,
        no_ignore=plan.no_ignore,
        max_results=plan.max_results,
    )

    print(format_output(_format_result(result)))
    return 0 if not result.errors else 1


def _format_result(result: DepsResult) -> dict:
    """Format deps result as output dict."""
    files_output = []
    for fd in result.files:
        entry: dict = {
            "file": fd.file,
            "language": fd.language,
            "imports": fd.imports,
            "imported_by": fd.imported_by,
            "efferent": fd.efferent,
            "afferent": fd.afferent,
        }
        if fd.instability is not None:
            entry["instability"] = round(fd.instability, 4)
        files_output.append(entry)

    # Find most-coupled file
    most_coupled: str | None = None
    if result.files:
        top = max(result.files, key=lambda fd: fd.afferent)
        most_coupled = top.file

    summary: dict = {
        "files_analyzed": len(result.files),
        "files_searched": result.files_searched,
        "cycles_detected": len(result.cycles),
        "most_coupled": most_coupled,
    }
    if result.truncated:
        summary["truncated"] = True
    if result.target:
        summary["target"] = result.target

    output: dict = {
        "summary": summary,
        "files": files_output,
        "cycles": result.cycles,
    }
    if result.errors:
        output["errors"] = result.errors

    return output
