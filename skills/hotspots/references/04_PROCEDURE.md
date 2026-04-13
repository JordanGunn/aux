---
description: Step-by-step execution flow, quadrant reference, and output interpretation.
index:
  - Invocation modes
  - Execution pipeline
  - Axes reference
  - Quadrant reference
  - Output interpretation
  - Agent usage patterns
---

# Procedure

## Invocation modes

**Simple mode:**
```bash
aux hotspots --root /path/to/repo
aux hotspots --root /path/to/repo --since "30 days ago"
aux hotspots --root /path/to/repo --since all --min-commits 5
aux hotspots --root /path/to/repo --max-results 20
aux hotspots --root /path/to/repo --exclude "**/test_*.py"
```

**Plan mode:**
```bash
aux hotspots --plan '{"root":"/path"}'
aux hotspots --plan '{"root":"/path","since":"60 days ago","min_commits":3}'
aux hotspots --plan '{"root":"/path","since":"all","max_results":10}'
```

**Schema:**
```bash
aux hotspots --schema
```

**Skill script:**
```bash
./skills/hotspots/scripts/skill.sh run --root ./
./skills/hotspots/scripts/skill.sh run --root ./ --since "30 days ago"
./skills/hotspots/scripts/skill.sh schema
echo '{"root":"./","since":"all"}' | ./skills/hotspots/scripts/skill.sh run --stdin
```

## Execution pipeline

1. **Normalize `since`** — the sentinels `""`, `"all"`, and `"unbounded"`
   are converted to `None` (unbounded log walk)
2. **`git_log_numstat(root, since=..., until=...)`**:
   a. Resolve repo root via `git rev-parse --show-toplevel`
   b. Detect shallow clone via `git rev-parse --is-shallow-repository`
      (warn only; does not fail)
   c. Run `git log --no-merges --numstat --pretty=format:...` with the
      window filters
   d. Parse the output into `NumstatCommitRecord[]` with per-file
      insertions/deletions
3. **Scope commits** to the subdirectory (if `root` is not the repo
   root) — filter each commit's `files_changed` tuple to paths under the
   subdirectory prefix
4. **`ccx_kernel(root, min_ccx=1, ...)`** — get per-file `FileMetrics`
   for every file with at least one function in a supported language
5. **Index both sides**:
   - `ccx_by_repo_path[repo_rel] → FileMetrics` (repo-root-relative key)
   - `churn_by_file[repo_rel] → [commit_date, ...]`
6. **Join** — iterate over the union of both key sets:
   - If file is not on disk at HEAD → `files_excluded_not_on_disk += 1`
   - If file has no `FileMetrics` (ccx language support missing OR no
     functions) → classify via `detect_language`, add to the appropriate
     exclusion count
   - If `sum_ccx == 0` → `files_excluded_no_functions += 1`
   - If `loc_delta < min_commits` → `files_excluded_below_min_commits += 1`
   - Otherwise → build a `FileHotspot` entry
7. **Sort** by `(-hotspot_score, -sum_ccx, -loc_delta, file)` for stable
   ordering
8. **Normalize scores** — divide by max to produce
   `hotspot_score_normalized ∈ [0, 100]`
9. **Classify quadrants** via `_assign_quadrants`:
   - If fewer than 8 files → all `insufficient_data`
   - Otherwise compute 75th-percentile cutoffs on both axes, assign each
     file to one of four quadrants
10. **Truncate** — apply `max_results` cap (post-classification so the
    quadrant counts reflect the full filtered set)
11. **Build guidance** — one line per non-calm file in the top 10

## Axes reference

| Axis | Source | Per-file value | Interpretation |
|------|--------|----------------|----------------|
| Complexity | `ccx_kernel` | `sum_ccx` (total cyclomatic complexity across all functions in the file) | How expensive it is to safely modify this file |
| Growth | `git log --numstat` | `loc_delta` (net lines of code change: insertions − deletions) | How much new code this file absorbed recently |
| Score | computed | `hotspot_score = sum_ccx × max(0, loc_delta)` | Combined refactor-priority signal |

