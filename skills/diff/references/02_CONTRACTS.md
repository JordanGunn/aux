---
description: Reasoning/compilation contracts that bridge `/diff <prompt>` intent to deterministic execution.
index:
  - Contract
  - Determinism
  - Guardrails
  - Mapping
---

# Contracts

## Contract

`/diff <prompt>` is treated as intent. The agent MUST compile it into ephemeral JSON artifacts:

1. `diff_intent_v1` (what the user wants)
2. `diff_discovery_plan_v1` (explicit, bounded discovery-only plan)
3. `diff_plan_v1` (explicit, bounded execution plan)

Schemas:

- `assets/schemas/diff_intent_v1.schema.json`
- `assets/schemas/diff_discovery_plan_v1.schema.json`
- `assets/schemas/diff_plan_v1.schema.json`
- `assets/schemas/diff_summary_v1.schema.json`
- `assets/schemas/diff_receipt_v1.schema.json`
- `assets/schemas/diff_result_bundle_v1.schema.json`

Discovery outputs (under `.aux/diff/`):

- `diff_discovery.json`
- `diff_discovery_receipt.json`
- `diff_discovery_view.txt`

Run outputs (under `.aux/diff/`):

- `diff_summary_v1.json`
- `diff_receipt_v1.json`
- `diff.patch` (optional; only when explicitly requested)

Runner invocation (plan JSON on stdin):

```bash
cat plan.json | bash scripts/skill.sh run --stdin
```

## Determinism

- Git-only v1 surface. No snapshot surface.
- Use stable ordering for all enumerations.
- Never emit nondeterministic IDs in output artifacts.
- Never silently drop data: truncation must be explicit in receipts and summaries.
- Whitespace and line-ending normalization must map only to explicit `git diff`-equivalent flags (no invented semantics).
- Rename detection, when enabled, must be explicit and surfaced in structured summary fields.

## Guardrails

- Enumerate-before-reason: discovery outputs are authoritative.
- Explicit scope/bounds: every plan must declare surface/root/scope/mode and caps.
- No mutation: never create/edit/delete files or git state.
- No network access.
- Fail closed on schema/config validation errors.
- If git is missing or the directory is not a git repo, the discovery receipt must record the condition explicitly and the run must not proceed.

## Mapping (must stay explicit)

- Static guardrails: schema fields, additionalProperties=false, symlink policy, git-only surface policy.
- Quantitative outputs: counts, truncation flags, bounded patch emission.
- Qualitative judgment: selecting scope/bounds from intent (must be explicit in the plan).
