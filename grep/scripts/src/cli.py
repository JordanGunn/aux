#!/usr/bin/env python3
"""
aux/grep CLI - Agent-assisted text search (deterministic ripgrep wrapper)

All execution is deterministic. The agent selects parameters; this script executes.
"""

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


def _get_tool_versions() -> dict:
    """Get tool versions for reproducibility metadata."""
    versions = {"python": platform.python_version()}
    try:
        r = subprocess.run(["rg", "--version"], capture_output=True, text=True, check=False)
        if r.returncode == 0:
            first_line = r.stdout.strip().split("\n")[0]
            versions["rg"] = first_line
    except OSError:
        versions["rg"] = "not found"
    return versions


def _compute_query_id(param_block: dict) -> str:
    """Compute stable query_id from normalized parameters."""
    keys_for_hash = [
        "root",
        "patterns",
        "mode",
        "globs",
        "excludes",
        "content_patterns",
        "file_filters",
        "case",
        "context",
    ]
    hashable = {k: param_block.get(k) for k in keys_for_hash if k in param_block}
    normalized = json.dumps(hashable, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    h = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"sha256:{h}"


def _emit_jsonl(obj: dict) -> None:
    """Emit a single JSONL record."""
    print(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False))


def _resolve_root(root: str) -> Path:
    """Resolve root path to absolute."""
    p = Path(root)
    return p.resolve()

def _read_plan_from_stdin() -> dict:
    raw = sys.stdin.read()
    if not raw.strip():
        raise ValueError("no plan JSON provided on stdin")
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid JSON on stdin: {e}") from e
    if not isinstance(obj, dict):
        raise ValueError("plan JSON must be an object")
    return obj


def _parse_grep_plan_from_stdin() -> dict:
    """
    Parse grep plan JSON from stdin.

    Supports:
      - grep_plan_v1 (legacy): string patterns + global mode (fixed|regex)
      - grep_plan_v2: per-pattern kind (fixed|regex) and separate file_filters globs
    """
    plan = _read_plan_from_stdin()
    schema = plan.get("schema")
    if schema not in ("grep_plan_v1", "grep_plan_v2"):
        raise ValueError("stdin plan schema must be 'grep_plan_v1' or 'grep_plan_v2'")

    search = plan.get("search")
    if not isinstance(search, dict):
        raise ValueError("stdin plan must contain object field 'search'")

    if schema == "grep_plan_v1":
        required = [
            "root",
            "pattern",
            "glob",
            "exclude",
            "mode",
            "case",
            "context",
            "format",
            "max_lines",
            "max_files",
            "max_matches",
            "parallelism",
            "policy",
        ]
        missing = [k for k in required if k not in search]
        if missing:
            raise ValueError(f"stdin plan missing fields in search: {', '.join(missing)}")

        policy = search.get("policy")
        if not isinstance(policy, dict):
            raise ValueError("stdin plan search.policy must be an object")

        mode = search["mode"]
        if mode not in ("fixed", "regex"):
            raise ValueError("stdin plan search.mode must be 'fixed' or 'regex'")

        patterns = list(search.get("pattern") or [])
        content_patterns = [{"kind": mode, "value": p} for p in patterns]

        return {
            "schema": schema,
            "root": search["root"],
            "content_patterns": content_patterns,
            "file_filters": {
                "include_globs": list(search.get("glob") or []),
                "exclude_globs": list(search.get("exclude") or []),
            },
            "case": search["case"],
            "context": search["context"],
            "format": search["format"],
            "max_lines": search["max_lines"],
            "max_files": search.get("max_files"),
            "max_matches": search.get("max_matches"),
            "parallelism": search["parallelism"],
            "policy": {
                "hidden": bool(policy.get("hidden", False)),
                "follow": bool(policy.get("follow", False)),
                "no_ignore": bool(policy.get("no_ignore", False)),
            },
            "limits": {"max_pattern_length": 512},
        }

    # grep_plan_v2
    required = [
        "root",
        "content_patterns",
        "file_filters",
        "case",
        "context",
        "format",
        "max_lines",
        "max_files",
        "max_matches",
        "parallelism",
        "policy",
        "limits",
    ]
    missing = [k for k in required if k not in search]
    if missing:
        raise ValueError(f"stdin plan missing fields in search: {', '.join(missing)}")

    policy = search.get("policy")
    if not isinstance(policy, dict):
        raise ValueError("stdin plan search.policy must be an object")

    limits = search.get("limits")
    if not isinstance(limits, dict):
        raise ValueError("stdin plan search.limits must be an object")

    max_pat_len = limits.get("max_pattern_length")
    if not isinstance(max_pat_len, int) or max_pat_len <= 0:
        raise ValueError("stdin plan search.limits.max_pattern_length must be a positive integer")

    cps = search.get("content_patterns")
    if not isinstance(cps, list) or not cps:
        raise ValueError("stdin plan search.content_patterns must be a non-empty array")

    content_patterns: list[dict] = []
    for i, it in enumerate(cps):
        if not isinstance(it, dict):
            raise ValueError(f"stdin plan search.content_patterns[{i}] must be an object")
        if "kind" not in it or "value" not in it:
            raise ValueError(f"stdin plan search.content_patterns[{i}] must include 'kind' and 'value'")
        kind = it.get("kind")
        value = it.get("value")
        if kind not in ("fixed", "regex"):
            raise ValueError("stdin plan search.content_patterns[*].kind must be 'fixed' or 'regex'")
        if not isinstance(value, str) or not value:
            raise ValueError("stdin plan search.content_patterns[*].value must be a non-empty string")
        if len(value) > max_pat_len:
            raise ValueError(f"stdin plan search.content_patterns[{i}].value exceeds max length {max_pat_len}")
        content_patterns.append({"kind": kind, "value": value})

    ff = search.get("file_filters")
    if not isinstance(ff, dict):
        raise ValueError("stdin plan search.file_filters must be an object")
    include_globs = ff.get("include_globs")
    exclude_globs = ff.get("exclude_globs")
    if not isinstance(include_globs, list) or not isinstance(exclude_globs, list):
        raise ValueError("stdin plan search.file_filters.include_globs and exclude_globs must be arrays")

    return {
        "schema": schema,
        "root": search["root"],
        "content_patterns": content_patterns,
        "file_filters": {"include_globs": list(include_globs), "exclude_globs": list(exclude_globs)},
        "case": search["case"],
        "context": search["context"],
        "format": search["format"],
        "max_lines": search["max_lines"],
        "max_files": search.get("max_files"),
        "max_matches": search.get("max_matches"),
        "parallelism": search["parallelism"],
        "policy": {
            "hidden": bool(policy.get("hidden", False)),
            "follow": bool(policy.get("follow", False)),
            "no_ignore": bool(policy.get("no_ignore", False)),
        },
        "limits": {"max_pattern_length": max_pat_len},
    }


