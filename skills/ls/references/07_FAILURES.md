---
description: Failure modes and recovery paths.
index:
  - Failure Modes
  - Recovery
---

# Failures

## Failure Modes

### Schema/config validation failed

The compiled plan or config does not match the schema.

**Recovery:** Fix the schema inputs. Do not execute.

### No entries found

The inventory returned zero entries.

**Recovery:** Report the empty result with full scope context. Suggest one widening axis (broader root, greater depth, include_hidden).

### Too many entries

The scan exceeded budget caps or output truncation occurred.

**Recovery:** Report truncation with counts and caps applied. Suggest narrowing axes (smaller depth, narrower root, smaller top_n).

### Root directory not found

The specified root does not exist.

**Recovery:** Fail explicitly. Do not guess alternative paths.

### Tool not available

A required dependency (python/uv) or optional dependency (git) is not available.

**Recovery:**

- If `uv`/python is missing: report and stop.
- If `git` is missing and git mapping was requested: report via the receipt `git` block (`git_not_found`) and proceed without per-entry git annotations.

### Permission denied

Cannot read directories in the target path.

**Recovery:** Report the error. Do not escalate privileges or retry.

### Git mapping failed

Git status mapping was requested but git invocation failed.

**Recovery:** Do not emit partial per-entry git claims. Report the condition via the receipt `git` block (`error`) and suggest disabling git mapping.

## Recovery

All failures must:

1. Stop execution immediately
2. Report the failure mode explicitly
3. Include the attempted parameters
4. Suggest a specific recovery action
5. Never silently fall back to alternative behavior
