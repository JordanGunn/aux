---
description: Step-by-step execution flow, metric reference, and output interpretation.
index:
  - Invocation modes
  - Execution pipeline
  - Metrics reference
  - Zone reference
  - Output interpretation
  - Agent usage patterns
---

# Procedure

## Invocation modes

**Simple mode:**
```bash
aux ccx --root /path/to/src
aux ccx --root /path/to/src --language python
aux ccx --root /path/to/src --language python --language go
aux ccx --root /path/to/src --min-ccx 11
aux ccx --root /path/to/src --max-results 20
aux ccx --root /path/to/src --exclude "**/test_*.py"
```

**Plan mode:**
```bash
aux ccx --plan '{"root":"/path"}'
aux ccx --plan '{"root":"/path","languages":["python","go"],"min_ccx":11}'
aux ccx --plan '{"root":"/path","max_results":20}'
```

**Schema:**
```bash
aux ccx --schema
```

**Skill script:**
```bash
./skills/ccx/scripts/skill.sh run --root ./src
./skills/ccx/scripts/skill.sh run --root ./src --language python --min-ccx 11
./skills/ccx/scripts/skill.sh schema
echo '{"root":"./src","languages":["python"]}' | ./skills/ccx/scripts/skill.sh run --stdin
```

## Execution pipeline

1. `find_kernel(root, globs)` — enumerate candidate files for active languages
2. For each file, `detect_language()` resolves the language from file extension
3. Files with no `_LANG_CONFIG` entry, or with extensions in
   `_EXCLUDED_LANGUAGES` (bash), are skipped silently
4. `_parse_file(path, language)` — tree-sitter parse, return `(tree, content_bytes, error)`
5. `find_functions(root_node)` — top-down traversal until a function definition
   node is found; do not descend further into that subtree
6. For each function definition, `_walk_function(node, ...)` walks its body:
   - Decision points (`if`, `for`, `case`, `catch`, ternary, etc.) add `+1`
     to CCX and `+1+nesting_depth` to CogC
   - Compensating decisions (`elif`, `switch_case`, `match_arm`) compensate
     for the parent's nesting bump by using `max(0, depth-1)`
   - Short-circuit boolean operators add `+1` to CCX; CogC adds `+1` only
     when not continuing a same-operator sequence
   - Nested function definitions are recursively processed as their own
     `FunctionMetrics` entries — the parent's walker stops descending into them
7. `_aggregate_file_metrics(functions)` — group by file, compute per-file
   `function_count`, `max_ccx`, `mean_ccx`, `sum_ccx`, `max_cog`, `mean_cog`,
   `sum_cog`, `untestable_count`
8. `_compute_zone(ccx, thresholds)` — classify each function
9. `_interpret(ccx, cog, zone)` — generate human-readable verdict, flagging
   nesting-heavy functions when CogC ≥ 1.5×CCX and CCX ≥ 3
10. Sort functions by `(-ccx, -cog, file, line)`; apply `min_ccx` filter and
    `max_results` cap
11. Build `zone_counts` and `guidance` (one entry per non-simple function)

## Metrics reference

| Metric | Formula | Range | Meaning |
|--------|---------|-------|---------|
| CCX (Cyclomatic Complexity) | 1 + (decision points) | ≥ 1 | Linearly independent paths through the function |
| CogC (Cognitive Complexity) | sum of weighted decision contributions | ≥ 0 | Subjective reading difficulty (Campbell 2018) |
| function_count | per file | ≥ 0 | Functions discovered in the file |
| max_ccx / max_cog | per file | ≥ 0 | Worst function in the file |
| mean_ccx / mean_cog | per file | ≥ 0 | File-wide average |
| sum_ccx / sum_cog | per file | ≥ 0 | File-wide total |
| untestable_count | per file | ≥ 0 | Functions with CCX > 50 |

Decision points counted (per language family):
- **Python**: `if`, `elif`, `for`, `while`, `except`, `conditional_expression`
  (ternary), `case_clause` (PEP 634), `boolean_operator` (`and`/`or`)
