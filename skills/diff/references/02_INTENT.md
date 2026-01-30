---
description: How to compile user intent into deterministic CLI parameters.
index:
  - Compilation
  - Guardrails
---

# Intent

## Compilation

`/diff <prompt>` is treated as intent. The agent compiles it into a plan matching the CLI schema.

**Source of truth:** Run `aux diff --schema` to get the current plan schema.

The compiled plan MUST be explicit about paths, context lines, and any normalization flags.

## Guardrails

- **Enumerate-before-reason:** Discovery outputs are authoritative.
- **Explicit scope:** Every plan declares paths, context, and caps.
- **No mutation:** Never create/edit/delete files or git state.
- **No network access.**
- **Ephemeral:** Do NOT write plan/intent artifacts to disk unless explicitly asked.
- **Determinism:** Use stable ordering; never emit nondeterministic IDs.