def _parse_rg_line(line: str) -> dict | None:
    """
    Parse a ripgrep output line into structured fields.

    Supports:
      - match lines:   path:line:content
      - context lines: path-line-content   (rg context output)
    """
    s = line.rstrip("\n")
    if not s:
        return None
    if s == "--":
        return {"kind": "separator"}

    # Find the first `:<digits>:` marker from the left. This avoids ambiguity when the content contains `:`,
    # and it won't get confused by Windows drive letters (`C:\...`) because `:\` is not `:<digits>:`.
    for i, ch in enumerate(s):
        if ch != ":":
            continue
        j = i + 1
        if j >= len(s) or not s[j].isdigit():
            continue
        k = j
        while k < len(s) and s[k].isdigit():
            k += 1
        if k < len(s) and s[k] == ":":
            return {"kind": "match", "path": s[:i], "line": int(s[j:k]), "content": s[k + 1 :]}

    # Same idea for context lines (`path-line-content`), where the content may contain `-`.
    for i, ch in enumerate(s):
        if ch != "-":
            continue
        j = i + 1
        if j >= len(s) or not s[j].isdigit():
            continue
        k = j
        while k < len(s) and s[k].isdigit():
            k += 1
        if k < len(s) and s[k] == "-":
            return {"kind": "context", "path": s[:i], "line": int(s[j:k]), "content": s[k + 1 :]}

    return {"kind": "line", "line": s}


def _build_rg_args(
    root: Path,
    pattern: str,
    globs: list[str],
    excludes: list[str],
    mode: str,
    case: str,
    context: int,
    hidden: bool,
    follow: bool,
    no_ignore: bool,
) -> list[str]:
    """Build ripgrep argument list."""
    args = ["rg", "--line-number", "--with-filename"]

    if mode == "fixed":
        args.append("--fixed-strings")

    if case == "sensitive":
        args.append("--case-sensitive")
    elif case == "insensitive":
        args.append("--ignore-case")
    # smart is rg default

    if context > 0:
        args.extend(["--context", str(context)])

    if hidden:
        args.append("--hidden")

    if follow:
        args.append("--follow")

    if no_ignore:
        args.append("--no-ignore")

    for g in sorted(globs):
        args.extend(["--glob", g])

    for e in sorted(excludes):
        args.extend(["--glob", f"!{e}"])

    args.append("--")
    args.append(pattern)
    # Use "." as search path since we'll run rg with cwd=root
    # This ensures globs are matched relative to root
    args.append(".")

    return args


