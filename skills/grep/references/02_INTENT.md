---
description: How to compile user intent into deterministic CLI parameters.
index:
  - Compilation
  - Guardrails
---

# Intent

## Compilation

`/grep <prompt>` is treated as intent. The agent compiles it into a plan matching the CLI schema.

**Source of truth:** Run `aux grep --schema` to get the current plan schema.

The compiled plan MUST map 1:1 to CLI flags (no implicit scope).

## Guardrails

- **Search-before-read:** Compilation and search MUST precede deep file reading.
- **Explicit scope:** Every run declares `root`, `glob`, `exclude`, and caps.
- **Absence is data:** Empty hits MUST be reported with scope + counts.
- **Ephemeral:** Do NOT write plan/intent artifacts to disk unless explicitly asked.
- **Determinism:** Keep lists stable-sorted; use consistent parameter ordering.
