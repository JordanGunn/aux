# Results Comparison

| Metric              | Session A (no skills) | Session B (skills + fixes) | Delta      |
|---------------------|-----------------------|----------------------------|------------|
| **Model**           | GPT-5.2 Medium        | GPT-5.2 Medium             | Same       |
| **read_file**       | 35                    | 28                         | **-20%**   |
| **grep/search**     | ~200-300 files        | 6 passes                   | **-98%**   |
| **Context used**    | 47% (182k)            | 25% (97.9k)                | **-22pp**  |
| **Coverage**        | Excellent             | Excellent                  | Same       |

*Tool call counts are not directly comparable: baseline includes batched parallel calls; Session B excludes `run_command` used to invoke `/grep`. Context delta is reported as percentage points (47% → 25%).

## Key Improvements Over Experiment 01

| Metric              | Exp 01 (B)   | Exp 02 (B)   | Delta     |
|---------------------|--------------|--------------|-----------|
| **Context used**    | 26% (98.4k)  | 25% (97.9k)  | **-1pp**  |
| **Skill adoption**  | 1× skill     | 1× skill     | Same      |

*Exp 01 tool calls include `grep_search`/IDE tools; Exp 02 excludes `run_command` used to invoke `/grep`, so totals are not directly comparable.
