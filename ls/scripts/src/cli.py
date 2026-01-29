#!/usr/bin/env python
import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from validate import validate_skill


def _emit_error(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)


def _json_dumps(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _write_json(path: Path, obj: object) -> None:
    path.write_text(_json_dumps(obj) + "\n", encoding="utf-8")


def _read_json_file(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid JSON in {path}: {e}") from e
    if not isinstance(obj, dict):
        raise ValueError(f"JSON in {path} must be an object")
    return obj


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


@dataclass(frozen=True)
class Limits:
    max_entries_scanned: int
    max_bytes_view: int


@dataclass(frozen=True)
class Plan:
    root: Path
    depth: int
    view: str
    sort: str
    order: str
    top_n: int
    include_hidden: bool
    classify_by_extension: bool
    classify_by_coarse_type: bool
    git_status: str
    limits: Limits
    raw: dict


@dataclass(frozen=True)
class Config:
    defaults: dict
    caps: dict
    policy: dict
    raw: dict


def _resolve_root(root: str) -> Path:
    return Path(root).resolve()


def _parse_plan(plan_obj: dict) -> Plan:
    schema = plan_obj.get("schema")
    if schema != "ls_plan_v1":
        raise ValueError("stdin plan schema must be 'ls_plan_v1'")

    ls = plan_obj.get("ls")
    if not isinstance(ls, dict):
        raise ValueError("stdin plan must contain object field 'ls'")

    required = [
        "root",
        "depth",
        "view",
        "sort",
        "order",
        "top_n",
        "include_hidden",
        "classify",
        "git_status",
        "limits",
    ]
    missing = [k for k in required if k not in ls]
    if missing:
        raise ValueError(f"stdin plan missing fields in ls: {', '.join(missing)}")

    root_raw = ls.get("root")
    if not isinstance(root_raw, str) or not root_raw:
        raise ValueError("stdin plan ls.root must be a non-empty string")

    depth = ls.get("depth")
    if not isinstance(depth, int) or depth < 0:
        raise ValueError("stdin plan ls.depth must be a non-negative integer")

    view = ls.get("view")
    if view not in ("flat", "tree"):
        raise ValueError("stdin plan ls.view must be 'flat' or 'tree'")

    sort = ls.get("sort")
    if sort not in ("mtime", "size", "name"):
        raise ValueError("stdin plan ls.sort must be one of: mtime, size, name")

    order = ls.get("order")
    if order not in ("asc", "desc"):
        raise ValueError("stdin plan ls.order must be 'asc' or 'desc'")

    top_n = ls.get("top_n")
    if not isinstance(top_n, int) or top_n <= 0:
        raise ValueError("stdin plan ls.top_n must be a positive integer")

    include_hidden = ls.get("include_hidden")
    if not isinstance(include_hidden, bool):
        raise ValueError("stdin plan ls.include_hidden must be boolean")

    classify = ls.get("classify")
    if not isinstance(classify, dict):
        raise ValueError("stdin plan ls.classify must be an object")
    for k in ("by_extension", "by_coarse_type"):
        if k not in classify:
            raise ValueError(f"stdin plan ls.classify missing field '{k}'")
        if not isinstance(classify.get(k), bool):
            raise ValueError(f"stdin plan ls.classify.{k} must be boolean")

    git_status = ls.get("git_status")
    if git_status not in ("auto", "on", "off"):
        raise ValueError("stdin plan ls.git_status must be 'auto', 'on', or 'off'")

    limits = ls.get("limits")
    if not isinstance(limits, dict):
        raise ValueError("stdin plan ls.limits must be an object")

    for k in ("max_entries_scanned", "max_bytes_view"):
        if k not in limits:
            raise ValueError(f"stdin plan ls.limits missing field '{k}'")
        if not isinstance(limits.get(k), int) or limits[k] <= 0:
            raise ValueError(f"stdin plan ls.limits.{k} must be a positive integer")

    return Plan(
        root=_resolve_root(root_raw),
        depth=depth,
        view=view,
        sort=sort,
        order=order,
        top_n=top_n,
        include_hidden=include_hidden,
        classify_by_extension=bool(classify["by_extension"]),
        classify_by_coarse_type=bool(classify["by_coarse_type"]),
        git_status=git_status,
        limits=Limits(
            max_entries_scanned=int(limits["max_entries_scanned"]),
            max_bytes_view=int(limits["max_bytes_view"]),
        ),
        raw=plan_obj,
    )


def _load_config(skill_dir: Path) -> Config:
    cfg_path = skill_dir / "assets" / "ls_config_v1.json"
    cfg = _read_json_file(cfg_path)

    if cfg.get("schema") != "ls_config_v1":
        raise ValueError("ls_config_v1.json must have schema 'ls_config_v1'")

    defaults = cfg.get("defaults")
    caps = cfg.get("caps")
    policy = cfg.get("policy")
    if not isinstance(defaults, dict) or not isinstance(caps, dict) or not isinstance(policy, dict):
        raise ValueError("ls_config_v1.json must contain objects: defaults, caps, policy")

    return Config(defaults=defaults, caps=caps, policy=policy, raw=cfg)


def _enforce_caps(plan: Plan, cfg: Config) -> None:
    caps = cfg.caps
    for k in ("max_depth", "max_entries_scanned", "max_top_n", "max_view_bytes"):
        if k not in caps or not isinstance(caps.get(k), int) or caps[k] <= 0:
            raise ValueError(f"ls_config_v1.caps.{k} must be a positive integer")

    if plan.depth > int(caps["max_depth"]):
        raise ValueError("plan depth exceeds config cap")

    if plan.top_n > int(caps["max_top_n"]):
        raise ValueError("plan top_n exceeds config cap")

    if plan.limits.max_entries_scanned > int(caps["max_entries_scanned"]):
        raise ValueError("plan max_entries_scanned exceeds config cap")

    if plan.limits.max_bytes_view > int(caps["max_view_bytes"]):
        raise ValueError("plan max_bytes_view exceeds config cap")


def _parse_git_porcelain_v1_z(output: bytes) -> dict[str, tuple[str, str | None]]:
    parts = output.split(b"\0")
    out: dict[str, tuple[str, str | None]] = {}
    i = 0
    while i < len(parts):
        rec = parts[i]
        i += 1
        if not rec:
            continue
        if len(rec) < 4 or rec[2:3] != b" ":
            continue

        xy = rec[:2].decode("utf-8", errors="replace")
        path = rec[3:].decode("utf-8", errors="replace")
        rename_from: str | None = None

        if ("R" in xy) or ("C" in xy):
            if i < len(parts) and parts[i]:
                rename_from = path
                path = parts[i].decode("utf-8", errors="replace")
                i += 1

        out[path] = (xy, rename_from)
    return out


def _compute_git_status(plan: Plan, root: Path) -> tuple[dict, dict[str, tuple[str, str | None]]]:
    if plan.git_status == "off":
        return (
            {"mode": plan.git_status, "detected": False, "status": "disabled", "message": None},
            {},
        )

    if shutil.which("git") is None:
        return (
            {
                "mode": plan.git_status,
                "detected": False,
                "status": "git_not_found",
                "message": "git not found",
            },
            {},
        )

    try:
        p = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as e:
        return (
            {
                "mode": plan.git_status,
                "detected": False,
                "status": "error",
                "message": str(e),
            },
            {},
        )

    if p.returncode != 0 or p.stdout.strip() != b"true":
        return (
            {
                "mode": plan.git_status,
                "detected": False,
                "status": "not_a_repo",
                "message": None,
            },
            {},
        )

    try:
        s = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain=v1", "-z"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as e:
        return (
            {
                "mode": plan.git_status,
                "detected": True,
                "status": "error",
                "message": str(e),
            },
            {},
        )

    if s.returncode != 0:
        msg = s.stderr.decode("utf-8", errors="replace").strip() or "git status failed"
        return (
            {
                "mode": plan.git_status,
                "detected": True,
                "status": "error",
                "message": msg,
            },
            {},
        )

    return (
        {"mode": plan.git_status, "detected": True, "status": "enabled", "message": None},
        _parse_git_porcelain_v1_z(s.stdout),
    )


def _coarse_type_from_extension(ext: str | None) -> str | None:
    if ext is None:
        return None
    e = ext.lower()
    if e in ("py", "js", "ts", "tsx", "jsx", "go", "rs", "java", "c", "cc", "cpp", "h", "hpp", "rb", "php"):
        return "code"
    if e in ("md", "rst", "txt"):
        return "doc"
    if e in ("json", "yaml", "yml", "toml", "ini", "cfg", "conf", "xml"):
        return "config"
    if e in ("png", "jpg", "jpeg", "gif", "webp", "svg", "pdf", "zip", "gz", "tar", "7z", "mp3", "mp4"):
        return "binary"
    return "other"


def _rel_path_str(path: Path, root: Path) -> str:
    try:
        rel = path.relative_to(root)
        return rel.as_posix() if rel.as_posix() else "."
    except ValueError:
        return str(path)


def _enumerate_entries(
    root: Path,
    *,
    max_depth: int,
    include_hidden: bool,
    max_entries_scanned: int,
    classify_by_extension: bool,
    classify_by_coarse_type: bool,
) -> tuple[list[dict], int, bool, list[dict]]:
    stack: list[tuple[Path, int]] = [(root, 0)]
    scanned = 0
    scan_truncated = False
    errors: list[dict] = []
    out: list[dict] = []

    while stack:
        current_dir, depth = stack.pop()

        try:
            with os.scandir(current_dir) as it:
                dir_entries = sorted(list(it), key=lambda e: e.name)
        except PermissionError as e:
            errors.append(
                {
                    "path": _rel_path_str(current_dir, root),
                    "kind": "permission_denied",
                    "message": str(e),
                }
            )
            continue
        except OSError as e:
            errors.append({"path": _rel_path_str(current_dir, root), "kind": "io", "message": str(e)})
            continue

        dirs_to_push: list[Path] = []
        for ent in dir_entries:
            if scanned >= max_entries_scanned:
                scan_truncated = True
                break

            name = ent.name
            if not include_hidden and name.startswith("."):
                continue

            # Do not resolve: resolving can escape root via symlinks.
            abs_path = Path(ent.path)
            rel_str = _rel_path_str(abs_path, root)
            scanned += 1

            try:
                is_link = ent.is_symlink()
            except OSError:
                is_link = False

            entry_type: str
            try:
                if is_link:
                    entry_type = "symlink"
                elif ent.is_dir(follow_symlinks=False):
                    entry_type = "dir"
                elif ent.is_file(follow_symlinks=False):
                    entry_type = "file"
                else:
                    entry_type = "other"
            except OSError:
                entry_type = "other"

            try:
                st = ent.stat(follow_symlinks=False)
                size_bytes = int(st.st_size)
                mtime_ms = int(st.st_mtime_ns // 1_000_000)
            except OSError as e:
                size_bytes = 0
                mtime_ms = 0
                errors.append({"path": rel_str, "kind": "stat_failed", "message": str(e)})

            ext: str | None = None
            if entry_type == "file" and classify_by_extension:
                suf = Path(ent.name).suffix
                if suf.startswith(".") and len(suf) > 1:
                    ext = suf[1:]

            coarse: str | None = None
            if classify_by_coarse_type:
                coarse = _coarse_type_from_extension(ext)

            out.append(
                {
                    "path": rel_str,
                    "type": entry_type,
                    "size_bytes": size_bytes,
                    "mtime_epoch_ms": mtime_ms,
                    "extension": ext,
                    "coarse_type": coarse,
                    "git_xy": None,
                    "git_rename_from": None,
                }
            )

            if depth < max_depth:
                try:
                    # Never traverse symlinks.
                    if ent.is_dir(follow_symlinks=False) and not is_link:
                        dirs_to_push.append(abs_path)
                except OSError:
                    pass

        if scan_truncated:
            break

        # Depth-first: push in reverse so lexicographic order is preserved.
        for d in reversed(dirs_to_push):
            stack.append((d, depth + 1))

    return out, scanned, scan_truncated, errors


def _compute_inventory(plan: Plan, cfg: Config, aux_dir: Path) -> tuple[dict, dict, str]:
    root = plan.root
    if not root.exists():
        raise ValueError(f"root directory not found: {root}")
    if not root.is_dir():
        raise ValueError(f"root is not a directory: {root}")

    entries, scanned, scan_truncated, errors = _enumerate_entries(
        root,
        max_depth=plan.depth,
        include_hidden=plan.include_hidden,
        max_entries_scanned=plan.limits.max_entries_scanned,
        classify_by_extension=plan.classify_by_extension,
        classify_by_coarse_type=plan.classify_by_coarse_type,
    )

    git_block, git_map = _compute_git_status(plan, root)
    if git_block["status"] == "enabled":
        for e in entries:
            m = git_map.get(e["path"])
            if m is not None:
                e["git_xy"] = m[0]
                e["git_rename_from"] = m[1]

    # Rank deterministically
    if plan.sort == "name":
        ranked = sorted(entries, key=lambda e: e["path"], reverse=(plan.order == "desc"))
    elif plan.sort == "mtime":
        if plan.order == "desc":
            ranked = sorted(entries, key=lambda e: (-int(e["mtime_epoch_ms"]), e["path"]))
        else:
            ranked = sorted(entries, key=lambda e: (int(e["mtime_epoch_ms"]), e["path"]))
    else:  # size
        if plan.order == "desc":
            ranked = sorted(entries, key=lambda e: (-int(e["size_bytes"]), e["path"]))
        else:
            ranked = sorted(entries, key=lambda e: (int(e["size_bytes"]), e["path"]))

    rank_truncated = False
    if len(ranked) > plan.top_n:
        ranked = ranked[: plan.top_n]
        rank_truncated = True

    counts_by_type = {"file": 0, "dir": 0, "symlink": 0, "other": 0}
    bytes_total = 0
    for e in ranked:
        t = e["type"]
        if t in counts_by_type:
            counts_by_type[t] += 1
        bytes_total += int(e["size_bytes"])

    inventory = {
        "schema": "ls_inventory_v1",
        "plan": plan.raw,
        "summary": {
            "root": str(root),
            "scanned": int(scanned),
            "returned": int(len(ranked)),
            "counts_by_type": counts_by_type,
            "bytes_total": int(bytes_total),
        },
        "entries": ranked,
    }

    view_text = _render_view(plan, inventory, scan_truncated, rank_truncated)
    view_bytes = view_text.encode("utf-8")
    view_truncated = False
    if len(view_bytes) > plan.limits.max_bytes_view:
        truncated = view_bytes[: plan.limits.max_bytes_view]
        view_text = truncated.decode("utf-8", errors="ignore")
        view_truncated = True

    receipt = {
        "schema": "ls_receipt_v1",
        "plan": plan.raw,
        "scan": {
            "root": str(root),
            "depth": int(plan.depth),
            "entries_scanned": int(scanned),
            "errors": errors,
        },
        "ranking": {
            "sort": plan.sort,
            "order": plan.order,
            "top_n": int(plan.top_n),
            "entries_returned": int(len(ranked)),
        },
        "git": git_block,
        "ignores": {
            "include_hidden": bool(plan.include_hidden),
            "sources": ["none"],
        },
        "artifacts": {
            "inventory_json": str(aux_dir / "ls_inventory.json"),
            "view_txt": str(aux_dir / "ls_view.txt"),
        },
        "truncation": {
            "scan_truncated": bool(scan_truncated),
            "rank_truncated": bool(rank_truncated),
            "view_truncated": bool(view_truncated),
            "reason": None,
        },
    }

    if receipt["truncation"]["scan_truncated"]:
        receipt["truncation"]["reason"] = "scan cap reached"
    elif receipt["truncation"]["rank_truncated"]:
        receipt["truncation"]["reason"] = "rank cap reached"
    elif receipt["truncation"]["view_truncated"]:
        receipt["truncation"]["reason"] = "view cap reached"

    return inventory, receipt, view_text


def _render_view(plan: Plan, inventory: dict, scan_truncated: bool, rank_truncated: bool) -> str:
    s = inventory["summary"]
    lines: list[str] = []
    lines.append(f"root: {s['root']}")
    lines.append(f"scanned: {s['scanned']}")
    lines.append(f"returned: {s['returned']}")
    if scan_truncated or rank_truncated:
        lines.append("(truncated)")
    lines.append("")

    for e in inventory["entries"]:
        lines.append(e["path"])

    return "\n".join(lines) + "\n"


def cmd_validate(_: argparse.Namespace) -> int:
    errors: list[str] = []

    if shutil.which("uv") is None:
        errors.append("missing command: uv")

    errors.extend(validate_skill())

    if errors:
        for e in errors:
            _emit_error(e)
        return 1

    print("ok: ls CLI is runnable")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    if not args.stdin:
        _emit_error("run requires --stdin")
        return 1

    script_dir = Path(__file__).resolve().parent
    skill_dir = script_dir.parent.parent
    repo_root = skill_dir.parent.parent
    aux_dir = repo_root / ".aux" / "ls"
    aux_dir.mkdir(parents=True, exist_ok=True)

    try:
        plan_obj = _read_plan_from_stdin()
        plan = _parse_plan(plan_obj)
        cfg = _load_config(skill_dir)
        _enforce_caps(plan, cfg)

        inventory, receipt, view_text = _compute_inventory(plan, cfg, aux_dir)

        _write_json(aux_dir / "ls_inventory.json", inventory)
        _write_json(aux_dir / "ls_receipt.json", receipt)
        (aux_dir / "ls_view.txt").write_text(view_text, encoding="utf-8")

        sys.stdout.write(view_text)
        return 0
    except ValueError as e:
        _emit_error(str(e))
        return 1
    except OSError as e:
        _emit_error(str(e))
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="aux/ls - Deterministic directory state inspection")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("validate", help="Verify the skill is runnable")

    run_parser = subparsers.add_parser("run", help="Execute a deterministic directory inventory")
    run_parser.add_argument("--stdin", action="store_true", help="Read plan JSON from stdin")

    args = parser.parse_args()

    if args.command == "validate":
        return cmd_validate(args)
    elif args.command == "run":
        return cmd_run(args)

    return 1


if __name__ == "__main__":
    sys.exit(main())
