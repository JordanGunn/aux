# AGENTS INSTRUCTIONS

## Skill Locations

All skills live under `skills/`:

| Skill | Manifest Path |
|-------|---------------|
| grep  | `skills/grep/SKILL.md` |
| find  | `skills/find/SKILL.md` |
| diff  | `skills/diff/SKILL.md` |
| ls    | `skills/ls/SKILL.md` |

## CLI Execution

Skills invoke the `aux` CLI as their execution backend:

```bash
aux grep --help
aux find --help
aux diff --help
aux ls --help
aux doctor  # Check system dependencies
```

## For ASI Skill Design

Refer to the ASI framework at:

- /home/jgodau/work/personal/asi/AGENTS.md
