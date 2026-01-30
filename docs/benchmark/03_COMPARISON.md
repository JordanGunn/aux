# Cross-Model Comparison

| Model   | Reasoning | With AUx | Context Used | Relative Cost   |
|---------|-----------|----------|--------------|-----------------|
| GPT-5.2 | Medium    | No       | 182k (47%)   | 1.0× (baseline) |
| GPT-5.2 | Medium    | Yes      | 117k (30%)   | ~0.64×          |
| GPT-5.2 | Low       | No       | 93k (24%)    | ~0.5×           |
| GPT-5.2 | Low       | Yes      | 64k (17%)    | **~0.35×**      |

**Best configuration**:  
Low reasoning + AUx skills achieves comparable output quality at ~35% of the baseline cost.
