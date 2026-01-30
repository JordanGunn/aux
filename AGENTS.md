# AGENTS INSTRUCTIONS

## Skill Locations

All skills live under `skills/`:

| Skill | Manifest Path          |
|-------|------------------------|
| grep  | `skills/grep/SKILL.md` |
| find  | `skills/find/SKILL.md` |
| diff  | `skills/diff/SKILL.md` |
| ls    | `skills/ls/SKILL.md`   |

## CLI Execution

Skills invoke the `aux` CLI as their execution backend:

```bash
aux grep --help
aux find --help
aux diff --help
aux ls --help
aux doctor  # Check system dependencies
```

## Schema (Source of Truth)

Always fetch the current schema before building a plan:

```bash
aux grep --schema
aux find --schema
aux diff --schema
aux ls --schema
```

## For ASI Skill Design

Refer to the ASI framework at:

- [ASI (Agentic Skill Interface)](https://github.com/JordanGunn/asi)
