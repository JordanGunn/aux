"""Robert command - Robert C. Martin package design metrics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from aux.kernels.robert import RobertResult, robert_kernel
from aux.output import format_output
from aux.plans import RobertPlan, parse_plan

CAPABILITY: dict = {
    "name": "robert",
    "description": (
        "Robert C. Martin package design metrics: coupling, abstractness, "
        "distance from main sequence."
    ),
    "category": "analysis",
    "intent_signals": [
        "evaluate package design quality",
        "detect Zone of Pain or Zone of Uselessness packages",
        "measure instability, abstractness, distance from main sequence",
        "assess structural brittleness before a refactor",
    ],
    "requires": ["root", "language"],
    "optional_deps": ["tree-sitter"],
    "compose_with": ["deps", "usages", "find"],
    "mutates": False,
    "schema_cmd": "aux robert --schema",
}


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the robert subcommand."""
    parser = subparsers.add_parser(
        "robert",
        help="Robert C. Martin package design metrics (coupling, abstractness, main sequence)",
        description="""
Compute Robert C. Martin package design metrics for a codebase.

Metrics computed per package:
  Ca  Afferent coupling (packages that import this)
  Ce  Efferent coupling (packages this imports)
  I   Instability = Ce / (Ca + Ce)   [0=stable, 1=unstable]
  Na  Abstract types (interfaces, ABCs, Protocols)
  Nc  Concrete types (structs, classes)
  A   Abstractness = Na / (Na + Nc)  [0=concrete, 1=abstract]
  D'  Distance = |A + I - 1|         [0=ideal, 1=worst]

Zones:
  pain        I < 0.3 AND A < 0.3    Stable-Concrete. Rigid under change.
  uselessness I > 0.7 AND A > 0.7    Unstable-Abstract. Abstract but rarely used.
  warning     D' >= 0.5              Drifting from main sequence.
  clean       D' < 0.2               On or near main sequence.
  ok          everything else

Simple usage:
  aux robert --root /path --language python
  aux robert --root /path --language go

Plan usage:
  aux robert --plan '<json>'

Schema:
  aux robert --schema
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Required in simple mode
    parser.add_argument(
        "--root",
        type=str,
        help="Search root directory (required in simple mode)",
    )
    parser.add_argument(
        "--language",
        type=str,
        help="Language to analyze: 'go' or 'python' (required in simple mode)",
    )

    # Optional filters
    parser.add_argument(
        "--glob",
        action="append",
        dest="globs",
        default=[],
        metavar="PATTERN",
        help="Include files matching glob (repeatable; overrides language defaults)",
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
        help="Maximum packages to include in output",
    )
    parser.add_argument(
        "--include-main",
        action="store_true",
        help="Go only: include 'package main' packages in analysis",
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

    parser.set_defaults(func=cmd_robert)


def cmd_robert(args: argparse.Namespace) -> int:
    """Execute robert command."""
    # Schema mode
    if args.schema:
        from aux.plans.validate import get_schema
        schema = get_schema("robert")
        print(json.dumps(schema, indent=2))
        return 0

    # Build plan
    if args.plan:
        try:
            plan = parse_plan(args.plan, RobertPlan)
        except ValueError as e:
            print(format_output({"error": str(e)}))
            return 1
    else:
        if not args.root:
            print(format_output({"error": "--root required"}))
            return 1
        if not args.language:
            print(format_output({"error": "--language required (go or python)"}))
            return 1

        try:
            plan = RobertPlan(
                root=args.root,
                language=args.language,
                globs=args.globs,
                excludes=args.excludes,
                hidden=args.hidden,
                no_ignore=args.no_ignore,
                max_results=args.max_results,
                include_main=args.include_main,
            )
        except Exception as e:
            print(format_output({"error": str(e)}))
            return 1

    root = Path(plan.root).expanduser().resolve()
    if not root.exists():
        print(format_output({"error": f"Root does not exist: {root}"}))
        return 1

    result = robert_kernel(
        root=root,
        language=plan.language,
        globs=plan.globs or None,
        excludes=plan.excludes or None,
        hidden=plan.hidden,
        no_ignore=plan.no_ignore,
        max_results=plan.max_results,
        include_main=plan.include_main,
    )

    print(format_output(_format_result(result, root)))
    return 0 if not result.errors else 1


def _format_result(result: RobertResult, root: Path) -> dict:
    """Format robert result as output dict."""
    # Compute mean distance (excluding unknowns)
    distances = [pm.distance for pm in result.packages if pm.distance is not None]
    mean_distance: float | None = (sum(distances) / len(distances)) if distances else None

    summary: dict = {
        "language": result.language,
        "packages_analyzed": result.packages_analyzed,
        "files_searched": result.files_searched,
        "zone_counts": result.zone_counts,
        "mean_distance": round(mean_distance, 4) if mean_distance is not None else None,
        "guidance": result.guidance,
    }
    if result.truncated:
        summary["truncated"] = True

    packages_output = []
    for pm in result.packages:
        entry: dict = {
            "package": pm.package,
            "path": pm.path,
            "language": pm.language,
            "files": pm.files,
            "ca": pm.ca,
            "ce": pm.ce,
            "instability": round(pm.instability, 4) if pm.instability is not None else None,
            "na": pm.na,
            "nc": pm.nc,
            "abstractness": round(pm.abstractness, 4) if pm.abstractness is not None else None,
            "distance": round(pm.distance, 4) if pm.distance is not None else None,
            "zone": pm.zone,
            "interpretation": pm.interpretation,
        }
        packages_output.append(entry)

    output: dict = {
        "summary": summary,
        "packages": packages_output,
        "errors": result.errors,
    }

    return output
