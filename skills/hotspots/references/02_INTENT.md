---
description: When and why to invoke the hotspots skill.
index:
  - Primary use cases
  - When NOT to use hotspots
  - Prerequisite signals
  - Composition with other skills
---

# Intent

## Primary use cases

hotspots is the correct skill when any of these questions must be answered:

1. **Find the highest-risk refactor targets in a repo** — a sorted list of
   files by hotspot score immediately identifies where refactoring effort
   has the highest expected return, because the files are both complex
   (hard to change safely) and active (being changed anyway).

2. **Catch agentic rot before it becomes architectural** — when an agent
   has been churning on a codebase, hotspots surfaces files whose
   complexity has grown alongside a burst of recent commits. This is the
   fastest method-level early-warning signal for agentic slop accumulating
   in a specific area.

3. **Post-incident blast-radius query** — after a bug fix lands, check
   whether the file that hosted the bug is in the hotspot quadrant. A bug
   in a hotspot file is a symptom, not an anomaly, and predicts more bugs
   in the same file.

4. **Quarterly codebase health check** — run hotspots against the whole
   repo with the default 90-day window. The `quadrant_counts` summary tells
   you in one number whether any files crossed the hotspot threshold since
   the last check.

5. **Targeted refactor justification** — when a developer argues for
   refactoring a specific file, hotspots produces a defensible quantitative
   case: here is the complexity, here is the churn, here is the quadrant
   label, here is the guidance line.

6. **Pre-release risk assessment** — before a release, run hotspots on the
   changed area to identify any hotspot-quadrant files that might be
   fragile under the release's new load.

## When NOT to use hotspots

- When you only need complexity, not churn → use `ccx` instead
- When you need package-level design metrics → use `robert` instead
- When you need file-level import coupling → use `deps` instead
- When you need a single commit's semantic diff → use `delta` instead
- When the repository has no git history (fresh init, shallow clone with
  no history) — hotspots requires git history to compute the churn axis
- For codebases primarily in languages ccx does not support (Bash, C,
  C++, Ruby) — those files will be excluded and the ranking will be
  incomplete
- For tiny repos (fewer than ~8 files after filtering) — the quadrant
  classification degrades to `insufficient_data` for such sets

## Prerequisite signals

Run hotspots when:
- A user asks "which files are the most problematic in this codebase?"
- A user asks "where should we focus our refactor effort?"
- A user describes a file as "constantly being touched and always causing
  bugs" and needs a defensible number to confirm or refute
- You are reviewing a codebase you're unfamiliar with and need to
  identify the high-risk areas before touching anything
- You are at the tail end of an agent-assisted sprint and want to audit
  what got churned and whether the churn landed in high-complexity areas
- You are establishing a baseline for ongoing codebase health monitoring
- You need to prioritize refactor work across many candidates and want a
  ranking driven by both complexity and recency

## Composition with other skills

hotspots composes naturally with three sibling skills:

- **hotspots → ccx**: hotspots surfaces *which files* are hot; ccx surfaces
  *which functions within those files* are complex. A typical agent
  workflow is `aux hotspots --max-results 5` followed by `aux ccx --root
  <hotspot_file> --min-ccx 11` to drill into the specific functions.

- **hotspots + robert**: `robert` produces package-level Distance-from-
  Main-Sequence scores. A file that is both in the hotspot quadrant AND in
  a Zone-of-Pain package is a double-red flag — it's hard to change AND
  it's architecturally stuck.

- **hotspots + delta**: `delta` shows *what symbols changed* in a specific
  commit or ref range. If hotspots identifies a file that became a hotspot
  in the last 30 days, `delta --ref-from HEAD~30` shows which symbols in
  that file moved during the window.
