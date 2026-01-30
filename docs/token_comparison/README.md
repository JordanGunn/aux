# Token Consumption Experiment

A controlled experiment to measure whether AUx skills reduce token consumption and keep context cleaner.

## Hypothesis

Using AUx skills (grep, find, diff, ls) for surface discovery before deep file reading will:

1. Reduce total tokens consumed
2. Reduce tool call count
3. Improve cross-cutting code discovery
4. Keep context more relevant

## Setup

| Session | Configuration                                                |
|---------|--------------------------------------------------------------|
| **A**   | Skills **disabled** (remove/unregister AUx skills)           |
| **B**   | Skills **enabled** (AUx skills registered)                   |

Run the **exact same prompt** in both sessions. The agent's behavior will differ based on available tools.

## Metrics to Capture

| Metric                   | How to capture                                                |
|--------------------------|---------------------------------------------------------------|
| **Tool calls**           | Count file reads, searches, commands in both sessions         |
| **Tokens used**          | Check platform dashboard (Windsurf usage) after each session  |
| **Files read**           | Note which files the agent actually opened                    |
| **Context relevance**    | Did the agent find cross-cutting auth code, or tunnel-vision? |
| **Time to completion**   | Wall clock for equivalent coverage                            |

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
