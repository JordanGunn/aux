---
description: Failure modes and recovery paths.
index:
  - Failure Modes
  - Recovery
---

# Failures

## Failure Modes

### Schema/config validation failed

The compiled discovery plan or execution plan does not match the schema.

**Recovery:** Fix the schema inputs. Do not execute.

### Clean state

There are no changes under the declared diff scope.

**Recovery:** Report the empty result with full scope context and the selected endpoints.

### Too many changes / truncation

Discovery or run exceeded explicit budget caps (max files, max lines, max bytes) or output truncation occurred.

**Recovery:** Report truncation with counts and caps applied. Suggest narrowing axes (smaller path scope, lower caps, disable patch emission).

### Not a git repository

The target directory is not inside a git working tree.

**Recovery:** Emit a discovery receipt explicitly recording `git_detected=false` and stop. Do not fall back to snapshot behavior in v1.

### Git tool not available

A required dependency (`git`, `python`, `uv`) is not available.

**Recovery:** Report and stop.

### Permission denied

Cannot read required paths or invoke git due to permissions.

**Recovery:** Report the error. Do not escalate privileges or retry.

### Binary or oversized files

Files are binary or too large for a bounded text diff.

**Recovery:** Summarize without emitting content diff for those files and record the decision in summary/receipt.

### Rename detection mismatch

Rename detection differs based on tool flags.

**Recovery:** Make rename detection explicit in the plan and surface results only when enabled.

## Recovery

All failures must:

1. Stop execution immediately
2. Report the failure mode explicitly
3. Include the attempted parameters
4. Suggest a specific recovery action
5. Never silently fall back to alternative behavior
