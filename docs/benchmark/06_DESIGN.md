# Experiment Design

## Methodology

Each experiment runs the **same prompt** in two sessions:

| Session | Configuration                                                             |
|---------|---------------------------------------------------------------------------|
| **A**   | Native IDE tools only: built-in grep, file reading                        |
| **B**   | AUx skills enabled: structured grep/find/diff/ls with explicit parameters |

All other factors held constant. Metrics captured:

- tokens used
- tool calls
- files read
- coverage quality

## Test Codebase

The subject is a **production SaaS monorepo** hosting a distributed cloud-computing platform:

| Metric         | Value                                                  |
|----------------|--------------------------------------------------------|
| Source files   | ~900                                                   |
| Lines of code  | ~110,000                                               |
| Disk size      | 1.6 GB                                                 |
| Languages      | Go, TypeScript, Python, YAML, Bicep, Shell, Dockerfile |
| Frameworks     | Kubernetes, Helm, ArgoCD, React, Gin, GraphQL          |
| Cloud          | Azure (Bicep IaC)                                      |

This represents a **high-complexity, polyglot environment** typical of enterprise platform teams.

## Task: Cross-Cutting Analysis

The prompt asks the agent to inventory authentication and authorization code across the entire codebase.

This is a **worst-case scenario** for agents:

- Auth touches backend middleware, deployment configs, Helm charts, IaC, Clients, etc
- Architectural roots scattered across 6+ directories
- Each directory contains dozens of subdirectories and hundreds of files
- **No single directory tells the whole story**

An agent without structured discovery tools tends to:

- Tunnel-vision on one directory
- Miss cross-cutting concerns (ignore related architectural components)
- Consume excessive context reading irrelevant files

AUx skills seek to address this by enabling bounded, repo-wide surface scans before deep file reads.

---

## Experiment 06: Write Task (aux sed)

A second experiment measures `aux sed` on a **bulk-refactoring task** — a different task type to the discovery experiments above.

| Session | Configuration                                               |
|---------|-------------------------------------------------------------|
| **A**   | Native tools only: Bash grep + Read + Edit (one file at a time) |
| **B**   | `aux sed` skill: plan → dry-run diff → apply               |

### Test Codebase

Synthetic Python codebase (reproducible, controlled ground truth):

| Metric       | Value                              |
|--------------|------------------------------------|
| Files        | 18 Python files across 5 packages  |
| LOC          | ~1,800                             |
| Target       | 114 occurrences of `process_event` |
| Task         | Rename `process_event` → `handle_event` everywhere |

The synthetic design gives an exact ground truth (114 occurrences in 18 files) and a clear correctness check (0 residual occurrences after completion).

### Why This Task

Bulk rename is a worst-case scenario for the read-Edit cycle: an agent must read every file before editing it. The `aux sed` approach inverts this — it reviews only the diff, not the full file content. The token cost gap should be structural and proportional to file size, not incidental.

---

## Experiment 07: File Rename with Scope Inference (aux rename)

A third experiment measures `aux rename` on a **filesystem rename task requiring domain inference** — distinct from both discovery and content-rewriting. The task is moving files, but the set of qualifying files cannot be determined by filename pattern alone.

| Session | Configuration                                                           |
|---------|-------------------------------------------------------------------------|
| **A**   | Native tools only: Glob (discover) + Bash mv (batched loop)             |
| **B**   | `aux rename` skill: Glob → RenamePlan JSON → dry-run → apply           |

### Test Fixture

Synthetic streaming-platform project (reproducible, with scope-inference ground truth):

| Metric    | Value                                                                       |
|-----------|-----------------------------------------------------------------------------|
| Files     | 17 Python files across 7 directories                                        |
| Structure | `pipeline/`, `connectors/`, `workers/` (qualifying) + `utils/`, `auth/`, `api/`, `cli/` (decoys) |
| Qualifying | 12 files: `*reader*` → `*source*`, `*writer*` → `*sink*` in stream dirs   |
| Decoys    | 5 files: same keywords in infrastructure dirs — must NOT be renamed          |
| Task      | Kafka Streams vocabulary migration: reader→source, writer→sink              |

Ground truth: 12 renames, 5 files unchanged. Scope boundary derivable from directory structure
(path-based inference sufficient; file content provides additional confirmation).

