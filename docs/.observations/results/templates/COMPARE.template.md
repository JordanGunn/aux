---
model: gpt-5.2
reasoning: medium
context: 384k
---

# Results Comparison (A vs. B)

| Metric           | Session A (no skills) | Session B (with skills) | Delta    |
|------------------|-----------------------|-------------------------|----------|
| **Tool calls**   | 98                    | 43                      | **+56%** |
| **read_file**    | 71                    | 32                      | **+55%** |
| **grep/search**  | 27                    | 7                       | **+74%** |
| **Context used** | 47% (182k)            | 26% (98k)               | **+45%** |
| **Coverage**     | Excellent             | Excellent               | Same     |
