# ccx — Cyclomatic + Cognitive Complexity Per Function

**Version:** 0.1.0 | **Type:** Read-only | **Tier:** Analysis

## What it does

`aux ccx` computes two complementary complexity metrics for every function in
a codebase, in a single tree-sitter AST traversal per file:

- **Cyclomatic Complexity (CCX)** — McCabe's 1976 metric, the count of
  linearly independent paths through a function. Every `if`, `elif`, loop,
  `case`, `catch`, ternary, and short-circuit boolean operator adds one path.
- **Cognitive Complexity (CogC)** — Campbell's 2018 metric, which adds a
  nesting penalty (deeper code costs more) and collapses homogeneous boolean
  operator sequences. Correlates more closely with the subjective experience
  of reading difficult code.

The skill is named after the metric, not a person, because it bundles two
metrics from two different authors. The primary zone classification uses CCX
(canonical thresholds); CogC is reported as a supplementary signal in the
interpretation string when it diverges meaningfully from CCX.

`ccx` is the **method-level** complexity primitive in the aux toolkit. Where
`robert` answers package-level design quality and `deps` answers file-level
import coupling, `ccx` answers a more granular question: which individual
functions are too complex to test or read?

## Quick start

```bash
# Analyze every supported language under ./src
aux ccx --root ./src

# Restrict to Python only
aux ccx --root ./src --language python

# Multi-language explicit list
aux ccx --root ./src --language python --language go

# Filter to moderate-or-worse functions only
aux ccx --root ./src --min-ccx 11

# Cap output at top 20 worst offenders
aux ccx --root ./src --max-results 20

# Plan mode
aux ccx --plan '{"root":"./src","languages":["python","go"],"min_ccx":11}'

# Schema
aux ccx --schema
```

