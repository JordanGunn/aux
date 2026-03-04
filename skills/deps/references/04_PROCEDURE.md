---
description: Step-by-step execution flow for the deps skill.
index:
  - Invocation modes
  - Execution pipeline
  - Output interpretation
  - Metrics reference
---

# Procedure

## Invocation modes

**Full graph mode** (no --target):
```bash
aux deps --root /path/to/src --glob "**/*.py"
```
Returns all files sorted by afferent coupling descending, plus cycle list and summary.

**Target mode** (--target <file>):
```bash
aux deps --root /path/to/src --glob "**/*.py" --target src/kernels/find.py
```
Returns one FileDeps entry with full imports and imported_by lists, plus cycles
containing that file.

**Plan mode**:
```bash
aux deps --plan '{"root":"/path","globs":["**/*.py"]}'
aux deps --plan '{"root":"/path","globs":["**/*.py"],"target":"src/kernels/find.py"}'
```

**Schema**:
```bash
aux deps --schema
```

## Execution pipeline

1. `find_kernel(root, globs)` — enumerate candidate files (fd)
2. Per file: attempt AST import extraction (tree-sitter, if available)
   - Fallback: regex import extraction on raw file content
3. Build `stem_to_path` map from scanned files
4. Resolve each imported module string → abs path via stem match
5. Build `efferent_resolved` (who this file imports) and `afferent_map` (who imports this)
6. DFS cycle detection over resolved graph
7. Compute Ca, Ce, instability per file
8. Sort by afferent descending, apply max_results cap

## Output interpretation

- `files[]` — FileDeps per file, sorted by afferent (most-imported first)
  - `imports` — raw module strings found in import statements
  - `imported_by` — abs paths of files that import this file
  - `efferent` (Ce) — number of unique external modules this file imports
  - `afferent` (Ca) — number of files that import this file
  - `instability` — Ce / (Ca + Ce); null if Ca + Ce == 0
- `cycles[]` — import cycles as lists of abs paths
- `summary.most_coupled` — file with highest afferent coupling
- `summary.cycles_detected` — total cycle count

## Metrics reference

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| Afferent (Ca) | count of files that import this | Higher = more depended-upon = more stable |
| Efferent (Ce) | count of unique modules imported | Higher = more dependencies = more volatile |
| Instability (I) | Ce / (Ca + Ce) | 0 = stable, 1 = unstable |

A module with I ≈ 0 is heavily imported and rarely changes (e.g., utility base).
A module with I ≈ 1 imports many things but nothing imports it (e.g., top-level script).