def _run_single_search(
    pattern: str,
    argv: list[str],
    cwd: Path | None = None,
) -> tuple[str, list[str], int]:
    """Run a single rg search and return (pattern, lines, return_code)."""
    try:
        result = subprocess.run(argv, capture_output=True, text=True, check=False, cwd=cwd)
        lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
        return pattern, lines, result.returncode
    except OSError as e:
        return pattern, [f"error: {e}"], 1


def cmd_run(args: argparse.Namespace) -> int:
    """Execute the grep search."""
    if args.stdin:
        try:
            plan = _parse_grep_plan_from_stdin()
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1

        root = _resolve_root(plan["root"])
        content_patterns: list[dict] = plan["content_patterns"]
        globs: list[str] = sorted(plan["file_filters"]["include_globs"] or [])
        excludes: list[str] = sorted(plan["file_filters"]["exclude_globs"] or [])
        case: str = plan["case"]
        context: int = plan["context"]
        output_format: str = plan["format"]
        max_lines: int = plan["max_lines"]
        max_files: int | None = plan["max_files"]
        max_matches: int | None = plan["max_matches"]
        parallelism: int = plan["parallelism"]
        hidden: bool = plan["policy"]["hidden"]
        follow: bool = plan["policy"]["follow"]
        no_ignore: bool = plan["policy"]["no_ignore"]
        plan_schema: str = plan["schema"]
    else:
        root = _resolve_root(args.root)
        content_patterns = [{"kind": args.mode, "value": p} for p in (args.pattern or [])]
        globs = sorted(args.glob or [])
        excludes = sorted(args.exclude or [])
        case = args.case
        context = args.context
        output_format = args.format
        max_lines = args.max_lines
        max_files = args.max_files
        max_matches = args.max_matches
        parallelism = args.parallelism
        hidden = args.hidden
        follow = args.follow
        no_ignore = args.no_ignore
        plan_schema = "cli_args_v1"

    if not content_patterns:
        print("error: at least one pattern is required", file=sys.stderr)
        return 1

    if not root.exists():
        print(f"error: root directory not found: {root}", file=sys.stderr)
        return 1

    # Build param block for reproducibility
    patterns_sorted = sorted(content_patterns, key=lambda p: (p["kind"], p["value"]))
    argv_by_pattern = []
    for p in patterns_sorted:
        mode = "fixed" if p["kind"] == "fixed" else "regex"
        argv_by_pattern.append(
            {
                "pattern": p,
                "argv": _build_rg_args(
                    root, p["value"], globs, excludes, mode, case, context, hidden, follow, no_ignore
                ),
            }
        )
    mode_summary = None
    if all(p["kind"] == "fixed" for p in patterns_sorted):
        mode_summary = "fixed"
    elif all(p["kind"] == "regex" for p in patterns_sorted):
        mode_summary = "regex"
    param_block = {
        "plan_schema": plan_schema,
        "root": str(root),
        "content_patterns": patterns_sorted,
        "file_filters": {"include_globs": globs, "exclude_globs": excludes},
        "globs": globs,
        "excludes": excludes,
        "case": case,
        "context": context,
        "format": output_format,
        "max_lines": max_lines,
        "max_files": max_files,
        "max_matches": max_matches,
        "parallelism": parallelism,
        "tool_versions": _get_tool_versions(),
        "argv_by_pattern": argv_by_pattern,
        "policy": {
            "hidden": hidden,
            "follow": follow,
            "no_ignore": no_ignore,
        },
    }
    # Legacy fields preserved when representable (v1 semantics).
    if mode_summary:
        param_block["patterns"] = [p["value"] for p in patterns_sorted]
        param_block["mode"] = mode_summary
    param_block["query_id"] = _compute_query_id(param_block)

    # Detect output format
    is_tty = sys.stdout.isatty()
    effective_format = output_format if output_format != "auto" else ("human" if is_tty else "jsonl")

    # Emit param block
    if effective_format == "jsonl":
        _emit_jsonl({"kind": "param_block", "param_block": param_block})
    else:
        print(f"# query_id: {param_block['query_id']}")
        print(f"# root: {root}")
        print(f"# content_patterns: {patterns_sorted}")
        print(f"# globs: {globs}")
        print(f"# excludes: {excludes}")
        print()

    # Run searches in parallel
    all_lines: list[str] = []
    parsed_for_files: list[dict] = []
    argv_map = {f"{d['pattern']['kind']}:{d['pattern']['value']}": d["argv"] for d in argv_by_pattern}

    with ThreadPoolExecutor(max_workers=parallelism) as executor:
        futures = {
            executor.submit(
                _run_single_search,
                p["value"],
                argv_map[f"{p['kind']}:{p['value']}"],
                root,  # Run rg with cwd=root so globs match correctly
            ): p["value"]
            for p in patterns_sorted
        }

        for future in as_completed(futures):
            _, lines, _ = future.result()
            for line in lines:
                all_lines.append(line)
                parsed = _parse_rg_line(line)
                if parsed and parsed.get("path"):
                    parsed_for_files.append(parsed)

    # Sort and apply caps
    all_lines.sort()

    all_files = sorted({p["path"] for p in parsed_for_files if "path" in p})
    selected_files = all_files
    truncated = False

    if max_files is not None and len(all_files) > max_files:
        selected_files = all_files[:max_files]
        truncated = True

    if max_files is not None:
        selected_set = set(selected_files)
        kept: list[str] = []
        for line in all_lines:
            if line.startswith("error:"):
                kept.append(line)
                continue
            parsed = _parse_rg_line(line)
            path = parsed.get("path") if parsed else None
            if path and path in selected_set:
                kept.append(line)
        all_lines = kept

    # Counts after max_files, before match/line truncation
    total_files = len(selected_files)
    total_matches = sum(1 for l in all_lines if (_parse_rg_line(l) or {}).get("kind") == "match")

    if max_matches is not None:
        kept: list[str] = []
        match_count = 0
        for line in all_lines:
            parsed = _parse_rg_line(line)
            if not parsed:
                continue
            if parsed.get("kind") == "match":
                if match_count >= max_matches:
                    truncated = True
                    continue
                match_count += 1
            kept.append(line)
        all_lines = kept

    if max_lines and len(all_lines) > max_lines:
        all_lines = all_lines[:max_lines]
        truncated = True

    # Emit results
    if effective_format == "jsonl":
        _emit_jsonl({
            "kind": "summary",
            "files": total_files,
            "matches": total_matches,
            "truncated": truncated,
        })
        for line in all_lines:
            parsed = _parse_rg_line(line)
            if not parsed:
                continue
            if parsed.get("kind") == "match":
                _emit_jsonl(
                    {
                        "kind": "match",
                        "path": parsed["path"],
                        "line": parsed["line"],
                        "content": parsed["content"],
                    }
                )
            elif parsed.get("kind") == "context":
                _emit_jsonl(
                    {
                        "kind": "context",
                        "path": parsed["path"],
                        "line": parsed["line"],
                        "content": parsed["content"],
                    }
                )
            elif parsed.get("kind") == "line":
                _emit_jsonl({"kind": "line", "line": parsed["line"]})
    else:
        print(f"files: {total_files}")
        print(f"matches: {total_matches}")
        if truncated:
            print("(truncated)")
        print()
        for line in all_lines:
            if line:
                print(line)

    return 0


