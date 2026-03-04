# Cross-Model Comparison

| Model         | Reasoning | With AUx | Tokens | Relative Cost   |
|---------------|-----------|----------|--------|-----------------|
| GPT-5.2       | Medium    | No       | 182k   | 1.0× (baseline) |
| GPT-5.2       | Medium    | Yes      | 117k   | ~0.64×          |
| GPT-5.2       | Low       | No       | 93k    | ~0.5×           |
| GPT-5.2       | Low       | Yes      | 64k    | **~0.35×**      |
| Haiku 4.5     | Standard  | No       | 88k    | ~0.48×          |
| Haiku 4.5     | Standard  | Yes      | 74k    | **~0.41×**      |

**Best configuration**:
Low reasoning + AUx skills achieves comparable output quality at ~35% of the baseline cost.

**Haiku observation**:
Haiku without AUx is already token-lean (88k vs 182k for GPT-5.2 Medium). Adding AUx brings it to 74k — a further 16% reduction. The efficiency gain from AUx is proportionally smaller on leaner models but the tool call reduction (53%) remains consistent across all model tiers.

---

## Haiku 4.5 — Skills benchmark series (single-task experiments)

| Task               | Skill   | Session A tokens | Session B tokens | Token Δ    | Tool call Δ | Correctness Δ |
|--------------------|---------|-----------------|------------------|------------|-------------|---------------|
| Symbol cross-ref   | usages  | 17,242          | 15,756           | **−8.6%**  | **−80%**    | Same          |
| Dependency graph   | deps    | 15,923          | 14,248           | **−10.5%** | **−80%**    | Session B wins |
| Change enumeration | delta   | 15,498          | 16,686           | +7.7%      | **−71%**    | Same          |

**Pattern**: Token savings on Haiku are modest (9–11%) for read-heavy tasks, zero or negative for
stat-only Bash tasks. Tool call savings are large (71–80%) and consistent. The `deps` benchmark
adds a quality dimension: deterministic graph computation outperforms manual coupling analysis.

**Delta exception**: `aux delta` without tree-sitter emits verbose JSON where native git emits
compact text. The token overhead is acceptable only when semantic output (symbol names) makes the
JSON worth its size. Install tree-sitter to unlock the semantic tier.