- **JavaScript / TypeScript**: `if`, `for`, `for_in`, `for_of`, `while`,
  `do_while`, `switch_case`, `catch`, `ternary`, `binary_expression` filtered
  to `&&`/`||`/`??`
- **Go**: `if`, `for`, `expression_case`, `type_case`, `communication_case`
  (in `select`), `binary_expression` filtered to `&&`/`||`
- **Rust**: `if_expression`, `while_expression`, `for_expression`, `match_arm`,
  `binary_expression` filtered to `&&`/`||`
- **Java**: `if`, `for`, `enhanced_for`, `while`, `do_while`, `switch_label`,
  `switch_rule`, `catch`, `ternary`, `binary_expression` filtered to `&&`/`||`

Decision points NOT counted (deliberately):
- `else` clauses (`else` does not branch — its `if` already counted)
- `default` cases (fall-through, not a decision)
- Rust `?` operator (early return, not a branch)
- TypeScript `conditional_type` (type-level, no runtime path)
- Comprehension / generator-expression `for` and `if` clauses (single expression)
- Rust `loop` keyword (unconditional)

## Zone reference

| Zone | CCX range | Label | Meaning |
|------|-----------|-------|---------|
| `simple` | 1-10 | Simple | Low risk. Straightforward to test. |
| `moderate` | 11-20 | Moderate | Medium risk. More paths, more test cases needed. |
| `complex` | 21-50 | Complex | High risk. Refactor candidate. |
| `untestable` | 51+ | Untestable | Exhaustive path coverage is impractical. |
| `unknown` | n/a | Unknown | Could not parse — see errors. |

The `simple` upper bound (10) is McCabe's original recommendation for
"well-structured" code. The `untestable` lower bound (51) is the SEI/NIST
practitioner consensus that combinatorial path coverage becomes infeasible
beyond 50.

## Output interpretation

- `summary.languages` — `{lang: function_count}` map; confirms which languages
  the kernel actually analyzed
- `summary.zone_counts` — count of functions per zone; scan for `complex` or
  `untestable` first
- `summary.guidance` — prioritized action list; one line per non-simple function
- `summary.functions_analyzed` — total functions found (before truncation)
- `summary.files_searched` — count of files discovered by `find_kernel`
- `functions[]` — sorted by CCX descending; first entry = worst function
  - `name` — function name (or `"<lambda>"` / `"<anonymous>"`)
  - `file` / `path` — relative and absolute file location
  - `line` / `end_line` — 1-based line range of the function definition
  - `ccx` / `cog` — the two complexity numbers
  - `zone` — machine-filterable zone label
  - `interpretation` — human-readable verdict; mentions CogC when it diverges
- `files[]` — per-file aggregates, sorted by `max_ccx` descending

## Agent usage patterns

**Worst-function triage:**
```
1. Run ccx --root <project>
2. Inspect summary.zone_counts: any complex or untestable?
3. If yes, walk summary.guidance from top — these are the highest-leverage
   refactor candidates
4. For each: read interpretation field for specific advice (heavy-nesting flag,
   CCX number, CogC number)
```

**Pre/post refactor measurement:**
```
1. Before refactor: run ccx on the touched file, note the function's CCX and CogC
2. Make changes
3. After refactor: re-run ccx on the same file
4. Report: "function f went from CCX=24 (complex) to CCX=8 (simple)"
```

**CI gate:**
```
1. Run ccx --root <touched-files-area> --min-ccx 21
2. If any functions returned, fail the build
3. The complex/untestable threshold is the gate; lower thresholds can be used
   for stricter teams
```

**Cross-language audit:**
```
1. Run ccx --root <project> with no language filter (auto-detects all supported)
2. Inspect summary.languages to confirm coverage
3. Sort functions by CCX desc to find worst offenders regardless of language
4. CCX is comparable across languages; CogC less so (nesting cost varies)
```
