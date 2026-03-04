"""Rename command — filesystem move/rename with dry-run gate."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from aux.kernels.mv import MvResult, mv_kernel
from aux.output import format_output
from aux.plans import RenamePlan, parse_plan
from aux.plans.schemas import MovePair


CAPABILITY: dict = {
    "name": "rename",
    "description": "Move or rename files and directories; dry-run by default, apply with --apply.",
    "category": "write",
    "intent_signals": [
        "rename a file or directory",
        "move files to a new location",
        "batch rename files matching a pattern",
    ],
    "requires": ["moves"],
    "optional_deps": [],
    "compose_with": ["usages", "replace"],
    "mutates": True,
    "schema_cmd": "aux rename --schema",
}


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the rename subcommand."""
    parser = subparsers.add_parser(
        "rename",
        help="Move/rename files or directories (dry-run by default)",
        description="""
Move or rename files and directories. Dry-run by default.

Phase 1 (default — dry-run):
  aux rename <src> <dst>

Phase 2 (apply):
  aux rename <src> <dst> --apply

Plan usage (batch):
  aux rename --plan '{"moves":[{"src":"...","dst":"..."}]}'
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("src", nargs="?", help="Source path")
    parser.add_argument("dst", nargs="?", help="Destination path")
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Copy src to <src>.bak before moving",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwriting existing destination",
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

    parser.set_defaults(func=cmd_rename)


def cmd_rename(args: argparse.Namespace) -> int:
    """Execute rename command."""
    if args.schema:
        from aux.plans.validate import get_schema
        print(json.dumps(get_schema("rename"), indent=2))
        return 0

    if args.plan:
        try:
            plan = parse_plan(args.plan, RenamePlan)
        except ValueError as e:
            print(format_output({"error": str(e)}))
            return 1
    else:
        if not args.src:
            print(format_output({"error": "src required (positional) or use --plan"}))
            return 1
        if not args.dst:
            print(format_output({"error": "dst required (positional) or use --plan"}))
            return 1
        try:
            plan = RenamePlan(
                moves=[MovePair(src=args.src, dst=args.dst)],
                backup=args.backup,
                overwrite=args.overwrite,
            )
        except Exception as e:
            print(format_output({"error": str(e)}))
            return 1

    if plan.moves is not None:
        move_pairs = [
            (Path(m.src).expanduser().resolve(), Path(m.dst).expanduser().resolve())
            for m in plan.moves
        ]
    else:
        move_pairs = _discover_moves(plan)
        if not move_pairs:
            print(format_output({"error": "Discovery mode produced no qualifying renames — no rule matched any filename in scope"}))
            return 1

    plan_hash = "sha256:" + hashlib.sha256(
        plan.model_dump_json(exclude_none=False).encode()
    ).hexdigest()[:16]

    result = mv_kernel(
        move_pairs,
        apply=args.apply,
        backup=plan.backup,
        overwrite=plan.overwrite,
    )

    if args.apply:
        output = _format_receipt(result, plan_hash)
    else:
        output = _format_dry_run(result, plan_hash)

    print(format_output(output))
    return 0 if not result.errors else 1


def _format_dry_run(result: MvResult, plan_hash: str) -> dict:
    conflicts = sum(1 for r in result.moves if r.conflict)
    errors = sum(1 for r in result.moves if r.error and not r.conflict)

    output: dict = {
        "phase": "dry_run",
        "plan_hash": plan_hash,
        "summary": {
            "total_moves": result.total_moves,
            "conflicts": conflicts,
            "errors": errors,
        },
        "preview": [
            {
                "src": r.src,
                "dst": r.dst,
                "status": "conflict" if r.conflict else ("error" if r.error else "ok"),
            }
            for r in result.moves
        ],
    }

    if result.errors:
        output["errors"] = result.errors

    return output


def _discover_moves(plan: "RenamePlan") -> list[tuple[Path, Path]]:
    """Discover files under plan.root and apply rules to generate move pairs.

    fd's --glob flag matches against filenames only, not full paths. Globs that
    contain "/" are treated as path-prefix filters applied via fnmatch on the
    relative entry path after discovery. Globs without "/" are passed to fd as
    filename patterns.
    """
    import fnmatch
    import re

    from aux.kernels.find import find_kernel

    root = Path(plan.root).expanduser().resolve()  # type: ignore[arg-type]

    # Separate path-scoped globs ("pipeline/**") from filename globs ("*.py")
    path_globs: list[str] = []
    name_globs: list[str] = []
    for g in (plan.globs or []):
        (path_globs if "/" in g else name_globs).append(g)

    result = find_kernel(
        root=root,
        globs=name_globs,
        excludes=plan.excludes or [],
        type_filter="file",
    )

    pairs: list[tuple[Path, Path]] = []
    for entry in result.entries:
        # Post-filter by path globs (fnmatch treats / as ordinary char)
        if path_globs and not any(fnmatch.fnmatch(entry.path, g) for g in path_globs):
            continue

        src = root / entry.path
        name = src.name
        new_name = name
        for rule in plan.rules:  # type: ignore[union-attr]
            if rule.regex:
                new_name = re.sub(rule.find, rule.replace, new_name)
            else:
                new_name = new_name.replace(rule.find, rule.replace)
        if new_name != name:
            pairs.append((src, src.parent / new_name))
    return pairs


def _format_receipt(result: MvResult, plan_hash: str) -> dict:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    skipped = sum(1 for r in result.moves if not r.applied and not r.error)

    output: dict = {
        "phase": "apply",
        "plan_hash": plan_hash,
        "timestamp": timestamp,
        "summary": {
            "total_moves": result.total_moves,
            "applied": result.total_applied,
            "skipped": skipped,
            "errors": len(result.errors),
        },
        "receipt": [
            {
                "src": r.src,
                "dst": r.dst,
                "status": (
                    "moved" if r.applied
                    else "conflict" if r.conflict
                    else "error" if r.error
                    else "skipped"
                ),
                "backup": r.backup_path,
            }
            for r in result.moves
        ],
    }

    if result.errors:
        output["errors"] = result.errors

    return output
