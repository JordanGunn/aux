"""Search command - hierarchical fd → rg [→ tree-sitter] pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from aux.kernels.find import find_kernel
from aux.kernels.grep import grep_kernel
from aux.output import format_output
from aux.plans import SearchPlan, parse_plan


CAPABILITY: dict = {
    "name": "search",
    "description": "Hierarchical fd → rg [→ tree-sitter] pipeline: find files, then grep content, then optionally query AST.",
    "category": "read",
    "intent_signals": [
        "search file contents for a pattern",
        "find code matching a regex across a codebase",
        "three-tier hierarchical search with surface and content filters",
    ],
    "requires": ["root", "surface", "search"],
    "optional_deps": ["tree-sitter"],
    "compose_with": ["find", "usages"],
    "mutates": False,
    "schema_cmd": "aux search --schema",
}


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the search subcommand."""
    parser = subparsers.add_parser(
        "search",
        help="Hierarchical pipeline: find files → grep patterns [→ tree-sitter AST]",
        description="""
Three-tier hierarchical search pipeline:

  Tier 1 (fd)           Surface reduction — enumerate files by name/glob
  Tier 2 (rg)           Content match    — grep patterns across tier-1 files
  Tier 3 (tree-sitter)  Structure match  — AST query across tier-2 files (optional)

Usage:
  aux search --plan '<json>'

Plan structure:
  {
    "root": "/path",
    "surface": { /* FilesPlan — tier 1 */ },
    "search":  { /* GrepPlan  — tier 2 */ },
    "structure": { /* StructurePlan — tier 3, optional */ }
  }
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--plan",
        type=str,
        help="Full plan as JSON (required for search)",
    )
    parser.add_argument(
        "--schema",
        action="store_true",
        help="Print JSON schema for --plan and exit",
    )

    parser.set_defaults(func=cmd_search)


def cmd_search(args: argparse.Namespace) -> int:
    """Execute search command (fd → rg [→ tree-sitter] pipeline)."""
    # Schema mode
    if args.schema:
        from aux.plans.validate import get_schema
        schema = get_schema("search")
        print(json.dumps(schema, indent=2))
        return 0

    # Plan is required for search
    if not args.plan:
        print(format_output({"error": "--plan required for search command"}))
        return 1

    try:
        plan = parse_plan(args.plan, SearchPlan)
    except ValueError as e:
        print(format_output({"error": str(e)}))
        return 1

    # Validate root exists
    root = Path(plan.root).expanduser().resolve()
    if not root.exists():
        print(format_output({"error": f"Root does not exist: {root}"}))
        return 1

    # Tier 1: Surface discovery (fd)
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
            "error": "Surface discovery failed",
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
            "note": "No files found in surface discovery",
        }))
        return 0

    # Convert find results to file paths for tier 2
    file_paths = [root / e.path for e in find_result.entries if e.type == "file"]

    # Tier 2: Content search (rg) — pass file list from tier 1
    grep_result = grep_kernel(
        patterns=[{"kind": p.kind, "value": p.value} for p in plan.search.patterns],
        root=root,
        files=file_paths,
        mode=plan.search.mode,
        case=plan.search.case,
        context_lines=plan.search.context_lines,
        hidden=plan.search.hidden,
        no_ignore=plan.search.no_ignore,
        max_matches=plan.search.max_matches,
    )

    # Tier 3 (optional): AST structural match (tree-sitter)
    if plan.structure is not None:
        return _run_tier3(plan, file_paths, grep_result)

    # Two-tier output
    errors = find_result.errors + grep_result.errors

    if plan.result_mode == "files":
        from collections import defaultdict
        file_counts: dict[str, int] = defaultdict(int)
        for m in grep_result.matches:
            file_counts[m.path] += 1
        summary: dict = {
            "surface_files": len(file_paths),
            "files_with_matches": grep_result.files_with_matches,
            "matches": grep_result.total_matches,
            "patterns": grep_result.patterns_searched,
        }
        if grep_result.truncated:
            summary["truncated"] = True
        output: dict = {
            "summary": summary,
            "results": [
                {"file": path, "matches": count}
                for path, count in sorted(file_counts.items(), key=lambda x: x[1], reverse=True)
            ],
        }
    else:
        summary = {
            "surface_files": len(file_paths),
            "matches": grep_result.total_matches,
            "files_with_matches": grep_result.files_with_matches,
            "patterns": grep_result.patterns_searched,
        }
        if grep_result.truncated:
            summary["truncated"] = True
        output = {
            "summary": summary,
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

    if errors:
        output["errors"] = errors

    print(format_output(output))
    return 0 if not errors else 1


def _run_tier3(plan: SearchPlan, surface_files: list[Path], grep_result: object) -> int:
    """Execute tier-3 tree-sitter query over tier-2 matched files."""
    from aux.kernels.query import query_kernel

    assert plan.structure is not None

    # Build the tier-2 file set (files that had content matches)
    matched_paths: set[str] = {m.path for m in grep_result.matches}  # type: ignore[attr-defined]
    content_files = [p for p in surface_files if str(p) in matched_paths]

    if not content_files:
        output = {
            "summary": {
                "tiers": ["fd", "rg", "tree-sitter"],
                "surface_files": len(surface_files),
                "content_files": 0,
                "matches": 0,
                "files_with_matches": 0,
            },
            "results": [],
            "note": "No files passed tier-2 content filter",
        }
        print(format_output(output))
        return 0

    query_result = query_kernel(
        files=content_files,
        query_str=plan.structure.query,
        language=plan.structure.language,
        max_matches=plan.structure.max_matches,
    )

    # Flatten captures into result entries
    results = []
    for match in query_result.matches:
        for cap in match.captures:
            results.append({
                "file": match.file,
                "language": match.language,
                "line": cap.line,
                "col": cap.col,
                "capture": cap.name,
                "text": cap.text,
            })

    errors = query_result.errors
    output = {
        "summary": {
            "tiers": ["fd", "rg", "tree-sitter"],
            "surface_files": len(surface_files),
            "content_files": len(content_files),
            "matches": query_result.total_matches,
            "files_with_matches": query_result.files_with_matches,
        },
        "results": results,
    }

    if errors:
        output["errors"] = errors

    print(format_output(output))
    return 0 if not errors else 1
