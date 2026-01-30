---
description: Schema contract and pattern semantics.
index:
  - Overview
  - Getting the Schema
  - Plan Fields
  - Deterministic Mapping
---

# Schemas

## Overview

The plan schema is defined by the `aux` CLI. Always fetch the current schema before building a plan.

## Getting the Schema

```bash
aux find --schema
# or: bash scripts/skill.sh schema
```

This returns the JSON Schema that `--plan` input must validate against.

## Plan Fields

Key fields in the plan:

- `root` (required): Search root directory
- `globs[]`: Include files matching glob
- `excludes[]`: Exclude files matching glob
- `type`: Entry type filter (`file`, `directory`, `any`)
- `max_depth`: Maximum search depth
- `max_results`: Maximum results to return

## Deterministic Mapping

fd semantics:

- `--glob` patterns for file name matching
- `--exclude` patterns for exclusions

**Key rule:** globs apply to file name selection only.