## Arguments

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--root` | path | required | Search root directory |
| `--language` | name | (auto) | Restrict to one language (repeatable) |
| `--glob` | pattern | (lang default) | Override include glob (repeatable) |
| `--exclude` | pattern | — | Exclude glob (repeatable) |
| `--hidden` | flag | false | Include hidden files |
| `--no-ignore` | flag | false | Don't respect gitignore |
| `--max-results` | int | unlimited | Cap on functions in output (post-sort) |
| `--min-ccx` | int | 1 | Filter — only functions with ccx ≥ N |
| `--plan` | JSON | — | Full plan JSON (overrides other options) |
| `--schema` | flag | — | Print JSON schema and exit |

When no `--language` is given, ccx auto-detects every file with a supported
extension and analyzes them together. The result includes a `summary.languages`
map showing how many functions were found per language.

## Output format

```json
{
  "summary": {
    "languages": { "python": 142, "go": 37 },
    "files_searched": 58,
    "functions_analyzed": 179,
    "zone_counts": { "simple": 154, "moderate": 18, "complex": 6, "untestable": 1, "unknown": 0 },
    "guidance": [
      "src/processor.py:88 process_batch (Untestable): CCX=63, CogC=89. Split this function into independently testable parts.",
      "src/router.py:42 dispatch (Complex): CCX=24, CogC=31. Refactor candidate — extract helpers or flatten nested conditionals."
    ]
  },
  "functions": [
    {
      "name": "process_batch",
      "file": "src/processor.py",
      "path": "/abs/path/src/processor.py",
      "line": 88,
      "end_line": 247,
      "language": "python",
      "ccx": 63,
      "cog": 89,
      "zone": "untestable",
      "interpretation": "Untestable (CCX=63, CogC=89). Exhaustive path coverage is impractical. Split this function into independently testable parts."
    }
  ],
  "files": [
    {
      "file": "src/processor.py",
      "path": "/abs/path/src/processor.py",
      "language": "python",
      "function_count": 8,
      "max_ccx": 63,
      "mean_ccx": 12.5,
      "sum_ccx": 100,
      "max_cog": 89,
      "mean_cog": 18.2,
      "sum_cog": 146,
      "untestable_count": 1
    }
  ],
  "errors": []
}
```

## Metrics reference

| Metric | Definition | Range | Meaning |
|--------|------------|-------|---------|
| CCX | 1 + (decision points) | ≥ 1 | Linearly independent paths through the function |
| CogC | sum of weighted decision contributions | ≥ 0 | Subjective reading difficulty |
| `function_count` | per file | ≥ 0 | Functions discovered in the file |
| `max_ccx` / `max_cog` | per file | ≥ 0 | Worst function in the file |
| `mean_ccx` / `mean_cog` | per file | ≥ 0 | File-wide average |
| `sum_ccx` / `sum_cog` | per file | ≥ 0 | File-wide total |
| `untestable_count` | per file | ≥ 0 | Functions with CCX > 50 |

### Decision points counted

- `if` / `elif` / `else if` (each branch except the first)
- `for`, `while`, `do-while` loops
- `case` / `when` clauses (each)
- `catch` / `except` / `rescue`
- Ternary expressions
- Each occurrence of `&&` / `||` / `??` / `and` / `or`
- `match_arm` (Rust), `case_clause` (Python PEP 634)

### Decision points NOT counted

- `else` clauses (the `if` already counted)
- `default` cases (fall-through, not a decision)
- Rust `?` operator (early return, not a branch)
- TypeScript `conditional_type` (type-level, no runtime path)
- Comprehension and generator-expression `for`/`if` clauses (single expression)
- Rust `loop` keyword (unconditional)

The comprehension exclusion matches SonarQube and diverges from Radon. The
comprehension is treated as a single expression rather than a control-flow
structure.

## Zone reference

| Zone | CCX range | Meaning |
|------|-----------|---------|
| `simple` | 1-10 | Low risk. Straightforward to test. |
| `moderate` | 11-20 | Medium risk. More paths, more test cases. |
| `complex` | 21-50 | High risk. Refactor candidate. |
| `untestable` | 51+ | Exhaustive path coverage is impractical. |
| `unknown` | n/a | Could not parse — see errors. |

The `simple` upper bound (10) is McCabe's original recommendation for
"well-structured" code. The `untestable` lower bound (51) is the SEI/NIST
practitioner consensus that combinatorial path coverage becomes infeasible
beyond 50.

## CCX vs CogC

The two metrics complement each other. CCX is older, more universally
recognised, and measures the *number of test cases* required for full path
coverage. CogC is newer, accounts for nesting depth, and measures the
*reading effort* required to understand the function.

A function with `CCX=8, CogC=8` is uniformly complex — eight paths, eight
units of cognitive effort. A function with `CCX=8, CogC=20` has the same
number of paths but is much harder to read because the branches are deeply
nested. The interpretation string flags this divergence:

> Simple (CCX=8, CogC=20 (heavy nesting)). Low cyclomatic complexity but
> readability cost exceeds path cost.

When CogC ≥ 1.5 × CCX and CCX ≥ 3, the function is flagged as nesting-heavy
even if its CCX places it in the `simple` zone. Such functions should be
flattened, not split.

## Supported languages

| Language | Extensions |
|----------|------------|
| Python | `.py` |
| JavaScript | `.js`, `.mjs`, `.cjs` |
| TypeScript | `.ts`, `.tsx` |
| Go | `.go` |
| Rust | `.rs` |
| Java | `.java` |

Files in unsupported languages are skipped silently. Bash files (`.sh`,
`.bash`) are intentionally excluded — CCX is not meaningful for shell scripts
where the real complexity lives in piped external commands.

C, C++, and Ruby are not supported in this version (deferred due to parser
quirks, macro handling, and goto semantics). They will be added in a follow-up.

## Composing with other skills

```bash
# Find the worst-offender functions, then read the file the worst lives in
aux ccx --root ./src --max-results 5
aux find --file src/processor.py --query '(function_definition name: (identifier) @name)'

# Pre-refactor baseline → make changes → post-refactor measurement
aux ccx --root ./src/router.py
# (refactor)
aux ccx --root ./src/router.py

# Combine method-level (ccx) and package-level (robert) for full picture
aux ccx --root ./src --language python
aux robert --root ./src --language python

# CI gate: fail if any complex-or-worse functions exist in touched files
aux ccx --root ./src/touched_dir --min-ccx 21 | jq '.functions | length'
```
