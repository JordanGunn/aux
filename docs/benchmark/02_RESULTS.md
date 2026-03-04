# Results by Model

## GPT-5.2 Medium Reasoning

| Metric               | Without AUx | With AUx   | Delta     |
|----------------------|-------------|------------|-----------|
| **Context consumed** | 182k (47%)  | 117k (30%) | **-36%**  |
| **Tool calls**       | ~30         | 20 (81 ops)| —         |
| **Files read**       | ~30         | 43         | +43%      |
| **Tokens/operation** | 6,067       | 1,444      | **-76%**  |
| **Coverage quality** | Excellent   | Excellent+ | Improved  |

**Outcome**:  
AUx skills reduced context consumption by over a third while enabling deeper analysis (+43% more files read).

## GPT-5.2 Low Reasoning

| Metric               | Without AUx | With AUx  | Delta     |
|----------------------|-------------|-----------|-----------|
| **Context consumed** | 93k (24%)   | 64k (17%) | **-31%**  |
| **Tool calls**       | 9 (36 ops)  | 28        | —         |
| **Files read**       | 22          | 11        | -50%      |
| **Tokens/operation** | 2,583       | 2,286     | **-11%**  |
| **Coverage quality** | Excellent   | Excellent | Same      |

**Outcome**:
AUx skills enabled a cheaper, low-reasoning model to outperform the baseline while reading half as many files.

## Claude Haiku 4.5 (Explore agent vs AUx search)

Same task: auth/authz inventory on the same production monorepo (1,738 source files).
Both sessions used the same model tier. Session A used the built-in Claude Code Explore agent (native Glob/Grep/Read/Bash tools). Session B used `aux search` for all discovery, then targeted reads.

| Metric               | Session A: Explore | Session B: AUx    | Delta    |
|----------------------|--------------------|-------------------|----------|
| **Total tokens**     | 88,344             | 74,307            | **-16%** |
| **Tool calls**       | 49                 | 23                | **-53%** |
| **Files read**       | 26                 | 13                | **-50%** |
| **Discovery calls**  | 16 (Glob+Grep)     | 4 (`aux search`)  | **-75%** |
| **Files surfaced**   | ~387 matched       | ~654 surfaced     | +69%     |
| **Coverage quality** | Very comprehensive | Solid, core paths | Narrower |

**Outcome**:
On Haiku, AUx cut tool calls by 53% and tokens by 16%. Session B surfaced significantly more candidate files (654 vs 387) with 4 structured calls vs 16 ad-hoc searches, but read fewer of them — reflecting the bounded discovery model. Session A's unrestricted exploration produced slightly broader final coverage (IaC/Bicep layer, CLI credential cache, frontend route guards), while Session B captured all critical auth enforcement paths.

The token reduction is lower than the GPT-5.2 experiments (16% vs 31–36%) because Haiku's native exploration is already lean. The tool call and file read reductions (53% and 50%) are consistent with prior results.

## Claude Haiku 4.5 (Native tools vs AUx rename — discovery mode)

Task: rename 12 stream-processing modules across `pipeline/`, `connectors/`, and `workers/` —
migrating from `reader`/`writer` naming to `source`/`sink` (Kafka Streams vocabulary). Five decoy
files with the same keywords exist in `utils/`, `auth/`, `api/`, and `cli/`; they must be left
untouched. The scope boundary is derivable from directory structure alone.

Both sessions used the same model tier (Haiku 4.5). Session A used native Glob and Bash tools.
Session B used `aux rename` in discovery mode (one plan with `root` + `globs` + `rules`, no
prior Glob calls).

| Metric               | Session A: Native        | Session B: AUx rename (discovery) | Delta     |
|----------------------|--------------------------|-----------------------------------|-----------|
| **Total tokens**     | 14,508                   | ~14,000 (projected)               | **~0%**   |
| **Tool calls**       | 3                        | 2                                 | **-33%**  |
| **Rename calls**     | 1 (batched Bash loop)    | 2 (dry-run + apply)               | +1        |
| **Read calls**       | 0                        | 0                                 | Same      |
| **Glob/discovery**   | 1 Glob                   | 0 (built into plan)               | **-100%** |
| **Conflicts caught** | N/A                      | 0 (dry-run verified)              | Safety ✓  |
| **Correctness**      | 12/12 renamed, 5/5 kept  | 12/12 renamed, 5/5 kept           | Same      |
| **plan_hash**        | —                        | `sha256:<receipt>`                | Audit ✓   |

