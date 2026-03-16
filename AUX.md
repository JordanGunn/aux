# AUx Skills

## Overview

AUx is a read-only, deterministic CLI for agentic code navigation. Each skill is a
single-purpose tool that replaces multiple Glob+Read+Grep round trips with one structured
call. Default behavior never mutates the filesystem — mutating skills (`replace`, `rename`)
require explicit opt-in.

## CLI

Install: `uv tool install aux-skills` (requires uv, rg, fd, git).

Two invocation modes for every skill:

```
aux <skill> <args>                    # simple mode
aux <skill> --plan '<json>'           # plan mode (structured JSON input)
aux <skill> --schema                  # print JSON schema (source of truth for field names)
```

Schema-first workflow: run `aux <skill> --schema` before writing a plan to confirm field names.

## Skills Index

- **search**: Find files containing a pattern, scoped by type/directory. Replaces multiple Glob+Grep calls. Answers: "Which files contain this pattern?"
- **files**: Enumerate files by name/glob/type. Pre-flight discovery before reads or operations. Answers: "What files exist matching this pattern?"
- **find**: Structure-aware AST search via tree-sitter. Regex cannot express code structure. Answers: "Where does this code structure appear?"
- **usages**: Symbol cross-reference — definitions and references. Pre-flight before rename, delete, or audit. Answers: "Where is this symbol defined and used?"
- **replace**: Bulk fixed-string replacement, dry-run by default. Eliminates O(N) Grep+Read+Edit per file. Answers: "Replace every occurrence of X with Y."
- **rename**: Move or rename files and directories, batch, dry-run by default. Replaces Glob enumeration and batched mv. Answers: "Rename or move this file to a new path."
- **deps**: Import graph — coupling, instability, cycles. Blast-radius analysis before refactor or delete. Answers: "What imports this module? Any cycles?"
- **delta**: Semantic git diff — files and symbols changed. Session drift, PR summary, refactor verification. Answers: "What changed between these two refs?"
- **prune**: Dead code candidates, advisory only. Starting point for cleanup efforts. Answers: "What might be unused in this codebase?"
- **robert**: Package design quality metrics (Martin: coupling, abstractness, main sequence distance). Quantifies structural brittleness per package. Answers: "Is this package in the Zone of Pain? How far from the main sequence?"
- **curl**: HTTP fetch with chunked progressive disclosure. External content without context blowout. Answers: "What does this URL return?"
- **capabilities**: Full skill registry as structured JSON. Bootstrap or ambiguous intent resolution. Answers: "What skills are available for this task?"
