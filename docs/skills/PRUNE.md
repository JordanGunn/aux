# prune

**Tiered dead code candidate audit** — advisory output for human verification.

`prune` scans a codebase for symbols and modules with zero detected external references. It is
a first-pass static analysis tool designed to surface candidates for investigation, not a
deletion planner.

> **ADVISORY:** prune output is static analysis only. grep cannot see dynamic dispatch,
> reflection, plugin registration, or cross-language calls. Every candidate requires human
> verification via `aux usages` before any action.

---

## Quick start

```bash
# Symbols scope (requires tree-sitter)
aux prune --root /path/to/src --glob "**/*.py"

# Files scope (text-only, no tree-sitter)
aux prune --root /path/to/src --glob "**/*.py" --scope files

# Both scopes
aux prune --root /path/to/src --glob "**/*.py" --scope symbols --scope files

# Widen threshold (flag symbols with ≤ 1 external ref)
aux prune --root /path/to/src --glob "**/*.py" --max-refs 1

# Plan mode
aux prune --plan '{"root":"/path","globs":["**/*.py"],"scope":["symbols"]}'

# Schema
aux prune --schema
```

---

## Output

`advisory` is always the first key — read it before acting on any candidate.

```json
{
  "advisory": "STATIC ANALYSIS ONLY: These candidates have zero detected references...",
  "summary": {
    "scope": ["symbols"],
    "symbols_analyzed": 47,
    "candidates": 4,
    "by_confidence": { "high": 1, "medium": 2, "low": 1 },
    "files_searched": 12
  },
  "candidates": [
    {
      "symbol": "LegacyExporter",
      "symbol_type": "class",
      "file": "/abs/path/legacy/exporter.py",
      "line": 14,
      "external_refs": 0,
      "confidence": "high",
      "caveats": []
    },
    {
      "symbol": "run",
      "symbol_type": "function",
      "file": "/abs/path/utils/runner.py",
      "line": 42,
      "external_refs": 0,
      "confidence": "low",
      "caveats": [
        "short name (3 chars) — high false-positive risk",
        "python: reflection and dynamic dispatch cannot be detected statically"
      ]
    }
  ],
  "next_steps": {
    "message": "Found 4 candidates (1 high, 2 medium, 1 low). ...",
    "verify_command": "aux usages <symbol> --root /path --glob \"**/*.py\""
  },
  "errors": []
}
```

---

## Scopes

| Scope | Method |
|-------|--------|
| `symbols` | Tree-sitter AST extraction of top-level definitions |
| `files` | Stem-matching across module files |

Default scope is `["symbols"]`. Tree-sitter is a core dependency of `aux-skills`, so
both scopes are always available; `--scope files` exists for cheap, language-agnostic
audits where AST work would be overkill.

---

## Confidence ratings

| Rating | Meaning |
|--------|---------|
| `high` | Long, unique-looking name; no dynamic-language risk |
| `medium` | Moderate name length or dynamic language |
| `low` | Short name, common identifier, dunder, or highly dynamic language — informational only |

`caveats` in each candidate lists the specific reasons confidence is reduced.

---

## Workflow

1. Run `aux prune` to get candidate list
2. Read `advisory` and all `caveats` before forming opinions
3. Run `aux usages <symbol>` for each high/medium candidate to check for hidden references
4. Only after the deeper-dive phase: decide whether to propose any mutation

---

## Plan schema

```bash
aux prune --schema
```

Key fields:

| Field | Default | Description |
|-------|---------|-------------|
| `root` | — | Search root (required) |
| `globs` | `[]` | Include globs |
| `excludes` | `[]` | Exclude globs |
| `scope` | `["symbols"]` | `"symbols"`, `"files"`, or both |
| `language` | auto | Tree-sitter language override |
| `min_name_length` | `4` | Skip symbols shorter than N |
| `max_refs` | `0` | Flag candidates with ≤ N external refs |
| `hidden` | `false` | Include hidden files |
| `no_ignore` | `false` | Don't respect gitignore |
| `max_symbols` | `null` | Cap on symbols analyzed |

---

## Skill layer

```bash
# Validate dependencies
./skills/prune/scripts/skill.sh validate

# Emit schema
./skills/prune/scripts/skill.sh schema

# Emit all reference docs (agent onboarding)
./skills/prune/scripts/skill.sh init

# Run via stdin plan
echo '{"root":"/path","globs":["**/*.py"]}' | ./skills/prune/scripts/skill.sh run --stdin
```
