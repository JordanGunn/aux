"""Prune command - tiered dead code candidate audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from aux.kernels.prune import ADVISORY, PruneResult, build_next_steps, prune_kernel
from aux.output import format_output
from aux.plans import PrunePlan, parse_plan


CAPABILITY: dict = {
    "name": "prune",
    "description": "Tiered dead code candidate audit: flag potentially unreferenced symbols and modules.",
    "category": "analysis",
    "intent_signals": [
        "find dead code or unused symbols",
        "audit unreferenced files or functions",
        "identify candidates for deletion before cleanup",
    ],
    "requires": ["root"],
    "optional_deps": [],
    "compose_with": ["usages", "replace"],
    "mutates": False,
    "schema_cmd": "aux prune --schema",
}


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the prune subcommand."""
    parser = subparsers.add_parser(
        "prune",
        help="Tiered dead code candidate audit (advisory — requires human verification)",
        description="""
Audit a codebase for potentially unreferenced symbols or modules.

ADVISORY: Output is static analysis only. Never act on prune results without
running `aux usages` to verify each candidate and reviewing the code.

Simple usage:
  aux prune --root /path --glob "**/*.py"
  aux prune --root /path --glob "**/*.py" --scope files

Plan usage:
  aux prune --plan '<json>'

Schema:
  aux prune --schema
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Simple mode
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
        "--scope",
        action="append",
        dest="scope",
        choices=["files", "symbols"],
        default=[],
        metavar="SCOPE",
        help="Analysis scope: 'symbols' (tree-sitter) or 'files' (text-only); repeatable",
    )
    parser.add_argument(
        "--language",
        type=str,
        help="Tree-sitter language override for symbols scope",
    )
    parser.add_argument(
        "--min-name-length",
        type=int,
        default=4,
        metavar="N",
        help="Skip symbols shorter than N characters (default: 4)",
    )
    parser.add_argument(
        "--max-refs",
        type=int,
        default=0,
        metavar="N",
        help="Flag candidates with <= N external references (default: 0)",
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
        "--max-symbols",
        type=int,
        default=None,
        metavar="N",
        help="Cap on symbols analyzed (performance safety valve)",
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

    parser.set_defaults(func=cmd_prune)


def cmd_prune(args: argparse.Namespace) -> int:
    """Execute prune command."""
    # Schema mode
    if args.schema:
        from aux.plans.validate import get_schema
        schema = get_schema("prune")
        print(json.dumps(schema, indent=2))
        return 0

    # Build plan
    if args.plan:
        try:
            plan = parse_plan(args.plan, PrunePlan)
        except ValueError as e:
            print(format_output({"error": str(e)}))
            return 1
    else:
        if not args.root:
            print(format_output({"error": "--root required"}))
            return 1

        scope = args.scope if args.scope else ["symbols"]

        try:
            plan = PrunePlan(
                root=args.root,
                globs=args.globs,
                excludes=args.excludes,
                scope=scope,
                language=args.language,
                min_name_length=args.min_name_length,
                max_refs=args.max_refs,
                hidden=args.hidden,
                no_ignore=args.no_ignore,
                max_symbols=args.max_symbols,
            )
        except Exception as e:
            print(format_output({"error": str(e)}))
            return 1

    root = Path(plan.root).expanduser().resolve()
    if not root.exists():
        print(format_output({"error": f"Root does not exist: {root}"}))
        return 1

    result = prune_kernel(
        root=root,
        globs=plan.globs or None,
        excludes=plan.excludes or None,
        scope=plan.scope,
        language=plan.language,
        min_name_length=plan.min_name_length,
        max_refs=plan.max_refs,
        hidden=plan.hidden,
        no_ignore=plan.no_ignore,
        max_symbols=plan.max_symbols,
    )

    print(format_output(_format_result(result, root, plan.globs)))
    return 0 if not result.errors else 1


def _format_result(result: PruneResult, root: Path, globs: list[str]) -> dict:
    """Format prune result as output dict. Advisory is the first key."""
    by_conf: dict[str, int] = {"high": 0, "medium": 0, "low": 0}
    for c in result.candidates:
        by_conf[c.confidence] = by_conf.get(c.confidence, 0) + 1

    summary = {
        "scope": result.scope,
        "symbols_analyzed": result.symbols_analyzed,
        "candidates": len(result.candidates),
        "by_confidence": by_conf,
        "files_searched": result.files_searched,
    }
    if result.truncated:
        summary["truncated"] = True

    candidates = [
        {
            "symbol": c.symbol,
            "symbol_type": c.symbol_type,
            "file": c.file,
            "line": c.line,
            "external_refs": c.external_refs,
            "confidence": c.confidence,
            "caveats": c.caveats,
        }
        for c in result.candidates
    ]

    output: dict = {
        "advisory": ADVISORY,
        "summary": summary,
        "candidates": candidates,
        "next_steps": build_next_steps(result.candidates, root, globs),
        "errors": result.errors,
    }

    return output
