---
description: Step-by-step execution flow for the delta skill.
index:
  - Invocation modes
  - Execution pipeline
  - Output interpretation
---

# Procedure

## Invocation modes

**Working tree diff** (default — changes vs. HEAD):
```bash
aux delta --root /path
aux delta --root /path --glob "**/*.py"
```

**Since N commits ago**:
```bash
aux delta --root /path --ref-from HEAD~3
```

**Between two refs**:
```bash
aux delta --root /path --ref-from v1.0 --ref-to v2.0
aux delta --root /path --ref-from main --ref-to feature/my-branch
```

**Stat-only** (no tree-sitter needed):
```bash
aux delta --root /path --stat-only
```

**Plan mode**:
```bash
aux delta --plan '{"root":"/path","ref_from":"HEAD~2","globs":["**/*.py"]}'
```

**Schema**:
```bash
aux delta --schema
```

## Execution pipeline

1. Check git availability — error and return if absent
2. `git diff --name-status <ref_from> [<ref_to>]` — get changed file list
3. Apply glob/exclude filters to changed file list
4. `git diff --numstat <ref_from> [<ref_to>]` — get line addition/deletion counts
5. For each changed file (if semantic mode and tree-sitter available):
   - Get old content: `git show <ref_from>:<rel_path>` (empty if Added)
   - Get new content: read from disk (working tree) or `git show <ref_to>:<rel_path>`
   - Extract symbols from each version using DEFINITION_QUERIES (from usages kernel)
   - Compute added / removed / unchanged symbol sets
6. Apply max_files cap; set truncated=true if capped
7. Compute summary totals

## Output interpretation

- `files[]` — FileDelta per changed file
  - `status` — "modified" | "added" | "deleted" | "renamed"
  - `additions` / `deletions` — raw git line counts
  - `symbols` — SymbolDiff or null (null if stat_only or tree-sitter absent)
    - `added` — list of {name, type} new in ref_to
    - `removed` — list of {name, type} present in ref_from, gone in ref_to
    - `unchanged` — list of {name, type} present in both
- `summary` — aggregate totals:
  - `files_changed`, `symbols_added`, `symbols_removed`, `lines_added`, `lines_deleted`
- `ref_from` / `ref_to` — the refs compared ("working tree" if ref_to was None)
