"""Replace command - focused fixed-string identifier rename backed by sed kernel."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from aux.kernels.sed import SedResult, sed_kernel
from aux.output import format_output
from aux.plans import ReplacePlan, parse_plan
from aux.plans.schemas import SedPlan, TextReplacement


CAPABILITY: dict = {
    "name": "replace",
    "description": "Fixed-string text replacement across files; dry-run by default, apply with --apply.",
    "category": "write",
    "intent_signals": [
        "replace a string across a codebase",
        "rename an identifier everywhere in source files",
        "bulk text substitution with dry-run preview",
    ],
    "requires": ["old", "new"],
    "optional_deps": [],
    "compose_with": ["usages", "search"],
    "mutates": True,
    "schema_cmd": "aux replace --schema",
}


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the replace subcommand."""
    parser = subparsers.add_parser(
        "replace",
        help="Replace a string everywhere in a codebase (dry-run by default)",
        description="""
Focused fixed-string replace across files. Simpler interface than sed.

Phase 1 (default — dry-run):
  aux replace <old> <new> --root /path --glob "*.py"

Phase 2 (apply):
  aux replace <old> <new> --root /path --glob "*.py" --apply

Plan usage:
  aux replace --plan '<json>'
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("old", nargs="?", help="Exact string to find")
    parser.add_argument("new", nargs="?", help="Replacement string")
    parser.add_argument(
        "--file",
        action="append",
        dest="files",
        default=[],
        metavar="PATH",
        help="File to process (repeatable)",
    )
    parser.add_argument("--root", type=str, help="Root directory for glob targeting")
    parser.add_argument(
        "--glob",
        action="append",
        dest="globs",
        default=[],
        help="Include files matching glob (repeatable)",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        dest="excludes",
        default=[],
        help="Exclude files matching glob (repeatable)",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Write .bak backup before modifying each file",
    )
    parser.add_argument(
        "--plan",
        type=str,
        help="Full plan as JSON (overrides positional args)",
    )
    parser.add_argument(
        "--schema",
        action="store_true",
        help="Print JSON schema for --plan and exit",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes to disk (default: dry-run only)",
    )

    parser.set_defaults(func=cmd_replace)


def cmd_replace(args: argparse.Namespace) -> int:
    """Execute replace command."""
    if args.schema:
        from aux.plans.validate import get_schema
        print(json.dumps(get_schema("replace"), indent=2))
        return 0

    if args.plan:
        try:
            plan = parse_plan(args.plan, ReplacePlan)
        except ValueError as e:
            print(format_output({"error": str(e)}))
            return 1
    else:
        if not args.old:
            print(format_output({"error": "old string required (positional) or use --plan"}))
            return 1
        if args.new is None:
            print(format_output({"error": "new string required (positional) or use --plan"}))
            return 1
        if not args.files and not args.root:
            print(format_output({"error": "--file or --root required"}))
            return 1
        try:
            plan = ReplacePlan(
                old=args.old,
                new=args.new,
                files=args.files,
                root=args.root,
                globs=args.globs,
                excludes=args.excludes,
                backup=args.backup,
            )
        except Exception as e:
            print(format_output({"error": str(e)}))
            return 1

    if plan.files:
        for f in plan.files:
            p = Path(f).expanduser().resolve()
            if not p.exists():
                print(format_output({"error": f"File does not exist: {p}"}))
                return 1

    if plan.root:
        root = Path(plan.root).expanduser().resolve()
        if not root.exists():
            print(format_output({"error": f"Root does not exist: {root}"}))
            return 1

    sed_plan = _to_sed_plan(plan)
    plan_hash = "sha256:" + hashlib.sha256(
        plan.model_dump_json(exclude_none=False).encode()
    ).hexdigest()[:16]

    result = sed_kernel(sed_plan, apply=args.apply)

    if args.apply:
        output = _format_receipt(result, plan_hash, plan)
    else:
        output = _format_dry_run(result, plan_hash, plan)
    print(format_output(output))
    return 0 if not result.errors else 1


def _to_sed_plan(plan: ReplacePlan) -> SedPlan:
    """Convert a ReplacePlan into a SedPlan for the sed kernel."""
    return SedPlan(
        files=plan.files,
        root=plan.root,
        globs=plan.globs,
        excludes=plan.excludes,
        replacements=[TextReplacement(
            mode="text",
            pattern=plan.old,
            replacement=plan.new,
            kind="fixed",
            case="smart",
        )],
        backup=plan.backup,
        encoding=plan.encoding,
    )


def _format_dry_run(result: SedResult, plan_hash: str, plan: ReplacePlan) -> dict:
    files_with_changes = [fr for fr in result.files if fr.changes]
    files_unchanged = [fr.path for fr in result.files if not fr.changes and not fr.error]

    output: dict = {
        "phase": "dry_run",
        "plan_hash": plan_hash,
        "replace": {"old": plan.old, "new": plan.new},
        "summary": {
            "files_examined": result.total_files,
            "files_with_changes": len(files_with_changes),
            "total_occurrences": result.total_changes,
            "applied": False,
        },
        "diff": [
            {
                "file": fr.path,
                "occurrences": len(fr.changes),
                "changes": [
                    {"line": c.line_number, "original": c.original, "replacement": c.replacement}
                    for c in fr.changes
                ],
            }
            for fr in files_with_changes
        ],
        "files_unchanged": files_unchanged,
    }

    if result.errors:
        output["errors"] = result.errors
    return output


def _format_receipt(result: SedResult, plan_hash: str, plan: ReplacePlan) -> dict:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    files_modified = [fr for fr in result.files if fr.applied]
    files_unchanged = [fr for fr in result.files if not fr.applied and not fr.error]

    output: dict = {
        "phase": "apply",
        "plan_hash": plan_hash,
        "timestamp": timestamp,
        "replace": {"old": plan.old, "new": plan.new},
        "summary": {
            "files_examined": result.total_files,
            "files_modified": len(files_modified),
            "files_unchanged": len(files_unchanged),
            "total_occurrences_replaced": result.total_changes,
            "applied": True,
        },
        "receipt": [
            {
                "file": fr.path,
                "status": "error" if fr.error else ("modified" if fr.applied else "unchanged"),
                "occurrences_replaced": len(fr.changes) if fr.applied else 0,
                "backup": fr.backup_path,
            }
            for fr in result.files
        ],
    }

    if result.errors:
        output["errors"] = result.errors
    return output
