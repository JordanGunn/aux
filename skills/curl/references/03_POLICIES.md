---
description: Mandatory and prohibited behaviors for this skill.
index:
  - Always
  - Never
---

# Policies

Mandatory and prohibited behaviors for the curl skill.

## Always

The agent MUST:

- Declare the correct `mode` or use `auto` when uncertain
- Read `has_more` before deciding to fetch the next chunk
- Stop fetching when the gathered content answers the question
- Check the `error` field in every response — a non-null value indicates a
  problem (timeout, network failure, JSON parse failure)
- Use `--schema` / `aux curl --schema` before assuming field names
- Use the scripts for all execution (never raw curl or wget)
- Report fetch results to the user before acting on them
- Treat `status` codes ≥ 400 as errors even when `error` is null

## Never

The agent MUST NOT:

- Put credentials, tokens, or passwords in plan JSON (headers are visible)
- Fetch the same URL + offset combination more than once in a single task
  (responses are deterministic; duplicate fetches waste budget)
- Auto-continue fetching chunks without checking whether more content is needed
- Assume HTML mode when `Content-Type` is not `text/html`
- Modify any files (this is a read-only skill)
- Bypass schema validation before invoking the kernel
- Use raw HTTP tools (curl, wget, requests) — always use this skill's scripts
