# Frequently Asked Questions

---

## Why do I need to run bootstrap?

Skills require a Python virtual environment with their dependencies installed. The bootstrap process:

1. Creates a local `.venv` in each skill's `scripts/src/` directory
2. Installs Python dependencies via `uv sync`
3. Validates that the skill can run

A top-level `scripts/bootstrap.sh` (or `bootstrap.ps1`) is provided for convenience to bootstrap all skills at once. You can also bootstrap individual skills via their own `bootstrap.sh` / `bootstrap.ps1` scripts.

**Without bootstrapping, skills will fail with missing module errors.**

---

## Why aren't system dependencies installed automatically?

System dependencies like `rg` (ripgrep), `fd`/`fdfind`, `git`, and `python` are **intentionally not installed** by any skill.

This is a deliberate design choice:

- **No surprises** — Skills never modify your system without explicit approval
- **Transparency** — You control what gets installed and where
- **Portability** — System package managers vary by OS; we don't assume which one you use
- **Security** — Automated installs of system binaries are a supply chain risk

Install these prerequisites manually before bootstrapping. See [QUICKSTART.md](QUICKSTART.md) for installation instructions.

---

## Why don't skills install anything automatically?

Skills are designed to be **read-only** and **non-mutating** by default:

- They never write outside their designated artifact directories (`.aux/`)
- They never install packages, binaries, or modify system state
- They never make network requests (except for dependency installation during bootstrap)

This ensures:

- **Auditability** — You can inspect exactly what a skill does
- **Reproducibility** — Same inputs produce same outputs
- **Trust** — Skills can be safely invoked by agents without fear of side effects

---

## How do agents invoke skills?

Agents do not run skills directly via shell commands. Instead:

1. The agent interprets natural language intent
2. The agent generates a **plan** (JSON) conforming to the skill's schema
3. The agent invokes the skill with the plan via stdin
4. The skill executes deterministically and emits structured output
5. The agent synthesizes the results for the user

This separation ensures the agent handles ambiguity while the skill handles execution.

---

## Can I run skills manually?

Skills are designed for agent invocation, but they can be run manually for debugging or testing:

```bash
# Validate a skill is runnable
./grep/scripts/skill.sh validate

# Run with a plan from stdin
cat plan.json | ./grep/scripts/skill.sh run --stdin

# Run with CLI arguments (skill-specific)
./grep/scripts/skill.sh run --root /path/to/repo --pattern "TODO"
```

However, the intended use is always via an agent that generates appropriate plans.

---

## What is ASI?

[ASI (Agentic Skill Interface)](https://github.com/JordanGunn/asi) is a governance framework for designing deterministic, auditable agent skills.

All skills in this repository are designed in accordance with ASI principles:

- **Deterministic execution** — Same plan produces same results
- **Bounded output** — Results are capped and predictable
- **Auditable artifacts** — Every run produces inspectable receipts
- **Read-only by default** — Skills never mutate without explicit approval

---

## What is asr?

[asr (Agentic Skill Registry)](https://github.com/JordanGunn/asr) is a CLI tool for installing and managing skills across vendors or agentic tooling.

You can use asr to:

- Install skills from registries
- Manage skill versions
- Configure skills for different agents

See the [asr documentation](https://github.com/JordanGunn/asr) for more details.

---

## Why are there both `.sh` and `.ps1` scripts?

Skills support both Unix (bash) and Windows (PowerShell) environments:

- `.sh` scripts — For Linux, macOS, and WSL
- `.ps1` scripts — For native Windows PowerShell

Both scripts implement the same interface and produce the same results.

---

## Where do skills write output?

Skills write artifacts to a `.aux/` directory in the working directory:

```
.aux/
  grep/<query_id>_receipt.json
  find/<query_id>_receipt.json
  diff/<comparison>_receipt.json
  diff/<comparison>.patch
  ls/<query_id>_receipt.json
```

This directory can be safely added to `.gitignore` if you don't want to track artifacts.

---

## How do I add a new skill?

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines on adding new skills. Key points:

- Each skill is fully self-contained
- Skills follow ASI conventions
- Skills must be read-only and deterministic
- Skills must have schemas, scripts, and documentation
