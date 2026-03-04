---
description: Identity and scope of the prune skill.
index:
  - Identity
  - Scope
  - Constraints
---

# Summary

## Identity

prune is a read-only advisory skill that performs first-pass dead code detection across a codebase.
It enumerates top-level symbol definitions (via tree-sitter) or module files (via text search) and
flags those with zero detected external references as candidates for review.

The output is explicitly advisory: it identifies candidates for human investigation, not a deletion
list. Confidence ratings and caveats are embedded in every candidate to structurally prevent
false-positive action.

## Scope

prune answers: which symbols or modules appear to have no callers, importers, or reference sites?

It does **not** answer: which of these are truly dead? That requires `aux usages` per candidate,
reading the code, and human judgment about dynamic dispatch, reflection, and plugin registration.

Two scopes are available:
- `symbols`: tree-sitter AST extraction of top-level functions, classes, interfaces, and types
  (requires `aux-skills[query]`)
- `files`: text-only stem-matching for module files (no tree-sitter required)

Default scope is `["symbols"]`.

## Constraints

- **Read-only** — no filesystem writes under any circumstances
- **Advisory** — output is always presented with an explicit advisory, not as confirmed findings
- **Deterministic** — same plan JSON produces the same output for a given codebase snapshot
- **No hidden state** — all criteria are visible in the invocation and echoed in output
