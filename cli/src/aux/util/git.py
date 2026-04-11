"""Git log primitive for AUx.

Provides a shared git-history walker used by history-aware skills (currently
hotspots; future: change coupling, ownership churn). Placed in util/ because
it is a primitive — it does not emit AUx-shaped result objects, it just walks
`git log` and returns per-commit records.

Security contract:
    The `since`, `until`, and `paths` parameters are passed directly to git as
    command-line arguments. To prevent git-flag injection, any value beginning
    with '-' is rejected at call time with ValueError. A `--` sentinel is
    inserted before pathspec arguments so git cannot interpret them as flags.
    subprocess.run is invoked with no shell, so OS-level metacharacter
    injection is impossible by construction.

Failure-mode contract:
    Operational errors (not-a-git-repo, git missing, timeout, git exit
    failure) are captured in GitLogResult.errors with ok=False. The function
    never raises for these. ValueError is reserved for programmer errors
    (argument validation).
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from aux.util.subprocess import run_tool, which

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CommitRecord:
    """One commit's metadata plus the files it touched."""

    commit_hash: str
    author_date: str                 # ISO 8601 with timezone (%aI)
    files_changed: tuple[str, ...]   # repo-relative, forward-slash
    parent_count: int                # 0 for root, 1 normal, >= 2 merge


@dataclass(frozen=True)
class GitLogResult:
    """Result of a git log walk."""

    commits: tuple[CommitRecord, ...]
    repo_root: Path | None           # None if cwd is not inside a git repo
    ok: bool
    is_shallow: bool
    errors: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# Pretty-format encoding
# ---------------------------------------------------------------------------
#
# We use ASCII control characters as delimiters in git's --pretty=format:
# because they cannot appear in commit hashes, ISO dates, or parent hash
# lists. Filenames *can* technically contain newlines, but git's default
# core.quotePath setting escapes such names with octal sequences in
# --name-only output, so plain newline-splitting is safe in the common case.
#
# Record separator (0x1e): between commits
# Unit separator (0x1f):   between header fields within a commit

_RS = "\x1e"
_US = "\x1f"
_FORMAT = f"%x1e%H%x1f%aI%x1f%P"


# ---------------------------------------------------------------------------
# Security guards
# ---------------------------------------------------------------------------


def _reject_flag_like(value: str, field: str) -> None:
    """Raise ValueError if a caller-supplied value looks like a git flag.

    Defense against git-flag injection: any value beginning with '-' could be
    parsed as an option by git. Reject early.
    """
    if value.startswith("-"):
        raise ValueError(
            f"{field} value {value!r} cannot begin with '-' "
            f"(guards against git-flag injection)"
        )


# ---------------------------------------------------------------------------
# Output parser
# ---------------------------------------------------------------------------


