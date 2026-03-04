"""Tests for aux rename discovery mode."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError

from aux.plans.schemas import MovePair, RenamePlan, RenameRule


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------


def test_explicit_mode_valid():
    plan = RenamePlan(moves=[MovePair(src="/a/old.py", dst="/a/new.py")])
    assert plan.moves is not None
    assert plan.root is None
    assert plan.rules is None


def test_discovery_mode_valid():
    plan = RenamePlan(
        root="/some/root",
        rules=[RenameRule(find="reader", replace="source")],
        globs=["pipeline/**"],
    )
    assert plan.moves is None
    assert plan.root == "/some/root"
    assert plan.rules is not None


def test_neither_moves_nor_rules_raises():
    with pytest.raises(ValidationError, match="Either 'moves'.*or 'root'.*'rules'"):
        RenamePlan()


def test_only_root_no_rules_raises():
    with pytest.raises(ValidationError, match="Either 'moves'.*or 'root'.*'rules'"):
        RenamePlan(root="/some/root")


def test_only_rules_no_root_raises():
    with pytest.raises(ValidationError, match="Either 'moves'.*or 'root'.*'rules'"):
        RenamePlan(rules=[RenameRule(find="reader", replace="source")])


def test_both_moves_and_discovery_raises():
    with pytest.raises(ValidationError, match="not both"):
        RenamePlan(
            moves=[MovePair(src="/a/old.py", dst="/a/new.py")],
            root="/some/root",
            rules=[RenameRule(find="reader", replace="source")],
        )


def test_globs_without_root_raises():
    with pytest.raises(ValidationError, match="'globs' and 'excludes' require 'root'"):
        RenamePlan(
            moves=[MovePair(src="/a/old.py", dst="/a/new.py")],
            globs=["**/*.py"],
        )


def test_excludes_without_root_raises():
    with pytest.raises(ValidationError, match="'globs' and 'excludes' require 'root'"):
        RenamePlan(
            moves=[MovePair(src="/a/old.py", dst="/a/new.py")],
            excludes=["*.bak"],
        )


# ---------------------------------------------------------------------------
# Rule application logic (unit — no filesystem needed)
# ---------------------------------------------------------------------------


def _apply_rules(name: str, rules: list[RenameRule]) -> str:
    """Mirror of the rule application logic in _discover_moves."""
    import re

    new_name = name
    for rule in rules:
        if rule.regex:
            new_name = re.sub(rule.find, rule.replace, new_name)
        else:
            new_name = new_name.replace(rule.find, rule.replace)
    return new_name


def test_literal_replace():
    rules = [RenameRule(find="reader", replace="source")]
    assert _apply_rules("event_reader.py", rules) == "event_source.py"


def test_literal_replace_writer():
    rules = [RenameRule(find="writer", replace="sink")]
    assert _apply_rules("batch_writer.py", rules) == "batch_sink.py"


def test_regex_replace():
    rules = [RenameRule(find=r"^read_", replace="source_", regex=True)]
    assert _apply_rules("read_worker.py", rules) == "source_worker.py"


def test_no_match_returns_original():
    rules = [RenameRule(find="reader", replace="source")]
    assert _apply_rules("config_loader.py", rules) == "config_loader.py"


def test_multiple_rules_applied_in_order():
    rules = [
        RenameRule(find="read_worker", replace="source_worker"),
        RenameRule(find="write_worker", replace="sink_worker"),
    ]
    assert _apply_rules("read_worker.py", rules) == "source_worker.py"
    assert _apply_rules("write_worker.py", rules) == "sink_worker.py"


def test_regex_capture_group():
    rules = [RenameRule(find=r"^(batch|event)_reader", replace=r"\1_source", regex=True)]
    assert _apply_rules("batch_reader.py", rules) == "batch_source.py"
    assert _apply_rules("event_reader.py", rules) == "event_source.py"


# ---------------------------------------------------------------------------
# Integration test — discovery mode against a real directory tree
# ---------------------------------------------------------------------------


FIXTURE_ROOT = (
    Path(__file__).parent.parent.parent
    / "docs/benchmark/fixtures/rename_inference/fixture/platform"
)

# Files that should be renamed (in pipeline/, connectors/, workers/)
EXPECTED_RENAMES = {
    # pipeline
    "pipeline/batch_reader.py": "pipeline/batch_source.py",
    "pipeline/batch_writer.py": "pipeline/batch_sink.py",
    "pipeline/event_reader.py": "pipeline/event_source.py",
    "pipeline/event_writer.py": "pipeline/event_sink.py",
    "pipeline/stream_reader.py": "pipeline/stream_source.py",
    # connectors
    "connectors/db_reader.py": "connectors/db_source.py",
    "connectors/db_writer.py": "connectors/db_sink.py",
    "connectors/kafka_reader.py": "connectors/kafka_source.py",
    "connectors/kafka_writer.py": "connectors/kafka_sink.py",
    "connectors/s3_reader.py": "connectors/s3_source.py",
    # workers
    "workers/read_worker.py": "workers/source_worker.py",
    "workers/write_worker.py": "workers/sink_worker.py",
}

# Files that must NOT be renamed (decoys outside scoped directories)
DECOYS = [
    "utils/config_reader.py",
    "utils/log_writer.py",
    "auth/token_reader.py",
    "api/request_reader.py",
    "cli/output_writer.py",
]

DISCOVERY_RULES = [
    RenameRule(find="read_worker", replace="source_worker"),
    RenameRule(find="write_worker", replace="sink_worker"),
    RenameRule(find="reader", replace="source"),
    RenameRule(find="writer", replace="sink"),
]

DISCOVERY_GLOBS = ["pipeline/**", "connectors/**", "workers/**"]


@pytest.fixture()
def workspace(tmp_path: Path) -> Path:
    """Copy fixture into a temp dir and return the platform root."""
    if not FIXTURE_ROOT.exists():
        pytest.skip(f"Fixture not found: {FIXTURE_ROOT}")
    shutil.copytree(FIXTURE_ROOT, tmp_path / "platform")
    return tmp_path / "platform"


def test_discover_moves_generates_correct_pairs(workspace: Path):
    """Discovery mode must generate exactly the 12 expected renames."""
    from aux.commands.rename import _discover_moves

    plan = RenamePlan(
        root=str(workspace),
        globs=DISCOVERY_GLOBS,
        rules=DISCOVERY_RULES,
    )
    pairs = _discover_moves(plan)

    # Map relative paths for easy assertion
    rel_pairs = {
        str(src.relative_to(workspace)): str(dst.relative_to(workspace))
        for src, dst in pairs
    }

    assert rel_pairs == EXPECTED_RENAMES, (
        f"Unexpected pairs.\nGot: {rel_pairs}\nExpected: {EXPECTED_RENAMES}"
    )


def test_discover_moves_skips_decoys(workspace: Path):
    """Decoy files outside scoped directories must not appear in pairs."""
    from aux.commands.rename import _discover_moves

    plan = RenamePlan(
        root=str(workspace),
        globs=DISCOVERY_GLOBS,
        rules=DISCOVERY_RULES,
    )
    pairs = _discover_moves(plan)

    moved_srcs = {str(src.relative_to(workspace)) for src, _ in pairs}
    for decoy in DECOYS:
        assert decoy not in moved_srcs, f"Decoy was included in renames: {decoy}"


def test_dry_run_then_apply(workspace: Path):
    """Full two-phase workflow: dry-run preview + apply verifies filesystem state."""
    from aux.kernels.mv import mv_kernel
    from aux.commands.rename import _discover_moves

    plan = RenamePlan(
        root=str(workspace),
        globs=DISCOVERY_GLOBS,
        rules=DISCOVERY_RULES,
    )
    pairs = _discover_moves(plan)
    assert len(pairs) == 12

    # Phase 1: dry-run
    dry = mv_kernel(pairs, apply=False)
    assert dry.total_applied == 0
    assert not dry.errors

    # Phase 2: apply
    result = mv_kernel(pairs, apply=True)
    assert result.total_applied == 12
    assert not result.errors

    # Verify new paths exist
    for src_rel, dst_rel in EXPECTED_RENAMES.items():
        assert (workspace / dst_rel).exists(), f"Expected renamed file missing: {dst_rel}"
        assert not (workspace / src_rel).exists(), f"Old file still present: {src_rel}"

    # Verify decoys untouched
    for decoy in DECOYS:
        assert (workspace / decoy).exists(), f"Decoy was unexpectedly moved: {decoy}"
