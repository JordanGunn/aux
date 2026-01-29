# Token Consumption Experiment

A controlled experiment to measure whether AUx skills reduce token consumption and keep context cleaner.

## Hypothesis

Using AUx skills (grep, find, diff, ls) for surface discovery before deep file reading will:

1. Reduce total tokens consumed
2. Reduce tool call count
3. Improve cross-cutting code discovery
4. Keep context more relevant

## Setup

| Session | Configuration |
|---------|---------------|
| **A** | Skills **disabled** (remove/unregister AUx skills) |
| **B** | Skills **enabled** (AUx skills registered) |

Run the **exact same prompt** in both sessions. The agent's behavior will differ based on available tools.

## Test Prompt

Use this identical prompt in both sessions:

```
I need you to analyze the authentication and authorization implementation across this codebase.

Specifically:
1. Identify all files related to authentication (OAuth2, tokens, sessions, login flows)
2. Identify all files related to authorization (RBAC, permissions, role checks)
3. Map which services/components handle auth vs which consume it
4. Note any security-relevant patterns (token validation, middleware, guards)

Work methodically. Show me what you find at each step before moving to the next.

Root: /home/jgodau/work/dsg/geoanalytics/platform
```

## Metrics to Capture

| Metric | How to capture |
|--------|----------------|
| **Tool calls** | Count file reads, searches, commands in both sessions |
| **Tokens used** | Check platform dashboard (Windsurf usage) after each session |
| **Files read** | Note which files the agent actually opened |
| **Context relevance** | Did the agent find cross-cutting auth code, or tunnel-vision? |
| **Time to completion** | Wall clock for equivalent coverage |

## Post-Task Prompt

Add this at the end of each session to get self-reported data:

```
Before we finish, can you summarize:
1. How many files did you read or search?
2. How many tool calls did you make?
3. What was your strategy for finding auth-related code?
```

## Expected Differences

### Without Skills (Session A)

- Agent will likely `read_file` many files sequentially
- May grep manually via shell commands
- Potentially miss cross-cutting concerns (tunnel-vision on one directory)
- Higher token consumption from reading full file contents

### With Skills (Session B)

- Agent should use `find`/`grep` skills for surface discovery
- Targeted file reads only after establishing what exists
- Better cross-cutting coverage (auth in backend, deployment, middleware)
- Lower token consumption from bounded, structured output

## Results Template

### Session A (No Skills)

- **Date:** 2026-01-29
- **Model:** GPT-5.2 Medium Reasoning
- **Tokens consumed:** 182,272 (47% of 384,000 context)
- **Tool calls:** 15 total
  - 5× todo_list
  - 4× multi_tool_use.parallel (search passes)
  - 4× multi_tool_use.parallel (file reading passes)
  - 2× multi_tool_use.parallel (targeted grep passes)
- **Files read:** 35 distinct files
- **Files searched:** ~200-300 files surfaced via grep_search/find_by_name
- **Coverage assessment:** Excellent cross-cutting coverage (backend, client, frontend, deploy, containers, docs, iac)
- **Strategy:**
  1. Broad discovery: find_by_name for `*auth*`, `*oauth*`, `*oidc*`, `*jwt*`, `*token*`
  2. Keyword grep across first-party code (excluded vendor dirs after initial noise)
  3. Drill into decision points (middleware, routers, controllers)
  4. Build system map (producers vs consumers of identity/claims)

### Session B (With Skills)

- **Date:** 2026-01-29
- **Model:** GPT-5.2 Medium Reasoning
- **Tokens consumed:** 98,350 (26% of 384,000 context)
- **Tool calls:** 43 total (32 read_file, 7 grep_search, 3 todo_list, 1 skill)
- **Files read:** 32 distinct files
- **Files searched:** 83 files (authn), 171 files (authz) reported with matches
- **Coverage assessment:** Excellent cross-cutting coverage
- **Strategy:** Broad grep → prioritize hot files → prove enforcement points → trace consumers

## Results Comparison

| Metric | Session A (no skills) | Session B (with skills) | Delta |
|--------|----------------------|------------------------|-------|
| **Model** | GPT-5.2 Medium | GPT-5.2 Medium | Same |
| **Tool calls** | 98 | 43 | **-56%** |
| **read_file** | 71 | 32 | **-55%** |
| **grep/search** | 27 | 7 | **-74%** |
| **Context used** | 47% (182k) | 26% (98k) | **-45%** |
| **Coverage** | Excellent | Excellent | Same |

## Conclusion

### What Worked

- **Tool call efficiency:** 56% reduction in tool calls with skills enabled
- **Context savings:** 45% less context consumed for equivalent coverage
- **Search consolidation:** 74% fewer grep operations needed

### Caveats

- Same model used (GPT-5.2) — valid A/B comparison
- Agent used `grep_search` (IDE tool) 7× but skill only 1× — partial adoption
- Skill output verbosity may offset some token savings

### Improvement Opportunities

1. **Skill adoption:** Agent defaulted to IDE grep; better discoverability needed
2. **Output modes:** Configurable summary vs detailed output to reduce follow-up reads
3. **Heuristic guidance:** Skills could suggest entry points, not just matches