def _parse_log_output(output: str) -> list[CommitRecord]:
    """Parse the output of our custom git log format into CommitRecords.

    Format emitted by:
        git log --name-only --pretty=format:%x1e%H%x1f%aI%x1f%P

    Each commit begins with RS (0x1e). Within a commit, the first line is
    the header (hash, date, parents — US-separated), followed by newline-
    separated filenames.
    """
    if not output:
        return []

    records: list[CommitRecord] = []
    blocks = output.split(_RS)
    for block in blocks:
        if not block or not block.strip():
            continue

        # Header ends at the first newline; files follow
        newline_idx = block.find("\n")
        if newline_idx == -1:
            header = block
            file_text = ""
        else:
            header = block[:newline_idx]
            file_text = block[newline_idx + 1:]

        header = header.rstrip("\r\n")
        fields = header.split(_US)
        if len(fields) < 3:
            continue  # Malformed, skip

        commit_hash = fields[0]
        author_date = fields[1]
        parents_str = fields[2]
        parent_count = len(parents_str.split()) if parents_str.strip() else 0

        files = tuple(
            line for line in file_text.split("\n") if line and line.strip()
        )

        records.append(
            CommitRecord(
                commit_hash=commit_hash,
                author_date=author_date,
                files_changed=files,
                parent_count=parent_count,
            )
        )

    return records


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def git_log_file_changes(
    cwd: Path,
    *,
    since: str | None = None,
    until: str | None = None,
    include_merges: bool = False,
    paths: list[str] | None = None,
    timeout: float = 300.0,
) -> GitLogResult:
    """Walk ``git log`` and return per-commit file-change records.

    Args:
        cwd: Any path inside the git repo. Used to locate the repo root via
            ``git rev-parse --show-toplevel``.
        since: Git-style time specifier (``"90 days ago"``, ``"2025-01-01"``,
            ...). Leading dashes are rejected (flag-injection guard).
        until: Upper bound on author date, same format as ``since``.
        include_merges: If False (default), merge commits are excluded
            (``--no-merges``).
        paths: Pathspec limits. Each element must not begin with ``-``. A
            ``--`` sentinel is inserted before the pathspec list so git
            cannot interpret elements as options.
        timeout: Seconds to wait for ``git log`` (default 300). Tuned for
            large repos; the 60s default in ``run_tool`` is too short.

    Returns:
        :class:`GitLogResult`. ``ok=False`` when cwd is not in a git repo,
        git is missing, ``git log`` fails, or the subprocess times out.
        Operational errors are captured in ``errors``, not raised.

    Raises:
        ValueError: If any ``since``/``until``/``paths`` argument begins
            with ``-``.
    """
    # --- Argument validation (flag-injection guard) ---
    if since is not None:
        _reject_flag_like(since, "since")
    if until is not None:
        _reject_flag_like(until, "until")
    if paths is not None:
        for p in paths:
            _reject_flag_like(p, "paths element")

    errors: list[str] = []

    # --- Git availability ---
    if which("git") is None:
        return GitLogResult(
            commits=(),
            repo_root=None,
            ok=False,
            is_shallow=False,
            errors=("git not found — install git and ensure it is in PATH",),
        )

    # --- Resolve repo root ---
    cwd_for_rev = cwd if cwd.is_dir() else cwd.parent
    top_result = run_tool(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=cwd_for_rev,
    )
    if not top_result.ok:
        err = top_result.stderr.strip() or f"git rev-parse failed (exit {top_result.returncode})"
        return GitLogResult(
            commits=(),
            repo_root=None,
            ok=False,
            is_shallow=False,
            errors=(f"not a git repository: {err}",),
        )

    repo_root = Path(top_result.stdout.strip())

    # --- Empty-repo short-circuit ---
    # git log on a repo with no commits exits non-zero with "does not have
    # any commits yet" — treat this as ok with empty result.
    head_result = run_tool(
        ["git", "rev-parse", "--verify", "--quiet", "HEAD"],
        cwd=repo_root,
    )
    if not head_result.ok:
        return GitLogResult(
            commits=(),
            repo_root=repo_root,
            ok=True,
            is_shallow=False,
            errors=(),
        )

    # --- Shallow repo detection (warn, don't fail) ---
    shallow_result = run_tool(
        ["git", "rev-parse", "--is-shallow-repository"],
        cwd=repo_root,
    )
    is_shallow = False
    if shallow_result.ok and shallow_result.stdout.strip() == "true":
        is_shallow = True
        errors.append(
            "repository is shallow; git log history is truncated — "
            "run `git fetch --unshallow` for complete history"
        )

    # --- Build log command ---
    log_args: list[str] = [
        "git",
        "log",
        "--name-only",
        f"--pretty=format:{_FORMAT}",
    ]
    if not include_merges:
        log_args.append("--no-merges")
    if since is not None:
        log_args.append(f"--since={since}")
    if until is not None:
        log_args.append(f"--until={until}")
    if paths:
        log_args.append("--")
        log_args.extend(paths)

    # --- Run log ---
    try:
        log_result = run_tool(log_args, cwd=repo_root, timeout=timeout)
    except subprocess.TimeoutExpired:
        return GitLogResult(
            commits=(),
            repo_root=repo_root,
            ok=False,
            is_shallow=is_shallow,
            errors=(*errors, f"git log timed out after {timeout}s"),
        )

    if not log_result.ok:
        err = log_result.stderr.strip() or f"git log failed (exit {log_result.returncode})"
        return GitLogResult(
            commits=(),
            repo_root=repo_root,
            ok=False,
            is_shallow=is_shallow,
            errors=(*errors, err),
        )

    # --- Parse output ---
    commits = _parse_log_output(log_result.stdout)

    return GitLogResult(
        commits=tuple(commits),
        repo_root=repo_root,
        ok=True,
        is_shallow=is_shallow,
        errors=tuple(errors),
    )
