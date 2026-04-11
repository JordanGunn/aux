---
description: When and why to invoke the ccx skill.
index:
  - Primary use cases
  - When NOT to use ccx
  - Prerequisite signals
---

# Intent

## Primary use cases

ccx is the correct skill when any of these questions must be answered:

1. **Find the worst-offender functions in a codebase** — sort all functions
   by CCX descending and inspect the top N. The result is an immediate,
   defensible refactor target list with concrete numbers attached.

2. **Pre-refactor blast radius (method-level)** — before touching a complex
   function, confirm its CCX and CogC scores so the post-refactor improvement
   can be measured numerically.

3. **Design review of a single file or directory** — restrict the analysis
   with `--root` and `--language` to focus on a specific area, surface its
   complexity hotspots, and report concrete numbers per function.

4. **Establish a baseline before merging a PR** — run ccx on the touched
   files before and after a change to verify the change does not increase
   the maximum function complexity beyond an agreed threshold.

5. **Catch slop early** — ccx is the earliest detection signal in the metric
   hierarchy. A function that crosses from `simple` to `moderate` is a smaller
   problem than a package that drifts into the Zone of Pain. Run ccx in CI
   on touched files to prevent gradient slop accumulation.

6. **Shared vocabulary for code review** — when a reviewer says "this is too
   complex", ccx produces a defensible CCX number, a zone label, and a
   threshold reference (McCabe 1976) that anchors the discussion.

## When NOT to use ccx

- When you need package-level architectural metrics → use `robert` instead
- When you need file-level import coupling → use `deps` instead
- When you need symbol-level cross-reference → use `usages` instead
- When you need to find files matching a pattern → use `find` or `search`
- When you need git change history → use `delta` instead
- For Bash scripts — bash is intentionally excluded; CCX is not meaningful
  for shell scripts where the real complexity lives in piped external commands
- For C, C++, or Ruby codebases — these languages are not supported in this
  version (deferred due to parser quirks and macro handling)

## Prerequisite signals

Run ccx when:
- A user asks "what are the most complex functions in this codebase?"
- You are about to refactor and need to identify high-CCX targets
- You are reviewing a PR and want to verify it does not introduce
  untestable functions
- A user describes a function as "too complex" or "hard to test" and you
  need a defensible number to confirm or refute the claim
- You are running periodic codebase health checks and want a method-level
  complement to `robert`'s package-level metrics
- You are establishing a baseline for ongoing complexity monitoring
