---
description: Identity and scope of the regex skill.
index:
  - Identity
  - Scope
  - Constraints
---

# Summary

## Identity

regex is a single skill that performs deterministic, auditable pattern matching and extraction over text.
It converts imprecise human intent into explicit regex patterns and executes structured extraction.
The output is matched content with capture groups suitable for further processing.

## Scope

regex answers what patterns exist in text, what specific values match, and what can be extracted.
It does not modify content, explain semantics, or validate correctness beyond pattern matching.
It does not replace parsing; it governs what to parse.

## Constraints

Execution is deterministic and reproducible for a given pattern and input.
All patterns are visible in the invocation and echoed in output.
No hidden state, learning, or semantic inference is introduced.
