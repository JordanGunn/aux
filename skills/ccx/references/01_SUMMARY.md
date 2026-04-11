---
description: Identity and scope of the ccx skill.
index:
  - Identity
  - Scope
  - Constraints
---

# Summary

## Identity

ccx is a single read-only skill that computes per-function complexity metrics
from source files: McCabe Cyclomatic Complexity (CCX, 1976) and Campbell
Cognitive Complexity (CogC, 2018). Both metrics are produced in a single
tree-sitter AST traversal per file. The skill is named after the metric, not
a person, because it bundles two metrics from two different authors.

ccx is the **method-level** complexity primitive in the aux toolkit. Where
`robert` answers package-level design quality and `deps` answers file-level
import coupling, ccx answers a more granular question: which individual
functions are too complex to test or read?

The two metrics complement each other:
- **CCX** counts linearly independent paths through a function — every `if`,
  loop, `case`, `catch`, and short-circuit operator adds one path. CCX is the
  oldest established complexity metric (McCabe, 1976) with universally
  recognized thresholds.
- **CogC** is a more recent metric (Campbell, 2018) that adds a nesting
  penalty (deeper code costs more) and collapses homogeneous boolean operator
  sequences. It correlates more closely with the subjective experience of
  reading difficult code.

ccx ships both numbers per function. The primary zone classification uses
CCX (canonical thresholds). CogC is reported as a supplementary signal in
the interpretation string when it diverges meaningfully from CCX, indicating
that nesting is the dominant complexity contributor.

## Scope

ccx answers: which functions in this codebase are most expensive to test,
most difficult to read, and most likely to harbor bugs?

The execution pipeline:

1. `find_kernel` (fd) — enumerate candidate files by language-specific glob
2. For each file, `_parse_file` — tree-sitter parse with the appropriate grammar
3. `_walk_function` — per function definition, recursively walk the body:
   - Each decision point: `+1` to CCX, `+1+nesting_depth` to CogC
   - Each short-circuit boolean operator: `+1` to CCX, `+1` to CogC unless
     continuing a same-operator sequence
   - Nested function definitions are emitted as separate FunctionMetrics
     entries — their CCX/CogC is not rolled into the parent
4. `_aggregate_file_metrics` — compute per-file maxima, means, sums
5. `_compute_zone` — classify each function by CCX threshold
6. Sort functions by CCX descending, apply `min_ccx` filter and `max_results` cap
7. Build per-zone counts and a guidance list of non-simple functions

Supported languages: **Python**, **JavaScript**, **TypeScript**, **Go**,
**Rust**, **Java**.

Detection is by file extension (via `aux.util.treesitter.detect_language`).
Files in unsupported languages are skipped silently. Bash files are
explicitly excluded — see `03_POLICIES.md`.

## Constraints

Execution is deterministic and reproducible for a given plan JSON.
Read-only — no file writes occur under any circumstances.
Tree-sitter is **required**. There is no regex text-tier fallback. Files
that fail to parse contribute an error and are skipped.
Cyclomatic Complexity is computed as `1 + (decision points)`. The minimum
value for any function is 1 — every function has at least one path.
Lambdas, anonymous functions, and nested function definitions are emitted as
their own `FunctionMetrics` entries. Their complexity is not folded into the
enclosing function's score.
Method names are emitted plain (e.g. `process_request`), not class-qualified
(`UserController.process_request`). The `file:line` makes disambiguation
unambiguous.
Comprehension and generator-expression `for` and `if` clauses are NOT counted
as decision points. This matches SonarQube; it diverges from Radon. The
comprehension is treated as a single expression rather than a control flow
structure.
McCabe's `1-10 / 11-20 / 21-50 / 51+` thresholds are hardcoded as the default
zone boundaries. They can be overridden via the kernel API (`thresholds`
parameter) but are not exposed on the plan schema in this version.