Session A breakdown: 1 Glob (discover all reader/writer files) + 1 Bash (batched mv loop, 12 renames) + 1 Glob (verify).
Session B breakdown: 1 Bash (dry-run with discovery plan) + 1 Bash (apply). Zero Glob calls — `aux rename` discovers files internally using `root` + `globs` + `rules`.

**Outcome**:
Discovery mode eliminates all pre-flight Glob calls. The agent constructs a single `RenamePlan`
JSON with `root`, path-scoped `globs` (e.g. `pipeline/**`, `connectors/**`), and `rules` for
filename substitution, then runs dry-run and apply. The rename kernel handles all discovery
internally — the agent never enumerates candidate files.

Both sessions achieve perfect correctness: all 12 qualifying files renamed, all 5 decoy files
untouched. The token overhead from the previous explicit-mode benchmark (+30%) is eliminated
because the plan is now compact: no `moves` array listing all 12 pairs, just a concise rules
specification. The `plan_hash` receipt and mandatory dry-run gate remain intact.

> **Note**: Session B token count is projected. The v0.1 benchmark (explicit mode, 5 tool calls,
> 18,907 tokens) used a different plan shape where the agent enumerated all 12 pairs manually.

## Claude Haiku 4.5 (Native tools vs `aux replace` — bulk text replacement)

Task: rename the identifier `DataProcessor` to `EventProcessor` across a 9-file Python codebase
(6 files containing 79 occurrences, 3 clean files). Context: domain model rename after migrating
to an event-driven architecture — class definitions, method signatures, type hints, imports,
docstrings, and comments all need updating.

Both sessions used the same model tier (Haiku 4.5). Session A used native Grep/Read/Edit tools.
Session B used `aux replace` (dry-run then apply) with no prior reads.

| Metric                    | Session A: Native tools | Session B: `aux replace` | Delta      |
|---------------------------|-------------------------|--------------------------|------------|
| **Total tokens**          | 33,811                  | 18,297                   | **-46%**   |
| **Tool calls**            | 30                      | 2                        | **-93%**   |
| **Read calls**            | 6                       | 0                        | **-100%**  |
| **Grep/discovery calls**  | 5                       | 0                        | **-100%**  |
| **Edit calls**            | 18                      | 0                        | **-100%**  |
| **Bash calls**            | 1                       | 2 (dry-run + apply)      | +1         |
| **Correctness**           | 79/79 replaced, 6/6 files | 79/79 replaced, 6/6 files | Same     |

Session A breakdown: 5 Grep (discover + per-file verify) + 6 Read (inspect each modified file) +
18 Edit (one-to-several edits per file) + 1 Bash (final verification) = 30 tool calls.

Session B breakdown: 1 Bash (dry-run, previews all 79 occurrences across 6 files) + 1 Bash
(apply) = 2 tool calls. Zero discovery calls — `aux replace` handles enumeration internally.

**Outcome**:
`aux replace` reduced tool calls by 93% and tokens by 46% on Haiku. The O(1) vs O(N) structural
advantage holds empirically: Session A required one Read + one-or-more Edit calls per modified
file (6 files × ~4 calls average = ~24 calls just for reads and edits), while Session B used
exactly 2 Bash calls regardless of file count. Both sessions achieved perfect correctness (79/79
occurrences, 6/6 files).

---

## Claude Haiku 4.5 (Native tools vs `aux usages` — symbol cross-reference)

Task: Find every definition and reference of `EventHandler` across a 7-file Python eventbus
fixture (class definition in `handler.py`, imported and subclassed across 6 other files).

Both sessions used Haiku 4.5. Session A used native Grep + Read. Session B used `aux usages`.

| Metric               | Session A: Native tools | Session B: `aux usages` | Delta     |
|----------------------|-------------------------|-------------------------|-----------|
| **Total tokens**     | 17,242                  | 15,756                  | **-8.6%** |
| **Tool calls**       | 10                      | 2                        | **-80%**  |
| **Read calls**       | 7                       | 1 (verify only)          | **-86%**  |
| **Grep/discovery**   | 2                       | 0                        | **-100%** |
| **Correctness**      | 33 hits / 7 files       | 33 hits / 7 files        | Same      |

Session A breakdown: 1 Bash (list files) + 2 Grep (file discovery + line content) + 7 Read (inspect each matched file) = 10 tool calls.

Session B breakdown: 1 Bash (`aux usages EventHandler --root ... --glob "**/*.py"`) + 1 Read (verify class definition line) = 2 tool calls.

