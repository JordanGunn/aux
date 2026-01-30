---
description: Reasoning/compilation contracts that bridge `/grep <prompt>` intent to deterministic CLI arguments.
index:
  - Contract
  - Determinism
  - Guardrails
  - Mapping
---

# Contracts

## Contract

`/grep <prompt>` is treated as intent. The agent compiles it into a plan matching the CLI schema.

**Source of truth:** Run `aux grep --schema` (or `bash scripts/skill.sh schema`) to get the current plan schema.

The compiled plan MUST map 1:1 to CLI flags (no implicit scope).

**Simple mode:** Pass pattern as positional argument with flags:

```bash
aux grep "pattern" --root /path --glob "*.py"
```

**Plan mode:** Pipe JSON matching the schema to stdin:

```bash
cat plan.json | bash scripts/skill.sh run --stdin
```

## Determinism

- Keep all lists stable-sorted where order is not semantically meaningful (globs, excludes).
- Use consistent parameter ordering for reproducibility.

## Guardrails

- Search-before-read: compilation and search MUST precede deep file reading.
- Explicit scope: every run declares `root`, `glob`, `exclude`, and caps.
- Absence is data: empty hits MUST be reported with scope + counts.
- Ephemeral receipts: do NOT write plan/intent artifacts to disk unless explicitly asked.

## Mapping (must stay explicit)

- Static guardrails: schema fields, caps (`max_*`), canonical excludes.
- Quantitative outputs: hit records, counts, file distributions.
- Qualitative judgment: choosing terms/scope/strategy (agent domain).
