# Summary of Findings

AUx skills reduce token consumption by **16–50%** and tool calls by **53–89%** while maintaining or improving output quality. The effect holds across model tiers, discovery and refactoring tasks.

| Task type          | Skill(s) used  | Token reduction | Tool call reduction | Models tested          |
|--------------------|----------------|-----------------|---------------------|------------------------|
| Discovery          | search/find    | 16–36%          | 53–76%              | GPT-5.2, Haiku 4.5     |
| Refactoring        | sed            | **50%**         | **89%**             | GPT-5.2                |
| Symbol cross-ref   | usages         | 9%              | **80%**             | Haiku 4.5              |
| Dependency graph   | deps           | 11%             | **80%** + accuracy  | Haiku 4.5              |
| Change enumeration | delta          | −8% (stat-only) | **71%**             | Haiku 4.5              |

Token reduction is proportional to model verbosity: larger gains on higher-reasoning models (36%), smaller on already-lean models like Haiku (16%). Tool call reduction is consistent (~53–80%) regardless of model tier, reflecting the structural advantage of bounded discovery over ad-hoc exploration.

For write tasks, the efficiency advantage is larger because `aux sed` eliminates full file reads entirely — only changed lines are consumed into context.

`aux deps` produced a unique quality advantage: native manual analysis miscomputed afferent coupling counts and instability scores; the skill's graph algorithm was accurate where hand-counting was not.

`aux delta` in stat-only fallback mode (tree-sitter unavailable) reduced tool calls 71% but used more tokens than compact git output. The semantic advantage (symbol names added/removed) requires tree-sitter.
