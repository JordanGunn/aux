"""CK command — Chidamber & Kemerer class-level metrics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from aux.kernels.ck import CkResult, ck_kernel
from aux.output import format_output
from aux.plans import CkPlan, parse_plan

CAPABILITY: dict = {
    "name": "ck",
    "description": (
        "Chidamber & Kemerer class-level metrics: CBO (coupling), DIT "
        "(inheritance depth), NOC (children), WMC (weighted methods). "
        "Language-agnostic via tree-sitter."
    ),
    "category": "analysis",
    "intent_signals": [
        "measure class-level coupling and cohesion",
        "find highly coupled classes in a codebase",
        "detect deep inheritance hierarchies",
        "identify god classes by weighted method complexity",
        "assess object-oriented design quality per class",
    ],
    "requires": ["root"],
    "optional_deps": [],
    "compose_with": ["ccx", "hotspots", "deps"],
    "mutates": False,
    "schema_cmd": "aux ck --schema",
}


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "ck",
        help="Chidamber & Kemerer class metrics (CBO, DIT, NOC, WMC)",
        description="""\
Compute Chidamber & Kemerer (1994) class-level metrics across a codebase:

  CBO   Coupling Between Object Classes — other classes referenced
  DIT   Depth of Inheritance Tree — levels above this class
  NOC   Number of Children — direct subclasses
  WMC   Weighted Methods per Class — sum of method CCX

Supported: python, javascript, typescript, go, rust, java.

Simple usage:
  aux ck --root /path
  aux ck --root /path --language python

Plan usage:
  aux ck --plan '{"root":"/path"}'

Schema:
  aux ck --schema
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
        help="Cap on classes in output",
    )
    parser.add_argument("--plan", type=str, help="Full plan as JSON")
    parser.add_argument("--schema", action="store_true", help="Print JSON schema and exit")
    parser.set_defaults(func=cmd_ck)


def cmd_ck(args: argparse.Namespace) -> int:
    if args.schema:
        from aux.plans.validate import get_schema
        print(json.dumps(get_schema("ck"), indent=2))
        return 0

    if args.plan:
        try:
            plan = parse_plan(args.plan, CkPlan)
        except ValueError as e:
            print(format_output({"error": str(e)}))
            return 1
    else:
        if not args.root:
            print(format_output({"error": "--root required"}))
            return 1
        try:
            plan = CkPlan(
                root=args.root,
                languages=args.languages,
                max_results=args.max_results,
            )
        except Exception as e:
            print(format_output({"error": str(e)}))
            return 1

    root = Path(plan.root).expanduser().resolve()
    if not root.exists():
        print(format_output({"error": f"Root does not exist: {root}"}))
        return 1

    result = ck_kernel(
        root=root,
        languages=plan.languages or None,
        globs=plan.globs or None,
        excludes=plan.excludes or None,
        hidden=plan.hidden,
        no_ignore=plan.no_ignore,
        max_results=plan.max_results,
    )
    print(format_output(_format_result(result)))
    return 0 if not result.errors else 1


def _format_result(result: CkResult) -> dict:
    summary: dict = {
        "languages": result.languages,
        "files_searched": result.files_searched,
        "classes_analyzed": result.classes_analyzed,
    }
    if result.truncated:
        summary["truncated"] = True

    classes_out = []
    for cm in result.classes:
        classes_out.append({
            "name": cm.name,
            "file": cm.file,
            "path": cm.path,
            "line": cm.line,
            "end_line": cm.end_line,
            "language": cm.language,
            "kind": cm.kind,
            "cbo": cm.cbo,
            "dit": cm.dit,
            "noc": cm.noc,
            "wmc": cm.wmc,
            "method_count": cm.method_count,
            "superclasses": cm.superclasses,
            "interpretation": cm.interpretation,
        })

    return {
        "summary": summary,
        "classes": classes_out,
        "errors": result.errors,
    }