The raw product is intentional. It penalises equally the two failure
modes: a very complex file that is growing fast, and a simple file
that is absorbing large amounts of code. A file with `sum_ccx=100, loc_delta=1` has the
same raw score as a file with `sum_ccx=1, loc_delta=100`, but they land
in different quadrants (`stable_complex` vs `churning_simple`) — the
quadrant is the real interpretation.

## Quadrant reference

| Quadrant | sum_ccx | loc_delta | Meaning |
|----------|---------|-------------|---------|
| `hotspot` | ≥ p75 | ≥ p75 | Active hotspot — complex AND frequently changed. Prime refactor target. |
| `stable_complex` | ≥ p75 | < p75 | Legacy — touch with care but not urgent. |
| `churning_simple` | < p75 | ≥ p75 | Hot path but straightforward — watch for accidental complexity growth. |
| `calm` | < p75 | < p75 | Low signal. |
| `insufficient_data` | n/a | n/a | Set too small (< 8 files) for percentile classification. |

The cutoff `p75` is computed **inclusively** — a file whose value is
*exactly* the 75th percentile is classified as "high". The formula is
`index = ceil(0.75 * n) - 1` on an ascending sort.

## Output interpretation

- `summary.window_since` / `window_until` — the values actually passed
  to git. `"unbounded"` means no lower bound.
- `summary.window_resolved_start` / `window_resolved_end` — ISO dates
  (YYYY-MM-DD) of the oldest and newest commits actually observed in the
  window. These are the real boundaries of the analyzed data.
- `summary.total_commits_analyzed` — commits that touched the
  subdirectory in the window
- `summary.files_analyzed` — files that survived all filters (pre-
  truncation)
- `summary.files_with_complexity` — files where `ccx` returned a
  `FileMetrics` (pre-filter)
- `summary.files_excluded.*` — per-reason exclusion counts
- `summary.quadrant_counts` — distribution across quadrants (always
  reflects the full filtered set, even when `max_results` is applied)
- `summary.guidance` — prioritized action list; non-calm files in the top 10
- `files[]` — sorted by `hotspot_score` descending; first entry = highest
  refactor priority
  - `file` / `path` — repo-root-relative and absolute file locations
  - `language` — detected from file extension
  - `sum_ccx` / `max_ccx` — file-level complexity totals from `ccx`
  - `loc_delta` — net LOC change (insertions − deletions) in the window
  - `first_seen` / `last_seen` — ISO dates (YYYY-MM-DD) of the first and
    last commit in the window that touched this file
  - `hotspot_score` — `sum_ccx × max(0, loc_delta)`
  - `hotspot_score_normalized` — 0–100 scaled by the max score
  - `quadrant` — machine-filterable quadrant label
  - `interpretation` — human-readable verdict keyed to the quadrant

## Agent usage patterns

**Refactor-target triage:**
```
1. Run aux hotspots --root <project>
2. Inspect summary.quadrant_counts: any hotspot or stable_complex?
3. If yes, walk summary.guidance from top — these are the highest-leverage
   refactor candidates
4. For each top file, drill down with: aux ccx --root <file> --min-ccx 11
   to identify the specific functions driving the complexity axis
```

**Agentic-sprint audit:**
```
1. Run aux hotspots --root <project> --since "14 days ago" --min-commits 2
2. Any files in the hotspot quadrant are candidates for where the agent
   left slop
3. Cross-reference with aux delta --ref-from HEAD~14 to see what symbols
   actually changed in each file
```

**Pre/post refactor measurement:**
```
1. Before refactor: run aux hotspots, note the target file's sum_ccx and
   hotspot_score
2. Make changes
3. After refactor: re-run. The file should drop a quadrant (hotspot →
   churning_simple is a real win; hotspot → calm is best)
```

**Quarterly health check:**
```
1. Run aux hotspots --root <project> --since "90 days ago"
2. Track hotspot count over time. Rising hotspot count in fixed windows
   is an early signal of architectural decay
3. If hotspot count grew since last check, inspect which files crossed
   the threshold
```

**Cross-language audit:**
```
1. Run aux hotspots --root <project> with no language filter
2. Inspect summary.languages to confirm ccx coverage
3. Note files_excluded_unsupported_language — these are blind spots
4. For blind-spot-heavy codebases, consider whether ccx language
   support should be expanded before relying on hotspots
```
