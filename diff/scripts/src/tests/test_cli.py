#!/usr/bin/env python3
"""Minimal tests for /diff skill determinism, bounds, and edge cases."""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest


SCRIPT_DIR = Path(__file__).parent.parent.resolve()
CLI_PATH = SCRIPT_DIR / "cli.py"


def run_cli(args: list[str], stdin_data: str | None = None, cwd: str | None = None) -> tuple[int, str, str]:
    """Run cli.py with given args and optional stdin."""
    cmd = ["python", str(CLI_PATH)] + args
    result = subprocess.run(
        cmd,
        input=stdin_data,
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=30,
    )
    return result.returncode, result.stdout, result.stderr


class TestValidate:
    """Tests for the validate command."""

    def test_validate_passes(self):
        """Validate should pass when all assets exist."""
        code, stdout, stderr = run_cli(["validate"])
        assert code == 0
        assert "ok" in stdout.lower()


class TestNonGitDirectory:
    """Tests for non-git directory handling."""

    def test_discover_non_git_returns_error(self):
        """Discovery in non-git directory should return error status."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan = {"root": tmpdir, "scope": {"mode": "working_tree"}}
            code, stdout, stderr = run_cli(
                ["discover", "--stdin"],
                stdin_data=json.dumps(plan),
            )
            assert code == 1
            result = json.loads(stdout)
            assert result["status"] == "error"
            assert "not a git" in result.get("error", "").lower()

    def test_run_non_git_returns_error(self):
        """Run in non-git directory should return error status."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan = {
                "root": tmpdir,
                "surface": "git",
                "scope": {"comparison": "working_tree_vs_index"},
                "mode": "summary_only",
                "bounds": {"max_files": 10},
            }
            code, stdout, stderr = run_cli(
                ["run", "--stdin"],
                stdin_data=json.dumps(plan),
            )
            assert code == 1
            result = json.loads(stdout)
            assert result["status"] == "error"


class TestCleanRepository:
    """Tests for clean repository (no changes) handling."""

    def test_run_clean_repo_returns_zero_changes(self):
        """Run on clean repo should return zero files changed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
            subprocess.run(
                ["git", "config", "user.email", "test@test.com"],
                cwd=tmpdir,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test"],
                cwd=tmpdir,
                capture_output=True,
            )
            Path(tmpdir, "README.md").write_text("# Test")
            subprocess.run(["git", "add", "."], cwd=tmpdir, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", "init"],
                cwd=tmpdir,
                capture_output=True,
            )

            plan = {
                "root": tmpdir,
                "surface": "git",
                "scope": {"comparison": "working_tree_vs_index"},
                "mode": "summary_only",
                "bounds": {"max_files": 10},
            }
            code, stdout, stderr = run_cli(
                ["run", "--stdin"],
                stdin_data=json.dumps(plan),
            )
            assert code == 0
            result = json.loads(stdout)
            assert result["summary"]["files_changed"] == 0


class TestBoundsEnforcement:
    """Tests for bounds enforcement."""

    def test_max_files_truncates(self):
        """Run should truncate when exceeding max_files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
            subprocess.run(
                ["git", "config", "user.email", "test@test.com"],
                cwd=tmpdir,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test"],
                cwd=tmpdir,
                capture_output=True,
            )

            for i in range(5):
                Path(tmpdir, f"file{i}.txt").write_text(f"content {i}")

            subprocess.run(["git", "add", "."], cwd=tmpdir, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", "init"],
                cwd=tmpdir,
                capture_output=True,
            )

            for i in range(5):
                Path(tmpdir, f"file{i}.txt").write_text(f"modified {i}")

            plan = {
                "root": tmpdir,
                "surface": "git",
                "scope": {"comparison": "working_tree_vs_index"},
                "mode": "summary_only",
                "bounds": {"max_files": 2},
            }
            code, stdout, stderr = run_cli(
                ["run", "--stdin"],
                stdin_data=json.dumps(plan),
            )
            assert code == 0
            result = json.loads(stdout)
            assert result["summary"]["files_changed"] <= 2
            assert result["summary"]["truncated"] is True


class TestDeterminism:
    """Tests for deterministic output."""

    def test_same_input_same_output(self):
        """Same input should produce same output (determinism)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
            subprocess.run(
                ["git", "config", "user.email", "test@test.com"],
                cwd=tmpdir,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test"],
                cwd=tmpdir,
                capture_output=True,
            )
            Path(tmpdir, "test.txt").write_text("hello")
            subprocess.run(["git", "add", "."], cwd=tmpdir, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", "init"],
                cwd=tmpdir,
                capture_output=True,
            )
            Path(tmpdir, "test.txt").write_text("hello world")

            plan = {
                "root": tmpdir,
                "surface": "git",
                "scope": {"comparison": "working_tree_vs_index"},
                "mode": "summary_only",
                "bounds": {"max_files": 10},
            }
            plan_json = json.dumps(plan)

            _, stdout1, _ = run_cli(["run", "--stdin"], stdin_data=plan_json)
            _, stdout2, _ = run_cli(["run", "--stdin"], stdin_data=plan_json)

            result1 = json.loads(stdout1)
            result2 = json.loads(stdout2)

            assert result1["summary"]["files_changed"] == result2["summary"]["files_changed"]
            assert result1["summary"]["insertions"] == result2["summary"]["insertions"]
            assert result1["summary"]["deletions"] == result2["summary"]["deletions"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
