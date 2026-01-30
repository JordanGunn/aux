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

`/find <prompt>` is treated as intent. The agent compiles it into a plan matching the CLI schema.

**Source of truth:** Run `aux find --schema` (or `bash scripts/skill.sh schema`) to get the current plan schema.

The compiled plan MUST map 1:1 to CLI flags (no implicit scope).

**Simple mode:** Pass options as flags:

```bash
aux find --root /path --glob "*.py" --type file
```

**Plan mode:** Pipe JSON matching the schema to stdin:

```bash
cat plan.json | bash scripts/skill.sh run --stdin
```

## Determinism

- Keep all lists stable-sorted where order is not semantically meaningful.
- Use consistent parameter ordering for reproducibility.

## Guardrails

- Enumerate-before-read: file discovery MUST precede deep file reading.
- Explicit scope: every run declares `root`, `pattern`, `exclude`, `type`, and caps.
- Absence is data: empty results MUST be reported with full scope context.
- Ephemeral receipts: do NOT write plan/intent artifacts to disk unless explicitly asked.

## Mapping (must stay explicit)

- Static guardrails: schema fields, caps (`max_*`), canonical excludes.
- Quantitative outputs: file lists, counts, type distributions.
- Qualitative judgment: choosing patterns/scope/type filters (agent domain).
