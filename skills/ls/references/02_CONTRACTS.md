---
description: Reasoning/compilation contracts that bridge `/ls <prompt>` intent to deterministic execution.
index:
  - Contract
  - Determinism
  - Guardrails
  - Mapping
---

# Contracts

## Contract

`/ls <prompt>` is treated as intent. The agent compiles it into a plan matching the CLI schema.

**Source of truth:** Run `aux ls --schema` (or `bash scripts/skill.sh schema`) to get the current plan schema.

The compiled plan MUST be explicit about:

- root
- depth
- include_hidden
- sort + order
- top_n
- scan caps
- whether git mapping is enabled

The skill interface remains **natural-language-only**; plans are internal artifacts.

Runner invocation (plan JSON on stdin):

```bash
cat plan.json | bash scripts/skill.sh run --stdin
```

## Determinism

- Use stable sorting for all enumerations and ranked outputs.
- Never emit nondeterministic IDs.
- Do not emit timestamps in the inventory/receipt outputs.
- Git status mapping (when enabled) is derived exclusively from `git status --porcelain=v1 -z` and is merged deterministically by path.

## Guardrails

- Enumerate-before-reason: inventory is authoritative; narrative is derived from emitted artifacts.
- Explicit scope: every run declares root, depth, include_hidden, ranking, and caps.
- No gitignore emulation: gitignore behavior is only applied via git (when enabled).
- No mutation: never create/edit/delete entries as part of listing.
- No content search: do not read file contents.
- Fail closed on schema/config validation errors.
- If git mapping is requested but cannot be performed (git missing / not a repo / git error), the run MUST still be explicit about the condition via the receipt `git` block; per-entry `git_xy`/`git_rename_from` MUST remain null unless git mapping is enabled and successful.

## Mapping (must stay explicit)

- Static guardrails: schema fields, config caps, symlink policy, git policy.
- Quantitative outputs: inventory entries, counts, truncation flags.
- Qualitative judgment: selecting root/ranking/caps from intent (must be explicit in plan).
