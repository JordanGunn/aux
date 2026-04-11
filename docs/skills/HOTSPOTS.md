# hotspots — Churn-Weighted Complexity Hotspots

**Version:** 0.1.0 | **Type:** Read-only | **Tier:** Analysis

## What it does

`aux hotspots` ranks files in a codebase by **churn-weighted complexity
score** — Tornhill's hotspot formula from *Your Code as a Crime Scene*
(2015):

```
hotspot_score = sum_ccx × change_freq
```

A file scores high when it's *both* complex (hard to change safely) *and*
frequently changed (being modified anyway). That intersection is where
bugs accumulate, because every change has to navigate the existing
complexity and every complexity increment compounds across future changes.

`hotspots` is a **composition** skill: it calls `aux ccx` for the
complexity axis and the shared `util/git.py` primitive for the history
axis, then joins the results by repo-relative path. Files are then
classified into four refactor-priority quadrants based on 75th-percentile
cutoffs on both axes.

Where `ccx` surfaces the single worst *functions* and `robert` surfaces
the worst *packages*, `hotspots` answers a different question: which
*files* are **actively burning**. A function with CCX=30 untouched for
three years is a different problem from a function with CCX=15 touched
twelve times in the last month.

### Why 90 days (not Tornhill's 1 year)?

Tornhill's canonical default is 1 year because his book is calibrated for
human release cycles. **The AUx user is catching agentic rot**, which
accumulates on a steeper curve than human-era churn. A 1-year window on
an agent-assisted repo surfaces a year's worth of human churn and drowns
the recent agentic signal in noise. `hotspots` defaults to 90 days for
this reason. Override via `--since` when you need Tornhill-style
long-horizon analysis.

## Quick start

```bash
# Default 90-day window
aux hotspots --root ./

# Tighter 30-day window — agent-sprint audit
aux hotspots --root ./ --since "30 days ago"

# Unbounded walk — full history analysis
aux hotspots --root ./ --since all

# Tighter minimum commit threshold
aux hotspots --root ./ --min-commits 5

# Top 10 hotspots only
aux hotspots --root ./ --max-results 10

# Plan mode
aux hotspots --plan '{"root":"./","since":"60 days ago","min_commits":3}'

# Schema
aux hotspots --schema
```

