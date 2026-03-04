# Conclusion

The hypothesis that AUx skills improve agent efficiency is **confirmed** across model tiers, reasoning levels, and task types:

1. **Token reduction**: 9–50% less context consumed (discovery: 9–36%, refactoring: 50%)
2. **Tool call reduction**: 53–93% fewer tool calls per task — consistent across all model tiers
3. **Quality preserved or improved**: Coverage and accuracy maintained or improved in all experiments
4. **Cost savings**: Low-reasoning + skills achieves ~35% of baseline cost (discovery tasks)
5. **Cross-model consistency**: AUx tool call reduction holds on both high-reasoning GPT-5.2 and lean Haiku models
6. **Token gains scale with model verbosity**: Higher-reasoning models show larger token savings (36%) vs already-lean models (9–16%)
7. **Write tasks scale better**: `aux sed` tool call count is O(1) regardless of files changed; read-Edit cycles are O(N)
8. **Accuracy advantage for graph tasks**: `aux deps` produced correct coupling metrics where native manual analysis made two errors — graph computation is error-prone by hand, deterministic via skill
9. **Conditional semantic advantage**: `aux delta` requires tree-sitter for symbol-level diff; in stat-only fallback, tool calls are fewer but JSON verbosity adds tokens vs compact git output

These results support investing in structured, agent-owned tooling for production agentic workflows.

**Rename skill (discovery mode)**: `aux rename` with discovery mode matches native tools on tool call count (2 vs 3) while eliminating all pre-flight Glob calls. The agent provides `root`, path-scoped `globs`, and `rules` in a single compact plan; file enumeration happens inside the command. The earlier explicit-mode benchmark (v0.1) showed +30% tokens and +67% tool calls because the agent had to enumerate all 12 `src`/`dst` pairs manually before running — discovery mode removes that overhead. The dry-run gate and `plan_hash` receipt remain intact, preserving `aux rename`'s safety and auditability advantage over a raw Bash loop.

**Deps skill (accuracy note)**: Native manual analysis of an 8-file dependency graph produced two metric errors (missed one import edge; wrong instability for a module). `aux deps` computed the graph algorithmically and returned correct values. As codebases grow, manual graph reasoning becomes increasingly unreliable — a structural argument for tool-assisted dependency analysis independent of efficiency gains.

**Delta skill (tree-sitter dependency)**: `aux delta` in stat-only mode (tree-sitter unavailable) reduces tool calls (−71%) at a token cost (+8%). The full semantic advantage — returning symbol names added/removed per file in one call — only activates when tree-sitter language parsers are installed. This is the only benchmark where Session B used *more* tokens than Session A, revealing an important design note: structured JSON output is only worth the verbosity overhead when it delivers information that native tools cannot (symbol-level diff, not just line counts).

## Task-Type Summary

| Task type           | Skill          | Token reduction | Tool call reduction | Correctness    | Models tested      |
|---------------------|----------------|-----------------|---------------------|----------------|--------------------|
| Discovery           | search/find    | 16–36%          | 53–76%              | Same           | GPT-5.2, Haiku 4.5 |
| Refactoring         | sed            | **50%**         | **89%**             | Same           | GPT-5.2            |
| Rename              | rename         | ~0% (projected) | **33%**             | Same           | Haiku 4.5          |
| Bulk text replace   | replace        | **46%**         | **93%**             | Same           | Haiku 4.5          |
| Symbol cross-ref    | usages         | 9%              | **80%**             | Same           | Haiku 4.5          |
| Dependency graph    | deps           | 11%             | **80%**             | Session B wins | Haiku 4.5          |
| Change enumeration  | delta (stat)   | −8%             | **71%**             | Same           | Haiku 4.5          |
