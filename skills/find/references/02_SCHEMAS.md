---
description: Schema contract and pattern semantics (v1 vs v2).
index:
  - Overview
  - Pattern Objects (v2)
  - Deterministic Mapping
  - Parity Checklist
---

# Schemas

## Overview

This skill supports two plan schemas:

- `find_plan_v1` — legacy string patterns (treated as glob name patterns)
- `find_plan_v2` — explicit per-pattern semantics via pattern objects

`find_plan_v2` is the preferred schema going forward. It makes regex usage explicit and auditable.

## Pattern Objects (v2)

`find_plan_v2.find.include_patterns[]` and `find_plan_v2.find.exclude_patterns[]` use the same shape:

- `kind` (required): `glob | regex`
- `value` (required): non-empty string

There are **no implicit defaults** in v2. If a pattern is present, `kind` MUST be present.

## Deterministic Mapping

fd semantics:

- fd default pattern mode is **regex**
- `--glob` switches to **glob**

Mapping rules:

- include `kind=glob` → `fd --glob <value> <root>`
- include `kind=regex` → `fd <value> <root>`
- exclude `kind=glob` → may be passed as `--exclude <value>` to reduce surface
- exclude `kind=regex` → applied deterministically as a post-filter to results

## Parity Checklist

When updating schemas, keep these aligned with `grep`:

- Pattern objects must always declare `kind`
- Max pattern length limits must be enforced or fail closed
- Globs must remain in the file-selection domain (not content matching)

