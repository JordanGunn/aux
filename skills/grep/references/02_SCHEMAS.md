---
description: Schema contract and pattern semantics.
index:
  - Overview
  - Getting the Schema
  - Pattern Objects
  - Deterministic Mapping
---

# Schemas

## Overview

The plan schema is defined by the `aux` CLI. Always fetch the current schema before building a plan.

## Getting the Schema

```bash
aux grep --schema
# or: bash scripts/skill.sh schema
```

This returns the JSON Schema that `--plan` input must validate against.

## Pattern Objects

Content patterns (`patterns[]`):

- `kind`: `fixed` (literal) or `regex` (default)
- `value` (required): non-empty string

File filters:

- `globs[]` — include files matching glob
- `excludes[]` — exclude files matching glob

## Deterministic Mapping

Mapping rules:

- `kind=fixed` → `rg --fixed-strings <value>`
- `kind=regex` → `rg <value>` (default rg mode)
- `--fixed` flag in simple mode sets all patterns to `kind=fixed`

**Key rule:** globs apply to file selection only, not content matching.
