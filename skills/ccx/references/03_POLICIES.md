---
description: Explicit prohibitions and mandates for the ccx skill.
index:
  - Prohibitions
  - Mandates
  - Scope limits
---

# Policies

## Prohibitions

ccx MUST NOT:
- Write to any file under any circumstances
- Compute complexity from regex parsing of source text — tree-sitter is the
  only supported front-end. There is **no text-tier fallback**. Counting
  decision points by regex is catastrophically unreliable (nested quotes,
  comments, stringified code masquerading as control flow), and silent
  numerical errors are worse than no number at all.
- Process Bash, C, C++, or Ruby files in this version — they are skipped
  silently. Bash is permanently excluded; the others are deferred to a future
  iteration.
- Roll a lambda's or nested function's complexity into the enclosing function
- Produce a CCX value below 1 — every function has at least one path
- Cache or persist state between invocations
- Count comprehension or generator-expression `for` and `if` clauses as
  decision points (matches SonarQube; diverges from Radon)

## Mandates

ccx MUST:
- Return the same output for the same plan JSON (determinism)
- Compute both CCX and CogC for every function in a single AST traversal
- Sort `functions` output by CCX descending, with CogC as the tiebreaker
- Include `zone` as a machine-readable field on every function entry
- Include `interpretation` as a human-readable verdict on every function entry
- Include `guidance` in summary for every function with zone moderate or worse
- Include all errors encountered in the `errors` field (never silently swallow)
- Report `truncated: true` when `max_results` cap is applied
- Emit lambdas, arrow functions, and nested function definitions as their own
  `FunctionMetrics` entries with name `"<lambda>"` or `"<anonymous>"` when
  no name is available
- Apply the `min_ccx` filter as a post-walk filter (not a pre-walk skip),
  so that lambdas with simple bodies inside complex parents still appear in
  the result if they pass the threshold

## Scope limits

Decision-point counting is intentionally conservative:
- `else` clauses do not count (the `if` already counted)
- `default` cases in switch statements do not count (fall-through, not a decision)
- Rust's `?` operator is not counted (early return, not a branch — opinionated)
- TypeScript `conditional_type` is not counted (type-level, no runtime path)
- Comprehension `for`/`if` clauses are not counted (single expression, not control)
- Container nodes (`switch_statement`, `match_statement`, `select_statement`,
  Rust `match_expression`) are nesting-only — they do not contribute a decision
  themselves; their case/arm children do

Threshold parameterisation is intentionally limited in this version:
- McCabe's `(10, 20, 50)` thresholds are hardcoded as the default
- The kernel API accepts a `thresholds` parameter for testing alternative
  values, but the plan schema does not expose it (avoids bikeshedding around
  what "complex" means in different teams)

Interpretation of metrics is advisory:
- A `complex` or `untestable` zone classification does not mandate refactoring
  — it surfaces a complexity tension for human judgment
- A function with CogC ≥ 1.5×CCX is flagged in its interpretation string as
  having "heavy nesting" — readability cost exceeds path count
- Tree-sitter grammar quirks (e.g. JS `else if` parsing as `else { if }`) are
  handled by the walker design but may produce surprising counts on
  unidiomatic code patterns
