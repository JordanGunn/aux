"""CCX command - Cyclomatic and Cognitive Complexity metrics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from aux.kernels.ccx import CcxResult, ccx_kernel
from aux.output import format_output
from aux.plans import CcxPlan, parse_plan

CAPABILITY: dict = {
    "name": "ccx",
    "description": (
        "Cyclomatic Complexity (McCabe 1976) and Cognitive Complexity "
        "(Campbell 2018) per function across a codebase. Language-agnostic "
        "via tree-sitter."
    ),
    "category": "analysis",
    "intent_signals": [
        "find the most complex functions in a codebase",
        "detect untestable functions before they accumulate",
        "measure cyclomatic and cognitive complexity per function",
        "establish a complexity baseline for refactor decisions",
        "catch over-complex methods before they become architectural rot",
    ],
    "requires": ["root"],
    "optional_deps": [],
    "compose_with": ["hotspots", "robert", "deps", "delta", "find"],
    "mutates": False,
    "schema_cmd": "aux ccx --schema",
}


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the ccx subcommand."""
    parser = subparsers.add_parser(
        "ccx",
        help="Cyclomatic + Cognitive Complexity per function (McCabe + Campbell)",
        description="""
Compute Cyclomatic Complexity (McCabe 1976) and Cognitive Complexity
(Campbell 2018) per function across a codebase. Language-agnostic via
tree-sitter.

Metrics computed per function:
  CCX  Cyclomatic Complexity = 1 + (decision points)
       — count of linearly independent paths
  CogC Cognitive Complexity (with nesting penalty + boolean sequence collapsing)
       — proxy for the subjective effort of reading the function

Zones (driven by CCX, McCabe's classic thresholds):
  simple       1-10    Low risk. Straightforward to test.
  moderate     11-20   Medium risk. More paths, more test cases.
  complex      21-50   High risk. Refactor candidate.
  untestable   51+     Exhaustive path coverage is impractical.

Supported languages: python, javascript, typescript, go, rust, java
(detected from file extension; bash files are intentionally skipped).

Simple usage:
  aux ccx --root /path
  aux ccx --root /path --languages python --languages go
  aux ccx --root /path --min-ccx 11

Plan usage:
  aux ccx --plan '<json>'

Schema:
  aux ccx --schema
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--root",
        type=str,
        help="Search root directory (required in simple mode)",
    )
    parser.add_argument(
        "--language",
        action="append",
        dest="languages",
        default=[],
        metavar="LANG",
        help="Restrict analysis to one language (repeatable; default: all supported)",
    )
    parser.add_argument(
        "--languages",
        action="append",
        dest="languages",
        default=[],
        metavar="LANG",
        help="Alias for --language (repeatable)",
    )

    parser.add_argument(
        "--glob",
        action="append",
        dest="globs",
        default=[],
        metavar="PATTERN",
        help="Override include glob (repeatable; otherwise derived from languages)",
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
        help="Maximum functions in output (post-sort cap)",
    )
    parser.add_argument(
        "--min-ccx",
        type=int,
        default=1,
        metavar="N",
        help="Filter — only return functions with ccx >= N (default: 1)",
    )

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

    parser.set_defaults(func=cmd_ccx)


def cmd_ccx(args: argparse.Namespace) -> int:
    """Execute ccx command."""
    if args.schema:
        from aux.plans.validate import get_schema
        schema = get_schema("ccx")
        print(json.dumps(schema, indent=2))
        return 0

    if args.plan:
        try:
            plan = parse_plan(args.plan, CcxPlan)
        except ValueError as e:
            print(format_output({"error": str(e)}))
            return 1
    else:
        if not args.root:
            print(format_output({"error": "--root required"}))
            return 1

        try:
            plan = CcxPlan(
                root=args.root,
                languages=args.languages,
                globs=args.globs,
                excludes=args.excludes,
                hidden=args.hidden,
                no_ignore=args.no_ignore,
                max_results=args.max_results,
                min_ccx=args.min_ccx,
            )
        except Exception as e:
            print(format_output({"error": str(e)}))
            return 1

    root = Path(plan.root).expanduser().resolve()
    if not root.exists():
        print(format_output({"error": f"Root does not exist: {root}"}))
        return 1

    result = ccx_kernel(
        root=root,
        languages=plan.languages or None,
        globs=plan.globs or None,
        excludes=plan.excludes or None,
        hidden=plan.hidden,
        no_ignore=plan.no_ignore,
        max_results=plan.max_results,
        min_ccx=plan.min_ccx,
    )

    print(format_output(_format_result(result)))
    return 0 if not result.errors else 1


def _format_result(result: CcxResult) -> dict:
    """Format ccx result as output dict."""
    summary: dict = {
        "languages": result.languages,
        "files_searched": result.files_searched,
        "functions_analyzed": result.functions_analyzed,
        "zone_counts": result.zone_counts,
        "guidance": result.guidance,
    }
    if result.truncated:
        summary["truncated"] = True

    functions_output = []
    for fn in result.functions:
        functions_output.append({
            "name": fn.name,
            "file": fn.file,
            "path": fn.path,
            "line": fn.line,
            "end_line": fn.end_line,
            "language": fn.language,
            "ccx": fn.ccx,
            "cog": fn.cog,
            "zone": fn.zone,
            "interpretation": fn.interpretation,
        })

    files_output = []
    for fm in result.files:
        files_output.append({
            "file": fm.file,
            "path": fm.path,
            "language": fm.language,
            "function_count": fm.function_count,
            "max_ccx": fm.max_ccx,
            "mean_ccx": round(fm.mean_ccx, 4) if fm.mean_ccx is not None else None,
            "sum_ccx": fm.sum_ccx,
            "max_cog": fm.max_cog,
            "mean_cog": round(fm.mean_cog, 4) if fm.mean_cog is not None else None,
            "sum_cog": fm.sum_cog,
            "untestable_count": fm.untestable_count,
        })

    return {
        "summary": summary,
        "functions": functions_output,
        "files": files_output,
        "errors": result.errors,
    }
