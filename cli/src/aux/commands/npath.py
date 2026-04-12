"""NPATH command — acyclic execution path complexity per function."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from aux.kernels.npath import NpathResult, npath_kernel
from aux.output import format_output
from aux.plans import NpathPlan, parse_plan

CAPABILITY: dict = {
    "name": "npath",
    "description": (
        "NPATH acyclic execution path count per function (Nejmeh 1988). "
        "Multiplicative — catches combinatorial explosion that CCX "
        "underreports. Language-agnostic via tree-sitter."
    ),
    "category": "analysis",
    "intent_signals": [
        "find functions with combinatorial path explosion",
        "detect flat-but-wide functions that CCX underreports",
        "measure acyclic execution paths per function",
        "identify functions where exhaustive testing is impractical",
        "compare NPATH vs CCX to find deceptively complex functions",
    ],
    "requires": ["root"],
    "optional_deps": [],
    "compose_with": ["ccx", "halstead", "hotspots"],
    "mutates": False,
    "schema_cmd": "aux npath --schema",
}


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "npath",
        help="NPATH acyclic execution path count per function (Nejmeh 1988)",
        description="""\
Compute NPATH (Nejmeh 1988) acyclic execution path count per function.

Unlike McCabe's CCX (additive: 1 + branches), NPATH is multiplicative:
sequential branches multiply path counts. This catches combinatorial
explosion that CCX underreports in flat-but-wide functions.

Example: 10 sequential ifs → CCX = 11, NPATH = 1024.

Supported: python, javascript, typescript, go, rust, java.

Simple usage:
  aux npath --root /path
  aux npath --root /path --language python --min-npath 100

Plan usage:
  aux npath --plan '{"root":"/path"}'

Schema:
  aux npath --schema
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
        "--min-npath", type=int, default=1, metavar="N",
        help="Filter — only return functions with npath >= N (default: 1)",
    )
    parser.add_argument("--plan", type=str, help="Full plan as JSON")
    parser.add_argument("--schema", action="store_true", help="Print JSON schema and exit")
    parser.set_defaults(func=cmd_npath)


def cmd_npath(args: argparse.Namespace) -> int:
    if args.schema:
        from aux.plans.validate import get_schema
        print(json.dumps(get_schema("npath"), indent=2))
        return 0

    if args.plan:
        try:
            plan = parse_plan(args.plan, NpathPlan)
        except ValueError as e:
            print(format_output({"error": str(e)}))
            return 1
    else:
        if not args.root:
            print(format_output({"error": "--root required"}))
            return 1
        try:
            plan = NpathPlan(
                root=args.root,
                languages=args.languages,
                max_results=args.max_results,
                min_npath=args.min_npath,
            )
        except Exception as e:
            print(format_output({"error": str(e)}))
            return 1

    root = Path(plan.root).expanduser().resolve()
    if not root.exists():
        print(format_output({"error": f"Root does not exist: {root}"}))
        return 1

    result = npath_kernel(
        root=root,
        languages=plan.languages or None,
        globs=plan.globs or None,
        excludes=plan.excludes or None,
        hidden=plan.hidden,
        no_ignore=plan.no_ignore,
        max_results=plan.max_results,
        min_npath=plan.min_npath,
    )
    print(format_output(_format_result(result)))
    return 0 if not result.errors else 1


def _format_result(result: NpathResult) -> dict:
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
            "npath": fn.npath,
        })

    return {
        "summary": summary,
        "functions": functions_out,
        "errors": result.errors,
    }
