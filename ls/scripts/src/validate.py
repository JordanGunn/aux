#!/usr/bin/env python
import json
import sys
from pathlib import Path


def _read_json(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid JSON in {path}: {e}") from e
    if not isinstance(obj, dict):
        raise ValueError(f"JSON in {path} must be an object")
    return obj


def validate_skill() -> list[str]:
    errors: list[str] = []

    script_dir = Path(__file__).resolve().parent
    skill_dir = script_dir.parent.parent
    assets_dir = skill_dir / "assets"
    schemas_dir = assets_dir / "schemas"
    templates_dir = assets_dir / "templates"

    required_files = [
        assets_dir / "ls_config_v1.json",
        schemas_dir / "ls_config_v1.schema.json",
        schemas_dir / "ls_intent_v1.schema.json",
        schemas_dir / "ls_plan_v1.schema.json",
        schemas_dir / "ls_result_bundle_v1.schema.json",
        templates_dir / "ls_intent_v1.template.json",
        templates_dir / "ls_plan_v1.template.json",
        templates_dir / "ls_config_v1.template.json",
    ]

    for p in required_files:
        if not p.exists():
            errors.append(f"missing file: {p}")

    if errors:
        return errors

    try:
        cfg = _read_json(assets_dir / "ls_config_v1.json")
        if cfg.get("schema") != "ls_config_v1":
            errors.append("ls_config_v1.json must have schema 'ls_config_v1'")

        defaults = cfg.get("defaults")
        caps = cfg.get("caps")
        policy = cfg.get("policy")
        if not isinstance(defaults, dict) or not isinstance(caps, dict) or not isinstance(policy, dict):
            errors.append("ls_config_v1.json must contain objects: defaults, caps, policy")
        else:
            if defaults.get("git_status") not in ("auto", "enabled", "disabled"):
                errors.append("ls_config_v1.defaults.git_status must be 'auto', 'enabled', or 'disabled'")

            for k in ("max_depth", "max_entries_scanned", "max_top_n", "max_view_bytes", "max_assumptions"):
                v = caps.get(k)
                if not isinstance(v, int) or v <= 0:
                    errors.append(f"ls_config_v1.caps.{k} must be a positive integer")

            follow = policy.get("follow_symlinks")
            if not isinstance(follow, bool):
                errors.append("ls_config_v1.policy.follow_symlinks must be boolean")

            gitignore = policy.get("gitignore")
            if not isinstance(gitignore, dict) or gitignore.get("mode") not in ("git_only", "none"):
                errors.append("ls_config_v1.policy.gitignore.mode must be 'git_only' or 'none'")
    except ValueError as e:
        errors.append(str(e))

    for fname in (
        "ls_config_v1.schema.json",
        "ls_intent_v1.schema.json",
        "ls_plan_v1.schema.json",
        "ls_result_bundle_v1.schema.json",
    ):
        try:
            sch = _read_json(schemas_dir / fname)
            if "$schema" not in sch:
                errors.append(f"{fname} missing $schema")
        except ValueError as e:
            errors.append(str(e))

    template_expectations = {
        "ls_intent_v1.template.json": "ls_intent_v1",
        "ls_plan_v1.template.json": "ls_plan_v1",
        "ls_config_v1.template.json": "ls_config_v1",
    }
    for fname, expected_schema in template_expectations.items():
        try:
            t = _read_json(templates_dir / fname)
            if t.get("schema") != expected_schema:
                errors.append(f"{fname} must have schema '{expected_schema}'")
        except ValueError as e:
            errors.append(str(e))

    return errors


def main() -> int:
    errs = validate_skill()
    if errs:
        for e in errs:
            print(f"error: {e}", file=sys.stderr)
        return 1
    print("ok: ls assets/config validate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
