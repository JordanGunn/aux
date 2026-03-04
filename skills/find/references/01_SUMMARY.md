---
description: Identity and scope of the find skill.
index:
  - Identity
  - Scope
  - Constraints
---

# Summary

## Identity

find is a single read-only skill that performs deterministic, auditable structural search over a codebase using tree-sitter AST queries.
It converts imprecise human intent into explicit query patterns and executes them against parsed syntax trees.
The output is a list of matched captures suitable for code analysis and surface discovery.

## Scope

find answers: where do structural patterns appear, what names/expressions match a given AST shape, and how do constructs distribute across a codebase.
It does not modify files. It does not infer behavior, architecture, or semantics.
It is the read-only counterpart to sed query mode — analysis without mutation.

Supported languages (requires grammar packages): Python, JavaScript, TypeScript, Rust, Go, Java, C, C++, Ruby, Bash.

## Constraints

Execution is deterministic and reproducible for a given plan JSON.
All query criteria are visible in the invocation and echoed in output.
No hidden state, indexing, or semantic inference is introduced.
Read-only — no file writes occur under any circumstances.