def cmd_validate(_: argparse.Namespace) -> int:
    """Verify the skill is runnable."""
    errors: list[str] = []

    if shutil.which("rg") is None:
        errors.append("missing command: rg (ripgrep)")

    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        return 1

    print("ok: grep CLI is runnable")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="aux/grep - Agent-assisted text search")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # validate
    subparsers.add_parser("validate", help="Verify the skill is runnable")

    # run
    run_parser = subparsers.add_parser("run", help="Execute a deterministic text search")
    run_parser.add_argument("--root", default=".", help="Root directory")
    run_parser.add_argument("--pattern", action="append", help="Search pattern (repeatable)")
    run_parser.add_argument("--glob", action="append", help="Include glob (repeatable)")
    run_parser.add_argument("--exclude", action="append", help="Exclude glob (repeatable)")
    run_parser.add_argument("--mode", choices=["fixed", "regex"], default="fixed")
    run_parser.add_argument("--case", choices=["sensitive", "insensitive", "smart"], default="smart")
    run_parser.add_argument("--context", type=int, default=0)
    run_parser.add_argument("--format", choices=["auto", "human", "jsonl"], default="auto")
    run_parser.add_argument("--max-lines", type=int, default=500)
    run_parser.add_argument("--max-files", type=int, default=None)
    run_parser.add_argument("--max-matches", type=int, default=None)
    run_parser.add_argument("--parallelism", type=int, default=4)
    run_parser.add_argument("--hidden", action="store_true")
    run_parser.add_argument("--follow", action="store_true")
    run_parser.add_argument("--no-ignore", action="store_true")
    run_parser.add_argument("--stdin", action="store_true", help="Read plan JSON from stdin")

    args = parser.parse_args()

    if args.command == "validate":
        return cmd_validate(args)
    elif args.command == "run":
        return cmd_run(args)

    return 1


if __name__ == "__main__":
    sys.exit(main())
