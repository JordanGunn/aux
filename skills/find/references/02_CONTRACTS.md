---
description: Reasoning/compilation contracts that bridge `/find <prompt>` intent to deterministic CLI arguments.
index:
  - Contract
  - Determinism
  - Guardrails
  - Mapping
---

# Contracts

## Contract

`/find <prompt>` is treated as intent. The agent MUST compile it into two ephemeral JSON receipts:

1. `find_intent_v*` (what the user wants)
2. `find_plan_v*` (explicit CLI args to run)

Schemas:

- v1:
  - `assets/schemas/find_intent_v1.schema.json`
  - `assets/schemas/find_plan_v1.schema.json`
- v2 (preferred; explicit pattern semantics):
  - `assets/schemas/find_intent_v2.schema.json`
  - `assets/schemas/find_plan_v2.schema.json`

The compiled plan MUST map 1:1 to CLI flags (no implicit scope).

Templates/examples:

- v1:
  - `assets/templates/find_intent_v1.template.json`
  - `assets/templates/find_plan_v1.template.json`
- v2:
  - `assets/templates/find_intent_v2.template.json`
  - `assets/templates/find_plan_v2.template.json`

Pipe the compiled plan JSON into the runner: `cat plan.json | bash scripts/skill.sh run --stdin`.

## Determinism

- Normalize intent JSON with stable key ordering, no whitespace, and UTF-8.
- Compute `intent_hash = "sha256:" + sha256(normalized_intent_json)`.
- Keep all lists stable-sorted where order is not semantically meaningful.
- Never emit timestamps or nondeterministic IDs in receipts.

## Guardrails

- Enumerate-before-read: file discovery MUST precede deep file reading.
- Explicit scope: every run declares `root`, `pattern`, `exclude`, `type`, and caps.
- Absence is data: empty results MUST be reported with full scope context.
- Ephemeral receipts: do NOT write plan/intent artifacts to disk unless explicitly asked.

## Mapping (must stay explicit)

- Static guardrails: schema fields, caps (`max_*`), canonical excludes.
- Quantitative outputs: file lists, counts, type distributions.
- Qualitative judgment: choosing patterns/scope/type filters (agent domain).
