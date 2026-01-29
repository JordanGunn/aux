#!/usr/bin/env python3
"""Deterministic git diff inspection CLI."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).parent.resolve()
SKILL_DIR = SCRIPT_DIR.parent.parent
ASSETS_DIR = SKILL_DIR / "assets"
SCHEMAS_DIR = ASSETS_DIR / "schemas"


def cmd_validate() -> int:
    """Validate that the skill is runnable."""
    errors = 0

    required_schemas = [
        "diff_intent_v1.schema.json",
        "diff_discovery_plan_v1.schema.json",
        "diff_plan_v1.schema.json",
        "diff_summary_v1.schema.json",
        "diff_receipt_v1.schema.json",
        "diff_result_bundle_v1.schema.json",
    ]

    for schema in required_schemas:
        path = SCHEMAS_DIR / schema
        if not path.exists():
            print(f"error: missing {path}", file=sys.stderr)
            errors += 1
        else:
            try:
                with open(path) as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                print(f"error: invalid JSON in {path}: {e}", file=sys.stderr)
                errors += 1

    required_templates = [
        "diff_intent_v1.template.json",
        "diff_discovery_plan_v1.template.json",
        "diff_plan_v1.template.json",
    ]

    templates_dir = ASSETS_DIR / "templates"
    for template in required_templates:
        path = templates_dir / template
        if not path.exists():
            print(f"error: missing {path}", file=sys.stderr)
            errors += 1
        else:
            try:
                with open(path) as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                print(f"error: invalid JSON in {path}: {e}", file=sys.stderr)
                errors += 1

    if errors > 0:
        return 1

    print("ok: cli validation passed")
    return 0


def detect_git_environment(root: str) -> dict[str, Any]:
    """Detect git environment at the given root."""
    result: dict[str, Any] = {
        "git_detected": False,
        "git_root": None,
        "git_version": None,
    }

    try:
        version_result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if version_result.returncode == 0:
            result["git_version"] = version_result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return result

    try:
        root_result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            cwd=root,
            timeout=10,
        )
        if root_result.returncode == 0:
            result["git_detected"] = True
            result["git_root"] = root_result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    return result


def cmd_discover(args: argparse.Namespace) -> int:
    """Run discovery phase to enumerate change candidates."""
    if args.stdin:
        try:
            plan = json.load(sys.stdin)
        except json.JSONDecodeError as e:
            print(f"error: invalid JSON input: {e}", file=sys.stderr)
            return 1
    else:
        print("error: --stdin required", file=sys.stderr)
        return 1

    root = plan.get("root", os.getcwd())
    env = detect_git_environment(root)

    timestamp = datetime.now(timezone.utc).isoformat()

    if not env["git_detected"]:
        receipt = {
            "status": "error",
            "timestamp": timestamp,
            "environment": env,
            "error": "Not a git repository",
        }
        print(json.dumps(receipt, indent=2))
        return 1

    # Run git diff --name-status to enumerate changes
    scope = plan.get("scope", {})
    mode = scope.get("mode", "working_tree")
    paths = scope.get("paths", [])
    bounds = plan.get("bounds", {})
    max_files = bounds.get("max_files", 100)

    cmd = ["git", "diff", "--name-status"]
    if mode == "staged":
        cmd.append("--cached")
    elif mode == "commit_range":
        base_ref = scope.get("base_ref", "HEAD~1")
        head_ref = scope.get("head_ref", "HEAD")
        cmd.extend([base_ref, head_ref])

    if paths:
        cmd.append("--")
        cmd.extend(paths)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=root,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        receipt = {
            "status": "error",
            "timestamp": timestamp,
            "environment": env,
            "error": "git diff timed out",
        }
        print(json.dumps(receipt, indent=2))
        return 1

    files = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) >= 2:
            status_code = parts[0]
            path = parts[-1]
            files.append({"status": status_code, "path": path})
        if len(files) >= max_files:
            break

    discovery = {
        "files": files,
        "count": len(files),
        "truncated": len(result.stdout.strip().split("\n")) > max_files,
    }

    receipt = {
        "status": "success",
        "timestamp": timestamp,
        "environment": env,
        "discovery": discovery,
    }

    print(json.dumps(receipt, indent=2))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    """Execute a bounded diff."""
    if args.stdin:
        try:
            plan = json.load(sys.stdin)
        except json.JSONDecodeError as e:
            print(f"error: invalid JSON input: {e}", file=sys.stderr)
            return 1
    else:
        print("error: --stdin required", file=sys.stderr)
        return 1

    root = plan.get("root", os.getcwd())
    env = detect_git_environment(root)

    timestamp = datetime.now(timezone.utc).isoformat()

    if not env["git_detected"]:
        receipt = {
            "status": "error",
            "timestamp": timestamp,
            "environment": env,
            "error": "Not a git repository",
        }
        print(json.dumps(receipt, indent=2))
        return 1

    scope = plan.get("scope", {})
    comparison = scope.get("comparison", "working_tree_vs_index")
    paths = scope.get("paths", [])
    mode = plan.get("mode", "summary_only")
    bounds = plan.get("bounds", {})
    max_files = bounds.get("max_files", 100)
    normalization = plan.get("normalization", {})
    rename_detection = plan.get("rename_detection", False)

    # Build git diff command
    cmd = ["git", "diff", "--numstat"]
    
    if comparison == "index_vs_head":
        cmd.append("--cached")
    elif comparison == "commit_range":
        base_ref = scope.get("base_ref", "HEAD~1")
        head_ref = scope.get("head_ref", "HEAD")
        cmd.extend([base_ref, head_ref])

    if rename_detection:
        cmd.append("-M")

    if normalization.get("line_ending"):
        cmd.append("--ignore-cr-at-eol")

    whitespace = normalization.get("whitespace", "none")
    if whitespace == "ignore_space_change":
        cmd.append("-b")
    elif whitespace == "ignore_all_space":
        cmd.append("-w")

    if paths:
        cmd.append("--")
        cmd.extend(paths)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=root,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        receipt = {
            "status": "error",
            "timestamp": timestamp,
            "environment": env,
            "error": "git diff timed out",
        }
        print(json.dumps(receipt, indent=2))
        return 1

    files = []
    total_insertions = 0
    total_deletions = 0
    truncated = False

    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) >= 3:
            ins = 0 if parts[0] == "-" else int(parts[0])
            dels = 0 if parts[1] == "-" else int(parts[1])
            path = parts[2]
            binary = parts[0] == "-" and parts[1] == "-"

            files.append({
                "path": path,
                "status": "binary" if binary else "modified",
                "insertions": ins,
                "deletions": dels,
                "binary": binary,
            })
            total_insertions += ins
            total_deletions += dels

        if len(files) >= max_files:
            truncated = True
            break

    summary = {
        "files_changed": len(files),
        "insertions": total_insertions,
        "deletions": total_deletions,
        "files": files,
        "truncated": truncated,
        "scope": scope,
    }

    receipt = {
        "status": "success" if not truncated else "truncated",
        "timestamp": timestamp,
        "environment": env,
        "bounds_applied": bounds,
        "truncation": {
            "truncated": truncated,
            "files_processed": len(files),
        },
        "artifacts_emitted": ["diff_summary_v1.json", "diff_receipt_v1.json"],
    }

    output = {
        "summary": summary,
        "receipt": receipt,
    }

    print(json.dumps(output, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic git diff CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate skill assets")

    discover_parser = subparsers.add_parser("discover", help="Run discovery phase")
    discover_parser.add_argument("--stdin", action="store_true", help="Read plan from stdin")

    run_parser = subparsers.add_parser("run", help="Execute bounded diff")
    run_parser.add_argument("--stdin", action="store_true", help="Read plan from stdin")

    args = parser.parse_args()

    if args.command == "validate":
        return cmd_validate()
    elif args.command == "discover":
        return cmd_discover(args)
    elif args.command == "run":
        return cmd_run(args)

    return 1


if __name__ == "__main__":
    sys.exit(main())