## Arguments

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--root` | path | required | Repository root (may be a subdirectory of the git repo) |
| `--glob` | pattern | — | Include glob (repeatable) |
| `--exclude` | pattern | — | Exclude glob (repeatable) |
| `--hidden` | flag | false | Include hidden files |
| `--no-ignore` | flag | false | Don't respect gitignore |
| `--since` | git-spec | `"90 days ago"` | Git log window start. Accepts any git-style time spec (`"30 days ago"`, `"2025-01-01"`, `"1 year ago"`) or the sentinels `"all"`/`"unbounded"` for unbounded walks |
| `--until` | git-spec | — | Git log window end (default: now) |
| `--min-commits` | int | 2 | Minimum commit count to include a file in the ranking |
| `--max-results` | int | unlimited | Cap on the ranked file list (post-sort) |
| `--percentile` | float | 0.75 | Percentile cutoff for quadrant classification |
| `--plan` | JSON | — | Full plan JSON (overrides other options) |
| `--schema` | flag | — | Print JSON schema and exit |

## Output format

```json
{
  "summary": {
    "window_since": "90 days ago",
    "window_until": "",
    "window_resolved_start": "2026-01-15",
    "window_resolved_end": "2026-04-08",
    "total_commits_analyzed": 87,
    "files_analyzed": 142,
    "files_with_complexity": 168,
    "files_excluded": {
      "unsupported_language": 12,
      "no_functions": 5,
      "below_min_commits": 9,
      "not_on_disk": 0
    },
    "languages": { "python": 634, "go": 48 },
    "quadrant_counts": {
      "hotspot": 6,
      "stable_complex": 28,
      "churning_simple": 30,
      "calm": 78,
      "insufficient_data": 0
    },
    "guidance": [
      "src/router.py (Hotspot): CCX=142, churn=14, score=1988",
      "src/processor.py (Hotspot): CCX=98, churn=12, score=1176",
      "src/auth/session.py (Stable Complex): CCX=203, churn=2, score=406"
    ]
  },
  "files": [
    {
      "file": "src/router.py",
      "path": "/abs/path/src/router.py",
      "language": "python",
      "sum_ccx": 142,
      "max_ccx": 42,
      "change_freq": 14,
      "first_seen": "2026-02-05",
      "last_seen": "2026-04-07",
      "hotspot_score": 1988.0,
      "hotspot_score_normalized": 100.0,
      "quadrant": "hotspot",
      "interpretation": "Active hotspot: CCX=142, churn=14 commits (last touched 2026-04-07). Complex AND frequently changed — prime refactor target."
    }
  ],
  "errors": []
}
```

## Axes reference

| Axis | Source | Per-file value | Interpretation |
|------|--------|----------------|----------------|
| Complexity | `ccx_kernel` | `sum_ccx` — sum of cyclomatic complexity across every function in the file | How expensive it is to safely modify this file |
| Churn | `git log --name-only --no-merges` | `change_freq` — count of commits in the window that touched the file | How actively this file is being changed |
| Score | computed | `sum_ccx × change_freq` | Combined refactor-priority signal |

The raw product is intentional. It penalises equally the two failure
modes: a very complex file that is changing slowly, and a simple file
that is changing rapidly. A file with `sum_ccx=100, change_freq=1` has the
same raw score as a file with `sum_ccx=1, change_freq=100`, but they land
in different quadrants (`stable_complex` vs `churning_simple`) — the
quadrant is the real interpretation.

## Quadrant reference

| Quadrant | sum_ccx | change_freq | Meaning |
|----------|---------|-------------|---------|
| `hotspot` | ≥ p75 | ≥ p75 | **Active hotspot**: complex AND frequently changed. Prime refactor target. |
| `stable_complex` | ≥ p75 | < p75 | **Legacy**: complex but dormant. Touch with care but not urgent. |
| `churning_simple` | < p75 | ≥ p75 | **Hot path**: frequently changed but straightforward. Safe for now; watch for accidental complexity growth. |
| `calm` | < p75 | < p75 | Low signal. |
| `insufficient_data` | n/a | n/a | Set too small (< 8 files) for percentile classification. |

The cutoff `p75` is computed inclusively — a file whose value is exactly
the 75th percentile is classified as "high". This matches Tornhill's
original presentation.

The classification is **relative to the analyzed set**, not an absolute
quality threshold. A small homogeneous codebase will always have some
"hotspots" in the statistical sense, even if every file is in good shape.
Use the raw `hotspot_score` and `sum_ccx` numbers for absolute judgments;
use the quadrants for relative prioritization.

## Exclusions

Files excluded from the ranking (surfaced as counts in
`summary.files_excluded`):

- **`unsupported_language`** — the file's language is not supported by
  `ccx` (Bash, C, C++, Ruby, etc.). There is no LOC fallback — see below.
- **`no_functions`** — the file has zero functions (e.g., a Python module
  of only top-level constants)
- **`below_min_commits`** — the file was touched fewer than `min_commits`
  times in the window (default 2 — filters drive-by noise)
- **`not_on_disk`** — the file appears in git history but not on disk at
  HEAD (deleted, or renamed without `--follow` tracking)

### Why no LOC fallback?

An earlier design proposal had `hotspots` fall back to LOC for files in
languages unsupported by `ccx`. This was dropped because LOC and
`sum_ccx` live on incompatible scales — a Bash file with LOC=120 and a
Python file with `sum_ccx=120` are not remotely equivalent on "effort to
change safely". Mixing them in a single ranking produces dishonest
output.

The follow-up path is clean: when `ccx` gains new language support,
`hotspots` gains it for free with zero changes.

## Supported languages

Inherited from `aux ccx`:

| Language | Extensions |
|----------|------------|
| Python | `.py` |
| JavaScript | `.js`, `.mjs`, `.cjs` |
| TypeScript | `.ts`, `.tsx` |
| Go | `.go` |
| Rust | `.rs` |
| Java | `.java` |

Files in other languages are excluded from the ranking and counted in
`files_excluded_unsupported_language`.

## Requirements

- **git**: required at runtime. If git is missing or `--root` is not
  inside a git repo, `hotspots` returns an empty result with `errors[]`
  populated. The skill never raises for operational errors.
- **aux ccx**: `hotspots` calls `ccx_kernel` in-process. Both skills must
  be installed together.

## Composing with other skills

```bash
# Step 1: find hot files; Step 2: drill into their worst functions
aux hotspots --root ./ --max-results 5
aux ccx --root src/router.py --min-ccx 11

# Agentic-sprint audit — what did the last 14 days of agent work leave behind?
aux hotspots --root ./ --since "14 days ago" --min-commits 2
aux delta --ref-from HEAD~14 --root ./

# Combine file-level (hotspots) and package-level (robert) for a layered picture
aux hotspots --root ./
aux robert --root ./src --language python

# Pre/post refactor measurement on a specific file
aux hotspots --root ./       # note target file's quadrant
# (refactor)
aux hotspots --root ./       # expect the file to drop a quadrant
```

## Limitations

- **No rename tracking.** `git log --follow` only works per-single-file,
  not for whole-log walks. A file renamed mid-window has its history
  split between the old and new paths, producing artificially low change
  counts for both. Documented limitation.

- **No ownership/author axis.** The skill is purely complexity × churn.
  Tornhill's book also discusses ownership churn (how many different
  authors touched a file) as a third signal. That's a future extension.

- **No temporal coupling matrix.** Hotspots surfaces *files* that are
  hot; change coupling surfaces *file pairs* that co-change (potential
  architectural seams). That's a separate skill entirely, not scoped to
  `hotspots`.

- **Percentile classification is relative, not absolute.** See the
  quadrant reference above. A tiny or uniformly healthy codebase will
  still have "hotspots" in the statistical sense. Use the raw scores for
  absolute judgments.

- **Raw-product scoring only.** Alternatives (log-scaled, weighted sum,
  recency-weighted churn) are deferred to a follow-up version once
  real-world signal quality is assessed.