**Outcome**:
The O(1) vs O(N) pattern holds for symbol cross-reference. Session A reads every matched file
to understand context; Session B returns structured per-entry output (file, line, kind) in a
single call. Token savings are modest (8.6%) because Haiku is already lean, but tool call
reduction is consistent (80%) with other benchmarks.

Note: tree-sitter was not available in this environment. Both sessions tagged `class EventHandler`
at `handler.py:4` as a reference rather than a definition. Semantic tagging (definition vs
reference) is only active when tree-sitter is installed.

---

## Claude Haiku 4.5 (Native tools vs `aux deps` — module dependency graph)

Task: Analyze the import topology of a synthetic 8-file Python pipeline package. Identify the
most heavily imported module (highest afferent coupling), the module with the highest instability
score, and whether any import cycles exist.

Both sessions used Haiku 4.5. Session A read every file manually and computed coupling metrics
by hand. Session B used `aux deps`.

| Metric               | Session A: Native tools | Session B: `aux deps`   | Delta      |
|----------------------|-------------------------|-------------------------|------------|
| **Total tokens**     | 15,923                  | 14,248                  | **-10.5%** |
| **Tool calls**       | 10                      | 2                        | **-80%**   |
| **Read calls**       | 8                       | 0                        | **-100%**  |
| **Correctness**      | Incorrect               | Correct                  | Session B wins |

Session A breakdown: 2 Bash (list files) + 8 Read (one per .py file) = 10 tool calls.
Then manually tallied import edges — and made two errors: reported `config.py` Ca=3 (missed
`transformer.py`'s import) and reported `transformer.py` instability=1.0 (wrong; Ca=1 because
`server.py` imports it, so instability=0.667).

Session B breakdown: 1 Bash (list files for verification) + 1 Bash (`aux deps --root ... --glob "**/*.py"`) = 2 tool calls. Returned correct Ca=4 for `config.py`, I=1.0 for `routes.py`, cycles=[].

**Outcome**:
`aux deps` was more efficient (80% fewer tool calls, 10.5% fewer tokens) and more accurate.
Graph computation is error-prone for manual analysis: Session A correctly identified the most
coupled file but computed the wrong Ca value and mislabelled a second module as maximally unstable.
The skill's graph algorithm is deterministic; manual counting is not.

This benchmark shows a qualitative advantage that goes beyond tool call counts: **structured
graph computation is more reliable than ad-hoc manual analysis**, especially as the number of
modules grows.

---

## Claude Haiku 4.5 (Native tools vs `aux delta` — git change enumeration, stat-only)

Task: List all Python files under `cli/src/aux/` that changed between commits `HEAD~7` and
`HEAD~6` (the commit that introduced the initial CLI package). Report status and line counts,
and identify the top 3 files by lines added.

Both sessions used Haiku 4.5. Note: tree-sitter was not available; `aux delta` ran in stat-only
mode (file names + line counts; no symbol-level diff).

| Metric               | Session A: Native tools | Session B: `aux delta`  | Delta      |
|----------------------|-------------------------|-------------------------|------------|
| **Total tokens**     | 15,498                  | 16,686                  | **+7.7%**  |
| **Tool calls**       | 7                       | 2                        | **-71%**   |
| **Bash calls**       | 7                       | 2                        | **-71%**   |
| **Correctness**      | 23 files / correct top 3 | 23 files / correct top 3 | Same      |

Session A breakdown: 7 Bash calls (git log, git rev-parse, git diff --name-status, git diff --name-only, git diff --numstat, git show commit, git log --format) = 7 tool calls. Output was compact native git text.

Session B breakdown: 1 Bash (`aux delta --root ... --ref-from HEAD~7 --ref-to HEAD~6 --glob "cli/src/aux/**/*.py"`) + 1 Bash (verify with git diff --stat) = 2 tool calls. Output was structured JSON (verbose per-file objects).

**Outcome**:
In stat-only mode (no tree-sitter), `aux delta` uses fewer tool calls (**-71%**) but consumes
**more tokens** (+7.7%) than native git. The JSON output format adds field-level overhead
(`language`, `status`, `additions`, `deletions` per file) that native `--numstat` avoids.

The efficiency advantage inverts for stat-only tasks because native `git diff` output is compact
text while `aux delta` JSON is verbose. **The real advantage of `aux delta` is semantic**: when
tree-sitter is available, Session B returns named symbols added/removed per file in a single call
— a capability that Session A would require multiple `git show` + file reads to replicate.

**Design note**: This benchmark intentionally captures the skill in its fallback (stat-only) mode
to establish the honest baseline. Install tree-sitter + language parsers to unlock the symbol-level
advantage.
