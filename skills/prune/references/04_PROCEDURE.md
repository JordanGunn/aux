---
description: Canonical execution path for the prune skill, including mandatory deeper-dive handoff.
index:
  - Step 1: Gather intent
  - Step 2: Check prerequisites
  - Step 3: Build prune plan
  - Step 4: Execute and present advisory output
  - Step 5: Offer the deeper dive (mandatory)
  - Step 6: Deeper dive execution
  - CLI
  - Output Format
---

# Procedure

## Step 1: Gather intent

- Parse the user's `/prune <prompt>` invocation
- Identify: which root, which file types (globs), which scope (`symbols` / `files`)
- Note any explicit `max_refs` threshold or `max_symbols` cap
- Record assumptions explicitly

## Step 2: Check prerequisites

```bash
bash scripts/skill.sh validate
```

If tree-sitter is absent and scope includes `"symbols"`:
- Report the missing dependency
- Offer to run `scope=["files"]` as a fallback (text-only, no tree-sitter required)
- Suggest: `pip install 'aux-skills[query]'`

Get the current schema (source of truth for plan structure):
```bash
bash scripts/skill.sh schema
# or directly: aux prune --schema
```

## Step 3: Build prune plan

- Run `aux prune --schema` to confirm field names
- Choose `scope`: `["symbols"]` (default, requires tree-sitter) or `["files"]` (text-only)
  or both
- Set `globs` to target the relevant file types
- Set `min_name_length` if the default (4) is too permissive or too restrictive
- Set `max_refs=1` to widen beyond zero-ref-only if the codebase uses thin wrappers
- Set `max_symbols` only for very large codebases where performance is a concern

## Step 4: Execute and present advisory output

```bash
# Via stdin
echo '<plan_json>' | bash scripts/skill.sh run --stdin

# Direct CLI
aux prune --plan '<plan_json>'

# Simple mode
aux prune --root /path --glob "**/*.py"
```

**Present the advisory first.** Before summarising candidates, communicate the `advisory` field
from the output verbatim or in equivalent language:

> "This is static analysis only. These candidates have zero detected references. grep cannot see
> dynamic dispatch, reflection, plugin registration, or cross-language calls. Each candidate
> requires human verification before any action."

Then present the candidate list, including `confidence` and `caveats` for each entry.

## Step 5: Offer the deeper dive (mandatory)

After presenting results, the agent MUST offer:

> "Found N candidates. Before I recommend any action, I can trace the full reference chain for
> each using `aux usages` to check for dynamic dispatch or indirect access. Would you like me
> to investigate the high-confidence ones first?"

This offer is **not optional**. It must be made even if:
- Confidence is high for all candidates
- The candidate list is short (even 1 candidate)
- The user said "just find unused code"

If the user says **yes** → proceed to Step 6.
If the user says **no** → present the candidate list as a starting point for manual review only,
and explicitly state that no action should be taken without further investigation.

## Step 6: Deeper dive execution

For each candidate the user selects:

```bash
aux usages <symbol> --root <root> [--glob <glob>]
```

Interpret the `usages` output:
- `definitions`: where is it defined? (expected: the file prune flagged)
- `references`: are there any? If yes, the candidate is NOT dead — remove it from consideration.
- If `references` is empty: the candidate may genuinely be unused, but check `caveats` before
  concluding.

After running `aux usages` for all selected candidates, present consolidated findings:
- Which candidates are confirmed as unreferenced?
- Which had hidden references?
- Which remain uncertain (e.g., dynamic language, short name)?

Only after this deeper-dive phase should the agent offer any mutation plan (rename, replace,
delete). And even then, the user must explicitly approve the specific action.

## CLI

**Get the schema first:**
```bash
bash scripts/skill.sh schema
# or: aux prune --schema
```

**Simple mode:**
```bash
aux prune --root /path/to/src --glob "**/*.py"
aux prune --root /path/to/src --glob "**/*.py" --scope files
aux prune --root /path/to/src --glob "**/*.py" --scope symbols --max-refs 1
```

**Plan mode:**
```bash
cat <<'JSON' | bash scripts/skill.sh run --stdin
{
  "root": "/path/to/src",
  "globs": ["**/*.py"],
  "scope": ["symbols"]
}
JSON
```

**Validate:**
```bash
bash scripts/skill.sh validate
```

## Output Format

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
        "short name (3 chars) — high false-positive risk from unrelated identifiers",
        "python: reflection and dynamic dispatch cannot be detected statically"
      ]
    }
  ],
  "next_steps": {
    "message": "Found 4 candidates (1 high, 2 medium, 1 low). ...",
    "verify_command": "aux usages <symbol> --root /path/to/src --glob \"**/*.py\""
  },
  "errors": []
}
```

`advisory` is always the **first key** in the output. `next_steps` provides the scripted
follow-up command for the deeper-dive phase.
