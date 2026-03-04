---
description: Mandatory and prohibited behaviors for the prune skill.
index:
  - Always
  - Never
---

# Policies

Mandatory and prohibited behaviors for the prune skill.

## Always

The agent MUST:

- Present the `advisory` field to the user **verbatim or paraphrased** before presenting any
  candidate list or conclusions. This is non-negotiable.
- Read and communicate the `caveats` for each candidate before forming any opinion about it.
- Offer the "deeper dive" (Step 5 in Procedure) as a mandatory follow-up to every prune run,
  regardless of candidate count or confidence.
- Run `aux usages <symbol>` for each high- and medium-confidence candidate before recommending
  any action. This must happen before any mutation plan is offered.
- Treat `low` confidence candidates as informational smell indicators only — report them but
  explicitly flag them as not actionable without further investigation.
- Compile intent into a schema-valid plan before execution (run `aux prune --schema` first).
- Use the scripts or `aux` CLI for all execution.
- Stop and report if schema validation fails.
- Treat zero candidates as a valid, reportable result — not a failure.

## Never

The agent MUST NOT:

- Take any action (delete, rename, replace, move) based solely on prune output.
- Present prune candidates to the user as a confirmed deletion list.
- Skip the deeper-dive offer because "the confidence is high" or "there are many candidates".
- Skip the advisory presentation because the output is truncated or the list is short.
- Run prune as a substitute for reading the code.
- Auto-widen scope (`max_refs`, `scope`, `globs`) without explicit user consent.
- Omit `caveats` when reporting candidates to the user.
- Proceed to mutation (rename, replace, delete) without completing the `aux usages` verification
  phase for every candidate in scope.
- Invent file paths not confirmed to exist in prune output.
- Write plan artifacts to disk unless explicitly asked.
