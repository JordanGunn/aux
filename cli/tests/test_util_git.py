"""Tests for aux.util.git — the git log primitive used by history-aware skills."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from aux.util.git import (
    CommitRecord,
    GitLogResult,
    NumstatCommitRecord,
    GitNumstatResult,
    _parse_log_output,
    _parse_numstat_log_output,
    _reject_flag_like,
    git_log_file_changes,
    git_log_numstat,
)


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _git(repo: Path, *args: str, env: dict[str, str] | None = None) -> None:
    """Run git in a test repo with a fixed author + committer identity."""
    full_env = os.environ.copy()
    full_env.update(
        {
            "GIT_AUTHOR_NAME": "Test",
            "GIT_AUTHOR_EMAIL": "test@example.com",
            "GIT_COMMITTER_NAME": "Test",
            "GIT_COMMITTER_EMAIL": "test@example.com",
            "GIT_AUTHOR_DATE": "2026-01-15T12:00:00+00:00",
            "GIT_COMMITTER_DATE": "2026-01-15T12:00:00+00:00",
        }
    )
    if env:
        full_env.update(env)
    subprocess.run(
        ["git", *args],
        cwd=repo,
        env=full_env,
        check=True,
        capture_output=True,
    )


def _init_repo(path: Path) -> Path:
    """Initialise an empty git repo at path and return it."""
    path.mkdir(parents=True, exist_ok=True)
    _git(path, "init", "-q", "-b", "main")
    _git(path, "config", "user.email", "test@example.com")
    _git(path, "config", "user.name", "Test")
    return path


def _commit(repo: Path, files: dict[str, str], message: str, date: str) -> None:
    """Write files and create a commit with a fixed date.

    files: relative-path -> content mapping.
    date: ISO 8601 string passed via GIT_*_DATE.
    """
    for rel, content in files.items():
        target = repo / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        _git(repo, "add", rel)
    env = {
        "GIT_AUTHOR_DATE": date,
        "GIT_COMMITTER_DATE": date,
    }
    _git(repo, "commit", "-q", "-m", message, env=env)


# ---------------------------------------------------------------------------
# 1. Basic log parsing
# ---------------------------------------------------------------------------


def test_empty_repo_returns_empty_commits(tmp_path: Path):
    repo = _init_repo(tmp_path / "empty")
    result = git_log_file_changes(repo)
    assert result.ok is True
    assert result.commits == ()
    assert result.repo_root == repo
    assert result.is_shallow is False


def test_single_commit_single_file(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    _commit(repo, {"a.py": "print(1)\n"}, "add a", "2026-03-01T00:00:00+00:00")
    result = git_log_file_changes(repo)
    assert result.ok is True
    assert len(result.commits) == 1
    c = result.commits[0]
    assert c.files_changed == ("a.py",)
    assert c.parent_count == 0  # root commit
    assert c.author_date.startswith("2026-03-01")


def test_multiple_commits_multiple_files(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    _commit(repo, {"a.py": "1\n"}, "c1", "2026-03-01T00:00:00+00:00")
    _commit(repo, {"b.py": "1\n", "c.py": "1\n"}, "c2", "2026-03-02T00:00:00+00:00")
    _commit(repo, {"a.py": "2\n"}, "c3", "2026-03-03T00:00:00+00:00")
    result = git_log_file_changes(repo)
    assert result.ok is True
    assert len(result.commits) == 3
    # Newest first (git log default)
    assert result.commits[0].files_changed == ("a.py",)
    assert set(result.commits[1].files_changed) == {"b.py", "c.py"}
    assert result.commits[2].files_changed == ("a.py",)
    # Parent counts: root=0, later=1
    assert result.commits[2].parent_count == 0
    assert result.commits[1].parent_count == 1
    assert result.commits[0].parent_count == 1


def test_merge_commit_excluded_by_default(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    _commit(repo, {"a.py": "1\n"}, "base", "2026-03-01T00:00:00+00:00")
    _git(repo, "checkout", "-q", "-b", "feature")
    _commit(repo, {"b.py": "1\n"}, "feature-side", "2026-03-02T00:00:00+00:00")
    _git(repo, "checkout", "-q", "main")
    _commit(repo, {"c.py": "1\n"}, "main-side", "2026-03-02T00:00:00+00:00")
    _git(
        repo,
        "merge",
        "--no-ff",
        "feature",
        "-m",
        "merge feature",
        env={
            "GIT_AUTHOR_DATE": "2026-03-03T00:00:00+00:00",
            "GIT_COMMITTER_DATE": "2026-03-03T00:00:00+00:00",
        },
    )
    result = git_log_file_changes(repo)
    assert result.ok is True
    # Merge excluded: 3 non-merge commits
    assert len(result.commits) == 3
    assert all(c.parent_count <= 1 for c in result.commits)


def test_include_merges_flag(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    _commit(repo, {"a.py": "1\n"}, "base", "2026-03-01T00:00:00+00:00")
    _git(repo, "checkout", "-q", "-b", "feature")
    _commit(repo, {"b.py": "1\n"}, "feature-side", "2026-03-02T00:00:00+00:00")
    _git(repo, "checkout", "-q", "main")
    _commit(repo, {"c.py": "1\n"}, "main-side", "2026-03-02T00:00:00+00:00")
    _git(
        repo,
        "merge",
        "--no-ff",
        "feature",
        "-m",
        "merge feature",
        env={
            "GIT_AUTHOR_DATE": "2026-03-03T00:00:00+00:00",
            "GIT_COMMITTER_DATE": "2026-03-03T00:00:00+00:00",
        },
    )
    result = git_log_file_changes(repo, include_merges=True)
    assert result.ok is True
    # 3 normal + 1 merge
    assert len(result.commits) == 4
    merges = [c for c in result.commits if c.parent_count >= 2]
    assert len(merges) == 1


# ---------------------------------------------------------------------------
# 2. Filtering
# ---------------------------------------------------------------------------


def test_since_filter_excludes_old_commits(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    _commit(repo, {"old.py": "1\n"}, "old", "2020-01-01T00:00:00+00:00")
    _commit(repo, {"new.py": "1\n"}, "new", "2026-03-01T00:00:00+00:00")
    result = git_log_file_changes(repo, since="2025-01-01")
    assert result.ok is True
    files = [f for c in result.commits for f in c.files_changed]
    assert "new.py" in files
    assert "old.py" not in files


def test_until_filter_excludes_newer_commits(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    _commit(repo, {"old.py": "1\n"}, "old", "2020-01-01T00:00:00+00:00")
    _commit(repo, {"new.py": "1\n"}, "new", "2026-03-01T00:00:00+00:00")
    result = git_log_file_changes(repo, until="2024-01-01")
    assert result.ok is True
    files = [f for c in result.commits for f in c.files_changed]
    assert "old.py" in files
    assert "new.py" not in files


def test_since_and_until_bound_window(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    _commit(repo, {"a.py": "1\n"}, "a", "2020-01-01T00:00:00+00:00")
    _commit(repo, {"b.py": "1\n"}, "b", "2023-06-01T00:00:00+00:00")
    _commit(repo, {"c.py": "1\n"}, "c", "2026-03-01T00:00:00+00:00")
    result = git_log_file_changes(repo, since="2022-01-01", until="2024-01-01")
    assert result.ok is True
    files = [f for c in result.commits for f in c.files_changed]
    assert files == ["b.py"]


def test_paths_scoping(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    _commit(repo, {"src/a.py": "1\n", "docs/a.md": "x\n"}, "c1", "2026-03-01T00:00:00+00:00")
    _commit(repo, {"src/b.py": "1\n"}, "c2", "2026-03-02T00:00:00+00:00")
    _commit(repo, {"docs/b.md": "x\n"}, "c3", "2026-03-03T00:00:00+00:00")
    result = git_log_file_changes(repo, paths=["src"])
    assert result.ok is True
    files = sorted({f for c in result.commits for f in c.files_changed})
    assert files == ["src/a.py", "src/b.py"]


# ---------------------------------------------------------------------------
# 3. Error modes
# ---------------------------------------------------------------------------


def test_not_a_git_repo_returns_not_ok(tmp_path: Path):
    non_repo = tmp_path / "plain"
    non_repo.mkdir()
    (non_repo / "a.py").write_text("x\n")
    result = git_log_file_changes(non_repo)
    assert result.ok is False
    assert result.repo_root is None
    assert result.commits == ()
    assert any("not a git repository" in e for e in result.errors)


def test_since_rejects_leading_dash(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    with pytest.raises(ValueError, match="since"):
        git_log_file_changes(repo, since="--upload-pack=/tmp/evil")


def test_until_rejects_leading_dash(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    with pytest.raises(ValueError, match="until"):
        git_log_file_changes(repo, until="-malicious")


def test_paths_rejects_leading_dash_element(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    with pytest.raises(ValueError, match="paths"):
        git_log_file_changes(repo, paths=["src", "-evil"])


def test_reject_flag_like_unit():
    with pytest.raises(ValueError, match="field"):
        _reject_flag_like("-bad", "field")
    # Non-dash values pass through without raising
    _reject_flag_like("90 days ago", "field")
    _reject_flag_like("2025-01-01", "field")


# ---------------------------------------------------------------------------
# 4. Edge cases
# ---------------------------------------------------------------------------


def test_filename_with_spaces(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    _commit(repo, {"my file.py": "1\n"}, "c1", "2026-03-01T00:00:00+00:00")
    result = git_log_file_changes(repo)
    assert result.ok is True
    assert len(result.commits) == 1
    # git may quote-wrap the name if core.quotePath is default; accept either form
    files = result.commits[0].files_changed
    assert len(files) == 1
    assert "my file.py" in files[0] or "my\\ file.py" in files[0] or '"my file.py"' in files[0]


def test_deleted_file_still_in_log(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    _commit(repo, {"temp.py": "1\n"}, "create", "2026-03-01T00:00:00+00:00")
    (repo / "temp.py").unlink()
    _git(repo, "add", "-A")
    _git(
        repo,
        "commit",
        "-q",
        "-m",
        "delete temp",
        env={
            "GIT_AUTHOR_DATE": "2026-03-02T00:00:00+00:00",
            "GIT_COMMITTER_DATE": "2026-03-02T00:00:00+00:00",
        },
    )
    result = git_log_file_changes(repo)
    assert result.ok is True
    assert len(result.commits) == 2
    # temp.py appears in both: creation and deletion
    all_files = [f for c in result.commits for f in c.files_changed]
    assert all_files.count("temp.py") == 2


def test_subdirectory_cwd_resolves_repo_root(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    _commit(repo, {"src/a.py": "1\n"}, "c1", "2026-03-01T00:00:00+00:00")
    # Pass a subdirectory as cwd
    sub = repo / "src"
    result = git_log_file_changes(sub)
    assert result.ok is True
    assert result.repo_root == repo
    assert len(result.commits) == 1
    # Files are repo-root-relative, not cwd-relative
    assert result.commits[0].files_changed == ("src/a.py",)


# ---------------------------------------------------------------------------
# 5. Parser unit tests (no subprocess)
# ---------------------------------------------------------------------------


def test_parse_empty_output():
    assert _parse_log_output("") == []


def test_parse_single_commit():
    output = "\x1eabc123\x1f2026-03-01T00:00:00+00:00\x1f\nfile1.py\n"
    records = _parse_log_output(output)
    assert len(records) == 1
    assert records[0].commit_hash == "abc123"
    assert records[0].author_date == "2026-03-01T00:00:00+00:00"
    assert records[0].parent_count == 0
    assert records[0].files_changed == ("file1.py",)


def test_parse_two_commits():
    output = (
        "\x1ea1\x1f2026-03-01T00:00:00+00:00\x1fp1\nfile_a.py\nfile_b.py\n"
        "\x1ea2\x1f2026-03-02T00:00:00+00:00\x1fp2 p3\nfile_c.py\n"
    )
    records = _parse_log_output(output)
    assert len(records) == 2
    assert records[0].parent_count == 1
    assert records[1].parent_count == 2  # merge
    assert records[0].files_changed == ("file_a.py", "file_b.py")
    assert records[1].files_changed == ("file_c.py",)


def test_parse_skips_malformed_header():
    output = "\x1eonly_one_field\nfile_a.py\n"
    records = _parse_log_output(output)
    assert records == []


# ---------------------------------------------------------------------------
# 6. Numstat parser unit tests (no subprocess)
# ---------------------------------------------------------------------------


def test_parse_numstat_empty_output():
    assert _parse_numstat_log_output("") == []


def test_parse_numstat_single_commit():
    output = "\x1eabc123\x1f2026-03-01T00:00:00+00:00\x1f\n3\t1\tfile.py\n"
    records = _parse_numstat_log_output(output)
    assert len(records) == 1
    assert records[0].commit_hash == "abc123"
    assert len(records[0].files) == 1
    assert records[0].files[0].file == "file.py"
    assert records[0].files[0].insertions == 3
    assert records[0].files[0].deletions == 1


def test_parse_numstat_two_commits():
    output = (
        "\x1ea1\x1f2026-03-01T00:00:00+00:00\x1fp1\n5\t2\tfile_a.py\n10\t0\tfile_b.py\n"
        "\x1ea2\x1f2026-03-02T00:00:00+00:00\x1fp2 p3\n1\t1\tfile_c.py\n"
    )
    records = _parse_numstat_log_output(output)
    assert len(records) == 2
    assert len(records[0].files) == 2
    assert records[0].files[0].insertions == 5
    assert records[0].files[0].deletions == 2
    assert records[0].files[1].insertions == 10
    assert records[0].files[1].deletions == 0
    assert len(records[1].files) == 1


def test_parse_numstat_binary_file():
    output = "\x1eabc\x1f2026-03-01T00:00:00+00:00\x1f\n-\t-\timage.png\n"
    records = _parse_numstat_log_output(output)
    assert len(records) == 1
    assert records[0].files[0].file == "image.png"
    assert records[0].files[0].insertions == 0
    assert records[0].files[0].deletions == 0


def test_parse_numstat_malformed_skipped():
    output = "\x1eonly_one_field\n3\t1\tfile.py\n"
    records = _parse_numstat_log_output(output)
    assert records == []


# ---------------------------------------------------------------------------
# 7. Numstat integration tests
# ---------------------------------------------------------------------------


def test_numstat_single_commit(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    _commit(repo, {"a.py": "line1\nline2\nline3\n"}, "add a", "2026-03-01T00:00:00+00:00")
    result = git_log_numstat(repo)
    assert result.ok is True
    assert len(result.commits) == 1
    c = result.commits[0]
    assert len(c.files) == 1
    assert c.files[0].file == "a.py"
    assert c.files[0].insertions == 3
    assert c.files[0].deletions == 0


def test_numstat_multiple_commits(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    _commit(repo, {"a.py": "line1\n"}, "c1", "2026-03-01T00:00:00+00:00")
    _commit(repo, {"a.py": "line1\nline2\nline3\n"}, "c2", "2026-03-02T00:00:00+00:00")
    result = git_log_numstat(repo)
    assert result.ok is True
    assert len(result.commits) == 2
    # Newest first: c2 added 2 lines, deleted 0
    c2 = result.commits[0]
    assert c2.files[0].file == "a.py"
    assert c2.files[0].insertions == 2
    assert c2.files[0].deletions == 0
    # c1 added 1 line
    c1 = result.commits[1]
    assert c1.files[0].insertions == 1


def test_numstat_since_filter(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    _commit(repo, {"old.py": "1\n"}, "old", "2020-01-01T00:00:00+00:00")
    _commit(repo, {"new.py": "1\n"}, "new", "2026-03-01T00:00:00+00:00")
    result = git_log_numstat(repo, since="2025-01-01")
    assert result.ok is True
    files = [f.file for c in result.commits for f in c.files]
    assert "new.py" in files
    assert "old.py" not in files


def test_numstat_not_a_repo(tmp_path: Path):
    plain = tmp_path / "plain"
    plain.mkdir()
    result = git_log_numstat(plain)
    assert result.ok is False
    assert any("not a git repository" in e for e in result.errors)


def test_numstat_flag_injection_rejected(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    with pytest.raises(ValueError, match="since"):
        git_log_numstat(repo, since="--upload-pack=/tmp/evil")
