---
description: How to compile user intent into deterministic CLI parameters.
index:
  - Compilation
  - Guardrails
---

# Intent

## Compilation

`/find <prompt>` is treated as intent. The agent compiles it into a plan matching the CLI schema.

**Source of truth:** Run `aux find --schema` to get the current plan schema.

The compiled plan MUST map 1:1 to CLI flags (no implicit scope).

## Guardrails

- **Enumerate-before-read:** File discovery MUST precede deep file reading.
- **Explicit scope:** Every run declares `root`, `pattern`, `exclude`, `type`, and caps.
- **Absence is data:** Empty results MUST be reported with full scope context.
- **Ephemeral:** Do NOT write plan/intent artifacts to disk unless explicitly asked.
- **Determinism:** Keep lists stable-sorted; use consistent parameter ordering.
