"""Scan command - composite find → grep pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from aux.kernels.find import find_kernel
from aux.kernels.grep import grep_kernel
from aux.output import format_output
from aux.plans import ScanPlan, parse_plan


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the scan subcommand."""
    parser = subparsers.add_parser(
        "scan",
        help="Composite: find files → grep patterns (pipeline)",
        description="""
Two-phase scan: surface discovery (find) followed by content search (grep).

This is more efficient than separate find + grep because:
- File list is passed in-memory (no I/O)
- Single command invocation

Usage:
  aux scan --plan '<json>'

Plan structure:
  {
    "root": "/path",
    "surface": { /* FindPlan */ },
    "search": { /* GrepPlan */ }
  }
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--plan",
        type=str,
        help="Full plan as JSON (required for scan)",
    )
    parser.add_argument(
        "--schema",
        action="store_true",
        help="Print JSON schema for --plan and exit",
    )

    parser.set_defaults(func=cmd_scan)


def cmd_scan(args: argparse.Namespace) -> int:
    """Execute scan command (find → grep pipeline)."""
    # Schema mode
    if args.schema:
        from aux.plans.validate import get_schema
        schema = get_schema("scan")
        print(json.dumps(schema, indent=2))
        return 0

    # Plan is required for scan
    if not args.plan:
        print(format_output({"error": "--plan required for scan command"}))
        return 1

    try:
        plan = parse_plan(args.plan, ScanPlan)
    except ValueError as e:
        print(format_output({"error": str(e)}))
        return 1

    # Validate root exists
    root = Path(plan.root).expanduser().resolve()
    if not root.exists():
        print(format_output({"error": f"Root does not exist: {root}"}))
        return 1

    # Phase 1: Surface discovery (find)
    find_result = find_kernel(
        root=root,
        globs=plan.surface.globs,
        excludes=plan.surface.excludes,
        type_filter=plan.surface.type,
        max_depth=plan.surface.max_depth,
        hidden=plan.surface.hidden,
        no_ignore=plan.surface.no_ignore,
        max_results=plan.surface.max_results,
    )

    if find_result.errors:
        print(format_output({
            "error": "Surface scan failed",
            "errors": find_result.errors,
        }))
        return 1

    if not find_result.entries:
        print(format_output({
            "summary": {
                "surface_files": 0,
                "matches": 0,
                "files_with_matches": 0,
            },
            "results": [],
            "note": "No files found in surface scan",
        }))
        return 0

    # Convert find results to file paths for grep
    file_paths = [root / e.path for e in find_result.entries if e.type == "file"]

    # Phase 2: Content search (grep) - using file list from Phase 1
    grep_result = grep_kernel(
        patterns=[{"kind": p.kind, "value": p.value} for p in plan.search.patterns],
        root=root,
        files=file_paths,  # Pipeline: pass file list directly
        mode=plan.search.mode,
        case=plan.search.case,
        context_lines=plan.search.context_lines,
        hidden=plan.search.hidden,
        no_ignore=plan.search.no_ignore,
        max_matches=plan.search.max_matches,
    )

    # Format combined output
    output = {
        "summary": {
            "surface_files": len(file_paths),
            "matches": grep_result.total_matches,
            "files_with_matches": grep_result.files_with_matches,
            "patterns": grep_result.patterns_searched,
        },
        "results": [
            {
                "file": m.path,
                "line": m.line_number,
                "content": m.content,
                "pattern": m.pattern,
            }
            for m in grep_result.matches
        ],
    }

    errors = find_result.errors + grep_result.errors
    if errors:
        output["errors"] = errors

    print(format_output(output))
    return 0 if not errors else 1
