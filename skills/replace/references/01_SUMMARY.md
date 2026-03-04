---
description: Identity and scope of the replace skill.
index:
  - Identity
  - Scope
  - Constraints
---

# Summary

## Identity

replace is a single-purpose skill: find every occurrence of an exact string and replace it with another string across a set of files.

It is a thin interface over `aux sed`, restricted to fixed-string substitution. No regex. No AST queries. No mode selection.

## Scope

replace answers: "if I replace every occurrence of X with Y in these files, what changes?" It produces a diff for review, then applies on explicit instruction.

It does not handle:
- Regex patterns (use `aux sed` via plan mode for that)
- AST-scoped replacements (use `aux find` to locate + manual edits)
- Semantic understanding of what the identifier means

## Constraints

- Fixed-string only: `old` and `new` are treated as literal strings, not patterns
- Case-sensitive by default
- Two phases are mandatory: dry-run first, then apply
- Deterministic: same plan always produces same diff and plan_hash
