"""Tests for aux hotspots — churn-weighted complexity scoring."""

from __future__ import annotations

import io
import json
import os
import subprocess
from contextlib import redirect_stdout
from pathlib import Path

import pytest
from pydantic import ValidationError

from aux.cli import create_parser
from aux.kernels.hotspots import (
    FileHotspot,
    HotspotsResult,
    _assign_quadrants,
    _interpret_hotspot,
    _percentile_cutoff,
    hotspots_kernel,
)
from aux.plans.schemas import HotspotsPlan


def _run(argv: list[str]) -> tuple[int, str]:
    """Run the CLI with captured stdout, return (exit_code, output)."""
    parser = create_parser()
    args = parser.parse_args(argv)
    buf = io.StringIO()
    with redirect_stdout(buf):
        assert hasattr(args, "func"), f"No func for {argv}"
        rc = args.func(args)
    return rc, buf.getvalue()


# ---------------------------------------------------------------------------
# Fixture helpers — tmp git repo with controlled commit dates
# ---------------------------------------------------------------------------


def _git(repo: Path, *args: str, env: dict[str, str] | None = None) -> None:
    """Run git in a test repo with a fixed identity."""
    full_env = os.environ.copy()
    full_env.update(
        {
            "GIT_AUTHOR_NAME": "Test",
            "GIT_AUTHOR_EMAIL": "test@example.com",
            "GIT_COMMITTER_NAME": "Test",
            "GIT_COMMITTER_EMAIL": "test@example.com",
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
    path.mkdir(parents=True, exist_ok=True)
    _git(path, "init", "-q", "-b", "main")
    _git(path, "config", "user.email", "test@example.com")
    _git(path, "config", "user.name", "Test")
    return path


def _commit(repo: Path, files: dict[str, str], message: str, date: str) -> None:
    for rel, content in files.items():
        target = repo / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        _git(repo, "add", rel)
    env = {"GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date}
    _git(repo, "commit", "-q", "-m", message, env=env)


# Python source snippets with known ccx values
_SIMPLE_PY = """\
def add(a, b):
    return a + b
"""  # ccx=1

_COMPLEX_PY = """\
def classify(x):
    if x < 0:
        return "negative"
    elif x == 0:
        return "zero"
    elif x < 10:
        return "small"
    elif x < 100:
        return "medium"
    elif x < 1000:
        return "large"
    else:
        return "huge"
"""  # ccx=6 (1 + 5 branches)

_VERY_COMPLEX_PY = """\
def branchy(a, b, c, d):
    if a and b:
        if c or d:
            return 1
        elif c:
            return 2
        else:
            return 3
    elif a:
        for i in range(10):
            if i > 5:
                return i
    else:
        while b:
            if c:
                return 4
            b -= 1
    return 0
"""  # ccx high


# ---------------------------------------------------------------------------
# 1. Schema / plan validation
# ---------------------------------------------------------------------------


def test_hotspots_plan_requires_root():
    with pytest.raises(ValidationError):
        HotspotsPlan()  # type: ignore[call-arg]


def test_hotspots_plan_defaults():
    plan = HotspotsPlan(root="/tmp")
    assert plan.root == "/tmp"
    assert plan.globs == []
    assert plan.excludes == []
    assert plan.hidden is False
    assert plan.no_ignore is False
    assert plan.since == "90 days ago"
    assert plan.until is None
    assert plan.min_commits == 2
    assert plan.max_results is None
    assert plan.hotspot_percentile == 0.75


def test_hotspots_plan_rejects_zero_min_commits():
    with pytest.raises(ValidationError):
        HotspotsPlan(root="/tmp", min_commits=0)


def test_hotspots_plan_rejects_negative_max_results():
    with pytest.raises(ValidationError):
        HotspotsPlan(root="/tmp", max_results=0)


def test_hotspots_plan_rejects_out_of_range_percentile():
    with pytest.raises(ValidationError):
        HotspotsPlan(root="/tmp", hotspot_percentile=0.3)
    with pytest.raises(ValidationError):
        HotspotsPlan(root="/tmp", hotspot_percentile=1.5)


def test_hotspots_plan_accepts_all_sentinel():
    plan = HotspotsPlan(root="/tmp", since="all")
    assert plan.since == "all"


# ---------------------------------------------------------------------------
# 2. Kernel basics
# ---------------------------------------------------------------------------


def test_empty_repo_returns_empty_result(tmp_path: Path):
    repo = _init_repo(tmp_path / "empty")
    result = hotspots_kernel(repo, since=None, min_commits=1)
    assert result.files == []
    assert result.total_commits_analyzed == 0
    assert result.files_analyzed == 0


def test_not_a_git_repo_returns_error(tmp_path: Path):
    plain = tmp_path / "plain"
    plain.mkdir()
    (plain / "a.py").write_text(_SIMPLE_PY)
    result = hotspots_kernel(plain)
    assert result.files == []
    assert any("not a git repository" in e for e in result.errors)


def test_single_complex_file_multiple_commits_ranked_first(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    _commit(repo, {"hot.py": _COMPLEX_PY}, "c1", "2026-03-01T00:00:00+00:00")
    # Touch it twice more
    _commit(
        repo,
        {"hot.py": _COMPLEX_PY + "\n# edit 1\n"},
        "c2",
        "2026-03-02T00:00:00+00:00",
    )
    _commit(
        repo,
        {"hot.py": _COMPLEX_PY + "\n# edit 1\n# edit 2\n"},
        "c3",
        "2026-03-03T00:00:00+00:00",
    )
    result = hotspots_kernel(repo, since=None, min_commits=2)
    assert len(result.files) == 1
    h = result.files[0]
    assert h.file == "hot.py"
    assert h.change_freq == 3
    assert h.sum_ccx >= 6
    assert h.hotspot_score == h.sum_ccx * 3


def test_no_commits_in_window_returns_empty(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    _commit(repo, {"a.py": _SIMPLE_PY}, "c1", "2020-01-01T00:00:00+00:00")
    result = hotspots_kernel(repo, since="2025-01-01", min_commits=1)
    assert result.files == []
    assert result.total_commits_analyzed == 0


def test_min_commits_filter(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    _commit(
        repo,
        {"once.py": _COMPLEX_PY, "twice.py": _COMPLEX_PY},
        "c1",
        "2026-03-01T00:00:00+00:00",
    )
    _commit(
        repo,
        {"twice.py": _COMPLEX_PY + "\n# edit\n"},
        "c2",
        "2026-03-02T00:00:00+00:00",
    )
    result = hotspots_kernel(repo, since=None, min_commits=2)
    # once.py has 1 commit, twice.py has 2 — only twice.py survives
    assert len(result.files) == 1
    assert result.files[0].file == "twice.py"
    assert result.files_excluded_below_min_commits == 1


# ---------------------------------------------------------------------------
# 3. Joining ccx + git
# ---------------------------------------------------------------------------


def test_file_with_no_functions_excluded(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    constants_only = "X = 1\nY = 2\nZ = 'hello'\n"
    _commit(
        repo,
        {"constants.py": constants_only, "code.py": _COMPLEX_PY},
        "c1",
        "2026-03-01T00:00:00+00:00",
    )
    _commit(
        repo,
        {
            "constants.py": constants_only + "W = 3\n",
            "code.py": _COMPLEX_PY + "\n# edit\n",
        },
        "c2",
        "2026-03-02T00:00:00+00:00",
    )
    result = hotspots_kernel(repo, since=None, min_commits=2)
    files = {h.file for h in result.files}
    assert "code.py" in files
    assert "constants.py" not in files
    assert result.files_excluded_no_functions >= 1


def test_unsupported_language_excluded(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    _commit(
        repo,
        {
            "code.py": _COMPLEX_PY,
            "script.sh": "#!/bin/bash\necho hi\n",
        },
        "c1",
        "2026-03-01T00:00:00+00:00",
    )
    _commit(
        repo,
        {
            "code.py": _COMPLEX_PY + "\n# edit\n",
            "script.sh": "#!/bin/bash\necho hello\n",
        },
        "c2",
        "2026-03-02T00:00:00+00:00",
    )
    result = hotspots_kernel(repo, since=None, min_commits=2)
    files = {h.file for h in result.files}
    assert "code.py" in files
    assert "script.sh" not in files
    assert result.files_excluded_unsupported_language >= 1


def test_deleted_file_excluded_not_on_disk(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    _commit(repo, {"temp.py": _COMPLEX_PY}, "c1", "2026-03-01T00:00:00+00:00")
    _commit(
        repo,
        {"temp.py": _COMPLEX_PY + "\n# edit\n"},
        "c2",
        "2026-03-02T00:00:00+00:00",
    )
    (repo / "temp.py").unlink()
    _git(repo, "add", "-A")
    _git(
        repo,
        "commit",
        "-q",
        "-m",
        "delete",
        env={
            "GIT_AUTHOR_DATE": "2026-03-03T00:00:00+00:00",
            "GIT_COMMITTER_DATE": "2026-03-03T00:00:00+00:00",
        },
    )
    result = hotspots_kernel(repo, since=None, min_commits=1)
    assert all(h.file != "temp.py" for h in result.files)
    assert result.files_excluded_not_on_disk >= 1


def test_root_as_subdirectory_of_repo(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    _commit(
        repo,
        {
            "src/code.py": _COMPLEX_PY,
            "docs/notes.md": "hi\n",  # not python, should be ignored
            "other/noise.py": _SIMPLE_PY,  # outside the subdir we analyze
        },
        "c1",
        "2026-03-01T00:00:00+00:00",
    )
    _commit(
        repo,
        {
            "src/code.py": _COMPLEX_PY + "\n# edit\n",
            "other/noise.py": _SIMPLE_PY + "# edit\n",
        },
        "c2",
        "2026-03-02T00:00:00+00:00",
    )
    # Analyze only the src subdirectory
    result = hotspots_kernel(repo / "src", since=None, min_commits=2)
    assert len(result.files) == 1
    h = result.files[0]
    # File path should be repo-root-relative
    assert h.file == "src/code.py"
    assert h.change_freq == 2


# ---------------------------------------------------------------------------
# 4. Quadrant classification
# ---------------------------------------------------------------------------


def _mk_hotspot(
    file: str, sum_ccx: int, change_freq: int
) -> FileHotspot:
    return FileHotspot(
        file=file,
        path=f"/{file}",
        language="python",
        sum_ccx=sum_ccx,
        max_ccx=sum_ccx,
        change_freq=change_freq,
        first_seen="2026-03-01",
        last_seen="2026-03-10",
        hotspot_score=float(sum_ccx * change_freq),
        hotspot_score_normalized=0.0,
        quadrant="calm",
        interpretation="",
    )


def test_percentile_cutoff_inclusive():
    # values = [1,2,3,4,5,6,7,8], p75, n=8
    # idx = ceil(0.75 * 8) - 1 = ceil(6) - 1 = 5 → value at index 5 = 6
    assert _percentile_cutoff([1, 2, 3, 4, 5, 6, 7, 8], 0.75) == 6


def test_quadrants_four_corners():
    hotspots = [
        # "calm" corner: low ccx, low churn (n=4)
        _mk_hotspot("calm1.py", 1, 1),
        _mk_hotspot("calm2.py", 2, 1),
        _mk_hotspot("calm3.py", 1, 2),
        _mk_hotspot("calm4.py", 2, 2),
        # "churning_simple": low ccx, high churn (n=2)
        _mk_hotspot("churn1.py", 1, 50),
        _mk_hotspot("churn2.py", 2, 40),
        # "stable_complex": high ccx, low churn (n=2)
        _mk_hotspot("stable1.py", 100, 1),
        _mk_hotspot("stable2.py", 90, 2),
        # "hotspot": high ccx, high churn (n=2)
        _mk_hotspot("hot1.py", 80, 30),
        _mk_hotspot("hot2.py", 70, 20),
    ]
    counts = _assign_quadrants(hotspots, 0.75)
    # Total files: 10, percentile cutoff should put top ~3 in high-band
    # hotspots must be non-empty, calm must dominate
    assert counts["hotspot"] >= 1
    assert counts["calm"] >= 1
    # Sanity: all quadrants assigned
    total = sum(counts.values())
    assert total == 10
    # Check the obvious hotspot files landed correctly
    by_file = {h.file: h for h in hotspots}
    assert by_file["hot1.py"].quadrant == "hotspot"
    assert by_file["calm1.py"].quadrant == "calm"


def test_small_set_returns_insufficient_data():
    hotspots = [
        _mk_hotspot("a.py", 100, 50),
        _mk_hotspot("b.py", 1, 1),
    ]
    counts = _assign_quadrants(hotspots, 0.75)
    assert counts["insufficient_data"] == 2
    assert counts["hotspot"] == 0
    for h in hotspots:
        assert h.quadrant == "insufficient_data"
        assert "Unclassified" in h.interpretation


def test_interpretation_keyed_to_quadrant():
    h = _mk_hotspot("foo.py", 100, 50)
    h.quadrant = "hotspot"
    assert "Active hotspot" in _interpret_hotspot(h)
    h.quadrant = "stable_complex"
    assert "Stable complex" in _interpret_hotspot(h)
    h.quadrant = "churning_simple"
    assert "Churning simple" in _interpret_hotspot(h)
    h.quadrant = "calm"
    assert "Calm" in _interpret_hotspot(h)


# ---------------------------------------------------------------------------
# 5. Ranking & truncation
# ---------------------------------------------------------------------------


def test_sort_stable_on_score_ties(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    # Two files with identical complexity and churn
    _commit(
        repo,
        {"aaa.py": _COMPLEX_PY, "bbb.py": _COMPLEX_PY},
        "c1",
        "2026-03-01T00:00:00+00:00",
    )
    _commit(
        repo,
        {
            "aaa.py": _COMPLEX_PY + "\n# 1\n",
            "bbb.py": _COMPLEX_PY + "\n# 1\n",
        },
        "c2",
        "2026-03-02T00:00:00+00:00",
    )
    result = hotspots_kernel(repo, since=None, min_commits=2)
    assert len(result.files) == 2
    # Tie broken by file name (asc) — aaa.py should come first
    assert result.files[0].file == "aaa.py"
    assert result.files[1].file == "bbb.py"


def test_max_results_truncates(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    files = {f"f{i}.py": _COMPLEX_PY for i in range(5)}
    _commit(repo, files, "c1", "2026-03-01T00:00:00+00:00")
    files2 = {f"f{i}.py": _COMPLEX_PY + f"\n# {i}\n" for i in range(5)}
    _commit(repo, files2, "c2", "2026-03-02T00:00:00+00:00")
    result = hotspots_kernel(repo, since=None, min_commits=2, max_results=3)
    assert len(result.files) == 3
    assert result.truncated is True


def test_normalized_score_max_is_100(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    _commit(
        repo,
        {"big.py": _VERY_COMPLEX_PY, "small.py": _SIMPLE_PY},
        "c1",
        "2026-03-01T00:00:00+00:00",
    )
    _commit(
        repo,
        {
            "big.py": _VERY_COMPLEX_PY + "\n# e\n",
            "small.py": _SIMPLE_PY + "# e\n",
        },
        "c2",
        "2026-03-02T00:00:00+00:00",
    )
    result = hotspots_kernel(repo, since=None, min_commits=2)
    assert result.files[0].hotspot_score_normalized == pytest.approx(100.0)
    assert all(h.hotspot_score_normalized <= 100.0 for h in result.files)


# ---------------------------------------------------------------------------
# 6. Error handling / degradation
# ---------------------------------------------------------------------------


def test_errors_prefixed_by_source(tmp_path: Path):
    plain = tmp_path / "plain"
    plain.mkdir()
    result = hotspots_kernel(plain)
    # Not a git repo — should produce a git-prefixed error
    assert any(e.startswith("git:") for e in result.errors)


def test_window_resolved_dates_populated(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    _commit(repo, {"a.py": _COMPLEX_PY}, "c1", "2026-03-01T00:00:00+00:00")
    _commit(
        repo,
        {"a.py": _COMPLEX_PY + "\n# e\n"},
        "c2",
        "2026-03-05T00:00:00+00:00",
    )
    result = hotspots_kernel(repo, since=None, min_commits=1)
    assert result.window_resolved_start == "2026-03-01"
    assert result.window_resolved_end == "2026-03-05"


def test_since_sentinel_all_means_unbounded(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    _commit(repo, {"old.py": _COMPLEX_PY}, "c1", "2020-01-01T00:00:00+00:00")
    _commit(
        repo,
        {"old.py": _COMPLEX_PY + "\n# e\n"},
        "c2",
        "2020-02-01T00:00:00+00:00",
    )
    # Default since="90 days ago" would exclude these
    result_bounded = hotspots_kernel(repo, min_commits=2)
    assert len(result_bounded.files) == 0
    # "all" sentinel picks them up
    result_all = hotspots_kernel(repo, since="all", min_commits=2)
    assert len(result_all.files) == 1
    assert result_all.window_since == "all"


# ---------------------------------------------------------------------------
# 7. CLI round-trip
# ---------------------------------------------------------------------------


def test_cli_schema_output():
    rc, out = _run(["hotspots", "--schema"])
    assert rc == 0
    data = json.loads(out)
    assert data["properties"]["root"]["type"] == "string"
    assert "since" in data["properties"]
    assert "min_commits" in data["properties"]


def test_cli_missing_root_errors():
    rc, out = _run(["hotspots"])
    assert rc == 1
    # Error output may be pretty text or JSON; check for the required marker
    assert "--root required" in out or "root" in out.lower()


def test_cli_simple_mode_smoke(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    _commit(repo, {"a.py": _COMPLEX_PY}, "c1", "2026-03-01T00:00:00+00:00")
    _commit(
        repo,
        {"a.py": _COMPLEX_PY + "\n# e\n"},
        "c2",
        "2026-03-02T00:00:00+00:00",
    )
    rc, out = _run(
        [
            "hotspots",
            "--root",
            str(repo),
            "--since",
            "all",
            "--min-commits",
            "2",
        ]
    )
    assert rc == 0
    data = json.loads(out)
    assert "summary" in data
    assert "files" in data
    assert len(data["files"]) == 1
    assert data["files"][0]["file"] == "a.py"
    assert data["files"][0]["sum_ccx"] >= 6
    assert data["files"][0]["change_freq"] == 2


def test_cli_plan_mode(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    _commit(repo, {"b.py": _COMPLEX_PY}, "c1", "2026-03-01T00:00:00+00:00")
    _commit(
        repo,
        {"b.py": _COMPLEX_PY + "\n# e\n"},
        "c2",
        "2026-03-02T00:00:00+00:00",
    )
    plan_json = json.dumps(
        {
            "root": str(repo),
            "since": "all",
            "min_commits": 2,
            "hotspot_percentile": 0.75,
        }
    )
    rc, out = _run(["hotspots", "--plan", plan_json])
    assert rc == 0
    data = json.loads(out)
    assert len(data["files"]) == 1
    assert data["files"][0]["file"] == "b.py"


def test_cli_json_output_shape(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    _commit(repo, {"a.py": _COMPLEX_PY}, "c1", "2026-03-01T00:00:00+00:00")
    _commit(
        repo,
        {"a.py": _COMPLEX_PY + "\n# e\n"},
        "c2",
        "2026-03-02T00:00:00+00:00",
    )
    _, out = _run(["hotspots", "--root", str(repo), "--since", "all", "--min-commits", "2"])
    data = json.loads(out)
    summary = data["summary"]
    for key in (
        "window_since",
        "window_until",
        "window_resolved_start",
        "window_resolved_end",
        "total_commits_analyzed",
        "files_analyzed",
        "files_with_complexity",
        "files_excluded",
        "languages",
        "quadrant_counts",
        "guidance",
    ):
        assert key in summary, f"Missing summary key: {key}"
    for subkey in (
        "unsupported_language",
        "no_functions",
        "below_min_commits",
        "not_on_disk",
    ):
        assert subkey in summary["files_excluded"]
    f = data["files"][0]
    for key in (
        "file",
        "path",
        "language",
        "sum_ccx",
        "max_ccx",
        "change_freq",
        "first_seen",
        "last_seen",
        "hotspot_score",
        "hotspot_score_normalized",
        "quadrant",
        "interpretation",
    ):
        assert key in f, f"Missing file key: {key}"
