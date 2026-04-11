---
description: Identity and scope of the hotspots skill.
index:
  - Identity
  - Scope
  - Constraints
---

# Summary

## Identity

hotspots is a read-only composition skill that computes **churn-weighted
complexity scores** per file and classifies files into refactor-priority
quadrants. The metric is Tornhill's hotspot formula from *Your Code as a
Crime Scene* (2015): `hotspot_score = complexity × change_frequency`. A
file that is complex AND frequently changed is where bugs accumulate,
because every change has to navigate the existing complexity and every
complexity increment compounds across future changes.

hotspots is a **composition** skill — it does not walk ASTs or parse git
output directly. It calls `ccx_kernel` for the complexity axis and a shared
`util/git.py` primitive for the history axis, then joins the results by
repo-relative path. This is the first AUx kernel that composes with another
*analysis* kernel; earlier kernels compose only at the discovery tier (via
`find_kernel`). The composition rule is: analysis kernels compose only
downward. `hotspots` → `ccx` is allowed; `ccx` → `hotspots` would be a
cycle and is forbidden.

Where `ccx` surfaces the single worst functions in a codebase and `robert`
surfaces the worst packages, hotspots surfaces a different question: which
files are *actively burning*. A function with CCX=30 that hasn't been
touched in three years is a different problem from a function with CCX=15
that's been touched twelve times in the last month — the latter is where
agentic slop accumulates fastest.

## Scope

hotspots answers: which files are the highest-risk refactor targets in
this repository, weighted by how actively they are being changed?

The execution pipeline:

1. `git_log_file_changes(root)` — walk `git log --name-only` to collect
   per-commit file touches in the configured time window; resolve the repo
   root via `git rev-parse --show-toplevel`; skip merge commits by default
2. Scope commits to the subdirectory (if `root` is not the repo root)
3. `ccx_kernel(root, ...)` — compute per-file complexity via tree-sitter,
   returning `FileMetrics` for every file with at least one function in a
   supported language
4. Index both sides by repo-root-relative forward-slash paths; join
5. For each file in the intersection:
   - Exclude files not on disk at HEAD (deleted, renamed without --follow)
   - Exclude files with `sum_ccx == 0` (no functions)
   - Exclude files in languages unsupported by `ccx`
   - Exclude files below `min_commits` (default 2)
6. Compute `hotspot_score = sum_ccx × change_freq` per surviving file
7. Sort by score descending (tie-break: sum_ccx, change_freq, file path)
8. Compute 75th-percentile cutoffs on both axes and assign quadrants
9. Build `guidance` for non-calm files in the top 10
10. Apply `max_results` truncation (post-classification)

**Supported languages**: inherited from `ccx` — Python, JavaScript,
TypeScript, Go, Rust, Java.

## Constraints

Execution is deterministic and reproducible for a given plan JSON and git
state. Read-only — no file writes occur under any circumstances.

**Requires git.** If git is not available or `root` is not inside a git
repo, the skill returns an empty result with `errors[]` populated. The
skill never raises for operational errors (missing git, not-a-repo,
shallow clone, timeout) — these are captured in the result.

**Requires ccx's language support.** Files in languages ccx doesn't
recognize (Bash, C, C++, Ruby, etc.) are excluded from the ranking
entirely, and counted in `files_excluded_unsupported_language`. There is
no LOC fallback — mixing LOC and `sum_ccx` in a single ranking would
produce dishonest output because the two scales are not comparable. When
`ccx` gains new language support in a future release, `hotspots` gains it
for free with zero changes.

**Rename tracking is out of scope.** `git log --follow` only works per
single file, not for whole-log walks. A file renamed mid-window appears
with its history split (old path + new path), producing artificially
shallow change counts for both. Documented limitation.

**The default time window is 90 days**, not Tornhill's canonical 1 year.
Agentic code rot accumulates on a steeper curve than human-era churn; a
1-year window on an agent-assisted repo produces noise. Override via
`--since`.

**Percentile classification requires ≥ 8 files.** Smaller result sets
cannot support meaningful quadrant classification — every file is labeled
`insufficient_data` in that case, and a guidance line explains the
fallback.
