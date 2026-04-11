---
description: Explicit prohibitions and mandates for the hotspots skill.
index:
  - Prohibitions
  - Mandates
  - Scope limits
  - Deliberate exclusions
---

# Policies

## Prohibitions

hotspots MUST NOT:
- Write to any file under any circumstances
- Fall back to LOC (lines-of-code) as a complexity axis for files in
  languages unsupported by `ccx` — mixing LOC and `sum_ccx` in the same
  ranking produces dishonest output because the two scales are
  incomparable (a Bash file with LOC=120 and a Python file with
  `sum_ccx=120` are not remotely equivalent on "effort to change safely")
- Follow file renames across the git history walk — `git log --follow`
  only works per single file, not for whole-log walks, and a synthesized
  rename graph is out of scope for this version
- Count merge commits in the change-frequency axis by default — merges
  are structural, not change events (override via `include_merges=True`
  on the util primitive, not surfaced on the CLI)
- Raise exceptions for operational errors (missing git, not-a-repo,
  shallow clone, timeout) — these are captured in the result's `errors`
  field
- Accept `since`/`until`/`paths` arguments beginning with `-` — rejected
  early as a git-flag-injection guard
- Cache or persist state between invocations

## Mandates

hotspots MUST:
- Return the same output for the same plan JSON and the same git state
  (determinism)
- Resolve the repo root via `git rev-parse --show-toplevel` even when the
  caller passes a subdirectory as `root`
- Normalize all path keys to forward-slash repo-root-relative strings
  before joining the ccx and git sides
- Sort `files[]` output by `hotspot_score` descending, with stable tie
  breakers on `sum_ccx`, `change_freq`, and file path
- Include `quadrant` as a machine-readable field on every file entry
- Include `interpretation` as a human-readable verdict keyed to the
  quadrant on every file entry
- Include `guidance` in summary with one entry per non-calm file in the
  top 10
- Include all errors encountered in the `errors` field, prefixed by
  source (`git:` or `ccx:`) so the origin is traceable
- Report `truncated: true` when `max_results` cap is applied
- Classify the whole set as `insufficient_data` when fewer than 8 files
  survive filtering — percentile classification is not meaningful below
  that threshold
- Compute quadrant classification BEFORE applying `max_results`
  truncation, so the counts reflect the full filtered set

## Scope limits

The composition pattern (one analysis kernel calling another) is new in
AUx. The rules codified in this version:
- Analysis kernels compose only **downward**. `hotspots` → `ccx` is
  allowed; `ccx` → `hotspots` would be a cycle and is forbidden.
- When a second caller of `ccx_kernel` at the analysis tier appears,
  extract a thin wrapper rather than duplicate the pattern ad hoc. Until
  then, direct composition is acceptable.

The scoring formula is intentionally fixed in this version:
- `hotspot_score = sum_ccx × change_freq` (raw product, no transforms)
- Alternatives (log-scaled, normalized, weighted sum, recency-weighted
  churn) are deferred to a follow-up version once real-world signal
  quality is assessed

The time window default is intentionally short (90 days, vs Tornhill's
canonical 1 year):
- Agentic code rot accumulates on a steeper curve than human-era churn
- A 1-year window on an agent-assisted repo surfaces a year's worth of
  human churn and drowns the recent agentic signal
- Override via `--since "2020-01-01"`, `--since "1 year ago"`, or
  `--since all` (sentinel for unbounded, which is a perf footgun on
  large repos — documented in the schema)

## Deliberate exclusions

Files excluded from the ranking (surfaced as counts for transparency):
- Files whose language is not supported by `ccx`
  (`files_excluded_unsupported_language`)
- Files with `sum_ccx == 0` — no functions in the file
  (`files_excluded_no_functions`)
- Files with `change_freq < min_commits` — default 2, filters drive-by
  single-touch noise (`files_excluded_below_min_commits`)
- Files present in git log but not on disk at HEAD — deleted or renamed
  without --follow tracking (`files_excluded_not_on_disk`)

The default `min_commits=2` is intentional: a file touched once in the
window is almost always noise (a one-off fix, a drive-by typo correction,
or the initial import of a dormant file). The threshold can be raised
(`--min-commits 5`) for tighter signal on high-activity repos.

Quadrant classification is fixed as percentile-based (not absolute
thresholds). Reasoning: absolute thresholds lie about calm repos
("nothing is a hotspot"), while percentile always surfaces the
worst-of-the-pack. The downside — that "hotspot" is relative to the
analyzed set, not an absolute quality level — is documented explicitly
in the output interpretation.
