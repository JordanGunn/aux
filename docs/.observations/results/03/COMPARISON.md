---
model: gpt-5.2
reasoning: low
context: 384k
---

# Results Comparison (A vs. B) — Low Reasoning Model

| Metric           | Session A (no skills) | Session B (with skills) | Delta       |
|------------------|-----------------------|-------------------------|-------------|
| **Context used** | 24% (93k)             | 28% (110k)              | +4pp (+18%) |
| **Tool calls**   | 9 (36 ops)            | 11 (45-50 ops)          | +25%        |
| **Files read**   | 22                    | ~39                     | +77%        |
| **grep passes**  | ~14 files surfaced    | 12 structured passes    | —           |
| **Coverage**     | Excellent             | Excellent               | Same        |

## Context Efficiency

| Session | Context | Files Read | Tokens per File |
|---------|---------|------------|-----------------|
| A (no skills) | 93k | 22 | 4,227 |
| B (with skills) | 110k | 39 | 2,821 |

**Session B is 33% more context-efficient per file read.**

With only +4pp context (+18%), Session B covered +77% more files. The skill overhead (reading docs, structured search) is amortized across a larger discovery surface.

## Key Observation

**Session B used MORE context (28% vs 24%) and read MORE files (39 vs 22).**

This is not a failure—it's expected behavior. The skill-guided session:
- Read skill reference docs (overhead)
- Followed a more exhaustive "search-before-read" discipline
- Covered more files because the structured approach surfaced more candidates

**The question is not "did it use less context?" but "did it produce better coverage and output quality?"**

## Output Quality Comparison

| Aspect | Session A | Session B |
|--------|-----------|-----------|
| **Architecture map** | Yes | Yes (more detailed) |
| **Component identification** | Backend, deploy, CLI | Backend, deploy, CLI, frontend guards, session storage |
| **Security findings** | Hardcoded secrets, SSRF risk, duplicate validation | Hardcoded secrets, cookie/JWT ambiguity, missing iss/aud checks |
| **Responsibility mapping** | Issuers vs consumers | Issuers → validators → enforcers → consumers (5-step chain) |
| **Strategy articulation** | 4-step (reactive to timeouts) | 5-step (proactive, skill-guided) |

## Comparison with Previous Experiments (Medium Reasoning)

| Metric           | Exp 02 A (medium, no skills) | Exp 03 A (low, no skills) | Delta     |
|------------------|------------------------------|---------------------------|-----------|
| **Context used** | 47% (182k)                   | 24% (93k)                 | **-50%**  |
| **Coverage**     | Excellent                    | Excellent                 | Same      |

| Metric           | Exp 02 B (medium, with skills) | Exp 03 B (low, with skills) | Delta     |
|------------------|--------------------------------|-----------------------------|-----------|
| **Context used** | 25% (98k)                      | 28% (110k)                  | +3pp      |
| **Coverage**     | Excellent                      | Excellent                   | Same      |

**Low-reasoning model achieves comparable coverage to medium-reasoning, with slightly higher context usage when skills are enabled.**
