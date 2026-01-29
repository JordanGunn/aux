#!/usr/bin/env python3
"""
aux/find CLI - Agent-assisted file enumeration (deterministic fd wrapper)

All execution is deterministic. The agent selects parameters; this script executes.
"""

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import sys
import fnmatch
import re
from pathlib import Path


def _fd_executable() -> str | None:
    """Resolve fd executable name across platforms.

    Debian/Ubuntu packages `fd-find` as `fdfind` to avoid conflicts.
    """
    if shutil.which("fd") is not None:
        return "fd"
    if shutil.which("fdfind") is not None:
        return "fdfind"
    return None


def _get_tool_versions() -> dict:
    """Get tool versions for reproducibility metadata."""
    versions = {"python": platform.python_version()}
    try:
        fd_exe = _fd_executable() or "fd"
        r = subprocess.run([fd_exe, "--version"], capture_output=True, text=True, check=False)
        if r.returncode == 0:
            versions["fd"] = r.stdout.strip()
    except OSError:
        versions["fd"] = "not found"
    return versions


def _compute_query_id(param_block: dict) -> str:
    """Compute stable query_id from normalized parameters."""
    keys_for_hash = [
        "root",
        "patterns",
        "include_patterns",
        "extensions",
        "excludes",
        "exclude_patterns",
        "type",
        "max_depth",
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


def _normalize_path_for_matching(p: str) -> str:
    return p.replace("\\", "/")


def _parse_find_plan_from_stdin() -> dict:
    """
    Parse find plan JSON from stdin.

    Supports:
      - find_plan_v1 (legacy): string patterns are treated as glob patterns
      - find_plan_v2: pattern objects with required `kind` per pattern
    """
    plan = _read_plan_from_stdin()
    schema = plan.get("schema")
    if schema not in ("find_plan_v1", "find_plan_v2"):
        raise ValueError("stdin plan schema must be 'find_plan_v1' or 'find_plan_v2'")

    find = plan.get("find")
    if not isinstance(find, dict):
        raise ValueError("stdin plan must contain object field 'find'")

    if schema == "find_plan_v1":
        required = [
            "root",
            "pattern",
            "extension",
            "exclude",
            "type",
            "max_depth",
            "max_results",
            "format",
            "policy",
        ]
        missing = [k for k in required if k not in find]
        if missing:
            raise ValueError(f"stdin plan missing fields in find: {', '.join(missing)}")

        policy = find.get("policy")
        if not isinstance(policy, dict):
            raise ValueError("stdin plan find.policy must be an object")

        include_patterns = [{"kind": "glob", "value": p} for p in (find.get("pattern") or [])]
        exclude_patterns = [{"kind": "glob", "value": p} for p in (find.get("exclude") or [])]
        return {
            "schema": schema,
            "root": find["root"],
            "include_patterns": include_patterns,
            "exclude_patterns": exclude_patterns,
            "extensions": list(find.get("extension") or []),
            "type": find["type"],
            "max_depth": find.get("max_depth"),
            "max_results": find["max_results"],
            "format": find["format"],
            "policy": {
                "hidden": bool(policy.get("hidden", False)),
                "follow": bool(policy.get("follow", False)),
                "no_ignore": bool(policy.get("no_ignore", False)),
            },
            "limits": {
                "max_pattern_length": 512,
                "max_exclude_pattern_length": 512,
            },
        }

    # find_plan_v2
    required = [
        "root",
        "include_patterns",
        "exclude_patterns",
        "extensions",
        "type",
        "max_depth",
        "max_results",
        "format",
        "policy",
        "limits",
    ]
    missing = [k for k in required if k not in find]
    if missing:
        raise ValueError(f"stdin plan missing fields in find: {', '.join(missing)}")

    policy = find.get("policy")
    if not isinstance(policy, dict):
        raise ValueError("stdin plan find.policy must be an object")

    limits = find.get("limits")
    if not isinstance(limits, dict):
        raise ValueError("stdin plan find.limits must be an object")

    include_patterns = find.get("include_patterns")
    exclude_patterns = find.get("exclude_patterns")
    if not isinstance(include_patterns, list):
        raise ValueError("stdin plan find.include_patterns must be an array")
    if not isinstance(exclude_patterns, list):
        raise ValueError("stdin plan find.exclude_patterns must be an array")

    def _validate_pattern_list(items: list, *, field: str, allowed_kinds: set[str], max_len: int) -> list[dict]:
        out: list[dict] = []
        for i, it in enumerate(items):
            if not isinstance(it, dict):
                raise ValueError(f"stdin plan {field}[{i}] must be an object")
            if "kind" not in it or "value" not in it:
                raise ValueError(f"stdin plan {field}[{i}] must include 'kind' and 'value'")
            kind = it.get("kind")
            value = it.get("value")
            if kind not in allowed_kinds:
                raise ValueError(f"stdin plan {field}[{i}].kind must be one of: {', '.join(sorted(allowed_kinds))}")
            if not isinstance(value, str) or not value:
                raise ValueError(f"stdin plan {field}[{i}].value must be a non-empty string")
            if len(value) > max_len:
                raise ValueError(f"stdin plan {field}[{i}].value exceeds max length {max_len}")
            out.append({"kind": kind, "value": value})
        return out

    max_pat_len = limits.get("max_pattern_length")
    max_exc_len = limits.get("max_exclude_pattern_length")
    if not isinstance(max_pat_len, int) or max_pat_len <= 0:
        raise ValueError("stdin plan find.limits.max_pattern_length must be a positive integer")
    if not isinstance(max_exc_len, int) or max_exc_len <= 0:
        raise ValueError("stdin plan find.limits.max_exclude_pattern_length must be a positive integer")

    include_out = _validate_pattern_list(
        include_patterns, field="find.include_patterns", allowed_kinds={"glob", "regex"}, max_len=max_pat_len
    )
    exclude_out = _validate_pattern_list(
        exclude_patterns, field="find.exclude_patterns", allowed_kinds={"glob", "regex"}, max_len=max_exc_len
    )

    extensions = find.get("extensions")
    if not isinstance(extensions, list):
        raise ValueError("stdin plan find.extensions must be an array")

    return {
        "schema": schema,
        "root": find["root"],
        "include_patterns": include_out,
        "exclude_patterns": exclude_out,
        "extensions": list(extensions),
        "type": find["type"],
        "max_depth": find.get("max_depth"),
        "max_results": find["max_results"],
        "format": find["format"],
        "policy": {
            "hidden": bool(policy.get("hidden", False)),
            "follow": bool(policy.get("follow", False)),
            "no_ignore": bool(policy.get("no_ignore", False)),
        },
        "limits": {
            "max_pattern_length": max_pat_len,
            "max_exclude_pattern_length": max_exc_len,
        },
    }


def _build_fd_args(
    root: Path,
    include_pattern: dict | None,
    extensions: list[str],
    excludes: list[str],
    entry_type: str,
    max_depth: int | None,
    hidden: bool,
    follow: bool,
    no_ignore: bool,
) -> list[str]:
    """Build fd argument list."""
    fd_exe = _fd_executable()
    if fd_exe is None:
        raise RuntimeError("missing command: fd (fd-find; binary may be 'fdfind' on Debian/Ubuntu)")

    args = [fd_exe]

    # Type filter
    if entry_type == "file":
        args.extend(["--type", "f"])
    elif entry_type == "directory":
        args.extend(["--type", "d"])
    # 'any' means no type filter

    if max_depth is not None:
        args.extend(["--max-depth", str(max_depth)])

    if hidden:
        args.append("--hidden")

    if follow:
        args.append("--follow")

    if no_ignore:
        args.append("--no-ignore")

    for ext in sorted(extensions):
        args.extend(["--extension", ext])

    for exc in sorted(excludes):
        args.extend(["--exclude", exc])

    # fd accepts a single positional pattern.
    # - regex is fd default
    # - --glob switches to glob semantics
    if include_pattern:
        kind = include_pattern["kind"]
        value = include_pattern["value"]
        if kind == "glob":
            args.append("--glob")
            args.append(value)
        else:
            args.append(value)
    else:
        args.append(".")

    args.append(str(root))

    return args


def cmd_run(args: argparse.Namespace) -> int:
    """Execute the find enumeration."""
    if args.stdin:
        try:
            plan = _parse_find_plan_from_stdin()
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1

        root = _resolve_root(plan["root"])
        include_patterns: list[dict] = plan["include_patterns"]
        extensions: list[str] = sorted(plan["extensions"])
        exclude_patterns: list[dict] = plan["exclude_patterns"]
        entry_type: str = plan["type"]
        max_depth: int | None = plan["max_depth"]
        max_results: int = plan["max_results"]
        output_format: str = plan["format"]
        hidden: bool = plan["policy"]["hidden"]
        follow: bool = plan["policy"]["follow"]
        no_ignore: bool = plan["policy"]["no_ignore"]
        plan_schema: str = plan["schema"]
    else:
        root = _resolve_root(args.root)
        include_patterns = [{"kind": "glob", "value": p} for p in sorted(args.pattern or [])]
        extensions = sorted(args.extension or [])
        exclude_patterns = [{"kind": "glob", "value": p} for p in sorted(args.exclude or [])]
        entry_type = args.type
        max_depth = args.max_depth
        max_results = args.max_results
        output_format = args.format
        hidden = args.hidden
        follow = args.follow
        no_ignore = args.no_ignore
        plan_schema = "cli_args_v1"

    if not root.exists():
        print(f"error: root directory not found: {root}", file=sys.stderr)
        return 1

    # Use glob excludes with fd to reduce surface; apply regex excludes post-filter.
    fd_excludes = [p["value"] for p in exclude_patterns if p["kind"] == "glob"]

    # Build param block for reproducibility
    param_block = {
        "plan_schema": plan_schema,
        "root": str(root),
        "include_patterns": include_patterns,
        "extensions": extensions,
        "exclude_patterns": exclude_patterns,
        "type": entry_type,
        "max_depth": max_depth,
        "max_results": max_results,
        "format": output_format,
        "tool_versions": _get_tool_versions(),
        "policy": {
            "hidden": hidden,
            "follow": follow,
            "no_ignore": no_ignore,
        },
    }
    param_block["query_id"] = _compute_query_id(param_block)

    # Detect output format
    is_tty = sys.stdout.isatty()
    effective_format = output_format if output_format != "auto" else ("human" if is_tty else "jsonl")

    # Build fd argv(s) up front so the parameter block is fully replayable.
    argv_by_pattern: list[dict] = []
    patterns_to_run: list[dict | None] = include_patterns or [None]
    for p in patterns_to_run:
        try:
            fd_args = _build_fd_args(
                root, p, extensions, fd_excludes, entry_type, max_depth, hidden, follow, no_ignore
            )
        except RuntimeError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        argv_by_pattern.append({"pattern": p, "argv": fd_args})

    if include_patterns:
        param_block["argv_by_pattern"] = [
            {"pattern": d["pattern"], "argv": d["argv"]} for d in argv_by_pattern
        ]
    else:
        param_block["argv"] = argv_by_pattern[0]["argv"]

    # Emit param block
    if effective_format == "jsonl":
        _emit_jsonl({"kind": "param_block", "param_block": param_block})
    else:
        print(f"# query_id: {param_block['query_id']}")
        print(f"# root: {root}")
        print(f"# include_patterns: {include_patterns}")
        print(f"# extensions: {extensions}")
        print(f"# exclude_patterns: {exclude_patterns}")
        print(f"# type: {entry_type}")
        print()

    # Run fd command(s).
    # Multiple patterns are supported by running fd once per pattern and unioning results.
    all_paths: set[str] = set()
    for d in argv_by_pattern:
        fd_args = d["argv"]
        try:
            result = subprocess.run(fd_args, capture_output=True, text=True, check=False)
        except OSError as e:
            exe = fd_args[0] if fd_args else "fd"
            print(f"error: failed to run {exe}: {e}", file=sys.stderr)
            return 1

        out_lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
        for line in out_lines:
            if line:
                all_paths.add(line)

    # Apply exclude_patterns deterministically (regex/glob), fail closed on invalid regex.
    if exclude_patterns:
        filtered: set[str] = set()
        compiled_regex: dict[str, re.Pattern] = {}
        for p in exclude_patterns:
            if p["kind"] == "regex":
                try:
                    compiled_regex[p["value"]] = re.compile(p["value"])
                except re.error as e:
                    print(f"error: invalid exclude regex '{p['value']}': {e}", file=sys.stderr)
                    return 1

        for path in all_paths:
            s = _normalize_path_for_matching(path)
            excluded = False
            for p in exclude_patterns:
                if p["kind"] == "glob":
                    if fnmatch.fnmatch(s, p["value"]):
                        excluded = True
                        break
                else:
                    if compiled_regex[p["value"]].search(s):
                        excluded = True
                        break
            if not excluded:
                filtered.add(path)
        all_paths = filtered

    # Sort and apply caps
    lines = sorted(all_paths)

    total_results = len(lines)
    truncated = False

    if len(lines) > max_results:
        lines = lines[:max_results]
        truncated = True

    # Count types
    file_count = 0
    dir_count = 0
    for line in lines:
        if line:
            p = Path(line)
            actual = p if p.is_absolute() else (root / p)
            if actual.is_dir():
                dir_count += 1
            else:
                file_count += 1

    # Emit results
    if effective_format == "jsonl":
        _emit_jsonl({
            "kind": "summary",
            "total": total_results,
            "files": file_count,
            "directories": dir_count,
            "truncated": truncated,
        })
        for line in lines:
            if line:
                p = Path(line)
                actual = p if p.is_absolute() else (root / p)
                entry_type_actual = "directory" if actual.is_dir() else "file"
                _emit_jsonl({"kind": "entry", "path": line, "type": entry_type_actual})
    else:
        print(f"total: {total_results}")
        print(f"files: {file_count}")
        print(f"directories: {dir_count}")
        if truncated:
            print("(truncated)")
        print()
        for line in lines:
            if line:
                print(line)

    return 0


def cmd_validate(_: argparse.Namespace) -> int:
    """Verify the skill is runnable."""
    errors: list[str] = []

    if _fd_executable() is None:
        errors.append("missing command: fd (fd-find; binary may be 'fdfind' on Debian/Ubuntu)")

    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        return 1

    print("ok: find CLI is runnable")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="aux/find - Agent-assisted file enumeration")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # validate
    subparsers.add_parser("validate", help="Verify the skill is runnable")

    # run
    run_parser = subparsers.add_parser("run", help="Execute a deterministic file enumeration")
    run_parser.add_argument("--root", default=".", help="Root directory")
    run_parser.add_argument("--pattern", action="append", help="Glob pattern (repeatable)")
    run_parser.add_argument("--extension", action="append", help="File extension (repeatable)")
    run_parser.add_argument("--exclude", action="append", help="Exclude pattern (repeatable)")
    run_parser.add_argument("--type", choices=["file", "directory", "any"], default="file")
    run_parser.add_argument("--max-depth", type=int, default=None)
    run_parser.add_argument("--max-results", type=int, default=1000)
    run_parser.add_argument("--format", choices=["auto", "human", "jsonl"], default="auto")
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