Fixture path: `docs/benchmark/fixtures/rename_inference/fixture/platform/`
Session working directories: `run_a/platform/` and `run_b/platform/` (independent copies, no cross-contamination).

### Why This Task

The previous benchmark (`*_test.py → test_*.py`) was fully determined by filename alone — any
agent could batch all renames in one shell loop without exercising scope judgment. This design
introduces 5 decoy files with the same keywords but different domains, requiring the agent to
distinguish qualifying files from infrastructure utilities. The inference requirement is:

- `pipeline/event_reader.py` → rename (stream data component)
- `auth/token_reader.py` → do NOT rename (auth utility that happens to read)

Both sessions solved inference via directory structure (no file reads required in either session).
The experiment tests safety guarantees and audit trail, not scope-inference capability.

---

## Experiment 08: Symbol Cross-Reference (aux usages)

| Session | Configuration                                                           |
|---------|-------------------------------------------------------------------------|
| **A**   | Native tools only: Bash (list files) + Grep (pattern search) + Read    |
| **B**   | `aux usages` skill: one plan call, optional verify read                 |

### Test Fixture

Synthetic Python eventbus package (reproducible):

| Metric    | Value                                                                                 |
|-----------|---------------------------------------------------------------------------------------|
| Files     | 7 Python files across 4 directories                                                   |
| Structure | `core/` (handler, dispatcher), `plugins/` (auth, logging), `tests/` (2 test files), `__init__.py` |
| Symbol    | `EventHandler` — class definition in `handler.py`, referenced across all 6 other files |
| Ground truth | 33 total occurrences: 1 class definition + 32 references across 7 files            |

Fixture path: `docs/benchmark/fixtures/usages/fixture/eventbus/`

### Why This Task

Symbol cross-reference is one of the most common agent tasks. An agent without structured
tooling must Grep for the symbol, collect matched files, then Read each file. An agent with
`aux usages` gets all occurrences (with file, line, kind) in one structured call.

Note: tree-sitter was unavailable in this environment. With tree-sitter, definition sites would
be distinguished from references semantically. Without it, all occurrences are tagged "reference".

---

## Experiment 09: Module Dependency Graph (aux deps)

| Session | Configuration                                                           |
|---------|-------------------------------------------------------------------------|
| **A**   | Native tools only: Bash (list files) + Read (one per .py file)         |
| **B**   | `aux deps` skill: one plan call, optional verify                        |

### Test Fixture

Synthetic Python pipeline package (reproducible, exact coupling ground truth):

| Metric         | Value                                                    |
|----------------|----------------------------------------------------------|
| Files          | 8 Python files across 4 directories                      |
| Structure      | `core/` (engine, runner, config), `processors/` (processor, transformer), `api/` (server, routes), `utils/` (helpers) |
| Ground truth   | config.py Ca=4 (most-imported), routes.py I=1.0 (highest instability), cycles=[] |

Import graph: `routes → server → {engine, transformer} → {config, runner, processor} → config`

Fixture path: `docs/benchmark/fixtures/deps/fixture/pipeline/`

### Why This Task

Module coupling metrics require reading every file and then computing a graph — two steps that
are each error-prone at scale. This benchmark tests both efficiency (fewer reads) and accuracy
(correct graph computation). Session A made two metric errors on an 8-file graph; Session B was
correct.

---

## Experiment 10: Change Enumeration (aux delta, stat-only)

| Session | Configuration                                                           |
|---------|-------------------------------------------------------------------------|
| **A**   | Native tools only: Bash (multiple git diff commands)                   |
| **B**   | `aux delta` skill in stat-only mode (tree-sitter unavailable)          |

### Test Fixture

The aux repo itself, using commit range `HEAD~7..HEAD~6` (initial CLI addition):

| Metric    | Value                                             |
|-----------|---------------------------------------------------|
| Scope     | `cli/src/aux/**/*.py` (filtered by glob)          |
| Files     | 23 Python files added                             |
| Ground truth | Top 3 by lines: kernels/grep.py (203), kernels/ls.py (193), commands/grep.py (186) |

### Why This Task

Git change enumeration tests whether `aux delta` provides a useful abstraction over raw git
output. This benchmark intentionally captures the stat-only fallback (tree-sitter not installed)
to establish the honest baseline. The semantic advantage (symbol names added/removed) requires
tree-sitter; without it, native git is more token-efficient. The tool-call reduction (71%) holds
regardless of tree-sitter availability.
