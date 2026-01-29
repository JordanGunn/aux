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

- `grep_plan_v1` — legacy string patterns + a global `mode` (`fixed | regex`)
- `grep_plan_v2` — explicit per-pattern semantics via content pattern objects, and globs restricted to file selection

`grep_plan_v2` is the preferred schema going forward.

## Pattern Objects (v2)

Content patterns (`grep_plan_v2.search.content_patterns[]`):

- `kind` (required): `fixed | regex`
- `value` (required): non-empty string

File filters (`grep_plan_v2.search.file_filters`):

- `include_globs[]` — passed as `rg --glob <glob>`
- `exclude_globs[]` — passed as `rg --glob !<glob>`

There are **no implicit defaults** in v2. If a pattern is present, `kind` MUST be present.

## Deterministic Mapping

Mapping rules:

- content `kind=fixed` → `rg --fixed-strings <value>`
- content `kind=regex` → `rg <value>` (default rg mode)

**Key rule:** globs never apply to content matching. They are only used for file selection.

## Parity Checklist

When updating schemas, keep these aligned with `find`:

- Pattern objects must always declare `kind`
- Max pattern length limits must be enforced or fail closed
- Globs must remain in the file-selection domain (not content matching)

