---
description: When and why to invoke the delta skill.
index:
  - Primary use cases
  - When NOT to use delta
  - Prerequisite signals
---

# Intent

## Primary use cases

delta is the correct skill when any of these questions must be answered:

1. **Session drift audit** — after a sequence of edits, determine the full scope of
   what changed: which files, how many lines, which symbols were added or removed.

2. **API surface change** — before submitting a PR or tagging a release, enumerate
   every symbol that was added or removed since the base branch.

3. **Refactor verification** — confirm that a rename/extract operation changed only
   the intended symbols and no others.

4. **Working tree summary** — get a structured account of all uncommitted changes vs.
   HEAD (the "what did I just do?" query).

5. **Ref-to-ref comparison** — compare two git refs (branches, tags, commit SHAs):
   `aux delta --root . --ref-from v1.0 --ref-to v2.0`

## When NOT to use delta

- When you need module-level coupling topology → use `deps` instead
- When you need symbol cross-reference across the whole codebase → use `usages` instead
- When you need to search file content → use `search` or `find` instead
- When you need dead code candidates → use `prune` instead

## Prerequisite signals

Run delta when:
- You are about to open a PR and need a change summary
- You suspect accumulated drift and need to verify scope
- A review requests a list of API additions/removals
- You need to confirm that a refactor was symbol-neutral
