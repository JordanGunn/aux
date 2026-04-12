"""Hotspots command - churn-weighted complexity scoring per file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from aux.kernels.hotspots import HotspotsResult, hotspots_kernel
from aux.output import format_output
from aux.plans import HotspotsPlan, parse_plan

CAPABILITY: dict = {
    "name": "hotspots",
    "description": (
        "Growth-weighted complexity hotspots per file: sum_ccx × loc_delta. "
        "Composes ccx (complexity) with git log --numstat (LOC change volume) "
        "and classifies files into Tornhill quadrants. Defaults to the last "
        "14 days — tuned for agentic code generation."
    ),
    "category": "analysis",
    "intent_signals": [
        "find files where complex code is being actively churned",
        "identify the highest-risk refactor targets in a codebase",
        "surface recent agentic rot before it becomes architectural",
        "measure churn-weighted complexity per file",
        "rank files by Tornhill-style hotspot score",
    ],
    "requires": ["root"],
    "optional_deps": ["git"],
    "compose_with": ["ccx", "robert", "deps", "delta"],
    "mutates": False,
    "schema_cmd": "aux hotspots --schema",
}


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the hotspots subcommand."""
    parser = subparsers.add_parser(
        "hotspots",
        help="Churn-weighted complexity hotspots per file (Tornhill-style)",
        description="""
Compute growth-weighted complexity hotspots per file. Composes `ccx`
(Cyclomatic Complexity) with `git log --numstat` (LOC change volume) to
rank files by hotspot score (sum_ccx × max(0, net LOC delta)). Files are
classified into four quadrants based on 75th-percentile cutoffs on both axes.

Quadrants:
  hotspot           High complexity AND high growth — prime refactor target
  stable_complex    High complexity, low growth — legacy, touch with care
  churning_simple   Low complexity, high growth — fast-growing but safe
  calm              Low on both — uninteresting
  insufficient_data Set too small (<8 files) for percentile classification

Default time window is 14 days — tuned for agentic code generation where
architectural damage from file growth accumulates in days, not months.
Override with --since "90 days ago" or --since all for unbounded.

Language coverage inherits from `ccx` (python, javascript, typescript, go,
rust, java). Files in unsupported languages are excluded from the ranking.

Simple usage:
  aux hotspots --root /path
  aux hotspots --root /path --since "30 days ago"
  aux hotspots --root /path --since all --min-commits 5
  aux hotspots --root /path --max-results 20

Plan usage:
  aux hotspots --plan '<json>'

Schema:
  aux hotspots --schema
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--root",
        type=str,
        help="Repository root (required in simple mode). Can be a subdirectory of the git repo.",
    )
    parser.add_argument(
        "--glob",
        action="append",
        dest="globs",
        default=[],
        metavar="PATTERN",
        help="Include glob pattern (repeatable)",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        dest="excludes",
        default=[],
        metavar="PATTERN",
        help="Exclude glob pattern (repeatable)",
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
        "--since",
        type=str,
        default="14 days ago",
        metavar="SPEC",
        help=(
            "Git log window start (default: '14 days ago'). Git-style: "
            "'90 days ago', '2025-01-01', '1 year ago', or 'all' for unbounded."
        ),
    )
    parser.add_argument(
        "--until",
        type=str,
        default=None,
        metavar="SPEC",
        help="Git log window end (default: now)",
    )
    parser.add_argument(
        "--min-commits",
        type=int,
        default=2,
        metavar="N",
        help="Minimum commit count to include a file (default: 2)",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=None,
        metavar="N",
        help="Cap the ranked result list (post-sort)",
    )
    parser.add_argument(
        "--percentile",
        type=float,
        default=0.75,
        metavar="P",
        dest="hotspot_percentile",
        help="Percentile cutoff for quadrant classification (default: 0.75)",
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

    parser.set_defaults(func=cmd_hotspots)


def cmd_hotspots(args: argparse.Namespace) -> int:
    """Execute hotspots command."""
    if args.schema:
        from aux.plans.validate import get_schema
        schema = get_schema("hotspots")
        print(json.dumps(schema, indent=2))
        return 0

    if args.plan:
        try:
            plan = parse_plan(args.plan, HotspotsPlan)
        except ValueError as e:
            print(format_output({"error": str(e)}))
            return 1
    else:
        if not args.root:
            print(format_output({"error": "--root required"}))
            return 1

        try:
            plan = HotspotsPlan(
                root=args.root,
                globs=args.globs,
                excludes=args.excludes,
                hidden=args.hidden,
                no_ignore=args.no_ignore,
                since=args.since,
                until=args.until,
                min_commits=args.min_commits,
                max_results=args.max_results,
                hotspot_percentile=args.hotspot_percentile,
            )
        except Exception as e:
            print(format_output({"error": str(e)}))
            return 1

    root = Path(plan.root).expanduser().resolve()
    if not root.exists():
        print(format_output({"error": f"Root does not exist: {root}"}))
        return 1

    result = hotspots_kernel(
        root=root,
        globs=plan.globs or None,
        excludes=plan.excludes or None,
        hidden=plan.hidden,
        no_ignore=plan.no_ignore,
        since=plan.since,
        until=plan.until,
        min_commits=plan.min_commits,
        max_results=plan.max_results,
        hotspot_percentile=plan.hotspot_percentile,
    )

    print(format_output(_format_result(result)))
    return 0 if not result.errors else 1


def _format_result(result: HotspotsResult) -> dict:
    """Format hotspots result as output dict."""
    summary: dict = {
        "window_since": result.window_since,
        "window_until": result.window_until,
        "window_resolved_start": result.window_resolved_start,
        "window_resolved_end": result.window_resolved_end,
        "total_commits_analyzed": result.total_commits_analyzed,
        "files_analyzed": result.files_analyzed,
        "files_with_complexity": result.files_with_complexity,
        "files_excluded": {
            "unsupported_language": result.files_excluded_unsupported_language,
            "no_functions": result.files_excluded_no_functions,
            "below_min_commits": result.files_excluded_below_min_commits,
            "not_on_disk": result.files_excluded_not_on_disk,
        },
        "languages": result.languages,
        "quadrant_counts": result.quadrant_counts,
        "guidance": result.guidance,
    }
    if result.truncated:
        summary["truncated"] = True

    files_output = []
    for h in result.files:
        files_output.append(
            {
                "file": h.file,
                "path": h.path,
                "language": h.language,
                "sum_ccx": h.sum_ccx,
                "max_ccx": h.max_ccx,
                "loc_delta": h.loc_delta,
                "loc_insertions": h.loc_insertions,
                "loc_deletions": h.loc_deletions,
                "commit_count": h.commit_count,
                "first_seen": h.first_seen,
                "last_seen": h.last_seen,
                "hotspot_score": round(h.hotspot_score, 2),
                "hotspot_score_normalized": round(h.hotspot_score_normalized, 2),
                "quadrant": h.quadrant,
                "interpretation": h.interpretation,
            }
        )

    return {
        "summary": summary,
        "files": files_output,
        "errors": result.errors,
    }
