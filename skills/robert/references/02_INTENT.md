---
description: When and why to invoke the robert skill.
index:
  - Primary use cases
  - When NOT to use robert
  - Prerequisite signals
---

# Intent

## Primary use cases

robert is the correct skill when any of these questions must be answered:

1. **Pre-refactor blast radius (structural)** — before restructuring a codebase, identify
   which packages are in the Zone of Pain. High Ca + low A = rigid under change. The D'
   score quantifies how much restructuring is warranted.

2. **Design review** — given a proposed new package structure, run robert to verify
   each package's projected I and A values land near the main sequence (D' < 0.2).

3. **Agent self-evaluation** — before proposing structural changes to a user, run robert
   on the current codebase to establish a D' baseline. After generating changes, re-run
   to verify D' improved. This provides a concrete, defensible metric rather than
   subjective design commentary.

4. **Shared vocabulary** — when a user asks about "coupling" or "brittle packages",
   robert produces I, A, D', and zone labels that give both agent and user a common
   frame of reference for the discussion.

5. **Zone detection** — identify Zone of Pain packages (stable-concrete, rigid) and
   Zone of Uselessness packages (unstable-abstract, wasted abstraction effort) as
   concrete candidates for targeted refactoring.

## When NOT to use robert

- When you need file-level import coupling → use `deps` instead
- When you need symbol-level cross-reference → use `usages` instead
- When you need dead code candidates → use `prune` instead
- When you need git change history → use `delta` instead
- When you need to search file content → use `search` or `find` instead
- For non-Go, non-Python codebases — language is required and only go/python supported

## Prerequisite signals

Run robert when:
- You are planning a structural refactor and need to identify which packages are rigid
- A user asks whether a package or module is "well-designed" or "tightly coupled"
- You want to verify that a proposed architecture satisfies the Stable Dependencies Principle
- You need a D' score to anchor a design conversation with a concrete number
- You are reviewing a codebase for architectural health before a large change
