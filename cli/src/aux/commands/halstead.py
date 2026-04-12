"""Halstead command — Software Science token metrics per function."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from aux.kernels.halstead import HalsteadResult, halstead_kernel
from aux.output import format_output
from aux.plans import HalsteadPlan, parse_plan

CAPABILITY: dict = {
    "name": "halstead",
    "description": (
        "Halstead Software Science metrics per function: Volume (information "
        "content) and Difficulty (cognitive burden). Language-agnostic via "
        "tree-sitter token classification."
    ),
    "category": "analysis",
    "intent_signals": [
        "measure information content of functions",
        "find functions with too many distinct operators or operands",
        "quantify cognitive burden per function",
        "detect functions that pack too much logic into one body",
        "assess function-level complexity beyond control flow",
    ],
    "requires": ["root"],
    "optional_deps": [],
    "compose_with": ["ccx", "npath", "hotspots"],
    "mutates": False,
    "schema_cmd": "aux halstead --schema",
}


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "halstead",
        help="Halstead Software Science metrics per function (Volume, Difficulty)",
        description="""\
Compute Halstead (1977) Software Science metrics per function:

  Volume      Length * log2(Vocabulary) — information content
  Difficulty  (n1/2) * (N2/n2) — cognitive burden

Raw counts: n1 (unique operators), n2 (unique operands),
N1 (total operators), N2 (total operands).

Supported: python, javascript, typescript, go, rust, java.

Simple usage:
  aux halstead --root /path
  aux halstead --root /path --language python --min-volume 100

Plan usage:
  aux halstead --plan '{"root":"/path"}'

Schema:
  aux halstead --schema
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--root", type=str, help="Search root directory")
    parser.add_argument(
        "--language", action="append", dest="languages", default=[],
        metavar="LANG", help="Restrict to one language (repeatable)",
    )
    parser.add_argument(
        "--max-results", type=int, default=None, metavar="N",
        help="Cap on functions in output",
    )
    parser.add_argument(
        "--min-volume", type=float, default=0, metavar="V",
        help="Filter — only return functions with volume >= V (default: 0)",
    )
    parser.add_argument("--plan", type=str, help="Full plan as JSON")
    parser.add_argument("--schema", action="store_true", help="Print JSON schema and exit")
    parser.set_defaults(func=cmd_halstead)


def cmd_halstead(args: argparse.Namespace) -> int:
    if args.schema:
        from aux.plans.validate import get_schema
        print(json.dumps(get_schema("halstead"), indent=2))
        return 0

    if args.plan:
        try:
            plan = parse_plan(args.plan, HalsteadPlan)
        except ValueError as e:
            print(format_output({"error": str(e)}))
            return 1
    else:
        if not args.root:
            print(format_output({"error": "--root required"}))
            return 1
        try:
            plan = HalsteadPlan(
                root=args.root,
                languages=args.languages,
                max_results=args.max_results,
                min_volume=args.min_volume,
            )
        except Exception as e:
            print(format_output({"error": str(e)}))
            return 1

    root = Path(plan.root).expanduser().resolve()
    if not root.exists():
        print(format_output({"error": f"Root does not exist: {root}"}))
        return 1

    result = halstead_kernel(
        root=root,
        languages=plan.languages or None,
        globs=plan.globs or None,
        excludes=plan.excludes or None,
        hidden=plan.hidden,
        no_ignore=plan.no_ignore,
        max_results=plan.max_results,
        min_volume=plan.min_volume,
    )
    print(format_output(_format_result(result)))
    return 0 if not result.errors else 1


def _format_result(result: HalsteadResult) -> dict:
    summary: dict = {
        "languages": result.languages,
        "files_searched": result.files_searched,
        "functions_analyzed": result.functions_analyzed,
    }
    if result.truncated:
        summary["truncated"] = True

    functions_out = []
    for fn in result.functions:
        functions_out.append({
            "name": fn.name,
            "file": fn.file,
            "path": fn.path,
            "line": fn.line,
            "end_line": fn.end_line,
            "language": fn.language,
            "n1": fn.n1,
            "n2": fn.n2,
            "total_n1": fn.total_n1,
            "total_n2": fn.total_n2,
            "vocabulary": fn.vocabulary,
            "length": fn.length,
            "volume": fn.volume,
            "difficulty": fn.difficulty,
            "effort": fn.effort,
        })

    return {
        "summary": summary,
        "functions": functions_out,
        "errors": result.errors,
    }
