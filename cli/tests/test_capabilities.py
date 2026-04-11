"""Tests for aux capabilities command."""

from __future__ import annotations

import json

import pytest

from aux.cli import create_parser


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(argv: list[str]) -> tuple[int, str]:
    """Run the CLI with captured stdout, return (exit_code, output)."""
    import io
    from contextlib import redirect_stdout

    parser = create_parser()
    args = parser.parse_args(argv)

    buf = io.StringIO()
    with redirect_stdout(buf):
        assert hasattr(args, "func"), f"No func for {argv}"
        rc = args.func(args)

    return rc, buf.getvalue()


# ---------------------------------------------------------------------------
# Registry structure
# ---------------------------------------------------------------------------

def test_capabilities_exits_zero():
    rc, _ = _run(["capabilities"])
    assert rc == 0


def test_capabilities_emits_valid_json():
    _, output = _run(["capabilities"])
    data = json.loads(output)
    assert isinstance(data, dict)


def test_capabilities_has_version():
    _, output = _run(["capabilities"])
    data = json.loads(output)
    assert "version" in data
    assert isinstance(data["version"], str)


def test_capabilities_has_skills_list():
    _, output = _run(["capabilities"])
    data = json.loads(output)
    assert "skills" in data
    assert isinstance(data["skills"], list)


def test_capabilities_has_exactly_14_skills():
    _, output = _run(["capabilities"])
    data = json.loads(output)
    assert len(data["skills"]) == 14, f"Expected 14 skills, got {len(data['skills'])}"


def test_capabilities_has_composition_note():
    _, output = _run(["capabilities"])
    data = json.loads(output)
    assert "composition_note" in data
    assert isinstance(data["composition_note"], str)


# ---------------------------------------------------------------------------
# Required keys on each skill entry
# ---------------------------------------------------------------------------

REQUIRED_KEYS = [
    "name",
    "description",
    "category",
    "intent_signals",
    "requires",
    "optional_deps",
    "compose_with",
    "mutates",
    "schema_cmd",
]


def test_each_skill_has_required_keys():
    _, output = _run(["capabilities"])
    data = json.loads(output)
    for skill in data["skills"]:
        for key in REQUIRED_KEYS:
            assert key in skill, f"Key '{key}' missing from skill '{skill.get('name', '?')}'"


def test_intent_signals_is_non_empty_list():
    _, output = _run(["capabilities"])
    data = json.loads(output)
    for skill in data["skills"]:
        assert isinstance(skill["intent_signals"], list), f"{skill['name']}: intent_signals not a list"
        assert len(skill["intent_signals"]) >= 1, f"{skill['name']}: intent_signals is empty"


def test_category_values_are_valid():
    valid_categories = {"read", "write", "analysis", "network", "meta"}
    _, output = _run(["capabilities"])
    data = json.loads(output)
    for skill in data["skills"]:
        assert skill["category"] in valid_categories, (
            f"{skill['name']}: invalid category '{skill['category']}'"
        )


# ---------------------------------------------------------------------------
# Mutates flag
# ---------------------------------------------------------------------------

def test_only_replace_and_rename_mutate():
    _, output = _run(["capabilities"])
    data = json.loads(output)
    writers = {s["name"] for s in data["skills"] if s["mutates"]}
    assert writers == {"replace", "rename"}, f"Wrong mutates set: {writers}"


def test_read_analysis_network_skills_do_not_mutate():
    _, output = _run(["capabilities"])
    data = json.loads(output)
    for skill in data["skills"]:
        if skill["category"] in ("read", "analysis", "network"):
            assert not skill["mutates"], f"{skill['name']}: read/analysis/network skill has mutates=True"


# ---------------------------------------------------------------------------
# Skill names
# ---------------------------------------------------------------------------

EXPECTED_SKILL_NAMES = {
    "files", "search", "find", "replace", "rename",
    "curl", "usages", "prune", "deps", "delta", "robert", "ccx", "ck", "hotspots",
}


def test_expected_skill_names_present():
    _, output = _run(["capabilities"])
    data = json.loads(output)
    names = {s["name"] for s in data["skills"]}
    assert names == EXPECTED_SKILL_NAMES, f"Unexpected skills: {names.symmetric_difference(EXPECTED_SKILL_NAMES)}"


# ---------------------------------------------------------------------------
# --format names
# ---------------------------------------------------------------------------

def test_format_names_exits_zero():
    rc, _ = _run(["capabilities", "--format", "names"])
    assert rc == 0


def test_format_names_emits_json_list():
    _, output = _run(["capabilities", "--format", "names"])
    data = json.loads(output)
    assert isinstance(data, list)


def test_format_names_contains_all_skills():
    _, output = _run(["capabilities", "--format", "names"])
    data = json.loads(output)
    assert set(data) == EXPECTED_SKILL_NAMES


def test_format_names_contains_only_strings():
    _, output = _run(["capabilities", "--format", "names"])
    data = json.loads(output)
    assert all(isinstance(n, str) for n in data)
