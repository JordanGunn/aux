"""Hotspots kernel — churn-weighted complexity scoring per file.

Composes `ccx_kernel` (complexity) with `git_log_file_changes` (change
frequency) to compute Tornhill-style hotspot scores. A file's hotspot score
is ``sum_ccx × change_freq``; files are classified into quadrants based on
75th-percentile cutoffs on both axes.

Cross-kernel composition contract:
    Analysis kernels compose **only downward**. ``hotspots`` calls ``ccx``
    to reuse the canonical complexity source; ``ccx`` must NEVER call
    ``hotspots`` (that would be a cycle). If a second caller of
    ``ccx_kernel`` at the analysis tier appears, extract a thin wrapper
    rather than duplicate the pattern ad hoc.

Path normalization:
    ``ccx`` emits paths relative to the caller-supplied ``root``. ``git log``
    emits paths relative to the repo root. When ``root`` is a subdirectory
    of the repo, ``hotspots`` prepends the subdirectory prefix to ``ccx``
    paths before joining with git paths. All keys are forward-slash
    repo-root-relative strings.

Agentic-era tuning:
    The default ``since`` window is 90 days (not Tornhill's canonical 1
    year). Agentic code rot accumulates on a steeper curve than human-era
    churn; a 1-year window on an agent-assisted repo produces noise.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

from aux.kernels.ccx import FileMetrics, ccx_kernel
from aux.kernels.ccx import _LANG_CONFIG as _CCX_LANG_CONFIG  # noqa: PLC2701 — composition contract
from aux.util.git import CommitRecord, git_log_file_changes
from aux.util.treesitter import detect_language

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class FileHotspot:
    """Per-file churn-weighted complexity record."""

    file: str                          # repo-root-relative, forward-slash
    path: str                          # absolute filesystem path
    language: str                      # from ccx detection
    sum_ccx: int                       # sum of ccx across all functions in file
    max_ccx: int                       # worst single function in file
    change_freq: int                   # commit count in window
    first_seen: str                    # ISO date (YYYY-MM-DD) of oldest commit in window
    last_seen: str                     # ISO date of newest commit in window
    hotspot_score: float               # sum_ccx * change_freq (sorting key)
    hotspot_score_normalized: float    # 0.0 - 100.0 scaled by max
    quadrant: str                      # "hotspot"|"stable_complex"|"churning_simple"|"calm"|"insufficient_data"
    interpretation: str                # human-readable verdict


@dataclass
class HotspotsResult:
    """Aggregated hotspots result."""

    files: list[FileHotspot]                     # sorted by hotspot_score desc
    window_since: str                            # value passed to git (or "unbounded")
    window_until: str
    window_resolved_start: str | None            # ISO date of oldest commit actually seen
    window_resolved_end: str | None              # ISO date of newest commit actually seen
    total_commits_analyzed: int                  # commits that touched the subdirectory
    files_analyzed: int                          # files in the final ranking
    files_with_complexity: int                   # files where ccx returned a FileMetrics
    files_excluded_unsupported_language: int
    files_excluded_no_functions: int             # sum_ccx == 0
    files_excluded_below_min_commits: int
    files_excluded_not_on_disk: int              # deleted / renamed w/o follow
    languages: dict[str, int]                    # from ccx
    quadrant_counts: dict[str, int]
    guidance: list[str]
    errors: list[str] = field(default_factory=list)
    truncated: bool = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_EMPTY_QUADRANT_COUNTS: dict[str, int] = {
    "hotspot": 0,
    "stable_complex": 0,
    "churning_simple": 0,
    "calm": 0,
    "insufficient_data": 0,
}


def _empty_quadrant_counts() -> dict[str, int]:
    return dict(_EMPTY_QUADRANT_COUNTS)


def _empty_result(
    *,
    since: str,
    until: str,
    errors: list[str],
) -> HotspotsResult:
    """Build an empty HotspotsResult with the given error list."""
    return HotspotsResult(
        files=[],
        window_since=since,
        window_until=until,
        window_resolved_start=None,
        window_resolved_end=None,
        total_commits_analyzed=0,
        files_analyzed=0,
        files_with_complexity=0,
        files_excluded_unsupported_language=0,
        files_excluded_no_functions=0,
        files_excluded_below_min_commits=0,
        files_excluded_not_on_disk=0,
        languages={},
        quadrant_counts=_empty_quadrant_counts(),
        guidance=[],
        errors=errors,
    )


def _normalize_since(since: str | None) -> str | None:
    """Convert the 'all'/'' sentinel to None for unbounded windows."""
    if since is None:
        return None
    trimmed = since.strip().lower()
    if trimmed in ("", "all", "unbounded"):
        return None
    return since


def _subdir_prefix(root: Path, repo_root: Path) -> str:
    """Compute the repo-root-relative prefix for files under root.

    Returns "" if root == repo_root, otherwise a forward-slash relative path
    without a trailing slash. Raises ValueError if root is not under repo_root.
    """
    root_resolved = root.resolve()
    repo_resolved = repo_root.resolve()
    if root_resolved == repo_resolved:
        return ""
    rel = root_resolved.relative_to(repo_resolved)
    return rel.as_posix()


def _scope_commits_to_prefix(
    commits: tuple[CommitRecord, ...], prefix: str
) -> list[CommitRecord]:
    """Filter a commit list to only files under the given repo-relative prefix.

    An empty prefix means no filtering (root == repo_root).
    """
    if not prefix:
        return list(commits)
    prefix_with_slash = prefix + "/"
    scoped: list[CommitRecord] = []
    for c in commits:
        kept = tuple(
            f for f in c.files_changed
            if f == prefix or f.startswith(prefix_with_slash)
        )
        if kept:
            scoped.append(
                CommitRecord(
                    commit_hash=c.commit_hash,
                    author_date=c.author_date,
                    files_changed=kept,
                    parent_count=c.parent_count,
                )
            )
    return scoped


def _ccx_key(fm: FileMetrics, subdir_prefix: str) -> str:
    """Translate a ccx FileMetrics.file (root-relative) to repo-relative."""
    rel = fm.file.replace("\\", "/")
    if subdir_prefix:
        return f"{subdir_prefix}/{rel}"
    return rel


# ---------------------------------------------------------------------------
# Quadrant classification
# ---------------------------------------------------------------------------


def _percentile_cutoff(values: list[int], percentile: float) -> int:
    """Return the inclusive percentile cutoff for a sorted list of ints.

    Uses ``index = ceil(percentile * n) - 1`` on an ascending sort. A value
    at exactly the cutoff is classified as "high" (inclusive boundary).
    """
    if not values:
        return 0
    n = len(values)
    idx = max(0, math.ceil(percentile * n) - 1)
    return sorted(values)[idx]


def _assign_quadrants(
    hotspots: list[FileHotspot], percentile: float
) -> dict[str, int]:
    """Assign quadrant classification to each hotspot in place.

    Returns the quadrant count dict. When fewer than 8 files remain after
    filtering, percentile classification is meaningless — everything gets
    the ``insufficient_data`` label.
    """
    counts = _empty_quadrant_counts()

    if len(hotspots) < 8:
        for h in hotspots:
            h.quadrant = "insufficient_data"
            h.interpretation = _interpret_hotspot(h)
            counts["insufficient_data"] += 1
        return counts

    p_ccx = _percentile_cutoff([h.sum_ccx for h in hotspots], percentile)
    p_churn = _percentile_cutoff([h.change_freq for h in hotspots], percentile)

    for h in hotspots:
        high_ccx = h.sum_ccx >= p_ccx
        high_churn = h.change_freq >= p_churn
        if high_ccx and high_churn:
            q = "hotspot"
        elif high_ccx:
            q = "stable_complex"
        elif high_churn:
            q = "churning_simple"
        else:
            q = "calm"
        h.quadrant = q
        h.interpretation = _interpret_hotspot(h)
        counts[q] += 1

    return counts


# ---------------------------------------------------------------------------
# Interpretation and guidance
# ---------------------------------------------------------------------------


_QUADRANT_LABELS: dict[str, str] = {
    "hotspot": "Hotspot",
    "stable_complex": "Stable Complex",
    "churning_simple": "Churning Simple",
    "calm": "Calm",
    "insufficient_data": "Unclassified",
}


def _interpret_hotspot(h: FileHotspot) -> str:
    """Human-readable one-line verdict keyed to the quadrant."""
    base = (
        f"CCX={h.sum_ccx}, churn={h.change_freq} commits "
        f"(last touched {h.last_seen})"
    )
    if h.quadrant == "hotspot":
        return (
            f"Active hotspot: {base}. Complex AND frequently changed — "
            f"prime refactor target."
        )
    if h.quadrant == "stable_complex":
        return (
            f"Stable complex: {base}. Legacy code — touch with care but "
            f"not urgent."
        )
    if h.quadrant == "churning_simple":
        return (
            f"Churning simple: {base}. Hot path but straightforward — "
            f"watch for accidental complexity growth."
        )
    if h.quadrant == "calm":
        return f"Calm: {base}. Low signal."
    if h.quadrant == "insufficient_data":
        return (
            f"Unclassified: {base}. Set too small for percentile "
            f"classification (needs >= 8 files)."
        )
    return f"Unknown: {base}."


_ACTIONABLE_QUADRANTS = frozenset({"hotspot", "stable_complex", "churning_simple"})


def _build_guidance(hotspots: list[FileHotspot]) -> list[str]:
    """One guidance line per non-calm top file (max 10)."""
    items: list[str] = []
    for h in hotspots:
        if h.quadrant not in _ACTIONABLE_QUADRANTS:
            continue
        label = _QUADRANT_LABELS.get(h.quadrant, h.quadrant)
        items.append(
            f"{h.file} ({label}): CCX={h.sum_ccx}, "
            f"churn={h.change_freq}, score={h.hotspot_score:.0f}"
        )
        if len(items) >= 10:
            break
    return items


# ---------------------------------------------------------------------------
# Main kernel entry point
# ---------------------------------------------------------------------------


def hotspots_kernel(
    root: Path,
    *,
    # file discovery (pass-through to ccx)
    globs: list[str] | None = None,
    excludes: list[str] | None = None,
    hidden: bool = False,
    no_ignore: bool = False,
    # time window
    since: str | None = "90 days ago",
    until: str | None = None,
    # filtering
    min_commits: int = 2,
    # ranking
    max_results: int | None = None,
    # classification
    hotspot_percentile: float = 0.75,
) -> HotspotsResult:
    """Compute churn-weighted complexity hotspots per file.

    Args:
        root: Repository root (or any subdirectory of a git repo).
        globs: File patterns to include (pass-through to ccx).
        excludes: File patterns to exclude (pass-through to ccx).
        hidden: Include hidden files.
        no_ignore: Ignore .gitignore rules.
        since: Git log window start. Default ``"90 days ago"`` — tighter
            than Tornhill's canonical 1yr because agentic rot accumulates
            on a steeper curve. Accepts git-style specifiers, ``None``, or
            the sentinels ``""``/``"all"``/``"unbounded"`` for full history.
        until: Git log window end.
        min_commits: Exclude files with fewer than this many commits in
            the window. Default 2 (filters drive-by single-touch noise).
        max_results: Cap the ranked result list (post-sort truncation).
        hotspot_percentile: Cutoff for quadrant classification (default
            0.75 = top 25% on each axis = hotspot quadrant).

    Returns:
        :class:`HotspotsResult`. Errors from the git primitive and the ccx
        kernel are captured in ``errors``, not raised.
    """
    errors: list[str] = []
    display_since = since if since is not None else "unbounded"
    display_until = until if until is not None else ""

    # --- Step 1: Walk git history ---
    # Run git first so we can detect not-a-repo before doing expensive ccx work.
    git_since = _normalize_since(since)
    git_result = git_log_file_changes(
        root,
        since=git_since,
        until=until,
        include_merges=False,
    )
    if not git_result.ok:
        errors.extend(f"git: {e}" for e in git_result.errors)
        return _empty_result(
            since=display_since,
            until=display_until,
            errors=errors,
        )
    errors.extend(f"git: {e}" for e in git_result.errors)

    repo_root = git_result.repo_root
    if repo_root is None:
        # Shouldn't happen with ok=True, but defensive
        errors.append("git: repo_root resolution failed despite ok=True")
        return _empty_result(
            since=display_since,
            until=display_until,
            errors=errors,
        )

    # --- Step 2: Scope commits to the subdirectory (if any) ---
    try:
        subdir_prefix = _subdir_prefix(root, repo_root)
    except ValueError:
        errors.append(
            f"root {root} is not inside repo_root {repo_root} — cannot join"
        )
        return _empty_result(
            since=display_since,
            until=display_until,
            errors=errors,
        )

    scoped_commits = _scope_commits_to_prefix(git_result.commits, subdir_prefix)

    # --- Step 3: Walk complexity ---
    ccx_result = ccx_kernel(
        root,
        globs=globs,
        excludes=excludes,
        hidden=hidden,
        no_ignore=no_ignore,
        min_ccx=1,
    )
    errors.extend(f"ccx: {e}" for e in ccx_result.errors)

    ccx_by_repo_path: dict[str, FileMetrics] = {
        _ccx_key(fm, subdir_prefix): fm for fm in ccx_result.files
    }

    # --- Step 4: Build per-file churn map ---
    churn_by_file: dict[str, list[str]] = {}
    for c in scoped_commits:
        for f in c.files_changed:
            churn_by_file.setdefault(f, []).append(c.author_date)

    # --- Step 5: Join, filter, build hotspots ---
    files_excluded_unsupported_language = 0
    files_excluded_no_functions = 0
    files_excluded_below_min_commits = 0
    files_excluded_not_on_disk = 0

    hotspots: list[FileHotspot] = []
    all_keys = set(ccx_by_repo_path.keys()) | set(churn_by_file.keys())

    for repo_rel in all_keys:
        abs_path = repo_root / repo_rel
        if not abs_path.exists():
            files_excluded_not_on_disk += 1
            continue

        fm = ccx_by_repo_path.get(repo_rel)
        if fm is None:
            # Distinguish "unsupported language" from "Python file with zero
            # functions": ccx_kernel only emits FileMetrics for files whose
            # language is supported AND contain at least one function, so a
            # None result conflates the two cases. Re-detect the language to
            # tell them apart.
            detected = detect_language(abs_path)
            if detected is not None and detected in _CCX_LANG_CONFIG:
                files_excluded_no_functions += 1
            else:
                files_excluded_unsupported_language += 1
            continue

        if fm.sum_ccx == 0:
            files_excluded_no_functions += 1
            continue

        dates = churn_by_file.get(repo_rel, [])
        change_freq = len(dates)
        if change_freq < min_commits:
            files_excluded_below_min_commits += 1
            continue

        score = float(fm.sum_ccx * change_freq)
        sorted_dates = sorted(dates)
        first_seen = sorted_dates[0][:10]
        last_seen = sorted_dates[-1][:10]

        hotspots.append(
            FileHotspot(
                file=repo_rel,
                path=str(abs_path),
                language=fm.language,
                sum_ccx=fm.sum_ccx,
                max_ccx=fm.max_ccx,
                change_freq=change_freq,
                first_seen=first_seen,
                last_seen=last_seen,
                hotspot_score=score,
                hotspot_score_normalized=0.0,  # filled below
                quadrant="calm",               # filled by _assign_quadrants
                interpretation="",             # filled by _assign_quadrants
            )
        )

    # --- Step 6: Sort + normalize scores ---
    hotspots.sort(
        key=lambda h: (-h.hotspot_score, -h.sum_ccx, -h.change_freq, h.file)
    )

    max_score = hotspots[0].hotspot_score if hotspots else 0.0
    if max_score > 0:
        for h in hotspots:
            h.hotspot_score_normalized = (h.hotspot_score / max_score) * 100.0

    # --- Step 7: Quadrant classification (+ interpretation) ---
    quadrant_counts = _assign_quadrants(hotspots, hotspot_percentile)

    # Record pre-truncation count for the summary (user cares about "how many
    # files survived the filters", not the post-cap slice length).
    files_analyzed = len(hotspots)

    # --- Step 8: Truncation (post-classification) ---
    truncated = False
    if max_results is not None and len(hotspots) > max_results:
        hotspots = hotspots[:max_results]
        truncated = True

    # --- Step 9: Resolved window from actual commits seen ---
    all_dates = sorted(c.author_date for c in scoped_commits)
    window_resolved_start = all_dates[0][:10] if all_dates else None
    window_resolved_end = all_dates[-1][:10] if all_dates else None

    # --- Step 10: Guidance ---
    guidance = _build_guidance(hotspots)

    return HotspotsResult(
        files=hotspots,
        window_since=display_since,
        window_until=display_until,
        window_resolved_start=window_resolved_start,
        window_resolved_end=window_resolved_end,
        total_commits_analyzed=len(scoped_commits),
        files_analyzed=files_analyzed,
        files_with_complexity=len(ccx_by_repo_path),
        files_excluded_unsupported_language=files_excluded_unsupported_language,
        files_excluded_no_functions=files_excluded_no_functions,
        files_excluded_below_min_commits=files_excluded_below_min_commits,
        files_excluded_not_on_disk=files_excluded_not_on_disk,
        languages=dict(ccx_result.languages),
        quadrant_counts=quadrant_counts,
        guidance=guidance,
        errors=errors,
        truncated=truncated,
    )
