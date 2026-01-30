---
description: How to compile user intent into deterministic CLI parameters.
index:
  - Compilation
  - Guardrails
---

# Intent

## Compilation

`/ls <prompt>` is treated as intent. The agent compiles it into a plan matching the CLI schema.

**Source of truth:** Run `aux ls --schema` to get the current plan schema.

The compiled plan MUST be explicit about root, depth, include_hidden, sort, order, top_n, and caps.

## Guardrails

- **Enumerate-before-reason:** Inventory is authoritative; narrative derives from artifacts.
- **Explicit scope:** Every run declares root, depth, include_hidden, ranking, and caps.
- **No mutation:** Never create/edit/delete entries as part of listing.
- **No content search:** Do not read file contents.
- **Ephemeral:** Do NOT write plan/intent artifacts to disk unless explicitly asked.
- **Determinism:** Use stable sorting; never emit nondeterministic IDs.
