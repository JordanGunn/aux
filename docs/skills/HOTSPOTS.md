# hotspots — Growth-Weighted Complexity Hotspots

**Version:** 0.2.0 | **Type:** Read-only | **Tier:** Analysis

## What it does

`aux hotspots` ranks files in a codebase by **growth-weighted complexity
score** — Tornhill's hotspot framework from *Your Code as a Crime Scene*
(2015) with an adapted churn proxy for agentic code generation:

```
hotspot_score = sum_ccx × max(0, loc_delta)
```

Where `loc_delta` is the net lines of code change (insertions − deletions)
over the time window, measured via `git log --numstat`. A file scores high
when it's *both* complex (hard to change safely) *and* growing fast
(absorbing new code). That intersection is where architectural damage
accumulates — every new line has to navigate the existing complexity.

Files that shrank (negative `loc_delta`) are clamped to score 0 — shrinkage
is the opposite of the growth failure mode this metric targets.

`hotspots` is a **composition** skill: it calls `aux ccx` for the
complexity axis and the shared `util/git.py` primitive for the history
axis, then joins the results by repo-relative path. Files are then
classified into four refactor-priority quadrants based on 75th-percentile
cutoffs on both axes.

Where `ccx` surfaces the single worst *functions* and `robert` surfaces
the worst *packages*, `hotspots` answers a different question: which
*files* are **actively burning**. A function with CCX=30 untouched for
three years is a different problem from a file that absorbed 200 lines of
helpers this week.

### Why 14 days (not Tornhill's 1 year)?

Tornhill's canonical default is 1 year because his book is calibrated for
human release cycles. **The AUx user is catching agentic rot**, which
accumulates in days, not months. An agent can dump 200 lines of private
helper functions into an existing file in a single session — the
architectural damage (namespace contamination, coupling growth, ownership
erosion) is immediate. A 1-year window on an agent-assisted repo drowns
the recent signal in human-era noise. `hotspots` defaults to 14 days for
this reason. Widen to `"90 days ago"` for human-pace repos, or `"all"` for
Tornhill-style long-horizon analysis.

### Why LOC delta (not commit count)?

Tornhill used commit count as the churn proxy because in 2015 most commits
were human-authored and roughly similar in scope. With agentic code
generation, one commit can add 400 lines to a file while 40 trivial commits
touch one line each. Commit count no longer correlates with actual change
volume. LOC delta (via `git log --numstat`) directly measures the volume
of change, which is the signal that matters.

## Quick start

```bash
# Default 14-day window
aux hotspots --root ./

# Wider 90-day window — human-pace repos
aux hotspots --root ./ --since "90 days ago"

# Unbounded walk — full history analysis
aux hotspots --root ./ --since all

# Tighter minimum commit threshold
aux hotspots --root ./ --min-commits 5

# Top 10 hotspots only
aux hotspots --root ./ --max-results 10

# Plan mode
aux hotspots --plan '{"root":"./","since":"30 days ago","min_commits":3}'

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
| `--since` | git-spec | `"14 days ago"` | Git log window start. Accepts any git-style time spec (`"90 days ago"`, `"2025-01-01"`, `"1 year ago"`) or the sentinels `"all"`/`"unbounded"` for unbounded walks |
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
    "window_since": "14 days ago",
    "window_until": "",
    "window_resolved_start": "2026-04-01",
    "window_resolved_end": "2026-04-13",
    "total_commits_analyzed": 42,
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
      "src/router.py (Hotspot): CCX=142, growth=+320 LOC, score=45440",
      "src/processor.py (Hotspot): CCX=98, growth=+180 LOC, score=17640",
      "src/auth/session.py (Stable Complex): CCX=203, growth=+12 LOC, score=2436"
    ]
  },
  "files": [
    {
      "file": "src/router.py",
      "path": "/abs/path/src/router.py",
      "language": "python",
      "sum_ccx": 142,
      "max_ccx": 42,
      "loc_delta": 320,
      "loc_insertions": 350,
      "loc_deletions": 30,
      "commit_count": 14,
      "first_seen": "2026-04-02",
      "last_seen": "2026-04-12",
      "hotspot_score": 45440.0,
      "hotspot_score_normalized": 100.0,
      "quadrant": "hotspot",
      "interpretation": "Active hotspot: CCX=142, growth=+320 LOC across 14 commits (last touched 2026-04-12). Complex AND growing fast — prime refactor target."
    }
  ],
  "errors": []
}
```

## Axes reference

| Axis | Source | Per-file value | Interpretation |
|------|--------|----------------|----------------|
| Complexity | `ccx_kernel` | `sum_ccx` — sum of cyclomatic complexity across every function in the file | How expensive it is to safely modify this file |
| Growth | `git log --numstat` | `loc_delta` — net lines of code change (insertions − deletions) in the window | How much new code this file absorbed recently |
| Score | computed | `sum_ccx × max(0, loc_delta)` | Combined refactor-priority signal |

The raw product penalises the agentic failure mode directly: a complex
file that is growing fast. A file with `sum_ccx=100, loc_delta=1` has the
same raw score as a file with `sum_ccx=1, loc_delta=100`, but they land
in different quadrants (`stable_complex` vs `churning_simple`) — the
quadrant is the real interpretation.

## Quadrant reference

| Quadrant | sum_ccx | loc_delta | Meaning |
|----------|---------|-----------|---------|
| `hotspot` | ≥ p75 | ≥ p75 | **Active hotspot**: complex AND growing fast. Prime refactor target. |
| `stable_complex` | ≥ p75 | < p75 | **Legacy**: complex but not growing. Touch with care but not urgent. |
| `churning_simple` | < p75 | ≥ p75 | **Fast-growing**: absorbing code but straightforward. Watch for accidental complexity growth. |
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
| C# | `.cs` |

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

- **No ownership/author axis.** The skill is purely complexity × growth.
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
