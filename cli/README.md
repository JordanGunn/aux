# AUx CLI

Structured I/O layer for agentic workflows — wraps Unix primitives (`rg`, `fd`, `git`, `sed`, `mv`, `curl`, tree-sitter) as deterministic, schema-driven skills with bounded output.

## Installation

```bash
# From repo root
./scripts/install.sh

# Verify dependencies
aux doctor
```

## Benchmarks

Across model tiers and task types, aux skills reduce tool calls by **53–93%** and tokens
by **9–46%** while maintaining or improving output quality.

| Task | Skill | Token Δ | Tool call Δ | Notes |
|------|-------|---------|-------------|-------|
| Codebase discovery | `search` | −16 to −36% | −53 to −76% | GPT-5.2, Haiku 4.5 |
| Bulk text replacement | `replace` | **−46%** | **−93%** | Haiku 4.5; 79 occurrences / 6 files |
| Symbol cross-reference | `usages` | −9% | **−80%** | Haiku 4.5 |
| Dependency graph | `deps` | −11% | **−80%** + accuracy† | Haiku 4.5 |
| Semantic git diff | `delta` | +8%‡ | **−71%** | Haiku 4.5 |

> † `aux deps` produced correct coupling values where manual analysis made computation errors.
> ‡ Benchmark snapshot ran with the historical stat-only fallback (tree-sitter not installed). Tree-sitter is now bundled, so semantic symbol output is the default.

**Cross-model**: GPT-5.2 Medium + AUx reduces total context cost to **~0.64×** baseline.
GPT-5.2 Low + AUx achieves comparable quality at **~0.35×** baseline cost.

Full methodology: [`docs/benchmark/`](../docs/benchmark/)

## Commands

| Command | Category | Description |
|---------|----------|-------------|
| `files` | read | Enumerate files by name/glob (fd) |
| `search` | read | Hierarchical pipeline: fd → rg [→ tree-sitter AST] |
| `find` | read | Tree-sitter AST structural search |
| `usages` | analysis | Symbol cross-reference: definitions + references |
| `prune` | analysis | Dead code candidate audit (advisory) |
| `deps` | analysis | Module dependency graph: coupling, cycles, blast radius |
| `delta` | analysis | Semantic git diff: files changed + symbols added/removed |
| `robert` | analysis | Robert C. Martin package design metrics (Go, Python) |
| `ccx` | analysis | Cyclomatic + Cognitive Complexity per function |
| `ck` | analysis | Chidamber & Kemerer class metrics (CBO, DIT, NOC, WMC) |
| `hotspots` | analysis | Growth-weighted complexity hotspots per file |
| `halstead` | analysis | Halstead Software Science metrics (Volume, Difficulty) |
| `npath` | analysis | NPATH acyclic execution path count per function |
| `replace` | write | Bulk fixed-string replacement (dry-run by default) |
| `rename` | write | Move/rename files or directories (dry-run by default) |
| `curl` | network | Agent-optimised HTTP fetch with progressive disclosure |
| `capabilities` | meta | Emit skill registry for agent discovery/routing |
| `doctor` | — | Verify system dependencies |

## Usage

```bash
# Help
aux --help
aux search --help

# Get JSON schema for plan-based invocation
aux search --schema
aux replace --schema

# Enumerate files
aux files --root /path --glob "**/*.py"

# Hierarchical search (fd → rg)
aux search --plan '{"root":"/path","surface":{"globs":["**/*.py"]},"search":{"patterns":[{"value":"TODO"}]}}'

# Symbol cross-reference
aux usages DataProcessor --root /path --glob "**/*.py"

# Bulk replacement (dry-run by default — shows preview without mutating files)
aux replace OldClass NewClass --root /path --glob "**/*.py"
# Apply after reviewing dry-run output:
aux replace OldClass NewClass --root /path --glob "**/*.py" --apply

# Agent bootstrap — emit full skill registry
aux capabilities

# System check
aux doctor
```

## Architecture

AUx has two layers:

**Kernels** — structured I/O wrappers around Unix primitives:

```
rg          → grep_kernel      (content search)
fd          → find_kernel      (file enumeration)
git         → delta_kernel     (change analysis)
sed         → sed_kernel       (text replacement)
mv          → mv_kernel        (filesystem moves)
curl        → curl_kernel      (HTTP fetch)
tree-sitter → query_kernel     (AST queries)
```

**Commands** — semantic ontologies built from kernel combinations:

```
search  = find_kernel + grep_kernel [+ query_kernel]
usages  = grep_kernel + query_kernel
prune   = find_kernel + query_kernel + grep_kernel
delta   = delta_kernel [+ query_kernel]
```

Kernels provide structured I/O over system tools. Commands express user intent as named
semantic operations rather than raw tool chains. Same determinism guarantee, higher-level
abstraction.

**Two invocation modes for every command:**

- Simple: `aux search "pattern" --root /path --glob "*.py"`
- Plan: `aux search --plan '<json>'` — accepts a full plan JSON matching the Pydantic schema

```
commands/<skill>.py   → arg parsing, plan construction, output formatting
plans/schemas.py      → Pydantic models (SearchPlan, ReplacePlan, ...)
kernels/<skill>.py    → deterministic execution
output/               → format_output(), TTY detection, truncation
```

## System Dependencies

| Dependency | Required for |
|-----------|-------------|
| `rg` (ripgrep) | `search`, `usages`, `prune`, `replace` |
| `fd` / `fdfind` | `files`, `search`, `prune`, `deps`, `rename` |
| `git` | `delta` |
| `tree-sitter` | `find`, `usages`, `prune`, `delta`, `deps`, `robert` (bundled core dependency) |
| `httpx` | `curl` (optional; install `aux-skills[curl]`) |

Run `aux doctor` to check availability.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AUX_OUTPUT` | Output format: `json`, `text`, `summary` | `json` |
| `AUX_MAX_MATCHES` | Maximum matches to return | unlimited |
