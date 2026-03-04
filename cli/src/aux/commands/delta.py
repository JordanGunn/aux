"""Delta command - semantic git diff (symbols added/removed since a ref)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from aux.kernels.delta import DeltaResult, delta_kernel
from aux.output import format_output
from aux.plans import DeltaPlan, parse_plan


CAPABILITY: dict = {
    "name": "delta",
    "description": "Semantic git diff: files changed plus symbols added/removed since a ref.",
    "category": "analysis",
    "intent_signals": [
        "see what changed since a git ref or commit",
        "list symbols added or removed between two refs",
        "semantic diff beyond line counts",
    ],
    "requires": ["root"],
    "optional_deps": ["tree-sitter"],
    "compose_with": ["usages", "deps"],
    "mutates": False,
    "schema_cmd": "aux delta --schema",
}


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the delta subcommand."""
    parser = subparsers.add_parser(
        "delta",
        help="Semantic git diff: files changed + symbols added/removed since a ref",
        description="""
Compute semantic changes between two git refs (or vs. working tree).

Pipeline:
  git diff --name-status  → changed file list
  git diff --numstat      → line addition/deletion counts
  tree-sitter (optional)  → symbol-level diff (added/removed/unchanged)

When tree-sitter is unavailable, falls back to stat-only mode automatically.

Simple usage:
  aux delta --root /path                          # vs working tree (HEAD)
  aux delta --root /path --ref-from HEAD~3        # since 3 commits ago
  aux delta --root /path --ref-from v1.0 --ref-to v2.0  # between tags

Plan usage:
  aux delta --plan '<json>'

Schema:
  aux delta --schema
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Simple mode
    parser.add_argument(
        "--root",
        type=str,
        help="Git repo root or subdirectory (required in simple mode)",
    )
    parser.add_argument(
        "--ref-from",
        type=str,
        default="HEAD",
        metavar="REF",
        help="Base ref (default: HEAD)",
    )
    parser.add_argument(
        "--ref-to",
        type=str,
        default=None,
        metavar="REF",
        help="Target ref (default: working tree)",
    )
    parser.add_argument(
        "--glob",
        action="append",
        dest="globs",
        default=[],
        metavar="PATTERN",
        help="Filter changed files by glob (repeatable)",
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
        default=None,
        help="Tree-sitter language override",
    )
    parser.add_argument(
        "--stat-only",
        action="store_true",
        help="Skip symbol analysis, return only file and line counts",
    )
    parser.add_argument(
        "--no-semantic",
        action="store_true",
        help="Disable tree-sitter symbol diff (same as --stat-only)",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=None,
        metavar="N",
        help="Maximum files to analyze",
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

    parser.set_defaults(func=cmd_delta)


def cmd_delta(args: argparse.Namespace) -> int:
    """Execute delta command."""
    # Schema mode
    if args.schema:
        from aux.plans.validate import get_schema
        schema = get_schema("delta")
        print(json.dumps(schema, indent=2))
        return 0

    # Build plan
    if args.plan:
        try:
            plan = parse_plan(args.plan, DeltaPlan)
        except ValueError as e:
            print(format_output({"error": str(e)}))
            return 1
    else:
        if not args.root:
            print(format_output({"error": "--root required"}))
            return 1

        stat_only = args.stat_only or args.no_semantic
        try:
            plan = DeltaPlan(
                root=args.root,
                ref_from=args.ref_from,
                ref_to=args.ref_to,
                globs=args.globs,
                excludes=args.excludes,
                language=args.language,
                semantic=not stat_only,
                stat_only=stat_only,
                max_files=args.max_files,
            )
        except Exception as e:
            print(format_output({"error": str(e)}))
            return 1

    root = Path(plan.root).expanduser().resolve()
    if not root.exists():
        print(format_output({"error": f"Root does not exist: {root}"}))
        return 1

    result = delta_kernel(
        root=root,
        ref_from=plan.ref_from,
        ref_to=plan.ref_to,
        globs=plan.globs or None,
        excludes=plan.excludes or None,
        language=plan.language,
        semantic=plan.semantic,
        stat_only=plan.stat_only,
        max_files=plan.max_files,
    )

    print(format_output(_format_result(result)))
    return 0 if not result.errors else 1


def _format_result(result: DeltaResult) -> dict:
    """Format delta result as output dict."""
    files_output = []
    for fd in result.files:
        entry: dict = {
            "file": fd.file,
            "language": fd.language,
            "status": fd.status,
            "additions": fd.additions,
            "deletions": fd.deletions,
        }
        if fd.symbols is not None:
            entry["symbols"] = {
                "added": [{"name": n, "type": t} for n, t in fd.symbols.added],
                "removed": [{"name": n, "type": t} for n, t in fd.symbols.removed],
                "unchanged": [{"name": n, "type": t} for n, t in fd.symbols.unchanged],
            }
        else:
            entry["symbols"] = None
        files_output.append(entry)

    output: dict = {
        "summary": result.summary,
        "ref_from": result.ref_from,
        "ref_to": result.ref_to,
        "files": files_output,
    }
    if result.truncated:
        output["truncated"] = True
    if result.errors:
        output["errors"] = result.errors

    return output
